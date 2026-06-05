#!/usr/bin/env python3
"""route.py — pure-rules, offline model router for skilldrop skills.

No API key, no network, no LLM call. Instant. Deterministic. Given a skill name
and the task input, it:

  1. reads the skill's declared tier from model-routing.json,
  2. applies transparent keyword + length signals (weights are right below — tune them),
  3. clamps to the documented escalation rules (never downgrade `heavy`, etc.),
  4. resolves the final tier to a concrete model via the active provider's map,
  5. prints the decision AND every signal that fired, so the choice is auditable.

This is the same routing the model-router agent does, but as a standalone CLI —
so any tool (Cursor, Codex, Kiro, a CI step, a git hook) can shell out to it for
free instead of spending a model on the decision.

Usage:
  python3 route.py --skill devils-advocate --input diff.txt
  git diff | python3 route.py --skill sonar-review --files 12
  python3 route.py --skill exec-summary --text "summarize this for the board" --json
  python3 route.py --skill design-doc --input brief.md --provider cursor
  python3 route.py --list
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════
#  TUNABLE WEIGHTS  —  edit these. Everything here is a small, transparent knob.
#  A signal contributes its weight (once) to a net "step delta". The delta moves
#  the skill's declared tier up/down the ladder light → standard → heavy.
# ════════════════════════════════════════════════════════════════════════════

TIER_LADDER = ["light", "standard", "heavy"]

# Net movement is clamped to this range, so no amount of stacking runs away.
MAX_STEP_UP = 2      # light can reach heavy if enough escalators fire
MAX_STEP_DOWN = 1    # at most one downgrade

# ── Structural signals (reliable: based on size, not wording) ────────────────
# large-input rule: escalate one tier past any of these.
LARGE_INPUT_WORDS = 20_000   # ~30 printed pages
LARGE_INPUT_FILES = 15
WORDS_PER_PAGE = 500         # only used to report an estimated page count

# downgrade-trivial rule: tiny, templated input drops one tier (unless escalated).
TRIVIAL_WORD_MAX = 60

STRUCTURAL_WEIGHTS = {
    "large-input(words)": +1,
    "large-input(files)": +1,
    "trivial-input": -1,
}

# ── Keyword signal groups (weaker hints from wording) ────────────────────────
# Each GROUP fires at most once (matching five times ≠ five votes), and adds its
# weight. Patterns are case-insensitive word/substring regexes.
KEYWORD_GROUPS = [
    {
        "name": "explicit-rigor",          # user asked for care
        "weight": +1,
        "patterns": [
            r"\bthorough\b", r"\brigorous\b", r"\bexhaustive\b",
            r"\bdouble[- ]check\b", r"\bbe (?:very )?careful\b",
            r"\bhigh[- ]stakes\b", r"\bno mistakes\b", r"\bget this right\b",
        ],
    },
    {
        "name": "high-stakes-context",      # where the output lands
        "weight": +1,
        "patterns": [
            r"\bboard\b", r"\bexec(?:utive)?s?\b", r"\bc-level\b", r"\bceo\b",
            r"\binvestor", r"\bproduction\b", r"\bprod\b", r"\blaunch\b",
            r"\bcompliance\b", r"\baudit\b", r"\bregulat",
        ],
    },
    {
        "name": "security-sensitive",
        "weight": +1,
        "patterns": [
            r"\bsecurity\b", r"\bvulnerab", r"\binjection\b", r"\bauth(?:n|z)?\b",
            r"\bcredential", r"\bsecret", r"\bbreach\b", r"\bexploit\b", r"\bcve\b",
        ],
    },
    {
        "name": "ambiguous-input",
        "weight": +1,
        "patterns": [
            r"\bcontradict", r"\bconflicting\b", r"\bambiguous\b",
            r"\bunclear\b", r"\bunsure\b", r"\bnot sure\b", r"\bunderspecified\b",
        ],
    },
    {
        "name": "trivial-intent",            # user signalled it's low-stakes
        "weight": -1,
        "patterns": [
            r"\bquick\b", r"\brough\b", r"\bdraft\b", r"\bjust a\b",
            r"\bsimple\b", r"\btl;?dr\b", r"\bdon'?t overthink\b",
        ],
    },
]

# ════════════════════════════════════════════════════════════════════════════
#  Engine  (you shouldn't need to touch anything below to tune behaviour)
# ════════════════════════════════════════════════════════════════════════════


def load_routing(repo_root: Path) -> dict:
    path = repo_root / "model-routing.json"
    if not path.exists():
        sys.exit(f"route.py: model-routing.json not found at {path}")
    with path.open() as fh:
        return json.load(fh)


def clamp_index(i: int) -> int:
    return max(0, min(len(TIER_LADDER) - 1, i))


def gather_signals(text: str, file_count: int | None) -> list[tuple[str, int]]:
    """Return [(label, weight), ...] for every signal that fired."""
    signals: list[tuple[str, int]] = []
    words = len(text.split()) if text else 0
    escalated = False

    if words >= LARGE_INPUT_WORDS:
        signals.append((f"large-input(words={words:,})", STRUCTURAL_WEIGHTS["large-input(words)"]))
        escalated = True
    if file_count is not None and file_count >= LARGE_INPUT_FILES:
        signals.append((f"large-input(files={file_count})", STRUCTURAL_WEIGHTS["large-input(files)"]))
        escalated = True

    for group in KEYWORD_GROUPS:
        for pat in group["patterns"]:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                signals.append((f"{group['name']}('{m.group(0)}')", group["weight"]))
                if group["weight"] > 0:
                    escalated = True
                break  # group fires once

    # downgrade-trivial only when nothing escalated it.
    if text and words <= TRIVIAL_WORD_MAX and not escalated:
        signals.append((f"trivial-input(words={words})", STRUCTURAL_WEIGHTS["trivial-input"]))

    return signals


def decide(routing: dict, skill: str, text: str, file_count: int | None,
           provider: str | None, override_tier: str | None):
    skills = routing.get("skills", {})
    declared = skills.get(skill, {}).get("tier")
    unrouted = declared is None
    if unrouted:
        declared = "standard"  # default for unknown skills

    declared_idx = TIER_LADDER.index(declared)

    if override_tier:  # user-override (hard): wins, but report what we'd have picked
        final_idx = TIER_LADDER.index(override_tier)
        signals, net = [], 0
    else:
        signals = gather_signals(text, file_count)
        net = sum(w for _, w in signals)
        step = max(-MAX_STEP_DOWN, min(MAX_STEP_UP, net))
        final_idx = clamp_index(declared_idx + step)
        # reasoning-floor (hard): a `heavy` skill is never downgraded.
        if declared == "heavy":
            final_idx = max(final_idx, declared_idx)

    final_tier = TIER_LADDER[final_idx]

    prov = provider or routing.get("active_provider", "claude-code")
    pconf = routing.get("providers", {}).get(prov, {})
    model = pconf.get("models", {}).get(final_tier, "<unknown>")
    placeholder = isinstance(model, str) and model.startswith("<")

    return {
        "skill": skill,
        "unrouted": unrouted,
        "declared_tier": declared,
        "final_tier": final_tier,
        "provider": prov,
        "model": model,
        "model_is_placeholder": placeholder,
        "override": override_tier,
        "net_score": net,
        "signals": signals,
        "words": len(text.split()) if text else 0,
        "est_pages": round(len(text.split()) / WORDS_PER_PAGE, 1) if text else 0,
        "files": file_count,
    }


def render_human(d: dict) -> str:
    arrow = "→"
    lines = []
    head = f"{d['skill']}: {d['declared_tier']} {arrow} {d['final_tier']}"
    if d["declared_tier"] == d["final_tier"]:
        head = f"{d['skill']}: {d['final_tier']} (no change)"
    lines.append(head)
    lines.append(f"  model:     {d['model']}  (provider: {d['provider']})")
    if d["model_is_placeholder"]:
        lines.append(f"  ⚠  model is a placeholder — fill in providers.{d['provider']}.models in model-routing.json")
    if d["unrouted"]:
        lines.append("  ⚠  skill not in model-routing.json — defaulted to 'standard'")
    if d["override"]:
        lines.append(f"  note:      user override forced '{d['override']}' (signals were ignored)")
    sized = []
    if d["words"]:
        sized.append(f"{d['words']:,} words (~{d['est_pages']} pages)")
    if d["files"] is not None:
        sized.append(f"{d['files']} files")
    if sized:
        lines.append(f"  input:     {', '.join(sized)}")
    if d["signals"]:
        lines.append(f"  signals (net {d['net_score']:+d}):")
        for label, w in d["signals"]:
            lines.append(f"    {w:+d}  {label}")
    elif not d["override"]:
        lines.append("  signals:   none fired — stayed at declared tier")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Pure-rules, offline model router for skilldrop skills. No API key, no network.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else None,
    )
    ap.add_argument("--skill", help="skill name (folder name under skills/)")
    ap.add_argument("--input", type=Path, help="file whose contents are the task input")
    ap.add_argument("--text", help="task input as a literal string")
    ap.add_argument("--files", type=int, default=None, help="number of files in scope (for large-input signal)")
    ap.add_argument("--provider", help="override active_provider for model resolution")
    ap.add_argument("--tier", choices=TIER_LADDER, help="force a tier (user-override); reports what rules would have picked")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--routing-dir", type=Path, default=Path(__file__).resolve().parent,
                    help="directory containing model-routing.json (default: this script's dir)")
    ap.add_argument("--list", action="store_true", help="list all skills and their declared tiers, then exit")
    args = ap.parse_args(argv)

    routing = load_routing(args.routing_dir)

    if args.list:
        skills = routing.get("skills", {})
        width = max((len(s) for s in skills), default=0)
        for name in sorted(skills):
            print(f"{name:<{width}}  {skills[name]['tier']}")
        return 0

    if not args.skill:
        ap.error("--skill is required (or use --list)")

    # input precedence: --text > --input > stdin (if piped)
    if args.text is not None:
        text = args.text
    elif args.input is not None:
        text = args.input.read_text(errors="replace")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        text = ""

    decision = decide(routing, args.skill, text, args.files, args.provider, args.tier)

    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(render_human(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Consistency lint for skilldrop. No deps, no network. Run from the repo root:

    python3 validate.py            # exit 0 = clean, 1 = failures
    python3 validate.py --quiet    # failures only, no warnings

Checks (FAIL):
  - folder name == SKILL.md frontmatter `name` == manifest.json `name`
  - manifest has all required fields (name, version, description, entrypoint,
    deps, env, related, tags, model)
  - manifest `model.tier` == model-routing.json tier, both directions
  - manifest `related`: every entry is a real skill folder, and every sibling
    skill referenced in SKILL.md (backticked) appears in `related` — and vice versa
  - evals/ files, when present, parse and have the right shape: evals.json has
    >=1 eval with prompt + assertions; eval_queries.json has both should_trigger
    true and false rows
  - manifest description == SKILL.md frontmatter description (whitespace-normalized)
  - packs.json: every pack entry is a real skill folder, and every skill
    belongs to at least one pack
  - manifest hooks (optional): each entry's event is in the RFC-0006 vocabulary,
    its action is a real skill folder, and it carries a description
  - README.md skill counts match the number of skills on disk (prose drifts; the
    generated catalogue site cannot, so only the hand-written numbers need checking)
  - agents/<name>.md: filename == frontmatter `name`, and `description` is present
  - every `<name>` subagent a SKILL.md delegates to is a real file in agents/
  - (RFC-0015) every in-skill path a SKILL.md names (scripts/, references/,
    ${CLAUDE_SKILL_DIR}/…) resolves to a real file; long-form material
    (reference.md, references/, lenses/, rubrics/) is linked from SKILL.md; and
    prose markdown links across skills/agents/docs/root docs don't dangle
    (fenced blocks + {template} lines + placeholder targets are skipped)
  - (RFC-0026) every skill belongs to at least one `outcomes` entry in packs.json,
    and every outcome entry names a real skill folder
  - (RFC-0016) every SKILL.md has a `## Quality bar` and `## Anti-patterns`
    section (golden rule 7); a skill with scripts/ cites both the
    ${CLAUDE_SKILL_DIR}/ and plain scripts/ forms; and a heavy-tier judgment
    skill ships an examples/ input→output oracle

Warnings (non-fatal):
  - SKILL.md over ~500 lines (golden rule 3)
  - agents/<name>.md missing the recommended `tools` or `model` frontmatter
"""
import glob
import json
import os
import re
import sys

import build_marketplace  # .claude-plugin/ drift check (RFC-0014)

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(ROOT, "skills")
AGENTS = os.path.join(ROOT, "agents")
LOOPS = os.path.join(ROOT, "loops")  # RFC-0028 — the third primitive
REQUIRED_FIELDS = ["name", "version", "description", "entrypoint", "deps", "env", "related", "tags", "model"]
HOOK_EVENTS = {"session-start", "pre-commit-review", "on-demand"}  # RFC-0006; kept in sync with bin/skilldrop.js

# RFC-0015 — the doc↔reality checks: a SKILL.md's in-repo paths must resolve, its long-form
# material must be linked, and prose markdown links must not dangle. Fenced code blocks,
# {placeholder}/… template text, and lines carrying a {…} template token are skipped so the
# repo's own scaffold examples don't false-fail (the exact false positives a naive scan hits).
INSKILL_REF = re.compile(r"(?<![\w/])((?:scripts|references|templates|lenses|rubrics|assets|examples)/[\w./-]+)")
CLAUDE_DIR_REF = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
MATERIAL = ("reference.md", "references/*.md", "lenses/*.md", "rubrics/*.md")  # AGENTS.md: link these from SKILL.md
LINK_DOCS = ("README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", "SECURITY.md", "MODEL-ROUTING.md")


def strip_fences(text):
    return FENCE.sub("", text)


def is_placeholder(target):
    return "..." in target or any(c in target for c in "{}<>")

failures, warnings = [], []


def fail(skill, msg):
    failures.append(f"{skill}: {msg}")


def warn(skill, msg):
    warnings.append(f"{skill}: {msg}")


SUBAGENT_REF = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+subagent")


def check_agents(skill_dirs):
    """agents/ is the repo's second primitive and had no enforced invariants at all.
    The link a skill declares to a subagent is real — feature-implement-loop delegates
    to `devils-advocate` — so a rename that misses one silently breaks the delegation."""
    if not os.path.isdir(AGENTS):
        return set()
    names = set()
    for f in sorted(os.listdir(AGENTS)):
        if not f.endswith(".md") or f == "README.md":
            continue
        stem = f[:-3]
        names.add(stem)
        fm = frontmatter(open(os.path.join(AGENTS, f), encoding="utf-8").read())
        fields = dict(re.findall(r"^([a-z-]+):\s*(.+?)\s*$", fm, re.M))
        if fields.get("name") != stem:
            fail(f"agents/{f}", f"frontmatter name '{fields.get('name')}' != filename '{stem}'")
        if not fields.get("description"):
            fail(f"agents/{f}", "missing `description` — it is what routes a delegation here")
        for k in ("tools", "model"):
            if k not in fields:
                warn(f"agents/{f}", f"no `{k}` in frontmatter (recommended)")

    for d in skill_dirs:
        sp = os.path.join(SKILLS, d, "SKILL.md")
        if not os.path.exists(sp):
            continue
        for ref in set(SUBAGENT_REF.findall(open(sp, encoding="utf-8").read())):
            if ref not in names:
                fail(d, f"SKILL.md delegates to the `{ref}` subagent, but agents/{ref}.md does not exist")
    return names



LOOP_REQUIRED = ["name", "description", "entrypoint", "kind", "stages"]
LOOP_OPTIONAL = ["$comment", "version", "cap"]
STAGE_REQUIRED = ["id", "type", "intent", "skills"]
STAGE_OPTIONAL = ["gate"]
GATE_REQUIRED = ["id", "kind", "verdicts"]
GATE_OPTIONAL = ["script", "revise_to"]
STAGE_TYPES = {"generate", "verify", "gate"}
GATE_KINDS = {"mechanical", "review", "human"}
GATE_ID = re.compile(r"^G[0-9]+(\.[0-9]+)?$")


def _closed(where, obj, required, optional):
    """contracts/*.schema.json are closed schemas. A typo'd key must fail, not be ignored."""
    for k in required:
        if k not in obj:
            fail(where, f"missing required key `{k}`")
    for k in obj:
        if k not in required and k not in optional:
            fail(where, f"unknown key `{k}` — the loop contract is closed (contracts/loop.schema.json)")


def check_loops(dir_set):
    """RFC-0028 — loops/ is the third primitive. A loop sequences skills; it never contains one.
    These checks exist because a loop that names a renamed skill, or a gate that can only say
    yes, is worse than no loop at all: it looks like governance and enforces nothing."""
    if not os.path.isdir(LOOPS):
        return set()
    terminals = json.load(open(os.path.join(ROOT, "contracts", "terminals.json")))
    vclass = {v: m["class"] for v, m in terminals["verdicts"].items()}
    names, seen_gates = set(), {}

    for d in sorted(x for x in os.listdir(LOOPS) if os.path.isdir(os.path.join(LOOPS, x))):
        names.add(d)
        p = os.path.join(LOOPS, d)
        where = f"loops/{d}"
        try:
            spec = json.load(open(os.path.join(p, "loop.json")))
        except (OSError, json.JSONDecodeError) as e:
            fail(where, f"loop.json unreadable: {e}")
            continue
        md_path = os.path.join(p, "LOOP.md")
        if not os.path.exists(md_path):
            fail(where, "no LOOP.md — it is the entrypoint an agent reads")
            continue
        md = open(md_path, encoding="utf-8").read()
        fm = dict(re.findall(r"^(name|description):\s*(.+?)\s*$", frontmatter(md), re.M))

        _closed(where, spec, LOOP_REQUIRED, LOOP_OPTIONAL)
        # Same name triple-match skills are held to: folder == loop.json == frontmatter.
        if spec.get("name") != d or fm.get("name") != d:
            fail(where, f"name triple mismatch: folder '{d}', loop.json '{spec.get('name')}', "
                        f"LOOP.md '{fm.get('name')}'")
        if spec.get("entrypoint") != "LOOP.md":
            fail(where, "entrypoint must be 'LOOP.md'")
        if spec.get("kind") not in {"loop", "wrapper"}:
            fail(where, f"kind must be 'loop' or 'wrapper', got {spec.get('kind')!r}")
        cap = spec.get("cap", 3)
        if not isinstance(cap, int) or not 1 <= cap <= 10:
            fail(where, f"cap must be an int 1..10, got {cap!r}")
        if " ".join(str(spec.get("description", "")).split()) != " ".join(fm.get("description", "").split()):
            fail(where, "loop.json description and LOOP.md frontmatter description differ")
        for section in ("## Quality bar", "## Anti-patterns"):
            if not re.search(rf"^{re.escape(section)}", md, re.M):
                fail(where, f"LOOP.md has no `{section}` section — a loop without one is a diagram")
        if len(md.splitlines()) > 500:
            warn(where, f"LOOP.md is {len(md.splitlines())} lines — spill into reference material")

        stages = spec.get("stages") or []
        if not stages:
            fail(where, "no stages — a loop with no stages sequences nothing")
        stage_ids = []
        for i, st in enumerate(stages):
            sw = f"{where} stage[{i}]"
            _closed(sw, st, STAGE_REQUIRED, STAGE_OPTIONAL)
            sid = st.get("id")
            if sid in stage_ids:
                fail(sw, f"duplicate stage id '{sid}'")
            stage_ids.append(sid)
            if st.get("type") not in STAGE_TYPES:
                fail(sw, f"type must be one of {sorted(STAGE_TYPES)}, got {st.get('type')!r}")
            for s in st.get("skills", []):
                if s == "*":
                    if spec.get("kind") != "wrapper":
                        fail(sw, "`*` (any generator) is legal only in a wrapper")
                elif s not in dir_set:
                    fail(sw, f"names skill '{s}', which is not a skills/ folder")
            g = st.get("gate")
            if not g:
                continue
            gw = f"{where} gate {g.get('id', '?')}"
            _closed(gw, g, GATE_REQUIRED, GATE_OPTIONAL)
            gid = g.get("id", "")
            if not GATE_ID.match(str(gid)):
                fail(gw, f"gate id '{gid}' must match G<n>[.<n>] — a gate is a place people point at")
            elif gid in seen_gates:
                fail(gw, f"gate id '{gid}' already used by {seen_gates[gid]} — gate ids are repo-unique")
            else:
                seen_gates[gid] = where
            if g.get("kind") not in GATE_KINDS:
                fail(gw, f"kind must be one of {sorted(GATE_KINDS)}, got {g.get('kind')!r}")
            if g.get("kind") == "mechanical":
                sc = g.get("script")
                if not sc:
                    fail(gw, "a mechanical gate needs a `script` — otherwise nothing mechanical decides")
                elif not os.path.exists(os.path.join(ROOT, sc)):
                    fail(gw, f"script '{sc}' does not exist")
            elif g.get("script"):
                fail(gw, f"`script` is only for a mechanical gate, not a {g.get('kind')} one")
            vs = g.get("verdicts") or []
            unknown = [v for v in vs if v not in vclass]
            if unknown:
                fail(gw, f"verdict(s) {unknown} are not in contracts/terminals.json — "
                         f"a new gate may not invent a new word for an existing outcome")
            known = [v for v in vs if v in vclass]
            if known and not any(vclass[v] == "pass" for v in known):
                fail(gw, "no pass-class verdict — this gate can never be satisfied")
            if known and not any(vclass[v] != "pass" for v in known):
                fail(gw, "only pass-class verdicts — a gate that can only succeed is not a gate")
            if "BLOCKED" not in vs:
                fail(gw, "cannot emit BLOCKED — every gate must be able to say its input is missing")
            rt = g.get("revise_to")
            if rt is not None and rt not in stage_ids[:-1] + [stage_ids[-1]][:0] + stage_ids[:i]:
                if rt not in stage_ids[:i]:
                    fail(gw, f"revise_to '{rt}' is not an earlier stage in this loop")
    return names

def frontmatter(md_text):
    parts = md_text.split("---")
    return parts[1] if len(parts) >= 3 else ""


def main():
    routing = json.load(open(os.path.join(ROOT, "model-routing.json")))["skills"]
    skill_dirs = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))
    dir_set = set(skill_dirs)

    for d in skill_dirs:
        p = os.path.join(SKILLS, d)
        try:
            manifest = json.load(open(os.path.join(p, "manifest.json")))
        except (OSError, json.JSONDecodeError) as e:
            fail(d, f"manifest.json unreadable: {e}")
            continue
        try:
            md = open(os.path.join(p, "SKILL.md")).read()
        except OSError:
            fail(d, "SKILL.md missing")
            continue

        fm = frontmatter(md)
        m_name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not m_name or not (d == manifest.get("name") == m_name.group(1)):
            fail(d, f"name triple mismatch: folder={d} manifest={manifest.get('name')} "
                    f"frontmatter={m_name.group(1) if m_name else None}")

        for field in REQUIRED_FIELDS:
            if field not in manifest:
                fail(d, f"manifest missing required field '{field}'")

        tier = manifest.get("model", {}).get("tier")
        if d not in routing:
            fail(d, "no entry in model-routing.json")
        elif tier != routing[d].get("tier"):
            fail(d, f"tier mismatch: manifest={tier} routing={routing[d].get('tier')}")

        refs = {r for r in re.findall(r"`([a-z][a-z0-9-]+)`", md) if r in dir_set and r != d}
        related = manifest.get("related")
        if isinstance(related, list):
            rel_set = set(related)
            for r in rel_set - dir_set:
                fail(d, f"related entry '{r}' is not a skill folder")
            for r in sorted(refs - rel_set):
                fail(d, f"SKILL.md references `{r}` but manifest related omits it")
            for r in sorted(rel_set & dir_set - refs):
                fail(d, f"manifest related lists '{r}' but SKILL.md never references it")
        elif related is not None:
            fail(d, "related must be a flat list of skill names")

        for h in manifest.get("hooks", []) or []:
            if not isinstance(h, dict):
                fail(d, "each hooks entry must be an object with event/action/description")
                continue
            if h.get("event") not in HOOK_EVENTS:
                fail(d, f"hook event {h.get('event')!r} not in {sorted(HOOK_EVENTS)}")
            if h.get("action") not in dir_set:
                fail(d, f"hook action {h.get('action')!r} is not a skill folder")
            if not h.get("description"):
                fail(d, f"hook for event {h.get('event')!r} needs a description")

        evals_path = os.path.join(p, "evals", "evals.json")
        queries_path = os.path.join(p, "evals", "eval_queries.json")
        if os.path.exists(evals_path):
            try:
                ev = json.load(open(evals_path))
                if ev.get("skill_name") != d:
                    fail(d, f"evals.json skill_name={ev.get('skill_name')} != {d}")
                if not ev.get("evals") or any(not e.get("prompt") or not e.get("assertions") for e in ev["evals"]):
                    fail(d, "evals.json needs >=1 eval, each with prompt + assertions")
            except json.JSONDecodeError as e:
                fail(d, f"evals.json invalid JSON: {e}")
        if os.path.exists(queries_path):
            try:
                qs = json.load(open(queries_path))
                flags = {q.get("should_trigger") for q in qs}
                if flags != {True, False}:
                    fail(d, "eval_queries.json needs both should_trigger true and false rows")
            except json.JSONDecodeError as e:
                fail(d, f"eval_queries.json invalid JSON: {e}")

        n_lines = md.count("\n") + 1
        if n_lines > 500:
            warn(d, f"SKILL.md is {n_lines} lines (golden rule: ~500 max)")

        m_desc = re.search(r"^description:\s*(.+?)(?=^\w+:|\Z)", fm, re.M | re.S)
        if m_desc and " ".join(m_desc.group(1).split()) != " ".join(manifest.get("description", "").split()):
            fail(d, "manifest description differs from SKILL.md frontmatter description")

        # RFC-0015: every in-skill path a SKILL.md names must resolve (fenced examples skipped),
        # so a `scripts/`, `references/`, or `${CLAUDE_SKILL_DIR}/` reference can't drift dead.
        body = strip_fences(md)
        refs = {(r, r) for r in INSKILL_REF.findall(body)}
        refs |= {("${CLAUDE_SKILL_DIR}/" + r, r) for r in CLAUDE_DIR_REF.findall(body)}
        for shown, rel in refs:
            rel = rel.split("#")[0].rstrip(".,)`")
            if is_placeholder(rel):
                continue
            if not os.path.exists(os.path.join(p, rel)):
                fail(d, f"SKILL.md references '{shown}' but {rel} does not exist in the skill")

        # RFC-0015: long-form material must be linked from SKILL.md (AGENTS.md golden rule) —
        # an orphaned reference.md/lens/rubric is invisible to a reader and drifts unnoticed.
        for g in MATERIAL:
            for sup in glob.glob(os.path.join(p, g)):
                rel = os.path.relpath(sup, p)
                if os.path.basename(sup) not in md and rel not in md:
                    fail(d, f"{rel} exists but SKILL.md never links it (reference it, or remove it)")

        # RFC-0016: golden rule 7 — a skill ships a Quality bar + Anti-patterns section, or it's a
        # description, not a generator. (AGENTS.md claimed this was enforced; now it actually is.)
        for heading in ("Quality bar", "Anti-patterns"):
            if not re.search(rf"^##\s+{heading}", md, re.M):
                fail(d, f"SKILL.md missing a '## {heading}' section (golden rule 7)")
        # RFC-0016: a skill with scripts/ must reach them from Claude Code AND other IDEs.
        if glob.glob(os.path.join(p, "scripts", "*")):
            if "${CLAUDE_SKILL_DIR}/scripts" not in md or not re.search(r"(?<!DIR\}/)\bscripts/", md):
                fail(d, "has scripts/ but SKILL.md must cite both ${CLAUDE_SKILL_DIR}/scripts/ and a plain scripts/ path")
        # RFC-0016: heavy-tier (adversarial/weighted-judgment) skills ship a behavioral oracle —
        # an examples/ input→output that shows what a passing output looks like.
        if tier == "heavy" and not glob.glob(os.path.join(p, "examples", "*")):
            fail(d, "heavy-tier judgment skill needs an examples/ input→output oracle (RFC-0016)")

    loop_dirs = set(os.listdir(LOOPS)) if os.path.isdir(LOOPS) else set()
    for r in sorted(set(routing) - dir_set):
        if r in loop_dirs:
            fail("model-routing.json", f"'{r}' is a loop, not a skill — loops sequence skills "
                                       f"and make no model call of their own, so they carry no tier")
        else:
            fail("model-routing.json", f"entry '{r}' has no skill folder")

    packs_doc = json.load(open(os.path.join(ROOT, "packs.json")))
    packs = packs_doc["packs"]
    packed = set()
    for pname, pack in packs.items():
        for s in pack.get("skills", []):
            if s not in dir_set:
                fail("packs.json", f"pack '{pname}' lists '{s}', which is not a skill folder")
            packed.add(s)
    for s in sorted(dir_set - packed):
        fail("packs.json", f"skill '{s}' belongs to no pack — every skill needs an audience")

    # RFC-0026: outcomes are the site's second browse axis. Same two-way check as packs, so a
    # new skill can't quietly become unreachable from the outcome chips.
    outcomes = packs_doc.get("outcomes", {})
    if not outcomes:
        fail("packs.json", "no `outcomes` block — the site's outcome axis is generated from it (RFC-0026)")
    outcomed = set()
    for oname, outcome in outcomes.items():
        if not outcome.get("description"):
            fail("packs.json", f"outcome '{oname}' needs a description — it is the chip's tooltip")
        for s in outcome.get("skills", []):
            if s not in dir_set:
                fail("packs.json", f"outcome '{oname}' lists '{s}', which is not a skill folder")
            outcomed.add(s)
    for s in sorted(dir_set - outcomed):
        fail("packs.json", f"skill '{s}' belongs to no outcome — add it to one in packs.json (RFC-0026)")

    # The Claude Code plugin marketplace (RFC-0014) is generated from package.json;
    # a committed file drifting from that generator fails here so it can't ship stale.
    for rel in build_marketplace.stale():
        fail(".claude-plugin", f"{rel} is stale — run `python3 build_marketplace.py`")

    agent_names = check_agents(skill_dirs)
    loop_names = check_loops(dir_set)

    # The site regenerates its counts from the manifests; README prose does not.
    # This is the only place a skill count can go stale unnoticed (RFC-0011).
    # RFC-0011/site: the OG share image hard-codes its headline counts (it is a rendered raster,
    # not generated at build time), so it is the one place a stale number can ship unnoticed.
    og = os.path.join(ROOT, "assets", "og.svg")
    if os.path.exists(og):
        og_txt = open(og, encoding="utf-8").read()
        n_agents = len([f for f in os.listdir(AGENTS) if f.endswith(".md") and f != "README.md"]) \
            if os.path.isdir(AGENTS) else 0
        n_packs = len(json.load(open(os.path.join(ROOT, "packs.json")))["packs"])
        for claim, actual in ((r"(\d+) skills", len(skill_dirs)),
                              (r"(\d+) role packs", n_packs),
                              (r"(\d+) reviewer subagents", n_agents)):
            m = re.search(claim, og_txt)
            if m and int(m.group(1)) != actual:
                fail("assets/og.svg", f"says '{m.group(0)}' but {actual} are on disk "
                                      f"— update the SVG and re-render: rsvg-convert -w 1200 -h 630 "
                                      f"assets/og.svg -o assets/og.png")

    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    # Prose only. The guard is about headline claims ("57 portable AI-agent skills"); a fenced
    # block legitimately carries per-pack counts ("# 17 skills" beside a pack install command),
    # and flagging those would force the docs to avoid the plainest way to write them.
    for n in set(re.findall(r"\b(\d{2})\s+(?:portable |)(?:AI-agent |)skills\b",
                            strip_fences(readme))):
        if int(n) != len(skill_dirs):
            fail("README.md", f"says '{n} skills' but {len(skill_dirs)} are on disk")

    # A matching count is not coverage. The count guard can pass while skills, packs or agents
    # have no documentation at all — it checks the number, not the thing the number describes.
    for d in sorted(skill_dirs):
        if f"skills/{d}/SKILL.md" not in readme:
            fail("README.md", f"no row for skill '{d}' — the catalogue documents what it ships")
    with open(os.path.join(ROOT, "packs.json"), encoding="utf-8") as fh:
        pack_names = sorted(json.load(fh)["packs"])
    for p in pack_names:
        if f"`{p}`" not in readme:
            fail("README.md", f"pack '{p}' is in packs.json but not documented in README")
    for a in sorted(agent_names):
        if f"agents/{a}.md" not in readme:
            fail("README.md", f"agent '{a}' ships but is not documented in README")
    for lp in sorted(loop_names):
        if f"loops/{lp}/LOOP.md" not in readme:
            fail("README.md", f"loop '{lp}' ships but is not documented in README")

    # RFC-0015: prose markdown links across skills, agents, docs, and the root convention files
    # must resolve — fenced blocks, {template} lines, and placeholder targets are skipped.
    md_files = set(glob.glob(os.path.join(SKILLS, "**", "*.md"), recursive=True))
    md_files |= set(glob.glob(os.path.join(AGENTS, "*.md")))
    md_files |= set(glob.glob(os.path.join(LOOPS, "**", "*.md"), recursive=True))
    md_files |= set(glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True))
    md_files |= {os.path.join(ROOT, f) for f in LINK_DOCS if os.path.exists(os.path.join(ROOT, f))}
    for mf in sorted(md_files):
        d0 = os.path.dirname(mf)
        for line in strip_fences(open(mf, encoding="utf-8").read()).splitlines():
            if "{" in line or "}" in line:  # a template/placeholder line — not a real link
                continue
            for target in MD_LINK.findall(line):
                if target.startswith(("http", "#", "mailto:", "//")) or is_placeholder(target):
                    continue
                t = target.split("#")[0].strip()
                if t and not os.path.exists(os.path.normpath(os.path.join(d0, t))):
                    fail("links", f"{os.path.relpath(mf, ROOT)}: dangling link -> {target}")

    quiet = "--quiet" in sys.argv
    if warnings and not quiet:
        print(f"-- {len(warnings)} warning(s) --")
        for w in warnings:
            print("  WARN", w)
    if failures:
        print(f"-- {len(failures)} FAILURE(s) --")
        for f in failures:
            print("  FAIL", f)
        sys.exit(1)
    print(f"OK: {len(skill_dirs)} skills + {len(loop_names)} loops + {len(agent_names)} agents validated"
          + ("" if quiet else f", {len(warnings)} warning(s)"))


if __name__ == "__main__":
    main()

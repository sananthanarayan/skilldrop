---
name: pre-merge-review
description: Gate an existing change for merge — run one skill that fires the whole production-readiness pass. First a deterministic mechanical gate (lint + typecheck + tests, via a script whose exit code decides), then the three-reviewer panel dispatched in parallel — devils-advocate (correctness), security-reviewer (exploitability), code-quality (craft) — then a single READY / NOT READY verdict. Use before opening a PR or merging, when you want the full review fleet run on a diff you already have. Do NOT use to implement a feature from a spec (that's feature-implement-loop) or to review a document (that's doc-critique).
---

# pre-merge-review

One command that runs the full production-readiness pass on a change you already have: the **mechanical gate** (deterministic — real commands, real exit codes) and the **reviewer panel** (three cold-read subagents), then a single **READY / NOT READY** verdict. This is the "is this safe to merge?" orchestrator — where [`feature-implement-loop`](../feature-implement-loop/SKILL.md) *generates* code and loops, this one *judges* a diff that already exists and gates it.

Two gates, and they are different kinds. The mechanical gate is **not a judgment call** — a script runs the project's checks and its exit code decides, so a red gate can't be talked past. The review panel *is* judgment — three lenses that a deterministic check can't cover.

## How to respond

1. **Scope the change.** The diff, the branch vs. its base, or the files the user names. Everything below reviews *that change*, never the whole repo.

2. **Run the mechanical gate first — it is un-bypassable.** Run the bundled gate script:
   - Claude Code: `python3 ${CLAUDE_SKILL_DIR}/scripts/gate.py`
   - Other IDEs: `python3 skills/pre-merge-review/scripts/gate.py`

   It auto-detects the project's lint / typecheck / test commands (or takes `--cmd "…"` / `--config gate.json`), runs each, and **exits non-zero if any fail**. A **RED gate is an automatic `NOT READY`** — do not proceed to a positive verdict, no matter how clean the review looks. The pass/fail is the script's exit code, not your assessment of the code. If the gate can't determine commands, surface `BLOCKED: need verify commands` and ask for them once — never fabricate a green gate.

3. **Fire the review panel — in parallel.** Independent lenses on the diff, each in a fresh context so none anchors on the author's reasoning:
   - **Subagent tools (Claude Code, …):** dispatch the `devils-advocate` subagent (correctness — edge cases, broken assumptions, staff-engineer pushback, test gaps), the `security-reviewer` subagent (exploitability — authz/IDOR, injection, secret exposure, SSRF, unsafe deserialization, weak crypto, risky deps), and the `code-quality` subagent (craft — naming, structure, duplication, readability). Run them together; they don't depend on each other.
   - **No-subagent tools (Codex, Cursor, Aider, …):** sweep the three lenses inline yourself — correctness, then security, then craft.
   - Tag findings 🟥 blocker · 🟧 major · 🟨 minor · ⚪ nit, each with `file:line` and a concrete fix. **Merge and de-dupe** across the three lenses — when two flag the same line, report it once with both angles.

4. **Render the verdict.** One word, then the reasons:
   - **`READY`** — the mechanical gate is GREEN **and** there is no 🟥 blocker and no 🟧 major.
   - **`NOT READY`** — the gate is RED, **or** any blocker/major stands. List every blocking item (gate failures first, then blocker/major findings) and what must change. 🟨 minor / ⚪ nit are listed but never block.
   - **`BLOCKED`** — the gate couldn't run (unknown commands, no test setup). Name what's missing.

5. **Escalate design disagreements — don't adjudicate them.** If the panel surfaces a genuine *tradeoff* dispute (not a bug — "should this be a queue or a cron?"), the verdict still gates on gate+blocker/major, but **offer [`council-review`](../council-review/SKILL.md)** for the open decision rather than settling a design debate here.

6. **Report.** Lead with the verdict. Then: the gate results table (command → PASS/FAIL), the merged panel findings by severity, and a **must-fix** list for `NOT READY`.

## Useful references in this skill

- [`scripts/gate.py`](scripts/gate.py) — the deterministic mechanical gate (`--list` to preview, `--cmd`/`--config` to override detection, `--install-hook` to enforce it — see below).

## Enforce as a harness (opt-in)

The verdict above is *advisory* — an agent can ignore prose. To make the gate **un-bypassable**, move enforcement into the substrate every tool shares (git and CI), not this skill's text:

- **Layer 1 — local git block (portable across every tool).** Install a blocking pre-commit hook:
  - Claude Code: `python3 ${CLAUDE_SKILL_DIR}/scripts/gate.py --install-hook --cmd "npm test" --cmd "npm run lint"`
  - other IDEs: `python3 skills/pre-merge-review/scripts/gate.py --install-hook --cmd "…"`

  Git runs it on every `git commit` no matter which tool (Claude, Cursor, Codex, Aider) drove the change; a RED gate blocks the commit. Bypassable with `git commit --no-verify`, so it stops honest mistakes, not a determined override. `--uninstall-hook` removes it.
- **Layer 2 — CI required checks (un-bypassable).** Run the same commands as a required status check on the branch; the git host refuses the merge when they're red, outside any local tool — the layer that can't be `--no-verify`'d. Pair Layer 1 (fast local feedback) with Layer 2 (the backstop).
- **Layer 3 — per-tool native (richer where it exists).** Where a tool can block its own turn, point it at the gate: Claude Code — a `Stop`/`PreToolUse` hook running `gate.py`; Aider — `--auto-test --test-cmd "python3 …/gate.py"`. Cursor and Codex lean on Layers 1–2.

The honest limit: a portable *skill* can't physically block an agent — enforcement lives in git/CI (universal) or per-tool hooks (uneven). Rationale and the distinction from RFC-0006's reminder-only hooks: RFC-0019.

## Quality bar

- **The mechanical gate is run, not assumed.** A verdict with no real gate result is invalid — you ran the script (or reported `BLOCKED`), you didn't eyeball the tests.
- **The gate is un-bypassable.** A RED gate is `NOT READY` regardless of how good the review looks. The review can add blockers; it can never clear a failing gate.
- **Findings are merged and de-duped** across the three lenses — the same line is not reported three times.
- **The verdict is one word plus the blocking reasons**, not a hedged paragraph. A reader sees READY/NOT READY and exactly what stands in the way.
- **Design disagreements go to `council-review`**, not adjudicated here — this skill gates a change, it doesn't decide an architecture.

## When to use this skill

- ✅ Before opening a PR or merging — the full production-readiness pass on a diff you already have.
- ✅ "Run all the reviewers on this change and tell me if it's safe to merge."
- ✅ Reviewing a change you (or another agent) generated elsewhere, or a teammate's branch.

## When NOT to use this skill

- ❌ Implementing a feature from a spec — that's [`feature-implement-loop`](../feature-implement-loop/SKILL.md), which generates and loops; this skill only judges an existing change.
- ❌ One lens is enough — a pure bug pass is [`devils-advocate`](../devils-advocate/SKILL.md) standalone; a pure doc pass is `doc-critique`.
- ❌ An open design decision ("Postgres or Dynamo?") — that's `council-review`.

## Anti-patterns to avoid

- ❌ **Declaring `READY` on a RED gate.** The whole point is that the mechanical gate is un-bypassable. A failing test or lint is `NOT READY`, full stop — the review does not get a vote on it.
- ❌ **Skipping the gate and "just reviewing".** Without the deterministic pass this is only half the check — the half that can be fooled. Run `scripts/gate.py`.
- ❌ **A toothless panel.** Firing the three subagents (or sweeping the lenses) and reporting "no issues" on a real change — the panel earns its keep only if it's actually adversarial.
- ❌ **Triple-reporting.** The same `file:line` flagged by all three lenses as three findings. Merge them.
- ❌ **Adjudicating a design debate.** Settling "queue vs cron" inside the verdict instead of gating on gate+severity and offering `council-review`.
- ❌ **Calling a reviewer *skill* from here.** Skills don't invoke skills (see CLAUDE.md). Drive the review *subagents* where they exist, or sweep the lenses inline.

**Non-interactive:** if the verify commands can't be detected and none were supplied, emit `BLOCKED: need verify commands (--cmd/--config)` — never fabricate a green gate. If the change scope is ambiguous, default to the working-tree diff and tag it `[assumption]` at the top of the report.

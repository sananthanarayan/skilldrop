---
rfc: 0018
title: pre-merge-review — one skill that fires the panel behind a mechanical gate
status: implemented
date: 2026-08-03
author: sananthanarayan
---

# RFC-0018: pre-merge-review — one skill that fires the panel behind a mechanical gate

## Problem / use case

Two deliberate differences remained between skilldrop and agent-ready-repo's `work-loop`
(RFC-0017 closed the third — the reviewer panel):

1. **No single skill fires the whole reviewer fleet on an existing change.** `feature-implement-loop`
   drives the panel, but only while *generating* a feature from a spec; its own "When NOT to use"
   punts a pure review of an existing diff to `devils-advocate` alone. There was no "run all the
   reviewers on this branch before I merge" entry point.
2. **The gate was discipline, not mechanism.** `feature-implement-loop`'s gate was the agent's own
   read of blocker/major/uncovered-criterion — nothing deterministic the agent couldn't talk past.
   `work-loop`'s hard lint/typecheck/test gate is a machine result.

## Fit check (new skill)

- **Concrete artifact:** a `READY` / `NOT READY` / `BLOCKED` verdict plus a gate results table, merged
  panel findings, and an ordered must-fix list.
- **Portable:** `scripts/gate.py` is stdlib and reads commands from `--cmd`/`--config`/auto-detect
  (Python/Node/Go/Makefile); the panel is subagents where a tool has them, an inline lens-sweep
  otherwise. Installs by folder copy like every skill.
- **Opinionated:** the mechanical gate is **un-bypassable** (a RED gate is `NOT READY` regardless of
  the review); the verdict is one word plus blocking reasons; design disagreements escalate to
  `council-review` rather than being adjudicated in the verdict.
- **Category:** Dev workflow (with `feature-implement-loop`, `devils-advocate`, `council-review`).

## Proposal

**New skill `pre-merge-review`** — gate an existing change with one command:
1. **Mechanical gate first (#2).** `scripts/gate.py` runs the project's lint/typecheck/test and
   **exits non-zero if any fail** — the pass/fail is a script's exit code, not a judgment. A RED gate
   is an automatic `NOT READY`; the review can add blockers but never clears a failing gate.
2. **Reviewer panel (#1).** Dispatch `devils-advocate` + `security-reviewer` + `code-quality` in
   parallel (inline three-lens sweep on tools without subagents); merge and de-dupe findings.
3. **Verdict.** `READY` only if the gate is GREEN and no 🟥 blocker / 🟧 major stands.

**`feature-implement-loop` gate hardened (#2 in the loop).** Step 5 now *runs* the project's verify
(tests + lint/typecheck) and honors the exit code — a red command is an automatic gap, not a
judgment call; it may not report `VERIFIED` while any command is red. The dedicated gate *script*
lives in `pre-merge-review`; the loop uses the same discipline inline (skills install à la carte, so
the loop can't depend on another skill's script).

Anti-patterns this bans: declaring `READY` on a red gate; skipping the deterministic pass and "just
reviewing"; adjudicating a design debate inside the verdict.

## Alternatives considered

- **Enhance `feature-implement-loop` only.** Rejected — it generates and loops; wedging a
  review-an-existing-diff mode into it conflates two entry points. A separate skill is the honest fit,
  and the loop still gets the #2 gate hardening.
- **Make the gate a git pre-commit hook** (skilldrop's hook mechanism). Rejected as the *primary*
  form — RFC-0006 hooks are reminders, not blocking execution, so they wouldn't enforce anything. A
  script's exit code is the portable mechanical gate; the skill notes wiring `gate.py` into a git hook
  as the strongest (commit-time-blocking) option for those who want it.
- **A review skill with no mechanical gate.** Rejected — that's just the panel; the un-bypassable gate
  is the whole point of closing difference #2.
- **Harness-enforced gates like `work-loop`.** Out of scope — skilldrop skills are portable
  instruction files, not a harness. A deterministic gate *script* the skill must run and honor is as
  mechanical as a tool-agnostic skill can be, and the honest limit is documented.

## Decision

Accepted and implemented: `skills/pre-merge-review/` (SKILL.md + `scripts/gate.py` + worked-example
oracle + evals), added to the `dev-team` pack, `model-routing.json`, and the README (skill count →
51); `feature-implement-loop`'s gate hardened to run-and-honor the verify. skilldrop now ships the
full production-grade loop: `feature-implement-loop` (generate → panel → gate → loop) and
`pre-merge-review` (mechanical gate → panel → verdict), with `council-review` above both.

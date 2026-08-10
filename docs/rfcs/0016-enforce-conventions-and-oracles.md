---
rfc: 0016
title: Enforce stated conventions and require heavy-tier oracles
status: implemented
date: 2026-08-03
author: sananthanarayan
---

# RFC-0016: Enforce stated conventions and require heavy-tier oracles

## Problem / use case

Follow-on to RFC-0015. The same QA that motivated it surfaced two more instances of the
"doc asserts a rule the tooling doesn't back" failure class — this time inside skilldrop's own
`AGENTS.md`:

- **Golden rule 7** states *"Both [`Quality bar` and `Anti-patterns to avoid`] are enforced by the
  Before you commit checklist below"* — but the checklist is a manual `- [ ]`, and `validate.py`
  never checked for those headings. The claim of enforcement was false (the exact pack-shell.md
  finding from the QA, in skilldrop form). All 50 current skills happen to comply — by discipline.
- **The scripts-portability rule** (`AGENTS.md`: reference scripts with *both* `${CLAUDE_SKILL_DIR}/…`
  and a plain `scripts/…`) is a hard "must," also unchecked.
- **The behavioral gap:** `validate.py` enforces a rich *structural* contract but nothing about
  *output quality*. skilldrop already ships `evals/` (activation) and `examples/` (input→output) —
  but only 10/50 skills carry an `examples/` oracle, and 5 of the 9 **heavy**-tier skills (the ones
  the repo itself classifies as adversarial/weighted-judgment) had none. The judgment-heavy skills,
  which benefit most from a golden "here's what a passing output looks like," were the least covered.

## Fit check (structural change)

Golden rules touched, and why they hold:

- **Golden rule 7 is now *actually* enforced**, not merely asserted — the change makes the doc honest.
  No skill changes shape; all 50 already have both headings.
- **No new authoring burden retroactively.** The heading and script-dual-reference checks pass on the
  current 50 unchanged. The heavy-tier `examples/` requirement is satisfied for all 9 heavy skills by
  adding 5 oracles here; future heavy skills must ship one (a proportionate bar — heavy tier is
  reserved for real judgment work).
- **Model-routing tier stays the single source of "how much judgment."** The oracle requirement keys
  off the existing `heavy` tier, not a new classification.

## Proposal

**Enforcement (added to `validate.py`, no new tool):**

1. **`## Quality bar` + `## Anti-patterns` sections required** (FAIL) — golden rule 7, now real.
2. **Script dual-referencing** (FAIL) — a skill with `scripts/` must cite both the
   `${CLAUDE_SKILL_DIR}/scripts/…` and the plain `scripts/…` form so non-Claude IDEs resolve them.
3. **Heavy-tier oracle** (FAIL) — a `heavy`-tier skill must ship at least one `examples/` input→output
   file. This is the *behavioral* contract that complements the structural one.

**Content:** five oracles authored for the heavy-tier gaps — `devils-advocate`, `doc-critique`,
`tech-comparison-matrix`, `strategy-analysis`, `business-case` — each a realistic input → a golden
output that demonstrates that skill's own `Quality bar` (placeholder data only, golden rule 5).

**Doc honesty (`AGENTS.md`):** golden rule 7's claim corrected to "enforced by `validate.py`"; the
`validate.py` enumeration and the tier rule-of-thumb updated; and a paragraph added after the
Before-you-commit checklist that names exactly which items are **machine-enforced** vs **human
judgment** — with the standing instruction that a rule which becomes mechanically checkable moves
into `validate.py` rather than staying a checklist claim. (`examples/` linking is clarified as
discovered-by-convention, consistent with RFC-0015's orphan check, which scopes to material files.)

Each check was verified to pass on the current tree and to fire on an injected violation.

## Alternatives considered

- **Warn instead of fail on the heavy-tier oracle.** Loses — after adding the 5, the check is clean,
  and a warning would let the next heavy skill ship without the behavioral contract (the drift the
  rule exists to stop). Consistent with the README-count and RFC-0015 checks being FAILs.
- **Require `examples/` for *every* skill.** Rejected — a mechanical light-tier extractor doesn't need
  a golden oracle; forcing 40 would produce low-value filler. Heavy tier is the principled scope.
- **Require `evals/` presence too.** Rejected here — 40/50 skills lack `evals/`; making it a FAIL would
  break the tree. `evals/` stays recommended-for-new-skills and shape-checked when present.
- **Leave golden rule 7 as a checklist claim.** Rejected — it was demonstrably false, and the whole
  point of `validate.py` is that the contract is checked, not trusted.

## Decision

Accepted and implemented in `validate.py` + `AGENTS.md`, with five heavy-tier oracles added. The
current catalogue passes clean; every future heavy-tier judgment skill now ships a behavioral oracle,
and `AGENTS.md`'s enforcement claims match what the lint actually does.

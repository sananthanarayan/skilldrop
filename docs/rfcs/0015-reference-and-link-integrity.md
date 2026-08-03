---
rfc: 0015
title: Reference and link integrity checks
status: accepted   # draft → accepted | rejected → implemented
date: 2026-08-03
author: sananthanarayan
---

# RFC-0015: Reference and link integrity checks

## Problem / use case

A QA pass on a sibling catalogue (agent-ready-repo's `catalogue-curation` skills) surfaced a
recurring failure mode that had nothing to do with logic: **the contract between what a doc says
and what is actually on disk was not machine-checked.** A skill named a SAST tool the repo no
longer used; a reference asserted a file "won't validate" when it did; procedure lived only in a
support doc the operator never opened. skilldrop's differentiator is that `validate.py` already
machine-checks that contract — name/description drift, `related` symmetry, pack membership,
model-routing tiers, README counts. But it did **not** check three things skilldrop passes only
*by discipline*: that a `SKILL.md`'s own `scripts/`/`references/`/`${CLAUDE_SKILL_DIR}/…` paths
resolve, that long-form material is actually linked from `SKILL.md` (AGENTS.md already *states*
this rule), and that prose markdown links don't dangle. A scan found skilldrop clean on the first
and third, and **one** already-latent violation of the second (`council-review/reference.md` was
orphaned — present but never linked). This RFC converts all three from "true by discipline" to
CI-enforced invariants.

## Fit check (structural change)

Golden rules touched, and why they hold:

- **AGENTS.md golden rule "spill into `reference.md`/`templates/`/… and always reference them from
  `SKILL.md`."** This RFC *enforces* that rule (the orphan check), rather than changing it. It was
  previously stated but unchecked.
- **No new authoring burden / no skill-anatomy change.** Nothing about a skill's shape changes; the
  checks only assert that references already written resolve and are linked. The current 50 skills
  pass unchanged (after linking the one orphan).
- **No false-positive tax.** The repo is template-heavy (AGENTS.md ships a `SKILL.md` scaffold with
  illustrative `[reference.md](reference.md)` links; skills carry `{placeholder}` templates). The
  checks skip fenced code blocks, lines carrying a `{…}` token, and placeholder targets
  (`{}`, `<>`, `...`) — the exact false positives a naive scan hits — so illustrative content never
  fails the lint.

## Proposal

Three checks added to `validate.py` (no new file, no new tool; runs in the same CI lint):

1. **Reference integrity (FAIL).** Every in-skill path a `SKILL.md` names —
   `(scripts|references|templates|lenses|rubrics|assets|examples)/…` and `${CLAUDE_SKILL_DIR}/…` —
   must resolve to a real file in the skill. Fenced blocks and placeholder targets are skipped.
2. **Orphaned material (FAIL).** Every `reference.md`, `references/*.md`, `lenses/*.md`,
   `rubrics/*.md` in a skill must be linked from its `SKILL.md`. (Scoped to long-form *material*;
   `templates/`, `examples/`, and helper `scripts/` are intentionally out — a paste-able template,
   an illustrative example, or an imported `_helper.py` submodule is legitimately unlinked.)
3. **Link integrity (FAIL).** Prose markdown links across `skills/**`, `agents/`, `docs/**`, and the
   root convention docs (README, AGENTS, CLAUDE, CONTRIBUTING, SECURITY, MODEL-ROUTING) must resolve.
   Same fence/placeholder/`{…}`-line skips.

Each check was verified to (a) pass on the current tree and (b) actually fire on an injected
violation. `council-review/reference.md` is linked from its `SKILL.md` in the same change.

Anti-patterns this bans: a `SKILL.md` that names a moved/renamed `scripts/` or `references/` file
(the agent-ready-repo SAST-drift failure, in skilldrop form); a support file that ships orphaned and
drifts unread; a dead relative link in any doc.

## Alternatives considered

- **Do nothing / keep it a discipline.** Loses — the QA showed this class of drift is exactly what
  slips through human review, and skilldrop already had one latent orphan. The whole point of
  `validate.py` is that the doc↔reality contract is checked, not trusted.
- **A separate link-check tool / CI action** (e.g. a markdown-link-checker dependency). Loses — it
  adds a dependency and a second CI entry point, and a generic checker false-positives on the repo's
  template content. A ~30-line stdlib check inside `validate.py` fits the zero-dependency norm and
  reuses the one lint entry point CI already runs.
- **Warn instead of fail.** Loses — a dangling reference or orphan is a defect, not a style nit; a
  warning would accumulate the same drift the check exists to prevent (cf. the README-count FAIL).

## Decision

Accepted and implemented in `validate.py` (RFC-0015). The three checks run in the existing
`python3 validate.py` CI lint; the current catalogue passes clean, and `council-review`'s orphaned
`reference.md` is now linked.

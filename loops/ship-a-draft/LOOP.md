---
name: ship-a-draft
description: Take raw mess to a stakeholder-ready artifact by wrapping any skilldrop generator in the two passes either side of it — structured intake before, critique and machine-residue scrub after. Use when the user has notes, a transcript, or a ticket and wants a finished document rather than a first draft.
---

# ship-a-draft

A **wrapper**, not a lifecycle loop. Its centre stage is whichever generator the user actually
needs — an ADR, a design doc, a runbook, a deck, an exec summary. The wrapper contributes the
two passes every generator otherwise leaves to chance: collect the input properly before, and
check the argument and the surface after.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `intake` | generate | [`brief-intake`](../../skills/brief-intake/SKILL.md) | — |
| 2 | `draft` | generate | any generator (`*`) | — |
| 3 | `critique` | verify | [`doc-critique`](../../skills/doc-critique/SKILL.md) | **G4** review |
| 4 | `polish` | verify | [`output-hygiene`](../../skills/output-hygiene/SKILL.md) | — |

## How to run this wrapper

1. **Pick the generator first.** The brief is shaped *for a target*, so `draft` is chosen
   before `intake` runs, not after. `brief-intake`'s own routing table maps trigger phrases to
   targets; use it.
2. **Collect once.** Run `brief-intake`. Every field is tagged `[explicit]` / `[implied]` /
   `[inferred]` / `[missing]`, and its "Missing for downstream" section predicts what the
   chosen generator will refuse to start without. Resolve those before drafting.
3. **Draft.** Run the chosen generator on the brief. It is a normal skilldrop skill with its
   own quality bar — this wrapper does not override it.
4. **Critique at G4.** Run `doc-critique`, which dispatches to the same rubric the generator
   was held to. `MAJOR REWRITE` returns to `intake` (not to `draft` — a rewrite usually means
   the input was wrong, not the prose). `WRONG ARTIFACT` leaves the wrapper entirely.
5. **Polish last.** Run `output-hygiene` only once the argument is settled. It is a surface
   pass; running it on a draft that is about to be rewritten wastes it.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). G4 emits the critique
vocabulary. `SHIP WITH CHANGES` carries its changes forward to `polish`; it does not mean the
changes are optional.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and say the stage ran degraded. Do not skip G4 — an unreviewed artifact is the failure
mode this wrapper exists to prevent.

## Quality bar

- **The generator is chosen before intake runs.** A brief collected for no particular target is a summary, and downstream will reject it for missing fields.
- **`polish` runs after the argument is settled, never before.** Scrubbing prose that is about to be rewritten is wasted work and hides the rewrite.
- **A `[missing]` tag is resolved or stated, never silently filled.** Fabricating a goal, an owner, or a decision corrupts every downstream artifact.
- **Every run ends by naming what was not touched.** `output-hygiene`'s "Not touched" section is part of the deliverable, not an appendix.

## Anti-patterns to avoid

- ❌ **Running `polish` as the whole review.** Clean prose with a broken argument still fails; that is what G4 is for.
- ❌ **Skipping `intake` because the input "is already structured."** A Slack thread that looks organized is still untagged — nobody downstream can tell what was inferred.
- ❌ **Looping `critique` → `draft` instead of `critique` → `intake`.** Re-drafting from the same incomplete brief reproduces the same gaps with new words.
- ❌ **Treating `WRONG ARTIFACT` as a severe `MAJOR REWRITE`.** It is a redirect: the user wanted a different document, and revising this one cannot get there.

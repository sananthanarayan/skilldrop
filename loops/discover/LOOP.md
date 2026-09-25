---
name: discover
description: Take raw signal — interviews, journeys, a strategy question — to a requirement a human has ratified, so design starts from an agreed problem rather than an assumed one. Use when the user is deciding what to build, scoping a feature, or turning stakeholder conversations into requirements.
---

# discover

The first loop of the lifecycle, and the cheapest one to run twice. Everything downstream
inherits whatever this loop got wrong, which is why it ends at a **human** gate rather than a
script: no check can tell you that you solved the wrong problem well.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `gather` | generate | [`requirements-interview`](../../skills/requirements-interview/SKILL.md), [`user-journey-map`](../../skills/user-journey-map/SKILL.md), [`strategy-analysis`](../../skills/strategy-analysis/SKILL.md) | — |
| 2 | `structure` | generate | [`brief-intake`](../../skills/brief-intake/SKILL.md) | — |
| 3 | `specify` | generate | [`prd-draft`](../../skills/prd-draft/SKILL.md) | — |
| 4 | `ratify` | gate | [`doc-critique`](../../skills/doc-critique/SKILL.md) | **G0** human |

## How to run this loop

1. **Gather from whichever direction the signal arrives.** A stakeholder conversation →
   `requirements-interview`. An existing experience with known friction → `user-journey-map`.
   An open strategic question → `strategy-analysis`. Run one; running all three on the same
   input produces three views of the same thing and no more information.
2. **Structure once.** `brief-intake` tags every field `[explicit]` / `[implied]` /
   `[inferred]` / `[missing]` with verbatim quotes. The tags are the deliverable — an
   untagged brief hides which parts are somebody's assumption.
3. **Resolve the missing before specifying.** `brief-intake` ends with what the downstream
   skill will refuse to start without. Answer those; do not let `prd-draft` invent them.
4. **Specify.** `prd-draft` turns the brief into numbered requirements a design can be held to.
5. **Ratify at G0.** Run `doc-critique` against the PRD, then put the decision to a human.
   The critique informs; the human decides. `REVISE` returns to `structure`, not to `specify`
   — a weak PRD almost always means a thin brief.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). G0 emits `PROCEED`,
`PROCEED WITH CONDITIONS`, `REVISE`, `RECONSIDER`, or `BLOCKED`. `RECONSIDER` leaves the loop:
the problem itself is wrong, and no amount of re-briefing fixes that.

## Non-interactive runs

With no human present, G0 cannot be satisfied. Emit `BLOCKED: need ratification of <the
brief's central claim>` and stop. Do not self-ratify — a fabricated goal corrupts every
artifact the other four loops produce.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. Never skip G0.

## Quality bar

- **Every field carries a provenance tag.** A brief that does not distinguish quoted from inferred cannot be ratified, only believed.
- **`[missing]` is resolved or stated, never filled.** Inventing the goal, the customer, or the success measure is the one failure this loop exists to prevent.
- **The requirements are numbered and testable.** "Fast" is not a requirement; a latency target is.
- **A human ratifies before design starts.** G0 is the loop's only reason to exist — an unratified brief is a draft, whatever the critique said.

## Anti-patterns to avoid

- ❌ **Running all three `gather` skills to be thorough.** Three lenses on one input is not three inputs; pick the one that matches where the signal came from.
- ❌ **Letting `prd-draft` fill a `[missing]` field.** That converts an open question into a fact nobody agreed to.
- ❌ **Treating `doc-critique`'s `SHIP IT` as ratification.** The critique judges the document; G0 judges the problem.
- ❌ **Returning `REVISE` to `specify`.** Re-writing the PRD from the same thin brief reproduces the same gaps in better prose.

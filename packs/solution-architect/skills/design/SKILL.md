---
name: design
description: Take a ratified requirement to a recorded architectural decision — constraints, structure, diagrams, threats, then a panel that must agree before the decision is written down. Use when the user is designing a system, choosing an architecture, or asking how something should be built.
---

# design

The loop with the worst reversibility profile in the repo. A discovery mistake costs a
re-brief; a design mistake surfaces months later, in code nobody wants to unwind. That is why
its gate is a **panel** — independent positions, surfaced cruxes, recorded dissent — and not
a script, and why the decision is recorded only *after* the panel agrees.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `constrain` | generate | [`nfr-spec`](../../skills/nfr-spec/SKILL.md) | — |
| 2 | `shape` | generate | [`design-doc`](../../skills/design-doc/SKILL.md), [`architecture-diagrams`](../../skills/architecture-diagrams/SKILL.md) | — |
| 3 | `threat` | verify | [`threat-model`](../../skills/threat-model/SKILL.md) | — |
| 4 | `ratify` | gate | [`council-review`](../../skills/council-review/SKILL.md) | **G1** review |
| 5 | `record` | generate | [`adr-generator`](../../skills/adr-generator/SKILL.md) | — |

## How to run this loop

1. **Constrain before shaping.** `nfr-spec` first, always. A design produced before its
   quality targets exist gets judged on taste, and taste does not survive a review panel.
2. **Shape prose and picture together.** `design-doc` and `architecture-diagrams` are one
   artifact in two renderings. A diagram that disagrees with the doc is a defect in both.
3. **Attack it before ratifying.** `threat-model` consumes the design directly. Running it
   after G1 means the panel ratified something nobody had attacked.
4. **Ratify at G1.** `council-review` seats the standing panel, takes positions *before*
   cross-talk, names the cruxes, and records dissent with "what would change our mind".
   `REVISE` returns to `shape`. `SPLIT` and `RECONSIDER` leave the loop.
5. **Record last.** `adr-generator` writes the decision *after* it is a decision, with the
   rejected options and the reasoning that killed them. An ADR written before G1 is a proposal
   wearing an ADR's clothes.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). `PROCEED WITH
CONDITIONS` is the common outcome and the most abused: the conditions are part of the
decision, and `record` must carry them into the ADR.

## Non-interactive runs

`council-review` can be run by an agent seating the panel itself, so G1 is satisfiable without
a human. `SPLIT` is not — a genuine unresolved split needs a person. Emit
`BLOCKED: need a decision-maker for <the crux>` and name the positions.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version, and record
the stage as degraded. If `council-review` is missing, do not skip G1 — run the panel inline
from the design's own quality attributes and say the seating was improvised.

## Quality bar

- **Quality targets exist before structure does.** `nfr-spec` is stage 1 because a design without numbers can only be argued about.
- **The ADR names what was rejected and why.** A decision record with one option is a description of what happened, not a decision.
- **Dissent is recorded, not resolved away.** A panel that always reaches consensus is not seating real positions.
- **The diagram and the doc say the same thing.** They are checked against each other before G1, not after someone builds from the wrong one.

## Anti-patterns to avoid

- ❌ **Writing the ADR before G1.** It pre-commits the panel to a decision it has not made, and every reviewer can feel it.
- ❌ **Running `threat-model` after ratification.** The panel then ratified an unattacked design, which is the failure this ordering exists to prevent.
- ❌ **Treating `PROCEED WITH CONDITIONS` as `PROCEED`.** The conditions must reach the ADR; dropping them is how a conditional approval silently becomes unconditional.
- ❌ **Skipping `constrain` because the NFRs are "obvious".** Obvious targets are the ones nobody writes down and everybody remembers differently.

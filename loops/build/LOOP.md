---
name: build
description: Take an agreed requirement to merged code through a capped generate-verify-gate loop, with a mechanical gate that decides and a human who owns the merge. Use when the user wants to implement a story, fix a triaged bug, or ask whether a change is safe to merge.
---

# build

The repo-scope loop: a requirement enters, merged code leaves, and nothing crosses a stage
boundary without passing that stage's gate. This loop *sequences* skills — it never contains
one. Every skill named below stays independently installable and runnable on its own.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `shape` | generate | [`user-story-splitter`](../../skills/user-story-splitter/SKILL.md), [`bug-triage`](../../skills/bug-triage/SKILL.md) | — |
| 2 | `implement` | generate | [`feature-implement-loop`](../../skills/feature-implement-loop/SKILL.md) | — |
| 3 | `verify` | verify | [`pre-merge-review`](../../skills/pre-merge-review/SKILL.md) | **G2** mechanical |
| 4 | `decide` | gate | [`council-review`](../../skills/council-review/SKILL.md) | **G2.1** human |

## How to run this loop

1. **Establish the unit of work.** New capability → `user-story-splitter`. Reported defect →
   `bug-triage`. The stage is done when there is one vertical slice with acceptance criteria a
   test can assert. Vague criteria are the single largest cause of a wasted round 3.
2. **Implement.** Hand the slice to `feature-implement-loop`, which runs its own capped
   generate-challenge-gate cycle internally. Do not re-implement its rounds here — this loop's
   `cap` governs returns from G2, not the inner skill's rounds.
3. **Verify at G2.** Run `pre-merge-review`. Its script decides and its panel explains:
   `python3 skills/pre-merge-review/scripts/gate.py`. The exit code is the verdict —
   `READY`, `NOT READY`, or `BLOCKED`.
4. **Honour the gate.** `NOT READY` returns to `implement`, up to `cap` (3) times. On the
   third return, stop looping and emit `BLOCKED` naming what did not converge. Never edit the
   gate to make it pass.
5. **Decide at G2.1.** The merge is a human's. Escalate design disagreements surfaced at G2 to
   `council-review` rather than arguing them inside the diff; `RECONSIDER` and `SPLIT` both
   leave this loop rather than revising within it.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). G2 emits
`READY` / `NOT READY` / `BLOCKED`. G2.1 emits the council vocabulary. A `revise`-class verdict
returns to the stage named in `revise_to`; a `redirect`-class verdict leaves the loop.

## When a stage's skill is not installed

Skills install à la carte, so a stage may name a skill the target environment does not have.
Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that the stage ran degraded. A missing skill is never a reason to skip a
**gate** — the gate is the loop's whole value.

## Quality bar

- **The gate decides, not the agent.** G2's verdict is `gate.py`'s exit code. An agent that reasons its way past a red gate has broken the loop, not passed it.
- **The cap is honoured.** Three returns to `implement`, then `BLOCKED` with what did not converge. A fourth round is a defect in this loop, not diligence.
- **Every stage leaves evidence.** Each stage names its skill, its verdict, and its round number, so the run is auditable after the fact rather than asserted.
- **Acceptance criteria exist before `implement` starts.** A slice whose criteria a test cannot assert is not shaped; return it to `shape`.

## Anti-patterns to avoid

- ❌ **Calling a skill from inside a skill to "continue the loop."** The loop sequences; skills do not chain. This is what keeps every skill portable to Cursor, Kiro, and Aider.
- ❌ **Editing `gate.py`, its config, or a test to turn G2 green.** That converts a mechanical gate into a decorative one.
- ❌ **Treating `PROCEED WITH CONDITIONS` as `PROCEED`.** The conditions travel with the artifact; dropping them is how conditional approvals become unconditional ones.
- ❌ **Running `decide` for every change.** G2.1 exists for escalated disagreement and the merge itself, not as a ceremony on top of a green gate.
- ❌ **Starting at `implement` because the story "is obvious."** Unshaped work is what produces a diff nobody can review against anything.

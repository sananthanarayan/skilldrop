---
name: adopt
description: Take an organisation from a pile of AI ideas to a first rollout wave its sponsor approved: the use cases ranked with a first slice, readiness scored against that slice, a usage policy covering the data the slice touches, and a cohort rollout whose first wave is the slice's users, with a gate that sends the slice back when a blocking gap stands in its way. Use when the user says "help us start using AI", "roll out AI across the team", "run the adopt loop", or has AI ideas, no policy and no rollout plan.
---

# adopt

One first slice, from a list of ideas to a wave of people using it. The four skills each work
alone; in order, each one narrows the next. Triage picks one use case, so readiness is scored
against what that use case needs instead of against the whole organisation. Readiness names the
gaps, so the policy covers the data the slice really touches. The rollout's pilot is the slice's
own users, and its adoption gate is the observable triage said would prove or kill the slice.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `triage` | generate | [`ai-use-case-triage`](../../skills/ai-use-case-triage/SKILL.md) | — |
| 2 | `readiness` | verify | [`ai-readiness-assessment`](../../skills/ai-readiness-assessment/SKILL.md) | **G11** review |
| 3 | `policy` | generate | [`ai-usage-policy`](../../skills/ai-usage-policy/SKILL.md) | — |
| 4 | `rollout` | generate | [`ai-adoption-rollout`](../../skills/ai-adoption-rollout/SKILL.md) | — |
| 5 | `sign-off` | gate | [`doc-critique`](../../../core/skills/doc-critique/SKILL.md) | **G11.1** human |

## How to run this loop

1. **Triage the ideas.** Run `ai-use-case-triage` on whatever the person brought: a brainstorm,
   a backlog, interview notes. Save it as `triage.md`. Carry three things from it into every
   later stage: the first slice (one workflow and the people who do it), the observable that
   proves or kills it, and the time box.
2. **Score readiness for the slice.** Run `ai-readiness-assessment` scoped to the slice's team
   and the decision "can this slice start". Each dimension is read against what the slice
   needs: Data is the data the slice reads, Tooling is the tool the slice uses, Process is the
   review step the slice's output passes through. Save it as `readiness.md`.
3. **Judge the slice at G11.** Ask three questions, then choose the verdict below:
   - Does any gap the assessment ranks as blocking sit on something the slice needs?
   - Can each remaining gap be closed inside the slice's time box, with an owner role named?
   - Is there a review step where a person checks the slice's output before anyone acts on it?
4. **On `REVISE`, change the slice, not the scores.** Return to `triage` with the blocking gap
   as a constraint, and pick the highest-ranked candidate that does not need what is missing.
   The not-yet list's promotion conditions say which one. Each return counts against the cap.
5. **Write the policy for the slice's data.** Run `ai-usage-policy` for the slice's people,
   naming every kind of data the slice puts into a tool (from triage and the Data line of
   readiness). Every kind of data the slice touches gets a rule; a rule for data the slice
   never touches stays out of this version. Save it as `policy.md`.
6. **Plan the rollout from the slice.** Run `ai-adoption-rollout` with the slice's users as the
   pilot cohort and triage's observable as the pilot's adoption gate. G11's conditions become
   preconditions the pilot cannot open without. Save it as `rollout.md`.
7. **Ask the sponsor at G11.1.** Run `doc-critique` over the policy and the rollout together,
   then put the first wave, the conditions and the critique's open findings to the person who
   sponsors the slice. Only they choose the verdict. In a non-interactive run, stop here and
   write the decision they need to make; never record their verdict for them.
8. **Hand over the plan, then the verdict.** Lead with the slice, who starts using it and when,
   and what would end it. The scorecard, the policy and the cohort plan go underneath. Close
   with each gate on its own line, `G11: <VERDICT>` and `G11.1: <VERDICT>` (or
   `G11.1: awaiting <role>`), and one sentence of reasons.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G11 emits:

- `PROCEED`: no blocking gap sits on what the slice needs, and its output has a review step.
- `PROCEED WITH CONDITIONS`: a gap sits on the slice but can close inside the time box, with
  an owner role. Each condition travels into the rollout as a precondition for the pilot.
- `REVISE`: a blocking gap sits on the slice and won't close inside the time box. Return to
  `triage` with that gap as a constraint.
- `RECONSIDER`: the gap blocks every candidate, such as no rule for what may go into any tool
  or no tool access at all. Fixing it is the work, so the loop ends here with that gap's first
  action and owner role.
- `BLOCKED`: no candidates to triage, or no team the slice belongs to.

G11.1 emits `PROCEED`, `PROCEED WITH CONDITIONS`, `REVISE` (back to `policy`, when the sponsor
rejects a rule or a cohort) or `BLOCKED` (no sponsor named).

On the cap-th `REVISE` at G11, emit `RECONSIDER`: three slices in a row hit blocking gaps, so
the gaps are the work.

## Non-interactive runs

With no candidates, `ai-use-case-triage` emits `BLOCKED`; carry it through as the loop's
verdict and run no further stages. Missing weights and readiness evidence degrade to the
skills' own `[assumption]` and `[insufficient evidence]` tags. G11.1 always stops at the
sponsor: write `G11.1: awaiting <role>` with the decision they face, never a verdict.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `readiness` still scores Data, Tooling,
Governance and Process against the slice with an evidence line each, because G11 can't be
judged without them. Never skip G11 or G11.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-11-03T10:15:00Z","loop":"adopt","stage":"readiness","gate":"G11","verdict":"REVISE","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never the use cases, the scores or the policy.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **Readiness is scored against the slice.** An organisation-wide score hides the one gap that stops the slice and flags gaps that stop nothing yet.
- **A `REVISE` changes the slice.** It never re-scores a dimension upward to let the same slice through.
- **The policy covers every kind of data the slice touches,** each restriction with what to do instead.
- **The pilot is the slice's users, and its adoption gate is triage's observable.** A pilot of volunteers from elsewhere proves nothing about the slice.
- **G11.1 is the sponsor's call.** The loop writes the decision they face; it never records their verdict.

## Anti-patterns to avoid

- ❌ **Scoring the whole company's readiness first.** The assessment then ranks gaps by how bad they look, not by what they block.
- ❌ **Writing a policy for every tool and every kind of data before anything ships.** It is long, it is late, and nobody reads the part that matters to the pilot.
- ❌ **Passing G11 with a blocking gap and a promise.** A gap that won't close inside the time box is a `REVISE`, however good the slice looks.
- ❌ **A pilot gate that is "the pilot went well".** The gate is triage's observable, with its threshold and time box.
- ❌ **Running all four skills before the first gate.** A policy and a rollout written for a slice that then fails G11 are thrown away.

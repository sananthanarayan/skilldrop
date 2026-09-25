---
name: operate
description: Take a shipped service through detection, response, and learning — instrument it, write the runbook, communicate the incident, then feed the postmortem's deltas back into the runbook. Use when the user is preparing to run a service, is in an incident, or is writing a postmortem.
---

# operate

The only loop whose failures are **irreversible and live**. The other four can be re-run at
the cost of time; this one runs while real users are affected. Its feedback edge is the point:
`postmortem-generator` emits runbook deltas phrased as edits, and those go straight back into
`document`. An incident that changes no procedure has not been learned from.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `instrument` | generate | [`observability-plan`](../../skills/observability-plan/SKILL.md) | — |
| 2 | `document` | generate | [`runbook-generator`](../../skills/runbook-generator/SKILL.md) | — |
| 3 | `respond` | generate | [`incident-comms`](../../skills/incident-comms/SKILL.md) | — |
| 4 | `learn` | verify | [`postmortem-generator`](../../skills/postmortem-generator/SKILL.md) | **G3** human |

## How to run this loop

1. **Instrument first.** `observability-plan` decides what is measured and what pages a human.
   You cannot respond to what you never detected, and you cannot write a runbook entry for an
   alert that does not exist.
2. **Write the runbook per alert.** Each alert the previous stage defined maps to a
   `runbook-generator` entry. An alert with no procedure wakes someone who then has to think.
3. **Respond to the audience the incident actually has.** `incident-comms` is staged —
   detect, mitigate, resolve — and the stage determines the message. Writing a resolution
   update during mitigation is the most common error here.
4. **Learn at G3.** `postmortem-generator` analyses blamelessly and ends with runbook deltas.
   A human signs off that the incident is closed. `REVISE` returns to `document`: the deltas
   are the loop's output, and applying them is what closes it.

Entering mid-loop is normal and expected. An incident starts at `respond`; a new service
starts at `instrument`. Do not replay earlier stages for their own sake.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). G3 emits `PROCEED`,
`PROCEED WITH CONDITIONS`, `REVISE`, or `BLOCKED`. `PROCEED WITH CONDITIONS` means the
incident is closed but named follow-ups are outstanding — they travel with the postmortem.

## Non-interactive runs

Never fabricate incident facts — timings, impact, customer counts, root cause. When the
timeline is incomplete, emit `BLOCKED: need <the missing facts>` and name them. A confident
postmortem built on guessed impact is worse than no postmortem.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version, and record
the stage as degraded. During a live incident, prefer the degraded inline version over
stopping to install anything.

## Quality bar

- **Every alert has a runbook entry.** An alert that pages someone with no procedure is an interruption, not a signal.
- **The postmortem ends in runbook deltas.** Analysis with no procedural change is a story about an outage.
- **Comms match the incident's actual stage.** Detect, mitigate, and resolve have different audiences and different truths.
- **Blameless means blameless.** Naming a person is a defect in the postmortem; naming a missing guardrail is the point.

## Anti-patterns to avoid

- ❌ **Writing the runbook before the observability plan.** Procedures for alerts that do not exist, and none for the alerts that do.
- ❌ **Skipping `learn` because the incident was small.** Small incidents are where the cheap runbook deltas are.
- ❌ **Guessing impact numbers to finish the postmortem.** State the gap; a postmortem's value is entirely in its accuracy.
- ❌ **Replaying `instrument` during a live incident.** Enter at `respond`; the loop is not a checklist to complete in order.

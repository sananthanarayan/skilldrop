---
name: release
description: Take merged code to live users through a planned, reversible rollout — plan the phases and the rollback, judge readiness on evidence, draft the release notes, then a human makes the go/no-go call. Use when the user has merged a change and asks how to roll it out, whether they are ready to launch, or for a go/no-go decision.
---

# release

This loop covers the step between `build`, which ends when a human merges, and `operate`,
which assumes the service is already live. A merge can be undone with a revert. A launch that
has touched users or data often cannot be undone, so this loop gets its own gates instead of
being folded into either neighbour.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `plan` | generate | [`migration-plan`](../../skills/migration-plan/SKILL.md) | — |
| 2 | `ready` | verify | [`launch-readiness`](../../skills/launch-readiness/SKILL.md) | **G2.5** review |
| 3 | `announce` | generate | [`release-notes`](../../skills/release-notes/SKILL.md) | — |
| 4 | `go` | gate | [`council-review`](../../skills/council-review/SKILL.md) | **G2.6** human |

## How to run this loop

1. **Plan the rollout and the way back.** `migration-plan` sets out the phases, a tested
   rollback for each one, and at most one named point of no return. For a code-only change
   behind a flag, the plan can be short: the flag, the stages and how to turn it off. It still
   has to exist.
2. **Judge readiness at G2.5.** `launch-readiness` lists the change's own failure modes, then
   checks rollback, detection, response, measured targets, data and privacy, comms and
   exposure, each with evidence. `REVISE` returns to `plan`, and the report names which gap to
   close and which skill closes it. A missing rollback is `BLOCKED` on its own.
3. **Announce only once it is ready.** `release-notes` drafts the customer-facing and
   internal notes from the git range. Writing them before G2.5 risks announcing a launch that
   then does not happen.
4. **A human decides at G2.6.** The release owner decides whether to ship *now*, given
   timing, freeze windows and on-call coverage. When that decision is contested, use
   `council-review`. `RECONSIDER` means it is ready but this is the wrong time, and the work
   waits instead of going back to `plan`.

After `PROCEED`, the change is live and the work moves to `operate`. Gaps that G2.5 sent to
`observability-plan` or `runbook-generator` are the first things `operate` picks up.

## Verdicts

Defined in [`contracts/terminals.json`](../../contracts/terminals.json). G2.5 emits `PROCEED`,
`PROCEED WITH CONDITIONS`, `REVISE` or `BLOCKED`. G2.6 adds `RECONSIDER`. `PROCEED WITH
CONDITIONS` at G2.5 is allowed only when the open rows are comms or exposure. A detection or
response gap is always `REVISE`.

## Non-interactive runs

Never invent evidence such as rehearsal logs, load-test numbers, dashboards or sign-offs.
When the change being released cannot be identified, emit `BLOCKED: need <the PR, tag, or
feature name>`. G2.6 is a human gate. A headless run stops after `announce` and reports the
G2.5 verdict for a person to act on.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record the stage as degraded. For `ready`, the minimal version is the seven checks
written as a list, each marked met, not met or n/a with a reason. Skipping it is never the
minimal version.

## Quality bar

- **Rollback exists before readiness is judged.** A plan with no way back is the one thing that cannot be fixed after launch.
- **Readiness rests on evidence.** Every check links to something; "we're good" is `not met`.
- **Can and should are separate gates.** G2.5 says whether it can ship; G2.6 says whether it should ship now.
- **Detection gaps leave this loop as hand-offs.** `operate` picks them up first, rather than discovering them during the first incident.

## Anti-patterns to avoid

- ❌ **Jumping from merge to "instrument a running service".** That skips this loop entirely, which is the gap it exists to close.
- ❌ **Announcing before G2.5.** Customers hear about a launch that is then pulled.
- ❌ **Treating flag-off as a rollback without a data story.** If dual-write or a backfill has run, turning the flag off does not undo the data.
- ❌ **Letting G2.6 overrule a G2.5 `BLOCKED`.** A human can delay a ready launch; they cannot make an unready one ready by deciding to go.

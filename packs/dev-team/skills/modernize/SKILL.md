---
name: modernize
description: Replace or rewrite a legacy component without changing what it does: orient in the old code, plan the restructuring and the move, record the old system's behaviour before anything is rebuilt, rebuild in small steps, prove the new one gives the same results on the recordings, and cut over only when a person accepts the evidence. Use when the user is migrating, rewriting or porting a legacy service, batch job or module (COBOL to Java, Python 2 to 3, a monolith to a service, one framework to another), says "run the modernize loop", or asks how to replace old code without breaking what depends on it.
---

# modernize

One legacy component, replaced without changing its behaviour. Models now migrate legacy code
at scale; what they can't do on their own is show that the result behaves the same. This
loop makes that the gate. The old system's behaviour is recorded **before** any new code
exists, so the evidence can't be shaped by what was built. A script decides whether the new
component matches the recordings. Then a person decides the cutover, because only a person
can accept what the recordings don't cover and approve every intended change.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `survey` | generate | [`codebase-tour`](../../skills/codebase-tour/SKILL.md), [`context-graph`](../../../core/skills/context-graph/SKILL.md) | — |
| 2 | `plan` | generate | [`refactor-plan`](../../skills/refactor-plan/SKILL.md), [`migration-plan`](../../skills/migration-plan/SKILL.md) | — |
| 3 | `capture` | generate | [`behaviour-equivalence`](../../skills/behaviour-equivalence/SKILL.md) | — |
| 4 | `rebuild` | generate | [`feature-implement-loop`](../../skills/feature-implement-loop/SKILL.md) | — |
| 5 | `prove` | verify | [`behaviour-equivalence`](../../skills/behaviour-equivalence/SKILL.md) | **G10** mechanical |
| 6 | `cutover` | gate | [`launch-readiness`](../../skills/launch-readiness/SKILL.md) | **G10.1** human |

## How to run this loop

1. **Survey the boundary.** Run `codebase-tour` on the component being replaced. The tour
   must end with the boundary it will be swapped at (an HTTP API, a function signature, a
   batch file, a queue) and every caller and side effect that crosses it, each cited to a
   file. A boundary nobody can name means the component isn't ready to be replaced.

   Then run `context-graph` on the same component, with git history. It finds the recorded
   decisions that govern it: why it was built this way, what was tried before, and the
   constraints the rewrite must keep. It also finds where the code has changed since those
   decisions were made, and who changed it. Carry every constraint a current decision sets
   into `plan`. A behaviour the old code has that contradicts its decision is a question for
   the owner before `capture`: record it as it is, and ask whether the rewrite should keep it.
   Each person who changed the code since the decision is worth asking what the records don't
   say.
2. **Plan the work.**
   - Restructuring the code in place → `refactor-plan`.
   - Moving data, a schema or a platform → `migration-plan`.
   - A rewrite usually needs both: a refactor to carve out a seam, then a migration across it.
3. **Capture before rebuilding.** Run `behaviour-equivalence` against the **old** component
   only:
   - record production-shaped inputs and the edge cases at the boundary;
   - run the old component twice on them;
   - write the normalisation rules from what differed between those two runs.

   Save `recordings/`, `rules.json` and the coverage note. Nothing from the new build may
   change these later; if they must change, that is a return to this stage.
4. **Rebuild in steps.** Hand each planned step to `feature-implement-loop`. Each step merges
   on its own, behind the boundary, with the old component still serving.
5. **Prove at G10.** Replay the recordings against the new component and compare:

   ```bash
   # Claude Code (the loop and behaviour-equivalence installed side by side)
   python3 "${CLAUDE_SKILL_DIR}/../behaviour-equivalence/scripts/golden_diff.py" old.jsonl new.jsonl --rules rules.json --accepted accepted.json
   # Other IDEs (from the folder the skills were installed into)
   python3 behaviour-equivalence/scripts/golden_diff.py old.jsonl new.jsonl --rules rules.json --accepted accepted.json
   ```

   The exit code is the verdict: `0` is `READY` (equivalent, or equivalent except the changes
   in `accepted.json`), `1` is `NOT READY`, `2` is `BLOCKED` (the recordings or rules can't
   be read). `NOT READY` returns to `rebuild` with the differences the script lists. Adding a
   normalisation rule to make a difference disappear is a return to `capture`, not a fix.
6. **Decide the cutover at G10.1.** Run `launch-readiness` for the switch itself: rollback to
   the old component, detection, the data cutover. Then show the person:
   - the G10 result;
   - what the recordings cover and what they don't;
   - every entry in `accepted.json`, with the approver each one names.

   The person decides.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json).

- G10 emits `READY`, `NOT READY` or `BLOCKED`, from the script's exit code alone.
- G10.1 emits:
  - `PROCEED`: the cutover goes ahead.
  - `PROCEED WITH CONDITIONS`: it goes ahead with named items, such as a shadow period or
    extra recordings for an uncovered input class, each with a date.
  - `REVISE`: the coverage is too thin or an intended change wasn't approved. Return to
    `capture`.
  - `RECONSIDER`: the boundary was wrong, so replacing the component this way won't work. The
    loop ends here.
  - `BLOCKED`: no person can accept the evidence, or no rollback exists.

## Non-interactive runs

With no person present, G10.1 cannot be satisfied. Run every stage through G10, deliver the
evidence, and emit `BLOCKED: need the cutover decision from <the owner>`. Never mark an
intended change as approved, and never widen a normalisation rule to reach `READY`.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. Without `behaviour-equivalence` there is no G10
script. Say so, compare the recordings field by field by hand under the same rules, and mark
G10 degraded. Never skip `capture` or G10.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-10-20T14:03:00Z","loop":"modernize","stage":"prove","gate":"G10","verdict":"NOT READY","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never recordings, code or data.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The old behaviour is recorded before the new code exists.** Recordings made after the rebuild prove only that the new code agrees with itself.
- **G10 is the script's exit code.** No difference is waved through by reading it.
- **Every normalisation rule is narrow and has a reason.** A rule added after a G10 failure goes back through `capture`.
- **Every intended change names its approver.** The person at G10.1 sees each one.
- **The coverage is stated.** The cutover decision is made knowing which input classes the proof does not reach.

## Anti-patterns to avoid

- ❌ **Recording from the new system,** or from tests written for it. The old system is the oracle.
- ❌ **Fixing a G10 failure by ignoring the field.** That hides the regression the loop exists to catch.
- ❌ **Rebuilding everything, then comparing once.** Each planned step merges on its own and is compared again.
- ❌ **Calling the migration done at G10.** Equivalence on the recordings is evidence; the cutover is a person's decision, with a rollback.
- ❌ **Skipping `survey` because the old code is "well known".** The callers and side effects nobody remembers are the ones that break.
- ❌ **Rewriting without reading the decisions behind the old code.** A constraint someone recorded years ago, such as a retention period or an ordering guarantee, is easy to drop in a rewrite and expensive to rediscover in production.

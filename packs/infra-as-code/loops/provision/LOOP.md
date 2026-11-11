---
name: provision
description: Take an infrastructure change from a described need to a Terraform apply a person approved: a module with secure defaults, a review of the real plan that names every destroy, replace, widening and out-of-scope change, and a check right before apply that the plan being applied is the one reviewed, with a gate that sends the module back when the plan would destroy state or widen access unasked. Use when the user says "write the terraform and check it before we apply", "provision this safely", "run the provision loop", or wants new infrastructure from module to apply in one pass.
---

# provision

One infrastructure change, from a need to an apply. A module with secure defaults can still
produce a plan that replaces a database, because the plan depends on the state and the
environment, not only on the code. So the loop reviews the real plan against the scope written
when the module was, and checks at apply time that nothing moved between review and apply.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `module` | generate | [`terraform-module`](../../skills/terraform-module/SKILL.md) | — |
| 2 | `plan` | verify | [`terraform-plan-review`](../../skills/terraform-plan-review/SKILL.md) | **G13** review |
| 3 | `apply` | gate | [`terraform-plan-review`](../../skills/terraform-plan-review/SKILL.md) | **G13.1** human |

## How to run this loop

1. **Write the module and the scope together.** Run `terraform-module` on the need. Beside it,
   write `scope.md`: the resource addresses this change is meant to create, change or destroy,
   and one sentence of intent. The scope is written now, before any plan exists, so the review
   can't read the plan to fit it.
2. **Get a saved plan.** The person, or you where credentials allow, runs the commands below.
   A plan printed without `-out` can't be applied as reviewed, so it doesn't count.

   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform show -json tfplan > plan.json
   ```

   Record the planfile's SHA-256 in `scope.md`. Without credentials or state, stop and say
   exactly which commands to run and what to bring back.
3. **Review the plan against the scope.** Run `terraform-plan-review` on `plan.json`, passing
   every address in `scope.md` as the intended scope. Every change outside it is listed, even
   when harmless. Save the review as `review.md`.
4. **Judge the plan at G13.** Map the review's verdict and findings to the gate:
   - `SAFE TO APPLY` with nothing out of scope is `PROCEED`.
   - `APPLY WITH CARE` is `PROCEED WITH CONDITIONS`, and the review's pre-apply checks are the
     conditions.
   - `DO NOT APPLY` caused by the code (a forced replacement, a widened rule, a missing
     `prevent_destroy`) is `REVISE`.
   - `DO NOT APPLY` caused by the change itself, such as a stateful resource that has to be
     replaced to reach the goal, is `RECONSIDER`.
5. **On `REVISE`, fix the module, then re-plan.** Return to `module` with the forcing attribute
   or the widened rule named. Re-plan from the fixed code; never edit `plan.json`. Each return
   counts against the cap.
6. **Check the apply at G13.1.** Right before apply, confirm two things:
   - the planfile's SHA-256 matches the one recorded in `scope.md`;
   - `terraform show -json tfplan` still lists the same resource changes `review.md` reviewed.

   Any difference is `REVISE` back to `plan`: re-plan and re-review. Then the person who will
   run `terraform apply tfplan` reads every destroy and replace in `review.md` and decides.
   Only they choose the verdict. Never run `terraform apply` yourself in this loop.
7. **Hand over the verdict and what apply will do.** Lead with what changes in plain words,
   what is destroyed or replaced, and the checks to do first. The review goes underneath.

## What the reply says

- **Lead with what was asked for, in plain words:** what the change does in plain words, what is destroyed or replaced, and the checks to do before apply. The review goes underneath.
- **No loop internals.** No gate id, verdict word, stage or skill name, and no path inside a
  skill folder, in the reply or in any file the person receives. Say the outcome instead:
  ✅ *"Safe to apply after one fix: the plan replaces the billing database because its engine version changed. Pin it and re-plan"* — ❌ *"G13: REVISE"*.
- **The verdict goes to the run log only,** when one is set. The reply never mentions the run
  log, whether it is set, or how the run was set up.
- **A person's decision never holds back the work.** Deliver everything up to it, then name
  the decision in one line: who makes it, and what each answer means. When the request
  already holds their decision ("the platform lead approved this plan"), record it as theirs and carry on.
- **Stop only when nothing can be made.** With an essential input missing, the first line says
  in plain words what's missing, then what you'll produce once it arrives.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G13 emits:

- `PROCEED`: every change is in scope, nothing stateful is destroyed or replaced, no access is
  widened, and no unexplained drift.
- `PROCEED WITH CONDITIONS`: in-scope replacements of stateless resources, in-place changes to
  stateful ones, or drift the plan overwrites. The review's pre-apply checks travel to G13.1.
- `REVISE`: the code causes a destroy, a replace or a widening nobody asked for. Return to
  `module`.
- `RECONSIDER`: the change can only be made by replacing state. It needs a migration with a
  backup and a rollback, not a module edit, so the loop ends here and names that work.
- `BLOCKED`: no plan to review, or a plan that errored.

G13.1 emits `PROCEED`, `REVISE` (back to `plan`, when the planfile or its changes moved) or
`BLOCKED` (no planfile, or nobody named to run apply).

On the cap-th `REVISE` at G13, emit `RECONSIDER`: the module isn't converging on a safe plan,
so the change needs a person to rethink it.

## Non-interactive runs

Missing provider or Terraform versions degrade to `terraform-module`'s `[assumption]` tags.
With no plan and no way to run one, deliver the module and the scope, and say plainly that the
review needs a saved plan, with the two commands that make one (`terraform plan -out=tfplan`,
then `terraform show -json tfplan`). Apply is always the person's: deliver the review and the
checks, and name their decision.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `plan` still lists every resource whose
actions include `delete`, every change to a security group, IAM policy or bucket policy, and
every address outside `scope.md`, because G13 can't be judged without them. Never skip G13 or
G13.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.
The reply never mentions the run log, whether or not it is set.

```bash
printf '%s\n' '{"ts":"2026-11-03T10:15:00Z","loop":"provision","stage":"plan","gate":"G13","verdict":"REVISE","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never resource names, plan contents or values.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The scope is written before the plan exists,** as resource addresses. A scope written after reading the plan covers whatever the plan does.
- **Only a saved planfile is reviewed.** A plan printed without `-out` can't be applied as reviewed.
- **Every change outside the scope is listed,** even when harmless.
- **The plan applied is the plan reviewed.** G13.1 checks the planfile's hash and its resource changes.
- **The loop never runs `terraform apply`.** The person who runs it decides at G13.1.

## Anti-patterns to avoid

- ❌ **Reviewing the module instead of the plan.** Secure code can still replace a database when the state disagrees with it.
- ❌ **Fixing a bad plan by editing plan.json.** Fix the code and re-plan.
- ❌ **Passing G13 because the destroy is "probably fine".** A stateful destroy without a confirmed backup is `DO NOT APPLY`, and the loop maps it to `REVISE` or `RECONSIDER`.
- ❌ **Applying a fresh plan after reviewing an old one.** Anything merged in between is unreviewed.
- ❌ **Treating `RECONSIDER` as a bigger `REVISE`.** A change that has to replace state is a migration; another module edit won't make it safe.
- ❌ **Gate talk in the reply.** "G9: READY, G9.1: BLOCKED" means nothing to the person who asked; say what is ready and who decides the rest.

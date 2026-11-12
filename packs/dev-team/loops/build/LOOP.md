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
| 1 | `shape` | generate | [`user-story-splitter`](../../skills/user-story-splitter/SKILL.md), [`bug-triage`](../../skills/bug-triage/SKILL.md), [`codebase-tour`](../../skills/codebase-tour/SKILL.md) | — |
| 2 | `implement` | generate | [`feature-implement-loop`](../../skills/feature-implement-loop/SKILL.md) | — |
| 3 | `verify` | verify | [`pre-merge-review`](../../skills/pre-merge-review/SKILL.md) | **G2** mechanical |
| 4 | `decide` | gate | [`council-review`](../../../core/skills/council-review/SKILL.md) | **G2.1** human |

## How to run this loop

1. **Establish the unit of work.** New capability → `user-story-splitter`. Reported defect →
   `bug-triage`. The stage is done when there is one vertical slice with acceptance criteria a
   test can assert. Vague criteria are the single largest cause of a wasted round 3. When the
   request is vague ("make the import better"), write the acceptance criteria first, mark the
   ones you assumed, and build against them; don't stop to ask unless nothing can be built. In a
   repository nobody on the change knows yet, run `codebase-tour` on the slice first: where
   the change goes, the commands that test it, and the traps, each cited to a file.
2. **Know whose change it is.** When the person asks you to build or fix something, the diff is
   yours to write. When they ask whether someone else's change is safe to merge, the diff is
   not yours: you review and report, and you leave its files as they are. A fix you find goes
   back as a suggestion or a patch file beside the review, never applied, unless they asked you
   to fix it.
3. **Implement.** Hand the slice to `feature-implement-loop`, which runs its own capped
   generate-challenge-gate cycle internally. Do not re-implement its rounds here — this loop's
   `cap` governs returns from G2, not the inner skill's rounds. Skip this stage for a review of
   someone else's change.
4. **Verify at G2.** Run `pre-merge-review`. Its script decides and its panel explains:
   `python3 packs/dev-team/skills/pre-merge-review/scripts/gate.py`. The exit code is the verdict —
   `READY`, `NOT READY`, or `BLOCKED`. Check the edges where data is lost quietly, beyond what
   the tests cover: blank or missing keys, duplicates, truncation, encoding, and rows dropped
   on error. A data-loss case the tests don't cover is a finding, even when every check is green.
5. **Honour the gate.** On your own change, `NOT READY` returns to `implement`, up to `cap` (3)
   times. On the third return, stop looping and emit `BLOCKED` naming what did not converge. On
   someone else's change, `NOT READY` is the report: the failed check, its output, and the fix
   offered. Never edit the gate to make it pass.
6. **Decide at G2.1.** The merge is a human's. A design disagreement surfaced at G2 goes to the
   person as a trade-off with the options, not argued inside the diff; `RECONSIDER` and `SPLIT`
   both leave this loop rather than revising within it. An approval already in the request is
   recorded as the approver's decision. It never lets you merge, deploy or push: say what is
   ready for them to merge.

## What the reply says

- **Lead with what was asked for, in plain words:** whether the change is ready to merge, what was fixed, and anything left for the person to decide.
- **No loop internals.** No gate id, verdict word, stage or skill name, and no path inside a
  skill folder, in the reply or in any file the person receives. Say the outcome instead:
  ✅ *"Ready to merge: lint, types and all 214 tests pass. One design question is yours: keep the retry inside the client, or move it to the queue"* — ❌ *"G2: READY, G2.1: PROCEED"*.
- **The verdict goes to the run log only,** when one is set. The reply never mentions the run
  log, whether it is set, or how the run was set up.
- **A person's decision never holds back the work.** Deliver everything up to it, then name
  the decision in one line: who makes it, and what each answer means. When the request
  already holds their decision ("approved, merge when it's green"), record it as theirs and carry on.
  Their approval is theirs to act on: say the change is ready for them to merge, and don't merge,
  deploy or push it yourself.
- **Make "safe to merge" depend on the data.** When a data-loss case is open (blank keys,
  duplicates, truncation), name it in the first lines and make the answer conditional on it:
  ✅ *"Safe to merge once blank customer IDs are handled: today they're dropped without an error."*
- **A failed check on someone else's change is reported, not fixed.** Give the check, its
  output, and the fix as a suggestion or patch file, and say their files are unchanged.
- **Show a check by its evidence, or leave it out.** Quote the command and its output, or the
  criteria and what was found. Never claim a pass without output, and never describe a review
  you shortened, skipped or ran yourself ("I didn't run the separate panel").
- **Say which acceptance criteria you assumed,** when the request didn't give them.
- **Stop only when nothing can be made.** With an essential input missing, the first line says
  in plain words what's missing, then what you'll produce once it arrives.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G2 emits
`READY` / `NOT READY` / `BLOCKED`. G2.1 emits the council vocabulary. A `revise`-class verdict
returns to the stage named in `revise_to`; a `redirect`-class verdict leaves the loop.

## When a stage's skill is not installed

Skills install à la carte, so a stage may name a skill the target environment does not have.
Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that the stage ran degraded in the run log, not the reply. A missing skill is
never a reason to skip a **gate** — the gate is the loop's whole value.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.
The reply never mentions the run log, whether or not it is set.

```bash
printf '%s\n' '{"ts":"2026-10-01T14:03:00Z","loop":"build","stage":"verify","gate":"G2","verdict":"READY","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
`skilldrop loop-stats` summarises the file: which gates pass first time, which loop back, and
which end in `BLOCKED`.

## Quality bar

- **The gate decides, not the agent.** G2's verdict is `gate.py`'s exit code. An agent that reasons its way past a red gate has broken the loop, not passed it.
- **The cap is honoured.** Three returns to `implement`, then `BLOCKED` with what did not converge. A fourth round is a defect in this loop, not diligence.
- **Every check leaves evidence.** The reply quotes each check's command and output; the run log holds each gate's verdict and round. A pass with no output was asserted, not run.
- **Acceptance criteria exist before `implement` starts.** A slice whose criteria a test cannot assert is not shaped; return it to `shape`. Assumed criteria are marked as assumed.
- **Someone else's change is left as it was.** A review changes no file in the diff it reviews; its fixes travel as suggestions or a patch file.
- **Every quiet data-loss case is named,** and "safe to merge" waits on it.
- **An approval is recorded, never acted on.** The person who approved merges.

## Anti-patterns to avoid

- ❌ **Calling a skill from inside a skill to "continue the loop."** The loop sequences; skills do not chain. This is what keeps every skill portable to Cursor, Kiro, and Aider.
- ❌ **Editing `gate.py`, its config, or a test to turn G2 green.** That converts a mechanical gate into a decorative one.
- ❌ **Treating `PROCEED WITH CONDITIONS` as `PROCEED`.** The conditions travel with the artifact; dropping them is how conditional approvals become unconditional ones.
- ❌ **Running `decide` for every change.** G2.1 exists for escalated disagreement and the merge itself, not as a ceremony on top of a green gate.
- ❌ **Starting at `implement` because the story "is obvious."** Unshaped work is what produces a diff nobody can review against anything.
- ❌ **Fixing the change you were asked to review.** The author can't see what you changed, and the review no longer describes their diff. Offer the patch.
- ❌ **"All checks pass, safe to merge" with a data-loss case open.** Green tests that don't cover blank keys say nothing about blank keys.
- ❌ **Merging because the request said "approved".** The approval is the approver's to act on.
- ❌ **Narrating the review instead of showing it.** "I ran a lighter review myself" tells the person nothing; the output does.
- ❌ **Gate talk in the reply.** "G9: READY, G9.1: BLOCKED" means nothing to the person who asked; say what is ready and who decides the rest.

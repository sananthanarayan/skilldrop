---
title: Release a change
summary: Take a merged change to live users with the release loop — a rollout plan with a way back, a readiness check on evidence, release notes, and your go/no-go call.
kind: how-to
stage: release
---

# Release a change

Take a merged change to live users with a plan to undo it, a readiness check that can say no, and a go/no-go call that stays yours.

## Install the release loop

The `release` loop ships in the `dev-team` pack. Install it with the skills its stages run:

```bash
npx skilldrop-cli install --loop release
```

That installs the loop with `migration-plan`, `launch-readiness`, `release-notes` and `council-review`.

## Start the loop on the merged change

Name the change and ask your agent to run the loop:

```text
Run the release loop on PR #482, the CSV export.
```

`migration-plan` writes the rollout phases first, each with a tested rollback, and names at most one point of no return.

## Close the gaps the readiness check finds

At gate G3, `launch-readiness` checks rollback, detection, response, targets, data and privacy, comms and exposure, each against evidence. A gap comes back as `REVISE` with the skill that closes it:

```text
Add the missing rollback for phase 2, then run the readiness check again.
```

A missing rollback is `BLOCKED` on its own, and the loop stops after three rounds.

## Make the go/no-go call

Once G3 passes, `release-notes` drafts the customer and internal notes, and the loop stops at G3.1 for you:

```text
Go: ship it Monday after the freeze.
```

`PROCEED` ships. `RECONSIDER` means the change is ready but the timing is wrong, so it waits instead of going back to the plan.

After the change is live, the [`operate` loop](../reference/loops.md) picks up any detection or runbook gaps G3 sent its way. The [operating model](../explanation/operating-model.md) shows where this stage sits, and [from idea to shipped feature](../tutorial/idea-to-shipped-feature.md) walks one release through both gates.

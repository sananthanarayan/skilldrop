---
name: migration-plan
description: Generate a phased migration or rollout plan (schema change, API version, datastore swap, platform move, auth-provider switch) — expand→migrate→contract by default, every phase reversible or its point of no return named, observable gates between phases, idempotent backfill with parity checks. Use when the user needs a migration plan, cutover plan, rollout strategy, or asks "how do we get from X to Y without downtime".
---

# migration-plan

Plans the road from current state to target state so that at every moment the system is in a stable, *reversible* position — until the one explicitly named point of no return. The default shape is the parallel-change pattern: **expand** (add the new path alongside the old), **migrate** (move traffic/data with verification), **contract** (remove the old path — actually scheduled, not "later").

## How to respond

1. **Pin both ends.** Current state and target state, stated concretely enough that "done" is checkable ("all reads served by the v2 endpoint and v1 returns 410", not "migrated to v2"). Ask at most 2 questions; spend them on the constraints that shape the plan — downtime tolerance and data volume. Everything else gets `[assumption]`.

2. **Cut phases by the one-change rule.** Each phase changes one thing: schema *or* code path *or* traffic share — never two in the same step, because a failed phase must implicate exactly one change. ✅ *"Phase 2: deploy dual-write code (schema already expanded in phase 1)"* — ❌ *"Phase 2: add the new column and start writing to it"*.

3. **Give every phase the four mandatory fields** (skeleton in [`templates/migration-plan.md`](templates/migration-plan.md)):
   - **Action** — what changes
   - **Gate** — observable criteria to pass before the next phase (error rates, data parity, shadow-diff results), plus **bake time**; a zero-bake gate is a gate in name only
   - **Rollback** — the tested way back, ✅ *"flip flag `orders_v2_read` off; old path still receives dual writes, no data loss"* — ❌ *"redeploy previous version"* when data has already moved
   - **Blast radius** — who/what is affected if this phase fails
   If a phase has no real rollback, it is the **point of no return**: name it in bold, schedule it as late as possible, and list what must be verified immediately before crossing it. A plan may have one; a plan with three has its phases cut wrong.

4. **Specify the backfill like an engineer will run it at 2am.** Idempotent (safe to re-run), resumable (checkpointed, not restart-from-zero), rate-limited (with the limit and the metric that triggers slowdown), and verified by **parity checks at three depths**: row/object counts, checksums or aggregates per partition, and a sampled deep-compare. Dual-write without a reconciliation job is drift with a delay timer — if the plan dual-writes, it names the reconciler and its alert.

5. **Cut traffic over incrementally by default** — flag-gated percentage ramp or canary cohort, with the ramp schedule and the abort threshold at each step. Big-bang cutover is allowed only when the user states why incremental is impossible (e.g. protocol can't run dual), and the plan then compensates with a rehearsal in staging and a widened rollback window.

6. **Schedule the contract phase with a date and an owner.** Removing the old path, the flag, the dual-write, the legacy table — this is a real phase with its own gate ("zero reads on old path for 14 days, verified by metric"), not a footnote. The two-paths-forever system is the most common migration failure and it happens by omission.

7. **Add the comms row per phase**: who needs to know (on-call, support, dependent teams, customers if visible), and what the message is. One line each; silence is a decision, mark it as one.

8. **Emit the plan in one message**: state summary, phase table (overview), per-phase detail, backfill spec, ramp schedule, point of no return, contract phase, and open `[assumption]`s. For the risk analysis itself, point the user at `test-plan-generator` (verification depth) or `council-review` (contested decisions) rather than duplicating them.

## Useful references in this skill

- [`templates/migration-plan.md`](templates/migration-plan.md) — phase skeleton with the four mandatory fields, backfill spec, and ramp table

## Quality bar

- **Every phase is reversible, or is *the* named point of no return.** A reader can answer "how do we get back from here?" for any row in the plan.
- **Every gate is observable with a bake time.** "Looks good" is not a gate; "error rate ≤ baseline +0.1% for 48h and parity job green" is.
- **One change per phase.** A failed phase implicates exactly one change — that's what makes rollback decisions fast.
- **Backfill is idempotent, resumable, rate-limited, parity-checked** — all four stated, none implied.
- **The contract phase has a date, an owner, and a gate.** Plans that end at "100% on new path" are unfinished.
- **Rollback steps are tested, not asserted.** Each rollback names when it was (or will be) rehearsed; an unrehearsed rollback is a hypothesis.

## When to use this skill

- ✅ Schema changes that need backfill on a live system
- ✅ API or service version migrations with consumers to move
- ✅ Datastore, queue, auth-provider, or platform swaps
- ✅ "How do we roll this out without downtime?" for any risky change

## When NOT to use this skill

- ❌ A change deployable in one reversible step — normal deploy, no plan needed
- ❌ Choosing the target ("should we move to DynamoDB?") — that's `tech-comparison-matrix`; this skill starts after the decision
- ❌ The test depth itself — emit gates here, hand verification design to `test-plan-generator`
- ❌ Organizational/process migrations with no system state — different problem

## Anti-patterns to avoid

- ❌ **Big-bang cutover as the default.** It's the plan you get by not planning; incremental is the default and exceptions must argue.
- ❌ **"Rollback: redeploy the previous version"** after data has migrated. Code rolls back in minutes; data doesn't. State the data story or the rollback is fiction.
- ❌ **Dual-write without reconciliation.** The two stores *will* drift — name the reconciler, its schedule, and its alert, or don't dual-write.
- ❌ **Schema and code in one phase.** When it fails, you won't know which to revert, so you'll freeze instead.
- ❌ **Zero bake time.** Phases passed in the same hour they started are phases nobody watched.
- ❌ **The unscheduled contract phase.** "We'll remove the old path later" — later has no owner, so dual paths become the architecture.
- ❌ **Migrating and improving simultaneously.** "While we're at it" scope is how a 3-week migration becomes a 6-month one; improvements go in the backlog, the migration moves like-for-like.

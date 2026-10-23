---
name: rollout-plan
description: Plan the progressive release of a code change behind a feature flag or canary — the exposure ladder (internal, beta cohort, 1%, 5%, 25%, 50%, 100%, or what the traffic supports), and for each step who is exposed, decision and guardrail metrics with a baseline and a threshold against a control cohort, the minimum traffic and time before the numbers mean anything, a promote / hold / roll back rule set in advance, who watches and what aborts automatically; then what turning the flag off does not undo, and who removes the flag by when. Use when the user asks for a rollout plan, canary plan, ramp schedule, progressive delivery or percentage rollout, "how long should the canary run", "when do we go from 5% to 25%", or how to turn on a flagged feature safely.
---

# rollout-plan

Plans how a code path already behind a flag or canary reaches users: in what steps, judged
by which numbers, decided by which rule, and undone how. The plan's unit is **exposure of a
code path to users**. Moving data or changing a schema is a migration and belongs to
`migration-plan`; whether the change may go live at all is `launch-readiness`'s go/no-go.
This plan starts once both of those are settled, or names them as open.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** the plan is built around the input's binding constraint, never around a stock ladder. Sample sizes are working, not the answer: state what they mean for the plan in one sentence, with the inputs that produced them.

1. **Answer the question in the first two lines.** "Who's right?" gets a name. "Is 1% Monday to 100%
   Thursday OK?" gets yes or no. "How long should the canary run?" gets a duration. Then the one
   fact from the input that settles it, and the shape of the plan.
   ✅ *"The payroll lead is right: 1% of employers for an hour sees no pay run at all, so a clean hour proves nothing. Shadow the new calculator on Friday's run, then move named employers through the next two pay cycles."*
   ❌ *"Each arm needs 9,412 units (19 days at 1%)."* (A statistic the reader didn't ask for, built on a rate they never gave.)

2. **Find the binding constraint before drawing a ladder.** Read the input for the fact that
   decides pacing, and name it in one line. The common ones:
   - **A partner or quota cap** ("stay under 500 new accounts a day"): convert each step's exposure into the capped unit (exposure × volume × take rate), state the take rate as an `[assumption]` if it isn't given, and hold the step that would cross it.
   - **A calendar cycle** (billing run on the 1st, payroll, month-end close, a weekly batch): the evidence arrives on the cycle, not by the hour. Count the cycles left before the deadline and place the steps on them.
   - **A deadline or freeze** ("before the holiday freeze on Dec 1", "before year-end close"): the schedule works back from it. If the evidence the steps need doesn't fit, say so in the opening, not in a footnote.
   - **Segments the flag targets** (tenants, accounts, regions, plans, allow-lists) or a flag that cannot target by %: steps are named cohorts chosen for a reason, not hash buckets.
   - **A result checkable without exposure** (tax, prices, ranking, balances): a shadow run beside the old path, writing nothing a customer or downstream system reads, is the main gate, whether the design already has one or the plan adds it.
   - **Low volume**: when a step sees single-digit counts, percentages and power calculations mean nothing. Judge in counts (zero tolerance, "no more than 2 per run") and widen the step to a segment or a cycle.
   The fixed internal → 1% → 5% → 25% → 50% → 100% ladder is the default **only** when traffic is high and nothing above shapes the pacing.

3. **Pin the mechanics.** The code path; the flag (key, where it is evaluated: server, client,
   edge, and what it can target); the **randomisation unit** (user, account, tenant, device,
   request); volume in that unit; the baselines given. Ask at most 2 questions, spent on volume
   and on what the new path writes or sends. A schema change, backfill or dual-write in the same
   change is a migration that finishes its expand phase before step 1; say so in one line.

4. **Pick cohorts with reasons.** Every step names who is in it and why:
   - **Internal or test accounts first.** They catch crashes, not rates.
   - **Chosen cohorts beat random ones when the risk sits in a segment.** Put the cases the change exists to fix (the edge cases, the large accounts, the unusual configurations) into an early cohort deliberately, with willing customers, or hold them back deliberately and say why. ❌ a random hash that may contain none of them.
   - **Sticky, nested assignment** for percentage steps: hash on the randomisation unit so the 1% stays inside the 5%. ✅ *"`hash(salt + user_id) mod 1000 < 10`"* — ❌ *"random 1% of requests"* when the flag changes what a user sees.
   - **SLA or contractual-notice customers** stay out before 50% unless they asked to be early; say how they are excluded.
   - **Units in another experiment on the same surface** are excluded, or the comparison is called confounded.
   - **B2B: assign by account or tenant**, so one team never sees two versions.

5. **Choose the metrics and write thresholds that can fire.** One decision metric (what the change
   exists to move, or the main correctness or safety rate) plus guardrails: error rate of the touched
   path, p95 of the touched endpoint, saturation of what it leans on (pool, queue, third-party quota),
   one business guardrail. Each carries the baseline from the input and a limit **against the
   concurrent flag-off control**, never against last week.
   - ✅ *"checkout errors, flag-on ≤ flag-off + 0.3 pp (baseline 0.8%)"* — ❌ *"monitor errors"*.
   - **Small counts get count rules.** ✅ *"any unexplained difference over $0.01 between old and new totals holds that account's statement from the send"* — ❌ *"mismatch rate ≤ 0.1%"* on 30 statements.
   - p95 needs 2,000+ requests per arm and p99 10,000+; below that, read the median.
   - A metric with no instrument yet is a precondition for step 1, written once.

6. **Size steps from the arithmetic, and say what it means.** For a rate metric on real traffic, run
   `python3 ${CLAUDE_SKILL_DIR}/scripts/canary_math.py --baseline 1% --detect-abs 0.3pp --traffic 2000 --unit users --steps 1,10,50`
   (other IDEs: `python3 scripts/canary_math.py ...` from the skill folder; `--direction down` when a
   fall is the harm, `--control-pct` for a fixed holdback; formula in [`reference.md`](reference.md)).
   - **Put one sentence in the reply, not the table.** ✅ *"At 2,000 users an hour, a 1% step needs about 20 days to see a 0.3 pp rise in errors, so it is a 2-hour crash check and errors are judged at 10% (about 2 days)."* Show the inputs (traffic, baseline, regression size) beside it.
   - **No figure without a source.** Every number in the reply is from the input, from arithmetic on the input, or tagged `[assumption]` in one line. With no baseline or traffic, write the step as a unit count and one line saying what was assumed; never a duration built on an invented rate.
   - **Step minimum = the largest of** the statistical time, one daily peak (24 h when traffic varies by hour), a weekday/weekend cycle where the business has one, and the delay of any late effect (nightly send, billing run).
   - **A step that can't detect anything** is merged, raised, or kept as a crash-only check, said plainly. ✅ *"1% for 2 h: crash check only"* — ❌ *"1% for 24 h to be safe"*.
   - **100% has no concurrent control**: promote on the 50% comparison, or keep a small holdback for a stated time.

7. **Put dates on it when the input has a date.** With a deadline, freeze, cycle or "this week",
   each step gets a calendar date counted from today, and the last line of the ladder shows the
   deadline is met or by how much it is missed. Name the slack: ✅ *"one failed cycle pushes 100% past year-end close."*

8. **Write each step's rule before it starts.**
   - **Promote** when the minimum time or count is reached and every guardrail is inside its threshold.
   - **Hold** when the sample is short or a metric sits between threshold and abort: extend once, by a stated time or cycle, then roll back.
   - **Roll back** when a guardrail breaches at the planned sample, or an abort fires.
   - **Abort, automated where the tooling allows**: wide, fast triggers. ✅ *"flag-on 5xx > 3× flag-off for 5 min → flag off automatically, page payments on-call"*; ✅ *"unexplained diff on a live statement → account back to the old engine, its unsent statements held"*.
   - **Watcher and override**: the role watching, the sign-off before each promotion where one is needed (finance, tax, a partner contact), and the one role allowed to promote past a breach.
   - **No promotion on peeks.** Promotion is read at the step's end; aborts fire any time.

9. **Name what flag-off does not undo.** Who flips the flag and how fast every client stops taking
   the new path (server: seconds; cached client config: its TTL; shipped binary: only a server-side
   switch). Then only the categories this change touches, each with its handling:
   - **Data in a new format or table**: what still reads it after rollback (the renderer, re-runs, credit notes, exports). Verified before step 1; the table can't be dropped while records point at it.
   - **Messages sent** (email, push, webhooks, accounting syncs): no recall; the correction or reissue path exists before the first live step.
   - **Money and third-party records** (charges, agreements, filings, per-call fees): the reversal procedure and who runs it, or "permanent".
   - **Jobs queued, caches written, clients shipped**: when they stop.
   Name the **point of no return**, or rule it out in a line.

10. **Schedule the flag's removal.** An owner (the named owner if the input gives one, else a role), a
    date (default 30 days after 100%; for a cycle-driven change, after the first full cycle at 100%
    with no rollback), and what goes: the flag, the dead path, its config and dashboards. Say what
    must stay (a reader for records the old path wrote; the minimum app version for shipped code).

11. **Deliver lean.** One plan, shaped by [`templates/rollout-plan.md`](templates/rollout-plan.md):
    the answer, the binding constraint, the dated ladder, the rules, the not-undone list, flag removal.
    Either the plan in the reply or a saved file with a five-line reply, never both at full length.
    "To confirm" holds at most 4 facts, each one that would change a step. Sections that don't apply
    are dropped, not filled with "does not apply".

**Non-interactive runs** (subagent, CI, headless): the regression size, take rates, cohort choices and
step lengths become `[assumption]`s in one line. Missing traffic or baselines are never invented. If
the change or its gate can't be identified, emit `BLOCKED: need the change being released and the flag
or canary that gates it`.

## Useful references in this skill

- [`templates/rollout-plan.md`](templates/rollout-plan.md) — the plan skeleton: answer, constraint, dated ladder, rules, not-undone list, flag removal
- [`reference.md`](reference.md) — the sample-size formula, the randomisation-unit trap, count rules for small volumes, threshold patterns, the not-undone checklist
- [`scripts/canary_math.py`](scripts/canary_math.py) — units and hours each percentage step needs; flags steps that can't reach sufficiency (stdlib only)
- [`examples/sync-engine-workspaces.md`](examples/sync-engine-workspaces.md) — a plan for a sync engine ramped by workspace, where flag-off leaves notes the old engine can't read

## Quality bar

- **The first two lines answer the user's question** in plain words, with the input fact that settles it.
- **The binding constraint is named** and the ladder visibly follows it (cap, cycle, deadline, segment, shadow, volume).
- **Every threshold is testable**: metric, baseline, limit against the flag-off control; counts where volumes are small.
- **Every number traces** to the input, to arithmetic on it, or to a one-line `[assumption]`.
- **A deadline in the input gets a dated ladder** that shows whether it is met.
- **Promote, hold, roll back and abort are written before the step**, with a watcher, a sign-off where one is needed, and an override role.
- **The not-undone list covers what this change sends, writes or charges**, with handling for each.
- **The flag has an owner and a removal date.**
- **The reply is shorter than the plan it replaces would be at full length**; "To confirm" is never longer than the ladder.

## When to use this skill

- ✅ A merged change behind a flag needs a ramp, canary schedule or cohort plan
- ✅ "How long does the 1% have to run?", "when do we promote?", "is this ramp right?"
- ✅ Turning on a risky path (payments, tax, auth, ranking, a new dependency) for real users
- ✅ A rollout that sends, charges or writes something the flag can't take back

## When NOT to use this skill

- ❌ Schema changes, backfills, datastore or provider swaps, dual-writes: `migration-plan`
- ❌ "Are we ready to launch?" go/no-go: `launch-readiness`
- ❌ SLOs, alerts and dashboards for the service: `observability-plan`
- ❌ Defining what success means for the feature: `success-metrics`
- ❌ The on-call procedure for the service as a whole: `runbook-generator`
- ❌ A change with no flag, canary or staged deploy: there is nothing to ramp; plan the gate first

## Anti-patterns to avoid

- ❌ **Statistics as the headline.** "11,734 per arm, 26 days" before the user knows whether their plan is right.
- ❌ **The ritual ladder.** 1% → 5% → 25% → 50% → 100% on a change whose evidence arrives once a month, or under a partner cap it would cross.
- ❌ **Random buckets where the risk is a segment.** A pricing change hashed by account may never touch the multi-currency accounts it exists to fix.
- ❌ **Percent thresholds on single-digit counts.** "Failure rate ≤ 0.5%" on 30 statements fires on one failure or never.
- ❌ **Invented inputs.** An adoption rate, mismatch rate or per-account volume the input never gave, presented as fact.
- ❌ **No dates under a deadline.** "Step 3: 48 h" when the user named a freeze date.
- ❌ **Comparing against yesterday** instead of the concurrent flag-off cohort.
- ❌ **"Rollback: turn the flag off"** when the path sent emails, charged cards or wrote rows old code can't read.
- ❌ **The padded reply.** A full plan in the message and again in a file, a "To confirm" table longer than the plan.
- ❌ **The flag that never leaves.** No owner and no date.

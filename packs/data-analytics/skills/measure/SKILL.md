---
name: measure
description: Take a dashboard request to a spec a BI developer can build on numbers people can defend: the decision it serves and one chart per question, every metric defined, the SQL behind each metric reviewed for the bugs that quietly inflate a figure, and the metric owner's sign-off on each definition before anything is built. Use when the user says "we need a dashboard for…", "run the measure loop", "make sure these numbers are right before the BI team builds it", or two teams disagree about a number that is about to go on a dashboard.
---

# measure

One dashboard, from the request to a spec whose numbers have been checked. A wrong number
on a dashboard does more damage than a wrong number in a query, because the chart makes it
look settled. So the loop reviews the SQL before anything is built, and it only reviews the
queries that matter. The spec runs first and cuts the charts that serve no decision, so no
time goes on queries for charts that won't exist. Last, each metric's owner confirms the
definition, because a query can be correct and still compute the wrong thing.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `spec` | generate | [`dashboard-spec`](../../skills/dashboard-spec/SKILL.md) | — |
| 2 | `review` | verify | [`sql-review`](../../skills/sql-review/SKILL.md) | **G9** review |
| 3 | `sign-off` | gate | [`doc-critique`](../../../core/skills/doc-critique/SKILL.md) | **G9.1** human |

## How to run this loop

1. **Spec the dashboard.** Run `dashboard-spec` with the audience, the decision and the
   charts people asked for. Save `dashboard-spec.md`. Its cut list removes charts before any
   SQL is read. Every surviving chart names its metric by defined name, grain, window and
   comparison. A metric with no written definition is marked `undefined`. Write it down as
   the person states it, or leave it as a question for the metric's owner. Don't define it
   yourself.
2. **Collect one query per surviving metric.** The person supplies the SQL, the dbt model or
   the view that computes each one, with the engine and what one output row represents.
   Where none exists yet, draft one from the definition and the schema they supply, and
   mark it as a draft. A metric with no query and no schema to draft from is `BLOCKED` for
   that metric, not skipped.
3. **Review every query at G9.** Run `sql-review` on each, one at a time. Collect each
   review's verdict line, findings, corrected query and verification queries. Ask the person
   to run the verification queries, or run them yourself when you have access.
4. **Map the reviews to G9's verdict:**
   - every query `SHIP IT` or `SHIP WITH NOTES` → `READY`. The notes travel to the owner at G9.1.
   - any query `BLOCK` or `FIX FIRST` → `NOT READY`. Return to `spec`. The corrected query
     becomes that metric's source in the spec, and its verification results go beside it.
     The fix changes the number the chart will show, sometimes by a lot, so its target,
     comparison and any threshold the decision uses need checking against it. Then review
     the corrected query again. Each return counts against the cap.
5. **Critique, then put each definition to its owner at G9.1.** Run `doc-critique` on the
   spec. Then show each metric's owner:
   - the definition in words;
   - the reviewed query;
   - what changed and by how much, from the verification queries;
   - every assumption the review made about keys, time zones and exclusions.

   The owner confirms that this is what the business means by the metric. The BI developer
   builds only from a spec that has passed G9.1.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json).

- G9 emits `READY`, `NOT READY` or `BLOCKED` (no query text, or no engine to review it
  against).
- G9.1 emits:
  - `PROCEED`: every metric's owner confirmed its definition and number.
  - `PROCEED WITH CONDITIONS`: confirmed, with named items that travel to the build, such as
    a `SHIP WITH NOTES` caveat shown on the chart, or a data gap with its date.
  - `REVISE`: an owner says the definition is wrong (the wrong time zone, an exclusion
    missing, the wrong grain). Return to `spec` with their definition.
  - `BLOCKED`: an `undefined` metric has no owner to define it, or an owner is unavailable.

An `undefined` metric can't pass G9.1. Its owner defines it, or the chart moves to the cut
list with the reason.

## Non-interactive runs

With no person present, G9.1 cannot be satisfied. Run `spec` and `review`, deliver the spec
with each query's review, and emit `BLOCKED: need each metric owner's confirmation of
<every metric on the spec>`. A metric whose query passed G9 still needs its owner: the review
says the SQL computes the definition, not that the definition is right. Never confirm a definition on an owner's behalf, and never fill an
`undefined` metric with a plausible one: two teams will each read it as theirs.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage, and record that it ran degraded. A degraded `review` still checks every join for
fan-out, every filter for NULLs and every date boundary for its time zone, in that order,
because those are the bugs that change the number. Never skip G9.1.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-10-19T14:03:00Z","loop":"measure","stage":"review","gate":"G9","verdict":"NOT READY","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never a query, a table name or a figure.
`skilldrop loop-stats` summarises the file.

## Quality bar

- **The cut list runs before any SQL is read.** Only the queries behind charts that serve the decision get reviewed.
- **Every surviving chart's metric has a definition and a reviewed query.** `undefined` and unreviewed are build blockers, not notes.
- **A fixed query goes back through the spec.** The corrected number can move a target or a threshold, and the spec is where those live.
- **The owner sees the change in the number.** The verification queries' before and after go to G9.1, not only the corrected SQL.
- **The metric's owner signs the definition.** A correct query for the wrong definition is still the wrong number.

## Anti-patterns to avoid

- ❌ **Reviewing every query in the BI tool.** Queries for charts the spec cut cost review time and add nothing.
- ❌ **Defining an `undefined` metric yourself to finish the spec.** That settles a disagreement between two teams by picking one at random.
- ❌ **Shipping the corrected SQL without telling the owner the number moved.** A revenue figure that drops a third overnight with no explanation gets reverted.
- ❌ **Passing G9 on a clean lint.** The lint can't see join fan-out; the review reads the joins.
- ❌ **Treating `SHIP WITH NOTES` as `SHIP IT`.** The notes go to the owner and, where they change how the chart reads, onto the chart.
- ❌ **Building before G9.1.** A dashboard built on an unconfirmed definition is the one the two teams will argue about.

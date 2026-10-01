---
name: metric-definition
description: Write a metric spec precise enough for a semantic layer or dbt metric to implement and for two analysts to get the same number — name, business question, exact numerator and denominator, grain, time window and timezone, filters and exclusions (test accounts, refunds), allowed dimensions, edge cases (NULLs, late data, currency), owner, reference SQL, and the sanity checks that catch it going wrong. Use when the user says "define this metric", "how exactly do we calculate X", "finance and product get different numbers for X", "write the metric spec for our semantic layer", or "what counts as an active user".
---

# metric-definition

Turns a metric name that people already argue about ("active customers", "net revenue", "refund rate") into one written definition that produces one number. Most metric disputes are not about the data: they're two queries with different filters, windows or timezones answering under the same name. This skill pins every one of those choices down, writes the reference SQL, and adds the checks that catch the number drifting. It defines **how a metric is computed**. Choosing **which metric** judges a feature is `success-metrics`; that skill picks the primary, guardrails and decision rule, and this one makes any of those metrics exact.

## How to respond

1. **Pin the question and the sources, asking once.** Ask at most 2 questions in one message: *"What decision does this number inform, and who reads it?"* and *"Which tables or models hold the data, and is there SQL or a dashboard already computing something under this name?"* Existing SQL is the best input you can get: it shows the definition people actually use today, including its bugs. If the user gave both, don't ask.

**Non-interactive runs** (subagent, CI, headless): derive the business question and sources from the input and tag each `[assumption]`. Choices the input doesn't settle (timezone, exclusions, late-data policy) get a stated default tagged `[assumption]` and are listed under open decisions. No metric name and no business question in the input → emit `BLOCKED: need the metric name and the question it answers`.

2. **Name it so one name means one formula.** `snake_case`, noun phrase, qualified where variants exist: ✅ `net_revenue_usd`, `gross_revenue_usd` — ❌ `revenue` covering both. If two teams compute it differently and both versions are legitimate, they get two names, not one name with a footnote. State the business question in one sentence: ✅ *"What share of last month's orders were refunded, by region?"* — ❌ *"Track refunds."*

3. **Write the exact formula.** Numerator and denominator, each in words and as an aggregation over named columns: ✅ *"Numerator: count of distinct `order_id` with at least one non-reversed refund. Denominator: count of distinct `order_id` created in the window."* Name the metric type (count, sum, distinct count, ratio, average, percentile, cumulative), the unit and the display format (%, USD, decimals). A ratio is always **ratio of sums**, never an average of per-row or per-day ratios. See [`reference.md`](reference.md) for the types and their traps.

4. **Fix the grain and the time.** Write down:
   - **Entity**: what one unit is (order, customer, account, session).
   - **Time column**: which timestamp decides membership in a period (created, paid, shipped, event or load time) and why.
   - **Window**: calendar month, ISO week (Monday start), rolling 28 days, trailing 7 complete days.
   - **Timezone**: the reporting zone, with the IANA name, e.g. `America/New_York`, not "EST".
   - **Partial periods**: whether the current period is shown, and how it's marked.
   - **Additivity**: whether the metric can be summed across days, regions or segments. Distinct counts and ratios can't (four weekly active-user counts don't add up to monthly active users), so say how it rolls up: recompute from the base, don't sum.

5. **List every filter and exclusion with its predicate and reason.** Always ask about the usual suspects: test and internal accounts, refunds and cancellations, fraud, deleted or merged records, free or zero-value transactions, and staff discounts. ✅ *"Exclude test accounts: `NOT EXISTS (SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id)`. Reason: QA places real orders in production."* An exclusion without a predicate gets implemented three different ways.

6. **Name the dimensions it can be sliced by, and the ones it can't.** For each allowed dimension, give the source column, the join path and whether the join is one-to-one. A dimension that fans out (product category on order-level revenue, when an order has many categories) is either disallowed or comes with an allocation rule. Say which.

7. **Settle the edge cases explicitly.** NULLs in each column the formula uses (counted, excluded or defaulted), zero denominators (show NULL, not 0), late-arriving data (how many days a closed period may still change, and when it locks), currency (rate source and which date's rate), DST days, duplicates and replays, backfills, and timezone changes. Each gets a one-line rule, not a "be careful".

8. **Assign an owner and a change policy.** The owner is a role and a team (✅ *"Finance analytics lead"*), not "data team". Status: `draft` or `certified`. Changing the formula is a new version with a change log entry and a dated cutover, never a silent edit, because a silent edit breaks every trend line that crosses the change date.

9. **Write the reference SQL** in the user's dialect: one CTE per step (base population, exclusions, numerator, denominator), half-open time windows (`>= start AND < end`), boundaries converted to the reporting timezone, and `NULLIF` on the denominator. The reference SQL is the tie-breaker when the prose and an implementation disagree. Recommend the user runs `sql-review` on it before it's certified.

10. **Add the sanity checks** that would catch the metric being wrong, each runnable: reconciliation with a system of record (the finance ledger, the billing system), hard bounds (a rate stays within 0 to 1), additivity (regions sum to the total, for additive metrics only), join row counts (the base population's count doesn't change after dimension joins), a period-over-period alert threshold, and a hand-computed fixture of 5–10 rows with the expected answer.

11. **Emit with [`templates/metric-spec.md`](templates/metric-spec.md)** in one message, ending with **open decisions**: each choice made by default, with the person who should confirm it.

## Useful references in this skill

- [`reference.md`](reference.md) — metric types and their traps, additivity rules, the exclusion and edge-case checklist, the sanity-check catalogue, and how the spec's fields map to a semantic layer (dbt MetricFlow and similar)
- [`templates/metric-spec.md`](templates/metric-spec.md) — the spec skeleton
- [`examples/refund-rate.md`](examples/refund-rate.md) — worked example: an order refund rate disputed between finance and support, defined end to end

## Quality bar

- **One name, one formula.** The numerator and denominator are written as aggregations over named columns, so two analysts would write the same SQL.
- **Grain, time column, window and timezone are all explicit**, with an IANA timezone name and a half-open window.
- **Every exclusion has a predicate and a reason.** No "exclude test data" without the SQL for it.
- **Additivity is stated**, with the roll-up rule for non-additive metrics.
- **Every allowed dimension has a join path and its cardinality**, and fan-out dimensions are disallowed or carry an allocation rule.
- **Edge cases get one-line rules**, including late data with a lock date and zero denominators.
- **The reference SQL runs as written** in the named dialect and matches the prose.
- **At least three runnable sanity checks**, including one reconciliation with a system of record where one exists.
- **Nothing is invented.** Table names, columns and business rules not given are marked `[assumption]` and listed in open decisions.

## When to use this skill

- ✅ Two teams report different numbers under the same metric name
- ✅ Putting a metric into a semantic layer, dbt metrics or a BI tool's model, and it needs one definition
- ✅ "What counts as an active user / a churned customer / net revenue?"
- ✅ Certifying a metric before it goes on an exec dashboard or into a board pack

## When NOT to use this skill

- ❌ Choosing which metric judges a feature, with targets, guardrails and a decision rule — that's `success-metrics`
- ❌ Checking that an existing query computes its number correctly — that's `sql-review`
- ❌ Deciding which charts and metrics go on a dashboard — that's `dashboard-spec`
- ❌ Agreeing a dataset's schema, freshness and quality guarantees with its consumers — that's `data-contract`
- ❌ Service health indicators, SLOs and error budgets — that's `observability-plan`

## Anti-patterns to avoid

- ❌ **The footnoted metric.** One name, three formulas, and a footnote on each dashboard. Split it into named variants.
- ❌ **Average of ratios.** `AVG(daily_refund_rate)` weights a quiet Sunday like Black Friday. Divide the sums.
- ❌ **"Monthly" with no timezone.** The UTC month and the New York month differ by hours of orders at each boundary, and the number won't match finance's.
- ❌ **Summing distinct counts.** Adding weekly active users to get monthly active users counts every returning user four times.
- ❌ **Exclusions in prose only.** "Excludes test accounts" with no predicate gets implemented three different ways.
- ❌ **Silent redefinition.** Changing the formula in place, so last quarter's trend line now compares two different metrics.
- ❌ **No owner.** A metric "owned by the data team" is owned by nobody when finance and product disagree about it.
- ❌ **Specs with no checks.** A definition that nobody tests drifts the first time an upstream table changes.

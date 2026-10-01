# metric-definition reference

## Metric types and their traps

| Type | Example | Additive across time and dimensions? | Trap |
|---|---|---|---|
| Count | orders | Yes | Counting rows of a joined table instead of the entity |
| Sum | revenue_usd | Yes, within one currency | Mixed currencies; refunds netted in some places and not others |
| Distinct count | active_customers | **No** | Summing daily or regional counts double-counts entities present in several |
| Ratio | refund_rate | **No** | Averaging per-day or per-segment ratios instead of dividing the sums |
| Average | avg_order_value | **No** | It's a ratio (sum / count): roll up the parts, not the averages |
| Percentile | p90_delivery_hours | **No** | Percentiles can't be combined; recompute from raw rows |
| Cumulative | customers_to_date | No (it is a running total) | Restating history when late rows land in an old period |

For every non-additive metric, the spec says: *"To roll up, recompute from the base rows; never sum or average the reported values."* A semantic layer that stores the numerator and denominator separately can roll up ratios correctly; one that stores only the ratio can't.

## Exclusion checklist

Ask about each. Every one that applies gets a predicate and a reason in the spec.

- Test, QA, demo and internal/staff accounts
- Refunds, chargebacks, cancellations and voids (and partial refunds)
- Fraudulent or blocked transactions
- Deleted, merged or anonymised records (including after a privacy erasure request)
- Zero-value, free-tier or 100%-discount transactions
- Duplicates from retries or event replays
- Records outside the product's scope (wholesale orders, a sister brand)

## Edge-case checklist

| Case | The spec must say |
|---|---|
| NULL in a formula column | Counted, excluded, or defaulted, and to what |
| Zero denominator | Show NULL (blank), not 0. 0% claims something happened. |
| Late-arriving data | How many days a closed period may change; when it locks; whether restatements are announced |
| Currency | Source of rates, which date's rate (transaction date or period end), and the reporting currency |
| Timezone and DST | IANA zone name; what a "day" means on 23- and 25-hour days |
| Week definition | ISO week (Monday start) or another start day, and how week 1 is numbered |
| Backfills | Whether historical values change when a backfill runs, and who is told |
| Definition change | New version number, change-log entry, cutover date; old version kept queryable for comparison |

## Sanity-check catalogue

Pick at least three. Each is written as a runnable query or test, not a description.

1. **Reconciliation with a system of record.** The metric's total for a closed period matches the ledger, billing system or source report within a stated tolerance.
2. **Bounds.** Rates within 0 and 1; counts not negative; revenue not negative unless refunds are netted.
3. **Additivity.** For additive metrics only, the sum over a dimension equals the total. For distinct counts, the sum over a dimension is **at least** the total.
4. **Join integrity.** Row count of the base population before and after each dimension join is equal.
5. **Known-answer fixture.** 5–10 hand-built rows covering each exclusion and edge case, with the expected result worked out by hand. Run it in CI (a dbt unit test or a plain SQL assertion).
6. **Period-over-period alert.** A change beyond a stated threshold (for example ±30% week over week) opens a ticket to check before anyone reports it.
7. **Freshness.** The latest timestamp in the source is recent enough for the window being reported.

## Mapping to a semantic layer

Semantic layers differ in syntax but share the same parts. Map the spec's fields like this, then write the definition in your tool's own syntax and check it against that tool's documentation.

| Spec field | Semantic layer concept |
|---|---|
| Entity | Primary entity or key of the model |
| Time column and window | Aggregation time dimension and granularity |
| Numerator, denominator | Measures (an aggregation plus an expression), combined in a ratio metric |
| Filters and exclusions | A filter on the metric or measure, or exclusion done in the underlying model |
| Allowed dimensions | Dimensions reachable through declared joins or entity relationships |
| Owner, status, version | Metadata or `meta` fields, plus the repo's code owners |

dbt's MetricFlow, for example, defines measures inside semantic models and offers simple, ratio, cumulative, derived and conversion metric types; a ratio metric there names a numerator metric and a denominator metric. Cube, LookML and other tools use their own terms for the same parts. Do the exclusions in the modelled table where you can, so every metric built on it inherits them, rather than repeating the filter in each metric.

# Metric: `<metric_name>` (v<N>, <draft | certified>)

**Business question:** <one sentence: what decision this number informs, and for whom>
**Owner:** <role, team> · **Status:** <draft | certified> · **Last changed:** <YYYY-MM-DD>

## Formula

| Part | In words | As an aggregation |
|---|---|---|
| Numerator | <what is counted or summed> | `<COUNT(DISTINCT x) / SUM(y) ...>` |
| Denominator | <population it is divided by, or "none"> | `<...>` |

- **Type:** <count | sum | distinct count | ratio | average | percentile | cumulative>
- **Unit and format:** <%, 1 decimal | USD, 0 decimals | count>

## Grain and time

- **Entity:** <order | customer | account | session>
- **Time column:** `<table.column>`, because <why this timestamp and not another>
- **Window:** <calendar month | ISO week | rolling 28 days | trailing 7 complete days>, half-open (`>= start AND < end`)
- **Timezone:** `<IANA name>`
- **Partial periods:** <shown and marked "to date" | hidden until complete>
- **Additivity:** <additive across time and dimensions | not additive: recompute from base rows to roll up>

## Filters and exclusions

| Exclusion | Predicate | Reason |
|---|---|---|
| <test accounts> | `<SQL>` | <why> |

## Dimensions

| Dimension | Source column | Join path | Cardinality | Allowed? |
|---|---|---|---|---|
| <region> | `<customers.region>` | `<orders.customer_id = customers.customer_id>` | <many-to-one> | <yes> |
| <product category> | `<...>` | `<...>` | <one-to-many: fans out> | <no, or allocation rule> |

## Edge cases

| Case | Rule |
|---|---|
| NULLs | <...> |
| Zero denominator | <NULL, not 0> |
| Late data | <closed period can change for N days; locks on day N+1> |
| Currency | <rate source and date> |
| Timezone and DST | <...> |
| Duplicates | <...> |

## Reference SQL (<dialect>)

```sql
-- base population, exclusions, numerator, denominator: one CTE each
```

## Sanity checks

1. <reconciliation with system of record: query and tolerance>
2. <bounds>
3. <join integrity or additivity>
4. <known-answer fixture>

## Change log

| Version | Date | Change | Approved by |
|---|---|---|---|
| v1 | <YYYY-MM-DD> | Initial definition | <owner> |

## Open decisions

- [ ] <choice made by default> — confirm with <role>

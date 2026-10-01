# Worked example: order refund rate

## Input

> Finance says our September refund rate was one number and support says another. Can you write a proper definition? We're on Postgres. Orders are in `orders` (`order_id`, `customer_id`, `created_at` timestamptz, `amount_usd`), refunds in `refunds` (`refund_id`, `order_id`, `status`, `created_at`), and `test_accounts` lists QA customers. Finance reports monthly in New York time. Finance counts an order as refunded if any refund on it went through; support counts refund tickets. The finance analytics lead at Acme owns finance metrics.

No questions asked: the decision (monthly finance reporting), the sources and the owner are all in the prompt. The dispute itself shows the two teams are measuring different things, so the spec splits them.

## Output

# Metric: `order_refund_rate` (v1, draft)

**Business question:** What share of the orders placed in a month had at least one refund go through, by region? Read monthly by finance to track refund exposure.
**Owner:** Finance analytics lead, Acme finance · **Status:** draft · **Last changed:** 2026-10-01

**Why support's number differs:** support counts refund tickets, which is a different metric (`refund_tickets`, a count of tickets, not a share of orders). An order with two partial refunds is one refunded order here and two tickets there. Both are legitimate; they need separate names.

## Formula

| Part | In words | As an aggregation |
|---|---|---|
| Numerator | Orders in the window with at least one refund whose status is not `reversed` | `COUNT(DISTINCT o.order_id)` where a qualifying refund exists |
| Denominator | Orders created in the window, excluding test accounts | `COUNT(DISTINCT o.order_id)` |

- **Type:** ratio
- **Unit and format:** %, 1 decimal

## Grain and time

- **Entity:** order
- **Time column:** `orders.created_at`, so the refund is attributed to the month the order was placed. A September order refunded in October counts toward September.
- **Window:** calendar month, half-open
- **Timezone:** `America/New_York`
- **Partial periods:** the current month is shown and labelled "month to date"
- **Additivity:** not additive. A quarterly or all-region rate is recomputed from the base rows, never averaged from monthly or regional rates.

## Filters and exclusions

| Exclusion | Predicate | Reason |
|---|---|---|
| Test accounts | `NOT EXISTS (SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id)` | QA places real orders in production |
| Reversed refunds | `r.status IS DISTINCT FROM 'reversed'` | A reversed refund returned no money |

## Dimensions

| Dimension | Source column | Join path | Cardinality | Allowed? |
|---|---|---|---|---|
| Region | `customers.region` | `orders.customer_id = customers.customer_id` | many-to-one `[assumption: customer_id unique]` | yes |
| Product category | `order_items` → `products.category` | through `order_items` | one-to-many: fans out | no. An order with two categories would count in both. |

## Edge cases

| Case | Rule |
|---|---|
| Refund with NULL status | Counts as a refund `[assumption]` |
| Zero orders in a region-month | Rate is NULL, shown blank |
| Late data | Refunds arrive weeks after the order, so a month's rate keeps rising. The month locks for reporting 60 days after month end `[assumption]`; before that, label it "provisional". |
| Currency | Not applicable: the metric counts orders, not money |
| DST | Not applicable at month grain; boundaries are converted to New York time |
| Duplicate refund rows | Handled: the numerator counts distinct orders |

## Reference SQL (Postgres)

```sql
WITH base AS (                   -- orders placed in the month, no test accounts
  SELECT o.order_id, o.customer_id
  FROM orders o
  WHERE o.created_at >= TIMESTAMP '2026-09-01' AT TIME ZONE 'America/New_York'
    AND o.created_at <  TIMESTAMP '2026-10-01' AT TIME ZONE 'America/New_York'
    AND NOT EXISTS (SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id)
),
refunded AS (                    -- one row per order with a qualifying refund
  SELECT DISTINCT r.order_id
  FROM refunds r
  WHERE r.status IS DISTINCT FROM 'reversed'
)
SELECT
  c.region,
  COUNT(rf.order_id)::numeric / NULLIF(COUNT(*), 0) AS order_refund_rate
FROM base b
JOIN customers c      ON c.customer_id = b.customer_id
LEFT JOIN refunded rf ON rf.order_id = b.order_id
GROUP BY c.region;
```

## Sanity checks

1. **Join integrity:** `SELECT COUNT(*) FROM base` equals the sum of per-region order counts from the query above with `COUNT(*)` added. If it's lower, orders without a matching customer are being dropped.
2. **Bounds:** every region's rate is between 0 and 1, or NULL.
3. **Customer key uniqueness:** `SELECT customer_id FROM customers GROUP BY customer_id HAVING COUNT(*) > 1` returns no rows.
4. **Known-answer fixture:** five orders in September 2026 New York time: one with no refund, one with a single refund, one with two partial refunds, one with only a reversed refund, and one placed by a test account and refunded. Expected rate: 2 of 4 = 50.0%.

## Change log

| Version | Date | Change | Approved by |
|---|---|---|---|
| v1 | 2026-10-01 | Initial definition | pending: finance analytics lead |

## Open decisions

- [ ] Does a refund with NULL status count? Defaulted to yes. Confirm with the finance analytics lead.
- [ ] Lock period of 60 days after month end. Confirm with the finance analytics lead against the refund policy window.
- [ ] Is `customers.customer_id` unique? Check 3 answers it.
- [ ] Support's `refund_tickets` metric needs its own spec, owned by support.

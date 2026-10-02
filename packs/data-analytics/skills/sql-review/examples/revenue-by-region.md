# Worked example: September revenue and refund rate by region (Postgres)

Shows the whole review: the lint as a first pass, the correctness findings the lint can't see, the corrected query, and the checks that prove it. The lint output below is the script's real output on these exact files.

## Input

> Can you check this before it goes into the finance dashboard? It's Postgres. Finance reports in New York time. One row per region. `customers.customer_id` is unique; an order has many `order_items`, and an order can have more than one refund row (partial refunds). `orders.created_at` is `timestamptz`.

```sql
-- September 2026 revenue and refund rate by region (finance reports in New York time)
SELECT
  c.region,
  COUNT(DISTINCT o.order_id)              AS orders,
  SUM(o.amount_usd)                       AS revenue_usd,
  COUNT(r.refund_id) / COUNT(o.order_id)  AS refund_rate
FROM orders o
JOIN customers c     ON c.customer_id = o.customer_id
JOIN order_items oi  ON oi.order_id = o.order_id
LEFT JOIN refunds r  ON r.order_id = o.order_id
WHERE o.created_at BETWEEN '2026-09-01' AND '2026-09-30'
  AND r.status <> 'reversed'
  AND o.customer_id NOT IN (SELECT customer_id FROM test_accounts)
GROUP BY c.region
ORDER BY revenue_usd DESC;
```

The user stated the dialect, grain and key uniqueness, so no questions are asked.

## Step 2: lint

```text
$ python3 scripts/sql_lint.py query.sql --dialect postgres
sql_lint: query.sql (dialect: postgres)

line 6  WARN   integer-division
    > COUNT(r.refund_id) / COUNT(o.order_id)  AS refund_rate
    COUNT / COUNT in postgres: integer divided by integer truncates, so a 0.37 rate comes back as 0. Cast one side (::numeric, CAST(... AS DECIMAL), or * 1.0).

line 11  WARN   between-timestamp
    > WHERE o.created_at BETWEEN '2026-09-01' AND '2026-09-30'
    BETWEEN on what looks like a timestamp column is inclusive at both ends. With a bare-date upper bound it drops everything after midnight on the last day; with a midnight upper bound it double-counts that instant across adjacent windows. Use col >= start AND col < next_day.

line 12  WARN   left-join-where-filter
    > AND r.status <> 'reversed'
    WHERE filters on 'r', the right side of a LEFT JOIN. Rows with no match have NULL there and are dropped, so the LEFT JOIN behaves as an INNER JOIN. Move the condition into the ON clause if you meant to keep them.

line 13  WARN   not-in-subquery
    > AND o.customer_id NOT IN (SELECT customer_id FROM test_accounts)
    NOT IN (subquery) returns zero rows if the subquery yields a single NULL. Use NOT EXISTS, or filter NULLs out of the subquery.

4 finding(s): 0 error, 4 warn, 0 info
```

All four hits are confirmed below. The lint missed the two fan-outs and the timezone, which are the findings that matter most.

## Output

**Verdict: BLOCK — 5 🟥, 2 🟧, 0 🟨.** Every column in this query is wrong today. The `WHERE` on the refunds table keeps only refunded orders, two joins multiply revenue, and the month boundaries are in the wrong timezone and miss 30 September.

### 🟥 1. `order_items` join multiplies revenue (line 9)

- **Where:** `JOIN order_items oi ON oi.order_id = o.order_id`
- **Wrong result:** each order appears once per line item, so `SUM(o.amount_usd)` counts a three-item order three times. Revenue is overstated by the average items per order. `COUNT(DISTINCT o.order_id)` on line 4 hides this in the order count, which is why the revenue looked plausible next to it. No column from `oi` is used.
- **Fix:** delete the join.

### 🟥 2. `refunds` join multiplies revenue again (line 10)

- **Where:** `LEFT JOIN refunds r ON r.order_id = o.order_id`
- **Wrong result:** an order with two partial refunds appears twice, on top of finding 1.
- **Fix:** reduce refunds to one row per order before joining:
  ```sql
  refunded AS (
    SELECT DISTINCT r.order_id
    FROM refunds r
    WHERE r.status IS DISTINCT FROM 'reversed'
  )
  ```
  (`DISTINCT` here sets the grain of a single-table CTE, which is the right use; it isn't hiding a join.)

### 🟥 3. `WHERE r.status` turns the LEFT JOIN into an INNER JOIN (line 12)

- **Where:** `AND r.status <> 'reversed'`
- **Wrong result:** orders with no refund have `r.status` NULL, the comparison is unknown, and they are dropped. The query reports revenue for **refunded orders only**. It also drops refunds whose status is NULL.
- **Fix:** move the condition into the refunds CTE above, using `IS DISTINCT FROM` so NULL-status refunds still count. Whether a NULL status counts as a refund is a business rule: confirm it with finance.

### 🟥 4. Refund rate is integer division (line 6)

- **Where:** `COUNT(r.refund_id) / COUNT(o.order_id)`
- **Wrong result:** in Postgres, `bigint / bigint` truncates. As written, finding 3 means every surviving row has a refund, so the rate returns 1 for every region. Fix finding 3 alone and it returns 0 for every region. Both counts are also inflated by findings 1 and 2.
- **Fix:** `COUNT(rf.order_id)::numeric / NULLIF(COUNT(*), 0)`, counted at order grain.

### 🟥 5. `BETWEEN` loses 30 September (line 11)

- **Where:** `o.created_at BETWEEN '2026-09-01' AND '2026-09-30'`
- **Wrong result:** the upper bound is midnight at the start of 30 September, so the last day of the month is missing.
- **Fix:** half-open window, `>= start AND < next month start` (combined with finding 6).

### 🟧 6. Month boundaries are in the session timezone, not New York (line 11)

- **Where:** the same predicate.
- **Wrong result:** the string literals are read in the session's `TimeZone`. On a UTC server, the window starts and ends four hours away from the New York boundaries (EDT in September), moving orders between August, September and October. The numbers won't match finance's.
- **Fix:** convert the boundaries, not the column, so the predicate stays sargable:
  ```sql
  o.created_at >= TIMESTAMP '2026-09-01' AT TIME ZONE 'America/New_York'
  AND o.created_at <  TIMESTAMP '2026-10-01' AT TIME ZONE 'America/New_York'
  ```

### 🟧 7. `NOT IN` returns nothing if `test_accounts` ever holds a NULL (line 13)

- **Where:** `o.customer_id NOT IN (SELECT customer_id FROM test_accounts)`
- **Wrong result:** correct today only if `test_accounts.customer_id` has no NULLs. One NULL row and the dashboard shows zero orders everywhere.
- **Fix:** `NOT EXISTS (SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id)`.

### Corrected query

```sql
WITH sept_orders AS (            -- one row per order
  SELECT o.order_id, o.customer_id, o.amount_usd
  FROM orders o
  WHERE o.created_at >= TIMESTAMP '2026-09-01' AT TIME ZONE 'America/New_York'
    AND o.created_at <  TIMESTAMP '2026-10-01' AT TIME ZONE 'America/New_York'
    AND NOT EXISTS (
      SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id
    )
),
refunded AS (                    -- one row per refunded order
  SELECT DISTINCT r.order_id
  FROM refunds r
  WHERE r.status IS DISTINCT FROM 'reversed'
)
SELECT
  c.region,
  COUNT(*)                                           AS orders,
  SUM(so.amount_usd)                                 AS revenue_usd,
  COUNT(rf.order_id)::numeric / NULLIF(COUNT(*), 0)  AS refund_rate
FROM sept_orders so
JOIN customers c      ON c.customer_id = so.customer_id
LEFT JOIN refunded rf ON rf.order_id = so.order_id
GROUP BY c.region
ORDER BY revenue_usd DESC;
```

Lint re-run on the corrected query (real output):

```text
$ python3 scripts/sql_lint.py query-fixed.sql --dialect postgres
sql_lint: query-fixed.sql (dialect: postgres)

No mechanical smells found. This does not mean the query is correct;
review joins, grain and date boundaries by reading it.
```

### Verification queries

1. **Revenue reconciles with the source.** The sum of `revenue_usd` across regions should equal:
   ```sql
   SELECT SUM(amount_usd) FROM orders o
   WHERE o.created_at >= TIMESTAMP '2026-09-01' AT TIME ZONE 'America/New_York'
     AND o.created_at <  TIMESTAMP '2026-10-01' AT TIME ZONE 'America/New_York'
     AND NOT EXISTS (SELECT 1 FROM test_accounts t WHERE t.customer_id = o.customer_id);
   ```
   If the region total is lower, some orders have no matching customer and the inner join dropped them.
2. **The customer key really is unique** (the fix depends on it):
   ```sql
   SELECT customer_id, COUNT(*) FROM customers GROUP BY customer_id HAVING COUNT(*) > 1 LIMIT 10;
   ```
3. **Sum of `orders` equals the row count of `sept_orders`**, which proves the joins kept one row per order.

### Assumptions

- `customers.customer_id` is unique (stated by the user; check 2 confirms it).
- A refund with a NULL status counts as a refund. Confirm with finance.
- `amount_usd` is already in USD for every order.
- "September" means order creation time, not payment or ship time.

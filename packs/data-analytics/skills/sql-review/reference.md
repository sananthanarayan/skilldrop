# sql-review reference

The catalogue the review walks, in the order it walks it. Each entry gives the symptom, the wrong result, and the fix. Dialect behaviour is collected in the table at the end. Where a dialect isn't listed, check its documentation rather than assume.

## Correctness

### 1. Join fan-out

- **Symptom:** a join to a table with several rows per key (line items, events, refunds, history or SCD rows), followed by `SUM`, `AVG` or `COUNT(*)` of a column from the other side.
- **Wrong result:** every left-side value is counted once per matching right-side row. Revenue, order counts and averages are all inflated. `COUNT(DISTINCT id)` beside a plain `SUM` is the tell that someone noticed the count and missed the sum.
- **Fix:** aggregate the many-side to the join key in a CTE first, then join one-to-one. Or drop the join if no column from it is used.
- **Verify:** `SELECT key, COUNT(*) FROM right_table GROUP BY key HAVING COUNT(*) > 1 LIMIT 10;` and compare `COUNT(*)` of the base table against the joined row count.

### 2. LEFT JOIN turned into INNER JOIN

- **Symptom:** `WHERE right.col = …` (or `<>`, `>`, `IN`, `LIKE`) on the right side of a `LEFT JOIN`.
- **Wrong result:** unmatched rows have NULL there, the comparison is unknown, and they are dropped. "Orders with their refunds" becomes "refunded orders only".
- **Fix:** move the condition into `ON`, or pre-filter the right side in a CTE. Keep `WHERE right.key IS NULL` only when you mean an anti-join.

### 3. NULL semantics

| Pattern | What happens | Fix |
|---|---|---|
| `x NOT IN (SELECT y …)` with any NULL `y` | Every row's predicate is unknown, so the query returns zero rows | `NOT EXISTS (SELECT 1 … WHERE y = x)` |
| `col = NULL`, `col <> NULL` | Never true | `IS NULL`, `IS NOT NULL`, or `IS DISTINCT FROM` where supported |
| `status <> 'cancelled'` | Rows with NULL status are dropped too | `status IS DISTINCT FROM 'cancelled'`, or `COALESCE(status, '') <> 'cancelled'` |
| `COUNT(col)` vs `COUNT(*)` | `COUNT(col)` skips NULLs | Pick deliberately and say which |
| `AVG(col)` | Ignores NULLs, so the denominator shrinks | `AVG(COALESCE(col, 0))` if a NULL means zero |
| `SUM` over all-NULL input | Returns NULL, not 0 | `COALESCE(SUM(col), 0)` |
| `a || b` with a NULL | NULL in Postgres and Snowflake; `CONCAT` in BigQuery also returns NULL | `COALESCE` each part, or `CONCAT_WS` where available |

### 4. Time and date boundaries

- **`BETWEEN` on timestamps.** `ts BETWEEN '2026-09-01' AND '2026-09-30'` stops at midnight starting 30 September, losing the last day. Use a half-open window: `ts >= '2026-09-01' AND ts < '2026-10-01'`.
- **Whose midnight.** Month and day boundaries are in a timezone. A UTC month is not the New York month; the gap is several hours of orders moving between months at each boundary. Ask which timezone the business reports in and convert the boundaries, not the column (keeps the predicate sargable).
- **Truncation zone.** `date_trunc('day', ts)` on a Postgres `timestamptz` uses the session `TimeZone` setting. BigQuery `DATE(ts)` uses UTC unless you pass a zone: `DATE(ts, 'America/New_York')`. Snowflake `TIMESTAMP_LTZ` values depend on the session `TIMEZONE` parameter; `TIMESTAMP_NTZ` carries no zone at all, so find out what zone was written.
- **DST.** Days are 23 or 25 hours twice a year in zones with daylight saving. Per-hour averages and "last 24 hours" windows shift on those days.
- **Late data.** Events that arrive after the window closes. Say whether the query reads by event time or load time, and whether yesterday's number will change.

### 5. Arithmetic and types

- **Integer division.** `COUNT(a) / COUNT(b)` truncates in Postgres, Redshift and SQL Server, so a 37% rate shows 0. Cast one side.
- **Divide by zero.** Wrap the denominator: `NULLIF(den, 0)`, or the dialect's safe function (table below).
- **Average of averages.** `AVG(daily_conversion_rate)` weights a 10-visit day the same as a 10,000-visit day. Compute `SUM(numerator) / SUM(denominator)`.
- **Implicit casts.** MySQL coerces strings to numbers when compared (`'abc' = 0` is true, and `'12abc' = 12` is true). Snowflake casts implicitly and can fail at runtime when one bad value appears. Postgres and BigQuery refuse most mixed comparisons at compile time. IDs stored as strings with leading zeros stop matching once cast to numbers.
- **Currency.** Summing an amount column across currencies. Convert at a stated rate and date first.

### 6. DISTINCT hiding a bad join

`SELECT DISTINCT` over a join removes duplicate output rows, but any aggregate computed underneath it is still inflated, and two genuinely different rows that happen to match on the selected columns are merged. If `DISTINCT` was added "because there were duplicates", find the join that made them.

### 7. Windows

- **Default frame.** With `ORDER BY` and no frame clause, the SQL standard default (which Postgres follows) is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. So `LAST_VALUE(x)` returns the current row's value (strictly, the last of its peers), and a running `SUM` gives tied rows the same total. Write the frame you mean. Other engines document their own defaults; check them before relying on one.
- **Non-deterministic picks.** `ROW_NUMBER() OVER (PARTITION BY user ORDER BY created_at)` with two rows at the same timestamp picks either one, and can pick differently on each run. Add a tie-breaker column.

### 8. Set operations and grouping

- **`UNION` vs `UNION ALL`.** `UNION` deduplicates. Two identical $20 orders from two sources become one.
- **Non-aggregated columns.** MySQL with `ONLY_FULL_GROUP_BY` disabled returns an arbitrary value for a selected column not in `GROUP BY`. Other engines reject it.
- **NULL groups.** NULLs form their own group in `GROUP BY`; a NULL region row is real money, not noise. Label it, don't drop it.

## Performance (only once correct)

- **Non-sargable predicates.** `WHERE DATE(created_at) = '2026-09-01'` stops a Postgres or MySQL index on `created_at` being used (unless there's an expression index). Compare the bare column to a range.
- **Partition filters.** BigQuery bills bytes scanned; a query on a date-partitioned table without a filter on the partition column scans every partition, and tables can be set to reject such queries (`require_partition_filter`). Postgres declarative partitioning prunes only when the predicate is on the partition key. Snowflake prunes micro-partitions from filter predicates, so filter early on the clustering columns.
- **`SELECT *` on columnar storage.** BigQuery and Snowflake read only the columns named, so `*` reads all of them. In BigQuery, `LIMIT` does not reduce the bytes billed on a non-clustered table.
- **Correlated subqueries.** A subquery in `SELECT` that references the outer row may run once per row. Rewrite as a join to a pre-aggregated CTE.
- **CTEs.** Postgres 12 and later inline a non-recursive CTE referenced once; `MATERIALIZED` forces it to be computed once. Older versions always materialise.
- **`ORDER BY` without `LIMIT`** inside a CTE or subquery is wasted work; the outer query's order is the only one that counts.
- **`COUNT(DISTINCT)`** on large tables is expensive. `APPROX_COUNT_DISTINCT` exists in BigQuery and Snowflake when an approximate figure is acceptable. Say so in the metric definition if you use it.

Always tell the user to check the change with `EXPLAIN` / `EXPLAIN ANALYZE` (Postgres), the query plan and bytes-processed estimate (BigQuery), or the query profile (Snowflake).

## Dialect table

| Behaviour | Postgres | BigQuery | Snowflake | SQL Server | MySQL |
|---|---|---|---|---|---|
| `INT / INT` | Truncates to integer | Returns FLOAT64 (`DIV()` for integer) | Returns a decimal | Truncates to integer | Returns decimal (`DIV` for integer) |
| Divide by zero | Error | Error; `SAFE_DIVIDE` returns NULL | Error; `DIV0` returns 0, `DIV0NULL` returns 0 for NULL or zero divisor | Error | NULL |
| Cast | `x::numeric`, `CAST` | `CAST(x AS FLOAT64)` | `x::float`, `CAST` | `CAST(x AS DECIMAL(18,4))` | `CAST(x AS DECIMAL(18,4))` |
| Date of a timestamp in a zone | `(ts AT TIME ZONE 'America/New_York')::date` on `timestamptz` | `DATE(ts, 'America/New_York')` | `CONVERT_TIMEZONE('America/New_York', ts)::date` | `CAST(ts AT TIME ZONE 'Eastern Standard Time' AS date)` on `datetimeoffset` | `DATE(CONVERT_TZ(ts, 'UTC', 'America/New_York'))` (needs tz tables loaded) |
| `IS DISTINCT FROM` | Yes | Yes | Yes | Yes (SQL Server 2022 and later) | No; use `NOT (a <=> b)` |
| `QUALIFY` | No | Yes | Yes | No | No |

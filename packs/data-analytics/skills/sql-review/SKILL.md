---
name: sql-review
description: Review a SQL query for correctness first and performance second — join fan-out inflating sums, NULL traps in filters and NOT IN, timezone and date-boundary errors, integer division, DISTINCT hiding a bad join, window-frame defaults, implicit casts, non-sargable predicates and missing partition filters — with each finding tied to a line, the wrong number it produces, and corrected SQL for the named dialect. Use when the user pastes a query and asks "is this right", "review my SQL", "why is this number too high", "check this before it goes in the dashboard", or "make this query faster".
---

# sql-review

Reviews a query the way a skeptical analyst would before trusting its output: first, does it return the right number; only then, does it return it cheaply. The failures this skill hunts are the silent ones — the query runs, returns a plausible figure, and is wrong by a factor of two because a join multiplied rows or a filter dropped NULLs. A slow correct query is an annoyance; a fast wrong one ends up in a board deck. The review is dialect-aware because the same SQL means different things in Postgres, BigQuery and Snowflake (integer division alone differs across them).

## How to respond

1. **Pin the dialect and the grain, asking once.** Ask at most 2 questions in one message: *"Which engine runs this (Postgres, BigQuery, Snowflake, Redshift, MySQL, SQL Server)?"* and *"What should one output row represent, and which join keys are unique?"* (for example: "one row per region; `customers.customer_id` is unique, `order_items` has many rows per order"). If the user already said, don't ask. Infer the dialect from syntax when you can — backtick-quoted `project.dataset.table` and `SAFE_DIVIDE` mean BigQuery, `::` casts mean Postgres, Redshift or Snowflake, `TOP n` means SQL Server — and state the inference.

**Non-interactive runs** (subagent, CI, headless): infer the dialect from syntax and tag it `[assumption]`; with no syntax clue, review against the SQL standard and say which findings change by dialect. Assume join keys on dimension tables are unique and on fact or line-item tables are not, tag each such assumption, and turn it into a verification query. No query in the input → emit `BLOCKED: need the SQL query text`.

2. **Run the lint for the mechanical layer.** It flags the smells regex can see — `= NULL`, `JOIN` with no `ON`, `NOT IN (SELECT …)`, `BETWEEN` on timestamps, `COUNT / COUNT` in dialects that truncate, `LAST_VALUE` without a frame, `LEFT JOIN` nullified by `WHERE`, `SELECT *`, `UNION` without `ALL`, functions on filtered columns:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/sql_lint.py" query.sql --dialect postgres
   # Other IDEs (from the skill folder)
   python3 scripts/sql_lint.py query.sql --dialect postgres
   ```

   Use `-` to read from stdin, `--format json -o findings.json` for a file, and `--strict` to exit 1 on any error or warn. The lint does not parse SQL or know the schema. Treat each hit as a place to look: confirm it, or dismiss it in one line with the reason. A clean lint does not mean a correct query. Join fan-out, the most expensive bug, is invisible to it.

3. **Review correctness by reading the query, in this order.** Walk the catalogue in [`reference.md`](reference.md):
   1. **Grain.** For each `JOIN`, ask whether the right side can have more than one row per left row. If it can and the query sums a left-side column, the sum is multiplied. ✅ *"`order_items` has many rows per order, so `SUM(o.amount_usd)` counts each order once per item."* `COUNT(DISTINCT …)` next to a plain `SUM` is the classic tell: someone fixed the count and missed the sum.
   2. **Filters and NULLs.** `NOT IN` with a nullable subquery, `col <> 'x'` silently dropping NULL rows, `WHERE` conditions on the outer side of a `LEFT JOIN`, `COUNT(col)` against `COUNT(*)`.
   3. **Time.** Which timezone the date boundaries are in, whether the reporting window is half-open (`>= start AND < end`), whether `DATE()` or `date_trunc` runs in UTC or the session zone, and whether late-arriving rows belong in the window.
   4. **Arithmetic and types.** Integer division, divide-by-zero, averaging averages (a mean of per-group ratios is not the overall ratio), implicit casts between strings and numbers, and currency mixed without conversion.
   5. **Windows and set operations.** Default frames, ties in `ORDER BY` making `ROW_NUMBER` picks non-deterministic, `UNION` deduplicating rows that should both count.

4. **Then performance, and only for a query that is already correct.** Look for non-sargable predicates, missing partition or cluster filters, `SELECT *` on columnar tables, correlated subqueries that run once per row, `ORDER BY` inside a CTE without a `LIMIT`, and `COUNT(DISTINCT)` where an approximate count would do. Name the cost model: bytes scanned in BigQuery, warehouse time in Snowflake, index use and the plan in Postgres. Tell the user to confirm with `EXPLAIN` or the bytes-billed estimate rather than assert a speed-up you did not measure.

5. **Write every finding in four parts.**
   - **Where:** line number and the quoted fragment.
   - **Severity:** 🟥 wrong number today · 🟧 wrong number when certain data appears (a NULL, a tie, a DST day) · 🟨 cost or speed · ⚪ readability.
   - **Wrong result:** the concrete effect on the output, in business terms. ✅ *"Revenue is overstated by the average number of items per order."* ❌ *"Possible duplication issue."* Don't invent magnitudes; if you can't compute the size, give the query that would.
   - **Fix:** corrected SQL for that fragment, in the user's dialect.

6. **Emit in one message:** a verdict line (`BLOCK`, `FIX FIRST`, `SHIP WITH NOTES`, `SHIP IT`) with the count by severity; the findings, correctness before performance; the **full corrected query**; and **2–4 verification queries** that prove the fix, such as row counts before and after each join, a reconciliation of the total against the source table, and a uniqueness check on each join key the fix depends on. List every assumption you made about keys and types.

## Useful references in this skill

- [`reference.md`](reference.md) — the correctness and performance catalogue, each with the wrong result and the fix, plus a dialect table (integer division, divide-by-zero, timezone functions, window-frame defaults, partition pruning)
- [`examples/revenue-by-region.md`](examples/revenue-by-region.md) — worked example: a Postgres revenue query with seven bugs, the lint's real output, the review, the corrected query, and the lint re-run
- [`scripts/sql_lint.py`](scripts/sql_lint.py) — the mechanical-smell lint (stdlib, Python 3.9+)

## Quality bar

- **Correctness findings come before performance findings**, and a query with an open 🟥 is never given performance advice as its headline.
- **Every finding names a line, the wrong result it produces, and corrected SQL.** A finding without a fix is a complaint.
- **The wrong result is stated in business terms**, such as "refund rate always shows 0", not as "integer division issue".
- **Fixes are in the user's dialect.** No `SAFE_DIVIDE` in a Postgres review, no `::numeric` in BigQuery.
- **Join fan-out is checked for every join**, even when the lint is clean.
- **A full corrected query is provided**, plus verification queries that would show whether the fix worked.
- **Lint hits are triaged, not pasted.** Each one is confirmed or dismissed with a reason.
- **Nothing about the schema is invented.** Key uniqueness, column types and timezones not given are listed as assumptions with a query to check each.

## When to use this skill

- ✅ "Is this query right?" before a number goes into a dashboard, report or deck
- ✅ A metric looks too high or too low and the SQL is the suspect
- ✅ Reviewing a teammate's analytics SQL or dbt model in a pull request
- ✅ A correct query is too slow or too expensive and needs tuning

## When NOT to use this skill

- ❌ Deciding what a metric should mean (formula, filters, owner) — that's `metric-definition`; this skill checks that SQL computes it correctly
- ❌ Designing tables, keys and indexes from access patterns — that's `db-schema-design`
- ❌ Agreeing a dataset's schema, quality SLAs and change policy with its consumers — that's `data-contract`
- ❌ General application code review, including SQL built in application code for security — that's `pre-merge-review`

## Anti-patterns to avoid

- ❌ **Performance first.** Suggesting an index for a query that double-counts revenue. Make it right, then make it fast.
- ❌ **DISTINCT as the fix for duplicates.** Adding `DISTINCT` hides a fan-out in the row count but leaves every `SUM` computed before it inflated. Fix the join grain.
- ❌ **Trusting a clean lint.** The lint can't see join cardinality, timezones or business rules. The worst bugs pass it.
- ❌ **Vague findings.** "Watch out for NULLs" with no line and no wrong result. Name the row that disappears and why.
- ❌ **Dialect-blind fixes.** Telling a BigQuery user to cast to `numeric` for division (BigQuery's `/` already returns FLOAT64), or a Postgres user that `/` on integers is safe.
- ❌ **Asserting a speed-up.** "This will be 10x faster" without a plan or bytes estimate. Say what to measure.
- ❌ **Rewriting the query in your own style.** Keep the user's structure and naming, and change only what the findings require, so the diff is reviewable.

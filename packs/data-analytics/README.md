# Data and analytics

For analysts and the people who rely on their numbers: define a metric once so everyone gets the same figure, review SQL for the bugs that quietly inflate it, and spec dashboards around a decision instead of every chart that was easy to make.

`/plugin install data-analytics@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Check a query before its number goes into a report

Paste this into Claude Code:

```text
Review this Postgres query before it goes into the finance dashboard. One row per region; customers.customer_id is unique and an order has many order_items. Finance reports in New York time.

SELECT c.region, SUM(o.amount_usd) AS revenue_usd
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.created_at BETWEEN '2026-09-01' AND '2026-09-30'
GROUP BY c.region;
```

- **Before you start:** A SQL query whose number you need to trust, and the database it runs on
- **How to tell it worked:** sql-review opens with a verdict, flags the order_items join as multiplying revenue and the BETWEEN as losing 30 September, gives a corrected query with New York boundaries, and lists verification queries to prove the fix.
- **If nothing happens:** If the review jumps to indexes before correctness, ask for it by name ("use sql-review"). If it guesses the database, tell it which one: integer division and timezone functions differ between engines.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `dashboard-spec`
- `doc-critique`
- `metric-definition`
- `output-hygiene`
- `sql-review`

More: https://sananthanarayan.github.io/skilldrop/packs/data-analytics/

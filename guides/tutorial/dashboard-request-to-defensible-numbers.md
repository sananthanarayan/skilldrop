---
title: From a dashboard request to numbers people can defend
summary: Run the measure loop on a real request. The spec cuts the charts that serve no decision, the SQL review catches a join that inflated revenue, and the loop stops for the metric owners instead of picking between two teams' definitions of an active customer.
kind: tutorial
---

# From a dashboard request to numbers people can defend

In about fifteen minutes you'll run the `measure` loop on a dashboard request and one SQL
query. You'll see it cut half the requested charts before reading any SQL, and catch a join
that counted every order once per line item. Then it stops: two teams define "active
customer" differently, and only they can choose. A BI developer can then build from the
spec without guessing.

Everything quoted below is from a real run of the loop on Claude Sonnet 5 with the prompt
and query on this page.

## Install the loop

```bash
npx skilldrop-cli install --loop measure
```

This installs the loop with `dashboard-spec`, `sql-review` and `doc-critique`. Each skill
also works on its own; the loop decides their order and the gates between them.

## Write the query the dashboard will use

Save this as `revenue.sql`. It looks fine, and its total is wrong:

```sql
SELECT c.region,
       date_trunc('week', o.created_at) AS week,
       SUM(o.amount_usd) AS revenue_usd
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.created_at BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY c.region, date_trunc('week', o.created_at);
```

## Start the loop with the request as it arrived

> Run the measure loop. Regional sales leads want a dashboard to decide each Monday where to
> send the two floating account managers. They asked for: weekly revenue by region, revenue
> all time, website sessions, active customers, average deal size by region, and a map.
> Revenue's query is in revenue.sql (Postgres; one row per region per week;
> customers.customer_id is unique and an order has many order_items). Nobody has written down
> what 'active customer' means; sales counts anyone with an open opportunity, finance counts
> anyone invoiced in 90 days.

## Watch the spec cut before any SQL is read

The loop runs `dashboard-spec` first and writes the decision in one sentence:

> **Decision:** Each Monday, regional sales leads decide which region(s) get the two floating
> account managers for the week.

Every requested chart is held against that sentence. Three don't survive:

| Requested item | Why it's cut |
|---|---|
| Revenue, all time | Cumulative total only goes up; doesn't change which region needs an AM this week |
| Website sessions | Activity with no outcome attached for this audience |
| Map | Ranking by region is answered more precisely by the sorted bars |

Two metrics are marked `undefined: needs a spec before build`: active customers, because
sales and finance disagree, and average deal size, because nobody has said whether a deal
is an order or a CRM opportunity. The loop doesn't choose a definition for them.

## See the review fail the revenue query at G9

Only the revenue query is behind a surviving chart, so only it is reviewed. `sql-review`
returns **BLOCK**. The `order_items` join repeats each order once per line item, so
`SUM(o.amount_usd)` overstates revenue by the average number of items per order. The fixed
date range can't serve a dashboard that refreshes every Monday. G9 says `NOT READY`, and the
loop goes back to the spec, because the fix changes the number the chart will show.

The corrected query drops the join and uses a rolling, half-open window:

```sql
SELECT COALESCE(c.region, 'Unknown') AS region,
       date_trunc('week', o.created_at) AS week,
       SUM(o.amount_usd) AS revenue_usd
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.created_at >= date_trunc('week', now()) - interval '8 weeks'
  AND o.created_at <  date_trunc('week', now())
GROUP BY COALESCE(c.region, 'Unknown'), date_trunc('week', o.created_at);
```

Reviewed again, it gets **SHIP WITH NOTES**, so G9 says `READY`. Two notes travel to the
build. A region-week with no orders produces no row, so the chart must draw it as zero, not
a gap. And the week boundary follows the database session's time zone, which nobody has
confirmed matches the sales leads' week.

Each review ends with verification queries, such as row counts before and after each join
and a reconciliation of the total against the `orders` table. Run them against your
database before you trust the fix. They also tell you how far the old number was off, which
the revenue owner will ask.

## Stop for the owners at G9.1

The loop ends without a person present:

> `BLOCKED: need each metric owner's confirmation of active customer and average deal size.`

That is the right ending. A query can be correct and still compute the wrong thing, and
picking between sales and finance would settle their disagreement by guessing. Take the
spec to both teams. When they agree a definition, tell the loop. It goes back to `spec`,
reviews the new query at G9, and returns to G9.1. If no one owns a metric, its chart moves
to the cut list.

The revenue owner has to confirm too, even though the query passed G9. The review shows
that the SQL computes the definition. Only the owner can say the definition is what the
business means.

## What you have now

A spec with the decision written down and a cut list with reasons. Each surviving chart
names its metric, and the one metric with SQL has a reviewed query and the notes the build
must honour. The two open definitions are named with the people who have to settle them.
Nothing is built until the owners sign.

Next: [The loops, stage by stage](../reference/loops.md) for the `measure` diagram, or
[Use the data-analytics pack](../how-to/packs/use-the-data-analytics-pack.md) to run one skill
on its own.

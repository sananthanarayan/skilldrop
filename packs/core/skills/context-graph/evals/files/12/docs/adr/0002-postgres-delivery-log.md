# ADR-0002: Postgres for the delivery log

- Status: Accepted
- Date: 2022-03-10
- Governs: `src/store/`

## Context
Partners dispute whether a webhook was sent. We need a durable, queryable record of every attempt.

## Decision
Every delivery attempt is written to the `delivery_attempts` table in the service's Postgres
database (event_id, partner_id, attempt_no, status_code, sent_at).

## Consequences
Support can answer "did we send it?" with a query. The table grows ~2M rows/month; partition by month.

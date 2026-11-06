# ADR-0006: Move idempotency keys to Postgres

- Status: Accepted
- Date: 2023-09-04
- Supersedes: ADR-0003
- Governs: `src/idempotency/pg_store.py`, `migrations/003_idempotency_keys.sql`

## Context
INC-1874 (2023-08-22): a Redis failover lost the idempotency keyspace and ~41,000 duplicate
webhooks went to partners in one hour.

## Decision
Idempotency keys move to the `idempotency_keys` table in Postgres with a unique constraint on
(event_id, partner_id). The dispatcher inserts with ON CONFLICT DO NOTHING and only dispatches
if a row was inserted. Rows older than 7 days are purged nightly. Redis is no longer used for idempotency.

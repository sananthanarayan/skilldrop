# ADR-0007: Remove Redis; use Postgres advisory locks for the invoice run

- Status: Accepted
- Date: 2024-02-20
- Deciders: Priya Okafor, Tomasz Lind, Wen Haddad
- Supersedes: ADR-0004
- Relates to: ADR-0002

## Context

Redis is used for exactly one thing: the invoice-run lock from ADR-0004. Running it costs a
managed instance and an on-call runbook. In January 2024 a Redis failover dropped the lock
mid-run and a second replica started; the idempotency check on `invoice_runs` caught it, but
only just.

## Decision

Remove Redis. The nightly run takes a session-level Postgres advisory lock with
`pg_try_advisory_lock(727001)` on a dedicated connection and holds it for the whole run.
Implemented in `src/ledgerline/scheduler/lock.py`.

## Consequences

- Back to one datastore, as ADR-0002 intended.
- Advisory locks are session-scoped: the lock connection must NOT go through PgBouncer in
  transaction-pooling mode, or the lock is released as soon as the transaction ends.
- If the lock-holding process dies, Postgres releases the lock when the session closes.

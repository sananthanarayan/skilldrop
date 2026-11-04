# ADR-0001: PostgreSQL is the system of record

- Status: Accepted
- Date: 2024-03-11
- Deciders: Platform team

## Context

Ledgerline needs one transactional store for tenants, customers, invoices and payments. We considered PostgreSQL, MySQL and a document store.

## Decision

PostgreSQL 15 (managed) is the single system of record for all billing data. Read replicas may be used for reporting and other read-heavy workloads; nothing writes to a replica.

## Consequences

- Heavy reads (reports, exports) should go to the read replica, not the primary.
- Replica lag is normally under 2 seconds; features that read from the replica must tolerate that.

## Governs

- `services/billing-api/db/`
- `infra/postgres/`

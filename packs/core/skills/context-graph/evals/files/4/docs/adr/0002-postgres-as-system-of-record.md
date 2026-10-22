# ADR-0002: Postgres is the system of record

- Status: Accepted
- Date: 2023-01-16
- Deciders: Priya Okafor

## Context

Invoices, line items and payment allocations need transactional integrity.

## Decision

All persistent state lives in a single Postgres 15 database. Access goes through
`src/ledgerline/db/`.

## Consequences

No second datastore is introduced without a new ADR.

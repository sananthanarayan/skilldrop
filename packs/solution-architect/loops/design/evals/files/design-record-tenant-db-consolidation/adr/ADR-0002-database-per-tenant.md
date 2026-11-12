# ADR-0002: One database per tenant

- **Status:** Accepted
- **Date:** 2023-10-16
- **Decider:** Rosalind Achebe-Marr

## Context

Tillowmere customers are accountancy practices. Their data is their clients' financial records. We had three tenants and expected about twenty within three years.

## Decision

Each tenant gets its own Postgres database. The application picks the database from the tenant in the request; there is no `tenant_id` column.

## Consequences

- A query bug cannot return another tenant's rows, because the rows are not there.
- We can restore one tenant to a point in time without touching anyone else.
- We can place a tenant's database in whichever cluster (and so region) the tenant needs.
- Every schema migration runs once per tenant. Accepted while tenants are few.

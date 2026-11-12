# ADR-0006: Where we host

- **Status:** Accepted
- **Date:** 2025-03-24
- **Decider:** Rosalind Achebe-Marr

## Context

Most tenants are UK practices. Two prospective tenants needed their data hosted in the EU.

## Decision

Our primary region is uk-south. We run a second Postgres cluster, `pg-eu1`, in eu-central for tenants that need EU hosting. Application servers run in both regions and route each tenant to its cluster.

## Consequences

- Tenants can be hosted in the UK or the EU.
- A second cluster to run and patch.

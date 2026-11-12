# ADR-0004: Backups and point-in-time restore

- **Status:** Accepted
- **Date:** 2024-05-07
- **Decider:** Rosalind Achebe-Marr

## Context

Customers occasionally delete or overwrite records by mistake and ask us to get them back.

## Decision

Each cluster keeps continuous WAL archiving and a nightly base backup, retained for 14 days, stored in the same region as the cluster. Point-in-time restore is done per database.

## Consequences

- We can restore any tenant to any point in the last 14 days.
- Backups never leave the cluster's region.

# ADR-0009: Catalogue database on managed Postgres

## Status
Accepted

## Context
We were spending too much time patching our own database hosts.

## Decision
The catalogue database (products, prices, stock, orders) runs on the hosting provider's
managed Postgres, version 16. Only extensions on the provider's allowlist can be
installed; the allowlist includes `pg_trgm` and `unaccent`.

## Consequences and risks
Patching and failover are the provider's job. We cannot install extensions outside the
allowlist. Owner: platform team.

## Alternatives considered
Self-managed Postgres on our own hosts; rejected for the patching load.

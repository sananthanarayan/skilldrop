# 6. Generate service clients from an OpenAPI spec

Date: 2024-06-03

## Status

Accepted

## Context

Three internal teams call the ledger and each hand-wrote a client.

## Decision

The ledger's public interface is defined in `api/openapi.yaml`. Clients are generated from it
into `clients/generated/` on every release; hand-written clients are not accepted.

## Consequences

- The spec is the source of truth; the server is checked against it in CI.

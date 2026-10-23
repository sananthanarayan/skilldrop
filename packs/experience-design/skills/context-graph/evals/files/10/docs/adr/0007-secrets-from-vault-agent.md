# ADR-0007: Runtime secrets come from the Vault agent, never from environment variables

- Status: Accepted
- Date: 2023-09-02
- Governs: `services/billing-api/config/`, `services/ledger-worker/config/`

## Context

A 2023 incident review found database passwords in a crash dump's environment block.

## Decision

All runtime secrets (database credentials, signing keys, processor API keys) are read from
JSON files rendered by the Vault agent sidecar under `/vault/secrets/`. Services must not read
secrets from environment variables, and no secret may be committed to the repository.

## Consequences

- Local development uses `/vault/secrets/` files rendered by `make dev-secrets`.

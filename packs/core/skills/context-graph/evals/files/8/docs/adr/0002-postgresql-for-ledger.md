# 2. Use PostgreSQL for ledger storage

Date: 2024-01-22

## Status

Accepted

## Context

The ledger needs transactional writes across journal entries and account balances, and the
team already operates PostgreSQL for two other services.

## Decision

Ledger state lives in PostgreSQL. Schema changes are plain SQL migrations under
`services/ledger/db/migrations/`, numbered sequentially and never edited once merged.

## Consequences

- Balances are computed inside a transaction with the entries that change them.
- No ORM-generated migrations.

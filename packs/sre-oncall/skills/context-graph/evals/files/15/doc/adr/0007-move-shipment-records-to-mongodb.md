# 7. Move shipment records to MongoDB

Date: 2022-08-22

## Status

Accepted

## Context

Enterprise customers want custom fields on shipments (purchase order numbers,
temperature bands, hazmat codes) that differ per customer. Every new field
currently needs a PostgreSQL migration.

## Decision

Shipment records will be stored as documents in MongoDB, owned by
`services/shipments/`, so per-customer fields need no schema migration.

## Consequences

Status transitions that touch several stops lose multi-row transactions
unless we use MongoDB multi-document transactions.

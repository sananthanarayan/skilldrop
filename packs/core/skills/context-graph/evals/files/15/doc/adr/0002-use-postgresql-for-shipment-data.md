# 2. Use PostgreSQL for shipment data

Date: 2021-02-10

## Status

Accepted

## Context

Shipments, stops and consignees are relational and need transactional
updates when a stop is marked delivered. The team already runs PostgreSQL 13.

## Decision

Shipment data lives in a single PostgreSQL database, `haulmark_core`, owned by
`services/shipments/`. Other services read shipment data only through the
shipments API, never by connecting to the database directly.

## Consequences

Strong consistency for status transitions. Schema migrations are needed for
new shipment fields.

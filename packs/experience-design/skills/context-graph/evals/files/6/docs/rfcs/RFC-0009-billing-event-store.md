# RFC-0009: Billing writes go to an append-only event store

- Status: Accepted
- Date: 2024-08-14
- Author: R. Achebe
- Governs: `services/billing/`
- Builds on: RFC-0012 (event schema registry)

## Proposal
Billing records every charge and correction as an immutable event in the DynamoDB table
`billing-events`. Current balances are projections of the event stream. This gives auditors a full
history of corrections.

## Rollout
Phase 1: write events alongside the existing store. Phase 2: read balances from projections.

# RFC-0010: Merge billing and invoicing into a revenue service

- Status: Proposed
- Date: 2026-09-30
- Author: L. Brandt
- Governs: `services/revenue/` (new)

## Proposal
Move `services/billing/` and `services/invoicing/` into a single deployable at `services/revenue/`,
with `billing/` and `invoicing/` as internal modules. Both old folders are deleted after the move.

## Records affected
- ADR-0002 (billing storage) — path changes to `services/revenue/billing/`.

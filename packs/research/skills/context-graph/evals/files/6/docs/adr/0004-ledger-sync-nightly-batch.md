# ADR-0004: Ledger sync runs as a nightly batch

- Status: Accepted
- Date: 2023-09-12
- Deciders: L. Brandt
- Governs: `services/ledger-sync/`

## Decision
Ledger sync to the finance system runs once a night at 02:00 UTC as a batch job, not as a stream.

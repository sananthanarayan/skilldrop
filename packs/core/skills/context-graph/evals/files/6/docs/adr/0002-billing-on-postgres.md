# ADR-0002: Billing data lives in Postgres

- Status: Accepted
- Date: 2023-05-03
- Deciders: H. Okafor, M. Szabo
- Governs: `services/billing/`

## Decision
The billing service stores charges and the invoice ledger in the shared Postgres cluster
(table `invoices_ledger`). Writes are transactional updates in place.

## Consequences
Reporting can join billing tables directly. Corrections overwrite the row and keep no history.

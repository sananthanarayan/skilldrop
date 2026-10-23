# Tallowmere Payments Platform

Two services:

- `services/billing-api` — HTTP API that creates invoices and takes card-on-file charges.
- `services/ledger-worker` — consumes billing events and writes the double-entry ledger.

Architecture decisions live in `docs/adr/`.

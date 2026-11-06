# Erasure automation: systems and discussion notes

Notes by Kasimir (eng lead, Customer Platform), from the thread and the 1 Oct call.

## Where customer personal data lives

| # | System | Personal data | Owner | Deletion today |
|---|--------|---------------|-------|----------------|
| 1 | Accounts DB (Postgres) | name, email, phone, addresses | Identity team (Rafael) | soft-delete flag; hard-delete script exists, run by hand |
| 2 | Orders DB (Postgres) | delivery address, phone, delivery notes, gift messages, invoices | Commerce team (Mei) | none |
| 3 | Search index | display name on reviews | Discovery team (Sunniva) | rebuilt nightly from Accounts and Reviews, so follows Accounts within 24h |
| 4 | Postwing (email/CRM, SaaS) | email, name, campaign history | Marketing ops (Jorge) | delete API exists, used by hand |
| 5 | Helpstack (support desk, SaaS) | tickets, free text | Support (Anneke) | delete API per ticket, used by hand |
| 6 | Data warehouse | copies of 1, 2, 4, 5 plus event logs keyed by customer_id | Data platform (Tunde) | none, partitions are append-only |
| 7 | Fraud scoring store | device fingerprints, email hash, address hash | none. Was the Risk team, which was dissolved in the June reorg. Nobody has picked it up | unknown, nobody on the call knew |

## Things people said

- Petra (Finance): invoices, including the customer name and billing address on them, have to
  be kept for 10 years for tax. "We cannot delete those, full stop."
- Mei: we could strip everything on an order that is not on the invoice (phone, delivery notes,
  gift messages) and keep the invoice itself.
- Backups: Accounts DB and Orders DB backups are immutable snapshots kept for 35 days. You
  cannot remove single rows from them. Ottilie has not been told this yet.
- Tunde: deleting from the warehouse means rewriting partitions. He suggested a tombstone table
  plus a weekly compaction job. "A few weeks of work", not scoped.
- Identity verification stays with support, as now. Not changing.
- Nobody has ever timed how long support spends on an erasure request.

## Approaches discussed

a. Central orchestrator: one new service calls each system's delete API in turn and tracks
   state per request. Rafael likes the single place to look. Mei does not want another team's
   service holding delete rights on the Orders DB.
b. Event-based: publish `customer.erasure_requested` on the existing event bus. Each owning team
   writes a consumer that deletes its own data and publishes an acknowledgement. A small ledger
   records acks per system per request, and flags any system that has not acked in N days.
   Most people leaned this way. Concern: a system with no owner never acks.
c. Keep it manual but move it from the spreadsheet into the ticketing tool with SLA timers and
   escalation. Cheapest. Does not remove the manual deletes.

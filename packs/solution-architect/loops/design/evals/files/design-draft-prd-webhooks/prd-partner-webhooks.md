# PRD: Partner webhooks

- **Product:** Ledgerline
- **Author:** Sam Okonkwo (PM, Integrations)
- **Status:** DRAFT — not yet reviewed
- **Tracking:** LDG-2341

## Problem

Partners who build on Ledgerline (accounting connectors, dunning tools) poll our REST API every few minutes to find out whether invoices have changed. Two partners have told us polling is costing them API quota and that they see changes late.

## Goals

- Partners find out about invoice changes without polling.

## Requirements (draft)

| ID | Priority | Requirement |
|---|---|---|
| R1 | Must | A partner can register an HTTPS endpoint URL per tenant connection. |
| R2 | Must | We send an event to that URL when an invoice is created, updated, paid or voided. |
| R3 | Must | Event body includes invoice ID, event type, timestamp, and the invoice as returned by `GET /v2/invoices/{id}`. |
| R4 | Should | Failed deliveries are retried. |
| R5 | ? | Partners can replay events from the last N days. |

## Non-goals

- Webhooks for objects other than invoices (customers, payments) in v1.

## Open questions

1. **Delivery guarantee.** At-least-once, or do partners need ordering per invoice? Two partners asked for "exactly once"; we haven't asked what they'd accept. — *owner: Sam, not started*
2. **Volume.** We don't know how many events this produces. Invoice updates per day across all tenants is not something we currently measure. "Somewhere between thousands and a lot." — *owner: data team, not started*
3. **Retry window.** How long do we keep retrying a failing partner endpoint? — *not discussed*
4. **R5 replay.** In or out of v1? — *not discussed*
5. **Who registers the URL** — the partner, or the tenant's admin when they connect the partner? — *not discussed*

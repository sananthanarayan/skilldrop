---
rfc: 0003
title: Represent money as integer minor units
status: accepted
date: 2024-03-04
authors: [mira.okafor]
governs:
  - src/payments/amount.ts
  - src/payments/charge.ts
---

# RFC-0003: Represent money as integer minor units

## Problem

A refund of 19.99 was stored as 19.989999999999998 after a floating-point
round trip, and the ledger failed to reconcile.

## Decision

All monetary amounts inside the service and on the wire are integers in the
currency's minor unit (cents for USD, pence for GBP), in a field named
`amountMinor`, paired with an ISO 4217 `currency` code. No decimal or
floating-point money fields anywhere in `src/payments/`. Conversion to a
display string happens only at the edge, via `formatAmount()` in
`src/payments/amount.ts`.

## Consequences

- API consumers must send `amountMinor: 1999`, not `amount: 19.99`.
- Currencies with three minor digits (e.g. KWD) work without special cases.

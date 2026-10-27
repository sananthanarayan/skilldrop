---
rfc: 0006
title: Move idempotency handling to the API gateway
status: proposed
date: 2024-09-30
authors: [tomas.vey]
governs:
  - src/payments/charge.ts
---

# RFC-0006: Move idempotency handling to the API gateway

## Problem

Three services now implement their own idempotency-key tables, each slightly
differently.

## Proposal

Enforce `Idempotency-Key` once at the API gateway and remove the per-service
checks, including the one RFC-0001 put in the charge handler.

## Open questions

- The gateway team has not yet committed to a delivery date.
- How are responses replayed for keys the gateway has seen?

Not yet reviewed. Until this is accepted, RFC-0001 stands.

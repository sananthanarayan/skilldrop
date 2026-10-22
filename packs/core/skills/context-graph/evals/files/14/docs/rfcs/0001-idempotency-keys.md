---
rfc: 0001
title: Idempotency keys on every charge request
status: accepted
date: 2024-02-12
authors: [mira.okafor]
governs:
  - src/payments/charge.ts
---

# RFC-0001: Idempotency keys on every charge request

## Problem

Mobile clients retry on flaky networks. Without a dedupe key, a retried
`POST /charges` can bill a customer twice. We had 14 double-charge tickets in
January 2024.

## Decision

Every `POST /charges` request MUST carry an `Idempotency-Key` header. The
charge handler rejects requests without one (HTTP 400) and stores the key with
the charge for 24 hours. A repeat key returns the original response instead of
creating a new charge.

The check lives in the charge handler itself, not in the retry layer: the
retry layer only sees our own outbound retries to the card processor, not
inbound client retries.

## Consequences

- Clients must generate a UUID per logical charge.
- The `idempotency_keys` table grows; rows expire after 24 hours.

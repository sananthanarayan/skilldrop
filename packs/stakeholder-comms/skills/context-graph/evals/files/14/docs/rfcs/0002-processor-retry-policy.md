---
rfc: 0002
title: Fixed-interval retries to the card processor
status: superseded
superseded_by: 0005
date: 2024-02-20
authors: [dev.raman]
governs:
  - src/payments/retry.ts
---

# RFC-0002: Fixed-interval retries to the card processor

## Problem

Calls to the card processor occasionally time out. We need a retry policy.

## Decision

Retry failed processor calls up to 3 times with a fixed 2-second delay
between attempts.

## Consequences

- Simple to reason about.
- Under a processor outage every instance retries in lockstep.

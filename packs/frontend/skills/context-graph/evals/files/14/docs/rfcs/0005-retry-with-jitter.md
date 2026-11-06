---
rfc: 0005
title: Exponential backoff with full jitter for processor retries
status: accepted
supersedes: 0002
date: 2024-06-03
authors: [dev.raman, mira.okafor]
governs:
  - src/payments/retry.ts
---

# RFC-0005: Exponential backoff with full jitter for processor retries

## Problem

During the processor outage on 2024-05-21, RFC-0002's fixed 2-second retries
made all 40 instances hit the processor in synchronised waves, extending the
outage on our side by about 25 minutes.

## Decision

Replace RFC-0002. Retry failed processor calls up to 4 times using
exponential backoff with full jitter: before attempt `n`, wait a random delay
between 0 and `min(8000, 250 * 2^n)` milliseconds. Never retry a 4xx response
from the processor.

## Consequences

- Retries spread out; no lockstep under outage.
- Worst-case added latency is bounded at roughly 15 seconds.

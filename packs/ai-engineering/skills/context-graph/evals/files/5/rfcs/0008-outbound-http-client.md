---
id: RFC-0008
title: One outbound HTTP client
status: accepted
date: 2025-09-30
authors: [Dara Mensah]
governs: [lib/http/, services/ingest/client.ts, services/export/client.ts]
amends: [RFC-0001]
cites: [RFC-0007]
---

# RFC-0008: One outbound HTTP client

## Decision

All outbound HTTP calls go through `lib/http/client.ts`. It sets timeouts, tracing headers and
applies retries uniformly (fixed 500 ms, 3 attempts). This amends RFC-0001 to allow `lib/http/`
as a second shared package. Idempotency keys are handled as described in RFC-0007.

## Rollout

Services migrate their `client.ts` to `lib/http/` during Q4 2025.

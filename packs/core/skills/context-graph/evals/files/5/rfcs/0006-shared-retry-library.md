---
id: RFC-0006
title: Extract a shared lib/retry package
status: rejected
date: 2025-06-19
authors: [Lucía Ferraro]
cites: [RFC-0001, RFC-0003]
---

# RFC-0006: Extract a shared lib/retry package

## Proposal

Move `services/ingest/retry.ts` and `services/export/retry.ts` into one `lib/retry/` package
with a single default policy.

## Outcome: rejected

- Export calls to the partner billing API are NOT idempotent; export only retries on 503
  responses that carry an `Idempotency-Key` echo. A single default policy would retry
  unsafe calls.
- RFC-0001 keeps runtime code per service.

Revisit only if RFC-0001 is superseded.

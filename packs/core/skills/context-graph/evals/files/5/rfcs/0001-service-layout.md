---
id: RFC-0001
title: Service layout and shared code
status: accepted
date: 2024-11-02
authors: [Dara Mensah]
governs: [services/, lib/]
---

# RFC-0001: Service layout and shared code

## Decision

Each service under `services/<name>/` owns its own client, retry and error-handling code.
The only shared package is `lib/types/` (pure type definitions, no runtime behaviour).

## Why

Ingest and export talk to different partners with different idempotency guarantees. A shared
runtime library would couple their failure behaviour and force lock-step releases.

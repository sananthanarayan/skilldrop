---
status: accepted
date: 2023-11-20
deciders: platform team
---

# Rate-limit the public API with a shared token bucket

## Context and Problem Statement

A partner's misconfigured sync job hit `/v1/products` 40 times a second for an hour. We need
per-API-key limits that hold across all app containers.

## Considered Options

* Per-container in-memory limiter
* Token bucket in Redis, shared by all containers
* Limit at the CDN edge

## Decision Outcome

Chosen option: "Token bucket in Redis", because limits must be global and the CDN plan we
are on cannot key on API key.

Implemented in `src/middleware/rateLimit.ts`: 600 requests per minute per API key, using a
Lua script so refill-and-take is atomic. Redis availability and failover are covered in
DR-007.

### Consequences

* Good, because limits are exact across containers.
* Bad, because if Redis is down the limiter fails open.

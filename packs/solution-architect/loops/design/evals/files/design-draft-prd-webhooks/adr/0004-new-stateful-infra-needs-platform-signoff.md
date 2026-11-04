# ADR-0004: New stateful infrastructure needs Platform sign-off

- Status: Accepted
- Date: 2025-08-14
- Deciders: Platform team, Engineering leadership

## Context

In 2025 three product teams each stood up their own stateful component (a second Redis, an Elasticsearch cluster, a RabbitMQ). Two had no on-call owner when they failed. Platform ended up running all three.

## Decision

No team adds a new stateful infrastructure component (database, message broker, streaming platform, search cluster, cache) to production without a Platform team review and a named on-call owner. Requests go through the Platform intake (PLAT board); the review takes about two weeks.

## Consequences

- Product teams should prefer the existing PostgreSQL, Redis job queue and object storage where they fit.
- A design that needs a new component must name it, state why the existing ones do not fit, and include the Platform review in its timeline.

## Governs

- `infra/`

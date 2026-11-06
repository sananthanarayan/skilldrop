---
status: accepted
date: 2026-02-10
---
# Order events on SQS

## Context

Only two consumers ever replayed, and the Kafka cluster is the team's largest on-call load.

## Decision

Supersedes ADR-0004. Order events move to SQS queues, one per consumer, published from
`services/orders/`. The bridge in `services/kafka-bridge/` is removed once billing has moved.

## Consequences

One fewer system to run, and the volume fits SQS. Replay for a new consumer now means a
backfill from the orders table.

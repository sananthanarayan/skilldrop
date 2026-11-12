# ADR-0003: Idempotency keys in Redis

- Status: Accepted
- Date: 2022-05-02
- Governs: `src/idempotency/redis_store.py`

## Context
The tracking platform delivers events at-least-once. Partners complained about duplicate webhooks.

## Decision
Before dispatching, the dispatcher sets `idem:{event_id}:{partner_id}` in Redis with NX and a
24h TTL. If the key already exists the event is dropped as a duplicate.

## Consequences
Fast and simple. If Redis is flushed or evicts keys under memory pressure, duplicates can get through.

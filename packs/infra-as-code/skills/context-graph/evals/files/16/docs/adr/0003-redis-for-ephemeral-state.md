# ADR-0003: Redis for short-lived state

Status: Accepted
Date: 2025-02-03
Deciders: Tomás Okafor
Governs: services/payments/redis_client.py

## Decision

Short-lived, reconstructable state (rate-limit counters, idempotency records)
lives in Redis with an explicit TTL on every key. Nothing in Redis is the
system of record.

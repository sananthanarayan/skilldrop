# 5. Retry failed background jobs

Date: 2024-03-04

## Status

Accepted

## Decision

A failed job in `services/worker/` is retried three times, then moved to a dead-letter queue.
Retry timing follows the backoff policy in ADR-0011.

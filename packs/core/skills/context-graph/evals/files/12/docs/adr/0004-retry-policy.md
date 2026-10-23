# ADR-0004: Retry policy for failed deliveries

- Status: Accepted
- Date: 2022-06-20
- Governs: `src/delivery/retry.py`, `config/delivery.yaml`

## Context
Partner endpoints go down. Retrying too aggressively has had us rate-limited and blocked by two partners.

## Decision
Retry failed deliveries with exponential backoff: delay = 30s * 2^(attempt-1), at most 6 attempts
(last retry roughly 16 minutes after the first). After the 6th failure, publish the event to the
dead-letter queue `parcelhook.dlq` for manual replay.

## Consequences
A partner outage of more than ~30 minutes means events land in the DLQ and need replaying.

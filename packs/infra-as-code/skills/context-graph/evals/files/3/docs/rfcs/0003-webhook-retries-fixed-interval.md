# RFC-0003: Fixed-interval webhook retries

Date: 2024-08-01

## Status

Superseded by [RFC-0006](0006-webhook-retry-backoff.md)

## Context

Merchants miss payment events when their endpoint is briefly down.

## Decision

`services/payments/webhooks/retry.py` retries a failed webhook every 30 seconds, up to 100 times.

## Consequences

Simple to reason about. A merchant endpoint that is down gets a request every 30 seconds.

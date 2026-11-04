# Runbook: webhook-dispatcher

Owner: payments-core
Last reviewed: 2026-06-18

## What it does

Delivers payment event webhooks (payment.succeeded, payment.failed, refund.created, payout.paid) to merchant endpoints. Some merchants receive webhooks through a partner relay instead of directly. Failed deliveries are retried with exponential backoff for up to 72 hours.

## Dashboards

- "webhook-dispatcher overview": delivery latency p50/p95, retry queue depth, error rate by destination host.

## Alerts

- WebhookDeliveryLatencyHigh — p95 delivery latency > 2m for 10m. Pages payments on-call.

## Common problems

### Retry queue growing

1. Check the error rate by destination host on the dashboard.
2. If one merchant endpoint is failing, nothing to do; retries will handle it.
3. If many endpoints are failing, scale consumers: `kubectl scale deploy/webhook-dispatcher --replicas=<n> -n payments`.

### Deploy rollback

`helm rollback webhook-dispatcher <revision> -n payments`

## Escalation

1. Payments on-call
2. payments-core lead
3. Status page: on-call posts; comms lead for anything over 1 hour

## Known gaps

- No guidance yet for partner relay problems.

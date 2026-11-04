# ADR-0002: Long-running work goes through the job queue

- Status: Accepted
- Date: 2024-06-02
- Deciders: Platform team, Billing team

## Context

Request handlers in billing-api were timing out on PDF generation and large reports, holding database connections for minutes. The load balancer cuts requests at 30 seconds.

## Decision

Any work expected to take more than 5 seconds, or that calls an external system, runs as a job on the existing Redis-backed job queue (`jobs-worker` service), never in the request path. The request handler enqueues the job and returns. Jobs must be idempotent and safe to retry; the queue retries a failed job up to 3 times with exponential backoff.

## Consequences

- `jobs-worker` concurrency is capped at 20 jobs per pod, 4 pods.
- The queue does not guarantee ordering between jobs.

## Governs

- `services/jobs-worker/`
- `services/billing-api/jobs/`

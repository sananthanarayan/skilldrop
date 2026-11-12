# ADR-0004: Background work runs on the Postgres job queue

Relates to: ADR-0002
Status: Accepted

## Context
We need retries and scheduled work (reminder emails, image resizing) without adding a broker.

## Decision
Background work is a row in the `jobs` table, picked up by the worker pool with
`SELECT ... FOR UPDATE SKIP LOCKED`. Jobs can be scheduled for a future time with
`run_after`. No external message broker or cloud queue.

## Consequences
Jobs are transactional with the data they touch. Throughput is bounded by the database;
fine at our scale (peak a few hundred jobs a minute).

## Alternatives considered
A hosted message broker; rejected (see ADR-0008, withdrawn).

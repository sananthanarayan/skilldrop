# ADR-0004: Redis locks for the nightly invoice run

- Status: Accepted
- Date: 2023-05-02
- Deciders: Tomasz Lind

## Context

We run three worker replicas. On 2023-04-27 two replicas both started the nightly invoice
run and 41 customers were billed twice.

## Decision

The nightly run takes a Redis `SET NX PX` lock (key `ledgerline:invoice-run`, 15 minute TTL,
renewed every 60 s) before it starts. Implemented in `src/ledgerline/scheduler/redis_lock.py`.

## Consequences

Adds Redis to the stack. This is an exception to ADR-0002, accepted for speed.

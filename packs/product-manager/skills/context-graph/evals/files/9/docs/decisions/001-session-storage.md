# 001. Store user sessions in Redis

Date: 2023-05-09

## Status

Superseded by [003](003-jwt-sessions.md)

## Context

We run three app containers behind the load balancer. In-memory sessions log users out
whenever a request lands on a different container.

## Decision

Sessions are stored in Redis via `connect-redis`, configured in `src/session/store.ts`,
with a 7-day TTL.

## Consequences

Redis becomes a hard dependency of login.

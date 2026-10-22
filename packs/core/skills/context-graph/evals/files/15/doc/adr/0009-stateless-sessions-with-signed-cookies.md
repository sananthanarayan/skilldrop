# 9. Stateless sessions with signed cookies

Date: 2024-05-07

## Status

Accepted

Supersedes [4. Use Redis for session storage](0004-use-redis-for-session-storage.md)

## Context

Redis was the only stateful dependency of `services/api/` and caused two
outages in Q1 2024 when its primary failed over.

## Decision

Sessions are stateless: a signed, encrypted cookie carries the dispatcher's
user ID, role and an 8-hour expiry. Redis is removed from `services/api/`.

## Consequences

No session store to operate. Revoking a single session before expiry needs a
short deny-list, kept in `haulmark_core`.

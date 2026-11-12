# 3. Use Redis for session storage

Date: 2024-05-14

## Status

Accepted

## Context

Login sessions are held in process memory on each API node, so the load balancer has to pin a
user to one node. When we scale out or restart a node, everyone pinned to it is logged out.

## Decision

Store sessions in Redis, keyed by a random session id held in an HttpOnly cookie. The code lives in
`services/auth/redis_sessions.py`. Sessions expire after 30 minutes of inactivity.

We chose Redis because "we already run it for the page cache, and a shared store removes sticky
sessions without adding a new system".

## Consequences

Any API node can serve any user. Login now depends on Redis being up.

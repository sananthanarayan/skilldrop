---
status: accepted
date: 2025-11-04
deciders: platform team, security
---

# Stateless signed session cookies

## Context and Problem Statement

On 2025-08-19 a Redis failover took 40 minutes. Every user was logged out and nobody could log
back in until it recovered. Login should not depend on a shared store.

## Considered Options

* Keep Redis and add a replica
* Sessions in Postgres (already rejected in ADR-0006)
* Signed, stateless session cookies

## Decision Outcome

Chosen option: "Signed, stateless session cookies", because "login should depend on nothing but
the auth service and its signing key; a replica makes the outage rarer but keeps the dependency".

Supersedes [ADR-0003](0003-use-redis-for-session-storage.md). The 8-hour lifetime from ADR-0005
carries over as the cookie expiry.

The new code is `services/auth/cookie_sessions.py`. `services/auth/redis_sessions.py` is removed
once every client is on cookie sessions.

### Consequences

* Good, because an outage of Redis no longer logs anyone out.
* Bad, because revoking a single session now needs a deny-list of session ids.
* Redis stays in use for the page cache.

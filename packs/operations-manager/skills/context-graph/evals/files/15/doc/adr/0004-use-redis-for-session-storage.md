# 4. Use Redis for session storage

Date: 2021-07-19

## Status

Accepted

## Context

The dispatcher web app needs server-side sessions shared across the API
instances in `services/api/`.

## Decision

Sessions are stored in Redis with a 12-hour TTL, keyed by an opaque session
ID held in a cookie.

## Consequences

One more piece of infrastructure to run. Logging out everywhere is a single
key delete.

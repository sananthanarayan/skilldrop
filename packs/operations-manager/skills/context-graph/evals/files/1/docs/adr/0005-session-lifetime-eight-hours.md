# 5. Session lifetime of eight hours

Date: 2024-09-23

## Status

Accepted

Amends [ADR-0003](0003-use-redis-for-session-storage.md).

## Context

Support staff using the back office were logged out every 30 minutes during long calls.

## Decision

Sessions expire 8 hours after login instead of after 30 minutes of inactivity. Everything else in
ADR-0003 stands.

## Consequences

A stolen session id is usable for longer. We accept that for now.

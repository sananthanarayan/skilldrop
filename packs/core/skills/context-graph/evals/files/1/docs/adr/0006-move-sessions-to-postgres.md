---
status: rejected
date: 2025-03-18
---

# Move sessions into Postgres

## Context and Problem Statement

Proposed by the API team to drop Redis from the login path by keeping sessions in a Postgres table.

## Decision Outcome

Rejected. Session reads happen on every request, and "putting that read load on the primary
database is a worse risk than the one we are trying to remove". Sessions stay as described in
ADR-0003 for now.

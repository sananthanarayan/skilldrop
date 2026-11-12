# ADR-0003: Tickets live in one Postgres primary

- **Status:** Accepted
- **Date:** 2025-02-11
- **Deciders:** Platform team

## Context

Ticket state (issued, transferred, void, used) has to be consistent: two people must not both own, or both use, the same ticket. Our peak write load is well within one Postgres primary.

## Decision

All ticket state lives in a single Postgres primary in eu-west, with a synchronous standby in a second zone. The Ticketing service and the Admissions API are the only writers. "Used" is set with a conditional update so two concurrent admits of the same ticket cannot both succeed.

## Consequences

- One source of truth for whether a ticket has been used.
- Anything that admits fans must go through the Admissions API to stay consistent.
- A region outage stops admissions; accepted at the time because handhelds were always online.

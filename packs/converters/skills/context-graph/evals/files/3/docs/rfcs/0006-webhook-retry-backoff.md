---
id: RFC-0006
title: Exponential backoff for webhook retries
status: accepted
date: 2025-04-22
supersedes: RFC-0003
authors: payments team
---

## Context and Problem Statement

During the 2025-03-06 incident a large merchant's endpoint was down for an hour. Fixed 30-second
retries from every queued event "hammered their endpoint as it came back and knocked it over
again".

## Decision Outcome

`services/payments/webhooks/retry.py` retries with exponential backoff: the first retry after 2
seconds, doubling each time, capped at 10 minutes between attempts, and at most 8 attempts in all.
A 4xx response is not retried, except 429. After the last attempt the event is marked failed and
the merchant can replay it from the dashboard.

### Consequences

* Good, because a recovering endpoint gets a trickle, not a flood.
* Bad, because an event can now be given up on within about four minutes.

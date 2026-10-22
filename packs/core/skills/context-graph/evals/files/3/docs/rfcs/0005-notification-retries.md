# RFC-0005: Retrying customer notifications

Date: 2025-01-27

## Status

Accepted

## Decision

Email and SMS sends that fail are retried by `services/notifications/retry.py` every 5 minutes for
up to 24 hours, then dropped and logged.

## Consequences

A customer may get a receipt email up to a day late.

# ADR-0012: Checkout latency budget

## Status
Accepted

## Context
Conversion dropped measurably when checkout pages got slower during last year's sale.

## Decision
Checkout API calls must complete within 300 ms at the 95th percentile, measured at the
load balancer, including during sale peaks.

## Consequences and risks
Any change that adds load to the catalogue database primary must show it does not push
checkout past this budget. Owner: checkout team.

## Alternatives considered
No formal budget; rejected after the sale incident.

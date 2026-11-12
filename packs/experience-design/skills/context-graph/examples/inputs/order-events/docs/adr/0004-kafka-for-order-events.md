# ADR-0004: Kafka for order events

## Status

Accepted

Date: 2025-03-02

## Context

Order events feed billing, notifications and the warehouse. We need replay for new consumers.

## Decision

Order events are published to Kafka from `services/orders/`, one topic per event type.

## Consequences

Replay works for a new consumer. We run a Kafka cluster.

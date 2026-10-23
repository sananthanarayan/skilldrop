# 3. Publish domain events over RabbitMQ

Date: 2024-02-14

## Status

Accepted

## Context

Downstream services (notifications, reporting) need to react when entries are posted.

## Decision

The ledger publishes `EntryPosted` and `AccountFrozen` events to a RabbitMQ topic exchange
named `ledger.events`. Publishing code lives in `services/ledger/events/`. Broker settings
are in `config/messaging.yaml`.

## Consequences

- Consumers bind their own queues; the ledger does not know who listens.
- Events are at-least-once; consumers must be idempotent.

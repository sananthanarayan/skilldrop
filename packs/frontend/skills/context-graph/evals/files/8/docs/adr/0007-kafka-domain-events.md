---
id: ADR-0007
title: Move domain events to Kafka
status: accepted
date: 2025-03-11
supersedes: ADR-0003
---

# Move domain events to Kafka

## Context and Problem Statement

Reporting now needs to replay the full history of posted entries, which RabbitMQ queues
cannot give us once a message is acknowledged.

## Decision Outcome

Domain events are published to the Kafka topic `ledger.entry-events`, keyed by account id,
with 30-day retention. This supersedes ADR-0003. Publishing stays in
`services/ledger/events/`; broker settings stay in `config/messaging.yaml`.

### Consequences

* Good, because consumers can replay from any offset within retention.
* Bad, because the team now operates a Kafka cluster.

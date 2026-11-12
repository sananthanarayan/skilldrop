# DD-002: Kafka is the event bus

Status: Accepted
Date: 2022-06-02
Deciders: O. Mensah, T. Lindqvist
Governs: pipelines/ingest/, pipelines/fanout/

## Context
Ingest events must reach several independent consumers (fan-out, billing export, the audit sink),
and a consumer that is down for a deploy must be able to catch up afterwards.

## Options considered
1. Postgres LISTEN/NOTIFY — rejected: notifications are lost if no listener is connected at the
   moment they fire, there is no replay, and payloads are capped at 8000 bytes.
2. RabbitMQ — rejected: no long replay window without extra plugins.
3. Kafka — chosen.

## Decision
Use Kafka. Every topic keeps 7 days of retention so any consumer can replay a week of events.
Retention policy details: see DD-007.

# ADR-0007: Kafka for domain event streaming

Status: Accepted
Date: 2025-01-27
Deciders: Joaquin Ferreira, Mara Lindqvist
Supersedes: ADR-0003
Governs: services/notifications/consumer.py

We need replay and per-key ordering, which our RabbitMQ setup does not give us. Domain
events move to Kafka topics `user-events` and `invoice-events`. Notifications consumes
both as consumer group `notifications`. See RFC-015 for the migration plan and cutover
dates.

# ADR-0003: RabbitMQ for asynchronous messaging

Status: Accepted
Date: 2024-04-02
Deciders: Mara Lindqvist, Joaquin Ferreira
Governs: services/notifications/consumer.py

Services publish domain events to a RabbitMQ topic exchange (`domain-events`).
Notifications consumes from its own durable queue bound to `user.*` and `invoice.*`.

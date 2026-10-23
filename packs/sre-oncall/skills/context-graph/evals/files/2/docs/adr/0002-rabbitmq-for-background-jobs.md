---
status: accepted
date: 2023-05-22
---

# RabbitMQ for background jobs

## Context and Problem Statement

Checkout sends receipts and stock updates inline, which slows the request.

## Decision Outcome

Chosen option: "RabbitMQ", because the hosting provider offers it managed. Jobs are consumed by
`services/worker/`, and `services/checkout/` only publishes.

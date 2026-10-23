---
id: RFC-0004
title: Idempotency keys on every webhook
status: accepted
date: 2024-11-19
---

## Decision

Every webhook sent from `services/payments/webhooks/` carries an `Idempotency-Key` header. The key
is generated once per event and "every retry of that event resends the same key, so a merchant who
receives it twice can drop the duplicate".

## Consequences

Merchants are told in the integration guide to deduplicate on the key.

# ADR-0004: Idempotency keys for payment creation

Status: Accepted
Date: 2025-03-03
Deciders: Priya Natarajan, Tomás Okafor
Governs: services/payments/api/create.py, services/payments/idempotency.py

## Context

Merchant integrations retry `POST /payments` on timeouts. In February we had two
incidents where a retried request created a second charge.

## Decision

1. `POST /payments` MUST carry an `Idempotency-Key` header. A request without
   one is rejected with `400`.
2. Keys are scoped per merchant: the stored record is keyed on
   `(merchant_id, Idempotency-Key)`.
3. The first response for a key is stored and replayed verbatim for 24 hours.
4. A request that reuses a key with a *different* request body is rejected with
   `422`. A client bug that reuses keys must never be handed the result of a
   different payment.
5. Records are stored in Redis, per ADR-0003.

## Consequences

Clients must generate a key per logical payment. Rule 4 means we fingerprint
the request body and compare it on every replay.

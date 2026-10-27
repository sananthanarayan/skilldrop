---
rfc: 0004
title: HMAC-SHA256 signatures on outbound webhooks
status: accepted
date: 2024-04-15
authors: [dev.raman]
governs:
  - src/webhooks/sign.ts
---

# RFC-0004: HMAC-SHA256 signatures on outbound webhooks

## Problem

Merchants cannot tell a genuine `charge.succeeded` webhook from a forged one.

## Decision

Every outbound webhook carries a `Ledgerline-Signature` header: an
HMAC-SHA256 of `timestamp + "." + body`, keyed with the merchant's webhook
secret. Signing is implemented in one place, `src/webhooks/sign.ts`, and every
sender must call `signPayload()` from it.

## Consequences

- Merchants verify with a constant-time compare.
- Rotating a merchant secret invalidates in-flight retries.

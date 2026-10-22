# ADR-0004: Service-to-service authentication with HMAC shared keys

- Status: Accepted
- Date: 2023-03-14
- Governs: `services/billing-api/auth/`, `services/ledger-worker/auth/`

## Context

billing-api and ledger-worker call each other over the internal network. We need callers to
prove who they are without standing up new infrastructure.

## Decision

Every internal request carries an `X-Tallow-Signature` header: HMAC-SHA256 over the method,
path, timestamp and body, keyed with a shared secret per service pair. Requests older than
300 seconds are rejected.

## Consequences

- Shared keys must be distributed to both sides and rotated by hand.
- A leaked key lets an attacker impersonate either side of the pair.

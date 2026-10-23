# ADR-0011: Service-to-service authentication with mutual TLS

- Status: Accepted
- Date: 2025-06-20
- Supersedes: ADR-0004
- Governs: `services/billing-api/auth/`, `services/ledger-worker/auth/`

## Context

ADR-0004's shared HMAC keys are rotated by hand and a single leak compromises both sides of a
pair. The 2025 PCI pre-assessment flagged this.

## Decision

Internal calls between billing-api and ledger-worker use mutual TLS. Each service gets a
short-lived client certificate from the internal Ironbark CA; the receiving side checks the
certificate's SPIFFE ID against an allow-list. HMAC signatures are removed once both services
are migrated. Certificate rotation follows ADR-0013.

## Consequences

- No shared secrets between services.
- Each service needs the Ironbark CA bundle mounted.

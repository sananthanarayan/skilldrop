# ADR-0005: Sign payloads with HMAC-SHA256

- Status: Accepted
- Date: 2022-07-11
- Governs: `src/delivery/signing.py`

## Decision
Each webhook body is signed with HMAC-SHA256 using the partner's shared secret. The hex digest
is sent in the `X-Parcelhook-Signature` header, together with `X-Parcelhook-Timestamp`, and the
timestamp is part of the signed string (`{timestamp}.{body}`) to prevent replay.

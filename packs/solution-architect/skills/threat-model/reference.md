# threat-model reference — STRIDE question banks + mitigation table

Questions are prompts for the analysis, not a checklist to transcribe. A question only becomes a finding when it can be narrated as actor → path → result against a named boundary in the system under review.

## STRIDE by boundary type

### Internet → edge (public API, web app, webhook receiver)

- **S** — Can a caller forge identity? Token audience/issuer validated? Webhook signatures checked, or just a "secret" URL? API keys distinguishable from user auth?
- **T** — Are request bodies/headers trusted downstream (forwarded `X-User-Id`)? Can query params alter server-side behavior beyond their contract (mass assignment, prototype pollution)?
- **R** — Are authentication failures and privileged calls logged with caller identity? Could a caller plausibly deny an action?
- **I** — Do error responses leak stack traces, internal hostnames, versions? Do list endpoints leak other users' resource IDs? Timing differences on auth (user enumeration)?
- **D** — Unauthenticated endpoints with expensive work (search, export, PDF render)? Rate limits per-IP only (trivially rotated) or per-principal? Payload size caps?
- **E** — Do any endpoints trust client-supplied role/scope claims? Hidden admin routes guarded by obscurity?

### Service → service (internal APIs, queues, RPC)

- **S** — Does service B verify *which* service is calling, or accept anything inside the network ("flat trust")? mTLS / workload identity, or shared static secrets?
- **T** — Are queue messages signed or schema-validated, or does the consumer trust whatever's enqueued? Can a compromised producer poison downstream state?
- **R** — Can an action be traced through the chain (correlation IDs), or does attribution die at the first hop?
- **I** — Do internal payloads carry more data than the consumer needs (full user record where an ID would do)?
- **D** — Can one service exhaust another (no backpressure, unbounded fan-out, retry storms)?
- **E** — Does a low-privilege service hold credentials that grant more than it uses (over-scoped IAM)?

### App → datastore (DB, object storage, cache)

- **S** — Shared DB credentials across services, or per-service identity?
- **T** — String-built queries anywhere? Can the app write rows/objects outside its tenant scope (key-prefix discipline)?
- **I** — Tenant isolation by `WHERE` clause convention only? Backups/replicas/cache covered by the same access controls as primaries? Presigned URLs scoped and short-lived?
- **D** — Unbounded queries reachable from user input (no LIMIT, full scans)? Cache stampede paths?
- **E** — Does the app account hold DDL/admin rights it never uses?

### Human → system (admin panels, support tooling, CI/CD)

- **S** — Admin auth at the same strength as user auth, or stronger (MFA, hardware keys)? Sessions revocable?
- **T** — Can CI run arbitrary code with deploy credentials on a PR from a fork? Are build artifacts verifiable (signed, pinned digests)?
- **R** — Are support/admin actions on user data logged immutably with operator identity?
- **I** — Can support staff browse data beyond the case at hand (no purpose-binding)?
- **E** — Path from "support role" to "admin role"? Long-lived personal tokens with org-wide scope?

### Tenant → tenant (multi-tenant SaaS) — run with the authz pass

- IDs guessable/enumerable across tenants (sequential integers, predictable UUIDs in URLs)?
- Every query path tenant-scoped by construction (middleware/RLS), or by developer discipline?
- Shared compute side-channels: can one tenant's load degrade another's (noisy neighbor as DoS)?
- Export/report/search features — the classic cross-tenant leak surfaces.

## Insider / compromised-credential pass

Assume one legitimate credential is attacker-held: a user account, a support login, a CI token, one service's IAM role. For each, what's the blast radius before detection? Findings here are usually 🟧 — they need position, but position is bought cheaply (phishing, leaked token).

## Common mitigations (with the verification that makes them real)

| Threat shape | Mitigation | Verified by |
|---|---|---|
| Forged inbound identity | Token validation incl. audience+issuer+expiry; webhook HMAC | Negative test: tampered/expired token rejected in CI |
| Cross-tenant access | Tenant scoping by construction (RLS, scoped prefixes), not per-query discipline | Cross-tenant fetch test as a permanent CI case |
| Trusted internal headers | Strip/rewrite identity headers at the edge; sign internal assertions | Request with spoofed header from outside → rejected |
| Queue poisoning | Schema validation on consume; producer allow-list | Malformed message → DLQ with alert, not crash-loop |
| Resource exhaustion | Per-principal rate limits, payload caps, timeouts, bounded queries | Load test on the most expensive unauthenticated path |
| Over-scoped credentials | Per-service identity, least-privilege IAM, short-lived tokens | Periodic automated diff of granted vs used permissions |
| Silent admin abuse | Immutable audit log, purpose-bound support access | Audit-log entry asserted in admin-action integration tests |

## Severity calibration

- 🟥 **critical** — unauthenticated attacker, or any cross-tenant data compromise, against a top-ranked asset. Halt-the-build territory.
- 🟧 **high** — authenticated user bypasses authz; single-tenant data exposure; insider blast radius covering a top asset.
- 🟨 **medium** — requires chaining 2+ weaknesses or unusual position; degraded availability short of outage.
- ⚪ **low / accepted** — real but marginal; document the acceptance so it's a decision, not an oversight.

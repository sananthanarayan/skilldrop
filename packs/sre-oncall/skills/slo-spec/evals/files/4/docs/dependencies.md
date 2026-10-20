# payments-api dependencies

| Dependency | Used by | Commitment | Behaviour when it fails |
|---|---|---|---|
| Halberd Payments Gateway (acquirer) | POST /v1/charges (synchronous, every request) | Contractual SLA 99.95% monthly uptime; we measured 99.97% over the last 90 days | Request fails with 502/504. No secondary acquirer today — Corvid Acquiring integration is on the Q2 2027 roadmap. |
| Ledger DB (managed Postgres, multi-AZ) | POST and GET | Provider SLA 99.95% monthly | Request fails with 503. |
| Fraud scoring (internal, team Sentinel) | POST /v1/charges | Internal SLO 99.9% availability, p99 180 ms | Called with a 250 ms timeout. On timeout or error we fall back to rules-based scoring and proceed (fail-open); logged as `fraud_fallback=true`. |
| Idempotency cache (self-hosted Redis, single primary + replica) | POST /v1/charges | No SLO | Fail-closed: request returns 503. |

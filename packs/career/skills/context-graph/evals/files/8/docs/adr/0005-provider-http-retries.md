# ADR 0005: Retry and timeout policy for payment-provider calls

* Status: Accepted
* Date: 2024-04-18

## Context

The payment provider occasionally returns 502/503 during their deploys. Unbounded retries
during an outage amplified load on them last year and held our worker threads.

## Decision

Calls from `services/ledger/clients/provider.py` to the provider:

| Setting            | Value                                   |
|--------------------|-----------------------------------------|
| Request timeout    | 5 seconds                               |
| Max retries        | 3                                       |
| Backoff            | exponential, 200 ms base, full jitter   |
| Retry on           | GET and idempotent POST (with key) only |

Values are read from `config/http.yaml`; the code must not hard-code them.

## Consequences

Worst-case latency of a provider call is bounded at roughly 21 seconds.

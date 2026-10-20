# payments-api — 90-day summary (2026-07-22 to 2026-10-19)

Two metric sources exist:

- **App:** `http_server_requests_total{service="payments-api", route, status}` and
  `http_server_request_duration_seconds_bucket{service="payments-api", route, le}` — emitted by the pods.
- **Ingress LB:** `lb_requests_total{backend="payments-api", route, code}` and
  `lb_request_duration_seconds_bucket{backend="payments-api", route, le}` — emitted by the ingress load balancer.

The LB sees ~0.02% more 5xx on POST /v1/charges than the app does: 502s returned by the LB while pods
restart during deploys (about 4 deploys/week) never reach the app, so the app metric doesn't count them.

## Traffic

| Route | Avg req/s | Daily peak req/s | Notes |
|---|---|---|---|
| POST /v1/charges | 36 | 95 (12:00–13:00 UTC); 210 during merchant batch runs | |
| GET /v1/charges/{id} | 22 | 60 | |
| GET /healthz | 30 | 30 | LB probes + kubelet; always 200 |

## POST /v1/charges — status breakdown (LB-measured, 90d)

| Status | Share |
|---|---|
| 201 created | 98.52% |
| 402 card_declined | 0.71% baseline; 1.5–4% during card-testing attacks on a single merchant (26 such spikes, 10–40 min each) |
| 400 / 422 validation | 0.55% |
| 409 idempotency conflict | 0.08% |
| 429 rate limited | 0.08% |
| 5xx | 0.06% (502: 0.02%, 503: 0.01%, 504: 0.03%) |

App-measured 5xx on the same route: 0.04%.

Monthly non-5xx share, LB-measured: Aug 99.95%, Sep 99.91%, Oct (1–19) 99.96%.

## POST /v1/charges — latency (LB-measured, 90d)

p50 310 ms · p90 640 ms · p95 820 ms · p99 1,850 ms · p99.9 4,200 ms

Share of requests completing under: 1,000 ms → 96.4% · 2,000 ms → 99.12% · 3,000 ms → 99.71%

## GET /v1/charges/{id} (LB-measured, 90d)

5xx 0.02% · p99 120 ms · share under 250 ms → 99.93%

## Pages from PaymentsApiHighErrorRate (90d)

31 pages total:
- 26 — card-testing decline spikes (402s), no service fault
- 3 — 502 bursts during deploys (resolved on their own within 6 min)
- 2 — Halberd gateway incidents (Sep 9: 504s on ~9% of POST /v1/charges for 22 min; Oct 2: 7 min)

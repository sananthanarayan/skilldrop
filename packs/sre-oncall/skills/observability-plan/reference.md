# observability-plan reference — signals, SLO math, burn-rate alerts, pillar split

## The golden signals (cover all four; they're cause/saturation signals, not SLOs by default)

| Signal | Question | Typical measure |
|---|---|---|
| **Latency** | how slow? (split success vs error latency) | p50/p95/p99 against a threshold |
| **Traffic** | how much demand? | rps, requests/min, active connections |
| **Errors** | how often failing? | error rate, by class (5xx vs 4xx) |
| **Saturation** | how full? | CPU/mem/queue depth/connection-pool % — the leading indicator of trouble |

User-facing **latency + errors** usually become SLIs; **saturation** is the early-warning/cause signal that informs diagnosis, not the page.

## SLI types (good events / valid events, from the user's side)

| SLI | Definition | Measured where |
|---|---|---|
| Availability | successful responses / valid requests | LB / gateway / client |
| Latency | requests faster than threshold / valid requests | same vantage as the user |
| Freshness | data served within max staleness / reads | for caches, pipelines, replicas |
| Correctness | correct outputs / total (where checkable) | post-processing validation |
| Throughput | jobs completed within deadline / scheduled | batch/streaming |

Measure as close to the user as practical. An SLI measured server-side misses the failures that never reached the server.

## SLO targets, windows, error budgets

- Target over a **rolling window** (28 or 30 days is common). 99.9%/28d ≈ **40 min** of budget; 99.95% ≈ 20 min; 99.99% ≈ 4 min.
- The **error budget** = (1 − SLO) × window. It is the allowed unreliability — spend it on releases and risk.
- **Error-budget policy** (write it): e.g. "budget >50% remaining → ship freely; <25% → freeze risky changes, prioritize reliability; exhausted → release freeze until recovered." Without a policy, the SLO doesn't change any behavior.
- Calibrate targets to cost (see `nfr-spec` down-for-an-hour). Internal tools rarely need >99.5%; payment paths may justify 99.95%+. Each nine is ~10× the effort.

## Multi-window, multi-burn-rate alerting (page on fast burn, ticket on slow)

"Burn rate" = how fast you're consuming the error budget relative to even consumption (1× burn would exactly exhaust it at window end). Alert on high burn over a short window AND confirm over a longer one to avoid flapping.

| Burn rate | Budget consumed | Long/short windows | Severity |
|---|---|---|---|
| 14.4× | 2% in 1h | 1h and 5m both breaching | 🔴 page — fast burn, acute |
| 6× | 5% in 6h | 6h and 30m | 🟠 page — sustained |
| 3× | 10% in 1d | 1d and 2h | 🟡 ticket — slow burn |
| 1× | tracking only | — | dashboard, no alert |

Require both the long and short window to breach before firing — the short window confirms it's still happening, the long window confirms it's significant. This is what replaces brittle "errors > N" static thresholds.

## Alert-quality rules

1. **Every page is actionable now** — there is a thing a human does on receipt. If not, it's a ticket.
2. **Every page maps to a runbook entry** (→ `runbook-generator`). No runbook = not ready to page.
3. **Page on symptoms** (SLO burn, user-facing errors), not causes (a pod restarted). Causes are diagnostic context.
4. **Deduplicate and group** — one incident, one page, not 200 per-host alerts.
5. **Tier severity:** page (wake someone) / ticket (next business day) / log (queryable, no notification). Most "alerts" should be tickets or logs.
6. **Review noisy/non-actionable pages** monthly; a page that's been ignored 5× is either re-tiered or fixed. Alert fatigue is a reliability risk in itself.

## Metrics vs logs vs traces (use each for its strength)

| | Metrics | Logs | Traces |
|---|---|---|---|
| Good at | aggregate state, alerting, SLOs | per-event detail, debugging one request | request flow across services |
| Cost driver | **cardinality** (label combinations) | **volume** (GB ingested) | sampling rate × span count |
| Cardinality | keep LOW — bounded labels only | high-cardinality lives here | high-cardinality lives here |
| Retention | long (cheap, downsampled) | short, sampled on hot path | short, tail-sampled on errors/slow |
| Don't | put user_id/request_id as a label | use as a metric (count via logs = $$$) | sample blindly and miss the error traces |

**Cardinality budget:** allowed metric labels are bounded sets — `region`, `status_class`, `endpoint_template`, `tenant_tier`. Forbidden as metric labels — `user_id`, `request_id`, raw `url`, `email`. Those identifiers belong in logs/traces, linked from metrics via **exemplars**. One unbounded label can create millions of series and a five-figure monthly bill.

**Structured logs:** key-value/JSON, consistent field names, a trace/correlation ID on every line so logs join to traces. Sample the hot path (keep all errors, sample successes). Set a retention budget (ties to `capacity-cost-model`).

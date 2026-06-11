# Observability-plan template

SLIs from the user's side, SLOs with budgets and a policy, pages that are actionable and runbook-linked, pillars split by purpose with a cost ceiling.

```markdown
# Observability plan: {service}

**Date:** {YYYY-MM-DD} · **On-call team:** {role}

## Critical user journeys (SLIs measure these)

| Journey | "Down" means to a user | SLI |
|---|---|---|
| {log in} | {can't authenticate} | success rate of auth requests |
| {place order} | {checkout errors / hangs} | % checkout req 2xx within 1s |

## SLIs / SLOs / error budgets

| SLI | Definition (good/valid) | SLO (target / window) | Error budget | Measured at |
|---|---|---|---|---|
| checkout availability | 2xx / valid checkout req | 99.9% / 28d | ~40 min/28d | load balancer |
| checkout latency | < 1s / valid checkout req | 99% < 1s / 28d | — | load balancer |

**Error-budget policy:** {>50% remaining → ship freely; <25% → freeze risky releases; exhausted → release freeze + reliability focus until recovered}.

## Alerts (symptom-based, burn-rate, every page runbook-linked)

| Alert | Condition | Windows | Burn | Page / Ticket | Runbook |
|---|---|---|---|---|---|
| checkout fast burn | budget burn ≥ 14.4× | 1h & 5m | acute | 🔴 page | runbook#checkout-errors |
| checkout slow burn | budget burn ≥ 3× | 1d & 2h | slow | 🟡 ticket | runbook#checkout-degraded |
| saturation early-warn | pool util > 85% | 15m | — | 🟡 ticket | runbook#scale-checkout |

{No page without a runbook link. Cause/resource signals are tickets or dashboards, not pages.}

## Three-pillar strategy

| Pillar | Used for | Key rules |
|---|---|---|
| Metrics | SLOs, alerts, golden signals | bounded labels only (region, status_class, endpoint_template) |
| Logs | per-request debugging | structured JSON, trace-id on every line, sample successes, keep errors, retention {N}d |
| Traces | cross-service latency/error attribution | propagate context all hops, tail-sample errors/slow, {x}% baseline |

## Cardinality & cost budget

- **Allowed metric labels:** {region, status_class, endpoint_template, tenant_tier}
- **Forbidden as metric labels (→ logs/traces):** user_id, request_id, raw url, email
- **Budgets:** metric series ≤ {N}; log ingest ≤ {GB/day}; trace sampling {x}%. Alert at 80% of each. (→ `capacity-cost-model`)

## Dashboards (by the question each answers)

| Dashboard | Question it answers | Panels |
|---|---|---|
| Service health | "is checkout healthy right now?" | golden signals + SLO/budget status |
| Checkout drill-down | "where is the latency/error coming from?" | per-dependency latency, error breakdown, trace exemplars |

## Instrumentation conventions

- Metric naming: {namespace.subsystem.unit} (e.g. `checkout.request.duration_ms`)
- Trace context propagated on every hop ({W3C traceparent}); exemplars link metrics → traces.
- Every new feature ships its SLI instrumentation with it (not as a fast-follow).
```

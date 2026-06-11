---
name: observability-plan
description: Design an observability plan for a service — user-journey SLIs, SLOs with error budgets, symptom-based burn-rate alerting (page vs ticket, every page actionable and runbook-linked), and a deliberate metrics/logs/traces split with a cardinality and cost budget. Use when the user needs SLOs, alerting design, a monitoring/observability strategy, dashboards, or wants to fix alert fatigue and know what to measure.
---

# observability-plan

Designs the telemetry that makes a service *debuggable at 3am and detectable before users complain* — SLOs measured from the user's experience, alerts that fire only when a human must act, and the three pillars each used for what they're good at. Expands the one-line observability requirement from `nfr-spec` into a full operating plan; upstream of `incident-comms` and `postmortem-generator` (you can't communicate or analyze an incident you couldn't detect). Distinct from `success-metrics` (business outcomes) — this is operational health.

## How to respond

1. **Start from user journeys, not from the resource dashboard.** The first artifact is the list of critical journeys ("log in", "place order", "load feed") — because an SLI measures *what the user experiences*, and CPU graphs measure what's easy. Ask at most 2 questions, spent on the most critical journey and what "down" means to a user there. Resource metrics (the golden signals) still get covered — but as saturation/cause signals, never as the SLO.

2. **Define SLIs as good-events / valid-events from the user's side** (catalog in [`reference.md`](reference.md)) — availability (success rate), latency (a threshold, measured at a percentile: "% of requests < 300ms"), and where relevant freshness, correctness, throughput. ✅ *"SLI: proportion of checkout requests returning 2xx within 1s, measured at the load balancer"* — ❌ *"SLI: average CPU"* (the user never feels your CPU). Latency SLIs are a *threshold count*, not an average — averages hide the tail that hurts.

3. **Set SLOs with an explicit error budget and window.** Each SLI gets a target over a rolling window: "99.9% over 28 days." That target *is* the error budget (0.1% = ~40 min/28d) — the quantity that governs both alerting and how aggressively you ship. State the budget in human terms (minutes/month) and name the **error-budget policy**: what happens when it's spent (freeze risky releases, redirect to reliability) — an SLO with no policy is a number nobody defends. Pick targets honestly (99.9% is not free; see `nfr-spec`'s down-for-an-hour calibration) — more nines is exponentially more cost.

4. **Alert on symptoms, page only on what's actionable now.** The hard rule that kills alert fatigue: **a page means a human must act immediately; everything else is a ticket or a dashboard.** Alert on SLO burn (the user is being hurt), not on every cause (a single CPU spike that auto-recovered). Cause-based signals inform diagnosis once you're paged — they don't page. Use **multi-window, multi-burn-rate alerts** ([`reference.md`](reference.md)): a fast burn (budget being consumed quickly) pages; a slow burn opens a ticket. Every page is actionable, deduplicated, severity-tiered, and **maps to a runbook entry** (→ `runbook-generator`) — a page with no runbook is a 3am puzzle, not an alert.

5. **Split the three pillars deliberately — each for what it's good at:**
   - **Metrics** — cheap, aggregatable, the basis of SLOs and alerts. Low-cardinality. Answer "is it broken and how much?"
   - **Logs** — expensive, high-detail, for debugging the specific failure. **Structured** (not string soup), sampled on the hot path, with a retention/cost budget. Answer "what exactly happened to this request?"
   - **Traces** — request flow across services, for "where in the chain did the latency/error come from?" Sample intelligently (tail-based on errors/slow); propagate context across every hop.
   Don't put in logs what should be a metric (cardinality and cost explode), and don't try to metric what needs a trace (you'll never reconstruct the path from counters).

6. **Set a cardinality and cost budget.** High-cardinality labels (user_id, request_id, full URL) on metrics multiply time series and the bill without bound — name which labels are allowed on metrics (bounded sets: region, status_class, endpoint-template) and push the high-cardinality identifiers to logs/traces where they belong. State the log-volume and metric-series budget (ties to `capacity-cost-model`); observability is routinely a top-3 cloud line item.

7. **Specify dashboards by the question each answers**, not by graph count. A service dashboard shows the golden signals + SLO/budget status at a glance (the at-a-glance health check); a debugging dashboard supports drill-down. The 3am questions from `nfr-spec` become concrete panels. A wall of 100 graphs is where signal goes to hide.

8. **Emit with [`templates/observability-plan.md`](templates/observability-plan.md)** in one message: critical journeys, SLI/SLO table with error budgets, the error-budget policy, the alert table (condition / window / burn-rate / page-or-ticket / runbook link), the metrics-logs-traces split, the cardinality+cost budget, and dashboards-by-question. Instrumentation naming conventions and trace-context propagation noted.

## Useful references in this skill

- [`reference.md`](reference.md) — golden signals, SLI types by component, SLO/error-budget math, the multi-window burn-rate alert table, the metrics-vs-logs-vs-traces decision guide, and alert-quality rules
- [`templates/observability-plan.md`](templates/observability-plan.md) — the plan skeleton with SLO, alert, and pillar tables

## Quality bar

- **SLIs measure user experience** (good/valid events), not resource utilization. Latency SLIs are threshold counts at a percentile, never averages.
- **Every SLO has an error budget in human terms and a policy** for when it's spent. A target with no budget consequence is decoration.
- **Pages are actionable, symptom-based, and runbook-linked.** If a page doesn't require an immediate human action, it's a ticket — the plan re-tiers it.
- **Burn-rate alerting is used**, not static "CPU > 80%" thresholds, for SLO-backed surfaces.
- **The three pillars are split by purpose**, with high-cardinality identifiers kept off metrics. Logs are structured and budgeted.
- **A cardinality/cost budget exists.** Observability without a cost ceiling becomes the surprise invoice.
- **Dashboards are defined by the question they answer**, not by quantity.

## When to use this skill

- ✅ Standing up monitoring/SLOs for a new or existing service
- ✅ "What should we measure / alert on?" / designing an alerting strategy
- ✅ Fixing alert fatigue — too many pages, most non-actionable
- ✅ Turning `nfr-spec`'s observability requirement into an implementable plan

## When NOT to use this skill

- ❌ Business/product success metrics — that's `success-metrics`
- ❌ Customer/stakeholder comms during an outage — that's `incident-comms`
- ❌ The post-incident analysis — that's `postmortem-generator`
- ❌ The one-line observability *requirement* in a spec — that's `nfr-spec`; this is the full design beneath it

## Anti-patterns to avoid

- ❌ **Resource metrics as SLOs.** Alerting on CPU/memory/disk as if they were user pain — they auto-recover, they spike harmlessly, and they page you at 3am for nothing while the actual user-facing error goes unnoticed.
- ❌ **Averages for latency.** "Average response 120ms" with a p99 of 4s means a lot of users are suffering invisibly. Measure the percentile and the threshold.
- ❌ **Cause-based paging.** A page for every component hiccup. Page on the symptom (users hurt / budget burning fast); let causes inform diagnosis, not wake people.
- ❌ **The alert with no runbook.** Firing a page that says "high error rate" with no "here's what to check" — that's a puzzle handed to someone half-asleep.
- ❌ **Unbounded metric cardinality.** `user_id` or `request_id` as a metric label — millions of time series, a five-figure bill, and a dashboard that times out. Those belong in logs/traces.
- ❌ **String-soup logs.** Unstructured `printf` logs you can't query or aggregate, retained forever at full volume. Structure them, sample the hot path, budget the retention.
- ❌ **The 100-graph dashboard.** Built to look thorough, used by no one, because no panel answers a question anyone asks under pressure.
- ❌ **99.99% by reflex.** Copying a target off a blog instead of from the down-for-an-hour cost calibration; every nine multiplies the engineering and on-call burden.

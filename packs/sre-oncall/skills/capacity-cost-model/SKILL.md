---
name: capacity-cost-model
description: Build a capacity and cost model for a service or feature — sized from a demand driver and its growth curve, not from instance types; unit economics (cost per request/tenant/GB); peak-vs-average and headroom as explicit decisions; cost at 1×/3×/10× with scaling cliffs named; and the forgotten line items (egress, logging, NAT, non-prod) checklisted. Use when the user needs to estimate cloud/infra cost, size capacity for launch or growth, project the bill at scale, or find what's driving a cost.
---

# capacity-cost-model

Turns "how much will this cost to run?" into a model a reviewer can re-run and finance can trust — sized from **demand**, expressed in **cost per unit**, and honest about the line items everyone forgets until the invoice. Distinct from `business-case` (which decides *whether* to invest, across options) and `nfr-spec` (which *sets* the throughput/availability targets); this models the resources and dollars to *meet* a target you've already chosen.

## How to respond

1. **Start from the demand model, never from instance types.** The first question is "how much of what?" — the **driver** (requests/sec, tenants, GB stored, events/day, concurrent users), its **current value**, its **growth curve**, and the **peak-to-average ratio**. Ask at most 2 questions, spent on the driver's current volume + source and the peak ratio (the spikiness that decides static-vs-autoscale). Sizing to a round instance count instead of to demand is how clusters end up 80% idle or 200% over.

2. **Express everything as unit economics.** Cost per request / per tenant / per 1k events / per GB-month — because that's what scales predictably, what finance budgets in, and what reveals whether the architecture gets cheaper or more expensive per unit as it grows. ✅ *"$0.012 per active tenant per day, dominated by the per-tenant search index"* — ❌ *"about $4k/month"* (a number with no denominator can't be reasoned about at 10×).

3. **Model the components against the cost catalog** ([`reference.md`](reference.md)) — compute, storage, **network egress** (the forgotten heavyweight), managed-service tiers, **logging/observability** (routinely a top-3 surprise), backups/DR, data transfer cross-AZ/region, and **non-production environments** (dev/staging/idle often 30–50% of the bill). Each line: the quantity from the demand model × the unit price, with the price's source/date tagged. Missing the egress and observability lines is the single most common way a model lands 40% low.

4. **Make peak-vs-average and headroom explicit decisions, not defaults.** State both the average load (what you bill for) and the peak (what you must serve), and the chosen **target utilization + buffer** with its reasoning: ✅ *"size to peak × 1.3 for failover + spike; accept ~55% average utilization because the spike is revenue-critical"*. Over-provisioning burns money; under-provisioning is an incident — the headroom number is where that tradeoff is decided, so it's named, not buried in a rounded-up instance count.

5. **Project at 1× / 3× / 10× and find the scaling cliffs.** Cost rarely scales linearly — name where it jumps: the next instance/managed-service tier, cross-AZ egress kicking in, a license seat band, single-node → sharded, a free-tier ceiling. ✅ *"linear to ~5×, then the search tier forces a sharded cluster (+$3k/mo step) at ~6×"*. A model that's a single multiplication hides the cliff that wrecks the budget.

6. **Rank the cost drivers and use ranges.** The 2–3 line items that dominate get named (optimization targets them, not the rounding error). Outputs are **ranges with a stated lean** (low/expected/high), never false precision — three estimated inputs don't produce "$4,271/mo". Tag input confidence like `business-case` does.

7. **Set the cost guardrails.** Budget alert thresholds, and the **unit-cost regression check**: cost-per-unit should hold flat or fall as volume grows; if the model shows it *rising* with scale, that's a flagged architectural problem, not a footnote. (Mirrors `success-metrics`' guardrail discipline; the alerting itself is an `nfr-spec` cost target.)

8. **Emit with [`templates/cost-model.md`](templates/cost-model.md)** in one message: demand model, component table with unit prices, unit economics, total at average + peak, growth scenarios with cliffs, cost-driver ranking, the forgotten-costs checklist (each ticked present or n/a), and guardrails. State the assumptions that most move the total at the top.

## Useful references in this skill

- [`reference.md`](reference.md) — the cost-component catalog, the forgotten-costs checklist, headroom guidance, and common scaling cliffs
- [`templates/cost-model.md`](templates/cost-model.md) — the model skeleton with demand, component, and growth-scenario tables

## Quality bar

- **Sized from a demand driver with a growth curve**, not a chosen instance count. The driver and its source are stated.
- **Every cost is a unit cost × a quantity**, with the unit price's source and date tagged. A bare monthly total fails.
- **Egress, observability, and non-prod lines are present** (or explicitly n/a). Their absence is the signature of a model that's 40% low.
- **Headroom and peak-vs-average are explicit decisions** with reasoning, not absorbed into a rounded number.
- **Scaling cliffs are named in the 1×/3×/10× projection.** A linear extrapolation that hides a tier jump is a budget trap.
- **Outputs are ranges with a lean; the unit-cost-at-scale trend is checked.** Rising per-unit cost with growth is flagged as an architecture issue.

## When to use this skill

- ✅ Estimating run cost for a new service/feature before launch
- ✅ Sizing capacity for a launch or a known growth event
- ✅ "What will this cost at 10× / when we hit N tenants?"
- ✅ Finding what's driving an existing cloud bill and where the next cliff is

## When NOT to use this skill

- ❌ Deciding whether to build/buy/invest at all — that's `business-case` (this can feed its run-cost line)
- ❌ Setting the performance/availability targets — that's `nfr-spec` (this sizes to meet them)
- ❌ The migration/rollout sequence — that's `migration-plan`
- ❌ A fixed-price SaaS seat with no scaling math — just read the price sheet

## Anti-patterns to avoid

- ❌ **Sizing from instance types.** "Let's run 3 large nodes" before knowing the load — that's a guess wearing a SKU, idle or overwhelmed by luck.
- ❌ **The denominator-free total.** "$4k/month" with no per-unit cost can't be projected, compared, or optimized.
- ❌ **Forgetting egress and observability.** The two line items that turn a tidy estimate into a 40%-low one; the checklist exists because they're forgotten every time.
- ❌ **Ignoring non-prod.** Three idle staging environments and a never-scaled-down dev cluster are real money the model pretends doesn't exist.
- ❌ **Linear extrapolation past a cliff.** "10× the load, 10× the cost" right up until the sharded-cluster step doubles it. Name the cliff.
- ❌ **False precision.** "$4,271.40/mo" from estimated inputs reads as certainty the model doesn't have. Ranges with a lean.
- ❌ **Missing the rising-unit-cost flag.** A model where cost-per-tenant climbs with scale is describing an architecture that gets worse the more it succeeds — that's the headline, not a row.

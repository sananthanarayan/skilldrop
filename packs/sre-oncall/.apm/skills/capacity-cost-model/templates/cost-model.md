# Capacity & cost-model template

Demand first, unit costs always, ranges not points, cliffs named. Every unit price tagged with source + date.

```markdown
# Capacity & cost model: {service / feature}

**Date:** {YYYY-MM-DD} · **Cloud/region:** {provider, region}

## Assumptions that most move the total (top 3)

- {driver value, headroom choice, or unit price the answer is most sensitive to} `[data|estimate]`

## Demand model

| Driver | Current | Growth | Peak : average | Source |
|---|---|---|---|---|
| {requests/sec | tenants | GB | events/day} | {value} | {curve, e.g. 8%/mo} | {e.g. 4:1} | `[data: …]` |

## Components (quantity × unit price)

| Component | Quantity (from demand) | Unit price (source, date) | Monthly (expected) | Range |
|---|---|---|---|---|
| Compute | {peak/autoscale} | {$/…} `[src 2026-06]` | {$} | {low–high} |
| Storage | {GB, cumulative} | {$/GB-mo} | {$} | |
| Egress | {GB out} | {$/GB} | {$} | |
| Managed: {db/cache/search} | {tier/nodes} | {$/node} | {$} | |
| Observability | {GB ingest, series} | {$/GB} | {$} | |
| Backups/DR | {GB × retention × copies} | {$/GB-mo} | {$} | |
| Non-prod | {fraction of prod} | — | {$} | |
| Always-on (NAT/LB/floor) | {24/7 units} | {$/hr} | {$} | |
| **Total (average load)** | | | **{$ range}** | |
| **Total (peak provisioned)** | | | **{$ range}** | |

## Unit economics

- Cost per {request | tenant | 1k events | GB}: **{$ expected (range)}**
- Dominated by: {the line item driving it}

## Growth scenarios & cliffs

| Scale | Monthly cost (range) | Cost per unit | Cliff hit? |
|---|---|---|---|
| 1× (today) | {$} | {$/unit} | — |
| 3× | {$} | {$/unit} | {none / names it} |
| 10× | {$} | {$/unit} | **{e.g. search → sharded cluster, +$3k step at ~6×}** |

**Unit-cost trend:** {flat / declining / ⚠ rising — and why if rising}

## Cost-driver ranking (optimize these, not the rounding error)

1. {line item} — {% of total} — {lever to reduce}
2. …

## Forgotten-costs checklist

{egress · cross-AZ · observability · backups×retention×copies · non-prod · NAT/LB ·
idle floor · support/licenses · migration egress · free-tier expiry — each: ✅ included / n/a (reason)}

## Headroom decision

Target utilization {x%}; buffer = peak × {multiplier} for {failover + spike}; {autoscale | static} because {peak:avg ratio}. Tradeoff accepted: {money vs incident}.

## Guardrails

- Budget alert at {threshold}; hard stop / review at {threshold}.
- Unit-cost regression: alert if cost-per-{unit} rises > {x%} quarter-over-quarter.
```

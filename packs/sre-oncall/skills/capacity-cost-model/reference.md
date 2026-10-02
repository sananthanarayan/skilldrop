# capacity-cost-model reference — component catalog, forgotten costs, cliffs

All unit prices are illustrative placeholders — the skill tags each with its real source and date. Cloud pricing changes; never hard-code a number without a date.

## Cost-component catalog (model every applicable line)

| Component | Demand quantity | Typical unit price shape | Notes |
|---|---|---|---|
| **Compute** | peak concurrent work / rps | $/vCPU-hr, $/instance-hr, $/request (serverless) | size to peak or autoscale; state which |
| **Storage** | GB stored × growth | $/GB-month, tiered (hot/warm/cold) | growth is cumulative — model the curve, not a point |
| **Network egress** | GB out to internet / cross-region | $/GB, often tiered, free inbound | THE forgotten heavyweight; cross-AZ counts too |
| **Managed services** (DB, cache, queue, search) | IOPS, nodes, throughput units | per-node / per-RU / per-throughput-tier | tier jumps are the classic cliff |
| **Logging / observability** | GB ingested, metrics cardinality, traces | $/GB ingested, $/metric series | routinely top-3; high-cardinality labels explode it |
| **Backups / DR** | snapshot GB, replica count, cross-region copy | $/GB-month × retention × copies | retention × copies multiplies fast |
| **Data transfer** | inter-service, cross-AZ, cross-region | $/GB | "internal" traffic is not always free |
| **Non-production** | dev + staging + preview envs | fraction of prod, often 30–50% | idle/never-scaled-down is pure waste — model it |
| **Support / licenses** | seats, support plan %, per-seat tools | $/seat, % of spend | seat bands are a cliff |
| **Idle / always-on** | min instances, provisioned capacity, NAT gateways | $/hr regardless of load | NAT gateways and provisioned concurrency bill 24/7 |

## Forgotten-costs checklist (tick each: present / n/a-with-reason)

- [ ] Network egress to internet
- [ ] Cross-AZ / cross-region data transfer
- [ ] Logging & observability ingestion (and metric cardinality)
- [ ] Backups × retention × replica copies
- [ ] Non-prod environments (dev/staging/preview), incl. idle
- [ ] NAT gateway / load balancer / always-on networking
- [ ] Provisioned-but-idle capacity (min autoscale floor, reserved-but-unused)
- [ ] Support plan (% of spend) and per-seat tooling
- [ ] Data egress on delete/migration (one-time but real)
- [ ] Free-tier expiry (the bill that appears in month 13)

A model that hasn't consciously cleared this list is presumed 30–40% low.

## Headroom guidance (state the decision)

- **Target utilization:** the average you design for. 50–70% is common for spiky interactive workloads; 80%+ only for smooth, predictable, non-critical load.
- **Buffer:** peak × (failover redundancy + spike margin). N+1 across AZs is a multiplier, not a rounding.
- **Autoscale vs static:** if peak-to-average > ~2–3×, autoscaling usually beats provisioning for peak. State the floor (min capacity bills 24/7) and the scale-up latency (cold starts during a spike are an availability risk, an `nfr-spec` concern).
- The headroom number is a money-vs-incident tradeoff — write the reasoning, not just the multiplier.

## Common scaling cliffs (name the one that bites first)

- **Managed-service tier jump** — DB/cache/search moves to the next node size or shard count; cost steps, not slopes.
- **Single-node → distributed** — replication, coordination, and cross-node transfer appear all at once.
- **Cross-AZ egress threshold** — multi-AZ for HA turns "internal" traffic into a metered line.
- **Free-tier / committed-use ceiling** — the discount or free allowance runs out; effective unit price jumps.
- **License/seat band** — per-seat tools and support plans step at user-count thresholds.
- **Observability cardinality wall** — a new label dimension multiplies metric series and the bill with them.
- **Connection/throughput limits** — hitting a managed service's connection cap forces a proxy/pooler tier.

## Unit-cost-at-scale check

Compute cost-per-unit at 1×, 3×, 10×. The healthy shape is flat or declining (economies of scale). If per-unit cost **rises** with volume, the model has found an architectural anti-pattern (per-tenant fixed overhead, N² chatter, cardinality explosion) — surface it as the headline finding, because it means success makes the economics worse.

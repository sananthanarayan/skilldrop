# {Decision title — e.g. "Primary OLTP datastore for ProjectX"}

**Use case:** {one sentence describing the workload / constraints — this is what the weights are tuned to}

**Hard constraints:** {bulleted list of things that must be true; an option failing any of these is eliminated, not scored}

**Options evaluated:** {Option A}, {Option B}, {Option C}
**Options excluded (and why):** {e.g. "MongoDB — single-region writes only, fails the multi-region constraint"}

## Scoring scheme

- **Weight (1–5):** how much this criterion matters for *this* use case. Justified inline.
- **Score (1–5):** how well the option meets the criterion. Each 5 and 1 has a one-line justification.

## Matrix

| Criterion | Weight | {Option A} | {Option B} | {Option C} |
|---|---:|---:|---:|---:|
| Throughput (writes/sec at p99 < 50ms) — *weight 5: directly stated in use case* | 5 | 5 — published bench 50k/s | 3 — caps around 15k/s | 4 — 30k/s with read replicas |
| Consistency model fit — *weight 5: financial data, no eventual consistency tolerated* | 5 | 5 | 2 — eventual by default | 5 |
| Operational complexity (self-hosted) — *weight 4: team has 1 SRE* | 4 | 3 | 4 — fully managed | 2 — manual sharding |
| Cost at projected scale — *weight 3: budget approved but not unlimited* | 3 | 4 | 2 — egress fees | 5 |
| Team familiarity — *weight 3: shortens ramp* | 3 | 5 | 2 | 3 |
| Vendor lock-in — *weight 2: prefer portable but not blocking* | 2 | 5 — open source | 2 — proprietary | 4 |
| Ecosystem / tooling — *weight 2* | 2 | 5 | 4 | 3 |
| Backup & restore story — *weight 4: compliance requirement* | 4 | 4 | 5 | 3 |
| **Weighted total** | | **{=Σ w·s}** | **{=Σ w·s}** | **{=Σ w·s}** |

## Justifications for outlier scores

- *{Option A}, Throughput = 5:* {one-line evidence — link to vendor bench, internal load test, or known reference deployment}
- *{Option B}, Consistency = 2:* {one-line evidence}
- *{Option C}, Operational complexity = 2:* {one-line evidence}

## Recommendation

**Pick {Option X}** — it's strongest on the two highest-weighted criteria (throughput + consistency) and acceptable on the rest. The gap to {next option} is meaningful (~{N}%), so this is not a close call.

**What would change this answer:**
- If managed-ness becomes the top constraint (e.g., SRE leaves), reconsider {Option B}.
- If we relax the latency target above 100ms, {Option C} becomes viable and cheaper.

## Open questions

- {Question for stakeholders — e.g., "Is multi-region active-active in scope for v1, or v2+?"}

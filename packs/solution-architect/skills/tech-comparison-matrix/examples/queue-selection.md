# Worked example — weighted comparison of message queues

Input → output oracle for `tech-comparison-matrix`. Shows shown weights, a one-line
justification per score, honest "rough" markers, and a one-sentence recommendation.

## Input

> "We need a message queue for an order-processing pipeline: ~5k msg/s, must not
> lose messages, small team, already on AWS. Compare [managed-broker-A],
> [self-hosted-broker-B], and [cloud-queue-C]."

## Output

**Weights** (sum to 100, set by the stated constraints — durability and ops-load dominate because the team is small and messages can't be lost):

| Criterion | Weight | Why this weight |
|---|--:|---|
| Durability / no message loss | 30 | Hard requirement — order data. |
| Operational load | 25 | Small team; running a broker is a tax. |
| Throughput headroom | 15 | 5k/s is modest; all three clear it, so it's not decisive. |
| Delivery semantics / ordering | 15 | Orders need per-key ordering. |
| Ecosystem fit (AWS) | 15 | Already on AWS; native integration saves glue. |

**Scores** (1–5, each justified; ties kept where real):

| Criterion | Wt | [managed-broker-A] | [self-hosted-broker-B] | [cloud-queue-C] |
|---|--:|--:|--:|--:|
| Durability | 30 | 5 — replicated, managed | 5 — replicated *if* configured right | 5 — replicated, managed |
| Ops load | 25 | 4 — managed, some tuning | 2 — you patch/scale/monitor it | 5 — fully serverless |
| Throughput (rough) | 15 | 4 — ~tens of k/s | 5 — highest ceiling | 4 — ample for 5k/s |
| Semantics/ordering | 15 | 4 — ordered per partition | 5 — most flexible | 3 — FIFO variant, lower quotas |
| AWS fit | 15 | 3 — runs on AWS, not native | 2 — self-run on EC2/EKS | 5 — native service |
| **Weighted total** | | **4.15** | **3.55** | **4.45** |

**Recommendation:** Pick **[cloud-queue-C]** — its serverless ops profile decisively fits a small team with a modest, durability-critical load, and the only real gap (ordering quotas) is manageable at 5k/s.

*Directional note:* throughput scores are rough (order-of-magnitude, not benchmarked); if load is likely to 10× within a year, re-weight throughput up and re-score — [self-hosted-broker-B]'s ceiling starts to matter.

## Why this passes the quality bar

Weights are shown and tied to the question; every score carries a one-line justification; ties (durability 5/5/5) are left as ties; the guessed throughput numbers are flagged "rough"/"directional"; and the recommendation is one decisive sentence, not hedged.

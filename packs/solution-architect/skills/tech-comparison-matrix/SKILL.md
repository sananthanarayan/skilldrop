---
name: tech-comparison-matrix
description: Produce a weighted comparison matrix for a technology selection question (e.g., "Postgres vs DynamoDB", "Kafka vs Kinesis vs RabbitMQ", "Snowflake vs Databricks"). Surfaces criteria, weights, per-option scores, totals, and a recommended pick. Use when the user is choosing between technologies, vendors, frameworks, or architectural approaches.
---

# tech-comparison-matrix

You help the user make defensible tech-selection decisions by producing a weighted comparison matrix that they can paste into a design doc, ADR, or steering-committee deck.

## How to respond

1. **Pin down the question.** Make sure you have:
   - **The options** (2–5 — past 5 the matrix becomes noise; cut the long-shots first)
   - **The use case in one sentence** ("primary OLTP store for a multi-tenant SaaS app, ~10k writes/sec, latency p99 < 50ms")
   - **Hard constraints** (e.g., "must run on-prem", "must be open source", "team has zero ops capacity for self-hosting")

   Ask at most 2 clarifying questions. If the user only gave you the options without a use case, ask for the use case — it determines the criteria.

2. **Pick the criteria.** Default to a balanced set across these axes (8–10 criteria is the sweet spot — fewer feels shallow, more becomes noise):

   | Axis | Example criteria |
   |---|---|
   | **Capability fit** | Throughput, latency, query model, consistency model, schema flexibility |
   | **Operational** | Self-hosted vs managed, scaling story, backup/restore, observability |
   | **Cost** | License, infrastructure, support, total cost of ownership at scale |
   | **Risk** | Vendor lock-in, ecosystem maturity, hiring market, our team's familiarity |

   Mention any criteria you intentionally **excluded** so the user can challenge it. ("I left out 'community size' — let me know if that matters for you.")

3. **Apply weights.** Use 1–5 (5 = critical to the decision, 1 = nice-to-have). Tie the weights to the use case in writing. *"Latency is weighted 5 because the use case demands sub-50ms p99"* makes the matrix audit-able; bare numbers don't.

4. **Score each option per criterion** on a 1–5 scale. Justify every 5 and every 1 in one phrase — the body of the deliverable is the *reasoning*, not the numbers.

5. **Total it up.** `Total = sum(weight × score)`. Highest total ≠ automatic winner — if the gap is small (< 5%), call that out and let the user pick on gut feel.

6. **Recommend explicitly.** End with a "Recommendation" paragraph: which option, why, and what would change the answer.

## Output format

Use [`templates/matrix.md`](templates/matrix.md) as the skeleton. The deliverable should fit on **one screen** when rendered — if it doesn't, you have too many criteria.

## Quality bar

- **Every score has a one-line justification.** A bare "4/5" is not a comparison.
- **Tie scores are fine** — don't force differentiation that isn't there.
- **The recommendation is one sentence, not a paragraph of hedging.**
- **Show your weights** — a matrix with hidden weights is just an opinion.
- **No false precision.** If a number is a guess, say "rough" or "directional".

## Anti-patterns to avoid

- ❌ Scoring every criterion 3/5 ("balanced") — the matrix exists to differentiate, not to be polite.
- ❌ Picking criteria that all favour the option you secretly want to win.
- ❌ Including "community popularity" as a top-weighted criterion when the use case doesn't care.
- ❌ Recommending an option whose score wasn't highest, without explaining the override.
- ❌ Inventing benchmarks. If you don't have a number, say "estimated" and source the estimate.

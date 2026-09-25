---
name: okr-cascade
description: Cascade company OKRs to team-level OKRs — with a gap registry for objectives no team credibly owns, and a causal metric tree connecting each team KR to the north-star it's supposed to move. Use when the user wants to set or cascade OKRs, align team goals to company goals, "turn strategy into quarterly objectives", or audit existing OKRs for gaps and vanity metrics.
---

# okr-cascade

Turns company objectives into team OKRs that actually roll up — and surfaces what a cascade usually hides: the objectives nobody credibly owns (the **gap registry**) and the KRs that count activity instead of causing outcomes (the **causal metric tree**). Org-level counterpart to `success-metrics`, which owns feature-level measurement — this skill decides *what the teams aim at*; `success-metrics` designs how one feature proves it moved a KR.

## How to respond

1. **Get the company OKRs and the cycle.** From the input or by asking (at most 2 questions, spent on: *"what are the company's top 3–5 objectives this cycle, verbatim?"* and *"which teams are in scope?"*). Record company OKRs **verbatim** — rewriting the company's words without saying so corrupts the roll-up. No company objectives exist at all → stop; that's a strategy conversation (`strategy-analysis`), not a cascade. Non-interactive run (no user to ask): an unstated cycle or team list gets assumed and tagged `[assumption]`; absent company OKRs are never invented — emit `BLOCKED: need the company OKRs, verbatim — rerun with the top 3–5 objectives, their KRs, and the teams in scope` instead.

2. **Grade the company KRs before cascading them.** Each company KR is either an **outcome** (a customer or business result: retention, revenue, time-to-value) or an **output** (a thing shipped: "launch v2", "migrate to k8s"). Outputs at company level get flagged with the outcome they presumably serve — ✅ *"'Launch self-serve onboarding' → presumably serves activation rate; recommend restating as the activation target"*. Cascading an output produces teams that hit every KR while the business stands still.

3. **Derive team OKRs per company objective.** For each in-scope team: an objective (qualitative, motivating, this-cycle) and 2–4 KRs that are (a) **measurable at the team's scope** — the team's work moves the number without needing three other teams to also succeed; (b) **causally upstream** of a company KR, with the causal sentence written out: ✅ *"Cut p95 checkout latency to 800ms — slow checkout is the top named cause of cart abandonment `[data: support tags]`, which feeds company KR 'checkout conversion +2pp'"*; (c) **scored 0.0–1.0 at cycle end** — a KR that can only be "done/not done" is a task wearing a KR's clothes. Not every team maps to every objective — forcing it manufactures alignment theater; a team with no credible contribution to an objective simply doesn't appear under it.

4. **Build the gap registry.** A gap is a company objective or KR with **no team-level expression** after step 3 — no owner, no credible path, or a current-vs-target delta no in-scope team can close. Name each gap (kebab-case slug), state which company KR it starves, and rank gaps by the weight of the objective they block. The registry is a first-class output: a cascade with zero gaps on the first pass usually means step 3 was generous, not that the org is perfectly shaped — say so if it happens.

5. **Draw the causal metric tree.** North-star (the one user-behavioral outcome metric capturing this cycle's most strategic objective — never "features shipped") at the root; each team KR attached at its causal position as a leading indicator; each edge carrying its causal sentence. A KR that can't be attached to the tree is either a guardrail (label it) or measurement theater (cut it, and say which). No credible north-star derivable → report that as the cascade's top finding and recommend naming one before committing OKRs.

6. **Emit with [`templates/okr-cascade.md`](templates/okr-cascade.md)** in one message: company OKRs (verbatim, with output-KR flags), team OKRs with causal sentences, ranked gap registry, metric tree (Mermaid `flowchart` — north-star at root, KRs as leaves), and next steps: each team KR needing full measurement design → `success-metrics`; each gap needing a decision → the owner who must staff or explicitly drop it.

## Useful references in this skill

- [`templates/okr-cascade.md`](templates/okr-cascade.md) — cascade tables, gap registry, and metric-tree skeleton

## Quality bar

- **Company OKRs appear verbatim**, and every restated one is marked as restated with the reason.
- **Every team KR has its causal sentence** naming the company KR it feeds and the mechanism. "Aligns with company goals" is not a mechanism.
- **Every team KR is scorable 0.0–1.0** and measurable at the team's own scope. Binary deliverables are tasks — they can live under a KR, not as one.
- **Output KRs are flagged** at every level, each with the outcome it presumably serves.
- **The gap registry is present and ranked** — even when its honest content is "none found; here's why that's suspicious".
- **The metric tree has one north-star**, and every KR is attached, labeled guardrail, or explicitly cut.

## When to use this skill

- ✅ "Cascade our company OKRs to the platform/growth/mobile teams"
- ✅ Quarterly planning: turning strategy into team objectives
- ✅ Auditing existing OKRs — which are vanity, which roll up nowhere
- ✅ "Leadership set five objectives; which have no owner?"

## When NOT to use this skill

- ❌ Measuring one feature's success — `success-metrics` (it declares org OKRs out of scope; this skill returns the favor)
- ❌ No strategy exists to cascade — `strategy-analysis` or `prfaq` first
- ❌ Sprint/backlog prioritization — OKRs are aims, not a work queue
- ❌ Individual performance goals — cascading OKRs to persons turns a steering tool into a rating tool, and both break

## Anti-patterns to avoid

- ❌ **Cascading outputs.** "Company: launch v2 → Team: ship 12 features" — everyone hits 100% while retention falls. Flag outputs at intake or inherit the disease.
- ❌ **Alignment theater.** Every team forced under every objective, with prose doing the aligning that causality can't. Empty cells are information.
- ❌ **Vanity KRs.** Page views, sign-ups, story points. If the number can improve while the business doesn't, it can't be a KR.
- ❌ **A gapless first pass.** The registry exists because real orgs have orphaned objectives — a clean sheet means the bar in step 3 slipped.
- ❌ **KR-as-task-list.** "Complete the migration" scores 0 or 1 and measures effort. What outcome does the migration purchase? That's the KR.
- ❌ **Metric list instead of metric tree.** "DAU, NPS, churn, revenue" with no causal positions is a dashboard inventory, not a tree — every node needs its edge.
- ❌ **Silent rewording of company OKRs.** Improving leadership's phrasing without marking it breaks the roll-up contract and hides a real disagreement worth surfacing.

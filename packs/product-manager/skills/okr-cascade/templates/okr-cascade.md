# OKR Cascade — {cycle, e.g. 2026 Q4}

> Teams in scope: {list} · Source of company OKRs: {doc/person} · Status: DRAFT

## Company OKRs (verbatim)

### O1: {objective, verbatim}
| KR | Type | Note |
|---|---|---|
| {KR verbatim} | outcome / **output ⚠** | {if output: the outcome it presumably serves} |

## Team OKRs

### Team: {name}

**O: {team objective — qualitative, motivating, this cycle}** _(feeds company O1)_

| KR | Baseline → Target | Causal sentence (mechanism → company KR) | Scoring |
|---|---|---|---|
| {KR} | {x → y} | {why moving this moves company KR n} | {how 0.0–1.0 is graded, e.g. linear on pp gained} |

<!-- A team with no credible contribution to an objective doesn't appear under it. -->

## Gap registry (ranked)

| # | Gap slug | Company KR or objective it starves | Why no team covers it | Decision needed from |
|---|---|---|---|---|
| 1 | {kebab-slug} | {KR, or "On (objective-level)"} | {no owner / no credible path / delta too large} | {role} |

## Causal metric tree

North-star: **{one user-behavioral outcome metric}**

```mermaid
flowchart BT
    KR1["{team KR}"] -->|{causal sentence, short}| NS["{north-star}"]
    KR2["{team KR}"] -->|{…}| NS
    G1["{guardrail KR}"] -.->|guardrail| NS
```

Cut from the tree: {KRs that attached nowhere, and why} — or "none".

## Next steps

- {team KR} → run `success-metrics` for full measurement design (baseline, counter-metric, instrumentation)
- {gap slug} → {owner role} staffs it or explicitly drops it by {date}

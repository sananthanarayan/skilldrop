# NFR-spec template

The ledger is the contract: all 11 categories appear, each in exactly one state — **target** / **n/a (reason)** / **default `[assumption]`**.

```markdown
# NFR spec: {feature / system}

**Archetype:** {customer-facing SaaS | internal tool | public API | batch | mobile/edge}
**Down-for-an-hour answer:** {verbatim from stakeholder — calibrates availability} `[reported]`
**Date:** {YYYY-MM-DD} · **Feeds:** design-doc, test-plan-generator, threat-model

## Ledger (all 11 — no silent rows)

| # | Category | State | Target / reason | Verification |
|---|---|---|---|---|
| 1 | Performance | target | p95 < 800ms search @ 2× peak (120 rps) | load test |
| 2 | Throughput | default `[assumption]` | 2× peak headroom | load test |
| 3 | Availability | target | 99.9% monthly, user-visible boundary | chaos drill + SLO dashboard |
| 4 | Durability/DR | target | RPO ≤ 5min, RTO ≤ 1h | timed restore rehearsal |
| 5 | Privacy/retention | target | see data-class table | deletion end-to-end test |
| 6 | Accessibility | target | WCAG 2.2 AA, all customer screens | axe + screen-reader pass |
| 7 | i18n | n/a | single-locale launch, stated in PRD non-goals | — |
| 8 | Observability | target | 3am questions below | game-day |
| 9 | Operability | default `[assumption]` | rollback ≤ 15 min; per-dep down-behavior | rollback drill |
| 10 | Compatibility | default `[assumption]` | last 2 major browsers | CI matrix |
| 11 | Cost | target | ≤ $N/mo @ target volume, alert at 80% | projection vs first bill |

## Per-category detail

{One block per non-n/a row: the target restated with its load condition and
source of the numbers, the verification method, and who owns it.}

## Data classes (category 5 expanded)

| Data | Classification | Retention | Deletion mechanism | Residency |
|---|---|---|---|---|
| {what} | {PII/payment/none} | {period or "indefinite — explicit decision"} | {TTL / user-triggered / legal-hold-aware} | {constraint or none} |

## 3am questions (category 8 expanded)

- On-call can answer "{question}" within {time}, from {alert/dashboard}.
- Alert: {condition + threshold + paging severity} → runbook entry: {ref}.

## Security posture (one line — depth lives in threat-model)

{e.g. "Authn via platform SSO; tenant-scoped authz; PII per table above. Full analysis: threat-model."}

## Assumptions log

- [assumption] {default taken} — confirm with {role} by {date}

## Exceeding-default justifications

{Required whenever a target beats the archetype default: "99.95% chosen over 99.9%
because {contractual SLA}; accepted cost: {on-call rotation, multi-AZ spend}."}
```

---
name: nfr-spec
description: Sweep a feature or system through the full non-functional requirements catalog — performance, throughput, availability, durability, privacy/retention, accessibility, i18n, observability, operability, compatibility, cost — forcing every category to a measurable target, an explicit n/a, or a tagged default. Use when the user needs NFRs, quality attributes, "how fast/reliable does it need to be", SLO targets for a feature, or the requirements everyone forgets until they're incidents.
---

# nfr-spec

Gathers the requirements nobody volunteers: the business says what the feature does, this skill pins down **how well** — with numbers. Every category in the catalog ends in exactly one of three states: a **measurable target with a verification method**, an explicit **n/a with a reason**, or an **accepted default tagged `[assumption]`**. Silence is the one forbidden state. Downstream of `prd-draft`; feeds `design-doc` (targets shape the architecture), `test-plan-generator` (verification methods become test cases), and `threat-model` (security depth lives there, not here).

## How to respond

1. **Classify the system first** — the archetype sets the defaults: customer-facing SaaS, internal tool, public API, batch/pipeline, mobile/edge. Ask at most 2 questions, spent on the two answers that move the most targets: **user-facing or internal**, and **what happens when it's down for an hour** (the honest availability requirement hides in that answer). Everything else: archetype default + `[assumption]`.

2. **Sweep every category in [`reference.md`](reference.md)** — performance/latency, throughput/capacity, availability/SLO, durability/backup/DR, privacy/retention/residency, accessibility, i18n/l10n, observability, operability, compatibility, cost. For each: target, verification, or n/a-with-reason. The output includes the **full ledger** so a reviewer sees the sweep happened — a skipped category is indistinguishable from a forgotten one otherwise.

3. **Force numbers tied to business reality, not aspiration.** ✅ *"p95 search < 800ms at 2× current peak (peak = 120 rps `[data: April dashboard]`)"* — ❌ *"sub-second response times"* (which percentile? at what load?) — ❌ *"99.999% availability"* for an internal tool whose users sleep at night (five nines costs 100× three nines; the archetype default exists to stop this).

4. **Attach a verification method to every target** — the method that would prove it before launch, not after: load test at stated volume, chaos drill, restore-from-backup rehearsal, axe-core scan + screen-reader pass, locale pseudo-translation run, cost projection at target volume. An NFR without a verification is a hope with units. These methods hand straight to `test-plan-generator`.

5. **Make retention and deletion first-class.** For every data class the feature touches: what's stored, how long, where (residency), and **how deletion actually happens** (user-triggered, TTL, legal hold override). "We keep it forever" is a decision with legal weight — make it visible, never implicit.

6. **State observability as requirements, not tooling.** What must be answerable at 3am: ✅ *"On-call can see per-tenant error rate and the last deploy time within 2 minutes of an alert"* — ❌ *"Use Datadog"*. The instrument choice is `design-doc`'s; the questions-it-must-answer are NFRs.

7. **Point, don't duplicate, for security.** One line stating the auth/data-classification posture, then hand depth to `threat-model`. An NFR doc with a 3-page security section has stolen another skill's job and done it worse.

8. **Emit with [`templates/nfr-spec.md`](templates/nfr-spec.md)**: summary table (category / target / verification / state), per-category detail, the n/a ledger, assumptions log, and the handoff map.

## Useful references in this skill

- [`reference.md`](reference.md) — the category catalog with per-archetype defaults and the verification menu
- [`templates/nfr-spec.md`](templates/nfr-spec.md) — the ledger-style output skeleton

## Quality bar

- **Every category lands in one of three states** — target, n/a-with-reason, or tagged default. The ledger shows all of them; silence fails the doc.
- **Every target has a percentile, a load condition, and a verification.** A latency number without load is a screenshot of a quiet day.
- **Availability matches the down-for-an-hour answer**, not the marketing instinct. The cost of each extra nine is named when the target exceeds the archetype default.
- **Every data class has a retention period and a deletion mechanism.** "Indefinite" is written as the decision it is.
- **Accessibility names level and scope** — "WCAG 2.2 AA on all agent-facing screens, axe + manual screen-reader pass" — not "accessible".
- **Cost has a number at target volume**, or a tagged `[assumption]` placeholder that explicitly hands the sizing to `capacity-cost-model`. Either way the line is present — an NFR spec that's silent on cost has delegated it to the first invoice.

## When to use this skill

- ✅ A PRD is done and the quality targets need pinning before design
- ✅ "How fast / how reliable / how much does this need to be?"
- ✅ Defining SLOs for a new service or feature
- ✅ A legacy system getting its implicit NFRs written down for the first time

## When NOT to use this skill

- ❌ Functional requirements — that's `prd-draft`
- ❌ Security threat depth — one posture line here, the analysis is `threat-model`
- ❌ Designing the architecture that meets the targets — `design-doc`
- ❌ Writing the verification tests themselves — hand the methods to `test-plan-generator`

## Anti-patterns to avoid

- ❌ **"As fast as possible."** That's a budget of infinity. Every performance target gets a percentile, a number, and a load.
- ❌ **Five-nines cargo cult.** Availability copied from a FAANG blog onto an internal CRUD tool — each nine multiplies cost; the down-for-an-hour question calibrates honestly.
- ❌ **Uniform targets.** The same p95 for search, checkout, and a monthly export means nobody thought about any of them.
- ❌ **"GDPR compliant" as the entire privacy section.** Which data, retained how long, deleted how, stored where — compliance is the output of those answers, not a substitute for them.
- ❌ **Tool names as observability requirements.** "Use Prometheus" survives a migration to nothing; "alert fires within 2 min of error-rate breach" survives any tool.
- ❌ **Untestable NFRs.** "The system shall be maintainable" — if no verification method exists, it's culture, not a requirement; cut it or make it measurable.

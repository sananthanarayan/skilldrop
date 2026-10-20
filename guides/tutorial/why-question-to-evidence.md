---
title: A why question to an answer the evidence carries
summary: Run the research loop on a conversion drop everyone blames on a new onboarding flow. The plan fixes what would change the decision first, the gate refuses to pick between two tied explanations, and one reconciliation shows the drop was a tracking bug.
kind: tutorial
---

# A why question to an answer the evidence carries

In about twenty minutes you'll run the `research` loop on a question with a decision riding
on it. Conversion fell, and the new onboarding flow is about to be rolled back. You'll see
the loop write down what would change that decision before it reads a source. Its gate will
refuse to choose between two explanations the evidence can't separate, and it will name the
one check that can. That check turns out to settle it: the drop was mostly a counting error.

Everything quoted below is from a real run of the loop on Claude Sonnet 5 with the files on
this page.

## Install the loop

```bash
npx skilldrop-cli install --loop research
```

This installs the loop with `research-plan`, `source-synthesis` and `hypothesis-comparison`.

## Put the sources in a folder

Make a `sources/` folder with four short files. The first is the analytics export,
`analytics-export.csv`:

```text
week_start,trials_started,trials_converted,conversion_pct,tracking_note
2026-08-25,415,59,14.2,
2026-09-01,420,56,13.3,
2026-09-08,431,47,10.9,payment-success event renamed in app v4.2 (deployed 11 Sep)
2026-09-15,428,37,8.6,
2026-09-22,436,38,8.7,
2026-09-29,429,39,9.1,
```

The run used three more August weeks at 14.1%, 14.2% and 13.8%. The other three files are:

- **`release-notes-september.md`.** v4.2 on 11 September replaced the guided tour with a
  setup checklist. The same release renamed the `payment_success` analytics event to
  `checkout_completed`, and said dashboards reading the old name should be updated.
  v4.2.1 on 18 September fixed the checklist not appearing on mobile.
- **`sales-call-notes.md`.** In 12 calls, 4 prospects mentioned that Rivalco cut its price
  (2 called it the main reason), 3 said the checklist was clearer, and 2 couldn't find where
  to invite teammates. The AE lead notes that these calls skew to larger accounts.
- **`rivalco-pricing.md`.** Team plan $29 per seat, down from $39 on 4 September.

## Start the loop with the decision

> Run the research loop: why did our trial-to-paid conversion drop from 14% to 9% in
> September? I've put the sources in sources/ (a product analytics export, the September
> release notes, 12 sales call notes, and a competitor's pricing page). The growth lead
> decides by 1 November whether to roll back the new onboarding flow.

Naming the decision matters. Without it, the loop stops and asks for it, because a stopping
rule set against a guessed decision stops in the wrong place.

## Read the plan before anything else

`research-plan` writes `plan.md` before any source is read. For each sub-question it writes
the finding that would move the decision either way:

> **2.** Is any part of the measured drop a tracking/instrumentation artifact rather than a
> real behaviour change? → If the `payment_success` → `checkout_completed` rename (11 Sep)
> caused undercounting, part of the drop is a measurement artifact, not a product problem —
> rollback wouldn't fix it. Threshold: if the artifact plausibly accounts for most of the
> drop, recommend fixing tracking before deciding on rollback.

It also sets the stopping rule before reading anything: stop once each sub-question is
answered well enough to rank the explanations, with at least one piece of diagnostic
evidence separating the leader from the runner-up.

## Watch the gate refuse to pick

`source-synthesis` writes a cited summary, every claim tied to a file and line. Then
`hypothesis-comparison` sets four explanations against fifteen pieces of evidence:

- the onboarding flow;
- the renamed tracking event;
- Rivalco's price cut;
- normal variation.

Each explanation is ranked by how much evidence contradicts it, not by how much fits it.

The onboarding flow comes out the most contradicted of the three live explanations. The
mobile fix shipped and conversion didn't recover, and more callers liked the checklist than
disliked it. But nothing separates the tracking bug from the price cut. G7 says so:

> **G7: REVISE** — the top two hypotheses (competitor pricing, tracking artifact) are tied
> with no diagnostic row separating them, and the discriminating observation (event-log
> reconciliation) isn't in the four supplied sources — it needs a one-day data pull from
> the analytics team before the 1 Nov decision.

A loop that ranked by supporting evidence would have named a winner here. This one names
the check instead. If reconciled conversions climb back to about 13–14%, it was the
tracking; if they stay near 9%, the drop is real and pricing leads.

## Add the one observation and go round again

Ask the data team for the reconciliation and add it as a new source,
`sources/event-reconciliation.csv`, with conversions as the dashboard counts them, under
every event name, and from billing. Then:

> Continuing the research loop. The data team ran the reconciliation you asked for; it's in
> sources/event-reconciliation.csv.

| Week | Dashboard reported | Reconciled (event logs) | Billing (new paid accounts) |
|---|---|---|---|
| 1 Sep | 13.3% | 13.3% | 56 |
| 8 Sep | **10.9%** | **13.0%** | 57 |
| 15 Sep | **8.6%** | **12.9%** | 55 |
| 22 Sep | **8.7%** | **13.1%** | 58 |
| 29 Sep | **9.1%** | **13.1%** | 56 |

Two separate systems agree, and both sit near the August baseline. This is round 2 of the
cap of 3:

> **G7: PROCEED WITH CONDITIONS** — diagnostic evidence (the reconciliation) clearly
> separates the tracking-artifact explanation from the others and meets the plan's
> threshold; the condition is that the ~1-point real residual and its cause (onboarding vs.
> pricing) remain open and unquantified.

The answer the growth lead gets leads with the decision: don't roll back the onboarding
flow, fix the dashboard, and fix the invite-teammates complaint on its own if it matters.

## What you have now

A plan that recorded what would change the decision before anyone looked, a synthesis with
every claim cited, and a comparison ranked on contradicting evidence. The verdict changed
because of one new observation, not more reading. The rollback, which the first theory
pointed to, would have fixed nothing.

Next: [The loops, stage by stage](../reference/loops.md) for the `research` diagram, or
[Use the research pack](../how-to/packs/use-the-research-pack.md) to run one skill on its own.

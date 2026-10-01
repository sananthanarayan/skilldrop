# PRD template

Sized for a 30-minute read. Every claim tagged `[reported by …]`, `[data: …]`, or `[assumption]`.

```markdown
# PRD: {feature name — noun phrase, not a solution name if avoidable}

**Status:** draft | in review | frozen · **Owner:** {role} · **Date:** {YYYY-MM-DD}
**Binding constraint:** {fixed deadline | fixed scope | fixed team} `[reported|assumption]`

## Problem

{Who, in what situation, suffers what, evidenced by what. Zero solution nouns.
Test before moving on: could this paragraph justify a completely different
solution than the one in everyone's head? If not, rewrite.}

## Users

**Primary:** {persona specific enough to find one} — job-to-be-done: {what they're
trying to accomplish when they hit the problem}
**Secondary (explicitly deprioritized):** {personas served incidentally, one line on why not primary}

## Goals

| # | Goal | We'll know it worked when |
|---|---|---|
| G1 | {outcome, not output} | {metric + target + timeframe; baseline if known, else "[baseline needed]"} |

Full measurement design (instrumentation, guardrails, decision rule): hand to `success-metrics`.

## Requirements

| ID | Requirement (testable, solution-free) | MoSCoW | Maps to goal |
|---|---|---|---|
| R1 | {observable behavior/capability a tester can verdict} | M | G1 |
| R2 | … | S | G1 |

**Won't have (this version):**
- {the tempting thing} — {one line why out}

## Non-goals (minimum 3 — the scope-creep firewall)

- **{Thing stakeholders will plausibly ask for}** — {why it's out; when it might come back}

## Quality targets

One line each if known; full treatment → `nfr-spec`.
{e.g. "Agent-facing: p95 lookup < 3s. Availability follows the support-tools tier."}

## Open questions

| Question | Owner | Needed by |
|---|---|---|
| {blocker to freezing requirements} | {person/role who can answer} | {date} |

## Assumptions log

- [assumption] {default picked} — challenge by {date/review}

## Handoffs

- Stories & slicing → `user-story-splitter`
- Quality targets → `nfr-spec`
- Measurement → `success-metrics`
- Technical approach → `design-doc`
```

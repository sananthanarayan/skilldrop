---
rfc: 0052
title: Research, comply and measure loops
status: accepted
date: 2026-10-19
author: sanjay-ananth
---

# RFC-0052: Research, comply and measure loops

## Problem / use case

Three packs added in 0.14.0 each hold skills that are only useful in order, and nothing
writes the order down. In `research`, a synthesis written before a plan answers whichever
question the sources happen to address, and a comparison of explanations run on uncited
notes ranks a favourite theory. In `grc`, a risk register whose residual ratings assume
controls nobody has evidenced looks finished and is wrong, and a DPIA filed apart from the
register leaves its risks to people off the list the owner signs. In `data-analytics`, SQL
reviewed before anyone has said which numbers the dashboard needs gets reviewed for charts
that are then cut, and a dashboard built on an unreviewed query publishes the wrong number
with a chart around it.

## Fit check

A structural change: three loops over skills that already exist (golden rule: sequencing
lives in a loop, never in a skill). No skill changes, and each skill still runs on its own.

- Each loop lives in one pack that, with `core`, holds every skill it runs.
- None goes in `model-routing.json`.
- Gate ids follow RFC-0044: the loops outside the lifecycle take G7, G8 and G9.

## Proposal

| Loop | Pack | Stages | Gates |
|---|---|---|---|
| `research` | `research` | `plan` (`research-plan`) → `synthesise` (`source-synthesis`) → `compare` (`hypothesis-comparison`) | **G7** review on evidence strength |
| `comply` | `grc` | `register` (`risk-register`) → `assess` (`dpia`) → `evidence` (`soc2-evidence-map`) → `check` → `sign-off` (`doc-critique`) | **G8** mechanical, `check_register.py`; **G8.1** human, the risk owner |
| `measure` | `data-analytics` | `spec` (`dashboard-spec`) → `review` (`sql-review`) → `sign-off` (`doc-critique`) | **G9** review, every query; **G9.1** human, the metric owner |

The rules each loop adds, which no single skill can enforce:

- **research:** the comparison rates only evidence the synthesis cited. G7 passes only when
  diagnostic evidence separates the leader from the runner-up, no linchpin rests on one
  source, and the plan's stopping rule is met. `REVISE` goes back to `synthesise` with the
  observation the comparison named as the one that would separate them.
- **comply:** the DPIA's risks to people join the register. A residual rating that relies on
  a control with an evidence gap reverts to its inherent rating until the evidence exists.
  The register's own script decides G8. Only the named owner accepts a residual risk, at G8.1.
- **measure:** the spec comes first, so only the queries behind charts that survive the cut
  list are reviewed. A query whose review is `BLOCK` or `FIX FIRST` sends the metric back to
  `spec`, because fixing it changes the number the chart shows. An `undefined` metric can't
  pass G9.1: its owner defines it or the chart is cut.

`metric-definition`, retired by RFC-0046, is not restored: the plain agent defines a metric
as well without it. The definition happens in `spec`, and its owner confirms it at G9.1.

## Alternatives considered

- **Pack journeys only.** Each `pack.json` already lists its skills in order, but a journey
  has no gate and no cap. The failures above all happen between two skills, and a journey has
  nowhere to stop them.
- **Measure in the order metric, SQL, dashboard.** Reviewing SQL before the spec reviews
  queries for charts the cut list then removes. The spec says which numbers matter.
- **A citation check as a second research gate.** `source-synthesis` already runs its own
  citation script. A loop gate on it could only send the draft back to itself.

## Decision

Accepted. Shipped in 0.16.29.

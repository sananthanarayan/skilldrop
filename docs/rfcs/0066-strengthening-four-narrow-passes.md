---
rfc: 0066
title: Strengthening four skills that only just passed admission
status: implemented
date: 2026-10-22
author: sanjay-ananth
---

# RFC-0066: Strengthening four skills that only just passed admission

## Problem / use case

Four skills were admitted at the bar's edge: one or both judges preferred them in exactly half
of the held-out pairs.
- `md-to-pptx` and `event-contract-draft` (RFC-0057, evals 4–5);
- `judge-audit` (evals 8–9, its third draft);
- `bundle-size-review` (evals 6–7, its second draft, which met 31% of the checks, the same as
  plain Claude Code).

Passing at the edge means a reader of the scorecard has little reason to choose them. Each lost
pairs for reasons its judges wrote down.

## Fit check

No new skills and no new flags. Each revision comes from the judges' reasons on the evals that
skill already had. Each is measured on two new held-out evals, written blind from the
description only. Nothing from any held-out eval goes into a skill's text. Draft examples in
all four that reused held-out figures or scenarios were caught by a scan of the diff against
every held-out eval, and replaced before measuring.

## Proposal

**md-to-pptx 0.1.2.** The judges marked down split risk items, a near-empty last slide, a
chart that "vanished", and confidential figures repeated in the reply.
- **Item boundaries.** A split moves a whole list item, from its top-level line, when a nested
  line would start the next slide. The exception is an item taller than 80% of a slide.
- **Balancing.** A section that splits is re-packed into less height while it keeps the same
  number of slides, so no continued slide is left with two lines.
- **Placeholder images.** An image under 64 pixels on a side gets a warning. An 8×6 placeholder
  embedded at its size was the "missing" chart.
- **Internal notes.** They are taken out of a deck the user says goes outside the team. The
  reply describes a note, never quotes it.

**event-contract-draft 0.1.3.** The judges marked down a reply that:
- rewrote the user's payload unasked;
- pasted a truncated AsyncAPI document;
- claimed a check passed without showing it;
- buried the answers to the user's questions.

Now:
- **The user's draft stays theirs.** Every change is listed with the rule it fixes, and other
  changes are only suggested.
- **Each question is answered in its own line first.**
- **The document is whole,** and the reply shows field tables instead of JSON.
- **The check is reported as what it covered.**

**judge-audit 0.3.1.** Its numbers were mostly right by its third draft. The losses were these:
- **A quoted figure that didn't reproduce.** It now gives its own figure, the statistic and
  the rows, and never rounds toward the quoted one.
- **The end of the scale.** It now reads the label distribution, for a judge that never uses
  one end of it.
- **What a score predicts.** It now checks that against outcome rates per score band, not
  against kappa.
- **Uneven sample-size standards.** Every subgroup is now held to the same one, and the headline
  and the verdict word agree.
- **Scratch files.** It now leaves none behind.

**bundle-size-review 0.2.3.** It lost pairs for describing a fix when the user needed the edit,
and for a budget step naming a flag that doesn't exist. Each fix is now the exact edit to a named
file, and files change only when asked. A guard is real configuration for a tool the repo has.

## Measured

Two new held-out evals per skill; two trials; model claude-sonnet-5; judges claude-sonnet-5-5
and claude-opus-5-5. Spend $10.23.

| Skill | Evals | Judge 1 | Judge 2 | Checks met | Plain Claude Code | Before (judges) |
|---|---|---|---|---|---|---|
| md-to-pptx | 6–7 | 2 of 4 | 3 of 4 | 59% | 22% | 2 and 2 of 4 |
| event-contract-draft | 6–7 | 2 of 4 | 3 of 4 | 56% | 31% | 2 and 3 of 4 |
| judge-audit | 10–11 | 4 of 4 | 2 of 4 | 73% | 65% | 2 and 2 of 4 |
| bundle-size-review | 8–9 | 3 of 4 | 3 of 4 | 56% | 16% | 3 and 3 of 4 |

**Where they still lose**
- **md-to-pptx:** a Mermaid diagram still shows as code when it can't be rendered offline.
- **event-contract-draft:** on a narrow "rewrite this spec" request it reaches further than
  asked.
- **judge-audit:** the second judge preferred the plainer reply on one eval.
- **bundle-size-review:** once, a working, verified size check from the baseline beat its
  guidance.

These are recorded, not tuned against: a fix would come from a new eval.

## Alternatives considered

- **Re-measure on the old held-out evals.** Revising from their judges' reasons and then scoring
  on them would be tuning on the test.
- **Retire the narrow passes.** Each beats plain Claude Code on checks met, and three by wide
  margins. Their losses were specific enough to fix.

## Decision

Accepted and implemented. The admission records in `docs/benchmarks/admissions.json` now cite
this RFC and the new evals.

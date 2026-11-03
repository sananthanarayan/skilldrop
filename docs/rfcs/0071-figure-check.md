---
rfc: 0071
title: A figure check that traces every number in a draft to its source
status: rejected
date: 2026-11-03
author: sanjay-ananth
---

# RFC-0071: A figure check that traces every number in a draft to its source

## Problem / use case

An exec summary, business case or status report is written from an export, a spreadsheet and
someone's notes, and the numbers are what the reader acts on. The failures are specific, and
the benchmark has watched the plain agent make them:
- a figure that comes from nowhere ("saves £58k a year");
- a figure rounded toward the claim it supports (64% written as "two thirds");
- a figure quoted from the wrong line (a target reported as the result);
- a difference in percentage points written as a percentage.

`judge-audit` lost pairs for giving a quoted figure that didn't reproduce (RFC-0066), and
`file-to-markdown` was rebuilt after keeping a total its source contradicted (RFC-0068). A
read-through catches totals that don't add up. It misses the invented figure, because a
plausible number is why it's there.

## Fit check

- **Concrete artifact:** a line-by-line table of every figure in the draft with its source
  location or formula, plus the draft with only the untraced and misquoted figures changed.
- **Portable:** one folder with a stdlib-only script, no network. It reads Markdown, text and
  CSV paths it's given.
- **Opinionated:** every untraced figure is sourced, marked `[estimate]` with its basis, or
  cut. It is never moved to a nearby number. Points and percentages are never mixed.
- **Category:** pipeline glue, in `core`, beside `doc-critique` and `output-hygiene`. Any
  document with numbers needs it, whatever the role.

**The rule it adds that the plain agent breaks** (the RFC-0046 bar): *every figure traces to
a source location or to one visible calculation from sourced figures, and one that doesn't is
marked or cut, never adjusted toward a number that happens to be nearby.* The script makes that
checkable. It finds every figure, the line it matches, and the near misses and alternative
calculations, so the model's judgment is limited to whether each trace is the same quantity.

## Proposal

- **`figure-check`**, tier `standard`. The script does the tracing; the model decides per
  finding and edits only those lines.
- **Script:** `figure_check.py DRAFT --source FILE … [--json] [-o OUT]`, which statuses each
  figure:
  - `exact`;
  - `rounded`, with the source value beside it;
  - `derived`, from a sum, difference, share, percentage change, point difference, multiple,
    per-unit × count, or column total or mean, with the formula and both locations;
  - `untraced`.

  It only combines figures that sit near each other, so a large source can't make every number
  derivable. A near miss outranks a coincidence down a column. Exit 0 if every figure traces, 1
  if any is untraced, 2 for bad input.
- **`related`:** `doc-critique`, `source-synthesis`, `exec-summary`, `output-hygiene`.
- **Quality bar:** every figure has a status and its evidence. No untraced figure survives
  unmarked. No figure is moved toward a number the author didn't write. Lines without findings
  are untouched.
- **Anti-patterns:** "fixing" an untraced figure to the nearest source number; accepting a
  trace without reading the source line.
- **Loop use:** the `ship-a-draft` wrapper's figures stage (RFC-0069) runs the script as
  mechanical gate G5.1, with exit codes 0, 1 and 2 read as `READY`, `NOT READY` and `BLOCKED`.

**Admission.** The skill ships with three author evals. It counts as admitted only after
held-out evals, written blind from its description, show it beating the plain agent on the
RFC-0040 benchmark.

## Alternatives considered

- **Add a numbers pass to `doc-critique`.** The critique reads the argument against a rubric
  and does catch totals that don't add up. Tracing every figure to a file and line is a
  different job with a script behind it, and bundling it in would make the critique heavier for
  documents with no numbers.
- **Generalise `resume-tailor`'s `claim_check.py`.** That checks a candidate's claims against
  their own material and lives in the career pack. A skill can't depend on another skill's
  script, and the job here (calculations, CSV columns, rounding) is wider.
- **Do nothing.** The plain agent then checks figures by eye, and the benchmark has seen what
  it misses.

## Measurement

Measured as every admission is: held-out evals written blind from the description, two
trials, `claude-sonnet-5-5` as the agent, and judges `claude-sonnet-5-5` and `claude-opus-5-5`.
The bar is the plain agent losing at least half the blind pairs.

| Draft | Evals | Checks met: skill / plain | Pairs won, judge 1 / judge 2 (of 4) | Cost |
|---|---|---|---|---|
| 1 | 4–5 | 78% / 66% | 1 / 1 | $0.89 |
| 2 | 6–7, fresh | 93% / 76% | 0 / 1 | $0.86 |

What the judges wrote:
- **Draft 1** lost on a draft with no sources, where the skill's rule was to emit `BLOCKED`.
  The person had asked for a check of the document itself, and the plain agent did it. In one
  run the skill passed £186,500 as traced because the value matched, though the sentence
  meant spend to date and the source gave one quarter.
- **Draft 2** checked a draft with no sources against itself, and read the period words in a
  sentence before accepting a trace. Draft 2 met more checks, and found the same errors as the
  plain agent. It lost the blind pairs on how it replied:
  - it wrote a corrected copy and edited the draft when only a check was asked for;
  - it cut the person's unsourced figure instead of flagging it;
  - it referred to "the script" and "the checker", which the person never saw.

So the rule the skill adds doesn't beat the plain agent. Sonnet 5.5 finds wrong totals, wrong
percentages and unsupported figures unaided. What's left for a skill is the reply's shape, and
the plain agent gets that right already.

## Decision

Rejected. The skill isn't shipped, and the `ship-a-draft` figures gate it would have backed
(G5.1) goes with it. RFC-0069 ships the four loops without it.

A third draft would follow three rules: answer the question asked and leave the draft alone
unless edits are asked for; flag an unsourced figure rather than cut it; keep every mention of
tooling out of the reply. It would need fresh blind evals, because evals 4–7 and their judges'
reasons have now been read. Its folder and both drafts' evals are kept on the local branch
`sanjay-ananth/figure-check-wip`.

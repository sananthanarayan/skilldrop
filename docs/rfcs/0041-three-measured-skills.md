---
rfc: 0041
title: Three skills admitted on a benchmark result
status: implemented
date: 2026-10-02
author: sananthanarayan
---

# RFC-0041: Three skills admitted on a benchmark result

## Problem / use case

The first benchmark (RFC-0040) showed that skills raise scores on their own rubric and are
not clearly preferred by a blind judge. Adding more skills the old way would add more of the
same. Three jobs people report doing by hand have no skill here: writing a pull request
description, turning technical-debt complaints into a ranked list, and answering a customer's
security questionnaire.

## Fit check

- **Concrete artifact:** a PR title and body; a debt register table; a questionnaire answer
  file with evidence citations.
- **Portable:** plain `SKILL.md` folders, no scripts, no dependencies.
- **Opinionated:** each fixes the output's order and refuses to invent (test results, costs,
  certifications) instead of asking.
- **Category:** `pr-description-writer` and `tech-debt-register` in `dev-team`;
  `security-questionnaire-response` in `grc`.

## Proposal

- **`pr-description-writer`** (standard tier; related: `release-notes`, `pre-merge-review`,
  `test-plan-generator`). Bar: everything traces to the diff, the test section lists only
  checks that were run, surprises the commits skip are reported. Bans: restating commit
  subjects, "tested locally".
- **`tech-debt-register`** (standard; related: `migration-plan`, `bug-triage`,
  `backlog-triage`, `risk-register`). Bar: every cost has evidence or says it has none, every
  item has a decision and a trigger. Bans: invented numbers, everything-is-high-priority.
- **`security-questionnaire-response`** (standard; related: `soc2-evidence-map`, `dpia`,
  `threat-model`, `risk-register`). Bar: every Yes, No and Partial cites a document, gaps and
  conflicts are listed first. Bans: "Yes" from common practice, upgrading a claim.

Two rules are new for these three and are the reason for this RFC:

1. **Three evals each, with input files, from the start.** Per-skill numbers from one eval
   are anecdotes (RFC-0040).
2. **Admission on a measured result.** Each skill is run through `run_bench.py` with two
   trials and two judges before release. The result is recorded below, including when it is
   unflattering.

They are also written to the lessons of the first run: deliver from what was given and state
what is unknown instead of stopping, keep the reply free of the skill's own vocabulary, and
keep the artifact short.

## Alternatives considered

- **A new `proposals` pack** with an RFP response skill beside the questionnaire skill. Held
  back: one skill is not a pack, and `grc` already owns the evidence the answers rest on.
- **Scripts for each** (a diff scanner, a register checker). Left out for now; the first run
  did not show script skills being preferred, and none of the three needs one to be correct.

## Open questions

- Whether "admission on a measured result" should apply to every future skill.

## Benchmark result

Run on 2026-10-02 with `run_bench.py --backend claude-cli --trials 2 --second-judge
claude-opus-5-5`: nine evals, two trials each, on `claude-sonnet-5`, judged by
`claude-sonnet-5-5` and `claude-opus-5-5`.

| Round | Assertions met, skill | Without | First judge preferred the skill | Second judge |
|---|---|---|---|---|
| 1, as first written | 93% | 52% | 10 of 18 pairs (56%) | 11 of 18 (61%) |
| 2, after one revision | 90% | 52% | 15 of 18 (83%) | 16 of 18 (89%) |

Round 1 was not a clear preference. The judges' reasons named four faults, fixed for round 2:
`tech-debt-register` printed the table without saving a file and set every item to Watch
when nothing was measured; `security-questionnaire-response` returned its own report instead
of the customer's form filled in, and wrote a CSV with unquoted commas;
`pr-description-writer` made a wrong claim about what a test covered.

Read the round 2 number with two limits. The revision was made after reading the judges'
reasons on these same nine evals, so some of the gain is fitting to them; evals the skills
have not seen would settle it. And nine evals is a small sample: the first judge's 95%
interval is 61% to 100%.

Two losses remain and are left as they are: `pr-description-writer` still misreads the
rounding test in eval 2 on one trial, and `security-questionnaire-response` adds a review
notes file the RFP did not ask for.

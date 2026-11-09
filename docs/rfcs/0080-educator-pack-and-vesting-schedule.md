---
rfc: 0080
title: An educator pack, and vesting schedules for startup-legal
status: implemented
date: 2026-11-09
author: sananthanarayan
---

# RFC-0080: An educator pack, and vesting schedules for startup-legal

## Problem / use case

Two documents whose arithmetic and dates a capable agent reads fluently and gets wrong:

- **An exam paper and its mark scheme.** The cover says 50 marks and the questions add up to
  41; an either/or pair is worth 12 and 10; Question 3 goes from (a) to (c); the scheme gives
  Question 7 twelve marks where the paper says ten, or states a total its own rows don't reach.
  Students and moderators find these.
- **A vesting schedule.** A start on the 31st, a cliff between two quarterly dates, rounding
  that runs ahead of the grant, a leaver counted to today instead of to their leaving date, a
  company buy-back window that has quietly closed, and an 83(b) deadline that lands on
  Thanksgiving.

No pack serves teachers. `startup-legal` (RFC-0078, RFC-0079) has contracts, cap tables and
leases; vesting is the founder's next question when someone leaves or a grant is signed.

## Fit check

- **Concrete artifact:** a fix list with a marks table and scheme mismatches; a dated vesting
  schedule with leaver, buy-back and 83(b) outcomes.
- **Portable:** plain folders; stdlib Python 3.9+ scripts that read only the files they are
  given, write only a path they are given, and contact no network.
- **Opinionated:** each script decides pass or fail; each skill leads with the answer, keeps
  the person's files untouched, and names at most two points for a lawyer or adviser.
- **Category:** a new pack, `educator`, with a new outcome, `set-a-fair-assessment`; one skill
  added to `startup-legal` and its outcome.

## Proposal

| Pack | Skill | Tier | Script |
|---|---|---|---|
| `educator` | `exam-paper-check` | standard | `exam_check.py`: reads the teacher's own paper and scheme (.md, .txt, .docx); part, question and paper totals with either/or choices; the scheme's own total; numbering; scheme against paper both ways; objective weighting; minutes per mark |
| `startup-legal` | `vesting-schedule` | standard | `vesting.py`: cliffs, month-end dates, whole shares that sum exactly, leavers with buy-back and exercise deadlines, single and double trigger, 83(b) deadline past weekends and US federal holidays |

The exam script reads the teacher's own files rather than a transcription, because
transcription is where a wrong total gets quietly corrected.

## Alternatives considered

- **Vesting inside `cap-table`.** Different question (who has earned what, by date) and a
  different moment (a leaver, a grant).
- **A general education pack with lesson planning.** Lesson plans are instructions alone, and
  instruction-only skills lose to the plain agent about two pairs in three.

## Measurement

Two held-out evals each, written blind; two trials on `claude-sonnet-5-5`; judges
`claude-sonnet-5-5` and `claude-opus-5-5`; `--allow-bash`. Both first drafts lost and were
revised once, with general rules only, then measured on two fresh blind evals each.

| Skill | Draft 1 (judges 1, 2, of 4) | Draft 2 | Checks met, draft 2: skill / plain |
|---|---|---|---|
| `exam-paper-check` | 1, 2 | 2, 3 | 93% / 86% |
| `vesting-schedule` | 1, 1 | 2, 2 | 85% / 80% |

- **`exam-paper-check` draft 1** found every mechanical fault the plain agent found, and lost on
  the questions: it called a square root to 2 decimal places "feasible" on a non-calculator
  paper, and missed a mark scheme whose rows didn't reach its stated total. Draft 2 works every
  calculation under the paper's conditions and checks the scheme's own total.
- **`vesting-schedule` draft 1** had every figure right, as did the plain agent, which answered
  more of what was asked. One trial also miscounted a month outside the script. Draft 2 runs
  every scenario as its own computation, answers each question in order, and gives the buy-back
  and exercise deadlines against today's date. It is admitted at the bar.

Checking the blind evals' figures against the script found one bug before measurement:
double-trigger acceleration was counted before its second trigger. It is fixed and tested.

## Decision

Implemented in 1.11.0: `exam-paper-check` in a new `educator` pack, and `vesting-schedule` in
`startup-legal`.

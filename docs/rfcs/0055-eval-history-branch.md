---
rfc: 0055
title: An eval-history branch the site draws its trend from
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0055: An eval-history branch the site draws its trend from

## Problem / use case

The evals workflow reports each run in the job summary and a 90-day artifact, and then the
result is gone. Nobody can see whether a skill's trigger accuracy is drifting, because no run
is kept next to the one before it. The acceptance assertions run only when someone presses the
button, so they are effectively never run.

## Fit check

A new generated artifact and a change to a workflow; golden rules hold.

- **Nothing is written to `main`.** `protect-main` stays the only route there.
- **The API key never shares a job with a token that can push.** One job runs the evals;
  a separate job does the push.
- **The branch holds counts only:**
  - no query text;
  - no model output;
  - no judge reasons;
  - nothing from a pull request.

## Proposal

- **`run_evals.py`:**
  - `--budget USD` is a hard stop. Each call's usage is priced at list price, and once the
    budget is spent no new call starts. Calls already in flight finish, so a run can end a
    few cents over.
  - `--summary FILE` writes the counts: per run, and per skill as passed out of total.
  - Assertion evals run in an order seeded by the month, so a run the budget cuts short
    covers a different part of the catalogue each month.
- **`evals.yml`:**
  - **Schedules:** the weekly schedule runs the trigger queries, as before. A new monthly
    schedule runs the assertions, with `--no-activation` and the budget in the repository
    variable `EVALS_MONTHLY_BUDGET` (default 20).
  - **History job:** a `history` job, with `contents: write` and no secret, appends the
    summary to the `eval-history` branch as `runs/<timestamp>-<run id>.json`. It checks the
    summary's keys first, and pushes only for scheduled runs or runs from `main`. The branch
    is append-only, never force-pushed. Like `plugins`, it is outside `protect-main`.
- **`pages.yml`** fetches `eval-history` into `.eval-history/` before building, anonymously and
  read-only. A missing branch is fine.
- **The *How skills are checked* page** gains *Week by week*:
  - a chart and a table of trigger accuracy over the last 12 weekly runs;
  - the skills whose routing changed since the run before, falls first;
  - the monthly assertion runs, with what each spent and how much is left for the next month.

  Until a run exists, the section says the workflow needs the secret. Runs over a subset of
  skills are marked `partial` and kept off the trend.

## Alternatives considered

- **Commit results to `main`.** A scheduled job would need to bypass the ruleset, or open a
  pull request every week for a person to merge.
- **Read the run artifacts at deploy time.** They expire after 90 days, which is too short for
  a trend, and reading them needs `actions: read` in the deploy job.
- **A hosted dashboard.** That is a new service and a new place data goes; the repo stays
  offline-first.

## Decision

Accepted and implemented in 0.16.33. The trend starts drawing once the repository has an
`ANTHROPIC_API_KEY` secret, which is the owner's decision.

---
rfc: 0065
title: context-graph 0.2 — code changed since each decision, a home in core, and two loops
status: implemented
date: 2026-10-22
author: sanjay-ananth
---

# RFC-0065: context-graph 0.2 — code changed since each decision, a home in core, and two loops

## Problem / use case

**A record can be consistent and still wrong.** context-graph 0.1 ([RFC-0063](0063-context-graph.md))
checks the records against each other and against which paths exist. It doesn't check whether the
code still does what a current decision says. The code changes under a decision one commit at a
time, by people who may never have read the record. Nobody edits the record, because nobody
decided anything new.

**The question people ask is "has the code drifted since we decided this, and who changed
it?".** The history answers the second half exactly. Only reading the changes answers the first.

**The decision graph is wanted before work starts, in two loops.**
- `modernize` (RFC-0057) replaces a legacy component. Its survey stage finds the boundary, but
  not the constraints someone recorded years ago, such as a retention period or an ordering
  guarantee. Those are what a rewrite drops.
- `design` (RFC-0028) ends with an ADR. It never reads the decisions already in force where the
  design lands, and it never checks that the new ADR's supersession is recorded on both sides.

## Fit check

No new skill. The script stays stdlib, and `git log` stays read-only. The new data is facts from
the history: commits, dates and authors. Whether they amount to drift is still the model's
judgement, made by reading the changes. The skill says a commit count is a reason to look, never a
finding.

## Proposal

**1. Code changed since each decision (`--git`).** For each current record that governs a path:
- **The commits** that changed those paths since the record's date, merges left out. A record with
  no date counts from when its file was first committed.
- **Who made them**, with counts, and how many cite the record.
- **When the record itself was last edited.**

The full report gains a table of these, most changed first. `--why` adds a "Changed since" line
under each current decision, `--record` lists the commits, and `--json` has a `drift` object per
record. That is additive under the 1.x promise (RFC-0064). SKILL.md says to start from the
changes that don't cite the record, newest first, and read each against the record's
requirements. Drift is reported with the requirement, the line and the commit. The people who
made the changes are named, because they are who to ask about what the record doesn't say.

**2. context-graph moves to the core pack.** A pack must ship every skill its loops run
(RFC-0033). `modernize` is in dev-team and the skill was in solution-architect. Three options were
weighed:
- making dev-team require solution-architect, which adds 12 skills to every dev-team install;
- naming the skill in the loop's text only, which the loop contract wouldn't enforce;
- moving the skill to core.

The owner chose core. Developers, architects and on-call engineers all ask "why is it like
this?", so it is a cross-role skill, which is what core holds. Every pack installs core, so every
pack now gets it: one more skill per install. The skill's name, install command and page URL
don't change. Only its folder moves, to `packs/core/skills/context-graph/`.

**3. The loops.**
- **`modernize` 0.2.0:** the `survey` stage runs `codebase-tour`, then `context-graph`. Each
  constraint a current decision sets goes into `plan`. A behaviour of the old code that
  contradicts its decision is a question for the owner before `capture`, recorded as it is.
- **`design` 0.3.0:** `constrain` runs `context-graph` before `nfr-spec`. The design then names
  each decision in force where it lands, and which it keeps or supersedes. `record` runs it again
  after `adr-generator`, so every record the new ADR supersedes says so too.

Each loop gains an eval for the new step.

**4. Git history in eval fixtures.** A drift eval needs real history, and git can't commit a
nested `.git` folder. So a fixture may hold a `git-history.json`: a start commit and a list of
commits, each with a date, an author, a message and the files it writes or deletes.
`run_bench.py` replays it into a real repository before the run. The history is reviewable text in
the repo, and the same on every machine. A path that would write outside the fixture is
refused.

## Alternatives considered

- **A drift finding per record** ("12 commits since the decision"). Most commits implement or
  refine a decision, so it would be noise in the check's exit code. The table is a list of
  places to look. The finding is the model's, after reading.
- **Blame per line of governed code.** It's slower, and it answers "who wrote this line", not
  "what changed since we decided".
- **Shipping a `.git` bundle in the fixture.** It's binary, unreviewable in a pull request, and
  a supply-chain smell in a public repo.

## Decision

Accepted and implemented in 1.1.0.

**Re-measured on two fresh held-out evals, written blind from the new description** (16 and 17;
two trials; model claude-sonnet-5). Eval 16 carries git history, and asks whether a payments
service still follows its idempotency decision.
- **The judges preferred it in 3 and 2.5 of 4 pairs**, with a tie counting half.
- **It met 53% of their checks, against 47% for plain Claude Code.**
- **Its one loss was on length:** asked to "keep it short", it wrote more than the baseline.

**The first run found a gap in the harness, not the skill.** The judges saw the files a run left
behind, but not `.git`. So they read every commit an answer cited as invented. `run_bench.py` now
shows them the repository's history, marked as an input, and runs from before that change aren't
reused from the cache.

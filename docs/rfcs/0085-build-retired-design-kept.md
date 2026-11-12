---
rfc: 0085
title: build retired after a fourth measurement, design kept
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0085: build retired after a fourth measurement, design kept

## Problem / use case

[RFC-0084](0084-build-and-design-rebuilt.md) rebuilt `build` and `design`, and both beat their
own skills. Both still lost to the plain agent more often than they won. The judges named a side
effect of each rebuild:
- **build** restated things it hadn't done ("nothing was merged or pushed").
- **design** kept the risks it found out of the ADR altogether, and edited accepted records the
  house rules said to leave alone.

## Fit check

Two loop changes, one of them a retirement in the pattern of
[RFC-0074](0074-loops-measured-four-retired.md). No skill, gate or verdict vocabulary changes.
With `build` gone, the lifecycle's "Build it" stage is drawn from its skills in order, as
"Find the problem" and "Run it" already are.

## Proposal

**`build` 0.5.0:**
- the reply says what was done and found, never what wasn't;
- data loss is checked and mentioned only when the change touches data;
- it keeps to the answer, the evidence and the fix.

**`design` 0.5.0:**
- **Record the risks as open.** For a decision already made, the risks found go in the ADR
  where the house format puts consequences, marked open and not accepted by the decider. The
  reply names the biggest one first.
- **Read the house rules before touching a record.** Accepted ADRs get only the edits those
  rules allow. A partial supersession names the part replaced.
- **Deliver what was asked for.** Quality targets, threats and diagrams go inside the documents
  the person asked for, not into extra files.

## Measurement

Both loops ran on two fresh held-out evals each, written blind from their descriptions:
- `build`:
  - a triaged bug whose obvious fix misses a second case;
  - a colleague's change that is sound apart from one nit.
- `design`:
  - a fresh design where the person names the two documents they want;
  - recording a decision that replaces only part of an older ADR.

There were two trials on `claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`,
with `--allow-bash` ([`loops-1.16.0.json`](../benchmarks/loops-1.16.0.json), $7.28).

| Loop preferred to… (judges 1, 2) | Its own skills | Plain agent |
|---|---|---|
| `build` 0.5.0 | 25%, 25% | 12%, 50% |
| `design` 0.5.0 | 25%, 50% | 75%, 50% |

Checks met (loop / skills / plain): `build` 69% / 81% / 81%, `design` 91% / 84% / 84%. The
skills alone beat the plain agent in every `build` pair, and in 75% and 100% of `design`'s.

**`build` lost to its skills with both judges.**
- **The sound pull request:** both trials said "Not yet" over an input-type problem the change
  didn't have, which both judges called speculative. The skills alone said yes, with
  follow-ups.
- **The bug fix:** it was even with its skills, apart from one reply that pasted the gate
  script's output ("GATE: GREEN").

This is `build`'s fourth measurement:
1. neither ahead of nor behind its skills (RFC-0074);
2. behind them (RFC-0083);
3. ahead of them (RFC-0084);
4. behind them again, with both judges.

Each rebuild's rule fixed what it was written for and overshot on the next fresh evals.
- "Make the answer wait on data loss" became blocking a sound change on a made-up case.
- "Say who merges" became announcing what wasn't done.

Used in order without the loop, the skills already do what the loop's order was meant to add.

**`design` fixed both of round 3's problems.**
- **The record eval:** it won 3 of 4 pairs against its skills, and 4 of 4 against the plain
  agent with both judges. It put the risks in the ADR, labelled its suggested mitigations as
  not agreed, and amended only the part of the older ADR that changed.
- **The two-document eval:** it lost every pair to its skills. Its ADR bundled several decisions
  where the house rules allowed one per record, and it amended two accepted ADRs. One reply also
  named a file by an absolute path outside the working folder.

## Alternatives considered

- **A fifth round for `build`.** Each of the last three rounds traded one failure for another.
  Its skills run in order do the same work and beat the plain agent in every pair, so another
  rule would be fitted to the last set of evals rather than adding something the skills lack.
- **Retire `design` too.** It isn't behind its skills with both judges, and it beats the plain
  agent. The loss it has left is one house rule, which the next rebuild names.

## Decision

Implemented in 1.16.0.
- **`build` is retired.** Its folder is removed, and a `"kind": "loop"` record in
  `catalogue.json` says why and what to run instead: `user-story-splitter` or `bug-triage`
  (`codebase-tour` in an unfamiliar repository), then `feature-implement-loop`, then
  `pre-merge-review`, and the merge stays the person's. The lifecycle's "Build it" stage is
  drawn from those skills.
- **`design` 0.5.0 is kept.** The next rebuild, measured on fresh held-out evals, covers:
  - one decision per ADR when the house rules say so, with any further decisions as separate
    proposed records;
  - every file named by a path inside the working folder.

---
rfc: 0084
title: build and design rebuilt, and measured a third time
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0084: build and design rebuilt, and measured a third time

## Problem / use case

[RFC-0083](0083-loop-replies-in-plain-words.md) gave every loop plain-words replies. `build`
and `design` still lost to their own skills with both judges, and RFC-0083 named what they lost on.
- **build:**
  - it edited someone else's change when it should have reported the failed check;
  - it missed a data-loss edge case its skills caught.
- **design:** it wrote conditions into an ADR that the decider never set, and named files it
  hadn't written.
- **both:** they described a review panel the agent had seated itself.

RFC-0083 kept both loops for one more rebuild and measurement. A loop that lost a third time
would be retired.

## Fit check

A change to two `LOOP.md` files and their `loop.json` versions, with two fresh held-out evals
each. No skill, gate, verdict vocabulary or stage order changes.

## Proposal

Each rule is general, written from the judges' reasons, not from the evals.

**`build` 0.4.0:**
- **Whose change it is.** When the person asks whether someone else's change is safe to merge,
  the loop reviews it and reports. It leaves that change's files alone, and any fix goes back
  as a suggestion or a patch file. Only a request to build or fix makes the diff the agent's.
- **Data loss decides the answer.** Blank or missing keys, duplicates, truncation, encoding and
  rows dropped on error are checked beyond what the tests cover. "Safe to merge" waits on any
  such case that is still open.
- **A check is shown by its evidence or left out.** The reply quotes the command and its output.
  It never claims a pass without them, and never describes a review it shortened or skipped.
- **An approval is recorded, never acted on.** The person who approved merges.
- **A vague request gets written acceptance criteria first,** with the assumed ones marked.

**`design` 0.4.0:**
- **Record only what was decided.** When the request already holds the decision, the ADR
  records the decider's choice in their terms. The threats and gaps the loop found go in the
  reply as risks for them. When nobody has decided, the ADR stays `Proposed` and names who
  decides.
- **No narrated panel.** The review reaches the person as trade-offs and open risks. Reviewers,
  "dissent" and how the review was run are never mentioned.
- **The reply names only files that exist,** by the paths they were written to.
- **The reply leads with the person's decision or question,** before threats, quality targets
  and diagrams.

## Measurement

Both loops ran on two fresh held-out evals each, written blind from their descriptions. Each
loop got one eval that RFC-0083's analysis asked for:
- `build`: a vague requirement.
- `design`: recording a decision already made, where the work turns up a risk the decider
  should know.

There were two trials on `claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`,
with `--allow-bash` ([`loops-1.15.0.json`](../benchmarks/loops-1.15.0.json), $7.92).

| Loop preferred to… (judges 1, 2) | Round 2 (RFC-0083) | Round 3 (this RFC) |
|---|---|---|
| `build` over its own skills | 0 and 1 of 4 | 62% and 88% |
| `design` over its own skills | 1 and 1 of 4 | 75% and 50% |
| `build` over the plain agent | — | 50% and 25% |
| `design` over the plain agent | — | 25% and 25% |

Ties count as half a pair. Checks met (loop / skills / plain): `build` 100% / 100% / 100%,
`design` 78% / 84% / 84%.

**Against their own skills, both rebuilds worked.** On the colleague's pull request, every
`build` reply found the defect, left the author's code untouched, and showed the run that proved
it. The judges preferred it to the skills for that evidence. `design`'s fresh design won all
four of its pairs against the skills with both judges. The decision held through a partial
outage where the other designs could admit a ticket twice.

**Against the plain agent, both lost more pairs than they won.** The judges' reasons point to
two side effects of the new rules:
- **build: rules restated as boilerplate.** Replies said nothing was merged or pushed in a
  folder that had no git, and closed with "no quiet data-loss cases" on a change with no data
  path. A rule about what not to do turned into a line saying it wasn't done.
- **design: risks taken out of the ADR altogether.** "Threats go in the reply, never into the
  ADR" over-corrected. The record eval's house rules want risks in the ADR's Consequences.
  Both judges preferred an ADR that listed them there as open and unaccepted to one that left
  them out. The same loop runs also edited accepted ADRs that the house rules said not to
  touch. One of them marked a record fully superseded when part of it still governed.

## Alternatives considered

- **Retire both anyway, since they lose to the plain agent.** The bar RFC-0074 set is the
  loop against its own skills, because that is the choice a person installing the pack makes.
  Both now clear it, so retiring them would move the bar after the measurement.
- **Fix the two side effects now and publish them.** The fixes come from the judges' reasons,
  but publishing them unmeasured would break the rule that every revision is measured on fresh
  blind evals. They are the next round's work.

## Decision

Implemented in 1.15.0. `build` 0.4.0 and `design` 0.4.0 are kept: neither loses to its own
skills with either judge. The next rebuild, measured on fresh held-out evals against the
plain agent as well as the skills, covers:
- **build:** what wasn't done is never restated. Say what was done, and mention a data-loss
  check only when the change touches data;
- **design:** an ADR for a decision already made lists the risks found as open and unaccepted
  wherever the house format puts consequences. They are never written as the decider's
  conditions;
- **design:** accepted records are never edited beyond what the house rules allow. A record
  that still partly governs is marked as partly superseded.

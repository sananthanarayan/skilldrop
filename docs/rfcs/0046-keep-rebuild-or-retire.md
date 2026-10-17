---
rfc: 0046
title: Keep, rebuild or retire the twelve skills that lost on held-out evals
status: accepted
date: 2026-10-17
author: sananthanarayan
---

# RFC-0046: Keep, rebuild or retire the twelve skills that lost on held-out evals

## Problem / use case

Twelve skills were revised twice against a blind judge's reasons. Both revisions improved
the evals they were written against and neither carried over to evals the skills had never
seen ([what the benchmark showed](../../guides/explanation/what-the-benchmark-showed.md)).
The roadmap's next step was to stop editing them and ask one question of each: **what rule
does this skill add that the plain agent breaks?** A skill with such a rule is worth
rebuilding around it. A skill that only adds a format is a candidate for retirement, because
a capable model produces the format unprompted when the request calls for it.

This RFC answers that question for all twelve and proposes what to do with each. It also
proposes how a skill leaves the catalogue. The CLI has no way to say a skill was retired: an
installed copy just stops showing in `outdated`, and `update` reports "skill gone from it".

## Fit check

Structural change. It touches golden rule 2 (paths stay where they are; a retired skill's
folder is deleted, not moved) and the `catalogue.json` schema. No skill invokes another, so
no rule 7 issue arises.

## Evidence

The released version of each skill, on its four held-out evals (ids 2 to 5). Each eval was
run twice and judged by both blind judges, giving 8 pairs per judge. An analyst read each
skill folder, then every verdict and reason and both arms' outputs, and counted how many of
the four evals had a plain-agent output that broke the candidate rule.

| Skill | Pairs won of 8 (judge 1, judge 2) | The rule it adds | Plain agent broke it | Verdict |
|---|---|---|---|---|
| `tool-use-schema-writer` | 5, 5 | The schema says only what the source enforces: the code over the comment, the API's cap over the policy. Open questions stay out of the description the model reads | 4 of 4 | **Keep**, trimmed |
| `release-notes` | 3, 3 | Nothing in the notes that the log or the user didn't say. A vague change is written only as far as described | 3 of 4 | **Rebuild** |
| `postmortem-generator` | 3, 2 | No person is named as the cause, even when the user's own message names them | 2 of 4 | **Rebuild** |
| `design-doc` | 2, 3 | A number the sources say nobody measured stays unknown, with how to measure it | 2 of 4 | **Rebuild** |
| `ai-usage-policy` | 2, 1 | Every "don't" names the approved way to do the same task, or says none exists yet and who decides | 3 of 4 | **Rebuild** |
| `source-synthesis` | 2, 0 | Nothing beyond the supplied material unless it is marked as not from it; a source that repeats another counts once | 3 of 4 | **Rebuild** |
| `guide-builder` | 5, 3 | The guide holds only what the notes say, inferences marked; open questions go in the reply, never the document | 3 of 4 | **Rebuild** |
| `devils-advocate` | 3, 3 | A green test run is not evidence until you say why it would have passed with the bug in it | 3 of 4 | **Rebuild** |
| `tech-comparison-matrix` | 2, 3 | None, format only. The weighted matrix caused arithmetic errors in 4 of 8 runs | | **Retire** |
| `db-schema-design` | 5, 2 | None, format only. The plain agent got money types, time zones and constraints right in every eval; skill assertions 71% against 73% | | **Retire** |
| `metric-definition` | 2, 1 | None, format only. The plain agent did everything the skill teaches, unprompted | | **Retire** |
| `contribution-wizard` | 1, 3 | None. Its format is skilldrop's own and is out of date (`evals/cases.json`); it imposed that layout on an unrelated repo | | **Retire** |

Eight pairs per judge is a small sample. The verdicts rest on whether the rule appears in
the outputs, not on the win count alone. One analyst also flagged a capture doubt in
`contribution-wizard` evals 2 and 4 (files the plain agent said it wrote were not in the
captured workspace). That can only weaken the skill's case.

The losses among the rebuild seven have the same cause. The rule is real, but it sits under
a fixed template, and the template causes the loss. It overbuilds a "half a page" or "just
the table" request. It fills slots with invented owners, dates and severities. It leaks its
working into the deliverable: `[missing]` rows, commit ranges in customer notes, pointers to
the skill's own checker.

## Proposal

**1. Keep `tool-use-schema-writer`, with one trim.** The Python usage snippet becomes
opt-in. As written, it contradicts the skill's own "no usage example unless asked", and it
leaked once. `packs/api-builder/pack.json` and the api-builder how-to stop promising it.

**2. Retire four skills:** `tech-comparison-matrix`, `db-schema-design`,
`metric-definition`, `contribution-wizard`. No loop runs any of them. Each one's
`related`, `handoff` and "When NOT to use" references in other skills are removed; the
analysts' lists are the checklist. `AGENTS.md` loses two worked examples that name them, and
`eval-harness-generator`'s claim that `contribution-wizard` "calls" it goes, because a skill
never calls a skill. The `define-and-trust-the-numbers` outcome and the data-analytics
journey are re-sequenced without `metric-definition`.

**3. A retired skill says so.** `catalogue.json` gains a `retired` map:

```json
"retired": {
  "db-schema-design": { "in": "0.16.13", "why": "The agent without it did as well on evals it was never revised against." }
}
```

- `outdated`, `update` and `doctor` name an installed skill found there, with `why` and the
  `uninstall` command. Nothing is deleted on the user's behalf.
- `install` of a retired name fails with the same line.
- `validate.py` checks that a retired name has no folder and that nothing references it.
- The site lists retired skills on the evals page. The benchmark data stays in git history.

**4. Rebuild seven skills around their rule,** one at a time, with the RFC-0041 admission
bar:

- The rule goes first.
- The skill writes in the user's own format and length.
- The fixed template, the in-document tags and the self-referencing steps are deleted.

Evals 2 to 5 have now been read closely, so they no longer count as unseen. Each rebuild is
measured on two new evals (ids 6 and 7), written by an agent that sees only the skill's
description. Each eval runs before and after, 2 trials, both judges. A rebuild ships only if
both judges prefer it in at least half the pairs on the new evals. A rebuild that misses the
bar is retired under (3), not revised again.

These refusals survive every rebuild, whatever a judge prefers:

- `postmortem-generator`: names no SLA credit and makes no cloud-blip "root cause" for an
  exec.
- `ai-usage-policy`: does not repeat a vendor's unverified data promises.
- `source-synthesis`: does not synthesise from titles or memory.
- `guide-builder`: does not document an endpoint the notes lack.
- `devils-advocate`: invents no row counts or false findings.

`devils-advocate` is rebuilt together with `agents/devils-advocate.md`, which already states
its rule.

Order: `source-synthesis` first (lowest score, and the research pack has nothing between
plan and ranking without it), then `release-notes` and `postmortem-generator`, whose loops
(`release`, `operate`) depend on them.

## Alternatives considered

- **Retire all eleven that aren't clearly winning.** This would throw away seven rules the
  plain agent demonstrably breaks. Those rules are what made the career pack and RFC-0041
  win on held-out evals.
- **A third round of edits from the judges' reasons.** Two rounds have shown it does not
  carry over.
- **Delete the folders with no `retired` record.** Users with an installed copy would never
  learn why it stopped updating.

## Decision

Accepted by the maintainer on 2026-10-17 as proposed, with one change to (3): `instead` is
omitted rather than set to `null`, because none of the four has a successor. Parts (1) to (3)
shipped in 0.16.13. The site lists retired skills on the evals page. (4) runs one skill at a
time from 0.16.14, starting with `source-synthesis`.

### Rebuild results

| Skill | Release | New evals | Before (judge 1, judge 2) | After | Cost per skill run, before → after |
|---|---|---|---|---|---|
| `source-synthesis` | 0.16.14 | 6, 7 | 1, 0 of 4 pairs | 3, 3 of 4 | $0.20 → $0.09 |
| `release-notes` | 0.16.15 | 6, 7 | 3, 3 of 4 pairs | 4, 4 of 4 | $0.08 → $0.06 |
| `postmortem-generator` | 0.16.16 | 6, 7 | 2, 3 of 4 pairs | 2, 3 of 4 | $0.26 → $0.11 |
| `design-doc` | not shipped | 6, 7 | 2, 2 of 4 pairs | 2, 2 of 4 | $0.10 → $0.08 |
| `ai-usage-policy` | 0.16.17 | 6, 7 | 0, 1 of 4 pairs | 3, 2 of 4 | $0.09 → $0.10 |

`source-synthesis`: both eval 6 wins came from adding up a source's own line items, which
showed that its stated total was wrong. The eval 7 loss and the judges' notes on the eval 7
win name reasoning slips that the rule does not prevent: an inference that two nights weren't
full, and calling 150 "not higher" than 110. One caveat on independence: the rebuild was written
after the eval writer's summary of eval 6 had been read, so its traps were known. No example
in the skill comes from either new eval, and the sum check had already been recommended from
evals 2 to 5. Evals 6 and 7 are now tuned for this skill; the next measure needs evals 8 and 9.

`release-notes`: the eval writer reported only each eval's topic, so the rebuild was written
without knowing the traps. Its prompt did name the kinds of trap to plant, chosen from the
evals 2 to 5 verdict. The released skill already cleared the bar on these evals (most of its
losses on evals 2 to 5 were working notes in customer text), so the rebuild had to beat the released version, not just reach half. It did. All
four wins name the action-first ordering, accurate counts or leaving out unconfirmed claims.
Eval 1's assertions, which checked the old format (range header, two artifacts, a hash on
every line), now check the rule instead.

`postmortem-generator`: shipped on the bar, not on a gain. Blind preference did not move, the
skill met slightly more of its own checks, and a run costs less than half as much. It won all
four pairs on the rich eval, where the judges named it staying blameless, saying a customer
noticed before monitoring, and inventing no owners. It lost three of four on the short email
for a three-person shop, for the reasons the rebuild was meant to remove: longer than asked, a
file nobody requested, and a postmortem-style opening. The short, small-audience case is
where this skill still loses. Two rules came out of the draft before it was installed. They
answered trap types that had been written into the eval writer's brief (conflicting
timestamps, a confident guess in chat) rather than lessons from evals 2 to 5.

`design-doc`: the rebuild was not shipped and the released skill stays. On the new evals the
released version already sat at even, and the rebuild matched it with both judges, cost a
fifth less, and met fewer of its own checks on the one-pager. Both versions lost for the same
reasons: details invented for a pilot plan, and a one-pager that ran past a page. Reaching the
bar without beating what is released is not a reason to change it. The two new evals stay.
This eval writer was given example trap types and chose its own, and reported only file paths.

`ai-usage-policy`: the judges credited a policy with no blanks, a workaround for each
restriction, and a no-blame reporting step. The loss on the rich eval softened an outright
ban the board had decided into "needs sign-off": the skill did not hold to a decision the
input had already made. In one run the skill named the account holder as the
staff contact, guessed from the signed-in email the benchmark session can see. The same habit
showed in `design-doc` (an email as author) on evals 2 to 5. It is a habit across skills, not
one to patch in this one after measuring it.

One harness fix came out of this round: `run_bench.py` decided which model had answered by
the most output tokens, so a short judge verdict could be credited to a side call on a smaller
model and rejected as served by the wrong one. It now accepts the requested model when that
model produced output. This affected only rejected runs, never a counted one.

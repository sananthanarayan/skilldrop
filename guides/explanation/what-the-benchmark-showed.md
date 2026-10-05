---
title: What the benchmark showed
summary: Five days of measuring skills against the agent without them - a large gain on the skills' own checks, no blind preference at first, a gain that did not survive new evals, and what the skills that do win have in common.
kind: explanation
---

# What the benchmark showed

Between 1 and 5 October 2026 every skill in this catalogue was run against the same agent
without it. This page is the account of what that showed, including the parts that do not
flatter the skills. The method is in [RFC-0040](../../docs/rfcs/0040-skill-benchmark.md) and
the commands are in [Benchmark skills against the agent without them](../how-to/benchmark-skills.md).

## The short version

- Skills meet far more of their own checks than plain Claude Code does. That number is
  real, and it mostly measures whether the output follows the skill's format.
- A blind judge, shown both results and no checklist, at first had no preference.
- Revising skills against the judge's reasons raised the preference on the evals they were
  revised against. On new evals for 12 of those skills, the judges preferred the plain
  agent in about 7 pairs out of 10.
- The skills that win on evals they have never seen share one trait: they add a rule the
  plain agent does not follow on its own, and do not add a format.

## Two measures that disagreed

Each eval runs twice as a full agent session in an empty sandbox, once with the skill and
once without. Two things are measured. A judge marks each output against the eval's
assertions without knowing which arm wrote it. A second judgement shows the request and both
outputs in shuffled order, with no assertions and no skill text, and asks which serves the
request better.

The first run, 122 evals on the standard tier, gave:

| Measure | With the skill | Without | |
|---|---|---|---|
| Assertions met | 68% | 24% | +45 points (95% interval 39 to 50) |
| Preferred blind | 52% | | interval 43% to 61%: no preference |

The skill's author wrote the assertions, so the first row partly says "the skill does what
the skill says". The second row says a reader with no checklist could not tell which result
was better.

## Why the judge was not persuaded

The judge gives a reason with every verdict. Across the losses four recurred:

1. **Stopping instead of delivering.** Skills replied `BLOCKED` and asked for input where
   the plain agent stated an assumption and did the work.
2. **Machinery in the output.** `[missing]` rows, "non-interactive run", the skill's own
   section names, references to sibling skills.
3. **A fixed structure on a small request.** A full template in answer to a short question.
4. **Invented specifics** used to fill the template.

## What moved it and what did not

| Step | What changed | Blind preference |
|---|---|---|
| Two anti-pattern bullets added to 29 skills | Told skills not to over-block or show machinery | 31% → 35% on those skills (+4, interval −5 to +13): nothing |
| A second judge added (`claude-opus-5-5`) | Checked the first judge was not the problem | The two agreed on 74% of decided pairs and gave the same catalogue-wide number |
| Three new skills written to the lessons, three evals each | Admission on a measured result ([RFC-0041](../../docs/rfcs/0041-three-measured-skills.md)) | 56% and 61%, then 83% and 89% after one revision |
| Four rules placed above the steps in 31 skills | Answer first; use only what was given; deliver from what you have; write for someone who never heard of the skill | 17% and 20% → 35% and 37% on those skills |
| Whole catalogue after that, 131 evals | | 61% and 63%, both intervals above even |

Two cautions came out of the same runs. The winner of a single pair flipped between two
identical trials in 15 of 52 evals, so a per-eval result means little and nothing is compared
on fewer than two trials. And the 31 skills were picked because they had lost: an eval a
skill lost scores about 17% when simply rerun, and scored 28% after the edit, so the real
gain was nearer 11 points than 17.

## The held-out test

A skill revised after reading the judge's reasons on one eval may have learned that eval. To
find out, 12 of the 31 revised skills each got two new evals, written without touching the
skill: one with rich input and planted traps (two sources that disagree, a number that does
not add up, a request the data cannot support), one with thin, messy input. Each ran twice,
with both judges. The skills were not edited afterwards.

| 12 revised skills | Evals | Pairs won, first judge | Second judge | Assertions met, skill | Without |
|---|---|---|---|---|---|
| The eval each was revised against | 12 | 11 of 24 (46%) | 9 of 24 (42%) | 59% | 24% |
| New evals | 24 | 14 of 48 (29%, interval 17 to 42) | 14 of 48 (29%, 17 to 44) | 84% | 71% |

On evals they had not seen, both judges preferred plain Claude Code in about 7 pairs of 10.
The two judges agreed on 40 of 48 pairs. The gap in assertions also shrank, from 36 points
to 13: on checks written by someone other than the skill's author, the plain agent meets
most of them. The skill arm wrote two thirds more (7,800 output tokens a run against
4,700) and cost half as much again ($0.16 against $0.10).

The reasons were the third and second from the list above, still. A "nothing fancy" write-up
for a five-person team came back as a template with empty rows. Customer release notes
carried the commit range. A casual "what tables do I need" got access-pattern tables. Longer
outputs also had more room for an error, and the judges found some.

Read this result with its limits. The 12 come from the 31 weakest skills, so it says nothing
about the other 68. Each skill has four held-out pairs, so only the total carries weight. The
new evals were written by an agent told to plant traps, which favours care over structure.

## What the winners have in common

The same week, a pack for job applications was built and measured the same way
([RFC-0042](../../docs/rfcs/0042-career-pack.md)). Its three skills were revised against
their own 13 evals, so they got the same test: six new evals about two new people, run once,
no edits after. The judges preferred the skills in 10 and 11 of 12 pairs.

| | Held-out pairs won, first judge | Second judge |
|---|---|---|
| 12 revised skills from the catalogue | 14 of 48 | 14 of 48 |
| 3 job-application skills | 10 of 12 | 11 of 12 |

Twelve pairs is a small sample, and one author wrote both the skills and their evals. With
that said, the difference in kind is plain. The job-application skills, like the three from
RFC-0041, are each built on one rule the plain agent does not keep by itself: nothing goes in
the document that the person did not supply; no evidence, no answer. Their format is whatever
the user's own document already was. The skills that lost are mostly a structure: sections,
tables and tags that a capable model can produce unprompted when the request calls for them,
and that get in the way when it does not.

[The fabrication comparison](resume-fabrication-comparison.md) shows what such a rule buys
in one case.

## A second revision, measured before and after

The obvious response to the held-out test was to fix what the judges named. The same 12
skills were given five more rules above their steps: fit the size the user asked for; keep
notes and open questions out of the deliverable; save a document as one file and nothing
else; give a worked estimate when asked for a figure the input does not settle; check
everything computed or written to be run. Each also got a line of its own from its judges'
reasons.

This time the test was set up first. Each skill got two more evals, written by an agent that
read only the skill's one-line description. They were run against the skills as released,
and only the totals were read. Then the revision was applied and the same evals run again.

| 12 skills | Before | After the revision |
|---|---|---|
| Evals 1 to 3, which the revision was written against | 25 and 23 of 72 pairs | 40 and 34 of 72 |
| Evals 4 and 5, never seen | 21 and 15 of 48 (44% and 31%) | 24 and 17 of 48 (51% and 36%) |

Each cell gives the first judge, then the second. On the evals it was written against, the
revision moved the skills from losing two pairs in three to about even. On the evals it had
never seen it moved three pairs with one judge and two with the other, which is inside the
noise; the intervals before and after overlap almost entirely.

The rules did change behaviour. The skills' replies became about 40% shorter and matched the
plain agent's for length. It did not help, because length was only one complaint. Across the
53 verdicts that still went against the skills on the fresh evals, the judges' reasons were
spread over unsupported detail, errors and contradictions, and over-built files, with no one
fault in the lead. A skill run also cost more after the revision, $0.16 against $0.14, and
the plain agent costs $0.10.

The revision was not released. The 24 new evals were kept.

This is the first finding again, under a cleaner design: for these skills, edits made from a
judge's reasons improve the evals the reasons came from and little else.

## Where the catalogue stands

Across all 209 evals, new ones included, the two judges prefer the skill's result in 61%
(interval 55 to 68) and 61% (55 to 67) of pairs. Skills meet 75% of their checks and the
plain agent 44%. That headline mixes skills that clearly help with skills that clearly do
not, and the held-out test says the second group is larger than the tuned numbers suggested.

## What follows from it

- **Held-out evals for every skill**, written by someone other than the skill's author, and
  the published number split into evals a skill was revised against and evals it was not.
- **Size the output to the request.** The losing skills need a rule that a short ask gets a
  short answer in the user's own format, before any template applies.
- **Ask of each skill what rule it adds.** A skill with no rule the plain agent breaks is a
  candidate for cutting, not for another round of edits. Two rounds of edits to the same 12
  skills have now failed to carry over, so the next step for them is that question.
- **Do not tune on the judge alone.** Deliberate refusals stay, such as declining to rank
  teams from delivery metrics, even where a judge prefers the answer that complies.

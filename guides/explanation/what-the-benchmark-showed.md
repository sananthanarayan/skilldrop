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
- Across the catalogue in late October, on the 176 held-out evals that no revision or
  admission was based on, the judges had no preference between the skill and the plain
  agent (49% and 48%). On the newer models it did worse: with the standard tier on Sonnet 5.5,
  the judges preferred the plain agent in about two pairs of three on those evals.

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
skill lost scores about 17% when rerun unchanged, and scored 28% after the edit, so the real
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

The published run is from 23 October 2026: all 520 evals of the 117 skills on the standard
tier, one trial, two judges. Skills meet 73% of their checks and the plain agent 53%. The two
judges prefer the skill's result in 62% (interval 58 to 67) and 61% (57 to 65) of pairs.

That headline now splits by who wrote the eval, which is the number this page has been
asking for since the held-out test:

| Evals | Count | Assertions met, skill | Without | Preferred blind, judge 1 | Judge 2 |
|---|---|---|---|---|---|
| Written by the skill's author | 212 | 72% | 35% | 69% (62 to 75) | 68% (62 to 74) |
| Written without seeing the skill | 308 | 74% | 66% | 58% (52 to 63) | 56% (50 to 61) |

On the authors' evals the skills win clearly, and part of that is fitted: many of those evals
were revised against. The gap on the checks shrinks from 37 points to 8 on the held-out
evals, as it did in the first held-out test: on checks written by someone other than the
author, the plain agent meets most of them.

"Written without seeing the skill" is not the same as "never decided on", though. The writer
of a held-out eval never read the skill, but the skill's author may have read the judges'
reasons on that eval afterwards and revised the skill, and a new skill is admitted only if it
wins on its held-out evals. Git history separates the 308 into three groups:

| Held-out evals | Count | Assertions met, skill | Without | Preferred blind, judge 1 | Judge 2 |
|---|---|---|---|---|---|
| Skill's instructions changed after the eval was added | 78 (23 skills) | 75% | 63% | 64% (54 to 74) | 64% (54 to 74) |
| Added since 18 October for skills admitted on them | 54 (18 skills) | 63% | 47% | 78% (67 to 89) | 72% (61 to 83) |
| Written by 18 October, skill unchanged since | 176 (88 skills) | 77% | 72% | 49% (42 to 57) | 48% (40 to 55) |

The first two groups are fitted or selected: a revision was written after reading their
verdicts, or a skill that lost on them was not admitted. Only the third was not the basis of
any decision, and on it the judges have no preference between the skill and the plain agent.
That is the same result the first held-out test found for 12 skills, now across 88 of them.
The 58% and 56% above are real, but they are not a measure of a skill on a request it was not
shaped around; the last row is.

A skill counts as changed if anything other than its evals, scripts, tests or manifest
changed in a commit after the eval's; script fixes are left out because they don't come from
reading verdicts. The rule cannot see a draft revised before its evals were committed, which
is how admission works, so the middle row is counted separately.

Per skill the picture is mixed, as it was. On their held-out pairs, 49 skills sit above
even, 36 below, and 32 at even. Each skill has two to four held-out pairs from one trial, so a
single skill's row is an anecdote and the totals are the result.

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

## What was done about it

[RFC-0046](../../docs/rfcs/0046-keep-rebuild-or-retire.md) asked that question of all 12
skills, using their four held-out evals. One skill already wins, and keeps its rule: a tool
definition says only what the source enforces. Seven have a rule the plain agent broke in
two or three of their four evals, buried under a template that cost them most of their
losses. They are being rebuilt with the rule first, and each one ships only if both judges
prefer it in at least half the pairs on two new evals. Four added only a format and were
retired in 0.16.13. The evals page lists them, with the reason for each.

## The three tiers

Until 18 October 2026 the benchmark had run only on the standard tier. That day the 224
held-out evals ran once each on the light tier (`claude-haiku-5-5`) and the heavy tier
(`claude-opus-5-5`), with the same two judges; the summary is in
[`docs/benchmarks/tiers.json`](../../docs/benchmarks/tiers.json). The standard tier
(`claude-sonnet-5`) ran on the same 224 evals five days later, as part of the full catalogue
run in [Where the catalogue stands](#where-the-catalogue-stands). Its row below is those 224
evals taken out of that run.

| Tier | Assertions met, skill | Without | Preferred blind, judge 1 | Judge 2 | $ per run, skill |
|---|---|---|---|---|---|
| light `claude-haiku-5-5` | 83% | 80% | 41% (35 to 48) | 48% (41 to 54) | $0.007 |
| standard `claude-sonnet-5` | 78% | 72% | 51% (45 to 58) | 50% (44 to 57) | $0.13 |
| heavy `claude-opus-5-5` | 85% | 83% | 31% (25 to 37) | 31% (25 to 37) | $0.19 |

- **On evals they were not written against, the skills do not beat the plain agent on any
  tier.** The lift on the checks is 3 to 6 points. On standard the judges are at even; on
  light the plain agent wins slightly more pairs, and on heavy both judges preferred plain
  Opus 5.5 in about 7 pairs of 10.
- **The standard tier scores below the light one, with the skill and without it.** Haiku 5.5
  meets 83% of the checks with the skill and Sonnet 5 78%; without the skill, 80% against 72%.
  Light came out more than 5 points ahead of standard for 53 of 97 skills and behind it for
  19. A gap that shows up in the plain agent too belongs to the model, not the skill: the
  routing table maps light and heavy to the 5.5 generation and standard to the one before it,
  at the same list price as its successor.
- **For most skills a cheaper model is enough, on the checks.** Taking the cheapest tier
  within 5 points of the best, light is enough for 56 of 97 skills, standard for 15 and heavy
  for 26. Of the 13 skills assigned heavy, light is enough for eight
  (`accessibility-audit`, `devils-advocate`, `doc-critique`, `dpia`, `skill-review`,
  `sql-review`, `strategy-analysis`, `terraform-plan-review`), standard for two
  (`agent-threat-model`, `council-review`), and three need heavy (`business-case`,
  `hypothesis-comparison`, `threat-model`). Heavy led standard by 15 points or more on 25
  skills, among them `adr-generator`, `bug-triage`, `prd-draft`, `pre-merge-review` and
  `subagent-design`, which is the weak standard model showing again.
- **No tier was changed.** Each row is two evals and one trial, and the standard tier ran on
  a different day and a slightly different catalogue: 29 of the 97 skills changed in between,
  almost all in their scripts and manifests. `SKILL.md` changed only in `api-contract-draft`
  and `file-to-markdown`, and five others had an example or template edited. Left out, the standard row barely moves (52%
  and 51% on the 152 evals of unchanged skills). The routing rule that a heavy skill is never
  routed below heavy is what the eight light rows question. Before any per-skill tier moved,
  the model behind the standard tier had to be settled; see the next section.

Claude Code had no price for Haiku 5.5 when this ran, so its runs are priced from the
runner's own table at $0.10 and $0.50 per million tokens. Light runs wrote more: 7,015 output
tokens with the skill and 4,099 without. Evals 4 and 5 of `role-shortlist` ran on the version
before 0.16.21.

### Standard on Sonnet 5.5

On 25 October the routing table's standard tier moved to `claude-sonnet-5-5`, the same
generation as light and heavy, at the same list price as Sonnet 5. All 308 held-out evals
then ran on it with the same two judges: one trial each, and a second trial on the first 118
before a plan usage limit stopped the run. The summary is in
[`docs/benchmarks/standard-sonnet-5-5.json`](../../docs/benchmarks/standard-sonnet-5-5.json).
On the same 224 evals as the table above:

| Tier | Assertions met, skill | Without | Preferred blind, judge 1 | Judge 2 | $ per run, skill |
|---|---|---|---|---|---|
| standard `claude-sonnet-5-5` | 85% | 83% | 36% (30 to 41) | 39% (33 to 45) | $0.07 |

- **The gap on the checks is gone.** With the skill, Sonnet 5.5 meets 85% of the checks,
  level with Opus 5.5 and above Haiku 5.5; without it, 83%, against Sonnet 5's 72%. It also
  costs less per run than Sonnet 5 did, $0.07 against $0.13 with the skill, because it
  writes less: 3,273 output tokens a run against 5,442.
- **Blind, the plain agent is now preferred on standard as well.** Both intervals on the
  224 sit below even. Across all 308 held-out evals the skill wins 40% (36 to 45) and 43%
  (38 to 48) of pairs. By the groups in [Where the catalogue stands](#where-the-catalogue-stands):

  | Held-out evals, on Sonnet 5.5 | Count | Preferred blind, judge 1 | Judge 2 |
  |---|---|---|---|
  | Skill's instructions changed after the eval was added | 78 | 50% (39 to 61) | 49% (38 to 60) |
  | Added since 18 October for skills admitted on them | 54 | 54% (42 to 66) | 61% (50 to 72) |
  | Written by 18 October, skill unchanged since | 176 | 32% (26 to 39) | 35% (28 to 41) |

  On the evals nothing was decided on, the judges preferred plain Sonnet 5.5 in about two
  pairs of three. Even the fitted and selected groups only reach about even.
- **The stronger the plain agent, the less the skill is preferred.** Across the four models
  on these 224 evals, ordered by how many checks the plain agent meets: Sonnet 5 (72%), skill
  preferred in 51% and 50%; Haiku 5.5 (80%), 41% and 48%; Sonnet 5.5 (83%), 36% and 39%; Opus
  5.5 (83%), 31% and 31%. Four points are not a law, but the direction fits the judges'
  reasons in the earlier held-out tests, where most losses came from structure a capable
  model did not need. This run's reasons have not been read, so its clean evals stay unseen
  for the next decision.
- **With Sonnet 5.5 as standard, the routing check moves.** Taking the cheapest tier within
  5 points of the best, light is enough for 54 of 97 skills, standard for 25 and heavy for
  18. Of the 13 skills assigned heavy, light is enough for six, standard for five, and only
  `hypothesis-comparison` and `threat-model` need heavy.
- **No per-skill tier was changed.** The winner of a pair was the same in both trials for 80
  of the 118 evals that had two, so one trial is still weak evidence for a single skill. Light
  and heavy have one trial each, run a week earlier on the 0.16.21 catalogue. Their second
  trials come next.

### The scripts without the instructions

A skill that loses blind could be losing to its instructions while its scripts still help, or
adding nothing at all. On 27 October the 44 skills that ship scripts ran a third arm on their
132 held-out evals. It got the scripts and the data they read, and no SKILL.md, reference or
examples: only a generated list of the scripts ([RFC-0067](../../docs/rfcs/0067-scripts-without-instructions.md)).
The run used one trial on `claude-sonnet-5-5`, with the same two judges, and cost $106.54 at
list price. The summary is in
[`docs/benchmarks/tools-arm-sonnet-5-5.json`](../../docs/benchmarks/tools-arm-sonnet-5-5.json).

| | Skill | Scripts only | Plain agent |
|---|---|---|---|
| Assertions met | 80% | 76% | 71% |
| $ per run | $0.112 | $0.094 | $0.087 |

| Blind pair | Judge 1 | Judge 2 |
|---|---|---|
| Skill preferred to the plain agent | 45% (37 to 53) | 44% (36 to 52) |
| Scripts only preferred to the plain agent | 44% (36 to 52) | 44% (36 to 53) |
| Skill preferred to scripts only | 48% (40 to 57) | 46% (38 to 54) |

- **On the checks, each layer adds a little.** The scripts add about 5 points to the plain
  agent, and the instructions about 4 more.
- **Blind, no arm reliably beats another.** Every interval spans even, and the plain agent
  leans slightly ahead of both. Taken together, the instructions add no measurable preference
  over the scripts alone, at about 19% more per run.
- **Per skill, most results are open.** A reading needs every judge to agree, and most skills
  have two evals:
  - **32 skills are mixed.**
  - **8 read *the plain agent is preferred*:** `ai-usage-report`, `deck-builder`,
    `file-to-markdown`, `hypothesis-comparison`, `marketing-flyer`, `md-to-html`,
    `mermaid-render` and `risk-register`.
  - **3 read *the scripts carry it*:** `backlog-triage`, `figma-diagrams`, and
    `interactive-diagram`, narrowly, on 10 evals.
  - **1 reads *instructions help*:** `codebase-tour`.

  Several on the plain-preferred list are converters whose real output is a file, so check
  those rows against the outputs before reading them as the skill failing.
- **Nothing was decided on this.** It is one trial. The judges' reasons haven't been read, so
  the list of losing skills can be fixed before anyone looks at why. A second trial on the same
  evals is running.

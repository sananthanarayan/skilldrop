---
rfc: 0047
title: A shortlist of an employer's roles, measured on saved postings
status: accepted
date: 2026-10-18
author: sananthanarayan
---

# RFC-0047: A shortlist of an employer's roles, measured on saved postings

## Problem / use case

Someone looking for work finds an employer with forty openings, or a job board with a long
export, and asks the agent which roles to apply for. `job-fit-analysis` answers that well for
one posting at a time and is too heavy for forty. Asked about the list as a whole, a plain
agent ranks the roles from their titles and from what such jobs usually ask for. That ranking
looks the same as one built from the postings, and it is wrong exactly where it matters: the
title that fits needs a registration the person lacks, or the role is a night shift in
another city.

The roadmap held this skill back because the benchmark sandbox has no network, and a
careers page is a website. The way round it is the one the converters already use: the evals
carry the employer's pages as saved files. A careers page saved as files is also what many
people will hand the agent anyway.

## Fit check

- **Concrete artifact:** a shortlist in the reply. Every role given is sorted into apply,
  maybe, skip, not read, or closed or duplicate, with one line of reason each.
- **Portable:** a plain `SKILL.md` folder, no script.
- **Opinionated:** a role is judged from its posting text or not at all; an unmet screening
  requirement takes a role out whatever else fits; one role is one role; every role given
  appears once.
- **Category:** the `career` pack, beside `job-fit-analysis`. The `apply-for-a-job` outcome
  gains it as its first step.

## Proposal

`role-shortlist` (standard tier; related: `job-fit-analysis`, `resume-tailor`; a hand-off to
`job-fit-analysis` for the first-choice role, with a fallback). Its rule: no posting read, no
verdict. Its bar: no role ranked unread; no role with an unmet screening requirement under
Apply; every role accounted for once; nothing credited that the person's material doesn't
show. It bans ranking from titles, guessing an unread posting, and match percentages.

`job-fit-analysis` now points to it for a long list of openings and keeps the two-or-three
case. The `apply` loop is unchanged. It starts from one posting, and a shortlist is how you
choose that posting, not a stage of applying.

**Admission** follows RFC-0041 and RFC-0042. The author writes three evals with fixtures and
a second writer, who never reads the skill, writes two held-out evals. The skill ships only
if both blind judges prefer it to plain Claude Code in at least half the held-out pairs over
2 trials.

## Alternatives considered

- **Extend `job-fit-analysis` to many postings.** That would keep one skill, but its output
  is a requirement-by-requirement table, and forty of those is not a shortlist. The two jobs
  have different outputs and different failure modes.
- **A loop stage that runs `job-fit-analysis` once per posting.** The cost grows with the
  number of postings, and no stage would catch the ranking-from-titles failure.
- **Wait for live network in the benchmark.** That would measure the skill against websites
  that change between runs, and saved pages measure the same behaviour reproducibly.

## Decision

Accepted with the roadmap item, and admitted in 0.16.20.

| Evals | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without |
|---|---|---|---|---|
| 1 to 3, by the author | 4 of 6 | 4 of 6 | 75% | 64% |
| 4 and 5, by a writer who never read the skill | 3 of 4 | 3 of 4 | 89% | 61% |

Two trials, two judges, `claude-sonnet-5`. The held-out pairs clear the bar of half from both
judges. The wins name the rule. A posting the skill couldn't read was listed as unread and
fetched next, where the plain agent guessed it was "likely the same role". A warehouse system
the posting required was not credited from a similar one on the CV. Several also preferred it
for writing to the person as "you", where the plain agent wrote "she".

It lost the thinnest case, six one-line blurbs and "just the top two", three times in four.
It printed empty "Not read" and "Closed or duplicate" groups, and it treated a degree the
blurb called preferred as a requirement. Step 5's fixed list of groups causes the first. The
second breaks step 3, which is about what an employer checks first, and a preferred item is
not that. Both are for the next revision, measured on new evals. The judges' reasons for
eval 5 have now been read, so it no longer counts as unseen.

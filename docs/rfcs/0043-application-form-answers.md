---
rfc: 0043
title: Career pack: source formats, evidence beyond the resume, and the application form
status: implemented
date: 2026-10-05
author: sananthanarayan
---

# RFC-0043: Career pack: source formats, evidence beyond the resume, and the application form

## Problem / use case

The `career` pack (RFC-0042) was built and measured on invented people with tidy Markdown
resumes. An end-to-end trial of the `apply` loop on the kind of input people actually have,
a two-page resume built from a Typst source, a posting given as a link and an online form
behind it, showed five things that none of the 19 evals could have.

1. **The best evidence was not on the resume.** The strongest answer to the posting was a
   project the resume did not mention. The skills allowed only "the resume and
   what the person told you" and had no step that asked.
2. **The resume was not text.** `resume-tailor` writes Markdown. The real work was finding
   the source file, editing a copy, building it and getting back to two pages, which took
   five builds. The skill said nothing about any of it.
3. **Lines were cut without the candidate seeing them.** Nine bullets went to hold the page
   count, reported only as "what changed". Adding one line afterwards meant another
   had to go.
4. **`claim_check.py` misread that input.** Unchanged names with an ampersand were listed as
   new, `\$2B` was read as a word, and layout lengths as figures.
5. **Nothing covered the application form.** It had required questions that mattered more
   than the letter, among them declarations that the content of a resume can bear on. Nothing
   in the pack said what to do with it.

## Fit check

For the new skill:

- **Concrete artifact:** an answer sheet in the form's own order.
- **Portable:** a plain `SKILL.md` folder, no script.
- **Opinionated:** every question is one of three kinds; a declaration, a preference or a
  private fact is never answered for the person; an honest answer that screens them out is
  named first and left honest.
- **Category:** `career`, and a fourth stage in the `apply` loop.

The revisions to existing skills need no RFC and are recorded here because they share a cause.

## Proposal

- **`application-form-answers`** (new; standard tier; related: `job-fit-analysis`,
  `resume-tailor`, `cover-letter`). Bar: every question appears once in the form's order; no
  declaration is answered for the person; every draft traces to the resume and fits its
  limit. Bans: ticking a declaration, answering to pass a screen, inventing the example a
  "tell us about a time" question asks for.
- **`resume-tailor`** revised: work in the resume's own format on a copy of its source, and
  build it when the tool is there; the page count is a budget, so an addition is paid for
  with a cut; the reply lists every line cut and every fact added from outside the resume;
  a posting given as a link is read in full or asked for, never reconstructed.
- **`job-fit-analysis`** revised: other files of the candidate's count as evidence, labelled
  as not on the resume; when a required item is not shown it asks once whether anything
  outside the resume covers it; no verdict on a posting it could not open.
- **`apply` loop** 0.2.0: a `form` stage after `letter`, and the final gate now shows the
  candidate four lists: not claimed, added from outside the resume, cut, and the form
  questions that are theirs alone.
- **`claim_check.py`** reads Typst and LaTeX escapes, names with an ampersand, and ignores
  layout lengths (shipped separately in `e31e191`).
- **Fixtures that look like that input.** A resume kept as Typst source with `&` in two
  names and an escaped dollar figure; a folder where the best evidence is in a LinkedIn
  summary and not the resume; a posting given only as a link that cannot be opened. Five
  application forms for the new skill, two of them held out.

## Alternatives considered

- **Fold the form into `cover-letter`.** Lost: a letter is prose the skill writes; a form is
  mostly questions it must refuse to answer. One skill cannot hold both rules cleanly.
- **A script that fills the form in a browser.** Out of scope and the wrong default: the
  candidate submits, the loop never does (RFC-0042).
- **A shortlist skill** that runs the fit check across an employer's whole board, for when
  one posting is a poor fit and the next question is what else that employer has open. Held
  back: it needs network access, which the benchmark sandbox does
  not allow, so it could not be admitted on a measured result.
- **Leave the cover letter's gap sentence as a choice.** Considered after the trial, where
  the skill stated a missing requirement outright. Left alone: the benchmark's judges
  preferred letters that name a gap plainly, and one trial is not evidence against that.

## Open questions

- Whether `resume-tailor` should ship a page-count helper for built PDFs.

## Benchmark result

Run on 2026-10-05 with `run_bench.py --backend claude-cli --trials 2 --second-judge
claude-opus-5-5`, on `claude-sonnet-5`, judged by `claude-sonnet-5-5` and `claude-opus-5-5`.
Pairs won by the skill, of pairs run; each cell gives the first judge, then the second.

| | Round 1 | Round 2, after one revision |
|---|---|---|
| `application-form-answers`, evals 1 to 3 | 4 and 5 of 6 | 6 and 6 of 6 |
| `application-form-answers`, evals 4 and 5 | 1 and 1 of 4 | 4 and 4 of 4 |
| `application-form-answers`, evals 6 and 7 (held out, run once) | not written yet | 4 and 3 of 4 |
| `resume-tailor`, 7 evals including the two new fixtures | 12 and 12 of 12 | 14 and 14 of 14 |
| `resume-tailor`, held out | 4 and 4 of 4 | 4 and 4 of 4 |
| `job-fit-analysis`, 5 evals including the two new fixtures | 6 and 9 of 10 | 8 and 5 of 10 |
| `job-fit-analysis`, held out | 4 and 4 of 4 | 4 and 4 of 4 |

`application-form-answers` was not preferred as first written. Its evals 4 and 5 were
written as held-out and it lost them, for reasons the judges named: asked to fill in the
form, it answered in chat while the plain agent filled in the file; on a form with no
numbers it invented its own, and they did not match; once it overlooked the posting file
and added an outcome the CV does not state. Those were fixed. Because that revision was made
after reading the judges on evals 4 and 5, they stopped counting as held-out, and two new
ones (6 and 7) were written before round 2 ran. The skill won 4 and 3 of those 4 pairs. Its
one loss there is a real fault, left in: it counted an internship that overlapped a
volunteer role twice, 23 months for 21.

`resume-tailor` won every pair with both judges, including the Typst resume and the folder
where the best evidence was off the resume.

`job-fit-analysis` is the weak one. The judges disagree about it: after two small fixes the
first judge moved from 6 to 8 of 10 and the second from 9 to 5. Rerun noise is part of that,
since a pair's winner flipped between two identical trials in 15 of 52 evals earlier in the
week ([what the benchmark showed](../../guides/explanation/what-the-benchmark-showed.md)). The
second judge's reasons are also real: a headline count that contradicted the table beneath it
in two runs, and marking so strict that a barista's customer-facing work was "not shown" for
a front-desk requirement. It still wins all its held-out pairs. It is left as it is, and it
is the next skill in this pack to work on.

On the link-only fixture, the plain agent twice remarked that the resume's name did not
match the signed-in account's email. Agent sessions run through a signed-in Claude Code
receive that address as context. It is a property of the benchmark's backend to keep in
mind: outputs in `bench-results/` can contain it, and the published summary holds no outputs.

**Follow-up, same day.** `job-fit-analysis` was revised once more for what the second judge
named. It now names the unmet requirements in its opening line and does not count them; it
marks a general ability, such as dealing with the public, as met by any job that plainly
involves it; and it may not advise rewording a partly met item so it reads as met. Run with
three trials: 13 and 11 of 15 pairs on its tuned evals, from 8 and 5 of 10, and 6 and 6 of 6
held out. Three of its four remaining losses with the first judge are on the link-only
fixture, where both answers are right.

Across the pack's 30 evals the skills meet 95% of their assertions and the plain agent 79%.
On evals the skills were never revised against, they won 14 and 14 of 16 pairs.

## Decision

Accepted 2026-10-05 and implemented the same day, released in 0.16.8.

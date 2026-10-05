---
rfc: 0042
title: A job applications pack, admitted on a fabrication measure
status: implemented
date: 2026-10-05
author: sananthanarayan
---

# RFC-0042: A job applications pack, admitted on a fabrication measure

## Problem / use case

Someone applying for a job asks an agent to tailor their resume and write a cover letter.
The agent is fluent at both, and that is the problem: it adds a tool the posting asked for,
turns a team of 4 into "teams of 8", gives a result a percentage, and opens the letter with
admiration nobody expressed. The person signs the document and is questioned on it at
interview. The catalogue has no skill for this, and it is the catalogue's first job where the
user is a person on their own account and not a team.

It also has to work for any occupation. A pack tuned to software resumes would be useless to
a nurse or a warehouse supervisor, and they are the larger audience.

## Fit check

- **Concrete artifact:** a fit analysis, a tailored resume file, a cover letter file.
- **Portable:** plain `SKILL.md` folders. Two carry one stdlib-only Python script.
- **Opinionated:** nothing enters a document that the person didn't supply; a similar tool is
  not the named tool; titles, dates and numbers are fixed; the verdict on fit is one of four
  phrases and never a percentage.
- **Category:** a new pack, `career`, with a new outcome, `apply-for-a-job`. No existing pack
  serves an individual, and three skills plus a loop is a pack by the bar RFC-0041 set when it
  declined a one-skill `proposals` pack.

## Proposal

- **`job-fit-analysis`** (standard; related: `resume-tailor`, `cover-letter`, `doc-critique`).
  Bar: every Met and Partly quotes the resume; screening requirements come first; `Not shown`
  and `Not met` are kept apart. Bans: a match percentage, cheerleading over an unmet
  requirement.
- **`resume-tailor`** (standard; related: `job-fit-analysis`, `cover-letter`, `doc-critique`).
  Bar: every employer, title, date and number matches the original; the file is sendable as
  written; what the resume cannot claim is reported. Bans: keyword stuffing, invented metrics.
- **`cover-letter`** (standard; related: `job-fit-analysis`, `resume-tailor`,
  `output-hygiene`). Bar: every claim about the person is theirs and every claim about the
  employer is in the posting; 200 to 350 words. Bans: invented enthusiasm, company facts from
  memory.
- **`apply`** loop: `fit` (gate G5, human: the candidate decides to apply) → `tailor` →
  `letter` → `confirm` (`output-hygiene`, then gate G6, human: the candidate confirms every
  line is true). Both gates are human because only the candidate knows what is true and what
  they want. The loop never submits an application.
- **`scripts/claim_check.py`**, shipped in `resume-tailor` and `cover-letter`. Given a draft,
  the person's own material and the posting, it lists figures and named things in the draft
  that the person's material doesn't contain, capitalised words that appear in the source but
  never together, and wording shared only with the posting. It reads text and cannot tell
  true from false; it says where to look. The file is duplicated across the two skills
  because a skill must work when copied alone (golden rule 7).
- **Any occupation.** The skills name no industry. The 19 evals use seven invented people
  with resumes (a ward nurse, a warehouse supervisor, a new graduate, a backend engineer, a
  teacher changing career, an accounts payable clerk and a sous chef) and two who give a few
  lines and no resume (a barista and a pharmacy counter assistant).
- **Admission on a measured result** (the RFC-0041 rule): three or more evals each with input
  files, two trials, two judges, recorded below whatever it shows. This pack adds a third
  measure, because its claim is specific: how often each arm puts something in the document
  that the person's material doesn't support.

## Alternatives considered

- **Do nothing.** Plain Claude Code writes a good-looking resume. The question the benchmark
  below answers is whether it writes a true one.
- **One `job-application` skill** doing all three jobs. Lost: the fit check is worth running
  alone, across several postings, before any writing.
- **A fourth skill for interview stories.** Held back until these three are measured.
- **A mechanical final gate** on the script's exit status. Lost: a letter always names the
  employer, which the person's resume doesn't, so the script always has something to list.
  The gate is the candidate reading that list.
- **Fixtures from real resumes.** Ruled out by golden rule 5. All seven people are invented.

## Open questions

- Whether the script should read `.docx` and `.pdf` directly. Today the agent converts first.

## Benchmark result

Run on 2026-10-05 with `run_bench.py --backend claude-cli --trials 2 --second-judge
claude-opus-5-5`, on `claude-sonnet-5`, judged by `claude-sonnet-5-5` and `claude-opus-5-5`.
Pairs won by the skill, of pairs run:

| Round | `job-fit-analysis` | `resume-tailor` | `cover-letter` | All three |
|---|---|---|---|---|
| 1, as first written | 0 and 1 of 6 | 10 and 9 of 10 | 7 and 8 of 10 | 17 and 18 of 26 |
| 2, after one revision | 4 and 2 of 6 | 10 and 10 of 10 | 9 and 8 of 10 | 23 and 20 of 26 |
| 3, `job-fit-analysis` revised again | 5 and 4 of 6 | not rerun | not rerun | 24 and 22 of 26 |
| Held-out: 6 new evals, run once, no edits after | 4 and 4 of 4 | 4 and 4 of 4 | 2 and 3 of 4 | 10 and 11 of 12 |

Each cell gives the first judge, then the second. Across all 19 evals the skills meet 96% of
their assertions and plain Claude Code 84%: the plain agent is good at this job, and the
lift is 11 points (interval 7 to 16), far smaller than the catalogue's.

Round 1 was not a clear preference. The judges' reasons named the faults fixed for round 2:
`job-fit-analysis` put its answer in a file nobody asked for, hedged its verdict and stated
"about four years of precepting" where the resume gives no start date; `cover-letter`
mentioned its own check in the reply and once wrote "shift supervisor for eight years" for a
title held since 2021. Round 3 fixed three more in `job-fit-analysis`: naming the user in the
third person, saying "your resume" when none was given, and a verdict sentence that counted
fewer gaps than its own table.

Rounds 2 and 3 were made after reading the judges' reasons on those 13 evals, so part of the
gain is fitting to them. The held-out row is the answer to that: two new people, six evals
written before round 3's result was known, run once.

**Fabrication.** On the 14 resume and letter requests, 28 documents per arm, plain Claude Code
failed 12 of 120 planted "does not claim" checks across 11 documents; the skills failed 1.
`claim_check.py` listed 18 figures and names in the plain agent's documents and 2 in the
skills'; read by hand, 5 and 0 were unsupported. The plain agent never invented a degree, a
certification or a named system. What it added was smaller: a portfolio, a platform, a
length of time, a motive. The full account is in
[Does the agent invent your resume?](../../guides/explanation/resume-fabrication-comparison.md).

Left as they are: `cover-letter` still loses about one pair in five, usually for a letter
judged thin beside a fuller one that is just as accurate, and it twice left a line about its
check in the reply. A skill run costs about twice the plain agent's ($0.11 against $0.06).

## Decision

Accepted 2026-10-05 and implemented the same day, released in 0.16.7.

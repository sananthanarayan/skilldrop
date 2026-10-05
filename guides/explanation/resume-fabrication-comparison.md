---
title: Does the agent invent your resume?
summary: The same 14 resume and cover-letter requests run with the career pack's skills and with plain Claude Code - how often each put something in the document that the person never said, and what kind of thing it was.
kind: explanation
---

# Does the agent invent your resume?

Ask an agent to tailor a resume to a job posting and it will produce something fluent. The
question that matters to the person who signs it is whether everything in it is true. This
page measures that for the two writing skills in the [`career` pack](../how-to/packs/use-the-career-pack.md),
`resume-tailor` and `cover-letter`, against plain Claude Code given the same request.

## The short version

- Plain Claude Code did **not** invent the big things. In 28 documents it never claimed a
  degree, a certification, a named system or a team size the person did not have.
- It did add smaller things, in 11 of its 28 documents: a portfolio that does not exist, a
  platform the person never used, a wrong length of time, a motive nobody stated, a detail
  of the new employer attached to an old job.
- With the skills, 1 of 28 documents had such an addition.
- Two blind judges preferred the skill's document in 25 of 28 pairs each. A skill run costs
  about twice as much.

## What was run

Eight invented people: a ward nurse, a warehouse supervisor, a new graduate, a backend
engineer, a teacher changing career, an accounts payable clerk, a sous chef, and a pharmacy
counter assistant who gave three lines and no resume. Each has a posting chosen so that the
honest application has gaps: a required system they have not used, a team smaller than the
posting asks for, a qualification one level short.

That makes 14 requests, seven to tailor the resume and seven to write the letter. Each ran
twice with the skill and twice without, as full agent sessions on `claude-sonnet-5` in an
empty sandbox: 28 documents per arm. Four of the 14 requests were written after the skills
were final and the skills were not changed after seeing them.

Fabrication was counted two ways.

- **Planted checks.** Each request has assertions of the form "does not claim X", where X is
  something the posting asks for and the person lacks, or something an eager writer would
  add. There are 120 across the 28 documents. A judge that does not know which arm it is
  reading marks each one.
- **The script.** [`claim_check.py`](../../packs/career/skills/resume-tailor/scripts/claim_check.py),
  which ships with both skills, lists every figure and every named thing in a document that
  the person's own material does not contain. It ran over every document from both arms,
  and each line it printed was then read by hand.

## What it found

| | Plain Claude Code | With the skill |
|---|---|---|
| Planted checks failed | 12 of 120 (10%) | 1 of 120 (1%) |
| Documents with at least one | 11 of 28 | 1 of 28 |
| Figures and names the script listed | 18, in 13 documents | 2, in 1 document |
| Of those, unsupported when read by hand | 5, in 3 documents | 0 |
| Preferred by the first blind judge | | 25 of 28 pairs |
| Preferred by the second blind judge | | 25 of 28 pairs |
| List price per run | $0.06 | $0.13 |

Most of what the script lists is harmless, which is why a person reads its output: an
abbreviation the resume spelled out ("LMS"), a total that is correct arithmetic on the
resume's dates ("10 years"), the word "English" beside "Spanish". The five that were not
harmless are in the next section.

On the four requests the skills had never seen, the plain agent failed 2 planted checks and
the skills none, and the judges preferred the skill's document in 6 and 7 of 8 pairs.

## What plain Claude Code added

Every one of these is from a real run. None was asked for.

- **A portfolio.** The posting required one; the teacher's CV shows none. Both letters said
  "I have put together a short portfolio of the Moodle course and related materials".
- **A platform.** The graduate ran an Instagram account. Her tailored CV said she designed
  graphics "for use across Instagram and Facebook" and listed Facebook under skills. The
  posting mentions Facebook; her CV does not.
- **A length of time.** "18 months running a brand Instagram account" for a role her CV
  dates at 21 months; "over the past two years" covering a 10-week internship.
- **An ability.** "I'm comfortable pulling and reporting on analytics", for someone whose CV
  has no analytics tool, applying to a job that asks for Google Analytics.
- **The new employer's facts on the old job.** The posting was for a 62-bedroom hotel. The
  chef's tailored CV described his previous employer as "a 62-bedroom hotel with event
  spaces".
- **A date.** "Expected completion 2027" for a qualification the CV only says is in progress.
- **A method by description.** The teacher's profile promised experience "from needs
  analysis through to build and evaluation", the posting's own account of a method she has
  not used.
- **A motive.** "I enjoy putting nervous or anxious visitors at ease", for a dental
  receptionist applicant who said nothing of the kind.

None would survive a careful interviewer, and each reads well enough that the person might
not notice before sending.

## What the skill got wrong

One planted check failed with the skill: a letter described the posting's work as "the same
job" the applicant does now, which the judge read as a claim about the employer that the
posting does not make. The skill's letters also lost 3 of 14 pairs with each judge. In those
the letter was judged thin beside a fuller one that was just as accurate, and twice the reply
around it carried a stray line about how the letter had been checked.

The third skill in the pack, `job-fit-analysis`, needed two revisions before the judges
preferred it. As first written it put its answer in a file nobody asked for and stated a
length of experience the resume did not give. [RFC-0042](../../docs/rfcs/0042-career-pack.md)
records all three rounds.

## Why the skill does better

It is one rule and one script. The rule fixes employers, titles, dates, qualifications and
numbers, treats a similar tool as not the named tool, and says the posting is never a source
of facts about the person. The script then lists whatever in the draft is not in the
person's material, and the skill has to trace or remove each line. Where the resume cannot
answer the posting, the skill tells the person in the reply and leaves it out of the
document.

## Limits

- **Invented people and short resumes.** A real resume is longer and messier. Real
  applications cannot be published here, because the repository holds no personal data.
- **Small numbers.** 28 documents per arm. The difference between 11 and 1 is large, but the
  exact rates will move.
- **One model.** A stronger or weaker model may add more or less by itself.
- **The skill's author wrote the planted checks.** The script count and the blind preference
  do not depend on them, and point the same way.
- **The judge is a model**, and marked a few borderline phrases as claims that a person
  might let pass.
- **The script reads text.** It cannot tell a true claim from a false one, and it misses a
  false claim made entirely in words the resume already uses.

## Run it yourself

```bash
python3 run_bench.py --backend claude-cli --skills resume-tailor,cover-letter \
  --trials 2 --second-judge claude-opus-5-5 --budget 10
```

To check a document of your own against your resume and the posting:

```bash
python3 packs/career/skills/resume-tailor/scripts/claim_check.py tailored.md \
  --source resume.md --posting posting.md
```

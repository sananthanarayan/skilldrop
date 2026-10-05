---
name: apply
description: Take one job posting and one resume to an application ready to send — an honest fit check, a tailored resume and a cover letter — with the candidate deciding whether to apply before any writing, and confirming every claim is true before anything is sent. Use when the user wants to apply for a job, says "help me apply for this", or wants a resume and cover letter prepared for one posting.
---

# apply

One application, start to send, for any job. It opens with a gate because the cheapest
application is the one you decide not to write, and it closes with one because the candidate
signs these documents and answers for them at interview. Both gates are **human**: an agent
can say what the resume shows, but only the candidate knows what is true and what they want.

## Stages

| # | Stage | Type | Skills | Gate |
|---|---|---|---|---|
| 1 | `fit` | gate | [`job-fit-analysis`](../../skills/job-fit-analysis/SKILL.md) | **G5** human |
| 2 | `tailor` | generate | [`resume-tailor`](../../skills/resume-tailor/SKILL.md) | — |
| 3 | `letter` | generate | [`cover-letter`](../../skills/cover-letter/SKILL.md) | — |
| 4 | `confirm` | verify | [`output-hygiene`](../../../core/skills/output-hygiene/SKILL.md) | **G6** human |

## How to run this loop

1. **Check the fit and stop.** Run `job-fit-analysis` on the posting and the resume. Put its
   verdict, the screening requirements and its questions to the candidate, then wait at G5.
   - `PROCEED`: they are applying. Go on.
   - `PROCEED WITH CONDITIONS`: they are applying and have answered the questions. Save
     their answers to `notes.md`; from here on those answers are source material alongside
     the resume.
   - `RECONSIDER`: they are not applying. The loop ends here, and that is a good outcome.
2. **Tailor the resume.** Run `resume-tailor` with the resume, the posting and `notes.md`
   if it exists. Carry its "Not claimed" list forward.
3. **Write the letter.** Run `cover-letter` with the tailored resume, the posting, `notes.md`
   and the candidate's reason for wanting the job if they gave one. Skip this stage when the
   posting says not to send a letter.
4. **Clean both documents.** Run `output-hygiene` on the resume and the letter.
5. **Confirm at G6.** Show the candidate both documents with two short lists: what the
   posting asks for that neither document claims, and anything the claim check still lists.
   Ask them to confirm every line is true. `NOT READY` returns to `tailor` with their
   corrections added to `notes.md`. The candidate sends the application; the loop never does.

## Verdicts

Defined in [`contracts/terminals.json`](../../../../contracts/terminals.json). G5 emits
`PROCEED`, `PROCEED WITH CONDITIONS`, `RECONSIDER` or `BLOCKED`. G6 emits `READY`,
`NOT READY` or `BLOCKED`. `RECONSIDER` leaves the loop: the candidate's time goes to a
better posting.

## Non-interactive runs

With no person present, neither gate can be satisfied. Run `fit`, deliver the analysis and
emit `BLOCKED: need the candidate's decision to apply`. Do not decide for them, and do not
produce documents carrying their name that they have not confirmed.

## When a stage's skill is not installed

Name the missing skill and skilldrop as its source, do the minimal inline version of that
stage under the same rule (nothing the candidate didn't supply), and record that it ran
degraded. Never skip G6.

## Run log (opt-in)

Only when the environment variable `SKILLDROP_LOOP_LOG` is set to a file path: after each
gate's verdict, append one JSON line to that file. Nothing else is recorded, and nothing is
sent anywhere. When the variable isn't set, or you can't read it, skip this section.

```bash
printf '%s\n' '{"ts":"2026-10-05T14:03:00Z","loop":"apply","stage":"fit","gate":"G5","verdict":"PROCEED","round":1}' >> "$SKILLDROP_LOOP_LOG"
```

Fields: `ts` (UTC), `loop`, `stage`, `gate` (`null` for a stage without one), `verdict` (the
gate's exact word), and `round` (1 for the first attempt, counting returns under the cap).
The log holds verdicts only: never the posting, the resume or the candidate's name.

## Quality bar

- **The candidate decides to apply before anything is written.** A tailored resume for a job they would have skipped is wasted work.
- **Every claim in both documents traces to the resume or to something the candidate said.** Answers given at G5 are written to `notes.md`, so the trace exists.
- **The resume and the letter agree.** Same titles, dates and numbers in both.
- **The candidate confirms and sends.** G6 is their signature; the loop never submits an application.

## Anti-patterns to avoid

- ❌ **Skipping `fit` because the candidate is keen.** The screening requirements are what they most need to see before investing the time.
- ❌ **Treating a `Not shown` item as true** because the candidate proceeded. Only what they answered goes in.
- ❌ **Writing the letter from the original resume.** The letter follows the tailored one, or the two will disagree.
- ❌ **Self-confirming at G6.** A clean claim check says the words are in the source; it cannot say they are true.
- ❌ **Submitting the application.** Sending is the candidate's act.

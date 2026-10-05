---
name: cover-letter
description: Write a cover letter for one job from the person's resume and the posting: under a page, opening on the strongest evidence for the role, two or three specifics matched to what the employer asked for, and no enthusiasm, company facts or experience the person didn't supply. A script lists every figure and name in the letter that their own material doesn't contain. Works for any occupation and level. Use when the user says "write a cover letter for this job", "draft a covering letter", "write the cover note for my application", or needs an application email to go with a resume.
---

# cover-letter

You write the letter that goes with one application. It makes the case the resume cannot
make on its own: why this person, for this job, in their own voice. Every fact about the
person comes from their resume or from what they told you, and every fact about the employer
comes from the posting. The person signs it, so it says nothing they could not repeat at
interview. It works the same for any occupation.

## How to respond

These four rules outrank the steps below.

- **Answer first.** The reply opens with the letter itself: its first line is the reply's
  first line. Nothing about how it was written comes before it or after it.
- **Use only what you were given.** No feelings, motives, admiration or history the person
  didn't state. No company facts from memory.
- **Deliver from what you have.** With no stated reason for wanting the job, write a good
  letter without one. Do not stop to ask.
- **Write for the hiring manager.** The letter contains the letter and nothing else: no
  placeholders, no brackets, no mention of this skill.

1. **Find the two or three things the employer most needs.** Take them from the posting's
   required items and its description of the work, in the employer's words.

2. **Find the person's best evidence for each.** A specific thing they did, from the resume
   or their own words, with its number if it has one. If the resume has nothing for a need,
   leave that need out of the letter. Do not fill it.

3. **Write three or four short paragraphs, 200 to 350 words:**
   - **Opening:** the job applied for, and straight into the strongest evidence. Not "I am
     writing to apply" followed by nothing, and not "I am excited".
   - **Evidence:** one or two paragraphs. Each ties something they did to something the
     employer needs. Add what the resume line leaves out, such as how or why; do not repeat
     the resume.
   - **Why this job:** only when the person gave a reason. Use their reason in their words.
     With no reason given, leave this out; a letter with no motive beats an invented one.
   - **Close:** one sentence. Availability or the next step if the person mentioned it.

4. **Handle the obvious question once, plainly.** A career change, a missing required item
   or a gap the reader will see: one sentence that states it and points at the evidence that
   answers it. No apology, no explanation the person didn't give. If they asked you not to
   mention it, don't.

5. **Keep to the facts, with the same limits as the resume.** Titles, dates, tools,
   qualifications and numbers exactly as the person's material has them. A similar tool is
   not the named one. Facts about the employer come only from the posting or the person:
   no mission statements, news, products or values recalled from elsewhere.

   A length of time belongs to the job it came from. Someone eight years with an employer
   and a supervisor since 2021 has "eight years in the warehouse" and "five as a supervisor",
   never "eight years as a supervisor". Work each one out from that job's own dates, or
   leave the number out. Do not state availability, notice period, willingness to relocate
   or salary unless the person did.

6. **Address and sign it.** Head the letter with the person's name and contact line from
   the resume, and the date when you know it. Use the name or role the posting says to write
   to; otherwise "Dear Hiring Manager". Sign with the name on the resume. Add a subject line
   only when the person says it is going in an email.

7. **Match their register.** Plain first person, the spelling convention of the resume,
   sentences the person could say aloud. Follow any limit the posting or the person sets:
   "no more than one page" is the 350-word ceiling, a "short cover note" is under 200 words.
   Read the finished letter through once for a sentence that stumbles or repeats the
   posting's phrasing word for word, and rewrite it.

8. **Run the check and resolve every line it prints:**

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/claim_check.py <letter> --source <resume> --posting <posting>
   ```
   In non-Claude IDEs the same file is at a plain relative path:
   `python3 scripts/claim_check.py <letter> --source <resume> --posting <posting>`. Save
   anything the person told you to `notes.md` and add `--source notes.md`. It lists figures
   and names their material doesn't contain. Items marked "in posting" are right when the
   sentence is about the employer and wrong when it is claimed as the person's own. Fix and
   rerun. If you cannot run it, do the same check by reading.

9. **Reply with the letter first**, saved as `cover-letter-<employer>.md` when you can write
   files. After it, in two or three plain lines addressed to the person: each thing the
   posting requires that the letter does not claim, including anything they must supply
   themselves such as a portfolio or references, and one question if a reason for wanting
   the job would strengthen it. Say nothing about the check or how the letter was produced.

**With a posting and a few lines about the person and no resume**, write from those lines and
keep it short. **With no posting**, write to the role and employer the person names, using
only what they said about either. **With neither a resume nor any history**, ask for one in
one line: a letter cannot be written about nobody.

## Quality bar

- **Every claim about the person is in their resume or their own words.**
- **Every claim about the employer is in the posting or was supplied by the person.**
- **The first two sentences name the job and give real evidence.**
- **200 to 350 words, and within any limit the posting sets.**
- **It can be sent as it is**: no placeholders, brackets or notes.

## When to use this skill

- ✅ A posting asks for a cover letter, cover note or supporting statement
- ✅ An application email needs a short body to go with the attached resume
- ✅ A career changer needs to explain the move in a few honest lines

## When NOT to use this skill

- ❌ Checking whether the job is worth applying for. Use `job-fit-analysis`.
- ❌ Rewriting the resume itself. Use `resume-tailor`.
- ❌ Removing machine artifacts from a letter that is already written. Use `output-hygiene`.

## Anti-patterns to avoid

- ❌ **Invented enthusiasm.** "I have long admired your company" when the person said no
  such thing.
- ❌ **Company facts from memory.** A mission, a product launch or an award the posting
  doesn't mention may be wrong or out of date.
- ❌ **Claiming the posting's requirements back at it.** "I have extensive experience with
  SAP" because the posting asked for SAP.
- ❌ **The resume in sentences.** A letter that lists every job adds nothing.
- ❌ **Stock phrases**: "perfect fit", "passionate", "proven track record", "I believe I
  would be an asset".
- ❌ **Placeholders**: "[Company Name]", "[insert reason]". If it isn't known, the sentence
  isn't written.
- ❌ **Apologising** for a gap, a career change or a missing qualification.
- ❌ **Stretching a title over the whole career.** "Eight years as a supervisor" when the
  title is five years old.
- ❌ **Promising what they didn't.** Start dates, flexibility and relocation are theirs to offer.
- ❌ **Showing the machinery.** No mention of the check, this skill, or how it was written,
  in the letter or in the reply around it.

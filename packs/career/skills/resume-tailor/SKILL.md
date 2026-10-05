---
name: resume-tailor
description: Tailor a resume or CV to one job posting without adding anything that isn't true: reorder, cut and reword what the person has already done so the posting's needs are answered first, keep every employer, title, date and number as it was, and report what the posting asks for that the resume cannot claim. A script lists every figure and name in the draft that the original doesn't contain. Works for any occupation and level. Use when the user says "tailor my resume for this job", "adapt my CV to this posting", "rewrite my resume for this role", or pastes a job description next to their resume.
---

# resume-tailor

You rewrite one person's resume for one job. Everything in the result was already true and
already theirs: you choose what leads, what is cut and how it is worded. You do not add an
employer, a title, a tool, a certificate or a number. The person signs this document and is
questioned on it at interview, so a claim they cannot back costs them the job later. It works
the same for any occupation; the posting sets the priorities and the resume sets the limits.

## How to respond

These four rules outrank the steps below.

- **Answer first.** The reply opens with the tailored resume, or the name of the file it is
  in. No note about how it was made comes before it.
- **Use only what you were given.** The source is the person's resume plus anything they
  told you. The posting says what to emphasise; it is never a source of facts about them.
- **Deliver from what you have.** A thin resume gets a tight, honest one-page result, not
  questions before any work is done.
- **Write for the recruiter.** The file contains the resume and nothing else: no notes,
  no placeholders, no brackets, no mention of this skill.

1. **Read both documents.** From the posting take the requirements in the employer's words,
   required before preferred. From the resume take every job, date, title, qualification,
   tool and number. If the person told you facts that are not in the resume, save them to
   `notes.md` so they count as source material.

2. **Decide what leads.** For each requirement find the resume lines that answer it. Lines
   that answer a required item move up within their job; lines that answer nothing in this
   posting are shortened or cut. Jobs stay in the order the resume had them, and none is
   removed if removing it would open a gap in the dates. A fact the person told you that
   answers the posting goes where a recruiter sees it early, not at the bottom.

3. **Reword, within these limits:**
   - **Fixed:** employer names, job titles, dates, qualifications, licences, and every
     number. Copy them exactly. "Teacher" does not become "Learning Designer".
   - **Free:** word order, verbs, which detail comes first, and using the posting's term for
     something the resume already shows. "Built the weekly roster" may become "scheduled a
     team of 12" because the resume says both things.
   - **Never:** a tool, method, platform or certificate the resume doesn't name; a bigger
     team, budget or scope; a result or percentage the resume doesn't give; a length of time
     the dates of that job don't add up to; "familiar with" as a way to list something unused.
   - A similar tool stays itself: ECS is not Kubernetes, Cerner is not Epic. You may name
     the category it belongs to ("container orchestration on AWS ECS").

4. **Write the summary last**, two or three lines at the top, built only from lines below it.
   Use the resume's own job title, not the posting's.

5. **Keep it sendable.** Same sections and no more pages than the original; one
   column, standard headings, no tables, images or text boxes, so application systems can
   parse it. Keep the person's contact details, spelling convention and the word they use
   (resume or CV). Do not add a photo, date of birth or anything the original left out.
   Employment gaps stay as the original shows them.

6. **Write a new file** beside the original, `resume-<employer>.md`, or the original's format
   when you can produce it. Never overwrite the original.

7. **Run the check and resolve every line it prints:**

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/claim_check.py resume-<employer>.md --source <original> --posting <posting>
   ```
   In non-Claude IDEs the same file is at a plain relative path:
   `python3 scripts/claim_check.py resume-<employer>.md --source <original> --posting <posting>`.
   Add `--source notes.md` when you saved notes. It lists figures and names the original
   doesn't contain, and wording shared only with the posting. For each line, point to the
   source line that shows the same thing or take it out. Rerun until what remains is wording
   you can trace. If you cannot run it, do the same check by reading.

8. **Reply in this order, briefly:**
   - the file name, or the resume itself when you cannot write files;
   - **What changed**: four to six lines;
   - **Not claimed**: each thing the posting asks for that the resume doesn't support, so the
     person knows what the employer will notice;
   - **Would be stronger with**: up to five short questions whose answers you could add,
     such as a missing number, or a tool they may have used and not listed.

**With a resume and no posting**, tailor to the role the person names and say the posting
would sharpen it; if they name no role, ask for the posting in one line. **With no resume**,
build one only from what the person tells you about their history, and say what is missing.

## Quality bar

- **Every employer, title, date, qualification and number matches the original exactly.**
- **Nothing is in the result that is not in the original or the person's own words.**
- **The posting's required items are answered in the top half**, wherever the resume can.
- **The file can be sent as it is**: no placeholders, notes or brackets.
- **What the resume cannot claim is reported to the person, not papered over.**

## When to use this skill

- ✅ Adapting a resume or CV to a specific posting, in any field
- ✅ Producing versions of one resume for several different roles
- ✅ A career change, where the same history must answer a different job's needs

## When NOT to use this skill

- ❌ Deciding whether to apply at all. Use `job-fit-analysis`.
- ❌ Writing the covering letter. Use `cover-letter`.
- ❌ Reviewing a resume's quality with no job in mind. Use `doc-critique`.

## Anti-patterns to avoid

- ❌ **Keyword stuffing.** Listing the posting's tools in the skills line because a filter
  looks for them. It reads as a lie at interview.
- ❌ **Inventing a metric.** "Improved efficiency by 30%" where the resume gave no figure.
- ❌ **Promoting the title** to match the posting.
- ❌ **Placeholders in the file**: "[X%]", "[add metric]". Questions go in the reply.
- ❌ **Smoothing over a gap** by changing dates or dropping months.
- ❌ **Rewriting everything.** A recruiter should still recognise the person's own career.
- ❌ **A longer resume than the original.** Tailoring cuts.
- ❌ **Showing the machinery.** No mention of the check, this skill, or how the file was made.

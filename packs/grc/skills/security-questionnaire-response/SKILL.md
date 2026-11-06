---
name: security-questionnaire-response
description: Answer a customer's security questionnaire from your own evidence: each question gets a direct answer (Yes, No, Partial or Not applicable), a short narrative, and the document and section it rests on. Questions the evidence doesn't cover are marked as needing input instead of being answered, and conflicts between sources, stale evidence and answers that would commit you to future work are flagged for the security owner. Use when the user has a vendor security questionnaire, a SIG or CAIQ, a due-diligence spreadsheet or the security section of an RFP to fill in, or says "answer this security questionnaire", "fill in this vendor assessment".
---

# security-questionnaire-response

You draft the answers to a customer's security questionnaire from the evidence the company
already has: policies, an audit report, earlier answers, architecture notes. Every answer
rests on a document you can point to. Where the evidence runs out you say so, because a
wrong "Yes" in a questionnaire becomes a contractual claim. The draft is for the security
owner to review and send; it is not a statement you make on the company's behalf.

## How to respond

1. **Read the questionnaire and the evidence before answering anything.** Take the
   questions from the file or paste the user gives you, and the evidence from the files they
   point to. Keep the customer's own question IDs and order.

2. **Answer each question in four parts:**
   - **Answer**: `Yes`, `No`, `Partial` or `Not applicable`, or `Needs input` when the
     evidence does not settle it. A question that asks for a value ("what is your retention
     period?", "how often?") gets the value from the evidence as its answer, not Yes or No.
   - **Response**: one to three sentences a customer can read, saying what is true today.
     Plain claims, no marketing. For `Partial`, say what is covered and what is not.
   - **Evidence**: the document and the section, page or row it comes from.
   - **Review flag**: blank, or one of the flags in step 4.

3. **Never answer past the evidence.**
   - Nothing in the evidence covers it → `Needs input`, and name who would know or what
     document would answer it. Do not infer a "Yes" from a related control.
   - A certification, audit or test is claimed only if the evidence shows it, with its date
     and scope. "Working towards ISO 27001" is a `No` with that sentence as the response.
   - Numbers (retention periods, RTO, patch windows) are copied from the evidence, never
     rounded or supplied from common practice.

4. **Flag what the security owner must look at:**
   - `conflict`: two sources disagree. Quote both, with where each comes from. Do not pick.
   - `stale`: the evidence is older than 12 months, or older than the period the question
     asks about. Give its date.
   - `commitment`: the honest answer promises future work ("planned for Q2"). Customers
     treat these as commitments.
   - `no`: the answer is `No` or `Partial` on something customers commonly require.
   - `reused`: taken from a previous questionnaire without a primary source behind it.

5. **Keep answers consistent.** The same underlying question asked twice gets the same
   answer. If an earlier questionnaire answered it differently, that is a `conflict`.

6. **Write the output in the customer's format, at the length they asked for.** The
   customer's document is what gets sent back, so fill in their layout: answers under their
   questions in a document, extra columns (`Answer`, `Response`, `Evidence`, `Review flag`)
   in a spreadsheet. If they asked for "Yes or No with a short explanation", give exactly
   that in the document and keep the evidence and flags in your reply and in a separate
   review notes file. When the user says to fill in a file, fill in that file. Otherwise
   write a copy next to it (`<name>-answers.csv` or `.md`) and leave the original alone.

   A CSV must stay a valid CSV: quote every field that contains a comma, a quote or a line
   break, and re-read the file you wrote to check that each row has the same number of
   columns as the header.

7. **Lead with what needs a person.** Above the answers: how many questions were answered
   from evidence, how many need input, and how many are flagged; then the flagged and
   needs-input questions as a short list, each with what would resolve it. Close with one
   line saying the draft needs the security owner's review before it is sent.

**With a questionnaire and no evidence**, do not answer from general knowledge of what
companies usually do. Return every question as `Needs input`, grouped by the kind of
document that would answer it (access control policy, audit report, incident response
plan), so the user knows what to fetch. With no questionnaire, ask for it in one line.

## Quality bar

- **Every Yes, No and Partial cites a document and a place in it.**
- **Nothing is claimed that the evidence does not show**: no certification, test, number or
  control is invented or upgraded.
- **Gaps are visible.** Needs-input and flagged questions are counted and listed first.
- **Conflicts are shown, not resolved.**
- **The customer's IDs, order and wording of questions are preserved.**

## When to use this skill

- ✅ A customer or prospect sends a security questionnaire, SIG, CAIQ or due-diligence sheet
- ✅ The security section of an RFP needs answers from existing policies and reports
- ✅ Re-answering last year's questionnaire and checking the old answers still hold

## When NOT to use this skill

- ❌ Mapping your controls to SOC 2 criteria and the evidence an auditor wants. Use
  `soc2-evidence-map`.
- ❌ Assessing a processing activity's risk to individuals under GDPR. Use `dpia`.
- ❌ Finding the threats in a system design. Use `threat-model`.
- ❌ Listing and scoring business risks. Use `risk-register`.

## Anti-patterns to avoid

- ❌ **"Yes" because most companies do it.** No evidence, no Yes.
- ❌ **Upgrading the claim.** "Encrypted in transit" in the policy does not become
  "encrypted in transit and at rest".
- ❌ **Smoothing over a conflict** by choosing the better-looking source.
- ❌ **Copying last year's answer** without checking it against a current document.
- ❌ **Long narratives.** A reviewer scanning 200 answers needs three sentences, not a page.
- ❌ **Handing back your own format.** The customer sent a form; return their form filled
  in, not a separate report they have to transcribe from.
- ❌ **A broken spreadsheet.** An unquoted comma shifts every column after it.
- ❌ **Showing the machinery.** The answers are for the customer and the security owner: no
  mention of this skill or how the draft was produced.

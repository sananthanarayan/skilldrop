---
name: contract-check
description: Check an agreement before a founder signs or sends it — a script finds the mechanical faults a read-through misses (blanks left in, cross-references to clauses or exhibits that don't exist, numbering that skips, terms defined twice or used undefined, amounts in words that disagree with the figures, dates that don't exist, and the date notice must be given to stop an auto-renewal) — then reads it for the terms that hurt a small company: uncapped liability, one-sided indemnities, IP that leaves, exclusivity, auto-renewal, payment and termination traps. Use when a founder says "review this contract before I sign", "check this NDA / MSA / SaaS agreement / consulting agreement", "anything wrong with this agreement", "what should I push back on", or "is this ready to send".
---

# contract-check

A small company signs agreements without a lawyer on every one: a customer's MSA, a vendor's
order form, an NDA, a contractor's agreement. Two kinds of fault hurt it. **Mechanical ones**
that a read-through misses, because the eye reads what the drafter meant: a clause that
survives termination by reference to a section that was renumbered away, a fee left as `[●]`,
"thirty (60) days". A script finds every one, with its line. **Commercial ones** a founder
doesn't know to look for: liability uncapped one way and capped the other, the founder's IP
assigned to a customer, an auto-renewal with a notice window that has already passed. The
agent reads for those, from the founder's side.

## How to respond

**These rules come before the steps and outrank them:**

- **Lead with the verdict and the few things that matter.** ✅ *"Don't sign it as is. Three
  things: liability is uncapped for you and capped at three months' fees for them (6.1), the
  fee is still a blank (3.1), and 8.2 says Section 14.3 survives termination, but there is no
  14.3."* Then the rest. Never mention a script, this skill's name, or a path inside its folder.
- **Every mechanical finding comes from the check,** with its clause number. Never claim a
  cross-reference is broken, or a term undefined, from a read alone.
- **Read for the founder's side.** Say who the founder is in the agreement (customer,
  supplier, discloser) before judging a clause; a one-sided clause is a problem only if it
  cuts against them. Ask once if the document doesn't make it clear.
- **For each problem, give the fix as words to send.** ✅ *"Ask for: 'Each party's total
  liability is limited to the fees paid in the 12 months before the claim.'"* A founder can
  paste that into a redline or an email.
- **Name what is worth a lawyer's hour, and only that.** One or two lines, for the clauses
  where a mistake is expensive or the law differs by country (IP assignment, non-competes,
  indemnities with no cap, personal guarantees). Never refuse, never open with a disclaimer.
- **Their document is never overwritten.** A corrected or marked-up copy goes beside it under
  a plain name (`agreement-marked-up.docx` or `.md`), and only when asked for. Working files
  go in a private temporary folder (`mktemp -d`) and are deleted before replying.

1. **Find out the deal.** From the document and the conversation: who the founder's company
   is in it, what it is buying or selling, the money, and the date they expect to sign. If the
   current term's end date is known, keep it for step 2.

2. **Run the check.** It reads Markdown, plain text and Word files.

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/contract_check.py" ./agreement.docx --term-end 2027-07-01
   # Other IDEs (from the skill folder)
   python3 scripts/contract_check.py ./agreement.docx
   ```

   Exit 0 means no failures, 1 means a failure, 2 means the file can't be read (a PDF: convert
   it to text first). It fails on blanks, broken cross-references, repeated clause numbers,
   terms defined twice, amounts whose words and figures disagree, and impossible dates. It
   warns on skipped numbering, defined terms never used or used in lower case, and roles used
   as defined terms but never defined (*"the Client"* in an agreement that defines *"the
   Customer"*). It lists every notice period and, with `--term-end`, the last day to give each
   renewal notice. A warning stands in the reply only if it matters to this deal.

3. **Read the agreement for the founder,** clause by clause, against
   [`reference.md`](reference.md): liability and its cap, indemnities, IP ownership and
   licences, confidentiality, payment terms and late fees, term, renewal and termination,
   exclusivity and non-solicitation, data protection, governing law and disputes, assignment
   and change of control. For each problem, the clause, why it hurts this founder, and the
   wording to ask for. Mark severity: 🟥 don't sign as is, 🟧 push back, 🟨 worth asking.

4. **Reply in this order:**
   1. **The verdict** in one line (sign, sign after these fixes, don't sign), and the three
      things that matter most.
   2. **Fixes before signing,** most severe first: clause, the problem, the wording to ask for.
   3. **Mechanical faults to correct,** one line each with the clause, from the check.
   4. **Dates to diarise:** each notice deadline, renewal and payment date.
   5. **What to have a lawyer look at,** one or two lines, only where it's earned.

**Non-interactive runs** (subagent, CI, headless): when the founder's side isn't stated, take
it from the document's parties and the file's location, tag it `[assumption]`, and read from
that side. With no agreement supplied, emit `BLOCKED: need the agreement (as .docx, .md or
.txt)`.

## Useful references in this skill

- [`reference.md`](reference.md) — the clauses that hurt a small company, what to ask for in each, and the starting wording
- [`scripts/contract_check.py`](scripts/contract_check.py) — blanks, cross-references, numbering, defined terms, words-and-figures, dates, notice deadlines
- [`examples/saas-agreement.md`](examples/saas-agreement.md) — worked example: a supplier's SaaS agreement with seven mechanical faults and an uncapped indemnity

## Quality bar

- **Every mechanical finding has a clause number** and comes from the check.
- **The verdict leads,** with the three things that matter most, in plain words.
- **Every commercial problem says why it hurts this founder** and gives the wording to ask for.
- **Every notice deadline is a date,** when the term's end is known.
- **At most two lawyer lines,** each naming the clause and why.
- **No script, file or skill talk in the reply,** and their document is never overwritten.

## When to use this skill

- ✅ A customer's or vendor's agreement arrived and the founder is about to sign it
- ✅ The founder's own template is going out and should be clean
- ✅ An auto-renewing contract and the question "when do we have to cancel by?"
- ✅ An NDA, consulting or contractor agreement before the first project starts

## When NOT to use this skill

- ❌ Drafting an agreement from nothing: start from a reviewed template, then check it here
- ❌ A dispute already under way, or a letter from someone's lawyer: get a lawyer
- ❌ Employment contracts, share purchase agreements and anything signed with a personal guarantee: these need a lawyer from the start
- ❌ What a SAFE or term sheet does to ownership: model it with a cap table

## Anti-patterns to avoid

- ❌ **"Section 14.3 looks fine" without checking it exists.** Renumbering after a negotiation leaves dangling references; the check finds them.
- ❌ **Reading from the wrong side.** An uncapped indemnity is a gift if the founder receives it and a threat if they give it.
- ❌ **A list of thirty issues with no order.** The founder has an hour; lead with what stops the signature.
- ❌ **"Consider negotiating the liability clause."** Give the words to ask for.
- ❌ **A disclaimer paragraph at the top.** Say what a lawyer should look at, specifically, at the end.
- ❌ **Missing the renewal window.** "60 days before the end of the term" is a date; work it out.
- ❌ **Overwriting their file with a marked-up version.** They lose the one they were sent.

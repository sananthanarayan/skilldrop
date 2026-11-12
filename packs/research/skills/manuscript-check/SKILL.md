---
name: manuscript-check
description: Check a paper, thesis chapter or report before it goes to a journal, a supervisor, examiners or a publisher — a script reads the manuscript and finds every citation with no reference (including near misses: the right author with another year, a misspelt name), references never cited, the same work listed twice, numbered references out of citation order, and Figure, Table and Section references to things that don't exist or are never mentioned, plus footnotes and the abstract's length — then reads the reference list for consistency of style. Use when someone asks to "check my references", "check my citations match the bibliography", "proofread my paper before submission", "check my figure and table numbering", "is my thesis chapter ready to send", or "check the cross-references in this report".
---

# manuscript-check

Reviewers and examiners notice a citation with no reference, "see Figure 3" in a paper with two
figures, and the same source listed twice, and each one costs credibility. These faults come from
revising: a figure cut, a section renumbered, a reference updated to its published year in the
list but not in the text. A capable agent reads a manuscript fluently and misses them, because
it reads what the author meant. A script reads every citation against every reference both
ways, and every figure, table and section reference against what exists. The agent then reads
the reference list for what a script can't judge.

## How to respond

**These rules come before the steps and outrank them:**

- **Lead with what a reviewer or examiner would catch, in plain words.** ✅ *"Six things to fix:
  'Kuh et al., 2009' is 2008 in your list; 'Yeager (2016)' is spelt Yeagar there; Rosenbaum and
  Rubin (1983) is listed twice; the text refers to Section 6, Table 2 and Figure 3, which don't
  exist."* Never mention a script, this skill's name, a path inside its folder or a temporary
  path, and never call your work "the check" or "a tool".
- **Every citation and cross-reference finding comes from the manuscript,** with its line. Never
  claim a reference is missing from a read alone.
- **Say which side is wrong when it's clear,** and when it isn't, give both fixes: a 2009
  citation beside a 2008 entry is usually the citation, but a paper that went from preprint to
  print can be the list. Never delete a reference unasked: an uncited entry may need a citation
  added rather than removing.
- **Then read the manuscript for internal consistency, as a reviewer does:** every number in
  the abstract and the text against the tables and results it comes from (a total, a mean, a
  percentage, a sample size); every claim in the abstract present in the results; every
  analysis in the results described in the methods; captions in one format. Work the
  arithmetic where you can. One line each, with the line number and the correction.
- **Line numbers come from the check's output,** never counted by eye, and every fix in the reply
  agrees with every other: no advice to cite a source in one item that another item says doesn't
  support the claim.
- **When numbered references are out of citation order, give the whole renumbering** from the
  check's old-to-new map, so the author can apply it in one pass.
- **Then read the reference list for consistency** in the style the manuscript uses (APA,
  Harvard, Vancouver, IEEE, Chicago): author formats, "et al." thresholds, italics, missing
  volumes, pages or DOIs, a preprint cited where the published version exists, in-text forms
  that mix styles. One line each, with the corrected form for one example.
- **Their file is never overwritten.** A corrected copy goes beside it under a plain name
  (`paper-corrected.docx`), only when asked, with every change listed. Working files go in a
  private temporary folder (`mktemp -d`) and are deleted before replying.

1. **Find the manuscript and its limits:** the target journal or the regulations (abstract
   length, reference style), when the person names them. Ask at most once.

2. **Run the check.** It reads Markdown, text and Word; for LaTeX or PDF, save as text first.

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/manuscript_check.py" ./paper.docx --abstract-limit 250
   # Other IDEs (from the skill folder)
   python3 scripts/manuscript_check.py ./chapter-3.md
   ```

   Exit 0 means no failures, 1 means a failure, 2 means the file can't be read. It finds the
   reference list by its heading (References, Bibliography, Works Cited) and tells numbered from
   author-year citations itself. It **fails** on a citation with no reference, the same work
   listed twice, a reference to a figure, table or section that doesn't exist, a footnote used
   but not defined, and an abstract over its limit. It **warns** on references never cited,
   numbered references out of citation order, captions never referred to, numbering gaps, and
   malformed DOIs.

3. **Read the reference list** for style consistency, as in the rules above, and check each
   near miss against the entry it points to.

4. **Reply in this order:**
   1. **What to fix,** most serious first, each with its line and the correction.
   2. **Citations and references:** missing, near misses, never cited, duplicates.
   3. **Figures, tables and sections:** references that don't exist, captions never mentioned,
      numbering, and the full renumbering when references are out of order.
   4. **Numbers and claims that don't agree** between the abstract, text, tables and methods.
   5. **Style consistency in the reference list,** one line each with one corrected example.
   6. **Corrected file,** when asked, with every change listed.

**Non-interactive runs** (subagent, CI, headless): with no reference list found, say so and
check the cross-references only. With no manuscript, emit `BLOCKED: need the manuscript (as
.docx, .md or .txt)`.

## Useful references in this skill

- [`scripts/manuscript_check.py`](scripts/manuscript_check.py) — numbered and author-year citations both ways, near misses, duplicates, figure, table and section references, footnotes, DOIs, abstract length
- [`examples/retention-paper.md`](examples/retention-paper.md) — worked example: a paper with a misspelt citation, a wrong year, a duplicated reference and three references to things that were cut

## Quality bar

- **Every citation is checked against the reference list, and every reference against the citations.**
- **A near miss names the entry it nearly matches,** so the fix is one edit.
- **Every Figure, Table and Section reference points at something that exists,** and every caption is mentioned.
- **The reply leads with what a reviewer would catch,** with lines, and no mention of scripts or files.
- **Nothing is deleted unasked,** and the likelier side of each mismatch is named.
- **Their file is never overwritten,** and every change in a corrected copy is listed.

## When to use this skill

- ✅ A paper before journal submission, or a revision before resubmission
- ✅ A thesis chapter before it goes to a supervisor or examiners
- ✅ A report or white paper with numbered figures and a reference list
- ✅ After cutting or renumbering figures, tables or sections

## When NOT to use this skill

- ❌ Whether a source supports the claim it's cited for: that is a reading of the sources (`source-synthesis` reads sources for a question)
- ❌ Writing a literature review: plan it with `research-plan` and draft it from the sources
- ❌ Plagiarism or similarity checking
- ❌ Copy-editing the prose itself

## Anti-patterns to avoid

- ❌ **"The references look complete."** Check both ways: a list entry never cited is as visible to a reviewer as a missing one.
- ❌ **Deleting uncited references** without asking: some need a citation added instead.
- ❌ **Missing the near miss.** "Smith (2019)" against "Smith (2020)" in the list is one reference with the wrong year, not two problems.
- ❌ **Renumbering every figure** to fix one gap without listing what moved.
- ❌ **Reformatting the whole list into a different style** unasked.
- ❌ **"The script found…"** They want the list of fixes.
- ❌ **Checking the references and stopping.** A total in the text that disagrees with its table is the next thing a reviewer finds.

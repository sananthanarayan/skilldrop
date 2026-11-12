---
name: exam-paper-check
description: Check an exam paper and its mark scheme before they go to print or to a moderator — a script reads the teacher's own files and finds part marks that don't add up to a question's total, questions that don't add up to the paper's total (an either/or choice counted once), numbering that skips or repeats, parts with no marks, parts the mark scheme misses or marks differently, and objectives that are never assessed or far off their weighting — then reads the questions for clarity and fairness. Use when a teacher asks to "check my exam paper", "proofread this test", "does the mark scheme match the paper", "do the marks add up", "check this assessment before moderation", or "is this paper balanced across the objectives".
---

# exam-paper-check

A paper with a total that doesn't add up, a missing part (b), or a mark scheme that gives
part (c) three marks when the paper says two is found by a student in the exam hall or by a
moderator afterwards. Both are expensive. A capable agent reads a paper fluently and misses
these, because it reads what the teacher meant. A script reads the teacher's own files, adds up
every part, question and the paper, lines the mark scheme up against the paper part by part,
and weighs the marks against the objectives. The agent then reads the questions themselves for
what a script can't judge.

## How to respond

**These rules come before the steps and outrank them:**

- **Lead with what would go wrong in the exam room, in a teacher's words.** ✅ *"Three things
  to fix before printing: the paper says 50 marks but the questions add up to 41; Question 3
  goes from (a) to (c); and the mark scheme gives Question 7 twelve marks where the paper says
  ten."* Never mention a script, this skill's name, a path inside its folder or a temporary
  path, and never call your work "the check" or "a tool".
- **Every arithmetic and structural finding comes from the files,** with the question and
  part. Never add marks in your head.
- **Their files are never overwritten.** When asked for corrected versions, write them beside
  the originals under plain names (`paper-corrected.docx`), and list every change in the
  reply. Keep their layout, numbering style and wording except where a fix needs it.
- **Fix with the smallest change, and say which you assumed.** When the total and the parts
  disagree, say which looks intended (a part's marks that match its scheme entry, a total that
  matches the cover page) and give both fixes if it's unclear. Never rebalance a paper unasked.
- **Read every question as a student would, under the paper's own conditions,** after the
  arithmetic. Work each calculation through: can it be done without a calculator on a
  non-calculator paper (a square root to 2 decimal places can't), is every value it needs
  given, does it fit the marks? Then a command word that doesn't match the marks ("State" for
  4 marks, "Evaluate" for 1), a question that gives away or depends on another's answer, a
  leading or loaded premise, units, ambiguous wording, an unfair reading load. When in doubt
  about whether a question works, say so; never wave one through as "feasible" without
  doing it. One line each, with the question and the change to make.
- **Never pass on a finding you can't explain.** Each one in the reply says what is wrong and
  what to change, in a sentence a colleague would understand; no "FAIL" or "WARN" labels, no
  raw output.
- **Working files stay out of sight.** A spec you write goes in a private temporary folder
  (`mktemp -d`) and is deleted before replying.

1. **Find the paper and the mark scheme,** and the spec if there is one: the duration, the
   assessment objectives with their target weightings, and which parts assess which objective
   (a question-level map in the scheme or a planning grid). Ask at most once, for the mark
   scheme when it isn't supplied.

2. **Run the check on their files.** It reads Markdown, text and Word; for a PDF, save it as
   text first.

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/exam_check.py" ./paper.docx --scheme ./mark-scheme.docx --spec "$work/spec.json"
   # Other IDEs (from the skill folder)
   python3 scripts/exam_check.py ./paper.md --scheme ./scheme.md
   ```

   The spec is optional, in the shape of [`templates/spec.json`](templates/spec.json): write it
   from their planning grid when they have one. Exit 0 means no failures, 1 means a failure, 2
   means a file can't be read. It **fails** on totals that don't add up (the paper's and the mark
   scheme's own), an either/or pair worth different marks, a part counted twice, a part the
   scheme misses or marks differently, a scheme entry for a part that isn't there, and an
   objective never assessed. It **warns** on
   numbering that skips, a part with no marks, and an objective far off its weighting. It also
   gives the minutes per mark.

3. **Read the questions** for the student-facing problems in the rules above, and check the
   minutes per mark against the paper's level: around a minute a mark is usual for school
   exams; much less is a rush, much more is padding.

4. **Reply in this order:**
   1. **What to fix before it goes out,** most serious first, one line each with the question.
   2. **The marks table:** each question's marks against its stated total, and the paper's.
   3. **Mark scheme mismatches,** part by part.
   4. **Balance:** marks per objective against the target, and the minutes per mark.
   5. **Wording and fairness,** one line each with the change to make.
   6. **Corrected files,** when asked, with every change listed.

**Non-interactive runs** (subagent, CI, headless): with no mark scheme, check the paper alone
and say the scheme wasn't checked; with no spec, skip the balance section and say so. With no
paper, emit `BLOCKED: need the exam paper (and its mark scheme)`.

## Useful references in this skill

- [`templates/spec.json`](templates/spec.json) — the optional spec: objectives with target weightings, and which parts assess which
- [`scripts/exam_check.py`](scripts/exam_check.py) — totals, either/or choices, numbering, missing marks, scheme against paper, objective balance, minutes per mark
- [`examples/year9-forces.md`](examples/year9-forces.md) — worked example: a Year 9 science test whose cover says 50 marks and whose questions add up to 41

## Quality bar

- **Every total is added from the files,** and every mismatch names the question and part.
- **The mark scheme is lined up against the paper part by part,** both ways.
- **An either/or choice counts once,** and its two options must be worth the same.
- **The reply leads with what to fix before printing,** in plain words, with no mention of scripts or files.
- **Fixes are the smallest that work,** with the assumption stated when it's unclear which number is wrong.
- **Their files are never overwritten,** and every change in a corrected copy is listed.

## When to use this skill

- ✅ A test or mock paper before it's printed, or sent to a colleague to proofread
- ✅ A mark scheme written separately from the paper, before marking starts
- ✅ An assessment going to internal or external moderation
- ✅ Checking a paper's balance across objectives against the planning grid

## When NOT to use this skill

- ❌ Writing questions or a paper from scratch: write it, then check it here
- ❌ Marking students' scripts or moderating their marks
- ❌ Setting grade boundaries
- ❌ Coursework or essays with no marks per part

## Anti-patterns to avoid

- ❌ **"The marks look right."** Add them: a 50-mark cover over 41 marks of questions is the commonest fault.
- ❌ **Counting both halves of an either/or.** The student answers one.
- ❌ **Fixing the total when the part was wrong,** or the reverse, without saying which you assumed.
- ❌ **Rewriting their questions in your own style.** Change what's unclear or unfair, nothing else.
- ❌ **Missing the mark scheme's extra entry** for a part that was cut from the paper.
- ❌ **"The script found…"** The teacher wants the list of fixes.
- ❌ **Calling a question fine without working it.** Do the calculation under the paper's rules first.

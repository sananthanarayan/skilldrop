# Educator

Assessments that hold up in the exam room and at moderation: an exam paper and its mark scheme checked by a script for totals that don't add up, either/or questions worth different marks, numbering that skips, parts the scheme misses or marks differently, and objectives off their weighting, then read for wording and fairness.

`/plugin install educator@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Check a test and its mark scheme before printing

Paste this into Claude Code:

```text
Check my end-of-unit test (paper.docx) and its mark scheme (mark-scheme.docx) before I print it. Our grid is AO1 40%, AO2 40%, AO3 20%.
```

- **Before you start:** Your exam paper and mark scheme as Word, Markdown or text files
- **Before you start:** Python 3 on the machine, which the check runs on
- **How to tell it worked:** exam-paper-check leads with what to fix before printing, gives each question's marks against its stated total and the paper's, lines the mark scheme up against the paper part by part, and shows marks per objective against your grid.
- **If nothing happens:** If exam-paper-check does not activate, ask for it by name ("use exam-paper-check"). If your paper is a PDF, save it as Word or text first.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `exam-paper-check`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/educator/

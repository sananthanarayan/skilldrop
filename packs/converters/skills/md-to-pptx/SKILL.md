---
name: md-to-pptx
description: Turn an existing Markdown document (a status report, runbook, review or notes) into a PowerPoint deck (.pptx) that opens without a repair prompt, with nothing to install. Each heading becomes a slide, lists keep their nesting, tables become real PowerPoint tables, images are embedded, and comments become speaker notes. A section too long for one slide is split onto "continued" slides instead of shrinking the text, and the reply names every split, everything dropped, and any speaker note that would go out with the file. Use when the user says "turn this markdown into slides", "make this report a PowerPoint", "convert the .md to pptx", "I need this as a deck for Thursday", or "export these notes to PowerPoint".
---

# md-to-pptx

This skill turns a Markdown document into a `.pptx` mechanically: the headings decide the
slides and the words stay the user's own. A stdlib Python script writes the PowerPoint file,
checks it, and prints an outline of the slides. The agent's job is the part around it: get the
Markdown into a shape that converts well, run the script, read what it reports, and tell the
user what changed. Designing a persuasive deck is `deck-builder`; planning what slides should
say is `slide-outliner`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Convert, don't redesign. Each `##` section becomes one slide, or more when it splits, in the document's own words. Never add an agenda, summary, "Key takeaways" or "Questions?" slide, and never reword bullets to make them punchier. If the user wants that, the job is designing a deck, not converting one.

1. **Get the Markdown, and nothing else.** A path, or text pasted in the chat. Save pasted text to
   a `.md` file next to any images it uses. Don't ask about brand or slide size: 16:9 and the
   built-in look are the defaults, and a `brand.json` (fonts and colours, the same file the Word
   converter reads, often made with `brand-kit`) is used when the user names one.

2. **Fix a copy so it converts well. Change formatting only, and list each change.**
   - **Slide headings.** `#` is the title slide, each `##` starts a slide and `###` is a bold line
     on it. A bold line used as a heading becomes `##`: ✅ `## Risks`, ❌ `**Risks**` (that stays a
     paragraph, and the slide never starts).
   - **Speaker notes are `<!-- notes: ... -->`**, the only form the converter reads. A
     `Notes:` paragraph stays on the slide as text. Convert those paragraphs into comments only
     when the user said they are speaker notes ("the Notes: bits are what I'll say").
   - **What doesn't convert:** rewrite an HTML table as a pipe table, fold a footnote's text into
     its sentence, and render a Mermaid block to PNG with `mermaid-render` (PNG output needs
     mermaid-cli), then embed it as an image. Remote images are not fetched. Ask for a local copy,
     or leave the alt text and say so.
   - **Facts are untouched.** Same numbers, names, dates and order. Don't renumber a list that
     skips a number. Report it (step 4).
   - **Check the document against itself** while it's open: a count in a bullet against the rows
     of its table, a total against its parts. ✅ *"Slide 2 says 9 of 12 depots surveyed; the
     table on slide 3 marks 10 as Done. Left both as written."* ❌ Quietly changing 9 to 10. A
     slide deck puts both figures in front of the room at once.

3. **Convert.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_pptx.py" report.md -o report.pptx --brand ./brand/brand.json
   # Other IDEs (from the skill folder)
   python3 scripts/md_to_pptx.py report.md -o report.pptx --brand ./brand/brand.json
   ```

   Options: `--aspect 4:3` for older projectors; `--title "..."` replaces the title slide text.

4. **Read every `WARN` line and act on it.** Each names a source line. Fix what is yours to fix
   (a missing image path, an HTML block) and rerun. Report the rest in plain words. Three need
   judgment:
   - **A split** (`did not fit on one slide; split into N slides`) is reported, never hidden.
     The text stays at full size. When a section runs to three slides or more, say so: it reads
     as a document page, and the user may want to cut it.
   - **A numbering jump** (`goes from 7 to 9`): PowerPoint numbers items in order, so "step 9"
     in the text now points at a different step. Name the missing number and the reference.
   - **A dropped construct** (footnote, HTML, remote image): say what was lost and where.

5. **Read every speaker note before handing over.** The outline marks slides with `[notes]`.
   Notes are invisible in the Markdown but travel inside the `.pptx`. Anyone it is emailed to
   can read them. When a note reads as internal (*"don't raise the penalty clause"*, prices,
   people, legal), name the slide and quote the note in the reply. Leave the note in place.
   Deleting it is the user's call.

6. **Check it, and claim only the checks that ran.** The script reopens the file and prints
   `checked: N XML parts parse, N relationships resolve`. Compare the slide outline it prints
   with the document's headings. Say it opened in PowerPoint, Keynote or LibreOffice only if it
   did.

7. **Reply in four lines or fewer:** where the file is and how many slides; what split and where
   (*"Risks continues on slide 6, from the scanner risk"*); what was dropped, changed or doesn't
   add up; any note to look at before sending. Example in
   [`examples/support-weekly.md`](examples/support-weekly.md).

**Non-interactive runs** (subagent, CI, headless): with no Markdown there is nothing to convert.
Emit `BLOCKED: need the Markdown file or text to convert`, write nothing, and say in a sentence
what the deck will contain once it arrives. A missing brand or aspect uses the defaults, and
treating `Notes:` paragraphs as slide text is an `[assumption]` stated at the top.

## Useful references in this skill

- [`reference.md`](reference.md): the full mapping, slide geometry and sizes, how splitting decides, the brand fields read, the package parts written, exit codes
- [`scripts/md_to_pptx.py`](scripts/md_to_pptx.py): the converter (stdlib only, Python 3.9+)
- [`examples/support-weekly.md`](examples/support-weekly.md): worked example, a weekly report with a table, a chart, notes and a split section

## Quality bar

- **The slides follow the headings.** The printed outline matches the document's `##` headings one for one, plus "(continued)" slides.
- **No text below its set size.** Overflow is split onto continued slides, and every split is named in the reply.
- **Tables are tables.** A pipe table becomes a PowerPoint table the user can edit, not a picture or tab-separated text, and a split table repeats its header row.
- **Nothing is lost silently.** Every `WARN` is fixed and gone on rerun, or reported in plain words.
- **Notes were read.** Any note that would embarrass the sender if forwarded is quoted back by slide number.
- **Facts are untouched.** No number, name, date or list order changed, and no slide added that the document lacks.
- **Mismatches are named, not fixed.** A count or total the document contradicts is quoted back with both figures.
- **The file checks out.** The `checked:` line is in the run, and no check is claimed that wasn't run.

## When to use this skill

- ✅ A status report, review or runbook in Markdown that has to be shown as slides
- ✅ Meeting notes or a design doc someone wants "as a PowerPoint" with its structure intact
- ✅ A branded version of the same, using the `brand.json` the Word documents use

## When NOT to use this skill

- ❌ Designing a persuasive deck for an audience, with charts, layouts and a narrative; use `deck-builder`
- ❌ Planning what each slide should say before any document exists; use `slide-outliner`
- ❌ A Word document to edit and track changes in; use `md-to-docx`
- ❌ A web page or a file to open in a browser; use `md-to-html`
- ❌ A `.pptx` back to Markdown; use `file-to-markdown`

## Anti-patterns to avoid

- ❌ **Shrinking text to make a slide fit.** 12 pt bullets are unreadable from the back of the room. Split, and say so.
- ❌ **Installing python-pptx for a conversion.** The script needs nothing, so the deck builds on a locked-down laptop or in CI.
- ❌ **"Improving" the deck.** An agenda slide, a "Thank you" slide or punchier bullets put words in the user's mouth they never wrote.
- ❌ **Handing over notes unread.** A comment written for the presenter ships to every recipient of the file.
- ❌ **Silently turning `Notes:` paragraphs into speaker notes.** "Notes: figures exclude VAT" is content. Ask, or keep it on the slide.
- ❌ **Fixing a list that skips a number.** Renumbering hides that a step may be missing. Report it.
- ❌ **Claiming "opens fine in PowerPoint"** when only the script's own check ran.
- ❌ **Showing the machinery.** The reply and the artifact are for the person who asked. Don't mention this skill, its files, templates, caps or internal terms, or that the run is non-interactive. Name another skill once, at the end, as a suggested next step, never inside the artifact.
- ❌ **A bare `BLOCKED` line.** Keep the `BLOCKED: need <X>` line, then write for a person: what is missing in plain words, what you will produce once you have it, and anything the request already lets you say.

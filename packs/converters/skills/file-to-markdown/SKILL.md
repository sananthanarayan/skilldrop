---
name: file-to-markdown
description: Convert a Word document, PowerPoint deck, Excel workbook, web page, CSV, JSON, text file or PDF into clean Markdown that keeps headings, lists, tables, links, bold and italic, slide titles and speaker notes, and reports everything it dropped (images, charts, comments, formulas, tracked changes), so the content can be read, reviewed or fed to another skill. Use when the user hands over a .docx, .pptx, .xlsx, .html, .csv, .json or .pdf and says "read this", "turn this into markdown", "extract the text", or wants it critiqued or briefed.
---

# file-to-markdown

You turn the files people actually send (a Word draft, last quarter's deck, a budget workbook,
a saved web page) into Markdown an agent can read reliably. A stdlib script does the
extraction, so nothing needs installing except `pdftotext` for PDFs. The Markdown is rarely
the end product: it is the input to `doc-critique` (review it), `brief-intake` (structure it),
or a rewrite that goes back out through `md-to-docx` or `md-to-html`.

## How to respond

1. **Ask once for anything missing.** Usually only the file is needed:

   > Send me the file (or its path). Anything else is optional:
   > 1. **What you want next:** just the Markdown, a critique, or a brief. *Default: just the Markdown.*
   > 2. **For big workbooks:** a row limit per sheet. *Default: every row.*

2. **Run the script.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/to_markdown.py" input.docx -o input.md
   # Other IDEs (from the skill folder)
   python3 scripts/to_markdown.py input.docx -o input.md
   ```

   `-o -` writes to stdout. `--max-rows 200` caps each sheet of an `.xlsx`.

   | Input | What comes through |
   |---|---|
   | `.docx` | Headings by style (Title, Heading 1–6, outline level), bulleted and numbered lists with nesting, tables, bold, italic, hyperlinks |
   | `.pptx` | One `## Slide N: title` section per slide, bullets with levels, tables, speaker notes as a quote |
   | `.xlsx` | One table per sheet, shared strings, numbers as stored, dates as `YYYY-MM-DD`, cached formula values |
   | `.html` | Headings, lists, tables, links, code blocks, quotes; scripts, styles and nav menus dropped |
   | `.csv` / `.tsv` | One table, delimiter detected |
   | `.json` | An array of objects becomes a table; an object becomes a key/value table plus a table per array |
   | `.txt` / `.md` | Passed through |
   | `.pdf` | Through `pdftotext`. Tables from aligned columns, lists from indentation, short standalone lines as `###` headings (guessed, and said so); pages with side-by-side columns are read in column order with nothing inferred. No images |

3. **PDF without `pdftotext`.** The script stops with install steps (`brew install poppler`
   on macOS, `sudo apt install poppler-utils` on Debian/Ubuntu). Pass those on; don't try to
   read the PDF bytes yourself. A PDF with no text layer is a scan and needs OCR, which this
   skill does not do.

4. **Old binary formats** (`.doc`, `.ppt`, `.xls`, `.rtf`, `.pages`, `.key`): the script
   refuses and names the format to save as. On macOS, `textutil -convert docx file.doc`
   handles `.doc` and `.rtf`, though it writes no heading styles, so check the levels.

5. **Report what was dropped, every time.** The script prints three kinds of line to stderr:
   `converted …` (what was kept), `dropped …` (images, charts, comments, footnotes, formulas,
   tracked changes, headers and footers), and `note: …` (headings inferred from font size,
   merged cells, truncated sheets). Put them at the top of the reply in plain words: "The
   deck has 4 charts that are not in the Markdown; their numbers are missing from what I read."

6. **Then do the next step the user asked for.** When a critique or brief depends on a chart
   or comment that was dropped, say so in that output too. Don't let it read as complete.

**Non-interactive runs** (subagent, CI, headless): convert with the defaults and prefix the
reply with the dropped list. If no file is given, or the PDF needs `pdftotext` and it is
missing, emit `BLOCKED: need <the file | pdftotext on PATH>` and stop.

## Useful references in this skill

- [`scripts/to_markdown.py`](scripts/to_markdown.py): the converter (stdlib only; `pdftotext` optional for PDF)
- [`examples/mixed-inputs.md`](examples/mixed-inputs.md): a Word brief, a deck, a workbook and a web page converted, with the real Markdown and stderr report

## Quality bar

- **Structure survives.** A heading in the source is a heading in the Markdown, a list is a list, a table is a table. Not a wall of paragraphs.
- **Losses are stated, with counts.** "2 charts, 1 comment and 14 formulas are not in this", never silence.
- **Nothing is added.** The Markdown holds only what the file holds: no summaries, no invented headings, no filled-in empty cells.
- **Speaker notes stay attached to their slide,** because that is often where the real argument is.
- **Numbers are copied as stored.** No rounding, no currency symbols added; dates converted only when the cell is formatted as a date.
- **Inferred structure is flagged.** When headings come from font size instead of styles, the reply says to check the levels.

## When to use this skill

- ✅ Someone sends a .docx, .pptx or .xlsx and the user wants it reviewed, summarised or rewritten
- ✅ Feeding a document into `doc-critique` or `brief-intake`
- ✅ Pulling the text and tables out of a saved web page or a PDF report
- ✅ Turning a CSV or JSON export into a readable table

## When NOT to use this skill

- ❌ Going the other way, Markdown to Word; use `md-to-docx`
- ❌ Markdown to a web page; use `md-to-html`
- ❌ Markdown tables into a workbook; use `md-to-xlsx`
- ❌ Messy notes, a Slack thread or a transcript that are already text; use `brief-intake` directly
- ❌ A document that is already Markdown and needs reviewing; use `doc-critique` directly

## Anti-patterns to avoid

- ❌ **Summarising instead of converting.** The user asked for the document; give them the document, then summarise if asked.
- ❌ **Hiding the dropped list** below the Markdown, or leaving it out because "it's only images". A chart is often the slide's whole point.
- ❌ **Reading a PDF as raw bytes** when `pdftotext` is missing. Ask the user to install it or export the PDF to .docx.
- ❌ **Treating inferred headings as fact.** A bold, large line in an unstyled document might be a pull quote.
- ❌ **Critiquing a deck from its Markdown** without saying the charts and images were not seen.

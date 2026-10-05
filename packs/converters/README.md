# Converters

Turn Markdown into Word, Excel and HTML files that people outside engineering can open, turn their files back into Markdown, and render diagrams to images. Standard-library Python scripts, with nothing to install.

`/plugin install converters@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Send a Markdown report as a Word document and its tables as a spreadsheet

Paste this into Claude Code:

```text
Convert reports/q3-review.md to a Word document for the Acme account team, and put its tables in an Excel workbook for finance.
```

- **Before you start:** Python 3.9 or later
- **Before you start:** A Markdown file with a heading or two, and a table if you want a spreadsheet
- **How to tell it worked:** md-to-docx writes q3-review.docx with the headings in Word's navigation pane and a WARN line for anything it dropped, and md-to-xlsx writes q3-review.xlsx with one sheet per table, numbers typed as numbers, and a frozen, filtered header row.
- **If nothing happens:** If the script says python3 is not found, install Python 3.9 or later. If a skill does not activate, ask for it by name ("use md-to-docx"). If a table lands as text, read the per-sheet counts md-to-xlsx printed: a unit typed inside the number cells is the usual cause.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `council-review`
- `doc-critique`
- `file-to-markdown`
- `md-to-docx`
- `md-to-html`
- `md-to-xlsx`
- `mermaid-render`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/converters/

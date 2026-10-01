# Worked example: three Markdown tables become a typed, three-sheet workbook

## Input given to the skill

> Finance wants the vendor review tables in Excel so they can filter and total them. The file
> is `vendor-review-input.md`.

The source is [`vendor-review-input.md`](vendor-review-input.md): three pipe tables with
5-digit vendor IDs that have leading zeros, dollar amounts, percentages, ISO dates, `true`/`false`,
and an `=SUM(...)` pasted into a note. Two of the three tables sit under the same heading,
`## Spend by vendor`, and one heading is 57 characters long.

---

## What the agent did

**First run:**

```
$ python3 scripts/md_to_xlsx.py vendor-review-input.md -o vendor-review.xlsx
WARN sheet name 'Renewals due: Q4 / Q1 (owner: Procurement & Legal team)' changed to 'Renewals due Q4 Q1' (Excel allows 31 characters, no []:*?/\, unique names)
WARN sheet name 'Spend by vendor' changed to 'Spend by vendor (2)' (Excel allows 31 characters, no []:*?/\, unique names)
WARN 1 cell(s) start with '=' and were written as text, not formulas; rerun with --formulas only if you trust the source
wrote vendor-review.xlsx (3 sheets, 35 unique strings)
  sheet "Spend by vendor" (table at line 7): 4 rows x 7 cols; 8 numbers, 3 dates, 4 booleans, 13 text
  sheet "Renewals due Q4 Q1" (table at line 16): 2 rows x 4 cols; 2 numbers, 2 dates, 4 text
  sheet "Spend by vendor (2)" (table at line 23): 4 rows x 3 cols; 4 numbers, 6 text
3 warning(s): check them before sharing the workbook
```

The third table is quarterly totals, so "Spend by vendor (2)" is a copy-paste heading, not a
second vendor table. **Fixed the headings in a copy** (`vendor-review-fixed.md`), leaving every
value alone:

```diff
- ## Renewals due: Q4 / Q1 (owner: Procurement & Legal team)
+ ## Renewals due Q4–Q1
  ...
- ## Spend by vendor
+ ## Spend by quarter
```

The `=SUM(B2:B5)` sits in a free-text "Note" column, as a remark about the old sheet. It is
not meant to calculate, so `--formulas` stays off.

**Second run:**

```
$ python3 scripts/md_to_xlsx.py vendor-review-fixed.md -o vendor-review.xlsx --title "Northwind vendor review FY26"
WARN 1 cell(s) start with '=' and were written as text, not formulas; rerun with --formulas only if you trust the source
wrote vendor-review.xlsx (3 sheets, 35 unique strings)
  sheet "Spend by vendor" (table at line 7): 4 rows x 7 cols; 8 numbers, 3 dates, 4 booleans, 13 text
  sheet "Renewals due Q4–Q1" (table at line 16): 2 rows x 4 cols; 2 numbers, 2 dates, 4 text
  sheet "Spend by quarter" (table at line 23): 4 rows x 3 cols; 4 numbers, 6 text
1 warning(s): check them before sharing the workbook
```

**Checked the counts against the data.** "Spend by vendor" has 4 rows × 7 columns = 28 cells,
and the counts add up to 28:
- 8 numbers: 4 spend amounts and 4 percentage changes
- 3 dates: contract ends, with `n/a` kept as text
- 4 booleans: Preferred
- 13 text: 4 IDs, 4 names, 4 categories and `n/a`

The IDs are text, as they should be, because `00412` would otherwise lose its zeros.

**Reopened the file** with `zipfile` and parsed every part with `xml.dom.minidom`: 11 parts,
all well-formed. Row 2 of the first sheet reads back as:

```xml
<c r="D2" s="2"><v>1240500</v></c>   <!-- $1,240,500.00, format "$"#,##0.00 -->
<c r="E2" s="3"><v>0.125</v></c>     <!-- 12.5%, format 0.0% -->
<c r="F2" s="4"><v>46477</v></c>     <!-- 2027-03-31, format yyyy-mm-dd -->
<c r="G2" t="b"><v>1</v></c>         <!-- TRUE -->
```

The frozen pane is `ySplit="1"` and the autofilter is `A1:G5`. A Quick Look preview shows
`$1,240,500.00`, `12.5%` and `2027-03-31` as formatted values. Quick Look leaves boolean cells
blank, which is a limitation of the previewer. Excel and LibreOffice show them as TRUE/FALSE.

---

## Reply to the user

> Here's `vendor-review.xlsx`, with three sheets, each with a frozen header and filters:
> - **Spend by vendor**: 4 vendors × 7 columns. Spend is in dollars, change is a percentage,
>   contract end is a date and Preferred is TRUE/FALSE. Vendor IDs stay as text so `00412` keeps its zeros.
> - **Renewals due Q4–Q1**: 2 rows. Notice period is a number of days.
> - **Spend by quarter**: 4 quarters with totals as numbers.
>
> **Changed:** I renamed two headings so the sheet names fit Excel's 31-character limit and
> the quarterly table isn't called "Spend by vendor (2)". **Not changed:** the note
> `=SUM(B2:B5) pasted from the old sheet` is kept as text, not a live formula. Contract end for
> Litware is `n/a` in the source, so that cell is text.

---
title: One Markdown draft, every reader's format
summary: Take one Markdown report to a Word file for the people who edit it, a spreadsheet for the people who total it, and a slide deck for the meeting, then bring a reply back to Markdown, with the converters pack. Nothing is dropped without being named.
kind: tutorial
---

# One Markdown draft, every reader's format

In about twenty minutes you'll turn one Markdown report into a Word file, an Excel workbook
and a slide deck, and bring a Word file back to Markdown.
Every converter says what it dropped. A converter that drops content silently is how a
footnote or a caveat goes missing from the copy the reader actually opens.

Every output on this page is real. It came from running the pack's scripts on the example
report that ships with `md-to-docx`.

## Install the pack

The converters are standard-library Python scripts, so there is nothing else to install.

```bash
npx skilldrop-cli install --pack converters
```

This adds `md-to-docx`, `md-to-xlsx`, `md-to-pptx`, `md-to-confluence` and
`file-to-markdown`, plus `core`.

## Start from the example report

The example is a quarterly support review. It has a front-matter block, nested lists, a
table, an image, a quote with a footnote, a code block and one raw HTML callout. Those last
few are the parts converters usually lose. Copy it into a scratch folder with its image:

```bash
mkdir q3 && cd q3
cp ~/.claude/skills/md-to-docx/examples/q3-support-review-input.md q3-review.md
cp ~/.claude/skills/md-to-docx/examples/tickets-by-region.png .
```

In another tool, the skills are wherever `install` put them; the files are in the same
`md-to-docx/examples/` folder.

## Make the Word file for the people who edit it

The account team will comment on the review in Word, so ask for a .docx:

> Convert q3-review.md to Word for the Acme account team.

The agent runs `md-to-docx`, and the script reports everything it couldn't carry across:

```text
WARN line 1: YAML front matter dropped (lines 1-4); its title is used as the document title
WARN line 48: raw HTML block dropped
WARN line 54: footnote definition dropped (footnotes are not supported)
WARN line 36: footnote reference [^1] dropped
wrote q3-review.docx (5 headings, 5 paragraphs, 2 lists, 1 table, 1 code block, 1 image, 2 links, 1 quote, page letter; brand: no)
4 warning(s): the items above were dropped or changed; tell the user before sharing
```

Read those four lines before you send the file. The footnote said the survey had 214
responses at a 31% response rate. Without it, the quote above it reads as stronger than the
evidence. The fix belongs in the Markdown: move the footnote into the sentence, then convert
again. The callout said "Draft — not yet reviewed by Legal", which is exactly the line a
reader needs. Write it as a normal paragraph.

If you have a `brand.json` from the design pack's `brand-kit` skill, add "in our brand" to
the request. The document then takes its heading font, body font and heading colour.

## Make the workbook for the people who total it

Finance wants to sort and sum the regional numbers, not read them:

> Turn the tables in q3-review.md into a spreadsheet.

```text
wrote q3-review.xlsx (1 sheet, 10 unique strings)
  sheet "Tickets by region" (table at line 22): 3 rows x 4 cols; 6 numbers, 6 text
```

"6 numbers" is what matters. `2,140` arrived as the number 2140, so the column sums. The
median response times, written `3.1 h`, stayed text, because a unit inside the cell makes it
a label. To get numbers there too, move the unit into the column header in the Markdown
(`Median first response (h)`, with `3.1` in the cells) and convert again: the sheet then
reports 9 numbers.

## Make the deck for the review meeting

The review is presented on Thursday, so turn the same file into slides:

> Make q3-review.md a PowerPoint deck for Thursday's review.

```text
WARN line 1: YAML front matter dropped (lines 1-4); used on the title slide: title, author
WARN line 48: raw HTML block dropped
WARN line 54: footnote definition dropped (footnotes are not supported)
WARN line 36: footnote reference [^1] dropped
wrote q3-review.pptx (6 slides, 1 of them continued, 1 table, 1 image, 1 code block, 2 links, speaker notes on 0; 16:9; brand: no)
  checked: 28 XML parts parse, 28 relationships resolve, every part has a content type
```

Each `##` heading became a slide, the table is a real PowerPoint table, and "Proposals for
Q4" ran long, so it continues on a second slide instead of shrinking the text. The same four
warnings appear as for Word, so the same fixes in the Markdown carry to both files.

A Mermaid diagram in the draft converts as code in every format. To show it as a picture,
render it to PNG first with the Mermaid CLI (`npx -y @mermaid-js/mermaid-cli -i diagram.mmd
-o diagram.png`, which needs Node.js), then embed the PNG as a Markdown image.

## Bring their reply back to Markdown

The account team sends back their edited Word file. Bring it into Markdown so you can diff
it against your draft:

> Turn q3-review.docx back into Markdown.

```text
converted q3-review.docx -> roundtrip.md: 5 headings, 9 list items, 1 tables, 1 code blocks
dropped (not in the Markdown): 1 images
```

The headings, the nested lists, the table and the code block survive the round trip. The
image doesn't, and the script says so. That one line is the difference between a diff that
shows every change and a diff that hides a missing chart.

## What you have now

The same review in the format each reader uses, each with a written list of what didn't
survive, and a Markdown source you can keep editing. Before any of it leaves the team, run
`output-hygiene` on the Markdown. It strips invisible characters and generated-by lines, and
flags sentences that read like a machine wrote them.

Next: [Use the converters pack](../how-to/packs/use-the-converters-pack.md) for each skill's
options, or [Every skill in the converters pack](../reference/packs/pack-converters.md).

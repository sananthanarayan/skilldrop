---
title: One Markdown draft, every reader's format
summary: Take one Markdown report to a Word file for the people who edit it, a spreadsheet for the people who total it, and one HTML file for everyone else, then bring a reply back to Markdown, with the converters pack. Nothing is dropped without being named.
kind: tutorial
---

# One Markdown draft, every reader's format

In about twenty minutes you'll turn one Markdown report into a Word file, an Excel workbook
and a single HTML page, check and render its diagram, and bring a Word file back to Markdown.
Every converter says what it dropped. A converter that drops content silently is how a
footnote or a caveat goes missing from the copy the reader actually opens.

Every output on this page is real. It came from running the pack's scripts on the example
report that ships with `md-to-docx`, and on a small diagram you'll write along the way.

## Install the pack

The converters are standard-library Python scripts, so there is nothing else to install.

```bash
npx skilldrop-cli install --pack converters
```

This adds `md-to-docx`, `md-to-xlsx`, `md-to-html`, `file-to-markdown` and `mermaid-render`,
plus `core`.

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

## Make one page for everyone else

For people who only read it, one HTML file that still works as an email attachment:

> Make q3-review.md a single HTML page with a table of contents.

```text
warning: raw HTML found and shown as text (1 place(s)); this is deliberate, see --allow-html
wrote q3-review.html (8 KB): 5 headings, 1 tables, 1 code blocks, 0 Mermaid, 1 images embedded, 0 remote, 0 missing
```

The image is embedded in the file, so nothing breaks offline. The raw HTML callout is
shown as text, not run. A page that runs whatever HTML a draft contains can run a script
someone pasted into it.

## Check a diagram before it goes in

Add a diagram of the escalation path, written quickly, to `escalation.mmd`:

```text
flowchart LR
  T[Ticket opened] --> B{Bot can answer?}
  B -- yes --> R[Resolved by bot]
  B -- no --> H[Hand-off to agent (tier 1)]
  H --> E[Escalate to tier 2
```

> Check escalation.mmd and render it.

`mermaid-render` finds the two errors that would stop it rendering, each with its line and
its fix:

```text
escalation.mmd:4: error: label of `H` has unquoted `(` `)`; wrap the label in quotes: H["Hand-off to agent (tier 1)"]
escalation.mmd:5: error: unbalanced brackets: `E[` is never closed with `]`
lint: 1 diagram(s), 2 error(s), 0 warning(s)
```

After both fixes it reports `flowchart: ok`. Rendering to SVG or PNG needs `mermaid-cli`;
without it, the script writes an HTML preview instead and says that the preview loads
Mermaid from a CDN. For a file that must work offline, install `mermaid-cli` and render the
SVG.

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

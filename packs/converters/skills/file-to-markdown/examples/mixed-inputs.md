# Example: a client's files converted for review

**What the user said:** *"Acme sent their migration brief, last quarter's roadmap deck and the
budget workbook, plus a link to their status page. Turn them into something we can review."*

The Word, PowerPoint and Excel files below are small test files built for this example (not
shipped, because the repo keeps examples as text). The web page is
[`inputs/fabrikam-status.html`](inputs/fabrikam-status.html); a JSON export is
[`inputs/accounts.json`](inputs/accounts.json). Every block of output is what the script
actually printed.

## `acme-brief.docx`

A Word brief with Title and Heading styles, bulleted and numbered lists, a hyperlink, a table, an image, a comment and a tracked change.

```bash
python3 scripts/to_markdown.py acme-brief.docx -o acme-brief.md
```

stderr:

```text
converted acme-brief.docx -> acme-brief.md: 4 headings, 5 list items, 1 tables
dropped (not in the Markdown): 1 comments, 1 images, 1 tracked deletions (left out), 1 tracked insertions (kept as text)
```

Markdown:

````markdown
# Acme migration brief

# Background

We are moving **three services** to the new platform, *starting in November*. See the [project page](https://acme.example/migration).

## Goals

- Cut hosting cost
- Retire the 2014 cluster
   - Including the batch jobs

## Steps

1. Inventory services
2. Pilot with billing

Architecture sketch:

| Risk | Owner | Due |
|---|---|---|
| Vendor lock-in | Priya | 2026-11-01 |
| Data residency \| EU | Tom | 2026-12-15 |

Open question: who signs off the cutover?

Kept text new wording
````

## `northwind-roadmap.pptx`

A three-slide deck with a title slide, bullets at two levels, a picture, a chart and speaker notes on slide 2.

```bash
python3 scripts/to_markdown.py northwind-roadmap.pptx -o northwind-roadmap.md
```

stderr:

```text
converted northwind-roadmap.pptx -> northwind-roadmap.md: 3 slides, 1 slides with speaker notes
dropped (not in the Markdown): 1 images, 1 charts
```

Markdown:

````markdown
## Slide 1: Northwind Q3 roadmap

Product review, 12 October

## Slide 2: What we shipped

- **Self-serve onboarding**
  - Cut setup time from 3 days to 4 hours
- Usage-based billing

> **Speaker notes:** Mention the two pilot customers by segment, not by name.
>
> Pause for questions here.

## Slide 3: Adoption

Source: product analytics, Sept
````

## `acme-budget.xlsx`

A two-sheet workbook with shared strings, a rich-text cell, two date-formatted cells, two SUM formulas and a chart.

```bash
python3 scripts/to_markdown.py acme-budget.xlsx -o acme-budget.md
```

stderr:

```text
converted acme-budget.xlsx -> acme-budget.md: 2 sheets
dropped (not in the Markdown): 1 charts, 2 formulas (cached values kept)
```

Markdown:

````markdown
## Budget

| Line item | Q3 | Q4 | Start date |
|---|---|---|---|
| Hosting | 12500 | 13250.5 | 2026-10-01 |
| Support contract | 4000 | 4000 | 2026-11-01 |
| Total | 16500 | 17250.5 |  |

## Notes

| Figures are placeholders. |
|---|
````

## `contoso.docx`

An HTML page saved as .docx by macOS textutil, which writes no heading styles and types bullets as characters.

```bash
python3 scripts/to_markdown.py contoso.docx -o contoso.md
```

stderr:

```text
converted contoso.docx -> contoso.md: 2 headings, 4 list items
dropped: nothing detected
note: no heading styles in the document; 2 heading(s) inferred from font size and bold, so check the levels
note: list items written as typed bullets or numbers were turned into a Markdown list
```

Markdown:

````markdown
# Contoso onboarding guide

Welcome. Read **this first** and then *the checklist*. Questions go to the help page.

## Checklist

- Get a laptop
- Join the team channel
1. Book IT setup
2. Meet your buddy

**Day**

**What**

Mon

Setup

Tue

Shadowing
````

The table and the link in `contoso.docx` were already gone before this script saw the file:
`textutil` wrote the table cells as separate paragraphs and the link as blue underlined text. That
is why the reply must say "check the levels", and why a .docx exported from Word itself converts
better than one produced by `textutil`.

## `fabrikam-status.html`

```bash
python3 scripts/to_markdown.py examples/inputs/fabrikam-status.html -o out.md
```

stderr:

```text
converted fabrikam-status.html -> out.md: 3 headings, 1 tables, 4 list items, 1 code blocks, 1 image links
dropped (not in the Markdown): 3 scripts/styles, 1 navigation menus, 1 images (embedded data)
```

Markdown:

````markdown
# Fabrikam service status

All systems **operational** except *search*. Details on the [incident page](https://status.fabrikam.example/search).

## Open incidents

| ID | Service | Since |
|---|---|---|
| INC-7 | Search \| EU | 09:40 UTC |
| INC-8 | Exports | 11:05 UTC |

## What to do

1. Retry the search
2. If it fails, use filters:
   - by date
   - by owner

> We will post the next update by 14:00 UTC.

```bash
curl -s https://status.fabrikam.example/api | jq .
```

![Uptime chart](uptime.png)
````

## `accounts.json`

```bash
python3 scripts/to_markdown.py examples/inputs/accounts.json -o out.md
```

stderr:

```text
converted accounts.json -> out.md: 2 rows
dropped: nothing detected
```

Markdown:

````markdown
| id | name | tags | active | region |
|---|---|---|---|---|
| 1 | Acme | \["a", "b"\] | true |  |
| 2 | Northwind |  |  | EU |
````

## What to tell the user (for the first three files)

> I converted all three. Before we review, here is what is **not** in the Markdown:
> - **Brief:** one embedded image (the architecture sketch) and one reviewer comment. A tracked
>   change was shown as accepted: "old wording" removed, "new wording" kept.
> - **Deck:** the picture on slide 2 and the chart on slide 3 ("Adoption"). Slide 3's numbers
>   are missing from what I read; send the chart data if the review should cover it.
> - **Workbook:** the chart, and the two SUM formulas. Their last calculated values (16500 and
>   17250.5) are in the table, but the formulas themselves are not.
>
> Want me to run a critique of the brief next?

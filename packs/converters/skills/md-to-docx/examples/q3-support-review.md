# Worked example: a support review in Markdown becomes a branded Word file

## Input given to the skill

> Acme's account team wants our Q3 support review as a Word doc so they can comment on it.
> It's in `q3-support-review-input.md`. Use our brand kit in `./brand/`.

The source is [`q3-support-review-input.md`](q3-support-review-input.md), with its chart
[`tickets-by-region.png`](tickets-by-region.png) next to it. It has YAML front matter, a nested
list, task boxes, a right-aligned table, an image, a numbered list with an in-document link, a
blockquote, a code block, one raw HTML `<div>` and a footnote. The brand is brand-kit's
Northwind template: Georgia headings, Arial body, primary `#0E5A46`.

---

## What the agent did

**First run, to see what doesn't convert:**

```
$ python3 scripts/md_to_docx.py q3-support-review-input.md -o q3-support-review.docx --brand ./brand/brand.json
WARN line 1: YAML front matter dropped (lines 1-4); its title is used as the document title
WARN line 48: raw HTML block dropped
WARN line 54: footnote definition dropped (footnotes are not supported)
WARN line 36: footnote reference [^1] dropped
wrote q3-support-review.docx (5 headings, 5 paragraphs, 2 lists, 1 table, 1 code block, 1 image, 2 links, 1 quote, page letter; brand: Georgia / Arial)
  title: Northwind Support — Q3 Review
4 warning(s): the items above were dropped or changed; tell the user before sharing
```

**Fixed the source in a copy** (`q3-support-review-fixed.md`), changing formatting only:

```diff
- > — from the September survey[^1]
+ > — from the September survey (214 responses, 31% response rate)
- <div class="callout">Draft — not yet reviewed by Legal.</div>
+ > **Draft:** not yet reviewed by Legal.
- [^1]: 214 responses, 31% response rate.
```

**Second run:**

```
$ python3 scripts/md_to_docx.py q3-support-review-fixed.md -o q3-support-review.docx --brand ./brand/brand.json
WARN line 1: YAML front matter dropped (lines 1-4); its title is used as the document title
wrote q3-support-review.docx (5 headings, 6 paragraphs, 2 lists, 1 table, 1 code block, 1 image, 2 links, 2 quotes, page letter; brand: Georgia / Arial)
  title: Northwind Support — Q3 Review
1 warning(s): the items above were dropped or changed; tell the user before sharing
```

The remaining warning is expected: the front matter isn't content, and its title went into
File > Properties.

**Checked it opens:**

```
$ textutil -convert txt q3-support-review.docx -stdout | head -4
Northwind Support: Q3 review
Prepared for the Acme account team. This review covers July to September and the three changes we propose for Q4. Raw numbers live in the support dashboard.
Summary
	•	First-response time fell from 6.1 to 3.4 hours
```

A Quick Look preview (`qlmanage -t`) shows green Georgia headings and Arial body text. The table
has a shaded header row and right-aligned numbers, and the 480 × 240 px chart (stored at 144
DPI) is centred at 3.3 × 1.7 in. The numbered proposals run 1 to 3, the "support dashboard" and
"the alias section" links are blue and underlined, and the quote is indented and italic.

---

## Reply to the user

> Here's the Word file: `q3-support-review.docx` (Letter, Northwind brand).
>
> **Changed so nothing was lost:** the survey footnote is now in brackets after the quote, and
> the "Draft, not yet reviewed by Legal" box is a quote line, because Word can't take the HTML
> box. No numbers or wording changed.
>
> **In Word:** the five headings show in the navigation pane. To add a contents page, use
> *References > Table of Contents*. The link to "the alias section" jumps to that heading.

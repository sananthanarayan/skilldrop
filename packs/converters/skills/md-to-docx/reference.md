# md-to-docx reference

How `scripts/md_to_docx.py` maps Markdown to Word, so you can predict the output and explain a
warning without reading the script.

## The package it writes

A `.docx` is a zip of XML parts. The script writes these and nothing else:

| Part | What it holds |
|---|---|
| `word/document.xml` | The body: paragraphs, runs, tables, drawings, bookmarks |
| `word/styles.xml` | Normal, Heading 1 to 4, Title, Quote, List Paragraph, Source Code, Hyperlink, Table Grid |
| `word/numbering.xml` | One bullet definition, plus one numbering definition per numbered list, so each list starts at its own number |
| `word/settings.xml` | Tab stops and compatibility mode (Word 2013 and later) |
| `word/_rels/document.xml.rels` | Links to styles, numbering, each hyperlink target and each image |
| `word/media/imageN.png` / `.jpeg` | The embedded images, byte for byte |
| `docProps/core.xml` | Title, created and modified time |

## Headings

Heading styles use Word's built-in style names (`heading 1` to `heading 4`) and carry an
outline level. That is what makes the navigation pane, *References > Table of Contents* and
"Heading" in the styles gallery work. A custom style that only looks like a heading does none of
this. Each heading also gets a bookmark named from its GitHub-style slug, so a link to `#retiring-the-alias`
becomes an internal link. A link to an anchor with no matching heading is kept as plain text, with a warning.

Title order: `--title`, then `title:` in YAML front matter, then the first `#` heading, then the
file name. The title goes into File > Properties; it doesn't add a line to the page.

## Lists

- A line is a list item when it starts with `-`, `*`, `+`, or a number followed by `.` or `)`.
- An item indented two or more spaces beyond the first item's marker is level 2. Anything deeper
  is flattened to level 2 with a warning: Word handles deep nesting, but a reader of a converted
  report rarely does.
- Level 1 numbers as `1.`, level 2 as `a.`. Bullets are `•` then `o`.
- A numbered list that starts at `3.` starts at 3 in Word.
- A code block or table inside a list item is written as plain text in the item, with a warning.
  Move it out of the list.

## Tables

The first row is the header: bold, shaded `F2F2F2`, and marked to repeat at the top of each page.
Alignment comes from the separator row (`:---` left, `---:` right, `:---:` centre). Columns are
equal width at first; Word's autofit adjusts them when the reader edits. A row with more or fewer
cells than the header is padded or cut, with a warning naming the row.

## Images

PNG and JPEG only. Size comes from the pixel dimensions and the DPI stored in the file (PNG
`pHYs`, JPEG JFIF). Without a stored DPI, 96 is assumed. An image wider than the text column
(6.5 in on Letter, 6.27 in on A4, with 1 in margins) is scaled down with its aspect ratio kept.
A paragraph that is only an image is centred. The alt text is stored as the picture description,
which screen readers read.

Not embedded, with a warning, and the alt text written in brackets instead: `http(s)://` and
`data:` images, missing files, GIF, SVG and WebP. Convert SVG to PNG first.

## Brand

`--brand` reads these brand.json fields from brand-kit, and ignores the rest:

| brand.json | Used for | Default |
|---|---|---|
| `fonts.heading.family` | Heading 1 to 4 and Title | Calibri |
| `fonts.body.family` | Normal text, lists, tables | Calibri |
| `colors.primary` | Heading colour | `#1F3864` |
| `colors.text` | Body text colour | `#222222` |

A colour that isn't a 6-digit hex code is ignored, with a warning. Fonts are named, not
embedded: a reader without the font sees Word's substitute. Brand fonts that are web-only
(Google Fonts not installed locally) fall back on the reader's machine, so tell the user.

## What is dropped, and why

| Construct | Why it's dropped | What to do instead |
|---|---|---|
| Raw HTML blocks | No dependable mapping from arbitrary HTML to Word | Rewrite as Markdown; HTML tables as pipe tables |
| Inline HTML tags | Same | The text is kept; `<br>` becomes a line break |
| Footnotes `[^1]` | Word footnotes need a separate part and are rarely worth it in a converted draft | Fold the note into the sentence, or a "Notes" section |
| Mermaid blocks | Rendering needs a browser engine | Render to PNG with mermaid-render, then embed the image |
| Nesting past 2 levels | Flattened to keep the document readable | Split with a sub-heading |
| YAML front matter | Not content | Its `title:` is used as the document title |

## Exit codes

`0` written (warnings may be printed); `1` bad input: file not found, not UTF-8, empty, binary,
output not ending in `.docx`, output folder missing, or brand.json not valid JSON.

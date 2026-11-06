# md-to-pptx reference

How `scripts/md_to_pptx.py` maps Markdown to slides, so the output can be predicted and a
warning explained without reading the script.

## What becomes what

| Markdown | In PowerPoint |
|---|---|
| `--title`, else the first `#` heading (when it is the first heading), else front matter `title:` | The title slide. Subtitle lines come from front matter `subtitle`, `author`, `presenter` and `date`, in that order, or from a single paragraph of 200 characters or fewer right under the `#` |
| Text between the `#` title and the first `##` (more than that one short paragraph) | A content slide titled with the deck title |
| `##` | A new slide on the *Title and Content* layout; the heading is the slide title |
| A later `#` with nothing under it before the next `##` | A section slide on the *Title Slide* layout |
| A later `#` with text under it | A content slide, like `##` |
| `###` to `######` | A bold line in the heading font and primary colour, kept with the item below it |
| `-` / `1.` lists, three levels | Bullets `•` `–` `◦`, numbers `1.` `a.` `i.`. A list starting at `3.` starts at 3. Level 4 and deeper are flattened to level 3, with a warning |
| `- [ ]`, `- [x]` | ☐ / ☒ before the item text |
| Paragraph | Body text, no bullet |
| `> quote` | Italic grey text, indented |
| Pipe table | A real table (`a:tbl`): shaded bold header row, banded rows, column alignment from the separator row |
| Fenced or indented code | A grey box in Consolas 14 pt, one paragraph per line |
| Local PNG / JPEG image | Embedded at its real size (from its DPI, 96 when none is stored), scaled down to fit and never up, centred, alt text kept as the picture description |
| `**bold**`, `*italic*`, `~~strike~~`, `` `code` `` | Bold, italic, strikethrough, Consolas |
| Links, `<https://…>`, bare URLs, `[text][ref]` | Clickable hyperlinks. `#heading-slug` jumps to the slide holding that heading |
| `---` | A new slide titled "<title> (continued)". Not reported as a split, because the author asked for it |
| `<!-- notes: ... -->` | Speaker notes for the slide the comment lands on. Several comments on one slide are joined |

**Why HTML comments for notes.** A comment is invisible when the Markdown is rendered, so it is
never content anyone meant the audience to read. A `Notes:` paragraph is ambiguous ("Notes:
figures exclude VAT"), so it stays on the slide and gets a warning. Put the comment right after
the heading to attach it to the first slide of a section that splits. One at the end lands on
the last continued slide.

## Slide geometry and text sizes

16:9 is 13.33 × 7.5 in; 4:3 is 10 × 7.5 in. Margins are 0.6 in at the sides. The title box sits
0.35 to 1.35 in from the top; the body runs from 1.45 to 7.05 in.

| Text | Size | Left margin |
|---|---|---|
| Slide title | 32 pt bold, heading font | 0 |
| Paragraph, level 1 item | 20 pt | 0 / 0.375 in |
| Level 2 item | 18 pt | 0.75 in |
| Level 3 item | 16 pt | 1.1 in |
| Subheading (`###`) | 22 pt bold | 0 |
| Table cells, code | 14 pt | |

These are fixed. Nothing is shrunk to fit. The body placeholder carries `normAutofit` so a
user who edits the slide in PowerPoint gets PowerPoint's usual behaviour from then on.

## How splitting decides

The script estimates each block's height: the number of wrapped lines, from the box width and
an average character width for the font (0.50 em for Calibri, Aptos and Segoe; 0.55 for Arial,
Georgia and most others; 0.60 for Verdana and Tahoma; 0.60 for code), times 1.2 × the font size,
plus the paragraph spacing. It packs blocks top to bottom into 96% of the body height and starts
a "(continued)" slide when the next block does not fit.

- **Text** splits between paragraphs or list items, never inside one. A subheading or a line
  ending in `:` moves to the next slide with the item it introduces. A nested line stays with
  the item above it: when a sub-bullet would start the next slide, the whole item moves, from
  its top-level line. The exception is an item taller than 80% of a slide, which breaks inside.
- **A section that splits is balanced.** It is packed again into up to 40% less height, in 5%
  steps, while it still takes the same number of slides. So the last slide isn't left
  holding one or two lines: three slides carry, say, 7, 7 and 6 items rather than 9, 9 and 2. A section with a `---` break isn't balanced,
  because the author placed the breaks.
- **Tables** split between rows, with the header row repeated, at least two rows per slide, and
  never one row left alone.
- **Code** splits between lines, at least three per slide, and never one or two left alone.
- **Images** shrink to the space left when at least 60% of their fitted size and 1.5 in remain;
  otherwise they move to the next slide.
- **An image under 64 pixels on a side** is embedded at its size, with a warning that it looks
  like a placeholder or a thumbnail: at 96 dpi an 8×6 image is a speck on the slide.
- **A single paragraph or table row taller than a slide** cannot split. It is placed alone and
  overflows, with a warning: break it into bullets.
- **A slide title over two lines** gets a warning. Titles are not shrunk either.

The estimate is deliberately cautious, so a slide can end with spare space at the bottom. It
should not overflow. If one does in PowerPoint, the font substituted was wider than the brand
font: install the font, or add a `---` above the line where it should break.

## Numbering

PowerPoint numbers list items itself, in order. The script carries the source's starting number
(`startAt`), keeps the count going across a continued slide, and keeps a run going past nested
items. A source that skips (`7.` then `9.`) shows `8.`, with a warning, because text that says
"go back to step 9" now points at a different step.

## Brand

`--brand` reads these fields and ignores the rest. The file is the same `brand.json` that the
Word converter and brand-kit use.

| brand.json | Used for | Default |
|---|---|---|
| `fonts.heading.family` (or `fonts.heading` as a string) | Theme heading font: titles, subheadings | Calibri |
| `fonts.body.family` (or `fonts.body`) | Theme body font: text, tables | Calibri |
| `colors.primary` | Titles, subheadings, table header fill, bullet colour | `#1F3864` |
| `colors.accent` | The short rule under each slide title | `#2E75B6` |
| `colors.text` | Body text | `#222222` |

A colour that isn't a 6-digit hex code keeps the default, with a warning. A primary lighter
than 3:1 contrast on white puts titles in the text colour, with a warning. The header row text
is white or near-black, whichever reads better on the primary. Fonts are named in the theme,
not embedded: a machine without the font shows a substitute, so a web-only brand font falls
back on the presenter's laptop.

## The package it writes

| Part | What it holds |
|---|---|
| `ppt/presentation.xml` | Slide list, slide size, notes size |
| `ppt/slideMasters/slideMaster1.xml` | Title and body placeholders, text styles for three list levels, the title rule |
| `ppt/slideLayouts/slideLayout1.xml`, `slideLayout2.xml` | *Title Slide* and *Title and Content* |
| `ppt/theme/theme1.xml` | Colours and fonts from the brand |
| `ppt/slides/slideN.xml` + `_rels` | Each slide, its images, hyperlinks and slide jumps |
| `ppt/notesMasters/notesMaster1.xml`, `ppt/theme/theme2.xml` | Only when a slide has notes |
| `ppt/notesSlides/notesSlideN.xml` + `_rels` | The notes for slide N |
| `ppt/media/imageN.png` / `.jpeg` | Embedded images, byte for byte, each stored once |
| `ppt/presProps.xml`, `viewProps.xml`, `tableStyles.xml` | Defaults PowerPoint expects |
| `docProps/core.xml`, `app.xml` | Title, created and modified time, slide and notes counts |

After writing, the script reopens the zip and checks that every XML part parses, every internal
relationship target exists, every `r:id` a part uses is defined, and every part has a content
type. A failure there exits 2 and is a bug in the script, not in the input.

## What is dropped or changed, and why

| Construct | What happens | What to do instead |
|---|---|---|
| Raw HTML blocks, other HTML comments | Dropped | Rewrite as Markdown; HTML tables as pipe tables |
| Inline HTML tags | Tags removed, text kept; `<br>` becomes a line break | |
| Footnotes `[^1]` | Dropped | Fold the note into the sentence, or into the slide's notes |
| Mermaid blocks | Kept as code text | Render to PNG, then embed the image |
| Remote, missing, GIF, SVG, WebP images | Alt text in brackets instead | Download or convert to PNG next to the Markdown |
| An image inside a text paragraph | Placed below the paragraph | |
| An image inside a list item or table cell | Alt text instead | Move it to its own line |
| Code or a table inside a list item | Plain text in the item | Move it out of the list |
| Link to `#anchor` with no heading | Plain text | Fix the slug |
| Link to a local file | Kept as a link, with a warning | The file is not inside the deck; link a shared copy |
| YAML front matter | Not a slide | Its title fields go on the title slide |

## Exit codes

`0` written (warnings may be printed); `1` bad input: file not found, not UTF-8, empty, binary,
output not ending in `.pptx`, output folder missing, or brand.json not a JSON object; `2` the
written file failed its own check.

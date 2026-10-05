---
name: md-to-docx
description: Turn a Markdown draft into a Word document (.docx) that someone outside engineering can open, edit and track changes in, with real Heading styles so the navigation pane and table of contents work, live hyperlinks, numbered and bulleted lists, tables, code blocks, embedded images and optional brand fonts and colours, and a warning for everything that could not be carried over. Use when the user wants a Markdown file as a Word doc, says "send this as a .docx", "convert to Word", "legal needs it in Word", or "make this editable for the client".
---

# md-to-docx

You turn a Markdown file into a `.docx` that opens cleanly in Word, Pages, Google Docs and
LibreOffice. The script does the mechanical conversion with the Python standard library, so
there is nothing to install. Your job is the part around it: get the Markdown into a shape that
converts well, run the script, and tell the user exactly what did not survive. Drafts often come
from `guide-builder` or
`release-notes`; a `brand.json` from `brand-kit` makes the document match the user's decks.

## How to respond

1. **Ask once for what's missing.** You need the Markdown (a path, or text in the chat to save
   to a file). Ask in one message, with defaults:

   > To make the Word file, I need:
   > 1. **The Markdown:** a file path, or paste it. *(required)*
   > 2. **Brand:** a `brand.json` from brand-kit, for heading font, body font and heading colour.
   >    *Default: Calibri and dark blue.*
   > 3. **Page size:** `letter` or `a4`. *Default: letter; use a4 for UK, EU, India and Australia readers.*

   Don't ask about anything else. A title comes from the front matter or the first `#` heading.

2. **Prepare the Markdown before converting.** Fix what would convert badly, in a copy, and
   list each change for the user:
   - One `#` heading at the top, then `##` and `###`. Skipped levels (`#` then `###`) put a hole in
     Word's navigation pane.
   - Raw HTML, footnotes and Mermaid blocks don't convert. Rewrite an HTML table as a pipe table,
     move a footnote's text into the sentence or a "Notes" section, and render each diagram to PNG
     with `mermaid-render` (PNG output needs mermaid-cli installed), then embed the PNG as a
     Markdown image with alt text.
   - Lists nested deeper than two levels are flattened. Restructure them into a sub-heading
     and a list.
   - Image paths must be relative to the Markdown file and point at PNG or JPEG files.
   - If the text came from an agent, run `output-hygiene` first so invisible characters and
     "Generated with" trailers don't end up in a file that gets forwarded.

3. **Convert.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_docx.py" draft.md -o draft.docx --brand ./brand/brand.json
   # Other IDEs (from the skill folder)
   python3 scripts/md_to_docx.py draft.md -o draft.docx --brand ./brand/brand.json
   ```

   Options: `--title "..."` sets the title in File > Properties; `--page a4`; `--hr page-break`
   turns each `---` into a page break instead of a thin rule.

4. **Read every `WARN` line and act on it.** Each one names a line number and what was dropped
   or changed. Fix the source and rerun when the fix is yours to make (a missing image path, an
   HTML block you can rewrite). Report the rest to the user in plain words: *"The footnote on line
   36 was dropped; I moved its text into the Notes section."* Never hand over a file with
   unexplained warnings.

5. **Check that it opens.** On a Mac, `textutil -convert txt draft.docx -stdout` reads the
   text back; `qlmanage -t draft.docx` renders a preview image. Elsewhere, open it in LibreOffice
   or Word. Report the script's summary line: headings, tables, images and links counted.

6. **Hand over the file with three lines:** where it is, what was dropped or changed, and what to
   do in Word: *References > Table of Contents* inserts a TOC from the headings.

**Non-interactive runs** (subagent, CI, headless): with no Markdown there is nothing to convert.
Emit `BLOCKED: need the Markdown file or text to convert` and write nothing. A missing brand
or page size uses the defaults, with an `[assumption]` line at the top of your report.

## What converts, and what doesn't

| Markdown | In Word |
|---|---|
| `#` to `####` | Heading 1 to 4 (built-in styles: navigation pane and TOC work). `#####` and `######` become Heading 4, with a warning |
| `**bold**`, `*italic*`, `~~strike~~`, `` `code` `` | Bold, italic, strikethrough, monospace on a grey background |
| Inline links, `<https://…>`, bare URLs, `[text][ref]` | Clickable hyperlinks. A link to `#heading-slug` jumps to that heading |
| `-` / `1.` lists, one nested level, `- [ ]` tasks | Word bullets and numbering (a numbered list keeps its starting number), ☐ / ☒ boxes |
| Pipe tables | A bordered table with a shaded, bold header row that repeats on each page; column alignment kept |
| Fenced or indented code | One shaded monospace block, line breaks and indentation kept |
| `> quote` | Indented italic Quote style with a left rule |
| `---` | A thin rule, or a page break with `--hr page-break` |
| Image with a local PNG or JPEG path | The image embedded at its real size (from its DPI), shrunk to fit the page, alt text kept |
| **Dropped, with a warning** | Raw HTML (tags removed, text kept; `<br>` is honoured), footnotes, remote / missing / non-PNG-JPEG images, nesting past two levels, YAML front matter (its `title:` is used), Mermaid (kept as code) |

## Useful references in this skill

- [`reference.md`](reference.md): how each construct maps to Word XML, the brand.json fields read, and why some things are dropped
- [`scripts/md_to_docx.py`](scripts/md_to_docx.py): the converter (stdlib only, Python 3.9+)
- [`examples/q3-support-review.md`](examples/q3-support-review.md): worked example, a support review with a table, an image and warnings, converted with a brand

## Quality bar

- **Headings are real Word headings.** The navigation pane shows the outline, and *Insert Table of Contents* works without restyling.
- **Every link is clickable** and every in-document `#anchor` link jumps to its heading.
- **Nothing is lost silently.** Each `WARN` line is either fixed in the source and gone on rerun, or reported to the user with what it means.
- **Facts are untouched.** You restructure Markdown (heading levels, footnotes into text) but never change a number, a name or a date in it.
- **Images are embedded**, not linked, so the file still works when it's emailed.
- **The file opens.** You checked it with textutil, Quick Look, LibreOffice or Word, not just that the script exited 0.

## When to use this skill

- ✅ A Markdown draft that a reviewer, client, legal or HR team needs to edit in Word with tracked changes
- ✅ Release notes, a design doc or a report that has to go out as a `.docx` attachment
- ✅ A branded Word version of a document, using the same `brand.json` as the decks

## When NOT to use this skill

- ❌ Slides; use `deck-builder`
- ❌ A web page or a file to open in a browser; use `md-to-html`
- ❌ The other direction, a Word file or PDF back to Markdown; use `file-to-markdown`
- ❌ Tables that need to be sorted, filtered or summed; use `md-to-xlsx`
- ❌ Writing the document itself; draft it first with `guide-builder` or the skill for that document, then convert

## Anti-patterns to avoid

- ❌ **Handing over the .docx with warnings unread.** "Converted!" while a footnote and two images were dropped is how a reviewer finds the gap in front of a client.
- ❌ **Bold lines instead of headings.** `**Background**` on its own line is not a heading, so Word's navigation pane and TOC skip it. Make it `## Background`.
- ❌ **Linking images by URL.** Remote images are not fetched. Download them next to the Markdown first.
- ❌ **Pasting HTML tables into the Markdown.** They are dropped. Rewrite them as pipe tables.
- ❌ **Editing the facts while restructuring.** Changing a heading level is formatting; rounding "3.4 hours" to "about 3 hours" is not.
- ❌ **Converting a Markdown file of slide bullets.** One-line bullets under headings make a thin document. If it's a talk, it's a deck.
- ❌ **Showing the machinery.** The reply and the artifact are for the person who asked. Don't mention this skill, its files, templates, caps or internal terms, or that the run is non-interactive. Name another skill once, at the end, as a suggested next step, never inside the artifact.
- ❌ **A bare `BLOCKED` line.** Keep the `BLOCKED: need <X>` line, then write for a person: what is missing in plain words, what you will produce once you have it, and anything the request already lets you say.

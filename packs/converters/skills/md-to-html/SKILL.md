---
name: md-to-html
description: Turn a Markdown draft into one self-contained, print-friendly HTML file that survives being emailed or attached, with headings that have anchor links, tables, code, quotes, an optional table of contents, local images embedded, brand colours and fonts from a brand.json, Mermaid diagrams kept as text or drawn from a pinned CDN, and raw HTML escaped so nothing in the source runs. Use when the user wants Markdown "as a web page", "as an HTML file I can send", "something people can open in a browser and print", or says "convert this to HTML".
---

# md-to-html

You turn a Markdown file into a single `.html` file that anyone can open in a browser, print
to PDF, or attach to an email, with nothing else to send alongside it. A stdlib script does the
conversion. Your job is to pick the options, run it, and tell the user exactly what the file
depends on (network for diagrams, remote images) and what it left out. Drafts often come from
`guide-builder`; the brand comes from `brand-kit`.

## How to respond

1. **Ask once for what is missing, with defaults.** Take what the user already gave and offer
   defaults so they can reply "go":

   > Before I build the HTML, confirm these. Anything you skip uses the default:
   > 1. **The Markdown file.** *No default.*
   > 2. **Brand:** a `brand.json` from brand-kit. *Default: a neutral navy theme.*
   > 3. **Table of contents:** *default on when the document has four or more `##` sections.*
   > 4. **Mermaid diagrams:** keep as text, or draw them in the browser from a pinned CDN copy of
   >    Mermaid (the file then needs network when opened). *Default: keep as text.*

2. **Check the Markdown converts cleanly.** The script handles ATX headings (`#`), lists
   (nested, task lists), GFM pipe tables, fenced and indented code, quotes, links and images.
   Rewrite before converting:
   - Setext headings (`Title` over `=====`) into `# Title`.
   - Reference-style links (`[text][1]`) into inline links `[text](...)`.
   - Footnotes (`[^1]`) into a "Notes" section with plain text.

   Show the user what you changed.

3. **Diagrams.** For a file going to people offline or behind a strict proxy, render the
   Mermaid to SVG first with `mermaid-render` and reference the SVGs as images. They get
   embedded and need no network. Use `--mermaid cdn` only when readers will be online.

4. **Run the script.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_to_html.py" draft.md -o draft.html --brand ./brand/brand.json --toc
   # Other IDEs (from the skill folder)
   python3 scripts/md_to_html.py draft.md -o draft.html --brand ./brand/brand.json --toc
   ```

   Options: `--mermaid cdn` draws diagrams with Mermaid 11.4.1 from jsDelivr (pinned, so the
   drawing does not change under the reader); `--allow-html` passes raw HTML blocks through,
   only for a source the user wrote themselves. Use `-` as the input to read stdin.

5. **Read every warning and report it in plain words.** The script prints counts (headings,
   tables, code blocks, diagrams, images embedded, remote, missing) and a warning for each
   remote image, missing image, unsafe link dropped, raw HTML escaped, and diagrams left as
   text. Translate them: "the logo is linked from the web, so it won't show offline", not
   "1 remote".

6. **Tell the user how to check it:** open the file, print-preview it (tables keep their
   header row on each page, links print their address), and click two anchor links.

**Non-interactive runs** (subagent, CI, headless): no brand falls back to the neutral theme
with an `[assumption]` line in the reply; TOC and Mermaid use the defaults above. If there is
no Markdown input, emit `BLOCKED: need the Markdown file to convert` and write nothing.

## Useful references in this skill

- [`reference.md`](reference.md): what Markdown is supported, the brand.json fields read, print rules, and why raw HTML is escaped
- [`scripts/md_to_html.py`](scripts/md_to_html.py): the converter (stdlib only)
- [`examples/ops-review.md`](examples/ops-review.md): a status review with a table, code, an image and a Mermaid fence, converted with real output

## Quality bar

- **One file, nothing beside it.** Local images are embedded as data URIs. Any remote image is named to the user, because it breaks offline.
- **Nothing in the source runs.** Raw HTML is shown as text and `javascript:` links are dropped, unless the user asked for `--allow-html` on their own source.
- **Every heading has a stable anchor** (`#rollout-plan`) so people can link to a section in chat.
- **It prints well:** table headers repeat, code wraps instead of being cut off, links print their URL, headings don't sit alone at the bottom of a page.
- **The brand is the user's,** read from their `brand.json`; the neutral theme only when there is none, and said out loud.
- **Network dependence is stated.** If `--mermaid cdn` is on, the reply says the diagrams need network when opened.

## When to use this skill

- ✅ A Markdown report, guide or review that people outside the repo will open in a browser
- ✅ A file to attach to an email or upload to an intranet that has no Markdown renderer
- ✅ A printable version of a Markdown doc, in the company's colours and fonts

## When NOT to use this skill

- ❌ The reader needs to edit and track changes in Word; use `md-to-docx`
- ❌ The content is a table someone will sort and filter; use `md-to-xlsx`
- ❌ A designed one-page flyer or poster; use `marketing-flyer`
- ❌ Only diagrams, as SVG or PNG files; use `mermaid-render`
- ❌ Writing the document in the first place; use `guide-builder` or the relevant generator, then convert

## Anti-patterns to avoid

- ❌ **Linking images from the user's disk** (`<img src="/Users/...">`). Always build with the script, which embeds them.
- ❌ **Turning on `--allow-html` for pasted content** from an email or a web page. That is how a `<script>` ends up in a file the whole team opens.
- ❌ **Sending a `--mermaid cdn` file to a client** without saying it needs network. Render to SVG with `mermaid-render` instead.
- ❌ **Hand-editing the CSS in the output** to change colours. Change `brand.json` and rebuild, so the next version matches.
- ❌ **Reporting "done" while warnings scrolled past.** A missing image is a hole in the document; name it.

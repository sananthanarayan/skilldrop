# md-to-html reference

## Markdown the script supports

| Construct | Supported | Notes |
|---|---|---|
| ATX headings `#` to `######` | ✅ | Each gets an `id` from its text (`## Rollout plan` becomes `#rollout-plan`); duplicates get `-1`, `-2` |
| Setext headings (`Title` over `===`) | ❌ | Comes through as a paragraph. Rewrite as `# Title` |
| Paragraphs, hard breaks (two trailing spaces or `\`) | ✅ | |
| `**bold**`, `*italic*`, `_italic_`, `~~strike~~`, `` `code` `` | ✅ | |
| Links `[text](...)` with an optional `"title"`, `<https://…>`, bare `https://…` | ✅ | `javascript:`, `vbscript:` and non-image `data:` targets are dropped with a warning |
| Reference links `[text][id]` | ❌ | Rewrite as inline links |
| Images `![alt](...)` | ✅ | Local files embedded as data URIs; remote URLs kept and warned about; missing files shown as `[image not found: alt]` |
| Ordered, unordered, nested lists; `- [ ]` task lists | ✅ | A blank line between items makes the list loose (each item a paragraph) |
| GFM pipe tables with `:---:` alignment | ✅ | `\|` for a literal pipe; pipes inside `` `code` `` are kept |
| Fenced code (```` ``` ```` or `~~~`) with a language | ✅ | `class="language-x"` on the `<code>`, no colouring |
| Indented code (4 spaces) | ✅ | |
| Blockquotes `>` | ✅ | Nested Markdown inside is rendered |
| `---` / `***` rules | ✅ | |
| YAML front matter at the top | ✅ | Removed from the output |
| Footnotes `[^1]`, definition lists, math | ❌ | Plain text. Rewrite footnotes as a Notes section |
| Raw HTML | Escaped | Shown as text; see below |

## Why raw HTML is escaped by default

The output is usually shared: attached to email, uploaded to an intranet, opened by people who
did not write the source. Markdown drafts pick up pasted HTML from emails, web pages and other
tools, and a `<script>`, an `onerror=` attribute or a `<form>` in that paste would run in every
reader's browser. Escaping shows the HTML as text, so nothing is lost and nothing runs.
`--allow-html` passes raw HTML *blocks* through (a line that starts with a tag, up to the next
blank line). Inline tags inside a paragraph stay escaped either way.

The file also carries a Content-Security-Policy that allows no scripts at all, or, with
`--mermaid cdn`, only the one Mermaid loader (by hash) and jsDelivr.

## brand.json fields read

From the `brand-kit` shape:

| Field | Used for |
|---|---|
| `colors.primary` | Headings, table header background, the header rule |
| `colors.secondary` | Links |
| `colors.accent` | Blockquote bar |
| `colors.background`, `colors.text` | Page background and body text |
| `fonts.heading.family` + `fallback` | Headings |
| `fonts.body.family` + `fallback` | Body text |
| `logo.primary` | Embedded at the top of the page, path relative to brand.json |
| `legal.footer` | Footer line |

A colour that is not a hex code is ignored with a warning. Fonts are named, not embedded: the
reader's machine must have them, or the fallback is used. Say so when the brand font is not a
common system font.

## Print rules in the stylesheet

- Page margins 18 mm top and bottom, 16 mm left and right; body text 11 pt.
- Table header rows repeat on every page; tables, code blocks, quotes and images avoid page breaks inside.
- Headings avoid being the last line on a page.
- Code wraps instead of running off the page.
- External links print their address after the link text.
- Anchor `#` markers are hidden.

## Mermaid

| Mode | What the reader sees | Needs network |
|---|---|---|
| default (`--mermaid none`) | The diagram source in a box | No |
| `--mermaid cdn` | The drawn diagram, by Mermaid 11.4.1 from jsDelivr, pinned to that exact version | Yes, each time the file is opened |
| Pre-render with `mermaid-render`, reference the SVG as an image | The drawn diagram, embedded | No |

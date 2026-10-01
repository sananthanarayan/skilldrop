---
name: deck-builder
description: Generate a real PowerPoint (.pptx) file from content, audience, and either a brand template or a color palette — with charts, tables and images, not only bullets. Slide count, density and layout are tuned to the audience: execs, boards, technical reviewers, sales prospects, investors, internal teams. Use when the user wants an actual editable .pptx rather than an outline, wants their corporate template or brand colours applied, or says "build the deck", "make it a pptx", "use our template".
---

# deck-builder

This skill produces an **actual editable `.pptx` file**, not an outline. It runs `python-pptx`
to materialise slides — either on a brand template's own masters and layouts, or on the skill's
built-in design in the user's brand: their colours, logo and fonts.

It pairs with three others:
- **[`brand-kit`](../brand-kit/SKILL.md)** — captures the brand once as a `brand.json` this skill reads, so nobody answers the brand questions for every deck
- **[`audience-profile`](../../../stakeholder-comms/skills/audience-profile/SKILL.md)** — decides how dense, how many, which sections
- **[`slide-outliner`](../slide-outliner/SKILL.md)** — drafts per-slide content before this skill builds it

For a single fast pipeline, run all three in order: profile → outline → build.

## How to respond

### 1. Run the setup block — once

Ask everything in **one** message, with defaults already chosen, so the user can answer with a
single line or say "go". Never trickle out four separate questions, and never generate a deck
with the design silently defaulted.

> Before I build, confirm these — reply "go" to take the defaults:
> 1. **Audience** — `exec` · `board` · `technical` · `sales` · `internal` · `investor` · `partner` · `customer`
> 2. **Format** — live presentation / read-ahead / async share, **how many minutes**, and **16:9** (default) or **4:3**
> 3. **Brand** — the deck should look like it came from your team. Send any of:
>    - a **`brand.json`** from brand-kit, which covers everything below in one file;
>    - a **template**: path to a corporate `.pptx` / `.potx`, and the deck inherits its masters, fonts, colours, logo and slide size;
>    - your **logo** as a PNG (and a white version for dark slides), **brand colours** as hex values for `primary` / `secondary` / `accent` / `background` / `text`, and your **heading and body fonts**;
>    - or, with no brand, a named **palette**: `corporate-blue` (default for B2B) · `monochrome` · `vibrant` · `dark-mode` · `editorial` · `forest` · `sunset`
> 4. **Anything to embed** — numbers to chart, a table, diagram PNGs

Rules for reading the answers:

- **Content is the one hard input.** If the user supplied only a topic, stop and ask for the
  material. Inventing the content is the easiest way to produce a bad deck.
- **A free-form audience maps to the closest archetype** — "VP of Eng and their staff at a
  partner" → `technical`, stated out loud. Mixed audience → the least technical archetype, with
  the rest served by appendix slides.
- **Time sets slide count**, not the other way round: 1.5–2 minutes per slide live. 30 minutes →
  12–15 slides including cover and close.
- **A partial brand palette gets completed**, using the rules in
  [`reference.md`](reference.md#color-palette-principles) — say which roles were filled in.
- **Template beats palette** for chrome; the palette still colours charts, tables, big numbers
  and quote bars, so ask for brand hexes even when a template is supplied.
- **Brand material beats a named palette.** If the user sent a logo or brand colours, never fall
  back to `corporate-blue`. If they have brand material but no `brand.json`, suggest running
  `brand-kit` first, so the next deck and any flyer match this one.
- **Logos must be PNG or JPG.** PowerPoint can't place SVG or EPS: ask for a PNG export, and
  never build with the logo silently missing.

**Non-interactive runs** (subagent, CI, headless): audience, format, time and palette degrade to
`[assumption]` lines stated at the top of the response — default `exec`, live, 16:9,
`corporate-blue`, or the `brand.json` when one is in the input. Never invent a logo or brand colour. Missing *content* does not degrade: emit `BLOCKED: need deck content
(outline, doc, or point list)` and build nothing.

### 2. Plan the slide list against the audience archetype

| Audience | Slide count | Density | Required sections |
|---|---|---|---|
| `exec` | 6–10 | Low — 3 bullets max | Ask • TL;DR • Business impact • Risks • Ask (closing) |
| `board` | 8–12 | Low — big numbers | Cover • TL;DR • Strategic context • Financials • Risks • Ask |
| `technical` | 12–20 | High — detail welcome | Context • Goals • Proposal (3–5) • Alternatives • Risks • Rollout |
| `sales` | 8–12 | Story arc, visual | Hook • Pain • Solution • Proof • Pricing • Close |
| `internal` | 5–10 | Mixed | Context • Proposal • Discussion topics • Action items |
| `investor` | 10–15 | Polished, narrative | Problem • Market • Product • Traction • Team • Ask |

Full archetype spec: [`audience-profile`](../../../stakeholder-comms/skills/audience-profile/SKILL.md). Slide-count budgets per
format and time: [`reference.md`](reference.md#slide-count-budgets).

### 3. Build a deck spec

A JSON document — full schema, with every layout and the template block, in
[`templates/deck-spec.json`](templates/deck-spec.json):

```json
{
  "title": "ProjectX Migration — Board Update",
  "audience": "board",
  "aspect": "16:9",
  "template": "./brand/acme-master.potx",
  "layout_map": { "title": "Title Slide", "content": "Title and Content" },
  "palette": { "primary": "#1A2A6C", "accent": "#FDBB2D" },
  "brand": "./brand/brand.json",
  "slides": [
    { "layout": "title", "title": "...", "subtitle": "...", "presenter": "...", "date": "..." },
    { "layout": "content", "title": "...", "bullets": ["..."], "notes": "..." },
    { "layout": "chart", "title": "...", "takeaway": "...", "chart": { "type": "column", "categories": ["..."], "series": [{ "name": "...", "values": [1, 2] }] }, "source": "..." },
    { "layout": "table", "title": "...", "columns": ["..."], "rows": [["..."]] },
    { "layout": "image", "title": "...", "image": "./diagram.png", "position": "right", "bullets": ["..."] },
    { "layout": "big_number", "title": "...", "number": "$24M", "caption": "ARR at risk" },
    { "layout": "closing", "title": "Approval requested", "subtitle": "..." }
  ]
}
```

Ten layouts: `title`, `section`, `content`, `two_column`, `big_number`, `quote`, `image`,
`table`, `chart`, `closing`. Most slides are `content`; `chart`, `table` and `big_number` carry
the evidence; `quote` and `image` break the rhythm. Which content shape earns which layout:
[`reference.md`](reference.md#layout--content-matching).

Every slide gets a `notes` field. Slide numbers appear automatically past 10 slides — override
with `"slide_numbers": false`.

### 4. Build from the user's template when there is one

A corporate template is the difference between a deck that gets presented and one that gets
rebuilt by hand. When the user names one:

```bash
# Claude Code — list the template's layouts first
python3 "${CLAUDE_SKILL_DIR}/scripts/build_deck.py" --list-layouts ~/brand/acme-master.potx

# Other IDEs (from the skill folder)
python3 scripts/build_deck.py --list-layouts ~/brand/acme-master.potx
```

Map each logical layout to one of the printed names in `layout_map`, then build. The template's
masters, theme fonts, colours, logos and slide size are inherited; any sample slides it ships
with are dropped. A logical layout left out of the map falls back to the skill's built-in
design on the template's blank layout — acceptable for `big_number` or `quote`, wrong for
`title` and `content`, which is where the branding shows.

`.potx` and `.pptx` both work. Templates carry no charts or tables of their own, so those are
drawn into whatever content region the mapped layout defines.

### 5. Run the build script

```bash
# Claude Code
python3 "${CLAUDE_SKILL_DIR}/scripts/build_deck.py" /tmp/deck-spec.json -o ./out/deck.pptx

# Other IDEs (from the skill folder)
cd path/to/deck-builder && python3 scripts/build_deck.py /tmp/deck-spec.json -o ./out/deck.pptx
```

Add `--brand ./brand/brand.json` to build in the user's brand (or set `"brand"` in the spec).
The brand fills whatever the spec leaves out: palette colours, the template, logo files and
fonts. On the built-in design the logo goes on every slide: large on the cover, small in the
lower-left corner elsewhere, and the on-dark version on dark section and closing slides. The
brand's heading and body fonts are applied to titles, text, tables and charts. A template
already carries its own logo and fonts, so they come from the template instead.

Add `--strict` to fail the build on a missing or unreadable image instead of drawing a
placeholder box — use it in CI, not in a conversation.

**Read the warnings.** The script degrades rather than crashing: a missing image, a short data
series, an unresolvable template layout each produce a warning and a visible fallback. Report
every warning to the user with the file path; never present a deck with an unexplained
placeholder box in it.

### 6. Recommend the refinement pass

A generated deck is a strong first draft. Always tell the user to:

- Review the speaker notes — the agent wrote them, and they get read aloud
- Replace any placeholder box with the real diagram
- Do one audience pass: read every slide title in order, does the *narrative* land for that audience?
- Run [`doc-critique`](../../../core/skills/doc-critique/SKILL.md) against the deck rubric before it goes out

## Useful references

- [`reference.md`](reference.md) — palette principles, layout-vs-content matching, chart and table rules, density and slide-count budgets
- [`templates/deck-spec.json`](templates/deck-spec.json) — full JSON schema with every layout and the template block
- [`templates/palettes.json`](templates/palettes.json) — the seven presets
- [`examples/exec-board-update.md`](examples/exec-board-update.md) — worked example: brief → spec → deck
- [`examples/templated-brand-deck.md`](examples/templated-brand-deck.md) — worked example: corporate `.potx` → layout map → deck
- [`scripts/build_deck.py`](scripts/build_deck.py) — the generator (don't edit unless adding a layout)

## Quality bar

- **Design is chosen by the user, never silently defaulted** — a `brand.json`, a template, brand colours and logo, or a named palette, confirmed in the setup block.
- **The user's brand shows on every slide** — their logo (PNG) and colours, and their fonts when they gave them. A deck built from brand material that comes out in `corporate-blue` has failed.
- **A supplied template is actually inherited** — `layout_map` covers `title`, `section`, `content` and `closing` at minimum. A branded deck rendered on the blank layout has thrown away the branding.
- **Title slide isn't blank** — real title, subtitle, presenter, date.
- **Numbers are charted, not bulleted** — three or more comparable figures belong in a `chart` or a `table`, not a bullet list.
- **Every chart and table cites its `source`** and uses only figures from the user's material.
- **Bullet density matches audience** — `exec`, *3 bullets max*, period. `technical`, up to 6 when the content needs it.
- **Speaker notes on every slide** — even one sentence.
- **Section dividers used sparingly** — at most one every 4–5 content slides.
- **Zero unexplained warnings** — every warning the script emits is fixed or reported to the user.
- **Colour is consistent** — palette roles only, no stray colours; text-on-background contrast ≥ 4.5:1.

## Anti-patterns to avoid

- ❌ Ignoring a template the user already named, or asking for a palette after they supplied one. The template is the answer to "what should this look like".
- ❌ Asking for brand colours when a `brand.json` was supplied, or building without the logo because it was an SVG. Ask for a PNG export instead.
- ❌ Mapping every logical layout onto the template's one title-and-bullets layout. That is a branded deck that still looks generated.
- ❌ Generating without confirming audience. The same content for execs and engineers is a different deck.
- ❌ Inventing a statistic to fill a `big_number`, or a series to fill a chart. No source, no chart.
- ❌ A table with 20 rows. Over ~12 it is an appendix or a spreadsheet, not a slide.
- ❌ Passing an SVG or EMF diagram to `image` — `python-pptx` reads raster only. Convert to PNG first.
- ❌ Shipping the deck with a grey placeholder box still in it because the warning went unread.
- ❌ Defaulting to bullets when a `big_number`, `chart`, `quote` or `two_column` would land harder.
- ❌ More than ~20 slides for any audience. If the point needs 21, the deck is the wrong format.

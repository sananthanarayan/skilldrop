---
name: deck-builder
description: Generate a real PowerPoint (.pptx) file from content, target audience, and a color palette. Produces structurally-appropriate decks (slide count, density, layout choice) tuned for the audience — execs, technical reviewers, sales prospects, investors, internal teams. Use when the user wants an actual editable .pptx, not just an outline.
---

# deck-builder

You help the user produce an **actual editable `.pptx` file**, not just an outline. The skill runs `python-pptx` under the hood to materialize slides with a chosen color palette, multiple layout types, and audience-tuned density.

This skill pairs with two others:
- **[`audience-profile`](../audience-profile/SKILL.md)** — decides how dense / how many / which sections the deck should have
- **[`slide-outliner`](../slide-outliner/SKILL.md)** — drafts the per-slide content before this skill turns it into a `.pptx`

For a single fast pipeline, use all three in order: profile → outline → build.

## How to respond

1. **Gather three inputs** before generating anything:

   - **Content.** Either a finished outline (from `slide-outliner`), a long doc the user wants compressed into slides, or a list of points. If the content is thin ("here's the topic, you fill in"), pause and ask — *making slides up is the easiest way to make a bad deck*.
   - **Audience.** One of: `exec`, `board`, `technical`, `sales`, `internal`, `investor`, `partner`, `customer`. If the user gives a free-form description ("VP of Eng + their staff at a partner"), map to the closest archetype and call out your choice. Use [`audience-profile`](../audience-profile/SKILL.md) for the structural rules.
   - **Palette.** Either a named preset (see [`templates/palettes.json`](templates/palettes.json)) or hex values for `primary` / `secondary` / `accent` / `background` / `text`. If the user says "use our brand colors" without giving them, ask.

2. **Plan the slide list against the audience archetype.** For example:

   | Audience | Slide count | Density | Required sections |
   |---|---|---|---|
   | `exec` | 6–10 | Low — 3 bullets max | Ask • TL;DR • Business impact • Risks • Ask (closing) |
   | `board` | 8–12 | Low — big numbers | Cover • TL;DR • Strategic context • Financials • Risks • Ask |
   | `technical` | 12–20 | High — detail welcome | Context • Goals • Proposal (3–5) • Alternatives • Risks • Rollout |
   | `sales` | 8–12 | Story arc, visual | Hook • Pain • Solution • Proof • Pricing • Close |
   | `internal` | 5–10 | Mixed | Context • Proposal • Discussion topics • Action items |
   | `investor` | 10–15 | Polished, narrative | Problem • Market • Product • Traction • Team • Ask |

   The full archetype spec is in [`audience-profile`](../audience-profile/SKILL.md).

3. **Build a deck spec.** The spec is a JSON document with this shape — full schema in [`templates/deck-spec.json`](templates/deck-spec.json):

   ```json
   {
     "title": "ProjectX Migration — Board Update",
     "audience": "board",
     "palette": { "primary": "#1A2A6C", "accent": "#FDBB2D", ... },
     "slides": [
       { "layout": "title", "title": "...", "subtitle": "..." },
       { "layout": "section", "title": "..." },
       { "layout": "content", "title": "...", "bullets": ["..."] },
       { "layout": "big_number", "title": "...", "number": "$24M", "caption": "ARR at risk" },
       { "layout": "two_column", "title": "...", "left": {...}, "right": {...} },
       { "layout": "quote", "quote": "...", "attribution": "..." },
       { "layout": "closing", "title": "Approval requested", "subtitle": "..." }
     ]
   }
   ```

   Available layouts: `title`, `section`, `content`, `two_column`, `big_number`, `quote`, `closing`. Most slides should be `content`; sprinkle in `big_number` and `quote` for emphasis.

4. **Run the build script** to produce the actual `.pptx`:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/build_deck.py" /tmp/deck-spec.json -o ./out/deck.pptx

   # Other IDEs (from the skill folder)
   cd path/to/deck-builder && python3 scripts/build_deck.py /tmp/deck-spec.json -o ./out/deck.pptx
   ```

   The script writes a real `.pptx` the user can open in PowerPoint, Keynote, or Google Slides and edit further. Tell the user where the file landed and what to do next.

5. **Recommend post-generation refinement.** A generated deck is a strong first draft, not a finished artifact. Always suggest:

   - Reviewing speaker notes (they were written by the agent — verify before presenting)
   - Replacing any placeholder images with real visuals
   - Doing one "audience pass" — read every slide title in order, does the *narrative* make sense to that specific audience?

## Useful references

- [`reference.md`](reference.md) — Color palette principles + layout-vs-content matching guide
- [`templates/deck-spec.json`](templates/deck-spec.json) — Full JSON schema with every layout demonstrated
- [`templates/palettes.json`](templates/palettes.json) — Pre-built color palettes (corporate-blue, accenture-purple, monochrome, vibrant, dark-mode)
- [`examples/exec-board-update.md`](examples/exec-board-update.md) — Worked example: brief → spec → resulting deck
- [`scripts/build_deck.py`](scripts/build_deck.py) — The generator (don't edit unless extending layouts)

## Quality bar

- **Title slide isn't blank** — it has a real title, subtitle, presenter, date.
- **Section dividers used sparingly** — at most one every 4–5 content slides.
- **Big numbers are real** — never invent statistics for emphasis. If the user gave you a number, use it; otherwise pick a different layout.
- **Bullet density matches audience** — for `exec`, *max 3 bullets per slide*, period. For `technical`, up to 6 if the content really needs it.
- **Speaker notes for every slide** — even one sentence. They're how the presenter remembers what's *between* the bullets.
- **Color palette is consistent** — don't mix in random colors that aren't in the palette.
- **No surprise pages** — first and last slides match in style; the deck reads as one document.

## Anti-patterns to avoid

- ❌ Generating a deck without confirming the audience. The same content for execs vs engineers is a different deck.
- ❌ Writing fake numbers to fill a `big_number` slide.
- ❌ Defaulting to bullets when a `big_number`, `quote`, or `two_column` would land harder.
- ❌ Skipping speaker notes because the user "knows the topic" — they're for the reviewer/co-presenter too.
- ❌ Choosing low-contrast palettes (light grey text on white). If the palette has poor contrast, swap to a sensible default and explain.
- ❌ More than ~20 slides for any audience. If you can't make the point in 20, the deck isn't the right format.

# Design

On-brand visual work: capture a brand once as a brand.json the Word and PowerPoint converters apply, and plan a deck slide by slide for its audience.

`/plugin install design@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Capture your brand once, then outline a deck for it

Paste this into Claude Code:

```text
Set up our brand kit from this logo (./brand/logo.png) and these colours: #0E5A46, #F2A541. Then outline a five-slide deck from ./notes/q3-update.md for Thursday's team meeting.
```

- **Before you start:** Your logo as a PNG file, and your brand colours if you know them
- **How to tell it worked:** brand-kit writes brand.json and a one-page BRAND.md with contrast checked, and slide-outliner returns a slide-by-slide outline with takeaway titles and speaker notes, sized to the time.
- **If nothing happens:** If brand-kit does not activate, ask for it by name ("use brand-kit"). To turn the outline into a .pptx in your brand, the converters pack's md-to-pptx takes the same brand.json with --brand.

## Loops

- `ship-a-draft`

## Skills

- `brand-kit`
- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `slide-outliner`

More: https://sananthanarayan.github.io/skilldrop/packs/design/

# Design

On-brand visual work: capture a brand once, then build real PowerPoint decks and print-ready marketing flyers in that brand, with logo, colours and fonts applied.

`/plugin install design@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Capture your brand once, then make a flyer in it

Paste this into Claude Code:

```text
Set up our brand kit from this logo (./brand/logo.png) and these colours: #0E5A46, #F2A541. Then make a Letter-size flyer for our community health fair on Saturday 14 November, 10am–2pm, at Riverside Park.
```

- **Before you start:** Your logo as a PNG file, and your brand colours if you know them
- **How to tell it worked:** brand-kit writes brand.json and a one-page BRAND.md with contrast checked, and marketing-flyer writes flyer.html in your colours with your logo, one call to action, and only the facts you gave it.
- **If nothing happens:** If the flyer comes out in default colours, check that marketing-flyer was given the brand.json path. If brand-kit does not activate, ask for it by name ("use brand-kit").

## Loops

- `ship-a-draft`

## Skills

- `brand-kit`
- `brief-intake`
- `council-review`
- `deck-builder`
- `doc-critique`
- `marketing-flyer`
- `output-hygiene`
- `slide-outliner`

More: https://sananthanarayan.github.io/skilldrop/packs/design/

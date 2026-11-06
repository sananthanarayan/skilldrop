# Interior designer

Furniture plans for one room: every piece at its real size and facing the way it's used, drawn as a dimensioned SVG, and shown only once a script has checked it for overlaps, pieces in a door's swing, blocked bed sides, chair pull-backs and wardrobe doors, and a clear walking route to everything.

`/plugin install interior-designer@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Get a checked, dimensioned furniture plan for one room

Paste this into Claude Code:

```text
Lay out our bedroom: 3.6 m wide × 3.3 m deep, door at the right end of the south wall opening in, window centred on the north wall with a 0.9 m sill. Furniture: a king bed (1.8 × 2.0 m), two nightstands, a 1.2 m wardrobe with hinged doors, and a small desk with a chair.
```

- **Before you start:** The room's width and depth, where its door and windows are, and the furniture you want in it
- **Before you start:** Python 3 on the machine, which the checker and drawing script run on
- **How to tell it worked:** furniture-layout states its zoning in a few lines, writes an SVG plan with the room's dimensions, every piece with its size, its clearances shaded and the walking route drawn, and says plainly what it changed or couldn't fit.
- **If nothing happens:** If furniture-layout does not activate, ask for it by name ("use furniture-layout"). If a piece won't fit, ask for the best smaller option, or say which piece may go.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `furniture-layout`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/interior-designer/

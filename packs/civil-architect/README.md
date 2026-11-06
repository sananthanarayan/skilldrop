# Civil architect

Building design from a client's room list and a footprint: a schematic floor plan placed at real sizes and drawn as a dimensioned SVG, shown only once a script has checked it for overlapping rooms, rooms outside the footprint, doors on no shared wall, rooms no one can reach and habitable rooms with no window.

`/plugin install civil-architect@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Get a checked, dimensioned concept plan from a room list and a footprint

Paste this into Claude Code:

```text
Draw a ground floor plan for a 10 m wide × 9 m deep footprint, road on the south, front door from the road. Rooms: foyer 6 m², living 26 m², dining 14 m², kitchen 12.6 m², utility 4 m² next to the kitchen, prayer room 4.5 m² not next to the kitchen or the toilet, guest toilet 3.2 m², and a stair. Living, dining, kitchen and prayer room need windows.
```

- **Before you start:** The rooms you need with their sizes, and the footprint's width and depth
- **Before you start:** Python 3 on the machine, which the checker and drawing script run on
- **How to tell it worked:** floor-plan-layout states its zoning in a few lines, writes an SVG plan with overall dimensions, room sizes and areas, door swings, windows, a scale bar and a north arrow, and shows a room table from a checker that reported no overlaps, every door on a shared wall and every room reachable.
- **If nothing happens:** If floor-plan-layout does not activate, ask for it by name ("use floor-plan-layout"). If the plan is too tight, ask for a second option with the rooms it may shrink named.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `floor-plan-layout`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/civil-architect/

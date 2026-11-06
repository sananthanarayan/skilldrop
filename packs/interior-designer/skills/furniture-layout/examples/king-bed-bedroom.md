# Worked example: a king bed that "fits" by area

Input → output oracle for `furniture-layout`. The room passes an area check easily: 11.9 m²
of floor for 5.2 m² of furniture. It fails twice on geometry before it passes. The first draft
puts the desk in the door's swing. The second leaves a 0.81 m diagonal between the desk and
the bed, under the 0.9 m walkway, so the wardrobe can't be reached. The answer keeps the king
bed and changes the one piece that can give: the desk.

## Input

> Lay out our bedroom: 3.6 m wide × 3.3 m deep, door at the right end of the south wall
> opening in, window centred on the north wall with a 0.9 m sill. Furniture: a king bed
> (1.8 × 2.0 m), two nightstands, a 1.2 m wardrobe with hinged doors, and a small desk with
> a chair.

## The zoning

- The bed's head goes on the north wall, under the window: it is the only wall long enough to
  give the bed 0.6 m on both sides.
- The wardrobe takes the west wall beside the bed, so its doors open into the bed's own side
  clearance, not into the route.
- The desk takes the south-west corner, away from the door's swing.
- The route runs from the door along the foot of the bed to both bed sides and the wardrobe.

## What the checker caught

**Draft 1** had the bed centred, the wardrobe on the west wall by the door, and the desk on the
east wall by the door:

```
FAIL Desk is in the swing of Door: the door can't open fully
FAIL nothing 0.90 m wide clears the way in at Door
```

**Draft 2** moved the bed 0.3 m east and the desk into the south-west corner, still at the
standard small-desk size of 1.0 × 0.5 m:

```
FAIL no clear 0.90 m route from the entrance reaches Wardrobe (its front side)
```

The desk's corner at (1.0, 0.5) and the bed's foot corner at (1.2, 1.3) leave a diagonal of
0.81 m. That's enough to squeeze past, but not the 0.9 m walkway. A 0.9 × 0.45 m desk
opens the gap to 0.94 m.

## The layout that passes

`layout.json` (excerpt):

```json
{
  "title": "Bedroom, 3.6 × 3.3 m: king bed, wardrobe and desk",
  "units": "m", "size": [3.6, 3.3],
  "doors": [{"name": "Door", "at": [3.1, 0], "width": 0.8, "hinge": "left", "swing": "in", "entrance": true}],
  "windows": [{"at": [1.8, 3.3], "width": 1.2, "sill": 0.9}],
  "furniture": [
    {"name": "King bed", "type": "bed", "width": 1.8, "depth": 2.0, "at": [1.2, 1.3], "facing": "S"},
    {"name": "Left nightstand", "type": "nightstand", "width": 0.45, "depth": 0.4, "at": [0.75, 2.9]},
    {"name": "Right nightstand", "type": "nightstand", "width": 0.45, "depth": 0.4, "at": [3.0, 2.9]},
    {"name": "Wardrobe", "type": "wardrobe", "width": 1.2, "depth": 0.6, "at": [0, 1.6], "facing": "E"},
    {"name": "Desk", "type": "desk", "width": 0.9, "depth": 0.45, "at": [0, 0], "facing": "N"}
  ]
}
```

```
| King bed | bed | 1.8 × 2 | 1.2, 1.3 | S | front 0.6, left 0.6, right 0.6 |
| Left nightstand | nightstand | 0.45 × 0.4 | 0.75, 2.9 | S | none |
| Right nightstand | nightstand | 0.45 × 0.4 | 3, 2.9 | S | none |
| Wardrobe | wardrobe | 1.2 × 0.6 | 0, 1.6 | E | front 0.6 |
| Desk | desk | 0.9 × 0.45 | 0, 0 | N | front 0.9 |

Floor 11.88 m² · furniture 5.09 m² (43 %) · walkway 0.90 m

PASS no overlaps, every piece in the room, no door swing blocked, every clearance clear,
every piece reached at the walkway width.
```

The drawing is [`king-bed-bedroom.svg`](king-bed-bedroom.svg).

## The reply

> **The plan is in `bedroom.svg`.** The king bed sits against the north wall under the
> window, the wardrobe on the west wall beside it, and the desk in the south-west corner.
> From the door there's a clear 0.9 m route along the foot of the bed to both sides and the
> wardrobe.
>
> | Piece | Size | Where |
> |---|---|---|
> | King bed | 1.8 × 2.0 m | head on the north wall, 1.2 m from the west wall |
> | Nightstands | 0.45 × 0.4 m | either side of the bed's head |
> | Wardrobe | 1.2 × 0.6 m | west wall, doors opening east beside the bed |
> | Desk | 0.9 × 0.45 m | south-west corner, chair facing the wall |
>
> **One change from what you asked:** the desk is 0.9 × 0.45 m, not a standard 1.0 × 0.5 m.
> At the standard size, its corner comes within 0.81 m of the bed's foot. You could squeeze
> past, but not walk through, to the wardrobe. If you'd rather keep a full-size desk, a
> queen bed (1.5 × 2.0 m) in the same place, its left edge 0.3 m further east, leaves room
> for it; that layout passes the same checks.
>
> **Assumed:** nightstands 0.45 × 0.4 m. The door is hinged on the east side as you face it
> from inside, swinging into the room.
>
> **This is a schematic.** It meets the clearances set here: 0.6 m beside and at the foot of
> the bed, 0.6 m in front of the wardrobe, 0.9 m behind the desk, and a 0.9 m route. It isn't
> a check against any building or accessibility code. Measure the real room, and the
> wardrobe's door width, before you buy.

## Why this is the oracle

- **Area is not fit.** 43 % coverage looks comfortable. The failures are a door swing and a
  0.81 m diagonal, which no area sum shows.
- **A layout is shown only after it passes,** and when the list doesn't fit as given, the
  reply names the piece, the number (0.81 m, not 0.9) and the smallest change that works.
- **The reply is for the client.** It gives a plan, a table, one change with its reason,
  the assumptions and what the plan is not. It never mentions the checker, the JSON or
  where the file was written from.

A cheaper pass answers "yes, it all fits: 5 m² of furniture in a 12 m² room". It then puts
the desk by the door, where the door hits it on every opening. Or it puts the full-size desk
in the corner and leaves a gap you turn sideways to get through to the wardrobe.

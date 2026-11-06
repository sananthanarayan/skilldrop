---
name: furniture-layout
description: Lay out the furniture in a room at real sizes and draw it as a dimensioned SVG, with a script that fails the layout when pieces overlap or leave the room, block a door's swing, or leave a walkway, bed side, chair pull-back or wheelchair turning space narrower than it needs. Use when a designer or homeowner asks to "lay out this living room", "will a king bed fit", "arrange the furniture", "plan this office for 8 desks", "check the clearances", or has a room's size, its doors and windows and a list of furniture.
---

# furniture-layout

A furniture plan for one room: every piece at its real size, facing the right way, with the
space each one needs to be used, and a clear way to walk to all of them from the door. The
agent does the design (zones, focal wall, what faces what); a script checks the geometry and
draws the plan, so a bed that blocks the wardrobe door or a sofa in the door's swing never
reaches the client. A whole-floor plan of rooms is `floor-plan-layout`; this skill furnishes
one room inside it.

## How to respond

**These rules come before the steps and outrank them:**

- **The client's pieces stay theirs.** Never swap, resize or drop a piece they chose, and
  never bring back one they refused. When their piece can't meet a clearance, keep it in the
  plan, mark the shortfall with its size (*"the bed leaves 0.55 m on the window side, not
  0.6"*), and offer a smaller piece only as a separate option.
- **Their file comes back in exactly its own shape.** A file the person gave returns with the
  same columns, column order, headers and row order, and only the cells that must change
  changed, ready to send. Every change is listed in the reply: the row, what changed and why.
  Add a change column only when they ask for one. Given a pasted list, reply with a table.
  One sendable drawing per room, of their actual layout.
- **A requirement is met only where it was tested.** A turning circle "in front of the WC
  door", "beside the bed" or "inside the bathroom" counts only when the check tested that
  zone (step 3). A circle that is clear somewhere else in the room meets nothing. Never call
  a requirement met that was tested in another place, or not at all; say which it is.
- **Working files stay out of sight.** The checker's input and any intermediate file go in a
  private temporary folder made for this run alone (`mktemp -d`, never a fixed path such as `/tmp/layout`, which another session can read or overwrite), and are deleted before you reply. Never overwrite a file the person gave you: write the corrected copy beside it under a plain name (`rota-fixed.csv`), and leave theirs as it was. Never
  leave anything running in the background.
- **The drawing says what the text says.** Every piece on the list is drawn, chairs included.
  A turning circle, walkway or clearance the reply mentions is drawn at the place the reply
  gives, as the check found it.
- **Carry every field and note through.** Every column or note per piece (finish, keep, from
  the old flat) appears in the deliverable. A soft note ("keep the armchair by the window") is
  a rule: build it in, or say why it couldn't be met.
- **Fixing their layout means minimal changes.** Move only what a clearance forces, list each
  move with the reason, and keep every other piece where they put it.

1. **Gather the room and the list.** From the conversation or the files named:
   - **The room:** width × depth, or the corners of an L-shaped room; walls and alcoves.
   - **Doors:** which wall, how far along, width, which side the hinge is on and whether it
     opens in, out or slides. **Windows:** position and sill height. **Fixed things:**
     columns, radiators, a chimney breast.
   - **The furniture:** each piece with its size, or its kind (a king bed, a 3-seat sofa) to
     size it from standard dimensions. A dining table includes its chairs; list the table only.

   Convert everything to one unit; feet and inches become feet as decimals, or metres.
   Ask at most two questions, and only for the room's size or the entrance door. A missing
   piece size takes a standard size, stated as an `[assumption]`.

2. **Zone the room before any coordinates,** in three to five lines:
   - the focal wall (TV, fireplace, the view) and what faces it
   - the conversation or use area, and what sits inside it
   - the circulation: the line from the door to each piece, kept off the middle of a seating group
   - what stays clear: the door swing, a wardrobe's doors, a window people open, a radiator

3. **Write `layout.json`** in the shape of [`templates/layout.json`](templates/layout.json).
   Each piece has `type`, `width` (its long front edge), `depth`, `at` (the corner nearest the
   origin) and `facing` (N, S, E or W: the way its front, the side you use it from, points).
   x runs left to right along the entrance wall's direction, y away from it. The type sets
   the use clearances below; override one with `clearance` (`{"back": 0}` for a table pushed
   against a wall), and set `min_walkway` or `accessible: true` when the person asks. Every
   turning space the brief ties to a place goes in `turning_circles`, tied to that place:
   `{"near": "WC door", "side": "front", "within": 1.0, "for": "WC"}` (a door's `side` is
   front, left or right as you face it from inside; a piece's is front, back, left, right or
   any). The check searches only that zone, reports the largest clear circle it found there,
   and draws it at that centre. `{"at": [x, y]}` fixes an exact point. `diameter` defaults to
   1.5 m. With `accessible` and no circle named, the check finds one and reports its centre:
   use that position in the reply.

   | Type | Clearance it needs (m) | Reached from |
   |---|---|---|
   | `bed` | 0.6 each side, 0.6 at the foot | both sides |
   | `single_bed` | 0.6 one side, 0.5 at the foot | either |
   | `dining_table` | 0.9 every side, for chairs to pull back | any side |
   | `desk` | 0.9 in front, for the chair | the front |
   | `wardrobe`, `dresser`, `sideboard` | 0.6 in front, for doors and drawers | the front |
   | `sofa`, `armchair` | 0.35 legroom in front | the front |
   | `bookcase` | 0.45 in front | the front |
   | `coffee_table`, `nightstand`, `side_table`, `tv_unit`, `rug`, `other` | none | not checked |

4. **Run the checker and fix every FAIL before showing anything.**

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code: layout.json in a temporary folder, the drawing in the working directory
   python3 "${CLAUDE_SKILL_DIR}/scripts/layout_check.py" "$work/layout.json" --svg living-room.svg
   # Other IDEs (from the skill folder)
   python3 scripts/layout_check.py "$work/layout.json" --svg living-room.svg
   ```

   Exit 0 means no failures. Exit 1 means a FAIL: an overlap, a piece outside the room or on
   a column, a piece in a door's swing, a blocked clearance, no clear route at the walkway
   width to a piece, a named turning circle that doesn't fit in its place, or, with
   `accessible`, no 1.5 m turning circle. Exit 2 means the input is
   malformed, or that a check didn't finish within `--max-seconds` (default 20): an
   INCOMPLETE result is never a pass. Fix only what it reports and rerun, **at most five
   rounds**. Never search every arrangement by hand, and never run it in the background. If it
   still fails after five, go to step 5 with the best layout so far. Write the SVG in the
   working directory under a plain name (`living-room.svg`), never inside this skill's folder.

5. **When the list can't fit, say so in numbers, and keep their piece.** Draw their layout
   with the piece that misses, name it and by how much (✅ *"the king bed leaves 0.42 m on the
   window side, not 0.6"*), and mark the shortfall on the drawing. Then offer the best change
   that passes as an option (the desk on the other wall, or a smaller piece only if they
   haven't ruled it out), checked like the first.

6. **Reply for the client, in this order:**
   1. **The plan** (the SVG's file name, and their corrected file in their format when they
      gave one) and one line on its idea. ✅ *"Sofa on the long wall
      facing the TV, reading chair by the window, a clear 0.9 m route along the east side to
      the balcony door."*
   2. **The zoning lines** from step 2.
   3. **The pieces,** as a short table of name, size and where it goes.
   4. **What changed against what was asked,** and every assumption.
   5. **Every WARN with what to do about it,** and what this is not: a schematic that meets
      the clearances it was set, not a check against a building or accessibility code.

   Never mention scripts, JSON, a checker's exit code, skill names or this skill's folder in
   the reply; the client sees a plan and the reasons for it.

**Non-interactive runs** (subagent, CI, headless): unsized pieces take standard sizes, the
entrance is the first door given, and north is up, each tagged `[assumption]`. With no room
size and nothing to derive it from, emit `BLOCKED: need the room's dimensions`, say in one
plain sentence what will be drawn once they arrive, and stop.

## Useful references in this skill

- [`templates/layout.json`](templates/layout.json) — the input shape: a 5.0 × 4.2 m living room with a sofa, chair, coffee table, TV unit, bookcase and rug
- [`scripts/layout_check.py`](scripts/layout_check.py) — overlaps, containment, door swings, use clearances, walking routes on a grid, turning circles at a point or searched for in the zone a brief names; draws the SVG
- [`examples/king-bed-bedroom.md`](examples/king-bed-bedroom.md) — worked example: a king bed that "fits" by area, the clearance the first layout broke, and the plan that passes

## Quality bar

- **The plan shown has passed the checker.** No overlap, no piece in a door's swing, no blocked clearance, every piece reachable at the walkway width.
- **Every piece from the list is on the plan,** at its real or stated standard size, or its absence is explained with the number that kept it out.
- **Each piece faces the way it is used:** a sofa toward the focal wall, a desk chair off the wall, a wardrobe's doors into open floor.
- **The walking route runs round a seating group, not through it.**
- **The drawing has overall dimensions, piece sizes, a scale bar and a north arrow,** and the reply says it is schematic.
- **No code or accessibility claim:** "meets the clearances you set", never "ADA compliant".
- **The client's pieces are kept,** with any shortfall marked in numbers; a smaller piece is only ever an option.
- **The drawing matches the reply:** every piece and chair drawn, every turning circle where the reply says.
- **Their file comes back in its exact columns and row order,** with every change listed in the reply, not in the file, and no working file is left in their folder.
- **Every place-tied requirement was tested in its place,** and its result is the one the check gave there.

## When to use this skill

- ✅ "Will a king bed fit in a 3.4 × 3.0 m room with the wardrobe?"
- ✅ Arranging a living room, bedroom, home office or dining room from a furniture list
- ✅ An office or studio fit-out: how many desks fit with their chairs and routes
- ✅ Checking an existing layout someone drew for door swings and clearances
- ✅ A layout with wheelchair turning space and wider routes, at the widths the person sets

## When NOT to use this skill

- ❌ Planning the rooms of a whole floor, or where walls go: that's `floor-plan-layout`
- ❌ Choosing finishes, colours, lighting or a mood board: this places furniture, it doesn't style it
- ❌ Kitchen cabinet runs and appliance clearances by manufacturer: use the cabinet maker's planner
- ❌ Certifying a plan against a building or accessibility code

## Anti-patterns to avoid

- ❌ **A fixed temporary path.** Two sessions at once share it, and one plan leaks into the other.
- ❌ **Overwriting the person's own file.** They lose the version they sent.
- ❌ **"It fits" from areas alone.** A 3.2 m² bed in a 10 m² room says nothing about the 0.6 m it needs on each side.
- ❌ **Showing a layout before it passes.** The wardrobe door that hits the bed is the one the client finds.
- ❌ **Furniture in the door's swing, or a rug's edge as the only route.** A route is clear floor at the walkway width.
- ❌ **A dining table with no room to pull a chair out,** because the chairs weren't drawn.
- ❌ **Every piece against a wall.** A sofa floated off the wall with the route behind it often works better; zone first.
- ❌ **An ASCII sketch or a list of coordinates as the plan.** The client reads the SVG.
- ❌ **"ADA compliant" or "meets code."** The checker tests the clearances it was given, not a code.
- ❌ **Swapping in a smaller bed the client turned down** so the plan passes. Keep theirs and show the shortfall.
- ❌ **A turning circle at the door when the text says it's by the desk.** The drawing is the promise.
- ❌ **Several drawings of the same room.** One sendable plan, plus an option if there is one.
- ❌ **"The turning circle passes" when the check found it on the far side of the room.** In front of the WC door means in front of the WC door.
- ❌ **A new column in the client's schedule.** They gave a CSV; they get the CSV, in its own columns.
- ❌ **Searching every arrangement by hand.** Build one, check, fix what fails, five rounds at most.

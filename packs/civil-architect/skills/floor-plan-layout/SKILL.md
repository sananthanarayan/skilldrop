---
name: floor-plan-layout
description: Lay out a schematic floor plan from a space programme and a footprint, and draw it as a dimensioned SVG — rooms placed as rectangles at real sizes, doors and windows on real walls, overall dimensions, a scale bar and north arrow — with a script that fails the plan when rooms overlap, a room spills outside the footprint, a door sits on no shared wall or a room can't be reached from the entrance. Use when an architect asks to "draw a floor plan", "lay out these rooms", "make a plan for a 10 × 9 m footprint", for a concept plan, a test fit, a zoning diagram or a dimensioned layout from room sizes.
---

# floor-plan-layout

A concept floor plan: every room from the programme placed at its real size inside the
footprint, connected by doors, lit by windows on outside walls, and drawn to scale. The
agent does the design reasoning (what goes where and why); a script checks the geometry and
draws it, so a plan that looks right but has a room overlapping its neighbour or a bedroom
reachable only through a bathroom never reaches the client. Its inputs are the
client's room list and the footprint the site allows.

## How to respond

1. **Gather the three inputs.** Take them from the conversation or the files the user names:
   - **Rooms and target areas,** with adjacencies: an area schedule or the user's list
   - **The outline** of the floor: footprint width × depth, or corner coordinates, inside the site's envelope
   - **Fixed points:** the road side and entrance, north, a stair or core position, an existing wall to keep

   Ask at most two questions, only for a missing outline or entrance side. A plan with no
   footprint and no plot to derive one from is `BLOCKED`.

2. **Decide the zoning before any coordinates.** Write three to six lines:
   - public rooms (living, reception) on the entrance side; private rooms (bedrooms) away from it
   - wet rooms (kitchen, toilets, bathrooms) grouped so plumbing stacks, and stacked over each other across floors
   - every `near` from the programme met by a shared wall, every `apart` by at least one room between
   - daylight: every habitable room on an outside wall; north or south as the climate wants, stated
   - the stair in the same place on every floor

   Then place rooms as rectangles on a grid of 0.3 m (1 ft) or its multiples, starting from a
   corner, so shared walls line up exactly. An L-shaped room is two or three rectangles under
   one name.

3. **Write `plan.json`** in the shape of [`templates/plan.json`](templates/plan.json): `outline`,
   each room's `rect` `[x, y, width, depth]` (or `rects`) with `target_area`, `min_width` and
   `habitable`, every door as `between` two rooms (or `"outside"`) `at` a point on the shared
   wall, and windows `at` a point on an outside wall. x runs left to right, y from the front
   (road side) to the back. One file per floor.

4. **Run the checker and fix every FAIL before showing anything.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/plan_check.py" plan.json --svg ground-floor.svg
   # Other IDEs (from the skill folder)
   python3 scripts/plan_check.py plan.json --svg ground-floor.svg
   ```

   Exit 0 means no failures; 1 means a failure (overlap, outside the outline, door on no
   shared wall, a room unreachable, no entrance); 2 means the input is malformed. Move rooms
   and rerun until it exits 0. A WARN can stand only with a sentence saying why.

5. **Report in this order:**
   1. **The plan's path** and one line on its organising idea. ✅ *"Public rooms along the road, wet rooms stacked on the east wall, stair by the entrance so the first floor is reached without crossing the living room."*
   2. **The zoning lines** from step 2.
   3. **The checker's room table and result,** unchanged.
   4. **Every remaining WARN with its reason,** and every area off target with what it traded for.
   5. **What this plan is not:** schematic, wall thicknesses nominal, no structure, services or code check. The architect checks it against the local rules before it goes further.

**Non-interactive runs** (subagent, CI, headless): take the entrance on the first outline edge
and north as up, tagged `[assumption]`, and size unsized rooms from the programme. With no
outline and no plot dimensions, emit `BLOCKED: need the footprint's dimensions or the plot and
setbacks to derive it`.

## Useful references in this skill

- [`templates/plan.json`](templates/plan.json) — the input shape: a 10 × 9 m ground floor with an L-shaped hall
- [`scripts/plan_check.py`](scripts/plan_check.py) — overlap, containment, doors on shared walls, reachability, areas, windows; draws the SVG
- [`examples/ground-floor.md`](examples/ground-floor.md) — worked example: a programme and footprint become a checked, drawn plan, including the FAIL the first draft hit

## Quality bar

- **The checker exits 0.** No plan with an overlap, a room outside the outline, a door on no wall or an unreachable room is shown to the user.
- **Every room from the programme is on the plan,** at its target area within 10 %, or the difference is explained.
- **Every stated adjacency is a shared wall,** and every `apart` has a room between.
- **Every habitable room has a window on an outside wall.**
- **No bedroom or living space is reached only through a bathroom, toilet or another bedroom.**
- **The drawing has overall dimensions, room sizes, a scale bar and a north arrow,** and says it is schematic.

## When to use this skill

- ✅ A concept plan or test fit from a programme and footprint
- ✅ Two or three layout options for the same brief, each checked
- ✅ Re-planning after the client changes a room
- ✅ A zoning diagram before detailed design

## When NOT to use this skill

- ❌ Working out the room list and areas from a brief, before any layout: total them first, then plan
- ❌ How big the footprint may be under setbacks, coverage and FAR: that is a site feasibility check, done before the plan
- ❌ Construction, working or submission drawings in CAD/BIM: this is a schematic for discussion
- ❌ Structural grids, MEP routing or a code compliance check

## Anti-patterns to avoid

- ❌ **Drawing the plan in ASCII or Mermaid.** Neither holds a dimension; the SVG does.
- ❌ **Showing a plan before the checker passes.** The overlap you can't see in a list of coordinates is the one the client finds.
- ❌ **Rooms that touch "nearly":** a 3.95 and a 4.0 leave a 50 mm sliver no one can build. Use the grid.
- ❌ **A corridor that serves nothing.** Circulation that reaches no door is area the client pays for.
- ❌ **Toilet doors opening onto the dining or kitchen,** and a prayer or puja room sharing a wall with a toilet when the brief keeps them apart.
- ❌ **Calling the plan code-compliant.** The checker tests geometry, not the building code.

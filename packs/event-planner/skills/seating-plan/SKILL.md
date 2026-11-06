---
name: seating-plan
description: Seat guests at tables for a wedding, gala, conference dinner or awards night, and check the chart with a script — every guest seated once, no table over capacity, people who must sit together together, people who must be kept apart apart, wheelchair users at accessible places — drawn as a room plan with names at each table. Use when an organiser asks to "make the seating plan", "who sits where", "seat these 120 guests", "check my table plan", or has a guest list with groups and keep-apart requests.
---

# seating-plan

A table plan for a seated event, where every rule the organiser gave holds at once: each guest
has exactly one seat, no table is over its count, households and groups sit together, the
people who must be kept apart are, and wheelchair users are at tables with step-free access.
With 120 guests and a dozen requests, a plan that looks right usually breaks one of them. The
agent decides who sits where and why; a script checks every rule on every table and draws the
room, so a broken request is found before the organiser prints place cards.

## How to respond

**These rules come before the steps and outrank them:**

- **Deliver in the person's format first.** Given a guest list CSV or spreadsheet, hand back
  the seating in the same columns with a table column added, ready for the venue; fixing
  their plan, return their file corrected, with a `change` column saying what moved and why.
  Given a pasted list, reply with a table. Write every deliverable the request names, such as
  place-card order or the caterer's list.
- **Working files stay out of sight.** The checker's input and any intermediate file go in a
  temporary folder outside the working directory, or are deleted before you reply. Draw the
  room only when a drawing is asked for or the venue needs a floor plan, and then once. Never
  leave anything running in the background.
- **Carry every field through.** Every column the person gave per guest (meal choice, dietary
  need, party, notes) appears in the deliverable, and each conflict between them is flagged:
  a vegan guest who chose the beef, a child in a seat marked for a speaker.
- **Soft notes are rules.** "Keep the grandparents near the door", "not by the speakers":
  build them in, and say which you couldn't meet.
- **Fixing their plan means minimal changes.** Move only the guests a rule forces, list each
  move with the rule, and keep every other seat as they placed it.
- **A passing check is the floor, not the reply.** The reply is about their guests, in their
  words: never file formats, tools or paths.

1. **Collect the guest list and the rules.** Take them from the files the organiser names (a
   guest list CSV or spreadsheet export, an RSVP export, a pasted list) or the message:
   - **Guests:** name, household or party, and needs: wheelchair, near an exit, dietary
     (dietary and meal choice are carried through to the deliverable, not seating rules)
   - **Tables:** how many, seats each, round or long, which are step-free, and where they
     stand, if a room layout exists
   - **Requests:** who must sit together, who must be kept apart, fixed seats (the head table,
     a sponsor's table)

   Ask at most two questions, only about a rule that changes the plan. With no guests, emit
   `BLOCKED: need the guest list`.

2. **Write the plan file** in the shape of [`templates/seating.json`](templates/seating.json):
   `tables` (id, capacity, shape, `at` in metres, `accessible`), `guests` (id, name, party,
   needs, dietary), `together`, `apart`, `fixed`, and `assignments` as table → guest ids.
   Seat in this order, because each step narrows the next:
   1. fixed seats;
   2. wheelchair users and anyone who must be near an exit, at the tables that allow it;
   3. together groups and households, whole;
   4. the apart pairs, kept on different tables;
   5. everyone else, filling tables evenly rather than leaving one half empty.

3. **Run the checker and fix every FAIL before showing anything.** Keep `seating.json` in a
   temporary folder; a drawing, when wanted, goes in the working directory as
   `seating-plan.svg`, never inside this folder.

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/seating_check.py" "$TMPDIR/seating.json"
   # Other IDEs (from the skill folder); add --svg only when a drawing is wanted
   python3 scripts/seating_check.py /tmp/seating/seating.json --svg seating-plan.svg
   ```

   Exit 0 means every rule holds; 1 means one is broken; 2 means the file is malformed. Move
   guests and rerun until it exits 0. A WARN (a household split because it is bigger than a
   table, a half-empty table, someone who came alone at a table of one family) stands only
   with a sentence saying why.

4. **When the rules can't all hold, say which and stop guessing.** Name the conflict and the
   smallest change that resolves it: ✅ *"The Moss and Park families (14 people) must sit
   together, and Ed and Bo must be kept apart, but Ed is in the Park group and Bo in the Moss:
   with 10-seat tables they can't share one, so one family splits. Splitting the Parks 6 + 4
   keeps every other request."* Never break a request quietly to make the plan pass.

5. **Reply for the organiser, in this order:**
   1. **The plan:** in their file's format when they gave one, otherwise a table of each
      table and who sits there, step-free tables marked.
   2. **What couldn't be met,** with the reason and the choice it needs from them.
   3. **The assumptions,** each tagged `[assumption]`: a seat count or a layout they didn't give.
   4. **The caterer's list:** meal choice and dietary need per guest and per table, with each
      conflict flagged.
   5. **The files:** their plan in their format, and the drawing if one was made.

   Write for someone planning an event: no file formats, no tool or script names, no paths
   inside this folder. Say *"every request is met"*, not what checked it.

**Checking a plan the organiser already made:** run the same checker on their plan, report
each problem with the fix that disturbs the fewest guests, and hand back their file with
those fixes made and noted. Don't reseat the room unless they ask.

**Non-interactive runs** (subagent, CI, headless): with no table size, use 10-seat rounds; with
no layout, draw tables in a grid; with no accessible tables named, mark the ones nearest an
exit, each tagged `[assumption]` at the top of the reply. With no guest list, emit
`BLOCKED: need the guest list`.

## Useful references in this skill

- [`templates/seating.json`](templates/seating.json) — the file shape: tables, guests, requests and assignments
- [`scripts/seating_check.py`](scripts/seating_check.py) — checks every guest seated once, capacity, together, apart, access and fixed seats; draws the room
- [`examples/wedding-dinner.md`](examples/wedding-dinner.md) — worked example: a 24-guest wedding where the brief itself conflicts, and the reply names it

The order-of-the-day timings, the speeches and the changeovers belong to `run-of-show`.

## Quality bar

- **Every guest has exactly one seat, and no table is over its count.** The checker exits 0 before the plan is shown.
- **Every together group and every apart pair holds,** or the reply names the one that can't and why.
- **Every wheelchair user is at a step-free table,** and every fixed seat is where it was fixed.
- **Tables fill evenly:** no half-empty table without a reason.
- **The reply leads with who sits where,** in a table the organiser could print.
- **Nothing is invented:** no guest, request or table that wasn't given.
- **The plan comes back in the person's format,** with every field they gave per guest and each conflict flagged.
- **Their notes are honoured,** and their own plan changes only where a rule forces it.
- **No working file is left in their folder.**

## When to use this skill

- ✅ A seating chart for a wedding, gala, awards dinner or conference dinner
- ✅ Checking an existing table plan before the place cards are printed
- ✅ Reseating after late RSVPs or a new keep-apart request
- ✅ A plan for 20 guests or 400

## When NOT to use this skill

- ❌ The order of the day, speeches and changeovers: that's `run-of-show`
- ❌ Theatre or classroom seating with numbered rows and no groups: it's a seat count, not a plan
- ❌ Furniture placement and clearances in a room: that's a layout drawing
- ❌ Choosing the venue or the menu

## Anti-patterns to avoid

- ❌ **Showing a plan before every rule is checked.** A keep-apart pair at table 7 is the one guests notice.
- ❌ **Breaking a request quietly to make the numbers fit.** Name the conflict and let the organiser choose.
- ❌ **Seating in guest-list order.** Fixed seats, access needs and groups go first, or they end up split.
- ❌ **One half-empty table at the back** while others are full. Spread the space.
- ❌ **Mentioning files, formats or tools in the reply.** The organiser wants names at tables.
- ❌ **Treating dietary needs as a seating rule.** They go to the caterer, per guest and table.
- ❌ **Dropping a column the person gave.** The meal choices are what the venue needs next.
- ❌ **A JSON file and a drawing nobody asked for** left beside their guest list.
- ❌ **Telling them the fixes instead of making them.** Hand back the corrected file.

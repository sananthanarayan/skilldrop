---
name: run-of-show
description: Turn an event's agenda into a timed run of show — every session, speaker, changeover and break with its start, end, room and who's needed — and check it with a script for two things in one room at once, a speaker booked in two places, changeovers shorter than the turnaround and anything outside venue hours, drawn as a timeline per room. Use when an organiser asks for "a run of show", "a running order", "the minute-by-minute for the day", "check the agenda for clashes", or has sessions, speakers and rooms for a conference, launch, festival or wedding day.
---

# run-of-show

The running order the crew works from on the day: every item with its start, end, room and
the people it needs, and the setup and changeover time between items. An agenda that reads
fine often has a speaker in two rooms at once, a room handed over with five minutes to reset a
stage that needs twenty, or a session that runs past the venue's close. The agent builds the
order; a script checks every room and every person against the clock and draws the day, so the
clash is found in the plan, not on the day.

## How to respond

**These rules come before the steps and outrank them:**

- **Deliver in the person's format first.** Given an agenda or runsheet as a CSV or
  spreadsheet, hand back the finished or corrected one in the same columns, with a `change`
  column saying what moved and why. Given a pasted agenda, reply with a table. Write every
  deliverable the request names: a minute-by-minute per room, a crew sheet with turnarounds,
  resets and host notes, a speaker call sheet.
- **Working files stay out of sight.** The checker's input and any intermediate file go in a
  private temporary folder made for this run alone (`mktemp -d`, never a fixed path such as `/tmp/show`, which another session can read or overwrite), and are deleted before you reply. Never overwrite a file the person gave you: write the corrected copy beside it under a plain name (`rota-fixed.csv`), and leave theirs as it was. Draw the
  timeline only when a drawing is asked for, and then once. Never leave anything running in
  the background.
- **Carry every field through.** Every column or note the person gave per item (crew, cues,
  AV, contact, notes) appears in the deliverable, and each conflict between them is flagged.
- **Soft notes are rules.** "Keep the couple's photos before sunset", "the band wants a break
  before the last set": build them in, and say which you couldn't meet.
- **Fixing their running order means minimal changes.** Move only what a rule forces, keep the
  rest at the times they set, and keep every supplier and venue limit, such as a call to
  seats or a music cut-off.
- **A passing check is the floor, not the reply.** The reply is about their day, in their
  words: never file formats, tools or paths.

1. **Collect the agenda and the constraints.** From the files the organiser names (an agenda,
   a speaker list, a venue contract) or the message:
   - **Items:** title, room, start and end or a length, and who's needed (speakers, hosts, AV
     crew, the band)
   - **Rooms:** opening and closing times, and the turnaround each needs between items
   - **Setup and changeover:** minutes an item needs in the room before it (a band's line
     check) or after it (striking a stage)
   - **Walking time** between rooms, and the published end of the day

   Ask at most two questions, only about a time that changes the order. With no items, emit
   `BLOCKED: need the sessions or items for the day`.

2. **Write the show file** in the shape of [`templates/show.json`](templates/show.json):
   `rooms` (`open`, `close`, `turnaround`), `items` (id, title, room, `start`, `end` or
   `duration`, `people`, `setup`, `changeover`), `travel` between rooms and `published_end`.
   Times are 24-hour `HH:MM`; a multi-day event gives each item a `day`. Make every break,
   changeover and doors-open an item, so nothing in the day is implied.

3. **Run the checker and fix every FAIL before showing anything.** Keep `show.json` in a
   temporary folder; a drawing, when wanted, goes in the working directory as
   `run-of-show.svg`, never inside this folder.

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/show_check.py" "$work/show.json"
   # Other IDEs (from the skill folder); add --svg only when a drawing is wanted
   python3 scripts/show_check.py "$work/show.json" --svg run-of-show.svg
   ```

   Exit 0 means no clashes; 1 means a clash (an overlap in a room, a person in two places or
   without time to walk, a changeover shorter than needed, an item outside the room's hours);
   2 means the file is malformed. Move or shorten items and rerun until it exits 0. A WARN
   (someone working three hours without a break, a room empty for most of an hour, the day
   running past its published end) stands only with a sentence saying why.

4. **When the day can't fit, say what gives.** Name the clash and the smallest change: ✅
   *"The panel and the pricing workshop both need Ana from 10:15. Moving the workshop to 11:10
   keeps every other time; shortening the keynote to 35 minutes is the other way."* Never
   squeeze a changeover below what the room needs to make the order pass.

5. **Reply for the organiser, in this order:**
   1. **The running order:** in their file's format when they gave one, otherwise a table of
      time, room, item and who's needed, sorted by time; and each sheet the request named.
   2. **What moved, and why,** if they gave an agenda and it had clashes.
   3. **What couldn't be resolved,** with the choice it needs from them.
   4. **The assumptions,** each tagged `[assumption]`: a turnaround or walking time they didn't give.
   5. **The files:** their running order in their format, and the drawing if one was made.

   Write for someone running an event: no file formats, no tool or script names, no paths
   inside this folder. Say *"no one is booked in two places"*, not what checked it.

**Checking an agenda the organiser already made:** run the same checker on it, report each
clash with the move that shifts the fewest items, and hand back their file with those moves
made and noted. Don't redo the day unless they ask.

**Non-interactive runs** (subagent, CI, headless): with no turnaround, use 15 minutes per room;
with no walking time, none; with no venue hours, none, each tagged `[assumption]` at the top of
the reply. With no items, emit `BLOCKED: need the sessions or items for the day`.

## Useful references in this skill

- [`templates/show.json`](templates/show.json) — the file shape: rooms, items, travel and the published end
- [`scripts/show_check.py`](scripts/show_check.py) — checks rooms, people, changeovers and venue hours; draws one lane per room
- [`examples/product-launch.md`](examples/product-launch.md) — worked example: a launch day where the first agenda booked the CEO in two rooms

Who sits where at the dinner belongs to `seating-plan`.

## Quality bar

- **No room holds two items at once, and no one is needed in two places.** The checker exits 0 before the order is shown.
- **Every gap in a room is at least the turnaround, the next item's setup and the last item's changeover.**
- **Nothing runs outside its room's hours,** setup included.
- **Breaks, doors and changeovers are items,** with times, not gaps someone has to infer.
- **The reply leads with the running order,** in a table the crew could print.
- **Nothing is invented:** no speaker, session or venue time that wasn't given.
- **The running order comes back in the person's format,** with every field they gave and each sheet they asked for.
- **Their notes and every supplier limit hold,** and their own order changes only where a rule forces it.
- **No working file is left in their folder.**

## When to use this skill

- ✅ A run of show or minute-by-minute for a conference, launch, festival or wedding day
- ✅ Checking an agenda for clashes before it's published
- ✅ Re-timing the day after a speaker cancels or a session moves room
- ✅ A multi-day, multi-room programme

## When NOT to use this skill

- ❌ Who sits where at the dinner: that's `seating-plan`
- ❌ Staff shifts across a week with hours rules: that's a rota, not a running order
- ❌ Writing the speeches or the event announcement
- ❌ The budget or the supplier list

## Anti-patterns to avoid

- ❌ **Showing an order before every room and person is checked.** The speaker double-booked at 10:15 is the one the crew finds out about at 10:14.
- ❌ **Squeezing a changeover to make the day fit.** The stage still takes twenty minutes to strike.
- ❌ **Breaks as gaps.** A break no one wrote down is the first thing an overrun eats.
- ❌ **Forgetting the walk.** Two rooms on different floors aren't back to back.
- ❌ **Mentioning files, formats or tools in the reply.** The organiser wants the times.
- ❌ **Re-timing the whole day unasked** when one move fixes the clash.
- ❌ **One merged table when they asked for a sheet per room.** The crew in room B needs room B's sheet.
- ❌ **Describing the fixes instead of making them.** Hand back the corrected runsheet.
- ❌ **A fixed temporary path.** Two sessions at once share it, and one plan leaks into the other.
- ❌ **Overwriting the person's own file.** They lose the version they sent.
- ❌ **A JSON file and a drawing nobody asked for** left beside their files.

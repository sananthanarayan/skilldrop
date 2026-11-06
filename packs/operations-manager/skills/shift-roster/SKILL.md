---
name: shift-roster
description: Build a staff rota for a week or a fortnight from who is available, what each shift needs and the working-time rules, and check it with a script before anyone sees it — every shift covered with the right skills, nobody double-booked, over their hours, short of rest between shifts or past the consecutive-day limit — drawn as a week grid. Use when a manager asks to "make the rota", "build next week's schedule", "who should work which shift", "check this rota", "fill these shifts", or has staff availability and shift needs for a shop, restaurant, clinic, warehouse or call centre.
---

# shift-roster

A rota a manager can publish: every shift covered by people with the skills it needs, and no
one double-booked, over their hours, short of rest or past their days in a row. The agent
does the scheduling (who takes which shift, and what's fair). A script checks every rule
for every person and every shift, and draws the week. A rota that looks fine can still hide
a closing shift followed by an opening one eight hours later, and the check stops it reaching
the team.

## How to respond

**These rules come before the steps and outrank them:**

- **No rule is broken quietly.** A rota either passes the check, or the reply says which
  shift can't be covered and what is in the way. Never publish a rota that breaks rest,
  hours, availability or skill cover because it was the closest you got.
- **Answer the manager, in a manager's words.** Lead with the rota or the answer. Never
  mention the check's script, a JSON file, this skill's name or a path inside its folder.
  Say "checked: every shift covered, no rest or hours rule broken", not what ran. A passing
  check is the floor, not the reply.
- **Their file comes back in exactly its own shape.** A file the person gave returns with the
  same columns, column order, headers and row order, and only the cells that must change
  changed, ready to post or import. Every change is listed in the reply: the row, what
  changed and why. Add a change column only when they ask for one. Given a pasted table,
  reply with a table. Write every deliverable the request names, such as a sheet per team.
- **The reply's facts come from the checked rota.** Every hour count, night count, run of
  days and change you write is read from the check's per-person summary and its comparison
  with their original, run on the final rota. Never from memory of an earlier draft.
- **Working files stay out of sight.** The check's input and any intermediate file go in a
  private temporary folder made for this run alone (`mktemp -d`, never a fixed path such as `/tmp/roster`, which another session can read or overwrite), and are deleted before you reply. Never overwrite a file the person gave you: write the corrected copy beside it under a plain name (`rota-fixed.csv`), and leave theirs as it was. Draw the
  week grid only when a drawing is asked for, or as the one extra file named in one line.
  Never leave anything running in the background; wait for it.
- **Carry every field through.** Every column or note the person gave about a person or a
  shift appears in the deliverable, and each conflict between them is flagged.
- **Soft notes are rules.** "Don't give her more than she needs", "keep him off nights if you
  can": build them in, and say which you couldn't meet.
- **Fixing their rota means minimal changes.** Change only what breaks a rule, list each
  change with the rule, and keep everything else as they placed it. Read an ambiguous rule
  the way the person most likely meant it, state the reading, and don't reshuffle on an
  unlikely one.

1. **Gather what the rota needs.** Take it from the conversation or the files named: a CSV, a
   spreadsheet export, a table, notes.
   - **Staff:** name, skills or roles, maximum and contracted hours, times they can't work.
   - **Shifts:** day or date, start and end (a shift ending after midnight is fine), and how many
     people of each skill it needs.
   - **Rules:** minimum rest between shifts, most days in a row, most hours in a day.

   A missing rule becomes a stated assumption with a common default: 11 hours' rest, 6 days in
   a row, 12 hours in a day. Ask at most two questions, and only for staff or shifts that are
   missing altogether.

2. **Write the roster** in the shape of [`templates/roster.json`](templates/roster.json):
   `staff`, `shifts` with `needs` as `{skill: count}`, `assignments` from shift to staff ids,
   and `rules`. Give a person a fixed role on a shift with `{"id": "ben", "as": "till"}`;
   otherwise people are matched to needs, one need each. Save it in a temporary folder, not
   the working directory.

3. **Build one rota, hardest shifts first.** Fill the shifts with the fewest qualified people
   first: nights, keyholder shifts, weekends. Then fill the rest from whoever has the most
   hours left before their contracted total. Spread nights and weekends evenly across the
   people who can work them, and keep a person's shifts in a block, not scattered. Fixing
   their rota, start from theirs and change only what the check reports.

4. **Check it, and fix every failure before showing anything.**

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/roster_check.py" "$work/roster.json"
   # Other IDEs (from the skill folder); add --svg only when a drawing is wanted
   python3 scripts/roster_check.py "$work/roster.json" --svg rota-week-of-2026-11-09.svg
   ```

   Exit 0 means no failures, 1 means a failure, and 2 means the input can't be read. Fix only
   what it reports, and rerun, **at most five rounds**. Never search every arrangement by
   hand. If it still fails after five, go to step 5 with the best rota so far. The check
   fails on:
   - a shift short of a skill it needs;
   - someone on two overlapping shifts, or working while unavailable;
   - someone over their weekly or daily maximum;
   - rest below the minimum, including across midnight and across the weekend;
   - too many days in a row;
   - a role filled by someone without the skill.

   It warns on hours far from contracted, uneven nights or weekends, and a short shift that
   qualified people are free to take (it names them). A warning can stand only with a reason.
   On the final rota, run it once more with `--summary`, and with `--compare original.json`
   when fixing theirs. The reply quotes those two outputs.
   A drawing, when wanted, goes in the working directory under a plain name, never inside
   this skill's folder.

5. **When no rota passes, deliver the best one, say why, and the smallest change that would fix it.** Name the
   constraint: ✅ *"Tuesday night needs two people with stock, and only Chloe and Dev have it;
   Dev is on Tuesday's late shift, so his rest would be 6 hours. One more person trained on
   stock, or moving Tuesday's late shift to Wednesday, fixes it."* — ❌ a rota with Dev on
   both, unflagged. Offer the closest rota only clearly labelled with the one rule it breaks.

6. **Reply in this order:**
   1. **The rota,** as a table: days across and people down (or shifts down for a big team),
      each cell the shift's times and role.
   2. **One line on the check:** every shift covered, and no rest, hours, availability or
      days-in-a-row rule broken. Or the failures, one line each.
   3. **Shifts it couldn't fill,** with why and who could take them.
   4. **Hours per person** against contracted, from the summary, and anything uneven, with the reason.
      Fixing theirs: **the changes**, one line each (row, what changed, why), from the comparison.
   5. **The rules assumed,** each with its value, for the manager to change.
   6. **The files:** the rota in the person's format, and the drawing if one was made.

**Non-interactive runs** (subagent, CI, headless): missing rules become `[assumption]`
lines with the defaults above, and a person with no stated maximum gets no weekly cap but is
flagged in the reply. With no staff or no shifts at all, emit
`BLOCKED: need the staff (with skills and availability) and the shifts to cover`.

## Useful references in this skill

- [`templates/roster.json`](templates/roster.json) — the input shape: four staff, three shifts including one overnight, an absence and a fixed role
- [`scripts/roster_check.py`](scripts/roster_check.py) — cover by skill, overlaps, availability, weekly and daily hours, rest across midnight, days in a row, fairness; `--summary` per person and per shift, `--compare` against their original; draws the week grid
- [`examples/cafe-week.md`](examples/cafe-week.md) — worked example: a café week where the first draft gave a closer an 8-hour turnaround, and the rota that fixed it

## Quality bar

- **The check passes before the rota is shown,** or the reply names the shift that can't be covered and the constraint in the way.
- **Every shift has the skills it needs,** each person filling one need.
- **No one is short of rest, over their hours, on while unavailable or past their days in a row.**
- **Nights and weekends are spread across the people who can work them,** or the reply says why not.
- **The reply leads with the rota as a table,** in plain words, with no mention of scripts, files inside the skill or the skill itself.
- **Every assumed rule is stated with its value.**
- **Their file comes back in its exact columns and row order,** with every change listed in the reply, not in the file.
- **Every number and change in the reply matches the checked rota,** read from the summary and the comparison.
- **Their notes are honoured,** and their own rota changes only where a rule forces it.
- **No working file is left in their folder,** and nothing is left running.

## When to use this skill

- ✅ Next week's or fortnight's rota from availability and shift needs
- ✅ Checking a rota someone drew in a spreadsheet before it's published
- ✅ Re-planning after a sickness, a swap request or a new starter
- ✅ "Can we cover the weekend with the people we have?"

## When NOT to use this skill

- ❌ Working out how many staff a site needs from footfall or demand: that's a forecast, done before the rota
- ❌ Payroll, overtime pay or holiday accrual calculations
- ❌ Employment-law advice: the check applies the rules it's given, and doesn't decide what the law requires
- ❌ Project task scheduling across weeks, where people aren't on shifts

## Anti-patterns to avoid

- ❌ **A rota with a closer back on the opening shift.** 22:00 to 06:30 is eight and a half hours. The check catches it; eyeballing a grid doesn't.
- ❌ **Counting heads instead of skills.** Three people on a shift that needs a keyholder is short if none of them holds keys.
- ❌ **Filling the easy shifts first.** The night and the keyholder shifts are the ones that run out of people.
- ❌ **Giving the same two people every weekend** because they said yes last time.
- ❌ **Bending a rule and not saying so.** A rota that breaks rest "just this once" is the one that gets challenged.
- ❌ **A rota in a new format the manager has to copy back.** They gave a CSV; they get the CSV, in its own columns.
- ❌ **An extra "change" column in their file.** It breaks the import they print or upload from; the changes go in the reply.
- ❌ **Notes written from memory.** "Tom is off Monday" when the rota has him on: read it from the summary.
- ❌ **Searching every arrangement by hand.** Build one, check, fix what fails, five rounds at most.
- ❌ **Reshuffling their rota** to fix three problems. Fix the three, and list them.
- ❌ **Ignoring "don't put her on more than she needs".** A note is a rule.
- ❌ **A fixed temporary path.** Two sessions at once share it, and one plan leaks into the other.
- ❌ **Overwriting the person's own file.** They lose the version they sent.
- ❌ **A JSON file and a drawing nobody asked for** left beside their files.
- ❌ **"The script says…"** The manager wants the rota and what's wrong with it, not how it was checked.

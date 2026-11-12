# Event planner

Seated dinners and event days that hold together: a table plan where every guest has one seat and every together, keep-apart and access request holds, and a run of show where no room or person is booked twice and every changeover has the time it needs, each checked by a script and drawn before anyone prints it.

`/plugin install event-planner@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Get a checked seating plan from a guest list and a few requests

Paste this into Claude Code:

```text
Seat these 36 wedding guests at four tables of 10 (the head table seats 6). Keep each household together, keep Dan and Priya apart, and Grandma Rose uses a wheelchair, so she needs table 1, which is step-free. Here's the list: <paste it>.
```

- **Before you start:** The guest list with households and requests, or the day's sessions with rooms and times
- **Before you start:** Python 3 on the machine, which the checking and drawing scripts run on
- **How to tell it worked:** seating-plan replies with a table of who sits where, names any request it couldn't meet and why, lists dietary needs per table, and saves a drawing of the room with names at each table, after a check that every guest has one seat and every request holds.
- **If nothing happens:** If seating-plan does not activate, ask for it by name ("use seating-plan"). If a request can't be met, say which one may give, and ask again.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `run-of-show`
- `seating-plan`

More: https://sananthanarayan.github.io/skilldrop/packs/event-planner/

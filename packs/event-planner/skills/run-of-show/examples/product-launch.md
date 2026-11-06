# Worked example: a product launch day

Input → output oracle for `run-of-show`. Shows an agenda that reads fine and has four clashes:
a keynote's stage setup colliding with doors in the same room, two handovers shorter than the
room needs, and the CEO due in the demo lab the minute her keynote ends.

## Input

> Here's the launch day. Auditorium 8:00–18:00, needs 20 minutes to turn over between
> sessions; the demo lab is 9:00–17:00, 10 minutes. It's a five-minute walk between them, and
> we've told people we finish at 17:00.
>
> - 8:30–9:00 doors and coffee, auditorium
> - 9:00–9:45 launch keynote, Mara (CEO); AV needs 30 minutes on stage before it
> - 9:45–10:30 live demo of the setup flow, demo lab, Mara and Theo
> - 10:00–11:00 customer panel, auditorium, Ines hosting; the stage takes 25 minutes to strike after
> - 11:15–12:15 lunch, auditorium
> - 13:00–15:30 hands-on lab, demo lab, Theo
> - 16:45–17:15 closing remarks, Mara

## The agenda as given, checked

```
FAIL Auditorium: 0 min between Doors and coffee (08:30) and Launch keynote (09:00), 30 min needed for Launch keynote's setup
FAIL Auditorium: 15 min between Launch keynote (09:00) and Customer panel (10:00), 20 min needed for the room's turnaround
FAIL Auditorium: 15 min between Customer panel (10:00) and Lunch (11:15), 25 min needed for Customer panel's changeover
FAIL Mara Quinn (CEO) has 0 min to get from Auditorium to Demo lab between Launch keynote and Live demo: setup flow; the walk takes 5
WARN Auditorium is empty for 270 min between Lunch and Closing remarks
WARN Demo lab is empty for 150 min between Live demo: setup flow and Hands-on lab
WARN Closing remarks ends at 17:15, 15 min after the published end of 17:00
4 failure(s)
```

Each one has a small fix that moves as little as possible. Doors and coffee go to the foyer,
so the stage crew has the auditorium from 8:30. The demo starts five minutes later, so Mara
can walk over. The panel moves 5 minutes and lunch 15, so each handover gets the time the
room needs. Closing starts 15 minutes earlier, to end on time.

## The reply

**No room or person is booked twice, and the day ends at 17:00 as published.** Five times
moved from your agenda, each by 15 minutes or less.

| Time | Room | Item | Who's needed |
|---|---|---|---|
| 08:30–09:00 | Foyer | Doors and coffee | Front of house |
| 09:00–09:45 | Auditorium | Launch keynote | Mara, AV crew (on stage from 08:30) |
| 09:50–10:35 | Demo lab | Live demo: setup flow | Mara, Theo |
| 10:05–11:05 | Auditorium | Customer panel | Ines, AV crew |
| 11:30–12:30 | Auditorium | Lunch | |
| 13:00–15:30 | Demo lab | Hands-on lab | Theo |
| 16:30–17:00 | Auditorium | Closing remarks | Mara |

**What moved, and why:**
- **Doors and coffee to the foyer.** The keynote stage needs 30 minutes and the room opened
  for coffee at 8:30.
- **Live demo to 09:50.** Mara's keynote ends at 09:45, and the lab is a five-minute walk.
- **Panel to 10:05, lunch to 11:30.** The auditorium needs 20 minutes between sessions, and 25
  after the panel to strike the stage.
- **Closing remarks to 16:30.** They ended at 17:15, after the time you've published.

**Assumption:** `[assumption]` the foyer is free from 08:00. If it isn't, the keynote moves to
09:30 instead, and everything after it moves 30 minutes.

The auditorium sits empty from 12:30 to 16:30 while the hands-on lab runs. That's fine if
everyone is in the lab; if not, it's the obvious slot for a second session.

The timeline, one lane per room, is in `run-of-show.svg`.

## Why this is the oracle

- **Setup, turnaround and changeover are checked as well as overlaps.** A plain read sees no
  two sessions at the same time in one room, and calls the agenda clash-free.
- **People are checked across rooms, with the walk.** The CEO's back-to-back across two rooms
  is the clash crews find on the day.
- **Each fix is the smallest move, and the reply lists them.** It doesn't silently re-time the
  day or squeeze the stage strike to fit.

---
rfc: 0077
title: An interior-designer pack on furniture-layout's third draft, and a private work folder for every checker skill
status: implemented
date: 2026-11-08
author: sanjay-ananth
---

# RFC-0077: An interior-designer pack on furniture-layout's third draft, and a private work folder for every checker skill

## Problem / use case

`furniture-layout` lost both drafts in RFC-0076, and `interior-designer` didn't ship. The
judges' reasons named three faults:
- **A false pass.** A turning circle "required in front of the bathroom door" was reported
  met because the checker found a clear circle somewhere else in the room.
- **Two timed-out runs.** Two runs produced nothing in 15 minutes.
- **The client's file changed shape.** It came back with different columns.

`seating-plan` shipped at the bar, and its losses pointed to a venue handout and to how
conflicts are settled.

## Fit check

No new skill or primitive. This is a third draft of one measured skill, which makes it a new
pack, plus patches to four skills' instructions. `judge-audit` (RFC-0066) and `shift-roster`
(RFC-0076) set the precedent for a third draft on fresh blind evals.

## Proposal

**`furniture-layout` 0.2.0:**
- **Requirements tied to a place.** `turning_circles` takes `near` (a door or a piece), `side`
  and `within`. The checker searches only that zone and reports the largest clear diameter
  there. A requirement counts as met only where it was tested.
- **Speed.** Profiling showed the checker was never slow: a café checks in 0.15 s. The
  timeouts were the agent iterating by hand. The skill now builds once and fixes only what the
  check reports, for at most five rounds. `--max-seconds` bounds the checker.
- **Exact columns.** The rule is taken from `shift-roster`.

**Private work folders, in `furniture-layout`, `shift-roster`, `seating-plan` and
`run-of-show`.** All four told the agent to write the checker's input to a fixed temporary path
(`$TMPDIR/layout.json`, `/tmp/layout/layout.json`). In the benchmark, two sessions running at
once shared it: the library-room run read the dental-room run's layout and attached its
drawing. A user running two sessions would get the same leak, one event's guest list in
another's plan. Each now makes a private folder per run (`mktemp -d`, or a hidden one in the
working directory when the system temp folder is closed) and deletes it before replying. It
also writes a corrected copy beside the person's file, never over it. These are patch
releases.

## Measurement

Two fresh held-out evals, written blind from the description: a dental waiting room (build)
and a library reading-room schedule (check). Two trials, judges `claude-sonnet-5-5` and
`claude-opus-5-5`, with `--allow-bash`.

| Skill | Draft | Pairs won (judges 1, 2, of 4) | Checks met: skill / plain |
|---|---|---|---|
| `furniture-layout` | 3 (0.2.0) | 2, 2 | 91% / 91% |
| `seating-plan` | patch 0.2.0 (venue sheets) | 1.5, 1 | 100% / 94% |

- **`furniture-layout` won the build in all 4 pairs.** It was the only arm to hand over a
  scaled, dimensioned drawing. It lost the check eval, once because of the leaked drawing
  above and both times for overwriting the client's CSV. Both faults are fixed in 0.2.1. It
  is admitted at the bar, on draft 3.
- **The `seating-plan` patch did worse,** and is not shipped.
  - Its "keep the row order" rule returned a fixed plan with tables scattered through the
    file, where the judges wanted it sorted by table.
  - Its contact-details rule produced a false claim that the list held emails and phone
    numbers.

  The shipped 0.1.2 stays, with the work-folder fix as 0.1.3. The four new held-out evals stay
  in its evals for the next attempt.

## Alternatives considered

- **Keep `interior-designer` retired.** Draft 3 won the build every time, and its check-eval
  losses were the two faults fixed here.
- **Isolate the benchmark's temp folder instead.** The sandbox allows the shared `/tmp` and
  refuses a per-run `TMPDIR`. The leak was in the skills' instructions, so the fix goes there,
  where users meet it too.

## Decision

`interior-designer` ships with `furniture-layout` 0.2.1. `seating-plan` stays on 0.1.2,
patched to 0.1.3. The work-folder and never-overwrite fix goes into all four checker skills.

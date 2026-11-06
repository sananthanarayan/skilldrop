---
rfc: 0076
title: An event-planner pack and a locale check (operations-manager and interior-designer measured, not admitted)
status: implemented
date: 2026-11-06
author: sanjay-ananth
---

# RFC-0076: An event-planner pack and a locale check (operations-manager and interior-designer measured, not admitted)

## Problem / use case

Four jobs end in an artifact that has to satisfy many hard constraints at once, and a capable
agent quietly breaks one:
- **A shift rota for 20 people.** Every shift needs the right skills, and nobody can be
  double-booked, over their hours, short of rest between shifts or past the consecutive-day
  limit.
- **A seating chart for 120 guests.** Tables have capacities, some people must sit together
  and some must be kept apart, and wheelchair users need accessible places.
- **A conference run of show.** Rooms have turnarounds, speakers can't be in two places, and
  everything must fit inside the venue's hours.
- **A furnished room.** Pieces must not overlap or block a door's swing, and walkways, bed
  sides, chair pull-back and turning space all need their clearances.
- **A release's translations.** Every placeholder, plural form, tag and character budget must
  survive in every locale.

Each is the kind of failure the 1.5.0 baseline and RFC-0075 found a skill can beat. A
script checks the constraint the model breaks, and draws or reports the result. Arithmetic
or advice the model already gets right is not that.

## Fit check

- **Concrete artifact:**
  - a checked rota with a week grid (SVG);
  - a checked seating chart with a room plan;
  - a checked run of show with a timeline;
  - a checked, dimensioned furniture plan;
  - a ranked list of translation failures.
- **Portable:** plain folders, stdlib Python 3.9+ scripts that read only the file they're
  given and write only the path they're given, with no network.
- **Opinionated:** each script decides pass or fail. The skill turns what the person brings
  into the script's input, iterates until the check passes, and names the constraint that
  makes a plan impossible rather than breaking it.
- **Category:** three new packs, because none of these audiences is served (operations
  managers, event planners, interior designers). `locale-check` joins `experience-design`,
  beside `ux-writing`, which writes the strings it checks.

## Proposal

| Pack | Skill | Tier | Script |
|---|---|---|---|
| `operations-manager` | `shift-roster` | standard | `roster_check.py`: coverage by skill, double-booking, unavailability, weekly and daily hours, rest across midnight, consecutive days; a week grid |
| `event-planner` | `seating-plan` | standard | `seating_check.py`: seated once, capacity, together and apart, accessible places; a room plan |
| `event-planner` | `run-of-show` | standard | `show_check.py`: room clashes, people in two places, changeovers, venue hours; a timeline per room |
| `interior-designer` | `furniture-layout` | heavy | `layout_check.py`: overlap, containment, door swing, use clearances, a walkway route on a grid, turning space; a dimensioned plan |
| `experience-design` | `locale-check` | standard | `locale_check.py`: keys, placeholders, ICU, CLDR plural categories, tags, budgets across JSON, ARB, .po, Android and iOS files |

The rules every one of them carries, from what lost before (RFC-0071, RFC-0075):
- the reply leads with the plan or the answer, for the person who asked;
- no script, file format, skill name or skill-folder path in the reply;
- drawings are saved in the working directory;
- a plan the person gave is checked, not rewritten unasked;
- missing values become stated assumptions, not a refusal.

**Admission.** Each skill is measured on two held-out evals, written blind from its
description: two trials, judges `claude-sonnet-5-5` and `claude-opus-5-5`, with
`--allow-bash`. A skill that doesn't win at least half its pairs with both judges is revised
once and measured on fresh blind evals. A skill that loses twice doesn't ship, and a pack
with no admitted skill doesn't ship.

## Measurement

Each skill was measured on two held-out evals written blind from its description: two trials on
`claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`, with `--allow-bash`.
Each first draft lost. Each was revised once from the judges' reasons, with general rules
only, and measured on two fresh blind evals.

| Skill | Draft 1, pairs won (judges 1, 2, of 4) | Draft 2 | Checks met, draft 2: skill / plain | Admitted |
|---|---|---|---|---|
| `locale-check` | 0, 0 | 3, 2 | 91% / 78% | yes |
| `run-of-show` | 1, 0 | 2, 3 | 84% / 81% | yes |
| `seating-plan` | 0, 1 | 2, 2 | 100% / 100% | yes, at the bar |
| `shift-roster` | 2, 1 | 2, 1 | 100% / 100% | no |
| `furniture-layout` | 0, 0 | 2, 1 of 3, and one run timed out twice | 88% / 96% | no |

**What the first drafts lost on.** Sonnet 5.5, with a shell, made valid rotas, seating plans,
schedules and layouts too. The judges preferred whichever delivered for the person:
- the corrected file in their own format, ready to send;
- the role sheets the request named;
- every field carried through, with conflicts flagged;
- soft notes honoured, and minimal changes to a plan they gave.

The skills added unrequested files and didn't return the person's own.
`locale-check` lost differently. It trusted a valid but meaning-changing placeholder swap
(`de %2$s a %1$s`), and didn't measure a length limit that was stated in the request.

**What the second drafts added:** deliver in the person's format, keep working files out of
sight, carry every field through, treat soft notes as rules, fix with minimal changes, and
keep the person's choices. `locale-check` also gained: read every reordered placeholder for
meaning, and measure every stated limit.

**What still lost.** One of the new rules, "add a change-note column when fixing", cost
`shift-roster` and `seating-plan` their fix-this evals. The judges preferred the plain
agent's file in the exact original columns. `furniture-layout` also declared a turning circle
clear when it didn't fit, and one run produced nothing in 15 minutes, twice.

`locale-check` still misses a translation that drops a "not" in valid syntax. That's a
meaning error no check catches, and it's named here as its known gap.

## Alternatives considered

- **One `planner` pack for rotas, seating and agendas.** The audiences differ: a shop
  manager and a wedding planner browse for different things, and a pack says who it is for.
- **Put `furniture-layout` in `civil-architect`.** An interior designer furnishes a room
  someone else drew. A separate pack lets them install it without the building skills.
- **Localization as a new pack.** One skill, used by the same people who write the strings
  in `experience-design`, so it joins that pack.

## Decision

`event-planner` ships with `seating-plan` and `run-of-show`, and `locale-check` joins
`experience-design`. `operations-manager` and `interior-designer` don't ship: each one's
only skill lost on both drafts. Both are kept on the local branch
`sanjay-ananth/ops-interior-wip`, for a third draft. That draft would drop the change-note
column, return files in their exact original columns, and give the furniture checker a time
bound. It would be measured on fresh evals.

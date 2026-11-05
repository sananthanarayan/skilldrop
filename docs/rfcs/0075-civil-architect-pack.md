---
rfc: 0075
title: A civil architect pack, admitted with its floor plan skill alone
status: implemented
date: 2026-11-05
author: sananthanarayan
---

# RFC-0075: A civil architect pack, admitted with its floor plan skill alone

## Problem / use case

An architect starting a building job has three numbers-heavy questions before any design:
what the plot allows, what the client's brief adds up to, and whether a first plan fits.
Each is answered today in a spreadsheet and a sketch that disagree with each other. A
capable agent asked the same questions gets the important part wrong in predictable ways:

- **Site feasibility.** It applies FAR to the envelope instead of the plot, reports the
  envelope as the footprint when ground coverage is lower, rounds floors up under a height
  limit, and fills a missing setback or FAR with a "typical" value as if it were the rule.
- **Space programme.** It totals unit areas without their counts, counts circulation twice
  (as a corridor and as an allowance), and presents a rule-of-thumb size as the client's
  requirement.
- **Floor plan.** It draws the plan in ASCII or Mermaid, where nothing holds a dimension, or
  writes an SVG whose rooms overlap, spill outside the footprint or have doors on no wall,
  and nothing catches it.

The catalogue's `solution-architect` pack is for software systems; nothing in it draws a
building.

## Fit check

- **Concrete artifact:** a feasibility table and dimensioned SVG site plan; an area schedule
  with a Mermaid bubble diagram; a checked, dimensioned SVG floor plan.
- **Portable:** plain folders. Each script is standard-library Python 3, reads only the JSON
  it is given, writes only the SVG path it is given, and contacts no network.
- **Opinionated:** the script decides the arithmetic and the geometry check; the skill decides
  the binding limit's meaning, the allowance for the building type, the zoning before
  coordinates, and refuses to invent a planning rule or call a plan code-compliant.
- **Category:** Diagrams. A new pack, `civil-architect`, because its audience (building
  architects and owners) is not served by any existing pack, and a new outcome,
  `design-a-building`.

## Proposal

| Skill | Tier | Script | Bans |
|---|---|---|---|
| `site-feasibility` | standard | `site_envelope.py`: envelope by per-edge setback on any convex plot, coverage, FAR, floors, binding limit, SVG | FAR on the envelope; an invented planning rule |
| `space-program` | standard | `area_schedule.py`: schedule per level, allowances, site check, Mermaid adjacency diagram | counts dropped; circulation counted twice |
| `floor-plan-layout` | heavy | `plan_check.py`: overlap, containment, doors on shared walls, reachability, windows, areas; SVG with dimensions, scale bar, north arrow | showing a plan the checker fails; ASCII plans |

`related` runs site → programme → plan, with hand-offs in that order and a fallback for each.
No loop: the three run in order without a gate the user doesn't already apply, and RFC-0074
showed a loop has to beat its own skills to earn its place.

## Alternatives considered

- **One `building-design` skill** doing all three. Rejected: each step is done on its own
  (a feasibility check for a plot the client hasn't bought; a programme for an RFP with no
  site yet), and one SKILL.md for all three would run past 500 lines.
- **Extend `architecture-diagrams` or `figma-diagrams`.** Rejected: both are for software
  systems; a floor plan needs real dimensions and a geometry check, not boxes and arrows.
- **Draw plans in DXF for CAD.** Deferred: SVG opens everywhere and is enough for a concept
  plan; a DXF export is a later addition to the same `plan.json`.

## Measurement

Each skill was measured on two held-out evals written blind from its description, two
trials, judges `claude-sonnet-5-5` and `claude-opus-5-5`, scripts free to run
(`--allow-bash`):

| Skill | Evals | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without |
|---|---|---|---|---|---|
| `floor-plan-layout` | 3 and 4 | 4 of 4 | 3 of 4 | 58% | 51% |
| `site-feasibility` | 3 and 4 | 0 of 4 | 0 of 4 | 82% | 79% |
| `space-program` | 3 and 4 | 1 of 4 | 0 of 4 | 73% | 42% |
| `site-feasibility`, revised | 5 and 6, new | 0.5 of 4 | 2 of 4 | 75% | 82% |
| `space-program`, revised | 5 and 6, new | 1 of 4 | 0 of 4 | 89% | 83% |

`floor-plan-layout` clears the bar with both judges. The plain agent drew its plans in ASCII
or as an SVG nothing had checked: in the judges' words, it put a 24 ft side on a street the
brief gave 30 ft, merged two rooms the programme kept apart, and left a laundry with no door.

The other two lost. On the first evals, the judges' reasons were the reply, not the figures:
it pointed to "the script" and to a drawing saved inside the skill's folder, which the user
never sees; it gave limits but no scheme; and it handed over JSON as the programme. The
revision fixed each of these and was measured on new blind evals. It still lost, for a
different reason: the plain agent got the same figures right (a trapezoid envelope, a
height-linked side yard, a duplicated room in a brief) and offered more options and fuller
adjacency diagrams. Arithmetic a capable agent already does correctly is not a skill.

## Decision

Implemented with `floor-plan-layout` alone, in a new `civil-architect` pack and a
`design-a-building` outcome. `site-feasibility` and `space-program` are not admitted. Their
scripts (a per-edge setback envelope with a scheme block for any convex plot; an area
schedule with a break-even allowance and an adjacency matrix) are kept on the local
`civil-architect-full` branch, for a rebuild that adds something the plain agent doesn't do.

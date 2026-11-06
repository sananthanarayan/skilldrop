---
rfc: 0075
title: A civil architect pack with a checked floor plan skill
status: implemented
date: 2026-11-05
author: sananthanarayan
---

# RFC-0075: A civil architect pack with a checked floor plan skill

## Problem / use case

An architect with a client's room list and a footprint wants a first plan to discuss. A
capable agent asked for one draws it in ASCII or Mermaid, where nothing holds a dimension, or
writes an SVG whose rooms overlap, spill outside the footprint or have doors on no wall, and
nothing catches it. The catalogue's `solution-architect` pack is for software systems;
nothing in it draws a building.

## Fit check

- **Concrete artifact:** a dimensioned SVG floor plan per level, with a room table.
- **Portable:** a plain folder. The script is standard-library Python 3, reads only the JSON
  it is given, writes only the SVG path it is given, and contacts no network.
- **Opinionated:** it decides the zoning before any coordinates, places rooms on a grid so
  walls line up, and refuses to show a plan the checker fails or to call one code-compliant.
- **Category:** Diagrams. A new pack, `civil-architect`, because its audience (building
  architects and owners) is not served by any existing pack, and a new outcome,
  `design-a-building`.

## Proposal

| Skill | Tier | Script | Bans |
|---|---|---|---|
| `floor-plan-layout` | heavy | `plan_check.py`: overlap, containment, doors on shared walls, reachability, windows, areas; SVG with dimensions, scale bar, north arrow | showing a plan the checker fails; ASCII plans |

No loop: one skill has nothing to sequence.

## Alternatives considered

- **Extend `architecture-diagrams` or `figma-diagrams`.** Rejected: both are for software
  systems; a floor plan needs real dimensions and a geometry check, not boxes and arrows.
- **Draw plans in DXF for CAD.** Deferred: SVG opens everywhere and is enough for a concept
  plan; a DXF export is a later addition to the same `plan.json`.

## Measurement

Measured on two held-out evals written blind from its description, two trials, judges
`claude-sonnet-5-5` and `claude-opus-5-5`, scripts free to run (`--allow-bash`):

| Skill | Evals | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without |
|---|---|---|---|---|---|
| `floor-plan-layout` | 3 and 4 | 4 of 4 | 3 of 4 | 58% | 51% |

It clears the bar with both judges. The plain agent drew its plans in ASCII or as an SVG
nothing had checked: in the judges' words, it put a 24 ft side on a street the brief gave
30 ft, merged two rooms the programme kept apart, and left a laundry with no door.

## Decision

Implemented in 1.6.0: `floor-plan-layout` in a new `civil-architect` pack and a
`design-a-building` outcome.

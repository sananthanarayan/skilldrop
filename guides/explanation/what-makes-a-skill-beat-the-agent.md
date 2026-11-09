---
title: What makes a skill beat the agent
summary: Twelve profession skills, each measured blind against Claude Code without it - which kind won, which kind lost twice, and the rule that predicts the difference before anything is built.
kind: explanation
---

# What makes a skill beat the agent

Between 5 and 9 November 2026 this catalogue built twelve skills for professions it had never
served: architects, operations managers, event planners, interior designers and founders.
Every one was measured the same way before it could ship, and most did not ship on the first
try. This page is what those measurements say about which skills are worth building. The
earlier account of the whole catalogue is [What the benchmark showed](what-the-benchmark-showed.md).

## How each one was measured

Each skill got two requests written blind, by an agent that saw only the skill's description,
never its instructions or scripts. Each request ran twice with the skill and twice with plain
Claude Code (`claude-sonnet-5-5`, file and shell tools, scripts free to run). Two judges,
`claude-sonnet-5-5` and `claude-opus-5-5`, saw the request and both answers in shuffled order,
with no rubric and no skill text, and picked the one that served the person better. A skill
ships only if both judges prefer it in at least half its pairs. One that loses is revised once,
from the judges' reasons, and measured again on new blind requests; one that loses twice is
removed. The decisions and numbers are in RFC-0075 to RFC-0079.

## What won

| Skill | Pack | Pairs won (judge 1, judge 2, of 4) | What its script checks |
|---|---|---|---|
| [`floor-plan-layout`](../../packs/civil-architect/skills/floor-plan-layout/SKILL.md) | civil-architect | 4, 3 | rooms overlapping or outside the footprint, doors on no shared wall, rooms no one can reach |
| [`contract-check`](../../packs/startup-legal/skills/contract-check/SKILL.md) | startup-legal | 3, 2 | references to clauses that don't exist, blanks left in, words that disagree with figures, renewal notice dates |
| [`cap-table`](../../packs/startup-legal/skills/cap-table/SKILL.md) | startup-legal | 2, 4 | SAFEs, notes and a pool top-up solved together, checked to sum to 100 % |
| [`lease-check`](../../packs/startup-legal/skills/lease-check/SKILL.md) | startup-legal | 3, 3 | the committed cost to each break, capped index reviews, notice dates, a term ending on 29 February |
| [`locale-check`](../../packs/experience-design/skills/locale-check/SKILL.md) | experience-design | 3, 2 (second draft) | placeholders, plural forms and length limits that break in translation |
| [`run-of-show`](../../packs/event-planner/skills/run-of-show/SKILL.md) | event-planner | 2, 3 (second draft) | a room or a person booked twice, changeovers too short |
| [`seating-plan`](../../packs/event-planner/skills/seating-plan/SKILL.md) | event-planner | 2, 2 (second draft) | capacity, keep-apart pairs, accessible places |
| [`shift-roster`](../../packs/operations-manager/skills/shift-roster/SKILL.md) | operations-manager | 2, 2 (third draft) | rest between shifts, hours, cover by skill |
| [`furniture-layout`](../../packs/interior-designer/skills/furniture-layout/SKILL.md) | interior-designer | 2, 2 (third draft) | door swings, clearances, a clear route, turning space where it's required |

Every winner has a script that checks a **constraint the plain agent breaks without noticing**,
on an artifact where the break is invisible until someone uses it: a door that opens into a
wall, a closing shift followed by an opening one eight hours later, "Section 14.3 survives
termination" in an agreement that ends at clause 9. The plain agent, asked the same thing,
produced work that looked right. In the judges' words, it "put a 24 ft side on a street the
brief gave 30 ft", "left a laundry with no door", and drew plans in ASCII.

## What lost twice

Three attempts in the same week lost on both drafts and were removed:

- a site feasibility calculator (setbacks, coverage, floor-area ratio, floors under a height limit);
- a space programme (a brief's rooms totalled with circulation and checked against the site);
- a privacy-policy reviewer that scanned an app's code for the services receiving users' data.

`furniture-layout` lost its first two drafts too, and won on its third.

Each was correct. The scripts were tested, and their answers agreed with hand calculations.
They lost because **the plain agent was also correct**: it got the trapezoid envelope and the
height-linked side yard right, totalled the rooms, and read the app's code well enough to find
the same undisclosed services, then offered more options and fuller drafts. The judges
preferred the fuller answer. Arithmetic a capable agent already does correctly is not a skill.

## The rule

Before building a skill, run one blind request through plain Claude Code and look at what
comes back:

- **If it is wrong in a way the person wouldn't notice until later** (a constraint broken, a
  reference dangling, a total that doesn't add up, a date off by a holiday), a script that
  checks that constraint is likely to win.
- **If it is right, and only less tidy than you'd like,** a skill will add structure the judges
  don't value, and lose.

The second half explains the catalogue-wide result in [the November baseline](what-the-benchmark-showed.md#a-new-baseline-with-scripts-free-to-run):
skills that ship a working script came out slightly ahead of the plain agent, and skills that
are instructions alone lost about two pairs in three.

## How the winners talk

A good script was not enough on its own. The first drafts of four winners lost on how they
replied, and each revision that fixed it was general, not tuned to the requests:

- **Lead with the answer for the person who asked:** the plan, the verdict, the percentage.
- **Never mention the script, a file format, the skill, or a temporary path.** "Refers to a
  check the reader never saw" was the commonest single reason a winner lost a pair.
- **Return the person's file in its own shape,** with changes listed in the reply, never in an
  added column, and never over their original.
- **Keep working files private** (`mktemp -d`), so two sessions never read each other's plan.
- **Name at most two things worth a professional's time,** instead of a disclaimer.

## Limits

Two requests and two trials per skill is a small sample: a skill admitted at 2 of 4 pairs with
each judge is at the bar, not clear of it. One author wrote the skills; the requests were
written blind, but by a model. The judges are models too, and agreed with each other in most
pairs where both chose a side, not all. Everything here is about `claude-sonnet-5-5`; a weaker
model would likely break more constraints on its own, and a stronger one fewer.

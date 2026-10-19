---
rfc: 0048
title: Interactive diagrams whose every part cites its source
status: implemented
date: 2026-10-18
author: sanjay-ananth
---

# RFC-0048: Interactive diagrams whose every part cites its source

## Problem / use case

A developer onboarding teammates, a lead explaining a request path in review, or someone
mapping an approval process asks the agent for a diagram they can click through and send as
one file. The catalogue's diagram skills write notation (`architecture-diagrams`: Mermaid,
PlantUML, C4) or a write-up (`reverse-architecture`), and none produces a page a reader can
explore. Archify (MIT, github.com/tt-a1i/archify) showed the demand for that page. It also
showed the costs: a 290 KB Node CLI, a 790 KB template copied into every output, a real
browser for its checks, coordinates the agent writes by hand and then repairs, and source
evidence only when asked.

A plain agent asked for the same page writes HTML that loads Mermaid or D3 from a CDN, so it
breaks offline, and it draws the system such repos usually have. In a diagram that failure is
worse than in prose, because a box reads as a fact.

## Fit check

- **Concrete artifact:** one self-contained HTML file, the JSON spec it was built from, and
  optionally a Mermaid file.
- **Portable:** a plain folder with one Python 3.9+ script that uses only the standard
  library. No npm, no browser, no network, at build time or when the page is opened.
- **Opinionated:** every part and connection cites a file and lines or the person's words,
  or is drawn dashed as an assumption; one question per map; the script lays it out.
- **Category:** `solution-architect`, beside `architecture-diagrams` and `reverse-architecture`;
  the `design-the-system` outcome.

## Proposal

`interactive-diagram` (standard tier; related: `architecture-diagrams`, `reverse-architecture`,
`mermaid-render`). Six types: architecture, dataflow, workflow, lifecycle, ERD, sequence. The
agent writes a JSON spec of meaning only; `scripts/build_diagram.py`:

- **checks** the spec (ids, references, evidence on every item) and, with `--repo-root`, each
  cited file, line range and quoted fragment, refusing to write on any error;
- **lays out** the diagram deterministically: layered placement, groups as non-overlapping
  bands, and orthogonal routes confined to gaps and corridors that hold no node;
- **writes** one page of about 30 KB: pan and zoom, click for detail and the cited lines,
  upstream and downstream reach, the path between two parts, search, a walkthrough, light and
  dark, deep links, SVG / PNG / Mermaid export, and the whole diagram as text first in the
  page; secrets files are never shown and secret-looking lines are masked;
- **compares** two specs, marking what was added, removed and changed.

Quality bar: every item cites or is an assumption; every file citation checked; nothing only
from a README or what such systems usually have; one question; one offline file; link and
takeaway first. Bans: the usual architecture, README as evidence, deleting evidence to pass,
everything in the repo, hand-placed coordinates, a CDN.

**Admission** follows RFC-0041 and RFC-0042: three evals by the author with fixtures, two
held-out evals by a writer who sees only the description, and the skill ships only if both
blind judges prefer it to plain Claude Code in at least half the held-out pairs over two
trials.

## Alternatives considered

- **Vendor archify.** It is MIT and capable, but it needs Node and a browser, its outputs are
  ~800 KB, and its agent places coordinates. Copying it would break the catalogue's
  single-folder, no-dependency install, and it would still make evidence optional.
- **Extend `architecture-diagrams`.** Its output is text notation for a doc. An explorable page
  with checked evidence is a different artifact with a different failure mode.
- **Render Mermaid in the page.** That needs the Mermaid library inline (about 3 MB) or from a
  CDN, and Mermaid's layout has no notion of evidence or assumptions. The page exports Mermaid
  instead.

## Decision

Accepted and admitted in 0.16.22.

| Evals | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without |
|---|---|---|---|---|
| 1 to 3, by the author | 5 of 6 | 4 of 6 | 94% | 75% |
| 4 and 5, by a writer who saw only the description | 4 of 4 | 3 of 4 | 94% | 62% |

Two trials, two judges (`claude-sonnet-5-5`, `claude-opus-5-5`), on `claude-sonnet-5`. The
held-out pairs clear the bar of half with both judges. Plain Claude Code loaded a diagram
library from a CDN in 4 of its 10 pages; the skill did in none. The skill's runs cost less
($0.20 against $0.22) and wrote fewer tokens (7,800 against 12,000), because the script does
the layout the plain agent writes by hand.

What it still misses: in four of ten runs the reply did not open with the file's location,
leading instead with the citation count or a summary. The fixed order in step 5 came from a
trial run on eval 1, before the measured run. The judges' reasons on evals 4 and 5 have now
been read, so the next revision needs evals of its own.

Built alongside: the page carries a Content-Security-Policy that lets only its own script run
(pinned by hash) and blocks every network request, checked by injecting an external script,
an image and an inline script into a built page; all three were refused. The page's lookups are
`Map`s, so an id or a deep link such as `#__proto__=x` can't reach an object prototype
(CodeQL `js/remote-property-injection`). The site publishes a
skill's `examples/*.html` beside its page as live examples, and `skilldrop scan` treats
`examples/inputs/` like eval fixtures.

## Revision: four more types, wrapping, computed findings (0.16.23)

The weaknesses named at admission, and what was done about each:

- **Six types to archify's ten.** Added `class` (members, stereotypes, and inherits,
  implements, composition, aggregation, association and dependency, with parents placed
  above), `tree` (single-parent containment), `timeline` (lanes, to scale, with a long quiet
  stretch shortened and marked, mixed time zones put on one clock, approximate times marked)
  and `waterfall` (spans to scale, the critical path, each span's own time). Each exports to
  Mermaid (`classDiagram`, `flowchart`, `timeline`, `gantt`).
- **A long chain shrank to fit.** A long left-to-right flow now wraps onto rows, choosing the
  number that keeps its text largest on a laptop screen; routes between rows run in the
  corridor between them, so no arrow crosses a box. `wrap` sets or turns it off.
- **The reply did not open with the link.** The script now prints the reply's first line
  before anything else. This is only partly fixed: 14 of 22 replies opened with it in the
  last run, against 6 of 10 at admission. The agent's habit of reporting the build first
  persists; it is the open item.

The first measurement of the new types, on two fresh evals written blind (6 and 7: a trace
and an incident timeline), was weak: two judges preferred the skill in 2 and 1 of 4 pairs.
The pages were right but the agent's account of them was not. The script now computes what
a waterfall or timeline shows (the total, what the whole waited on, spans that mostly wait,
siblings that overlap with the wall-clock time and the misleading sum, spans that outlive
their parent, the longest quiet stretch, time zones) and states it at the top of the page and
in its output. On the next two fresh evals (8 and 9) assertions met rose to 84% against 56%,
but the judges still preferred plain Claude Code on readability: raw milliseconds, findings
hidden in a collapsed section, an author's warning box on a shared page, and a detached span
counted as a cost. Those were fixed: durations read as a person says them, findings and an
`answers` table for the person's own guesses sit at the top of the page, warnings stay in the
terminal, and only the critical path counts as waited on. A bug that put a detached span on
the critical path was fixed too, and the panel's two reach buttons, which had their labels
swapped, now say what they do in each diagram's terms.

Measured on two more fresh evals (10 and 11: a build timing export and a class diagram from
Java source), two trials, two judges, `claude-sonnet-5`:

| Evals | Pairs won, judge 1 | Judge 2 | Assertions met, skill | Without |
|---|---|---|---|---|
| 6 and 7, first version of the new types | 2 of 4 | 1 of 4 | 62% | 56% |
| 8 and 9, with computed findings | 2 of 4 | 1 of 4 | 84% | 56% |
| 10 and 11, final | 4 of 4 | 2 of 4 | 81% | 44% |
| All eleven, final | 20 of 22 | 12 of 22 | 83% | 59% |

The fresh pairs clear the bar of half with both judges. The second judge still prefers plain
Claude Code in about half the pairs overall, most often for a page it finds easier to read.
Evals 6 to 11 have now had their reasons read, so the next revision needs evals of its own.

## Tried and reverted: a reply drafted by the script (0.16.25)

To make the reply open with the link, the script printed a whole reply to send (link,
summary, findings, assumptions, notes, citation count). Measured on all thirteen evals, two
trials: 13 of 26 replies opened with the link, against 14 of 22 without it, because the
agent still wrote a line about the build and then pasted the draft under it. Judge 1's
preference on evals 1 to 11 fell from 20 to 15 of 22 with the replies made longer. It was
reverted. The released skill, on two new evals written blind (12 and 13: a library-holds
repository and an adoption process told in words), was preferred in 4 and 3 of 4 pairs, with
66% of checks met against 38%; one of its four replies opened with the link.

What is left is the agent's habit of reporting a tool run before its result. Three changes
to what the skill says and prints have not moved it past about two in three, and the judges'
preference does not follow it. The next attempt should change something the agent can't
narrate around, or accept the line and stop checking for it.

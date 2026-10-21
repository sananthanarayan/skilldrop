---
rfc: 0063
title: A context graph of the decisions behind a codebase
status: implemented
date: 2026-10-21
author: sanjay-ananth
---

# RFC-0063: A context graph of the decisions behind a codebase

## Problem / use case

**The question.** "Why is it like this?" is the first thing a newcomer asks, and the last thing
anyone checks before changing code. The answer usually exists, in an ADR, an RFC or a design
decision. Most teams' records decay the same ways:
- **A newer decision supersedes an older one,** and nobody updates the older one's Status line.
- **A decision names a folder that has since been deleted.**
- **Two decisions about the same code both say Accepted.**
- **A record cites one that was never written.**

**What a plain agent does.** It reads the first record that matches and answers from it. Then it
supplies a rationale from general knowledge ("Kafka gives you ordering") that the record never
gave.

The owner asked for a context-graph skill. The recommendation was a decision graph, prototyped
and admitted on the same evidence bar as every other skill.

## Fit check

**What it makes:** a concrete answer and a graph, as Markdown, JSON or Mermaid, from files in
the repository.
- **Portable:** a stdlib Python script, plus `git log` (read-only) when asked.
- **Opinionated:** a rationale comes only from a record, and "no recorded decision" is said when
  it's true.
- **Category:** design-phase, beside `adr-generator`, which writes the records this reads. The
  home pack is `solution-architect`.

## Proposal

**`context-graph`, version 0.1.0.** Its script, `context_graph.py`, does three things.

**Finds records** in the usual folders, or the ones named. It reads MADR, Nygard and frontmatter
formats, taking each record's:
- id, title, status and date;
- what it supersedes or amends, and what it cites;
- the paths it governs: those it names in backticks or links, and that exist;
- with `--git`, the commits that mention it.

**Checks the graph:**
- **Problems:**
  - a supersession only one side records;
  - a dangling successor;
  - a current record naming code that is gone;
  - duplicate ids;
  - cycles.
- **Warnings:**
  - a successor that doesn't record the link back;
  - a record marked superseded with no successor named;
  - a reference to a record that doesn't exist;
  - a missing or unrecognised status;
  - a current record citing one that has since been superseded;
  - two current records governing the same path, with neither superseding nor amending the other.

**Answers questions:**
- `--why PATH`: live decisions first, superseded ones marked, and records on a folder above the
  path included.
- `--record ID`: one record with its neighbours, including successors only the newer record
  names.

Outputs Markdown, `--json` and `--mermaid`. Exit 1 means problems were found, and exit 2 means
bad input.

**Also:** 48 unit tests (`tests/test_context_graph.py`) and a fuzz target in
`tests/fuzz/targets.py`. Writing the tests found five parsing bugs, all fixed before measurement:
- a heading id was ignored;
- "rfc" in a filename made a record an RFC;
- date-named files collided as duplicate ids;
- MADR 2's `* Status:` line wasn't read;
- dot-folders were dropped from governed paths.

The author evals found that nested scopes, a folder-wide decision and a file inside it, were
reported as conflicts. The conflict check now requires the exact same path.

## Alternatives considered

- **A code graph** (symbols, calls, imports). That is what agent-ready-repo's `code-intelligence`
  does, with an external Rust binary. Agents already read code well. What they can't see is the
  history of decisions, which is where they go wrong.
- **A general knowledge graph over every doc.** It has no shape to check against, so it couldn't
  say "this is no longer true", which is the part teams lack.
- **A graph database or an embedding index.** Both need dependencies and a service. A
  decision-record folder is small enough to read on every run.

## Decision

Admission results, measured on held-out evals written blind from the description, go here.

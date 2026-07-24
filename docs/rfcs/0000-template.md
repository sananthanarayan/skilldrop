---
rfc: 0000
title: {Noun phrase naming the thing proposed, not the activity — "Skill packs", not "Add packs"}
status: draft   # draft → accepted | rejected → implemented
date: {YYYY-MM-DD}
author: {handle}
---

# RFC-0000: {title}

<!--
Copy this file to docs/rfcs/NNNN-<kebab-slug>.md (next sequential number).
An RFC is required before: a new skill, a new top-level file/directory, a
change to the skill anatomy or manifest schema, or a new repo-wide convention.
It is NOT required for: fixes and improvements to an existing skill, doc
corrections, or eval additions.
Keep it under a page. The RFC records the decision; the PR does the work.
-->

## Problem / use case

{What deliverable or failure mode motivates this. One paragraph, concrete — name the user and the artifact, not "improve developer experience".}

## Fit check

For a new skill, answer the four criteria from AGENTS.md **Authoring a new skill** step 1 — one line each:

- **Concrete artifact:** {what file/output does it produce?}
- **Portable:** {works via plain folder copy in Claude Code and the other IDEs?}
- **Opinionated:** {what decisions does it make instead of asking?}
- **Category:** {which existing README category — or the case for a new one}

For a structural change, instead state which golden rule(s) it touches and why it doesn't break them.

## Proposal

{The shape of the thing. For a skill: proposed `name`, model tier + rationale, `related` list, a 3-bullet sketch of the quality bar, and the top 2 anti-patterns it will ban. For a structural change: the files touched and the new convention stated in one paragraph.}

## Alternatives considered

{At least one, with the reason it lost. "Do nothing" counts.}

## Decision

{Filled in when status moves past draft: what was decided, and — once implemented — the commit or PR that shipped it.}

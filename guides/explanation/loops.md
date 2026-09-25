---
title: Why loops
summary: Why skilldrop sequences skills in a separate primitive instead of letting skills call each other, and why there are four lifecycle loops rather than three.
kind: explanation
---

# Why loops

## The problem a catalogue has

57 skills is enough that a newcomer's first question stops being *"is there a skill for this"*
and becomes *"what order do I do these in, and what stops me shipping something bad"*.

skilldrop always had answers, but only as prose: a README paragraph about "two value streams",
two hand-maintained Mermaid diagrams, a loop schema written inside `agent-loop-design`, and a
hand-off graph spread across 57 `SKILL.md` files. None of it was machine-readable, installable,
or checked. Loops make it all three.

## Why sequencing moved up instead of sideways

The obvious way to get ordering is to let a skill call the next skill. skilldrop refuses to,
and the reason is narrow and load-bearing.

Every skill installs as **one folder, copied verbatim**. That is the whole advantage over
heavier agent platforms: what is reviewed here is byte-identical to what runs in your IDE, and
it works the same in Claude Code, Cursor, Kiro, Continue, Cline, and Aider. The moment a skill
invokes a sibling, it stops working when installed alone — and "installed alone" is the normal
case, because people install what they need.

So the sequencing lives one level up. A **loop** owns the order; a skill never calls a skill.
A skill may *declare* a directed `handoff`, but the loop — or a human — is what acts on it.
Chaining behaviour, no loss of portability.

The same reasoning shapes the install: `LOOP.md`'s frontmatter is deliberately identical to
`SKILL.md`'s, so a loop installs into the skills directory and becomes invokable without any
target needing a loop concept of its own.

## Why the hand-off `fallback` is mandatory

Skills install à la carte, so a loop will routinely name a skill the environment lacks. The
repo's rule was already "a dangling hand-off is never an error" — but that was prose, and an
agent under pressure ignores prose.

Making `fallback` a required field turns it into a contract: every hand-off states what to do
when its target is absent. A hand-off now degrades in a stated, reviewable way instead of
dead-ending or being silently skipped.

## Why four loops, not three

The obvious model is discovery → build → release. skilldrop uses four plus a wrapper, on the
criterion that actually distinguishes them: **reversibility**, which is also what decides who
is allowed to sign off.

| Loop | Mistake costs | So the gate is |
|---|---|---|
| `discover` | a re-brief | a **human** — no check can tell you that you solved the wrong problem well |
| `design` | months, unwound in code | a **review panel** — independent positions, recorded dissent |
| `build` | a revert | **mechanical** — a script's exit code, which cannot be argued with |
| `operate` | live users; irreversible | a **human** closing the incident |

Three loops do not fit this catalogue. `design` is 15 skills and does not fold into discovery
without losing the panel gate that makes it worth having. The SRE skills have no home at all
in a three-loop model, and `operate` is the only loop whose failures cannot be undone — the
one place a gate matters most.

`ship-a-draft` is deliberately **not** a lifecycle stage. It is a wrapper whose middle is any
generator: collect the input properly before, check the argument and the surface after. It
applies to an ADR, a deck, or a postmortem alike, which is exactly why it cannot be a phase.

## What this buys

A stranger can install one command and get a way of working, rather than a list of 57 things
to choose between. And because the loops are data rather than prose, the diagrams cannot drift
from them, a renamed skill breaks a check instead of a silently-wrong document, and a gate
cannot quietly become decorative.

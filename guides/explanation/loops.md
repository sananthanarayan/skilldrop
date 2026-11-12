---
title: Why loops
summary: Why skilldrop sequences skills in a separate primitive instead of letting skills call each other, why the lifecycle has five stages rather than three, and why only some of them run as loops.
kind: explanation
---

# Why loops

## The problem a catalogue has

Past fifty skills, a newcomer's first question stops being *"is there a skill for this"*
and becomes *"what order do I do these in, and what stops me shipping something bad"*.

skilldrop always had answers, but only as prose: a README paragraph about "two value streams",
two hand-maintained Mermaid diagrams, a loop schema written inside `agent-loop-design`, and a
hand-off graph spread across every `SKILL.md`. None of it was machine-readable, installable,
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

## Why five stages, not three, and a loop for only one of them

The obvious model is discovery → build → release. skilldrop uses five stages, on the
criterion that actually distinguishes them: **reversibility**, which is also what decides who
is allowed to sign off.

| Stage | Mistake costs | Who decides |
|---|---|---|
| Find the problem | a re-brief | **you** — no check can tell you that you solved the wrong problem well |
| Decide how to build it | months, unwound in code | a **review panel** (`council-review`) — independent positions, recorded dissent — then **you** record the decision |
| Build it | a revert | **mechanical** — `pre-merge-review`'s script exit code, which cannot be argued with — then **you** merge |
| `release` | users and data, often irreversible | a **review** on evidence (can it ship?), then a **human** (should it ship now?) |
| Run it | live users; irreversible | **you**, closing the incident |

Three stages do not fit this catalogue. The design skills (requirements for quality, diagrams,
design docs, contracts, threat models, ADRs) do not fold into discovery without losing the
panel gate that makes them worth having, and the SRE skills have no home at all in a
three-stage model.

Finding the problem, deciding how to build it, building it and running the service had loops
too, and all four were retired. On held-out evals, their own skills used without the loop were
preferred: the loops' gates stopped for decisions the person had already made, their replies
carried gate jargon, and the build and design loops' rebuilds each traded one failure for
another on the next evals. Those stages now run as their skills,
in order, and the decisions stay with you.

`ship-a-draft` is deliberately **not** a lifecycle stage. It is a wrapper whose middle is any
generator: collect the input properly before, check the argument and the surface after. It
applies to an ADR, a deck, or a postmortem alike, which is exactly why it cannot be a phase.
The gate codes follow the same order. The whole number is the stage's place in the
lifecycle, G3 at `release`, and a decimal is a second gate inside the same
loop, so G3.1 is the human go/no-go that follows the G3 readiness review. G0, G1, G2 and G4 went
with the retired loops and are not reused. The loops outside the lifecycle take the next numbers,
from G5 for `ship-a-draft` upward. The [operating model](operating-model.md) draws every stage
and gate on one page.

## What this buys

A stranger can install one command and get a way of working, rather than a list of skills to
choose between. And because the loops are data rather than prose, the diagrams cannot drift
from them, a renamed skill breaks a check instead of a silently-wrong document, and a gate
cannot quietly become decorative.

# {System / feature} — How it works

**Who this is for:** {e.g. "an engineer joining the payments team" / "an adjacent team integrating with us"}
**After reading, you'll be able to:** {concrete capability — "trace a checkout request end-to-end and know which service owns each step"}
**Status:** describes the system as built on {YYYY-MM-DD}. For *why we chose this design*, see {link to ADRs / design-doc}.

## The mental model

{One paragraph or one diagram. The single idea a reader must hold to understand everything below — e.g. "Every write goes through the command bus; reads come straight from a denormalized view. Nothing reads the write tables directly."}

```
{Optional ASCII or Mermaid sketch — or link to an architecture-diagrams output. Keep it to the load-bearing boxes and arrows, not every box.}
```

## Components

What each piece does and why it exists — not how to deploy it.

| Component | Responsibility | Why it's separate |
|---|---|---|
| {name} | {one line — what it owns} | {what would break if it were merged into its neighbour} |
| {…} | … | … |

## How a {request / event / job} flows through

Trace one representative path step by step. This is the heart of the walkthrough.

1. **{Entry point}** — {what happens, which component, what data} → `{file or module:fn}`
2. **{Next hop}** — {…} → `{file:fn}`
3. **{…}** — {…}
4. **{Result}** — {what the caller gets back / what side effect lands}

> Trace it yourself: {how to watch this flow live — a log query, a trace ID, a debug endpoint}.

## Key design decisions (and why)

The non-obvious choices a reader will otherwise undo by accident.

- **{Decision}** — {why; what was rejected}. {Link to the ADR if one exists.}
- **{Decision}** — {…}

## Data & state

- **Source of truth:** {where the canonical data lives}
- **Derived / cached:** {what's a projection of it, and how it's kept in sync}
- **What's NOT persisted:** {e.g. "session state is in memory; a restart drops it — by design"}

## Where the code lives

| Concern | Path | Notes |
|---|---|---|
| {entry points / routes} | `{path}` | {…} |
| {core logic} | `{path}` | start here when reading |
| {data layer} | `{path}` | … |
| {tests worth reading first} | `{path}` | the integration tests document the contract |

## Making common changes

How to do the things a new contributor will need in week one.

- **Add a {new endpoint / event / field}:** {the 2–4 places to touch, in order}
- **Change {common thing}:** {…}

## Gotchas / sharp edges

- ⚠️ {Non-obvious constraint that will bite — "the queue is at-least-once; handlers must be idempotent"}
- ⚠️ {…}

## Glossary

- **{Term}** — {definition in this system's context, not the generic one}
- **{Term}** — {…}

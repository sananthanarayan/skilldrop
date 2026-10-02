# Rubric: Generic

Use this when the doc doesn't cleanly match any of the skilldrop archetypes (ADR, design doc, runbook, exec summary, tech-comparison, deck, decision log). Also use when the doc is a *blend* (e.g. "a design doc that's also being used as a runbook" — pick one as primary and flag the dual-use).

The first finding is usually whether the doc is the **wrong artifact for the job**.

## Blockers
- **Purpose is clear in the first paragraph.** The reader must know what kind of doc this is and what it's for.
- **The doc has a single audience.** Trying to address "execs + engineers + customers" in one doc almost always fails one of them.
- **The doc makes a claim or a request.** If after reading it the user doesn't know what action is being requested or what conclusion was reached, the doc has no point of view.
- **No `TBD` / `<insert later>` left in a doc being shared.**

## Major
- **Section ordering matches the reader's path.** What does a reader who skims need first? That's slide 1, paragraph 1, section 1.
- **Claims have evidence.** Numbers, quotes, links — not assertions in a vacuum.
- **The doc is the right length** for its purpose. A 12-page doc when a 1-pager would do, or vice versa.
- **Wrong artifact:** the situation needed an ADR but the user wrote a design doc, or vice versa. Verdict: `WRONG ARTIFACT` + recommend the correct skilldrop skill.

## Minor
- **Title is descriptive** — a reader scanning a doc index can tell what's inside.
- **Last-updated date present.**
- **Owners / authors named.**
- **Cross-links** to related docs (ADRs, design docs, dashboards).

## Nits
- Heading hierarchy.
- Tense consistency.
- Code-block language tags.

## Anti-patterns to flag (always major)
- Burying the recommendation / conclusion.
- Sections of "background" longer than the conclusion.
- Hedging language masking a real position ("we believe", "it could be argued", "potentially").
- Footnotes that contradict the body.

## What's working — look for
- A clear point of view stated up front.
- Section ordering that respects the reader's path.
- Honest acknowledgement of what the doc *doesn't* cover.
- Cross-links to related artifacts (no doc is an island).

# Rubric: Design Doc

Mirrors `design-doc`'s quality bar.

## Blockers
- **"Why now" is present.** No forcing function = a design doc that can be postponed indefinitely. Refuse to ship.
- **Goals and non-goals both exist.** A missing non-goals section means scope will eat the project.
- **Proposal is the longest section.** If "Background" or "Alternatives" is longer than "Proposal", the doc has buried the lede.
- **At least 2 alternatives** each with a *why-not*. "We didn't pick X" with no reason is not an alternative.
- **Risks have mitigations.** A bare risks list is anxiety, not engineering.

## Major
- **Non-goals are real, not throat-clearing.** ❌ *"We're not solving world hunger"* ✅ *"v1 will not migrate existing customers."*
- **Rollout criteria are concrete.** ❌ *"We'll monitor closely"* ✅ *"Roll forward to 100% if p99 < 80ms for 48h after 10% rollout."*
- **TL;DR is self-contained.** A reader who stops after the TL;DR should know what's being proposed and the recommendation.
- **Diagrams where structural.** Long prose for things a flowchart would convey in 10 seconds is a smell.
- **Open questions name owners.** "We need to figure out X" with no one tagged means X won't get figured out.

## Minor
- **Length: 2–5 rendered pages.** Longer means the doc is reference material in disguise, or solving two problems at once.
- **Status field present and current** (`Draft | In Review | Approved`).
- **Author + date** at the top.
- **Active voice when assigning ownership** ("Team Foo will own X", not "X will be owned").
- **Inline links to ADRs / runbooks / dashboards** that the doc references.

## Nits
- Heading hierarchy consistency.
- Code-block language tags.
- Acronyms expanded on first use.

## Anti-patterns to flag (always major)
- Implementation detail before problem statement.
- "Future work" section that doubles the doc length with hypotheticals.
- Passive voice masking ownership ("it will be deployed" — by whom?).
- "We already know what to do" alternatives section that skips the analysis.

## What's working — look for
- A genuine non-goal that constrains scope.
- A concrete rollback criterion with a number.
- An "Open question" with a named owner.
- Diagrams that *replace* prose rather than decorate it.
- Honest trade-offs in the recommended approach (not just upsides).

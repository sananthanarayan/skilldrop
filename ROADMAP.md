# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Rebuild five more skills around their rule** ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)): `postmortem-generator`, `design-doc`, `ai-usage-policy`, `guide-builder`, `devils-advocate`. One at a time, with the rule first and the user's own format. Each is measured on two new evals before and after, and ships only if both judges prefer it in at least half the pairs. One that misses is retired. Done: `source-synthesis` in 0.16.14 (1 and 0 of 4 pairs before, 3 and 3 after) and `release-notes` in 0.16.15 (3 and 3 before, 4 and 4 after).
- **Held-out evals for every skill** — 12 skills now have evals they were never revised against; the published number should be split into the two kinds for all of them.
- **A shortlist skill for `career`** — run the fit check across an employer's open roles. Needs network access the benchmark sandbox lacks, so it waits on a way to measure it.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

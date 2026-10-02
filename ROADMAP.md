# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Skills a blind judge prefers** — the catalogue-wide benchmark shows skills meeting far more of their own checks than the agent alone, and only a slight blind preference for their results. Next: make skills deliver from what they were given instead of stopping, and remove hand-off lines from inside the artifact, measured with two trials and two judges.
- **Three or more evals per skill** — most skills have one acceptance eval, so a per-skill number is an anecdote. The three skills added in 0.16.4 set the pattern.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

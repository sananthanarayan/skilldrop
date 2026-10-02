# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Skills a blind judge prefers** — after 0.16.6 two blind judges prefer skills' results in about three pairs in five. Next: the skills still below even, starting with the three that got worse in the last round (`deck-builder`, `file-to-markdown`, `delivery-metrics-report`), and evals the skills have not been revised against.
- **Three or more evals per skill** — most skills have one acceptance eval, so a per-skill number is an anecdote. The three skills added in 0.16.4 set the pattern.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Skills that hold up on evals they have not seen** — 12 revised skills given new evals lost to plain Claude Code in about 7 pairs of 10 ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md)). Next: a rule in each that sizes the output to the request, and a decision on skills that add a format and no rule the plain agent breaks.
- **Held-out evals for every skill** — 15 skills now have evals they were never revised against; the published number should be split into the two kinds for all of them.
- **The `career` pack on real applications** — the fabrication comparison uses invented people; the next evidence is the `apply` loop run on real postings, reported without the documents.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Re-tier from measurement.** All three tiers now have the 224 held-out evals ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md#the-three-tiers)). The skill is not preferred to the plain agent on any of them, and the standard tier (`claude-sonnet-5`) scores below the light one (`claude-haiku-5-5`) with the skill and without it, most likely because it maps to a model a generation older. First decide which model the standard tier maps to; then run a second trial on all three and set each tier from the numbers, looking first at what the skills lose to plain Opus 5.5.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

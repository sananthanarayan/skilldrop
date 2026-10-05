# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Skills that hold up on evals they have not seen** — 12 revised skills given new evals lost to plain Claude Code in about 7 pairs of 10 ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md)). Next: a rule in each that sizes the output to the request, and a decision on skills that add a format and no rule the plain agent breaks.
- **Held-out evals for every skill** — 15 skills now have evals they were never revised against; the published number should be split into the two kinds for all of them.
- **`job-fit-analysis`** — the two judges disagree about it (8 and 5 of 10 pairs on its tuned evals), and its headline count still sometimes contradicts its own table. It is the next `career` skill to work on ([RFC-0043](docs/rfcs/0043-application-form-answers.md)).
- **A shortlist skill for `career`** — run the fit check across an employer's open roles. Needs network access the benchmark sandbox lacks, so it waits on a way to measure it.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

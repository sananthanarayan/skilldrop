# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Decide which skills to keep** — 12 skills revised twice from a blind judge's reasons improved on the evals the reasons came from and not on fresh ones ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md)). Each now has an answer to "what rule does it add that the plain agent breaks", in [RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md), a draft awaiting a decision. It proposes keeping one skill, rebuilding seven around their rule against a fresh held-out bar, and retiring four that only add a format, with a `retired` record so an installed copy says why it stopped updating.
- **Held-out evals for every skill** — 15 skills now have evals they were never revised against; the published number should be split into the two kinds for all of them.
- **A shortlist skill for `career`** — run the fit check across an employer's open roles. Needs network access the benchmark sandbox lacks, so it waits on a way to measure it.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. Running all three shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

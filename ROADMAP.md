# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Publish the benchmark on the current catalogue.** Every skill now has held-out evals and the summary splits them from the author's; the published run is still the 0.16.9 catalogue. A full run of 376 evals is about $50 of plan usage and several hours.
- **The light and heavy tiers** — the benchmark has run on the standard tier only. `run_bench.py --held-out --models light,heavy` on the 224 held-out evals is about $80 of plan usage and shows where a cheaper model is enough.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing, containment, org governance), live evals, new skills and loops, and docs depth.

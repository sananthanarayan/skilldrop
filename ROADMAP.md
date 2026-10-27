# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Re-tier from measurement.** The standard tier now maps to Sonnet 5.5 and has run on all 308 held-out evals ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md#standard-on-sonnet-55)). Next, a second trial on light (about $85 of plan usage) and heavy (about $280) on the same evals, then set each skill's tier from the numbers.
- **What the skills lose to the plain agent on current models.** On the held-out evals nothing was decided on, the judges preferred plain Sonnet 5.5 to the skill in about two pairs of three, and plain Opus 5.5 in about seven of ten. Once the tier trials are in, pick the skills that lose on both trials with both judges, and ask of each what rule it adds that the plain agent breaks: keep, rebuild rule-first, or retire ([RFC-0046](docs/rfcs/0046-keep-rebuild-or-retire.md)). For the 44 skills that ship scripts, `run_bench.py --tools-arm` says whether the instructions or the scripts carry the result ([RFC-0067](docs/rfcs/0067-scripts-without-instructions.md)). Over two trials ($213.05), neither beat the plain agent blind, and the instructions came out even with the scripts alone. The five skills that lost in each trial with both judges have been decided: four retired and `file-to-markdown` rebuilt ([RFC-0068](docs/rfcs/0068-five-skills-that-lost-to-the-plain-agent.md)). Next are the three that lost over both trials together, `ai-usage-report`, `judge-audit` and `lean-canvas`, and a re-run of `figma-diagrams` now that the benchmark installs its package. Five others gained from their instructions ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md#the-scripts-without-the-instructions)). Don't read the clean evals' judge reasons before that list is fixed; measure any rebuild on fresh evals.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

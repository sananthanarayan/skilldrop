# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Measure the older loops.** Each of the 11 loops from before 1.3.0 now has two held-out evals, written blind from its description ([what the benchmark showed](guides/explanation/what-the-benchmark-showed.md)). The four new loops were measured first: each beat the plain agent, but only `ship-agent` clearly beat its own skills, and `adopt` lost to them in every pair. Next, ask the RFC-0046 question of `adopt`, then run the same benchmark on the older 11, with `run_bench.py --loops ... --held-out --trials 2 --second-judge claude-opus-5-5`. Any loop that its own skills beat gets the RFC-0046 question, asked of a loop.
- **Rebuild `judge-audit` around the one rule it adds:** report each run on its own, and name the items that flipped ([RFC-0072](docs/rfcs/0072-the-last-three-and-figma-diagrams.md)). Measure it on fresh blind evals with `--allow-bash`, so its script isn't held for approval.
- **A new baseline with `--allow-bash` on.** Until now, a compound command was held for an approval nobody could give, in every arm. The next full run turns it on, and its numbers replace the published ones instead of being compared with them.
- **Oracles for the four skills measured heavier.** `bug-triage`, `prd-draft`, `prompt-caching-advisor` and `subagent-design` met more than 5 points more checks on heavy in both tier trials. Each moves to heavy once it ships an `examples/` input-to-output oracle ([RFC-0073](docs/rfcs/0073-tiers-from-two-trials.md)).

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

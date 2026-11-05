# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Keep gate jargon out of every loop's reply.** In the loop benchmark, the closing gate line, verdict words and run-log talk were the commonest reason a loop lost ([RFC-0074](docs/rfcs/0074-loops-measured-four-retired.md)). Every remaining `LOOP.md` writes the verdict to the run log only and answers the person in plain words. Then every loop is measured again on fresh blind evals, and any that still loses to its own skills is retired.
- **Rebuild `measure`.** When the people asked hand the call to the analyst, it proposes a definition, marked unconfirmed; it delivers what can be built now and says plainly who confirms what; it leaves out the spec when only the numbers were asked for.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

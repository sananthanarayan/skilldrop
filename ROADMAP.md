# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Get `build` and `design` ahead of plain Claude Code.** Rebuilt, both now beat their own skills, but they still lose to the plain agent more often than they win ([RFC-0084](docs/rfcs/0084-build-and-design-rebuilt.md)). The judges' reasons name two side effects of the rebuild:
  - **build** restates what it didn't do ("nothing was merged or pushed", "no quiet data-loss cases") where none of it applied;
  - **design** keeps the risks it finds out of the ADR altogether, where the house format wants them listed as open, and edits accepted records the house rules said to leave alone.

  The fix is measured on fresh held-out evals against the plain agent as well as the skills.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

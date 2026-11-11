# Roadmap

What is being worked on next. Not a commitment — a direction. Shipped work moves to [CHANGELOG.md](CHANGELOG.md).

## Upcoming

- **Rebuild `build` and `design`, then measure them a third time.** With plain-words replies, both still lost to their own skills ([RFC-0083](docs/rfcs/0083-loop-replies-in-plain-words.md)). Neither leaked gate jargon. They lost on what the loop pushed the agent to do:
  - **build** edited someone else's change when it should have reported a failed check, and missed a data-loss edge case its skills caught;
  - **design** wrote into an ADR conditions the decider never set, and named files it hadn't written;
  - **both** narrated a review panel the agent had seated itself.

  If either loses a third time, it's retired, and its skills are run in order instead.

## Considering

Everything else raised in the 2026 reviews and not yet built, with why, size and dependencies, is in
[docs/designs/future-ideas.md](docs/designs/future-ideas.md): distribution, the remaining OWASP gaps
(signing catalogues), live evals, new skills and loops, and docs depth.

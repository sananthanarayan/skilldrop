# Engineering policy - AI coding agents (v2, March 2026)

1. Agents run on developer laptops only. Agents have no access to CI runners, staging or
   production credentials.
2. Agents may not open pull requests themselves; the engineer who ran the agent opens the PR.
3. Every PR containing agent-authored code needs approval from two human reviewers, at least one
   of whom must be a senior engineer. We have 12 senior engineers.
4. Agent-authored PRs are labelled `agent` so they can be tracked.
5. Human-only PRs need one reviewer (any level).

Note added 30 September 2026 (from the CFO): no new tooling contracts or tier upgrades will be
approved before the FY27 budget is set in April 2027. Existing licences continue.

Note added 6 October 2026 (from the head of platform): senior engineers report spending about
40% of their week on code review.

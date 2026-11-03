# Agent brief: weekly changelog drafter

**Team:** Platform, Kestrel Point
**Owner:** Platform engineering lead (Dana Whitcombe)
**Launch target:** first Friday of December 2026

## What it does
Every Friday at 14:00 UTC, the agent reads the pull requests merged into our private `platform` monorepo in the last 7 days and drafts a release-notes section for CHANGELOG.md, grouped by the PR's label (feature, fix, security, internal). It commits the change to a new branch `changelog/YYYY-MM-DD` and opens a pull request. An engineer reviews and merges it. The agent never merges.

## Inputs
- Merged PR titles, descriptions and labels, read with the `gh` CLI.
- The current CHANGELOG.md.
- About 40 merged PRs a week; descriptions average around 600 words.

## Who writes the input
- Our engineers, plus two contractors from an outside agency who open PRs against the repo.
- PR descriptions for bug fixes often paste the customer's bug report from the support portal verbatim, so customer-written text ends up in the input.

## What it must not do
- Push to any branch other than `changelog/*`.
- Edit any file other than CHANGELOG.md.
- Talk to anything other than our git host. It needs no other network access.

## How it runs
- Claude Code in headless mode on the CI runner, with the project settings in claude-settings.json.
- Authenticated as the `platform-bot` account. Its token has repo scope on all 140 repositories in our org.

## Cost
- Finance has asked for this to stay under $20 a month.
- Last spring a home-made script that did this retried a failing commit in a loop all weekend and cost $310. We want a hard stop this time.

## Done means
- A pull request updating CHANGELOG.md is open for review, every merged PR from the week appears in it exactly once, and nothing in it came from instructions inside a PR description.

# Maintainers

This file lists the people authorised to **review, approve, and merge** pull requests into `main`.

## Current maintainers

| Name | GitHub | Role | Scope |
|---|---|---|---|
| Sanjay Ananthanarayan | [@sanjay-ananth](https://github.com/sanjay-ananth) | Lead maintainer | All skills, repo policy, releases |
| Sanjay Ananthanarayan | [@sananthanarayan](https://github.com/sananthanarayan) | Lead maintainer | All skills, repo policy, releases |

Both lead maintainers have equal authority. Either may review, approve, and merge a PR; approval from one is sufficient under the current branch-protection policy (`required_approving_review_count: 1`).

## What maintainers do

- Review every incoming PR against the [CONTRIBUTING.md](CONTRIBUTING.md) PR checklist.
- Approve PRs that pass the checklist and quality bar.
- Merge approved PRs. **Only maintainers may merge.**
- Cut releases by bumping `.claude-plugin/plugin.json` and tagging.
- Triage issues and proposals; close out-of-scope or stale work.

## What contributors do

- Open a branch, make changes, open a PR — see [CONTRIBUTING.md](CONTRIBUTING.md#branching-prs-and-merging) for the full rules.
- Respond to review feedback. Push fixes to the same branch.
- **Do not self-merge**, even with admin access. The protected-branch rule and the maintainer review are the same safety net; bypassing one is bypassing both.

## Becoming a maintainer

We don't have a formal nomination process yet because the repo is small. As a rough bar: a contributor who has landed **3+ non-trivial PRs**, demonstrates the project's [voice and tone](CONTRIBUTING.md#voice--tone-the-most-important-section), and engages constructively in review may be invited as a maintainer by an existing maintainer. Open an issue if you want to discuss it.

## Maintainer responsibilities (in order of priority)

1. **Keep the bar high.** Reject PRs that don't meet the quality bar even if they're well-intentioned — it's kinder than a slow-rotting merged skill.
2. **Be timely.** Acknowledge new PRs within a week. A response of "I'll look at this next weekend" is better than silence.
3. **Document decisions.** When a PR is closed without merging, leave a comment explaining the reason — it's how future contributors learn the project's taste.
4. **Eat our own dog food.** Use `doc-critique` on incoming SKILL.md changes; use `devils-advocate` on incoming script changes. The skills should pass their own rubrics.

## Emergency / security contact

For security-sensitive issues (vulnerable dependencies, leaked credentials in templates, etc.) — **don't open a public issue**. Contact either lead maintainer directly via GitHub, or by the email in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

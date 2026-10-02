# Dev team

Build-and-ship: story splitting, implementation with adversarial review, test plans, triage, pull request descriptions, a ranked technical-debt register, migrations, launch readiness, release notes, agent-policy files, and code-quality gates.

`/plugin install dev-team@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Find out whether your current branch is safe to merge

Paste this into Claude Code:

```text
Is this branch safe to merge? Run a pre-merge review on the current diff.
```

- **Before you start:** A git repository with changes on a branch
- **Before you start:** The reviewer subagents, for the full panel: `skilldrop install --panel review` (the Claude plugin includes them)
- **How to tell it worked:** pre-merge-review runs the project's lint, typecheck and tests through its gate script, then the reviewer panel, and ends with READY or NOT READY.
- **If nothing happens:** If the gate script cannot find your lint or test commands, tell it what they are. If the panel is skipped, install the reviewer subagents with `skilldrop install --panel review`.

## Loops

- `ship-a-draft`
- `build`
- `release`

## Skills

- `accessibility-audit`
- `agents-md-generator`
- `brief-intake`
- `bug-triage`
- `contribution-wizard`
- `council-review`
- `devils-advocate`
- `doc-critique`
- `feature-implement-loop`
- `launch-readiness`
- `migration-plan`
- `output-hygiene`
- `pr-description-writer`
- `pre-merge-review`
- `release-notes`
- `sonar-onboard`
- `sonar-review`
- `tech-debt-register`
- `test-plan-generator`
- `user-story-splitter`

More: https://sananthanarayan.github.io/skilldrop/packs/dev-team/

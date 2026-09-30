---
title: Use skilldrop with GitHub Projects
summary: Pipe GitHub issues and project boards into skilldrop skills — implementation loops, review gates, and release notes that trace back to issues.
kind: how-to
---

# Use skilldrop with GitHub Projects

In Claude Code the `gh` CLI is available — you can ask the agent to fetch issue and PR text directly rather than copying it manually.

## Implementation from an issue

Fetch the issue inline and pass it to the skill:

```
gh issue view 42 and then run feature-implement-loop on it.
```

Or copy the issue text manually and reference the number for traceability:

```
GitHub issue #42: [paste title and body]
Acceptance criteria: [paste from issue body]

Run feature-implement-loop.
```

The issue number in the session means any output (files created, commit messages, PR descriptions) can be linked back to the issue.

## Pre-merge review as a PR gate

`pre-merge-review` maps directly onto a GitHub PR review. After implementing:

1. Open a draft PR for the branch
2. Run `pre-merge-review` — it fires `devils-advocate`, `security-reviewer`, and `code-quality` in parallel
3. Address any findings
4. Mark the PR ready and merge only after all three reviewers pass

```
The diff is on branch feature/proj-42. Run pre-merge-review.
```

This keeps the review panel's findings tied to the PR and auditable.

## Release notes from merged PRs

At the end of a release cycle, fetch the merged PR list and pass it to `release-notes`:

```
Here are the PRs merged to main since the last release:

$(gh pr list --state merged --base main --limit 20 --json number,title,body \
  --template '{{range .}}#{{.number}} {{.title}}{{"\n"}}{{end}}')

Run release-notes.
```

The skill groups changes by type (features, fixes, internal) and formats a changelog entry.

## Story splitting from a milestone

Copy the open issues in a milestone and split them into implementable slices:

```
Here are the open issues in milestone v2.0:

$(gh issue list --milestone "v2.0" --json number,title --template \
  '{{range .}}#{{.number}} {{.title}}{{"\n"}}{{end}}')

Run user-story-splitter.
```

The output slices can be created as new issues or sub-tasks in a GitHub Project board.

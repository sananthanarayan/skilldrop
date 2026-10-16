---
title: Run a skill in CI
summary: Use the skilldrop GitHub Action to run a skill on every pull request, such as a document critique or a pre-merge review, post the result to the job summary, and optionally fail the check on a verdict.
kind: how-to
---

# Run a skill in CI

You can run a skill on every pull request with the skilldrop GitHub Action, read its answer in the job summary, and fail the check on a verdict you name.

No pack needs installing: the action reads the skill from skilldrop's catalogue, or from your repo. It sends the skill to Claude and runs none of its scripts, so keep your real lint and test gate as its own step. Every input, output and limit is on [The skilldrop GitHub Action](../reference/ci-action.md).

## Save your API key

Store an Anthropic API key as a repository secret.

```bash
gh secret set ANTHROPIC_API_KEY
```

It prompts for the key and saves it, the same as adding it under *Settings → Secrets and variables → Actions*.

## Critique every changed design doc

Add this workflow as `.github/workflows/doc-review.yml`.

```yaml
name: doc review
on:
  pull_request:
    paths: ["docs/**/*.md"]
permissions:
  contents: read
jobs:
  critique:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: sananthanarayan/skilldrop@main   # pin to a SHA
        with:
          skill: doc-critique
          input: "Critique the design docs changed in this pull request."
          diff-base: origin/${{ github.base_ref }}
          fail-on: "MAJOR REWRITE|WRONG ARTIFACT"
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

The critique lands in the run's summary page, and a MAJOR REWRITE or WRONG ARTIFACT verdict fails the check; leave `fail-on` out to report without blocking.

## Pin the action to a commit

Replace `@main` with a commit SHA, as you would for any third-party action.

```bash
git ls-remote https://github.com/sananthanarayan/skilldrop refs/heads/main
```

It prints the latest commit on `main`; put that SHA after `sananthanarayan/skilldrop@`.

## Run your own skills

Point the action at your repo to run a skill you wrote.

```yaml
      - uses: sananthanarayan/skilldrop@<sha>
        with:
          skill: my-skill
          catalog: .
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

It finds `my-skill` under `.claude/skills/`, `.agents/skills/`, `skills/` or `packs/` in your checkout.

---
title: Run a skill in CI
summary: Use the skilldrop GitHub Action to run a skill on every pull request, such as a document critique or a pre-merge review, post the result to the job summary, and optionally fail the check on a verdict.
kind: how-to
---

# Run a skill in CI

The repo root is a GitHub Action. It sends a skill's `SKILL.md` (with the reference files it
links) to Claude as the system prompt, gives it your input, writes the answer to the job
summary and a file, and can fail the step when the answer contains a verdict you name.

Nothing in the skill is executed. Skills that normally run a script (like `pre-merge-review`'s
gate) are told they can't, and reason through it by hand instead, naming the command to run.
Run the script in its own step if you need its real exit code.

## Before you start

- An Anthropic API key, saved as a repository secret named `ANTHROPIC_API_KEY`
  (*Settings → Secrets and variables → Actions*).
- Pin the action to a commit SHA, as you would any third-party action. The examples use `@main`
  for readability only.

## Critique every changed design doc

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

The critique lands in the run's summary page. With `fail-on` set, a verdict of MAJOR REWRITE
or WRONG ARTIFACT fails the check; leave `fail-on` out to report without blocking.

## Inputs

| Input | Default | What it does |
|---|---|---|
| `skill` | required | The skill's name: `doc-critique`, `pre-merge-review`, `release-notes`, … |
| `input` | — | The request text |
| `input-file` | — | A file appended to the request, such as a generated report |
| `diff-base` | — | A git ref; `git diff <ref>...HEAD` is appended. Check out with `fetch-depth: 0`. |
| `catalog` | skilldrop's catalogue | Where to find the skill: a skilldrop catalogue, or any folder of `<skill>/SKILL.md`. Use `.` for skills in your own repo (`.claude/skills/`, `.agents/skills/`, `skills/` and `packs/` are all searched). |
| `model` | `claude-sonnet-5-5` | Any Claude model ID |
| `max-tokens` | `8000` | Output cap |
| `fail-on` | — | A regular expression; the step fails when the output matches |
| `output-file` | `skill-output.md` | Where the output is written, for a later step to post as a PR comment or upload |
| `anthropic-api-key` | required | Pass `${{ secrets.ANTHROPIC_API_KEY }}`, never a literal |

Outputs: `output-file`, and `failed` (`true` when `fail-on` matched).

## Good fits

- `doc-critique` on changed ADRs, design docs and runbooks
- `release-notes` on `diff-base: <last tag>` to draft the notes for a release PR
- `pre-merge-review` as an advisory second reviewer, with the real lint and test gate as its own step
- Your own skills, with `catalog: .`

## Cost and privacy

Each run is one API call: the skill's files plus your input in, the answer out. A diff and a
skill together are usually well under 50k input tokens. The input goes to the Anthropic API
under your key and your organisation's data terms. Don't point it at files you couldn't send
there.

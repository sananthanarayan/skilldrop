# Security policy

## Reporting a vulnerability

**Do not open a public issue.** Use GitHub's [private vulnerability reporting](https://github.com/sananthanarayan/skilldrop/security/advisories/new) — it creates a private advisory only the maintainer can see.

Expect an acknowledgement within 7 days. If a fix ships, the advisory is published with credit unless you ask otherwise.

## What counts as a vulnerability here

skilldrop has an unusual threat surface, because **a skill is instructions an AI agent will follow**. Two distinct things are worth reporting:

**In this repo's code and supply chain**
- Anything that makes `skilldrop install` write outside its target directory — path traversal via a skill name, a catalog entry, or a `--dest` value
- Anything that causes catalog content to be *executed* rather than copied (see the guarantee below)
- A weakness in the release pipeline that could publish `skilldrop-cli` without a maintainer's commit
- Secrets, tokens, or personal data committed to this repo

**In a skill's instructions**
- A `SKILL.md` that directs an agent to exfiltrate data, weaken a security control, or run something destructive
- A skill's `scripts/` that reads credentials it has no reason to read, or sends data anywhere other than the API it documents

The second category is a real bug class, not a theoretical one — [`agent-threat-model`](packs/ai-engineering/skills/agent-threat-model/SKILL.md) is the lens this project uses for it.

## What the installer guarantees

- **Install copies files. It never executes catalog content.** Not on install, not on update. If you find a path where it does, that is a vulnerability — report it.
- **Third-party catalogs are not trusted.** `--from` prints a review-before-use warning, because a stranger's `SKILL.md` is a stranger's instructions to your agent.
- **Hooks are opt-in.** They wire only under `--with-hooks`, and the CLI prints every file it wrote. See [RFC-0006](docs/rfcs/0006-per-ide-hooks.md).

## Not vulnerabilities

- A skill producing low-quality or wrong output. That's a bug — open an issue.
- Prompt injection *against an agent you pointed at untrusted content*, when skilldrop's role was only to supply the instructions you chose to install. Model that with `agent-threat-model`.
- Unpinned Python ranges in a skill's `requirements.txt`. Known, tracked, and installed on your machine under your control — a hardening item, not a live vulnerability.

## Keeping your identity out

This repository is public, and two things try to publish its maintainers without asking. An
agent session knows who is signed in, and a model will write that name into a document's
Author or contact field. Git records whatever email the machine is configured with. Four
guards stop both ([RFC-0049](docs/rfcs/0049-identity-guard.md)), and none of them needs your
private details written anywhere in the repository: [`privacy.py`](privacy.py) reads them from
the machine it runs on (the signed-in Claude account, git config, your user name and home
directory) and reports a match by kind, never by printing it.

| Guard | Where | What it stops |
|---|---|---|
| `pre-commit` and `commit-msg` hooks | each clone (`.githooks/`) | your name, email, organization or home path in a staged change or a commit message; a commit email that is not a GitHub noreply address |
| `python3 validate.py` | locally and in CI | the same, across every tracked file |
| `Commit identities are noreply` | CI, every push and pull request | any commit whose author or committer email is not a GitHub noreply address, whoever pushed it |
| `run_bench.py` | each benchmark run | outputs that name you are counted in the report and redacted in `results.json`; `--publish` refuses a summary that names you |

Your name is allowed only where it is published on purpose: `package.json`, the `LICENSE`
files, `.claude-plugin/` and the site footer. Public GitHub handles are never flagged.

**Set up once, for each GitHub account that commits here** (today `sananthanarayan` and
`sanjay-ananth`):

1. On github.com, **Settings → Emails**: turn on **Keep my email addresses private** and
   **Block command line pushes that expose my email**. GitHub then rejects a push that would
   publish your address, and uses your noreply address for commits made on the website.
2. In each clone or worktree, commit as that account's noreply address and turn the hooks on:

   ```bash
   git config user.name  <handle>
   git config user.email <id>+<handle>@users.noreply.github.com   # Settings → Emails shows it
   git config core.hooksPath .githooks
   ```

3. Anything else to protect (a second email, a work domain, a nickname) goes one per line in
   `.skilldrop-private` at the repository root. Git ignores that file, so it never leaves your
   machine; `SKILLDROP_PRIVATE_TERMS` (comma-separated) works too.

## Supported versions

Only the latest `skilldrop-cli` on npm is supported. Fixes ship forward; there are no backports.

## How this repo is hardened

- The npm package has **zero runtime dependencies** — nothing transitive to compromise — and runs no code at install. `validate.py` holds both: adding a dependency fails CI until a lockfile and npm Dependabot updates come with it, and an install-time script (`preinstall`, `install`, `postinstall`, `prepare`) fails it outright.
- Publishing uses **npm OIDC trusted publishing with provenance**. No long-lived token exists to steal.
- **GitHub Actions are pinned to commit SHAs**, so a repointed tag cannot inject code into a job that holds publish rights.
- Workflows default to `permissions: contents: read`; write scopes are granted per job.
- `main` requires a pull request; every change is owned by [CODEOWNERS](.github/CODEOWNERS).
- Every push and pull request runs **gitleaks** over the full history, **actionlint**, and **zizmor** over the workflows and `action.yml` ([security.yml](.github/workflows/security.yml)). The tools are pinned to exact versions, and their downloads are checksum-verified.
- Read-only jobs check out with `persist-credentials: false`, so a later step can't reuse the job token.

## OWASP

[skilldrop and the OWASP Top 10s](guides/reference/owasp-mapping.md) maps each control to the Agentic Skills Top 10 and the LLM Top 10 2025, and lists the gaps. `skilldrop scan` tags its findings with the same IDs.

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

The second category is a real bug class, not a theoretical one — [`agent-threat-model`](skills/agent-threat-model/SKILL.md) is the lens this project uses for it.

## What the installer guarantees

- **Install copies files. It never executes catalog content.** Not on install, not on update. If you find a path where it does, that is a vulnerability — report it.
- **Third-party catalogs are not trusted.** `--from` prints a review-before-use warning, because a stranger's `SKILL.md` is a stranger's instructions to your agent.
- **Hooks are opt-in.** They wire only under `--with-hooks`, and the CLI prints every file it wrote. See [RFC-0006](docs/rfcs/0006-per-ide-hooks.md).

## Not vulnerabilities

- A skill producing low-quality or wrong output. That's a bug — open an issue.
- Prompt injection *against an agent you pointed at untrusted content*, when skilldrop's role was only to supply the instructions you chose to install. Model that with `agent-threat-model`.
- Unpinned Python ranges in a skill's `requirements.txt`. Known, tracked, and installed on your machine under your control — a hardening item, not a live vulnerability.

## Supported versions

Only the latest `skilldrop-cli` on npm is supported. Fixes ship forward; there are no backports.

## How this repo is hardened

- The npm package has **zero runtime dependencies** — nothing transitive to compromise.
- Publishing uses **npm OIDC trusted publishing with provenance**. No long-lived token exists to steal.
- **GitHub Actions are pinned to commit SHAs**, so a repointed tag cannot inject code into a job that holds publish rights.
- Workflows default to `permissions: contents: read`; write scopes are granted per job.
- `main` requires a pull request; every change is owned by [CODEOWNERS](.github/CODEOWNERS).

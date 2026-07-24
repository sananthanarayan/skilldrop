---
rfc: 0004
title: Automated npm releases via GitHub Actions (OIDC trusted publishing)
status: implemented
date: 2026-07-24
author: sananthanarayan
---

# RFC-0004: Automated npm releases via GitHub Actions (OIDC trusted publishing)

## Problem / use case

Publishing is manual and 2FA-interactive: every release needs a maintainer at a browser. That caps release cadence, and `skilldrop outdated` is only as useful as the registry is fresh. Releases should happen automatically when the version bumps on `main`.

## Fit check

Structural change — adds `.github/workflows/release.yml` and makes the repo's "no CI" claim false, so AGENTS.md's golden rule 4 and commands section are updated in the same change. Both linters (`validate.py`, `skilldrop validate`) now also run in CI on every push and PR, which strengthens the existing quality story rather than changing it.

## Proposal

One workflow, two jobs:

- **lint** (every push and PR): `python3 validate.py` + `node bin/skilldrop.js validate`.
- **publish** (pushes to `main` only, after lint): version-gated — reads `package.json` version, compares against `npm view skilldrop-cli version`, exits quietly if already published, otherwise `npm publish --provenance`. Auth is npm **OIDC trusted publishing** (no token stored anywhere): GitHub's OIDC identity is exchanged for a publish grant, and `--provenance` attaches a verifiable build attestation to the package.

The version field in `package.json` is the single release trigger: bump it, merge to main, the release ships. No tags, no secrets.

One-time manual setup (account owner only): on npmjs.com → package `skilldrop-cli` → Settings → Trusted Publisher → GitHub Actions, repository `sananthanarayan/skilldrop`, workflow `release.yml`.

## Alternatives considered

- **Automation token in GitHub secrets:** rejected — npm is actively restricting tokens that bypass 2FA (deprecation notice shown at login), and a long-lived secret is strictly worse than OIDC.
- **Tag-triggered releases:** rejected — a second source of truth for the version invites drift between tag and `package.json`; the file already drives users' `outdated`.
- **Keep publishing manual:** rejected by the problem statement, but the manual PTY flow still works as a fallback and stays documented in memory.

## Decision

Implemented: `.github/workflows/release.yml` with lint + version-gated OIDC publish; AGENTS.md CI claims updated. Pending the one-time trusted-publisher configuration on npmjs.com, which only the account owner can do.

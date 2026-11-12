---
rfc: 0088
title: Older CLI versions refuse to install, and are deprecated on npm
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0088: Older CLI versions refuse to install, and are deprecated on npm

## Problem / use case

Every published `skilldrop-cli` stays installable. `npx skilldrop-cli@1.15.0 install --loop build`
still installs a loop that 1.16.0 retired. A global install from months ago keeps installing
skills whose bugs have since been fixed, and nothing tells its user. Once a version is out,
people shouldn't be able to keep using an older one to install.

## Fit check

npm can't stop anyone installing a published version. It allows unpublishing only within 72
hours, or under narrow conditions, and an unpublished version number can never be reused. So
this has two parts:
- the CLI refuses to install or update when a newer version is out;
- npm warns anyone installing an older version, including the versions from before the
  refusal existed.

No dependency is added. The CLI already writes only to disk; this adds one read-only request
on two commands.

## Proposal

**1. An older CLI refuses to install or update.**
- **The check.** Before `install` and `update`, the CLI fetches `<registry>/skilldrop-cli/latest`.
  The registry is the one npm uses (`npm_config_registry`, which `npx` sets), so an internal
  mirror's latest is the one that counts. When that version is newer than the CLI's own, it
  stops before writing anything, and prints the same command with `npx skilldrop-cli@latest`.
- **What it sends.** The request carries nothing about the user or their files.
- **Offline.** On any error, a non-200 reply, or no answer within 2.5 seconds, the command runs as
  before.
- **`SKILLDROP_ALLOW_OLD_CLI=1` skips the check,** for a pinned CI job or an air-gapped mirror.
- **A git checkout of skilldrop is never checked,** because it is the development copy, not an old
  install. Otherwise a pull request branched before a release would fail its own tests once the
  release went out. Setting `SKILLDROP_REGISTRY` turns the check on, which is how `cli_smoke.js`
  tests it against a local registry.
- **Every other command runs on any version,** because those commands read what is already installed.

**2. Every older version is deprecated on npm.** Once a version is live, the maintainer runs:

```bash
npm deprecate "skilldrop-cli@<X.Y.Z" "Superseded by skilldrop-cli X.Y.Z. Older versions install skills and loops that have since been fixed or retired: use npx skilldrop-cli@latest"
```

npm then warns anyone who installs an older version. The release workflow prints this exact
command, with the version filled in, beside its notice to approve the staged publish.

## Alternatives considered

- **Deprecate from CI.** Deprecating needs an npm write token in the repository's secrets. A token
  that can deprecate can also publish, so it would skip the 2FA approval every publish now waits
  for. One command at approval time keeps that approval in place.
- **Unpublish old versions.** It's only allowed briefly after publishing, breaks anyone pinned to
  that version, and burns the version number.
- **Warn instead of refusing.** A warning in an install's output is read once and ignored. A
  refusal names the one command that works.

## Decision

Implemented in 1.18.0, so 1.18.0 is the first version that refuses. The versions before it get
npm's deprecation warning only. `cli_smoke.js` checks the behaviour on every OS:
- the refusal names the latest version and installs nothing;
- the opt-out installs;
- `list` is unaffected;
- an unreachable registry runs as before.

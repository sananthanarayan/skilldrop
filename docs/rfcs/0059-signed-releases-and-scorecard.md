---
rfc: 0059
title: Signed releases, an OpenSSF Scorecard and a README that leads with the evidence
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0059: Signed releases, an OpenSSF Scorecard and a README that leads with the evidence

## Problem / use case

**Few people find the repo.** In two weeks it had 106 unique visitors, all arriving from one
internal share, and 2 stars, while npm counted 8,147 downloads in a month. Someone choosing
between agent-skill catalogues sees three things first, and each undersold this one:
- **The README** opened with a list of 19 packs. The one thing no other catalogue has, a
  published with-and-without measurement with retired skills, was a sentence further down.
- **The Releases page** titled each release "Merge pull request #77 from …", and its notes
  were the pull request's title.
- **Nothing outside the repo vouched for its supply chain.** The practices were already
  there: actions pinned to commit SHAs, CodeQL, zizmor, npm provenance, zero dependencies.

## Fit check

No skill changes. Everything here is CI, release and README work. The published package still
has zero dependencies.

## Proposal

- **README:**
  - It leads with one real with-and-without example. The example comes from a held-out
    `lean-canvas` eval, and the judge's reason is quoted verbatim.
  - Next come the run's headline numbers. They say plainly that the author-written checks
    flatter the skill, and that the blind preference is the fairer measure.
  - Then a three-line install. The packs list is folded below.
  - New badges: Scorecard, and the three-OS CLI job.
- **Releases** take their notes from this version's CHANGELOG entry and their title from the
  pull request.
- **The release job:**
  - It packs the tarball once and publishes that file, so the tarball attached to the
    Release is byte for byte the one on npm.
  - It signs a build provenance for the tarball with `actions/attest-build-provenance`. The
    provenance is attached as `.sigstore.json` and recorded as a GitHub attestation.
  - It attaches a CycloneDX SBOM.
  - The global `npm install -g npm@…` step is replaced by a version check. Node 24's own npm
    already supports trusted publishing.
- **The Scorecard workflow** runs weekly and on every merge. It publishes results for the
  badge and uploads SARIF to code scanning.
- **Scorecard gaps closed:**
  - CI's tools install from hash-locked files in `.github/tools/`:
    - pagefind from a `package-lock.json`, with `npm ci --ignore-scripts`;
    - zizmor with `pip --require-hashes`.

    Dependabot watches both.
  - `plugins.yml` moves its write permission from the workflow to its one job.
  - `SECURITY.md` states a disclosure window, and explains how to verify a release.
- **A one-time star line in the CLI.** It prints after the first successful install, at an
  interactive terminal only. It never prints in CI, in a pipe or with `--json`. One local
  marker file stops it repeating; `SKILLDROP_NO_STAR=1` turns it off; nothing is sent
  anywhere. `cli_smoke.js` holds that it never reaches a pipe.

**Not done, with reasons:**
- **Fuzzing:** Scorecard detects fuzzing in neither Python nor plain Node tests. It would
  need a fast-check dependency, and the package has none.
- **Contributors:** this needs commits from three companies.
- **Four-tier branch protection:** this needs two reviewers.
- **CII Best Practices:** this needs the owner to register at bestpractices.dev.

## Alternatives considered

- **A recorded GIF for the README.** A quoted, real pair of answers is checkable, and it
  stays true without re-recording.
- **SLSA `.intoto.jsonl` provenance through `slsa-github-generator`.** That would score 10
  instead of 8 on Signed-Releases, but needs a reusable workflow referenced by tag, which this
  repo's pinning rule forbids.
- **Ask for stars on every install.** People notice a nag more than the tool.

## Decision

Accepted and implemented in 0.16.40.

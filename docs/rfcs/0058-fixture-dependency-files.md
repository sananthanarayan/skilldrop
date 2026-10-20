---
rfc: 0058
title: Eval fixtures that hold no live dependency files
status: implemented
date: 2026-10-20
author: sanjay-ananth
---

# RFC-0058: Eval fixtures that hold no live dependency files

## Problem / use case

Eval fixtures are small fictional projects, and many need a `package.json`, `go.mod`,
`pyproject.toml` or CI workflow for the scenario to be real. GitHub's dependency graph reads
every such file on the default branch as this repo's own dependencies.

That had two effects:
- **33 open Dependabot alerts**, one rated critical. All were against code that nothing
  installs or runs.
- **Six security PRs:** #62, and #70–#74.
  - Merging one would break its eval. The old pins are the scenario: the stats files and
    assertions are written for those versions.
  - Closing them by hand leaves the alerts open, and a new fixture raises the next batch.

Dependabot's `exclude-paths` covers version updates only, not security updates, so
configuration can't stop this.

## Fit check

No skill changes. A file a run needs is still in the fixture, under a name GitHub doesn't
read, and the run sees the real name.

## Proposal

- **A fixture's dependency files are stored as `<name>.fixture`.** This covers the
  manifests and lockfiles of every ecosystem the dependency graph reads, plus workflow files
  under `.github/workflows/`. 48 files were renamed, across 8 skills.
- **`run_bench.py` strips `.fixture`** when it copies a fixture into a run's workspace.
  The cache key hashes the restored names, so cached results stay valid.
- **`validate.py` fails** on a dependency file under `evals/files/` or `examples/inputs/`
  that still has its real name. The message gives the name to use.

Once the manifests leave the default branch, GitHub closes the alerts raised against them.
No fixture can raise a new one.

## Alternatives considered

- **Bump the fixtures to patched versions.** That changes what the evals test and means
  re-measuring each skill. It also has to be repeated every time a new advisory lands.
- **Dismiss each alert, or add a repo auto-triage rule.** That needs an admin, works one
  alert or one path at a time, and still shows the repo depending on vulnerable versions.
- **Turn off Dependabot alerts.** That would also hide the alerts for the two real pip
  manifests and the Actions pins.

## Decision

Accepted and implemented in 0.16.39.

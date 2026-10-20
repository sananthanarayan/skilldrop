# dependency-upgrade-review reference

Long-form material for the steps in `SKILL.md`: what each ecosystem's diff shows, where the risky signals live, how to list the releases between two versions, how to trace a behaviour change to its callers, where runtime floors bite, how to verify a pin, and how to roll back.

## Reading a lockfile diff, by ecosystem

| Ecosystem | Manifest | Lockfile | Transitive changes visible? | Install-time code signal | Source signal | Licence in lockfile? |
|---|---|---|---|---|---|---|
| npm | `package.json` | `package-lock.json` (v2/v3: `packages["node_modules/<name>"]`) | Yes | `"hasInstallScript": true`; lifecycle hooks in `package.json` `scripts` | `"resolved"` URL host | Yes, `"license"` |
| Yarn | `package.json` | `yarn.lock` | Yes | Not recorded; check the package's own `package.json` | `resolved` URL host (v1), `resolution` (Berry) | No |
| pnpm | `package.json` | `pnpm-lock.yaml` (`packages:` keys `name@version`) | Yes | `requiresBuild: true` | `resolution.tarball` when not the registry | No |
| pip | `requirements*.txt`, `pyproject.toml` | pinned `requirements.txt`, `poetry.lock`, `uv.lock`, `Pipfile.lock` | Only in a lockfile or a fully pinned requirements file | An sdist with no wheel for the platform runs its build backend at install | `--index-url` / `--extra-index-url`, `[[package.source]]`, `"index"` | No |
| Go | `go.mod` | `go.sum` | Yes; `// indirect` marks modules the code does not import directly | None at install; `go generate` never runs on its own | `replace` directives; `GOPROXY` / `GOPRIVATE` settings | No |
| Cargo | `Cargo.toml` | `Cargo.lock` | Yes | `build.rs` in the crate; `-sys` crates link native libraries | `source = "registry+…"` or `git+…` | No |
| Maven | `pom.xml` | None by default | No; diff `mvn dependency:tree` output before and after | Plugins run at build time | `<repositories>` / `<pluginRepositories>` URLs | No |
| Gradle | `build.gradle(.kts)`, `gradle/libs.versions.toml` | `gradle.lockfile` only when locking is on | Only with locking; else diff `gradle dependencies` | Plugins run at build time | `repositories { }` blocks | No |
| GitHub Actions | `.github/workflows/*.yml`, `action.yml` | None | No; a composite action's own `uses:` lines are not in the diff | Every action runs code in the job | The `owner/repo` itself | No |

Notes that change the reading:

- **npm nested copies.** `node_modules/a/node_modules/b` is a second copy of `b` that only `a` sees. Two versions of one package in the lockfile is normal; a new nested copy of a security-sensitive package (a parser, a crypto library) gets its own row.
- **Removed packages are evidence.** A dependency dropped by the upgrade often means the package now does that job itself (escaping, parsing). Read what replaced it.
- **`optional: true` still installs.** Optional dependencies install wherever the platform matches; an optional package with an install script runs it on every developer machine and CI runner that matches.
- **Go major versions are new modules.** `example.com/lib` to `example.com/lib/v2` is an import path change in every file, not a version bump. Renovate and Dependabot do not rewrite imports.
- **Maven and unlocked Gradle hide transitive changes.** The diff shows one `<version>` line; the resolved tree can move a dozen artifacts. Ask for the tree diff before reasoning about transitive risk.

## Listing the releases between two versions

```bash
npm view <pkg> versions --json            # npm: every published version
npm view <pkg> time --json                # npm: publish date of each version
pip index versions <pkg>                  # pip 21.2+: versions on the index
go list -m -versions <module>             # Go: tagged versions
gh release list -R <owner>/<repo>         # any GitHub-hosted project, including actions
gh release view <tag> -R <owner>/<repo>   # one release's notes
```

The changelog file inside the published package (`CHANGELOG.md`, `HISTORY.rst`, `NEWS`) is often more complete than the release page. For an action, the release notes are the only changelog; a major tag such as `v3` is moved by the maintainer to each new v3.x release.

What to pull from each release, in this order:

1. **Breaking:** removed or renamed APIs, changed signatures, changed defaults, dropped runtime versions (Node, Python, Go, MSRV), changed output formats.
2. **Security:** a fixed advisory, the affected range, and the first fixed version. That version is the floor for any pin-back.
3. **Deprecations:** still works, removed later. A deprecated call the repo makes is a 🟧, not a 🟥.
4. **Licence:** a changed `license` field or a LICENSE file change. Moves between permissive licences (MIT, BSD, Apache-2.0, ISC) are a note. A move to a copyleft licence (GPL, AGPL, MPL at file level, LGPL) or a source-available licence (BUSL, SSPL, Elastic, "Commons Clause") needs a sign-off from whoever owns licence policy before merge.

## Tracing a behaviour change to its callers

A search hit is where the review starts. Read the calling function and write what it does under the new version.

| Change in the notes | What to look for in the caller | What breaks |
|---|---|---|
| Returns `None` / `-1` / `false` → raises | `if result is None`, `== -1`, `if not ok` branches; retry loops and fallbacks built on them | The branch never runs; the first failure escapes as an exception and the retry or fallback is dead code |
| Raises → returns a sentinel | `try` / `except` around the call | The error is swallowed; the code carries on with the sentinel |
| Exception class renamed or re-parented | `except OldError`, `catch (e instanceof OldError)` | The handler stops catching it |
| Tuple or dict → object | `a, b = f(...)`, `result["key"]` | Unpacking or key access fails at runtime |
| Changed default | Every call that does not pass the option | Each one gets the new behaviour silently |
| Module or function removed | Imports at the top of a file, and imports inside functions | A top-level import fails at startup and in tests; an import inside a function fails only when that function runs |

Name the fix in the repo's code, and any migration aid an intermediate release ships (an opt-in flag that turns on the new behaviour early). Moving to that release first lets the code change land and be tested before the major.

## Runtime floors

A release that drops a runtime version breaks wherever the old runtime still runs, and CI usually runs a newer one.

| Floor raised in | Compare with |
|---|---|
| Release notes ("requires Python 3.10"), `python_requires`, `python-versions` in `poetry.lock`, `requires-python` in `uv.lock` | Dockerfile `FROM`, `setup-python` version and matrix, `.python-version`, the Python the lockfile was compiled on |
| `engines.node` in `package-lock.json` or `package.json` | `.nvmrc`, `setup-node` / toolchain version, Dockerfile `FROM`, `engine-strict` in `.npmrc` |
| `go` directive in `go.mod`, `toolchain` line | `setup-go` version, Dockerfile builder image |
| `rust-version` (MSRV) in a crate | `rust-toolchain.toml`, CI toolchain |
| Wheels or prebuilt binaries only for some versions or platforms | Every image and runner that installs it; elsewhere it builds from source and needs a compiler or toolchain |
| An action's runtime (`node20` → `node24`) | Self-hosted runner versions; GitHub-hosted runners update themselves |

A lockfile generated on a newer runtime than production can resolve versions production cannot install. `pip install --require-hashes` and `npm ci` fail at build time, not at review time.

## Verifying a pin

```bash
git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag> 'refs/tags/<tag>^{}'
```

- Annotated tag: two lines. The plain `refs/tags/<tag>` line is the tag object; the `refs/tags/<tag>^{}` line is the commit. The pinned SHA must equal the `^{}` line.
- Lightweight tag: one line, and it is the commit.
- No output: the tag does not exist in that repository. The pin is wrong or the comment is.
- `gh api repos/<owner>/<repo>/commits/<sha>` confirms the commit exists, but GitHub serves commits from any fork in the network under the upstream path, so existence proves nothing. Only the tag match does.
- A SHA with no `# vX.Y.Z` comment: list the tags (`git ls-remote --tags https://github.com/<owner>/<repo>`) and find the SHA. No tag points to it means it is not a release.
- Tag-only pin (`uses: owner/repo@v3`): the maintainer, or anyone who takes over the account, can point `v3` at new code after review. Pin to the commit the `^{}` line returns and keep the tag as a comment.
- Branch pin (`@main`): every run gets whatever was pushed last. A PR that introduces one is DO NOT MERGE.
- Two SHAs for one tag: when the same `owner/repo` and `# vX.Y.Z` comment appear with different SHAs across workflow files, at most one is the tag's commit. Run the command once and compare both; until then, the PR is DO NOT MERGE. Read the PR's commit list: a bot writes every pin the same way, so a pin that differs from the bot's usually came from a hand-made commit.

Stakes come from the job, not the action: look at `permissions:` (`contents: write`, `id-token: write`, `packages: write`), the `secrets.*` it receives, and the `environment:` it runs in.

## Did CI run it?

| Where the dependency is used | Runs on the PR? |
|---|---|
| A workflow with `on: pull_request` that imports or calls it | Yes, if a test reaches the code path |
| A workflow with only `on: push: tags`, `release`, `schedule`, `workflow_dispatch`, `workflow_run` | No |
| A job guarded by `if: github.event_name == 'push'` or a branch condition | No |
| A build or publish step (bundler, packager, uploader) not in the PR workflow | No |
| A source file no test imports | No |
| A test that imports the file but never hits the changed behaviour (a default, an edge case the notes name) | Not the part that changed |
| A test that mocks the dependency with the old contract (a fake that returns a value where the new version raises) | No; it tests the old behaviour |
| An import inside a function no test calls | No; it never fails at import or collection |
| An install script, when the PR job installs with `--ignore-scripts` and the release job does not | No; it first runs in the release job, with that job's secrets and permissions |
| A runtime older than the one CI uses (production image, self-hosted runner) | No |

Ways to exercise an unrun path before merge: a `workflow_dispatch` dry run on the PR branch, a release to a test index (TestPyPI, a scratch npm scope), or a test that covers the changed behaviour, added in the same PR.

## Rollback, by ecosystem

| Ecosystem | Pin back | Then |
|---|---|---|
| npm | `npm install <pkg>@<old> --save-exact` (or restore the old range) | Commit `package.json` and `package-lock.json`; `npm ci` in CI |
| Yarn | `yarn add <pkg>@<old>` | Commit `yarn.lock` |
| pnpm | `pnpm add <pkg>@<old>` | Commit `pnpm-lock.yaml` |
| pip (requirements) | Restore `<pkg>==<old>` | Regenerate the pinned file with the tool that made it (`pip-compile`, `uv pip compile`) |
| Poetry | `poetry add <pkg>@<old>` | Commit `pyproject.toml` and `poetry.lock` |
| uv | `uv add "<pkg>==<old>"` | Commit `pyproject.toml` and `uv.lock` |
| Go | `go get <module>@<old> && go mod tidy` | Commit `go.mod` and `go.sum` |
| Cargo | `cargo update -p <crate> --precise <old>` | Commit `Cargo.lock` (and `Cargo.toml` if the requirement moved) |
| Maven / Gradle | Restore the old `<version>` or version catalog entry | Re-resolve and commit any lockfile |
| GitHub Actions | Restore the old `uses:` line, SHA and comment | Nothing else |

`git revert <merge-commit>` does all of the above in one step when nothing else touched those files since.

What a revert does not undo:

- **Lockfile format migrations.** `lockfileVersion` 2 → 3, Poetry `lock-version`, a new `uv.lock` schema. An older tool may refuse the reverted lockfile if someone regenerated it with the newer tool in between.
- **Data the new version wrote.** Database migrations an ORM or library ran, cache files, serialised sessions, search indexes, file formats. The old version may not read them.
- **Artifacts built or published with it.** A package version on npm, PyPI or crates.io cannot be republished with different contents; a container image already deployed stays deployed.
- **Security fixes.** Rolling back past a fixed advisory reopens it; pin back to the first fixed version, not to the old one, when the old one is in the affected range.
- **Downstream consumers.** A library that widened its own dependency range in the same PR has already told its users the new version works.

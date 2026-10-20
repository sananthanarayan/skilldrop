# bramblewick/setup-toolchain releases

## v3.3.0 (2026-10-06)

### Breaking-ish
- The action now runs on the `node24` runtime (was `node20`). GitHub-hosted runners already support it. **Self-hosted runners must be on actions/runner v2.328.0 or newer**, otherwise the job fails with `Parameter 'using: node24' is not supported`.

### Changed
- `cache` now defaults to `true` (was `false`). The npm cache is keyed on the lockfile hash and restored automatically. Set `cache: false` to keep the old behaviour.

### Added
- `node-version-file` accepts `package.json#engines.node`.

## v3.2.1 (2026-09-12)

### Security
- Fixed a cache-key collision (GHSA-xxxx-fict-0001) in which a workflow run triggered by a pull request from a fork could write a cache entry that a later run on the default branch restored. Only affected users who set `cache: true`.

## v3.2.0 (2026-07-30)

### Added
- Support for `.tool-versions`.

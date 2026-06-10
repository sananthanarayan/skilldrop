# Release-notes templates

Two artifacts, two readers. Customer notes sell nothing and explain everything; the internal changelog trades polish for traceability.

## Artifact 1 — customer-facing release notes

```markdown
# {Product} {version} — {YYYY-MM-DD}

> Covers {ref}..{ref} · {N} changes

## ⚠ Breaking changes

- **{What broke, in reader terms.}**
  Action required: {the exact step — config to change, endpoint to migrate, deadline}.
  (flagged by: {signal — `!:` marker / removed API / migration file})

## New

- {What the reader can now do. One sentence, benefit first.}

## Improved

- {What got better, measurably where possible: "export is ~3× faster on reports over 10k rows".}

## Fixed

- {The symptom the reader no longer suffers: "Fixed a crash when …", "Dates no longer shift by one day when …".}

## Security

- {Reader-relevant statement; severity and affected versions; no exploit detail.}
```

Rules: no class/function/service names, no ticket IDs, no author names, no "various improvements". A section with nothing in it is deleted, not left empty — except Breaking changes, which when empty becomes the single line "No breaking changes."

## Artifact 2 — internal changelog (Keep a Changelog)

```markdown
## [{version}] - {YYYY-MM-DD}

Range: `{ref}..{ref}` · {N} commits · {N} PRs

### Added
- {change} ({#PR}, `{hash}`)

### Changed
- **BREAKING:** {change + migration step} ({#PR}, `{hash}`)
- {change} ({#PR}, `{hash}`)

### Fixed
- {change} ({#PR}, `{hash}`)

### Deprecated / Removed / Security
- {change} ({#PR}, `{hash}`)

### Internal
- {refactor / CI / deps / tests — one line each} (`{hash}`)
```

## Needs review (always emitted, both modes)

```markdown
## Needs review — {N} commits not classified

| Hash | Subject | Why unclear |
|---|---|---|
| `{hash}` | {verbatim subject} | {vague / contradicts diff / can't tell if user-visible} |
```

## Classification cheat-sheet

| Signal | Bucket |
|---|---|
| New endpoint, flag default-on, new UI surface | Added |
| Behavior or default changed for existing users | Changed (BREAKING if old behavior unobtainable) |
| `fix:`, bug ticket, regression revert | Fixed |
| `chore:`, `refactor:`, `test:`, `ci:`, deps, lockfiles | Internal |
| CVE, auth/authz, input validation, secrets | Security |
| `feat!:`, `BREAKING CHANGE:`, removed public API, schema migration, major version bump of a public SDK | Breaking — hoist to top |
| "wip", "fix stuff", "address comments", empty body + vague subject | Needs review |

---
rfc: 0039
title: Commit-pinned catalogues and a permission manifest for skills
status: implemented
date: 2026-10-01
author: sananthanarayan
---

# RFC-0039: Commit-pinned catalogues and a permission manifest for skills

## Problem / use case

The OWASP mapping ([guides/reference/owasp-mapping.md](../../guides/reference/owasp-mapping.md))
named two of its biggest gaps, and this RFC closes both.

**No commit pinning (AST02, AST07).** `--from <url>#<ref>` accepted only a branch or tag, both
of which can be moved to different code after a reviewer read them. The ledger recorded no
commit, and `update` triggered on the version string alone, so a catalogue could change a
skill's files under the same version and nobody would see it.

**No permission manifest (AST03, AST10).** Nothing said what a skill's scripts may do, so
`skilldrop scan` could only report patterns, never compare them with an intent. There was no
security property to keep when a skill moved between tools.

## Fit check

Golden rules touched:
- **Zero dependencies:** the pinning uses `git`, which the CLI already required for remote
  catalogues.
- **Copy, never execute:** unchanged. The manifest describes scripts; nothing runs them.

Third-party catalogues without a `permissions` block still install. The scan names the gap
and doesn't refuse, because refusing would break every existing catalogue for no safety gain.

## Proposal

**Pins.**
- `--from <url>#<sha>` (7 to 40 hex characters) fetches that commit exactly. The CLI fetches
  the commit itself, since `git clone --branch` takes only branches and tags, and checks that
  `HEAD` matches.
- Every install records `commit` in the ledger.
- An unpinned third-party install prints the `#<commit>` URL that reproduces it.
- `update` leaves pinned skills alone and says so.
- `outdated` and `update` compare files as well as versions. A same-version change is named,
  and taken only with `update --changed`.

**Permissions.** `manifest.json` gains an optional, closed `permissions` block:

```json
"permissions": { "network": ["api.figma.com"], "commands": ["pdftotext"], "files": "named-paths", "notes": "…" }
```

It's required, by `validate.py`, for any skill that ships `scripts/`. `skilldrop scan` compares
the scripts' findings with the declaration:
- a network call with no hosts declared → 🟥 `undeclared-network`
- a shell or exec call with no commands declared → 🟥 `undeclared-commands`
- a write outside its own paths without `files: "anywhere"` → 🟥 `undeclared-files`
- scripts with no block at all → 🟨 `no-permissions`

`skilldrop validate` fails a catalogue on any `undeclared-*` finding. `info` shows the
declaration, and third-party installs print each script skill's declaration.

All 24 bundled script skills declare their permissions, taken from reading each script rather
than from the scan: the scan's patterns miss some real behaviour, such as `figma-diagrams`
calling `api.figma.com` through `requests`.

## Alternatives considered

- **Require a signature on third-party catalogues.** Stronger than a pin, but it needs key
  distribution that a zero-dependency CLI can't do well. A pin gets most of the protection,
  and signing stays on the future list.
- **Block installs that lack permissions.** Rejected: it breaks existing catalogues without
  making anyone safer. The scan names the gap instead.
- **Infer permissions from the code.** Rejected as the source of truth: pattern matching
  misses things. Inference is the check against the declaration, not the declaration.

## Decision

Accepted by the maintainer on 2026-10-01 ("do … commit-pinned third-party catalogues,
permission manifest for skills"). Ships in 0.16.0.

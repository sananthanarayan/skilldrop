---
rfc: 0034
title: Physical pack layout
status: implemented
date: 2026-10-01
author: sanjay-ananth
---

# RFC-0034: Physical pack layout

## Problem / use case

RFC-0033 gave every skill and loop exactly one pack, but membership still lived in a list
(`packs.json`) separate from the folders. Two things kept in sync by hand drift: a skill could
be renamed on disk and not in the list, and a newcomer browsing the repo saw 63 folders in one
flat `skills/` with no sign of who each is for. The maintainer's stated direction (RFC-0032,
**Forward compatibility**) is agent-ready-repo's model, where the folder *is* the pack.

## Fit check

Structural change. It reverses golden rule 2 ("do not move `skills/`"), RFC-0001's rejection
of physical packs, and RFC-0014's "Path A never". It doesn't break the property those rules
protected:

- **One folder is one working skill.** A skill is still a self-contained folder, copied
  verbatim. Only its path changes: `packs/<pack>/skills/<name>/`.
- **Zero dependencies.** JSON, not TOML (`pack.json`, not `pack.toml`), so `validate.py`
  still runs on Python 3.9 with no parser.
- **The installer contract.** Ledger entries record skill names, not paths, so `outdated`
  and `update` keep working across the move.

## Proposal

```
packs/<pack>/
├── pack.json            # description, display_name, keywords, links, maintainers,
│                        # first-value, requires — RFC-0032/0033 keys, unchanged
├── skills/<name>/       # SKILL.md + manifest.json + supporting files, as before
└── loops/<name>/        # LOOP.md + loop.json, as before
catalogue.json           # pack display order + the outcomes axis (RFC-0026)
catalog.py               # the one loader every Python script reads through
```

- **The folder is the membership.** `pack.json` has no skill or loop list. `validate.py`
  fails a name with a folder in two packs, a pack folder with no `pack.json`, a pack missing
  from or extra in `catalogue.json`, and a leftover flat `skills/` or `loops/`.
- **The layout is skilldrop-native, not agent-ready-repo's exactly.** There is no hidden
  `.apm/` folder and no TOML. The maintainer chose this over the exact layout because hand
  copying stays obvious and the per-skill `manifest.json` (version, tier, `related`) stays
  first-class. The CLI still reads agent-ready-repo catalogs (RFC-0014).
- **The CLI reads three shapes:** `packs/<pack>/pack.json` (this one), flat `skills/` (older
  skilldrop and most third-party catalogs), and agentbundle `pack.toml`. Third-party flat
  catalogs keep working unchanged.
- **Claude plugins.** The whole-catalogue plugin's `plugin.json` lists each
  `./packs/<pack>/skills/` folder; Claude Code's `skills` manifest field adds those
  directories to discovery. The per-pack plugins stay on the generated `plugins` branch,
  because a role pack's plugin must also carry `core`, and a plugin cannot reference paths
  outside its own folder.
- **Migration.** One `git mv` per skill and loop, so history follows each file. Links
  across README, guides, LOOP.md files and agents were rewritten. RFC and CHANGELOG prose
  keeps the paths that were true when written; only broken links in them were repointed.

## What breaks

- **Old CLIs pointed at this repo with `--from`.** A pre-0.13.3 CLI does not know the new
  shape. Upgrade the CLI; the bundled catalog (`npx skilldrop-cli`) is unaffected.
- **Hand-copy instructions and deep links** to `skills/<name>/`. GitHub links into the old
  paths 404 after merge; the README, site, `llms.txt` and plugins all point at the new ones.

## Alternatives considered

- **agent-ready-repo's exact layout** (`pack.toml`, `.apm/skills/`). Rejected by the
  maintainer: it needs TOML parsing, a hidden folder is unfriendly to hand copying, and the
  CLI's agentbundle reader drops `manifest.json` detail.
- **Keep flat `skills/` with membership in `packs.json`** (RFC-0033's state). Rejected: two
  sources of truth for one fact, and it leaves the repo browsable only by name.
- **Symlink packs to a flat tree.** Rejected: symlinks break on Windows checkouts and inside
  npm tarballs.

## Decision

Accepted 2026-10-01, with the skilldrop-native layout chosen over agent-ready-repo's exact
one. It supersedes golden rule 2's "do not move `skills/`", RFC-0001's rejection of physical
packs, and RFC-0014's "Path A never".

# skilldrop CLI — design sketch

> A proposal for distributing skilldrop skills via an npm-published CLI that installs into any supported IDE (Claude Code, Cursor, Kiro, Continue, Cline, Aider, Codex) and updates in place when new versions ship. This is a design sketch for review, not a build plan — the goal is to get reactions on shape and scope before committing to the work.

## Why npm (and why not the others)

| Option | Verdict | Reason |
|---|---|---|
| **npm** | ✅ Recommended | Universally installed on dev machines; `npx` gives zero-install UX; skills are text + small scripts, which npm packages perfectly |
| Maven | ❌ | JVM-ecosystem; devs in Cursor/Kiro/Codex won't have it. Wrong audience. |
| PyPI | ⚠️ Possible alternative | Reasonable — Python is also broadly installed, and several skills already have `pip` deps. But `npx` UX beats `pipx run` for one-shot install. |
| Artifactory | ❌ (as primary) | Hosting, not a distribution format. Could *mirror* the npm package internally for orgs that need it, but the public-facing channel should be npm. |
| Claude Code plugin marketplace | ✅ (in parallel) | Native path for Claude Code users. Already wired via `.claude-plugin/plugin.json`. The npm CLI is the multi-IDE complement, not a replacement. |

**Decision:** npm as the primary CLI distribution. Keep the Claude Code plugin marketplace entry as the native path for that one IDE.

## CLI command surface

Package name: `skilldrop` (or `@skilldrop/cli` if scoped). Invoked via `npx skilldrop <cmd>` (no global install required) or `npm i -g skilldrop` for users who want `skilldrop <cmd>` directly.

### Core commands

```bash
# Discover
skilldrop list                          # all skills in the registry
skilldrop list --installed              # skills installed on this machine
skilldrop search <query>                # keyword/tag search
skilldrop info <skill>                  # description, version, deps, install paths

# Install
skilldrop install <skill>               # install into auto-detected IDE
skilldrop install <skill> --ide=cursor  # explicit target
skilldrop install <skill> --ide=all     # install into every detected IDE
skilldrop install <skill>@<version>     # pin to a specific version
skilldrop install --all                 # install the whole catalog

# Update
skilldrop update                        # update all installed skills to latest
skilldrop update <skill>                # update one skill
skilldrop outdated                      # show installed vs latest, no changes
skilldrop pin <skill>@<version>         # opt out of auto-update for one skill

# Remove
skilldrop uninstall <skill>             # remove from all IDEs it was installed in
skilldrop uninstall <skill> --ide=kiro  # remove from one IDE only

# Diagnostics
skilldrop doctor                        # detect installed IDEs, report install paths, flag drift
skilldrop where <skill>                 # print the install path(s) for a skill
```

### IDE detection

`skilldrop doctor` and the auto-detect path used by `install` look for:

| IDE | Detection signal |
|---|---|
| Claude Code | `~/.claude/` exists, or `.claude/` in cwd |
| Cursor | `~/Library/Application Support/Cursor/` (macOS), `%APPDATA%/Cursor/` (Windows); or `.cursor/` in cwd |
| Kiro | Kiro config dir (TBD — confirm with Kiro docs) |
| Continue | `~/.continue/` |
| Cline | VS Code extensions dir + Cline workspace markers |
| Aider | `.aider*` files in cwd or `~/.aider*` |
| Codex | Codex CLI config dir |

If multiple IDEs are detected, `install` without `--ide` prompts (TTY) or errors (non-TTY) asking the user to pick. `--ide=all` skips the prompt.

### Scope: user vs project

Mirror npm's `--global` vs project-local distinction:

```bash
skilldrop install adr-generator                  # user-scope (default; installs to ~/.claude/skills/, etc.)
skilldrop install adr-generator --project        # project-scope (installs to .claude/skills/ in cwd)
```

User-scope is the default because the README already steers users toward user-scope installs for development.

## Per-IDE install logic

The CLI's main value is translating a single source skill into the right format/location per IDE. The mapping is the load-bearing piece.

| IDE | Install path | Format transformation |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` or `.claude/skills/<name>/` | Copy folder as-is. SKILL.md is already the native format. |
| Cursor | `.cursor/rules/<name>.mdc` | Wrap `SKILL.md` content in MDC frontmatter (`description`, `globs`, `alwaysApply`). Bundle supporting files into the rule's referenced paths. |
| Kiro | Kiro agent definition | Paste `SKILL.md` content into Kiro's agent definition format (TBD — confirm Kiro's file layout) |
| Continue | `~/.continue/rules/` or `config.json` `customCommands` | Translate SKILL.md to a Continue rule. |
| Cline | Workspace rules or `.clinerules/` | Copy SKILL.md into the rules folder. |
| Aider | `.aider.conf.yml` `read` list, or `--read <path>` | Copy folder under repo, register in conf. |
| Codex | Codex equivalent (TBD) | TBD |

**Critical:** the source of truth stays the same — `SKILL.md` + supporting files + `manifest.json`. The CLI does the format adaptation at install time. This is what gives users a single mental model across IDEs.

### Dependency install

After the file copy, the CLI runs the dep install step from `manifest.json`:

- `deps.pip` → `python3 -m pip install -r requirements.txt` in the installed folder (or warn if no python found)
- `deps.npm` → `npm install` in the installed folder
- `env.required` → print a clear "set these env vars before using" message; exit non-zero if `--strict` is passed

`skilldrop install <skill> --no-deps` skips this step for users who manage deps themselves.

## Registry & distribution model

### v1: single monolithic package

The simplest shape: `skilldrop` npm package contains the CLI **and** all skills, baked in.

- **Pros:** one package, one version, atomic updates, trivial publishing (`npm publish` from this repo's CI).
- **Cons:** every skill update bumps the whole package; users always get all skills (~MB of markdown — still small).

This is the right v1. Skills are small; coupling them into one release artifact is fine until the catalog grows past ~50.

### v2: split CLI + per-skill packages

If the catalog grows or third parties want to publish their own skills:

- `skilldrop` (CLI only)
- `@skilldrop/<skill-name>` for each first-party skill
- Third parties publish `<their-scope>/<skill>` following the same `manifest.json` contract
- `skilldrop install <foo>` resolves: first-party catalog → npm scope lookup → install

Defer this until there's actual demand. Pre-building plugin architecture is the classic skilldrop trap (see `AGENTS.md`).

### Registry metadata

A `registry.json` (generated from each skill's `manifest.json` at build time) lives at the package root:

```json
{
  "generated_at": "2026-05-22T00:00:00Z",
  "schema_version": 1,
  "skills": [
    {
      "name": "adr-generator",
      "version": "0.1.0",
      "description": "...",
      "tags": ["adr", "architecture"],
      "deps": { "pip": [], "npm": [] },
      "env": { "required": [], "optional": [] },
      "ide_support": ["claude-code", "cursor", "kiro", "continue", "cline", "aider"],
      "path": "skills/adr-generator"
    }
  ]
}
```

`skilldrop list` reads this; no network call needed once the package is installed.

## `manifest.json` extensions

The current manifest is close. Additions needed:

```json
{
  "name": "adr-generator",
  "version": "0.1.0",
  "description": "...",
  "entrypoint": "SKILL.md",
  "deps": { "npm": [], "pip": [] },
  "env": { "required": [], "optional": [] },
  "install": { "pip": "python3 -m pip install -r requirements.txt" },
  "tags": ["adr", "architecture"],

  // --- NEW FIELDS ---

  "ide_support": {
    "claude-code": { "supported": true },
    "cursor": { "supported": true, "format": "mdc" },
    "kiro": { "supported": true, "format": "agent-paste" },
    "continue": { "supported": true, "format": "rule" },
    "cline": { "supported": true, "format": "rule" },
    "aider": { "supported": true, "format": "read-file" },
    "codex": { "supported": false, "reason": "not yet mapped" }
  },

  "files": {
    "required": ["SKILL.md"],
    "include": ["scripts/**", "reference/**", "requirements.txt"],
    "exclude": ["**/__pycache__/**", "**/.DS_Store"]
  },

  "post_install": {
    "message": "Set FIGMA_TOKEN before invoking this skill.",
    "verify": "python3 -c 'import requests'"
  },

  "compat": {
    "min_skilldrop_cli": "0.1.0",
    "platforms": ["darwin", "linux", "win32"]
  },

  "deprecated": false,
  "replaced_by": null
}
```

**Field-by-field rationale:**

- `ide_support` — per-IDE format hints. Lets the CLI know how to transform the skill at install time and lets `skilldrop info` show "works in: X, Y, Z." Without this the CLI has to guess (defaulting to "supported everywhere" is wrong — some skills genuinely don't make sense in Aider).
- `files.include` / `files.exclude` — explicit allowlist of what to copy. Avoids shipping `__pycache__`, editor scratch files, etc. The current "copy the folder" approach works but is sloppy.
- `post_install` — message printed after install; optional verify command. Saves users from "I installed it but it doesn't work because I missed an env var."
- `compat.min_skilldrop_cli` — guards against schema-version drift if the manifest format evolves. Mirrors how npm packages declare `engines.node`.
- `deprecated` / `replaced_by` — lets the registry retire skills cleanly. `skilldrop update` can surface "this skill was renamed; do you want to install <new>?"

**What does NOT need to change:**

- `name`, `version`, `description`, `entrypoint`, `tags`, `deps`, `env`, `install` — already present and correctly shaped.
- No need for a separate per-IDE manifest. One source of truth, transformed at install time.

## Update flow

```bash
skilldrop update
```

1. Read the installed-skills index (a JSON file in `~/.skilldrop/state.json` recording what's installed where and at what version).
2. For each installed skill, compare local version vs registry version.
3. For each out-of-date skill:
   - If pinned (`skilldrop pin`), skip with a notice.
   - If not pinned, re-run the install logic into the same IDE(s) it was previously installed in.
   - Detect local edits (hash mismatch on `SKILL.md`); prompt before overwriting (or warn and skip if `--no-prompt`).
4. Print a summary: updated / skipped / failed.

**State file** (`~/.skilldrop/state.json`):

```json
{
  "schema_version": 1,
  "installations": [
    {
      "skill": "adr-generator",
      "version": "0.1.0",
      "ide": "claude-code",
      "scope": "user",
      "path": "/Users/.../.claude/skills/adr-generator",
      "installed_at": "2026-05-22T10:00:00Z",
      "pinned": false,
      "source_hash": "sha256:abc..."
    }
  ]
}
```

The state file is what makes `update`, `uninstall`, and `doctor` work cleanly. Without it the CLI has to scan every possible install location on every invocation.

## Build effort — honest estimate

| Phase | Scope | Effort (single engineer, focused) |
|---|---|---|
| **Phase 1: MVP** | npm package; `list` / `install` / `uninstall` / `update`; Claude Code + Cursor only; monolithic registry | **~1 week** |
| **Phase 2: Multi-IDE** | Kiro, Continue, Cline, Aider adapters; `doctor`; state file; pin/unpin | **~1 week** |
| **Phase 3: Polish** | `info`, `search`, `where`, format-verification tests, CI publish workflow, docs | **~3–5 days** |
| **Phase 4 (optional)** | Codex support, per-skill packages, third-party skill registry | **Defer** |

Total realistic MVP-to-shippable: **~2.5 weeks of focused work**. Most of the surface area is the per-IDE adapter logic and getting the format transformations right — the CLI scaffolding itself is straightforward.

## Tradeoffs & open questions

- **CLI vs shell script.** The lighter alternative is `install.sh` / `install.ps1` in this repo doing the same thing. Lower maintenance, worse UX, no `update` story. If you only care about getting skills installed once and never updating, the script is enough. If you want "package manager for AI skills" positioning with versioning + updates, the CLI is the right investment.
- **Who owns per-IDE format drift?** Cursor's MDC format, Kiro's agent format, Continue's rule format — these evolve independently of skilldrop. The CLI's adapter layer becomes the maintenance hot-spot. Plan for monthly check-ins on each format.
- **Telemetry on installs?** Tempting to track which skills get installed where. Strongly recommend *not* doing this in v1 — adds privacy surface and the data is low-value early. If it becomes useful later, opt-in.
- **Org-internal skill catalogs.** Some teams will want a private catalog. Easy path: support a `--registry <url>` flag that points at an alternate `registry.json`. Don't build auth / private npm tokens in v1 — most orgs can host a static JSON file behind their VPN.
- **Versioning across IDEs.** If a user has `adr-generator@0.1.0` in Claude Code and `adr-generator@0.2.0` in Cursor (because they installed at different times), do we surface the drift? Yes — `skilldrop doctor` should flag it. `update` resolves by default.
- **What's the "official" registry URL?** v1 ships the registry inside the npm package itself, so there's no URL. v2 would need one (GitHub Pages on this repo? A `skilldrop.dev` site?). Decide at v2 time, not now.
- **Schema validation in CI.** Worth adding a CI step in this repo that validates every skill's `manifest.json` against the extended schema. Catches drift before publish.

## What to decide before building

1. **Go / no-go on the npm CLI vs the shell-script alternative.** Most consequential choice. CLI is the better product, the script is faster to ship.
2. **Scope of v1 IDE support.** Claude Code + Cursor only is realistic for an MVP. Adding more is incremental.
3. **Monolithic vs split packages.** Recommend monolithic for v1; revisit when catalog grows.
4. **Who maintains it.** A CLI is an ongoing commitment — per-IDE format drift, security advisories, npm publish hygiene. Confirm an owner before starting.

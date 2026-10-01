---
title: Publish your own catalogue
summary: Shape a repo so `skilldrop --from <you>` installs from it, and how the CLI reads agentbundle-shaped catalogues too.
kind: how-to
---

# Publish your own catalogue

#### Third-party catalogs — publish your own skills through the same CLI

A git repo or directory is a **catalog** if it has either shape the CLI reads ([RFC-0003](../../docs/rfcs/0003-third-party-catalogs.md), [RFC-0034](../../docs/rfcs/0034-physical-pack-layout.md)):

- **Pack folders, like this repo:** `packs/<pack>/pack.json`, with skills at `packs/<pack>/skills/<name>/` (`SKILL.md` + `manifest.json`) and optional loops at `packs/<pack>/loops/<name>/`. An optional root `catalogue.json` sets pack order.
- **Flat:** `skills/<name>/` folders, optionally with a root `packs.json` that lists each pack's skills. This is the simplest shape and still fully supported.


```bash
npx skilldrop-cli list --from https://github.com/you/your-skills
npx skilldrop-cli install my-skill --from https://github.com/you/your-skills#3f9c2ab   # #<commit> pins exactly
npx skilldrop-cli install my-skill --from https://github.com/you/your-skills#v1.2      # a tag or branch works, but can move
npx skilldrop-cli install --pack starter --from ../local-catalog
npx skilldrop-cli update      # updates bundled and third-party skills side by side — the ledger remembers each skill's source
```

The CLI also reads **agentbundle-shaped catalogs** ([agent-ready-repo](https://github.com/eugenelim/agent-ready-repo)) — `packs/<pack>/.apm/skills/<name>/SKILL.md` with a `pack.toml` per pack — so you can install *its* packs through the same command ([RFC-0014](../../docs/rfcs/0014-agentbundle-interop.md)). This is one-directional by design: skilldrop reads his shape, and no longer publishes a generated catalogue back into it ([RFC-0027](../../docs/rfcs/0027-retire-agentbundle-export.md)). Both shapes share the agentskills.io `SKILL.md`, so the reader just maps his packs onto the accessors above:

```bash
npx skilldrop-cli packs --from https://github.com/eugenelim/agent-ready-repo
npx skilldrop-cli install --pack contracts --from https://github.com/eugenelim/agent-ready-repo --dest .agents/skills
```

**Pin to a commit.** A tag or branch can be moved to different code after you reviewed it; a
commit SHA can't. Every install records the commit it got in the ledger, and an unpinned
third-party install prints the exact `--from <url>#<commit>` that reproduces it. A pinned skill
stays put on `update` until you reinstall with a new commit. If a catalogue changes a skill's
files without bumping its version, `outdated` names it and `update` leaves it alone unless you
add `--changed` ([RFC-0039](../../docs/rfcs/0039-commit-pins-and-skill-permissions.md)).

Safety model: installs **copy files only — nothing from a catalog is ever executed**; every skill passes a structural check before copying (broken folders are refused with reasons); and third-party installs print a review-before-use warning, because skills are instructions your AI agent will follow — read a stranger's `SKILL.md` before letting your agent obey it.

Third-party installs also print what each skill's scripts declare they do (hosts contacted,
programs run, where files are written) from its `permissions` block, and `scan` flags any
script that does something its skill doesn't declare.

**Authoring a catalog:** mirror the layout above, give every skill that ships scripts a `permissions` block (see [AGENTS.md](../../AGENTS.md)), then check it with `npx skilldrop-cli validate --from <your-repo-or-path>` before publishing. `related`, packs (either shape), `requires`, and `requirements.txt` all work in third-party catalogs exactly as they do here.

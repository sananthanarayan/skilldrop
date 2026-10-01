---
title: Roll out skilldrop across your org
summary: Bootstrap the hosted marketplace for every machine in one command — covers the public catalogue and private-fork setups for enterprise orgs.
kind: how-to
---

# Roll out skilldrop across your org

This guide shows how to give every developer on your team access to the skilldrop catalogue without asking them to configure anything manually. Two pieces work together: a hosted marketplace at a stable URL, and a bootstrap command that points Claude Code at it in one step.

## Prerequisites

- Node.js 16.7+ (for `npx`)
- Claude Code installed

## For teams using the public catalogue

The public catalogue already has both pieces set up. Team members run one command:

```bash
npx skilldrop-cli bootstrap
```

This writes `extraKnownMarketplaces.skilldrop` into `~/.claude/settings.json` pointing at the GitHub-hosted marketplace. Idempotent — safe to include in a provisioning script or onboarding runbook.

Then in any Claude Code session, install a role pack:

```
/plugin install dev-team@skilldrop
/plugin install solution-architect@skilldrop
/plugin install ai-engineering@skilldrop
```

Or the full catalogue:

```
/plugin install skilldrop@skilldrop
```

## For orgs hosting a private catalogue

### 1. Enable GitHub Pages on your fork

In your repo's Settings → Pages → Source: set to **GitHub Actions**. The `pages.yml` workflow deploys `marketplace.json` to Pages on every push to `main`, so your marketplace appears at:

```
https://<org>.github.io/<repo>/marketplace.json
```

### 2. Update the bootstrap constants in `bin/skilldrop.js`

```js
const BOOTSTRAP_MARKETPLACE_KEY = "your-org-skilldrop";
const BOOTSTRAP_GITHUB_OWNER   = "your-org";
const BOOTSTRAP_GITHUB_REPO    = "your-skilldrop-fork";
```

Publish your fork to npm or distribute `bin/skilldrop.js` directly.

### 3. Team members run bootstrap

```bash
node skilldrop.js bootstrap
# or, if published to npm:
npx your-org-skilldrop-cli bootstrap
```

## Mirror a vetted subset internally

Not every org can install from a public git host, and most want a reviewer to sign off on what
reaches their machines. `package` copies the packs or skills you choose into a standalone
catalogue you can host anywhere git runs:

```bash
npx skilldrop-cli package ./skills-mirror --pack dev-team,design   # brings core along, plus loops whose skills are all included
npx skilldrop-cli package ./skills-mirror --skills doc-critique,adr-generator
npx skilldrop-cli scan --from ./skills-mirror                       # the supply-chain scan, before anyone reviews it
```

`MIRROR.json` in the output records the source, the CLI version, the date, and a SHA-256 for
every file, so the reviewer can see exactly what came across and a later mirror can be diffed
against it. Push the folder to your internal git host, tag it, and install from the tag:

```bash
npx skilldrop-cli install --pack dev-team --from https://git.example.internal/platform/skills-mirror#2026-10
```

## Start your own catalogue

For skills your teams write themselves:

```bash
npx skilldrop-cli init-catalogue ./team-skills --pack platform
cd team-skills && npx skilldrop-cli new-skill deploy-checklist --pack platform
```

`init-catalogue` writes the layout the CLI reads, one example skill that passes
`skilldrop validate`, a README with the install command, and a GitHub workflow that runs
`validate` and `scan` on every pull request.

## What bootstrap writes

```json
{
  "extraKnownMarketplaces": {
    "skilldrop": {
      "source": { "source": "github", "owner": "sananthanarayan", "repo": "skilldrop" }
    }
  }
}
```

Running it a second time is safe — it detects the existing entry and exits cleanly.

## CI drift guard

The `pages.yml` workflow runs `python3 build_marketplace.py --check` before every Pages deploy. A PR that changes a pack without regenerating `marketplace.json` fails at that step. To regenerate:

```bash
python3 build_marketplace.py
```

Commit the updated `.claude-plugin/marketplace.json`.

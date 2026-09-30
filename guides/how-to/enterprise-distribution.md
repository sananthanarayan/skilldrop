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

The `pages.yml` workflow runs `python3 build_marketplace.py --check` before every Pages deploy. A PR that edits `packs.json` without regenerating `marketplace.json` fails at that step. To regenerate:

```bash
python3 build_marketplace.py
```

Commit the updated `.claude-plugin/marketplace.json`.

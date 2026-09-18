---
rfc: 0027
title: Retiring the agentbundle export, and per-pack Claude plugins
status: implemented   # draft → accepted | rejected → implemented
date: 2026-09-18
author: sananthanarayan
---

# RFC-0027: Retiring the agentbundle export, and per-pack Claude plugins

Supersedes the **outbound** half of [RFC-0014](0014-agentbundle-interop.md). The inbound half —
`skilldrop-cli --from <repo>` reading `packs/<p>/.apm/skills` catalogues — is untouched and stays.

## Problem / use case

RFC-0014 shipped a generated `agentbundle-catalogue` branch so an agentbundle user could run
`agentbundle install --pack <p> git+…#agentbundle-catalogue`. RFC-0014 itself left the open
question: *confirm the agentbundle install base justifies owning the re-alignment tax.* Two
months of evidence answers it.

- **Nobody is told it exists.** `README.md` carries zero install instructions pointing at the
  branch. Its only mention outside the generator is RFC-0014. An undocumented install path has
  no users by construction.
- **The tax is real and one-sided.** agentbundle shipped 61 releases between 2026-06-08 and
  2026-09-16 (0.2.0 → 0.46.1). skilldrop targets adapter-contract 0.17, from July. His verifier
  gates our branch publish, so his release cadence sets our maintenance cadence.
- **It broke, on a field we will never have.** The 2026-09-18 run failed CAT-V-018 —
  `evals[N].expected_output must be a non-empty string` — across 48 of 57 skills, 47 of them
  untouched by that push. skilldrop's eval shape is `{id, prompt, assertions}`; `expected_output`
  exists only to satisfy a schema we do not own. Satisfying it means either inventing a field or
  synthesizing one from `assertions` and calling the result an expected output, which it is not.
- **The export carries no capability.** Every file in `dist/` is `packs.json` + `skills/`
  rearranged into a different directory layout. There is nothing to lose — with one exception.

That exception is **per-pack Claude Code plugins**. The export's generated
`.claude-plugin/marketplace.json` listed six pack plugins; main's lists one whole-catalogue
plugin. RFC-0014 called per-pack granularity "a deliberately deferred step" because it needs
generated directories. It has been shipping this whole time, but only as a side effect of an
export aimed at a different tool — the right capability reached through the wrong contract.

## Fit check

Structural change. Golden rules touched:

- **Rule 1–2 and RFC-0001 (skills stay in flat `skills/<name>`)** — upheld. The per-pack trees
  exist only in build output on a force-pushed branch; `skills/<name>` on main remains the single
  source. This is the same rule that made physical packs unacceptable in the source tree.
- **Rule 4 (never invent commands or file conventions)** — the `git-subdir` plugin source, its
  `path`/`ref` fields, and the `#branch` marketplace suffix are all read from Claude Code's
  published plugin-marketplace schema, not inferred.

## Proposal

1. **Delete the outbound export**: `build_catalogue.py` (295 lines),
   `.github/workflows/agentbundle-catalogue.yml` (66), the `dist/` ignore entry, and the
   `agentbundle-catalogue` branch.
2. **Keep the inbound reader** unchanged in `bin/skilldrop.js`. Consuming his catalogue costs
   nothing and is the documented half.
3. **Re-home per-pack plugins under skilldrop's own contract.** `build_marketplace.py` gains
   `--dist DIR`, rendering `packs/<pack>/{.claude-plugin/plugin.json, skills/…, agents/…}`, and
   the committed marketplace on main gains one `git-subdir` entry per pack pointing at
   `packs/<name>` on a new generated `plugins` branch. Discovery stays one command against main:

   ```
   /plugin marketplace add sananthanarayan/skilldrop
   /plugin install solution-architect@skilldrop
   ```

   A pack ships the reviewer agents its own skills delegate to — resolved with the same
   `` `x` subagent `` pattern `validate.py` uses — so a pack carrying `pre-merge-review` cannot
   hand the user a dangling delegation.
4. **Two build-time guards**, because a plugin that advertises what it does not carry is worse
   than no plugin: `--dist` refuses to render when `packs.json` names a skill folder that does
   not exist, and the workflow asserts every `git-subdir` path the marketplace advertises was
   actually rendered, before publishing.

The difference that matters: `plugins` renders against Claude's plugin schema, which skilldrop
reads directly. No third-party verifier gates the publish, so there is no re-alignment tax.

## Alternatives considered

- **Keep the export and synthesize `expected_output` from `assertions`.** Lost: it would turn
  CI green while making skilldrop's evals assert something they do not mean, and it buys a
  re-alignment obligation against a contract moving ~20 minor versions a month for an audience
  that is, on the evidence, zero.
- **Keep the export unfixed and let the branch go stale.** Lost: a permanently red workflow
  trains everyone to ignore CI, which is the one signal that has to stay trustworthy.
- **Put the per-pack directories on main.** Lost: that is physical packs, duplicating every
  skill file in git — exactly what RFC-0001 rejected.
- **Skip per-pack plugins entirely.** Lost: it is the one real capability in the export, and
  `git-subdir` makes it cost one generated branch that answers only to us.
- **Do nothing.** Lost: RFC-0014's open question now has an answer, and it is no.

## Decision

Accepted and implemented 2026-09-18. RFC-0014 stays as the record of the inbound reader and of
why the outbound branch was built; this RFC records why it was retired.

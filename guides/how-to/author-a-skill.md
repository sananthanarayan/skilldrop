---
title: Author a new skill
summary: The short version of the authoring path — what a skill must contain, what gates it, and where the full contributor rules live.
kind: how-to
---

# Author a new skill

Full contributor guide — the three lanes, the PR gates, and the release flow — is in [CONTRIBUTING.md](../../CONTRIBUTING.md). The short version:

0. Write a one-page RFC first — copy [`docs/rfcs/0000-template.md`](../../docs/rfcs/0000-template.md) to `docs/rfcs/NNNN-<slug>.md` and record the problem, the fit check, and the alternatives. New skills and structural changes need one; fixes to existing skills don't.
1. Create `skills/<your-skill>/SKILL.md` with this frontmatter:
   ```yaml
   ---
   name: your-skill
   description: One sentence, use-case-first. AI agents match this against user prompts to decide when to invoke.
   ---
   ```
2. Add `skills/<your-skill>/manifest.json` with the same `name` + `description` plus declared `deps` and required env vars — this is what makes the skill portable across IDEs.
3. Keep `SKILL.md` short (under ~500 lines). Move long reference material into sibling files like `reference.md`, `examples.md`, or `templates/`.
4. If your skill needs scripts, drop them in `scripts/` and reference them with a path relative to the skill folder — **avoid hard-coding `${CLAUDE_SKILL_DIR}` only**; show both paths so non–Claude-Code users aren't stuck.
5. Add an `evals/` folder: `evals.json` (at least one realistic prompt with a list of assertions the output must satisfy) and `eval_queries.json` (phrases that should and should **not** trigger the skill). These double as the checklist for the manual test pass and keep the `description` honest about when the skill fires.
6. Add an entry to the **Skills in this repo** table above and to the **Installing dependencies** table.
7. Add the skill to at least one pack **and** at least one outcome in `packs.json`.
8. If the change is going out in a release, add a bullet to [`CHANGELOG.md`](../../CHANGELOG.md) under the new version — the site build fails without one.
9. Run `python3 validate.py` from the repo root — it checks name consistency, the tier sync with `model-routing.json`, the `related`↔SKILL.md reference sync, description sync, pack and outcome membership, and eval file shape.

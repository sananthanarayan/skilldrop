## What this changes

<!-- What a user can now do, in a sentence or two. Link the RFC for a new skill or a structural change. -->

## Checklist

The full list is in [AGENTS.md → Before you commit](../AGENTS.md#before-you-commit). The ones most often missed:

- [ ] `python3 validate.py` passes
- [ ] New or changed skill: folder name = `SKILL.md` name = `manifest.json` name, the `version` is bumped, and `evals/` has realistic trigger *and* no-trigger queries
- [ ] Ran the changed skill by hand at least once, and the output meets its own quality bar
- [ ] A new or changed script has tests in `tests/test_<skill>.py`, and `python3 -m unittest discover -s tests -t .` passes
- [ ] `CHANGELOG.md` has a bullet under the new version, saying what a user can now do, if this ships in a release
- [ ] `python3 build_marketplace.py && python3 build_llms.py` rerun if a skill, pack or loop changed
- [ ] No secrets, customer or employer data, or real people's or organisations' names in examples or evals; every scenario is made up

## How I checked it

<!-- Commands run and what they showed. -->

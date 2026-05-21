<!--
Thanks for contributing to skilldrop. A couple of policy rules before you submit:

1. PRs must come from a feature branch in a fork or in this repo — never directly from `main`.
2. Only maintainers can approve and merge (see MAINTAINERS.md).
   - Contributors: do not self-merge even if you have access.
   - Maintainers: self-merge is allowed for the bypass cases documented in CONTRIBUTING.md → "Maintainer bypass". For everything else, request review from the other maintainer.
3. Make sure your branch is up to date with `main` before requesting review.
-->

## Summary

<!-- 1–3 sentences. What does this PR do, and why? Lead with the *why*. -->

## Type of change

- [ ] New skill
- [ ] Improvement to an existing skill (tightened rubric / new template / new example / bug fix)
- [ ] Repo / docs / governance change (README, CONTRIBUTING, CODEOWNERS, .claude/settings.json, etc.)
- [ ] Other — please describe

## Worked example (required for new skills, encouraged for existing-skill changes)

<!--
Show one realistic input and the output you produced during manual testing.
For new skills: this is the proof the skill earns its keep. For improvements:
showing before/after output makes review fast.
-->

**Input:**

```
{paste a realistic prompt or input}
```

**Output:**

```
{paste the artifact the skill produced}
```

## PR checklist

<!--
Lifted from CONTRIBUTING.md. Tick each item. If one doesn't apply, mark it
N/A with a one-line reason — don't silently skip.
-->

### Skill basics
- [ ] Folder name = `SKILL.md` `name` = `manifest.json` `name`. Kebab-case, no version suffix.
- [ ] `SKILL.md` is under ~500 lines (long material moved to `reference.md` / `templates/` / `lenses/` / `rubrics/`).
- [ ] **Quality bar** and **Anti-patterns to avoid** sections present in `SKILL.md`.
- [ ] Description leads with the use case and ends with trigger phrases.
- [ ] At least one worked example (inline or in `examples/`).
- [ ] No secrets / personal data / proprietary content in templates or examples.

### Repo housekeeping
- [ ] **`README.md` updated** — table row added in the right section; install line added if there are runtime deps.

### Quality gates
- [ ] **Manual test pass** — installed into Claude Code and invoked end-to-end on the example above; output meets the skill's own quality bar.
- [ ] (If touching code/scripts) — ran `devils-advocate` on the diff. List any deliberate exceptions below.
- [ ] (If touching a `SKILL.md` for an existing artifact-generator skill) — ran `doc-critique` against the matching rubric. List any deliberate exceptions below.

### Branch & merge policy
- [ ] This PR is from a feature branch, **not** from `main`.
- [ ] Branch is up to date with `main` (rebase or merge before requesting review).
- [ ] **Contributor:** I will not self-merge — only a maintainer can.
- [ ] **Maintainer:** if self-merging without peer review, the change fits a documented [Maintainer bypass](../CONTRIBUTING.md#maintainer-bypass-when-direct-commits-are-ok) case, and I've explained why above.

## Linked issues / context

<!-- e.g. "Closes #12", "Follow-up to #7", or "Discussed in #15" -->

## Notes for the reviewer

<!--
Anything reviewer-specific: places you're unsure about, parts you'd like a
second opinion on, deliberate trade-offs you made. Honesty here saves a
round trip.
-->

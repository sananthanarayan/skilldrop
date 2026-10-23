---
name: dependency-upgrade-review
description: Give a merge verdict on a dependency-upgrade pull request (Dependabot, Renovate or a hand-made bump) across npm, pip, Go, Cargo and Maven lockfiles and GitHub Actions pins. Reads the release notes for every skipped version, lists what the lockfile changes beyond the PR title (transitive bumps, new and removed packages, install scripts, registry changes), checks each SHA pin against its release tag and against the PR's other pins, checks raised runtime floors against the images and runners that install it, says whether CI ran the changed code, traces what each caller of a changed API now does and writes the rollback. The reply leads with MERGE, MERGE AFTER CHECKS or DO NOT MERGE and the reasons that decide it. Use when the user says "review this Dependabot PR", "is this Renovate bump safe to merge", "can I merge this dependency upgrade", "check this lockfile diff", or "is this action SHA pin right".
---

# dependency-upgrade-review

A dependency bump is someone else's code entering the repo under a one-line title. This skill reads it the way a careful maintainer does: every release between the old and new version, every line of the lockfile, every pin, every place the code installs and runs, and the tests that would have caught a break. The verdict follows from those checks, not from a green badge. The reply is short: the verdict and what decides it come first, and the checks that found nothing take one line. Reviewing the repo's own code changes is `pre-merge-review`; writing the notes for a release of this project is `release-notes`; planning a framework migration across many PRs is `migration-plan`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** A check nobody ran is an open check, written as the command that runs it. It is never reported as passed, and "CI is green" closes only the checks CI actually ran. Say what was not checked and the command that checks it; never narrate the session (what was blocked, denied or unavailable).

Steps 1 to 10 are the review. Step 11 is the reply, and most of what the review turns up stays out of it.

1. **Get the diff, the notes and the code, asking once.** Three inputs: the PR diff covering manifests, lockfiles and workflow files (`gh pr diff 212` or `git diff origin/main...HEAD`); the release notes or changelog for every version between old and new; the repo, or at least the files that import the package and the CI workflow files. Also read what decides where the code installs and runs: the Dockerfile or base image, every workflow that installs dependencies (release, deploy and scheduled ones too, not only the PR's), `.nvmrc` / `.python-version` / `engines`, and any note in the PR body of the runtime the lockfile was generated on. When the PR has more than one commit, note who made each; a hand-made commit on a bot's PR is read first. Ask for what is missing in one message. With network access, fetch missing notes; without it, each missing release becomes an open check.

2. **Run the diff script first.** It lists every changed dependency with old → new, semver class, direct or transitive, and flags added and removed packages, install hooks, native-code hints, registry changes, licence changes, runtime requirement changes, pins, and one tag pinned to different commits, then prints a floor verdict.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/upgrade_diff.py" pr.diff --title "Bump quillmark from 3.4.1 to 4.1.0"
   # Other IDEs (from the skill folder)
   python3 scripts/upgrade_diff.py pr.diff --title "Bump quillmark from 3.4.1 to 4.1.0"
   ```
   It reads stdin with `-` (`gh pr diff 212 | python3 scripts/upgrade_diff.py -`). If it reports version lines out of context, re-run on `git diff -U12`. If no script can run, read every lockfile hunk by hand with the per-ecosystem notes in [`reference.md`](reference.md).

3. **List everything the lockfile changes beyond the title.** The title names one package; the lockfile is the truth. Find each of: transitive bumps (with class), packages added, packages removed, new install scripts (`hasInstallScript: true`, a `preinstall` / `install` / `postinstall` / `prepare` hook, pnpm `requiresBuild: true`), new native or binary dependencies (`prebuild-install`, `node-gyp`, a Cargo `-sys` crate, wheels for only some platforms), a changed `resolved` / `source` / index URL, a raised `engines` or `python-versions`, and a maintainer or publisher change when the input shows one. ✅ *"Also changes: `entity-codec` 2.1.0 → 3.0.2 (major, licence MIT → MPL-2.0), adds `quill-native-highlight` 1.0.0 with an install script, removes `html-escape-lite`."* ❌ *"Bumps quillmark to 4.1.0."*

4. **Class each jump.** Major, minor or patch from the version numbers. Below 1.0 the minor is the breaking number: 0.8.3 → 0.9.0 is a breaking jump, and below 0.1 so is the patch. A Go module path gaining `/v2` is a new module, not a bump. A prerelease target (`-rc.1`, `-beta`) or a downgrade is never a plain MERGE. A moving major tag (`@v2` → `@v3`) spans every v2.x after the one in use plus v3.0.0 to the current v3.

5. **Read every release between old and new, not only the target.** For each direct dependency, read every release after the old version up to and including the new one, and pull five things from each: breaking changes, dropped runtime versions, deprecations, security fixes, licence changes. Transitive majors, 0.x breaking jumps and new packages get the same reading; transitive patch and minor bumps are listed, not read. Name each release whose notes are missing. Copy version numbers exactly as the notes give them: "deprecated since 2.2, warns from 2.5.0" is two facts. Note any migration aid an intermediate release offers (an opt-in flag, a compatibility mode); it is the staged path. A security fix is a reason to take the upgrade; when the full jump is blocked, name the smallest version that carries the fix as the alternative.

6. **Search for every changed API, then trace each caller.** For each removed or renamed function, changed signature, changed default, changed return value and changed error, search and report `file:line` for each hit, or "no hits". Give the search (`git grep -n -E "renderInline|setOptions|render\(" -- '*.js' '*.ts'`); with no repo in hand, give that command as an open check and claim neither hits nor no hits. Then read the calling function and say what it does under the new behaviour, and the fix in this repo's code:
   - A return value that became an exception skips every `if result is None` / `== -1` branch and escapes the retry or fallback built on it.
   - A tuple or dict that became an object breaks the unpacking or the key access.
   - A changed default hits every call that doesn't pass the option.
   - An import inside a function fails only when that function runs, never at import time or test collection.
   ✅ *"`load_profile` (`app/cache.py:31`) falls back to the database when `cache.get()` returns `None`; from 5.0.0 `get()` raises `CacheMiss`, so every miss escapes as an error and the fallback never runs. Catch `CacheMiss` there, or move to 4.6 first with `strict_miss=True`."* ❌ *"`get()` behaviour changed in 5.0.0; check usages."*

7. **Check every runtime floor against where the code runs.** A raised minimum (Python `>=3.10`, Node `engines >=20`, a Go directive, an MSRV, wheels built only for some interpreter versions, an action needing a newer runner) is compared with the Dockerfile `FROM`, each workflow's `setup-*` version and matrix, `.nvmrc` / `.python-version`, self-hosted runner versions, and the runtime the lockfile was generated on. CI and the lock tool running a newer runtime than production is how a green PR breaks the image build. ✅ *"`deploy/Dockerfile:1` builds on `node:18-alpine` and 6.0 needs Node >=20; CI runs Node 22 (`ci.yml:14`), so the PR passed and the image build will fail at `npm ci`."*

8. **Verify every pin the PR changes; an unverified SHA is an open check.** A SHA-pinned action (or any dependency pinned to a commit) must be the commit its release tag points to:
   ```bash
   git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag> 'refs/tags/<tag>^{}'
   ```
   For an annotated tag the `^{}` line is the commit; for a lightweight tag the single line is. Not run means unverified, never "looks right": a SHA from a fork also resolves under the upstream path. Compare the PR's pins with each other: one action and tag pinned to two different SHAs means at most one is the tag's commit, and the suspect is the one changed by hand or in the job with secrets. A SHA with no version comment is an unknown release. A tag-only pin (`@v3`) is weaker than a SHA, because the tag can be moved after review. Say what the job hands the action: a `secrets.*` token, `id-token: write` or `contents: write` raises the stakes. Pins the PR does not change are not part of this review.

9. **Say whether CI ran the changed code.** A green check proves what it ran and nothing else. For each changed package or action, name the workflow job and test that exercise it, or say nothing does. The usual gaps: a workflow triggered only by a tag push, a release, a schedule or `workflow_dispatch`; a file no test imports (a step 6 hit with no test); a mock that returns the old behaviour (a fake client that never times out tests the old contract); a PR job that installs differently from the release job (`npm ci --ignore-scripts` on the PR, plain `npm ci` in release means a new install script first runs in the job holding the secrets). ✅ *"`ci / test` runs `test/note.test.js`, which renders Markdown with no raw HTML, so the `sanitize` change is untested; nothing imports `src/render/comment.js`."* ❌ *"All checks pass."*

10. **Write the rollback, then derive the verdict.** Rollback: `git revert` of the merge commit, or the pin-back for the ecosystem (`npm install quillmark@3.4.1`, `poetry add tidyparse@2.2.0`, `go get <module>@v0.8.3 && go mod tidy`, the old `uses:` line and SHA) with the lockfile regenerated, plus what a revert does not undo (a lockfile format migration, data or cache the new version wrote, an artifact already published or deployed, a security fix that rolling back reopens; then pin back to the first fixed version). Per-ecosystem commands are in [`reference.md`](reference.md). Then exactly one verdict per PR:
    - **DO NOT MERGE** when any holds: a removed or changed API is still used and the PR does not fix it; a runtime floor above what production or the release job runs; a new install script or native binary download nobody has confirmed is expected; a dependency source moved to an unexplained host; a SHA that does not match its tag, or two SHAs for one tag; a pin weakened (SHA to tag, tag to branch); a licence the project cannot ship; a target version an advisory names as vulnerable; a red CI check.
    - **MERGE AFTER CHECKS** when none of those holds but any of these does: an unverified SHA; a major or 0.x breaking jump; a release whose notes were not read; changed code no CI job runs; a deprecated API still used; a new package or transitive major; a licence change that needs sign-off; a moved tag-only pin; no repo to search.
    - **MERGE** only when every check above is closed, with the evidence in the reply.
    The script's floor is a minimum; raise it on what steps 5 to 9 find. Lower DO NOT MERGE only when the user confirms the install script or new source is expected, and say so.

11. **Reply short, verdict first, in one message.** Only what changes the decision or the fix goes in.
    - **First line:** the verdict and the one to three reasons that decide it, in plain words. With two PRs, one line each. ✅ *"DO NOT MERGE. 6.0 needs Node 20 and the production image runs 18, and two call sites break on removed APIs."* ❌ *"Here is my review of the quillmark upgrade."*
    - **🟥 Blockers, numbered, the one that breaks first on top.** Each: what breaks, `file:line`, why the green check missed it, and the fix in this repo, in two to four lines. When an intermediate release offers a migration aid, one line after the blockers gives the staged path. The count in the first line matches the list.
    - **🟧 Before merge:** each open check as the command or action that closes it. An unverified SHA is written as the command and the SHA it must equal.
    - **Also in the lockfile:** one line naming every package added, removed or moved beyond the title, with install scripts and source changes called out. Not a table.
    - **Rollback:** one or two lines, the command and what a revert leaves behind.
    - **To confirm** only for what only the user can answer (is this install script expected?); omit it when empty.
    - **Last line:** one sentence offering the next piece of work (the code fixes, the pin change).
    No tables, no recited changelog, no pins or files the PR does not touch, no empty sections. A clean MERGE fits in about 120 words; a blocked PR with three blockers in about 300.

**Non-interactive runs** (subagent, CI, headless): with no diff, emit `BLOCKED: need the PR diff covering the manifests, lockfiles and workflow files (gh pr diff <number>)`. Missing release notes, repo or CI files do not block: each becomes a named open check, the verdict is at best MERGE AFTER CHECKS, and the gap is stated first as `[assumption] notes for <versions> not read` or `[assumption] CI coverage unknown, treated as none`.

## Useful references in this skill

- [`reference.md`](reference.md): reading each ecosystem's lockfile diff, where install scripts, sources and runtime floors show up, how to list the releases between two versions, SHA verification details, tracing behaviour changes, and per-ecosystem rollback commands with what a revert leaves behind
- [`scripts/upgrade_diff.py`](scripts/upgrade_diff.py): stdlib parser for a unified diff of manifests, lockfiles and workflow files; prints changes, flags, pin checks and a floor verdict (exit 2 on bad input)
- [`examples/ledgerline-tidyparse.md`](examples/ledgerline-tidyparse.md): worked example, a Poetry patch bump that earns MERGE, and a blocked reply in the same shape

## Quality bar

- **The first line is the verdict and the reasons that decide it,** one verdict per PR, following from the checks. Any unverified SHA, added install script, or removed API still in use rules out MERGE.
- **Every release between old and new is accounted for:** read, with its breaking changes, runtime drops, deprecations, security fixes and licence changes, or named as unread.
- **Everything the lockfile changes beyond the title is listed,** in one line: transitive bumps, added and removed packages, install scripts, native code, source and runtime changes.
- **Every changed API has a search result and every hit is traced:** what the caller does now and the fix, or the search command when there is no repo.
- **Every raised runtime floor is compared** with the base image, the CI runtime, the runners and the lockfile tool's runtime.
- **Every changed SHA pin is verified or given as the `git ls-remote` command,** and the PR's pins are compared with each other.
- **CI coverage is named per changed package:** the job and test that exercise it, or "nothing does", and how each workflow installs.
- **A rollback with the exact command** and what a revert does not undo.
- **Nothing reads as checked that was not run,** and nothing describes the session's tools or network.
- **No invented versions, advisories, APIs, files or test names;** version numbers are copied from the notes.

## When to use this skill

- ✅ A Dependabot or Renovate PR is open and someone asks whether to merge it
- ✅ A hand-made bump of one or more packages, with its lockfile diff
- ✅ A GitHub Actions version bump, SHA-pinned or tag-pinned
- ✅ A grouped update PR where the title hides how many packages moved
- ✅ Checking whether a lockfile diff brings in install scripts, new registries or new packages

## When NOT to use this skill

- ❌ Reviewing a PR whose substance is the repo's own code change: use `pre-merge-review`
- ❌ Writing the release notes or changelog for this project's next version: use `release-notes`
- ❌ Planning a multi-step framework or runtime migration (a major framework version across many services): use `migration-plan`
- ❌ Scanning installed skills for supply-chain patterns: that is the `skilldrop scan` command
- ❌ Choosing which library to adopt in the first place: this reviews a version change, not a selection

## Anti-patterns to avoid

- ❌ **The report reply.** A package table, a rollback essay and an empty "To confirm" around a verdict the reader has to dig for. Verdict and reasons first; the rest in a line each.
- ❌ **Reading only the target version's notes.** The breaking change usually lives in a release the PR skipped.
- ❌ **Trusting the title.** "Bump X from 1 to 2" says nothing about the transitive packages that moved with it.
- ❌ **Finding the change but not the caller.** "`fetch()` now raises" is half a finding; "so the retry loop never retries" is the finding.
- ❌ **Trusting CI's runtime.** CI on Python 3.11 says nothing about an image built on 3.9.
- ❌ **Calling a SHA pin fine because it is a SHA.** A SHA proves nothing until it matches the release tag, and two SHAs for one tag cannot both match.
- ❌ **"CI is green, ship it."** Release workflows, publish steps, lazy imports and mocked paths never ran on the PR.
- ❌ **Explaining the session.** "The network was blocked, so I couldn't check" is about the run, not the PR; give the command.
- ❌ **Hedged verdicts.** "Probably safe" is not a verdict; pick one of the three and give the reason.

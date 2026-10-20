---
name: dependency-upgrade-review
description: Give a merge verdict on a dependency-upgrade pull request (Dependabot, Renovate or a hand-made bump) across npm, pip, Go, Cargo and Maven lockfiles and GitHub Actions pins. Reads the release notes for every skipped version, lists what the lockfile changes beyond the PR title (transitive bumps, new and removed packages, install scripts, registry changes), checks that each SHA pin is the commit its release tag points to, says whether CI ran the changed code, finds the repo's uses of changed APIs and writes the rollback, ending in MERGE, MERGE AFTER CHECKS or DO NOT MERGE. Use when the user says "review this Dependabot PR", "is this Renovate bump safe to merge", "can I merge this dependency upgrade", "check this lockfile diff", or "is this action SHA pin right".
---

# dependency-upgrade-review

A dependency bump is someone else's code entering the repo under a one-line title. This skill reads it the way a careful maintainer does: every release between the old and new version, every line of the lockfile, every pin, and the tests that would have caught a break. The verdict follows from those checks, not from a green badge. Reviewing the repo's own code changes is `pre-merge-review`; writing the notes for a release of this project is `release-notes`; planning a framework migration across many PRs is `migration-plan`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** A check nobody ran is an open check, written as the command that runs it. It is never reported as passed, and "CI is green" closes only the checks CI actually ran.

1. **Get the diff, the notes and the code, asking once.** Three inputs: the PR diff covering manifests, lockfiles and workflow files (`gh pr diff 212` or `git diff origin/main...HEAD`); the release notes or changelog for every version between old and new; the repo, or at least the files that import the package and the CI workflow files. Ask for what is missing in one message. With network access, fetch missing notes from the package's releases page or changelog; without it, each missing release becomes an open check.

2. **Run the diff script first.** It lists every changed dependency with old → new, semver class, direct or transitive, and flags added and removed packages, install hooks, native-code hints, registry changes, licence changes and pins, then prints a floor verdict.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/upgrade_diff.py" pr.diff --title "Bump quillmark from 3.4.1 to 4.1.0"
   # Other IDEs (from the skill folder)
   python3 scripts/upgrade_diff.py pr.diff --title "Bump quillmark from 3.4.1 to 4.1.0"
   ```
   It reads stdin with `-` (`gh pr diff 212 | python3 scripts/upgrade_diff.py -`). If it reports version lines out of context, re-run on `git diff -U12`. If no script can run, read every lockfile hunk by hand with the per-ecosystem notes in [`reference.md`](reference.md).

3. **List everything the lockfile changes beyond the title.** The title names one package; the lockfile is the truth. Report each of: transitive bumps (with class), packages added, packages removed, new install scripts (`hasInstallScript: true`, a `preinstall` / `install` / `postinstall` / `prepare` hook, pnpm `requiresBuild: true`), new native or binary dependencies (`prebuild-install`, `node-gyp`, a Cargo `-sys` crate), a changed `resolved` / `source` / index URL, and a maintainer or publisher change when the input shows one. ✅ *"Also changes: `entity-codec` 2.1.0 → 3.0.2 (major, licence MIT → MPL-2.0), adds `quill-native-highlight` 1.0.0 with an install script, removes `html-escape-lite`."* ❌ *"Bumps quillmark to 4.1.0."*

4. **Class each jump.** Major, minor or patch from the version numbers. Below 1.0 the minor is the breaking number: 0.8.3 → 0.9.0 is a breaking jump, and below 0.1 so is the patch. A Go module path gaining `/v2` is a new module, not a bump. A prerelease target (`-rc.1`, `-beta`) or a downgrade is never a plain MERGE. A moving major tag (`@v2` → `@v3`) spans every v2.x after the one in use plus v3.0.0 to the current v3.

5. **Read every release between old and new, not only the target.** For each direct dependency, list every release after the old version up to and including the new one, and pull four things from each: breaking changes, deprecations, security fixes, licence changes. Transitive majors, 0.x breaking jumps and new packages get the same reading; transitive patch and minor bumps are listed, not read. Name each release whose notes are missing. ✅ *"3.5.0 fixes an attribute-injection bug in link titles and deprecates `setOptions()`; 4.0.0 removes `renderInline()` and turns `sanitize` off by default; 4.0.1 and 4.1.0 are fixes and an optional highlighter."* ❌ *"4.1.0 adds a native highlighter. Looks fine."* A security fix is a reason to take the upgrade; when the full jump is blocked, name the smallest version that carries the fix as the alternative.

6. **Search the repo for every API the notes change.** For each removed or renamed function, changed signature and changed default, search and report `file:line` for each hit, or "no hits". A changed default hits every call that doesn't pass the option. ✅ *"`src/render/note.js:7` calls `quillmark.render(markdown)` with no `sanitize`, so from 4.0.0 note bodies pass raw HTML through."* ❌ *"Check whether the code uses `renderInline`."* Give the search you ran (`git grep -n -E "renderInline|setOptions|render\(" -- '*.js' '*.ts'`); with no repo in hand, give that command as an open check and claim neither hits nor no hits.

7. **Verify every pin; an unverified SHA is an open check.** For a SHA-pinned action (or any dependency pinned to a commit), the pinned SHA must be the commit the release tag points to:
   ```bash
   git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag> 'refs/tags/<tag>^{}'
   ```
   For an annotated tag the `^{}` line is the commit; the other line is the tag object. For a lightweight tag the single line is the commit. Not run means `UNVERIFIED`, never "looks right": a SHA from a fork of the repo also resolves under the upstream path. A SHA with no version comment is an unknown release. A tag-only pin (`@v3`) moved to another tag is weaker than a SHA, because the tag can be moved after review; say so and give the command that finds the SHA to pin. Say what the job hands the action: a `secrets.*` token, `id-token: write` or `contents: write` raises the stakes of every pin in that job.

8. **Say whether CI ran the changed code.** A green check proves what it ran and nothing else. For each changed package or action, name the workflow job and test file that exercise it, or say nothing does. The usual gaps: an action or tool used only in a workflow triggered by a tag push, a release, a schedule or `workflow_dispatch`, which the PR never ran; a library used only in a file no test imports (a step 6 hit with no test); a test that runs the code but not the changed behaviour. ✅ *"`ci / test` runs `test/note.test.js`, which renders Markdown with no raw HTML, so the `sanitize` change is untested; nothing imports `src/render/comment.js`."* ❌ *"All checks pass."*

9. **Write the rollback.** The exact revert: `git revert` of the merge commit, or the pin-back for the ecosystem (`npm install quillmark@3.4.1`, `poetry add tidyparse@2.2.0`, `go get <module>@v0.8.3 && go mod tidy`, `cargo update -p <crate> --precise <old>`, the old `uses:` line) with the lockfile regenerated and committed. Then name what a revert does not undo: a lockfile format migration, a data, cache or schema format the new version wrote, an artifact built or published with it (a registry version cannot be republished), and a security fix that rolling back reopens. When the old version sits inside a fixed advisory's range, the pin-back target is the first fixed version, not the old one: ✅ *"pin back to 3.5.0"* ❌ *"pin back to 3.4.1"* when 3.5.0 fixed a bug affecting 3.0.0 to 3.4.x. Per-ecosystem commands are in [`reference.md`](reference.md).

10. **Derive the verdict from the checks.** Exactly one of:
    - **DO NOT MERGE** when any holds: a removed or changed API is still used and the PR does not fix it; a new install script or native binary download nobody has confirmed is expected; a dependency source or registry moved to an unexplained host; a SHA that does not match its tag; a pin weakened (SHA to tag, tag to branch); a licence the project cannot ship; a target version an advisory names as vulnerable; a red CI check.
    - **MERGE AFTER CHECKS** when none of those holds but any of these does: an unverified SHA; a major or 0.x breaking jump; a release whose notes were not read; changed code no CI job runs; a deprecated API still used; a new package or transitive major; a licence change that needs sign-off; a moved tag-only pin; no repo to search. Each check is a command or a concrete action.
    - **MERGE** only when every check above is closed, with the evidence in the reply.
    The script's floor is a minimum. Raise it on what steps 5 to 8 find. Lower DO NOT MERGE only when the user confirms the install script or new source is expected, and say so in the reply.

11. **Reply in this order, in one message:** the verdict and the one reason that decides it; 🟥 blockers, 🟧 checks before merge and 🟨 notes, each with `file:line` or the command; a short table of what the PR changes, including everything beyond the title; the rollback; "To confirm". A routine PR fits in about 300 words. Lead with what blocks, not with the package history.

**Non-interactive runs** (subagent, CI, headless): with no diff, emit `BLOCKED: need the PR diff covering the manifests, lockfiles and workflow files (gh pr diff <number>)`. Missing release notes, repo or CI files do not block: each becomes a named open check, the verdict is at best MERGE AFTER CHECKS, and the gap is stated first as `[assumption] notes for <versions> not read` or `[assumption] CI coverage unknown, treated as none`.

## Useful references in this skill

- [`reference.md`](reference.md): reading each ecosystem's lockfile diff, where install scripts and sources show up, how to list the releases between two versions, SHA verification details, and per-ecosystem rollback commands with what a revert leaves behind
- [`scripts/upgrade_diff.py`](scripts/upgrade_diff.py): stdlib parser for a unified diff of manifests, lockfiles and workflow files; prints changes, flags, pin checks and a floor verdict (exit 2 on bad input)
- [`examples/ledgerline-tidyparse.md`](examples/ledgerline-tidyparse.md): worked example, a Poetry patch bump with a transitive bump, real script output and the review that reaches MERGE

## Quality bar

- **Exactly one verdict, first, and it follows from the checks.** Any unverified SHA, added install script, or removed API still in use rules out MERGE.
- **Every release between old and new is accounted for:** read, with its breaking changes, deprecations, security fixes and licence changes named, or listed as unread.
- **Everything the lockfile changes beyond the title is listed:** transitive bumps, added and removed packages, install scripts, native code, source changes.
- **Every changed API has a search result:** `file:line` hits, "no hits", or the command to run when there is no repo.
- **Every SHA pin is verified or marked UNVERIFIED with the `git ls-remote` command;** tag-only pins are called weaker.
- **CI coverage is named per changed package:** the job and test that exercise it, or "nothing does".
- **A rollback with the exact command** and what a revert does not undo.
- **No invented versions, advisories, APIs, files or test names.** Everything cited appears in the diff, the notes or the repo supplied.

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

- ❌ **Reading only the target version's notes.** The breaking change usually lives in a release the PR skipped.
- ❌ **Trusting the title.** "Bump X from 1 to 2" says nothing about the twelve transitive packages that moved with it.
- ❌ **Calling a SHA pin fine because it is a SHA.** A SHA proves nothing until it matches the release tag.
- ❌ **"CI is green, ship it."** Release workflows, publish steps and untested code paths never ran on the PR.
- ❌ **"No breaking changes affect us" without a search.** Show the grep and its hits, or say it was not run.
- ❌ **A rollback that is only "revert the PR".** Name the lockfile regeneration and what a revert leaves behind.
- ❌ **Reciting the changelog.** Report the releases that change the verdict; one line covers the rest.
- ❌ **Hedged verdicts.** "Probably safe" is not a verdict; pick one of the three and give the reason.

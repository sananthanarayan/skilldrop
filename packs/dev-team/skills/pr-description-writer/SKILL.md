---
name: pr-description-writer
description: Write the pull request title and description for one change, from the actual diff and commits: what changed and why, how it was tested with only the checks that were really run, what a reviewer should look at first, and the risk and rollback. It also reports what the diff contains that the commits don't mention, such as a dependency bump, a deleted test or a schema change. Use when the user asks to write a PR description, a pull request summary, a merge request body, or says "describe this change for review", "write up this branch".
---

# pr-description-writer

You write the description a reviewer reads before the diff: a title, why the change exists,
what it does, how it was checked, where to look first, and what could go wrong. Everything in
it comes from the diff, the commits and what the user told you. One change, one description.

## How to respond

1. **Read the change itself.** In a git repository, find the base branch (the one the user
   names, else `main` or `master`) and read `git diff <base>...HEAD` and
   `git log <base>..HEAD`. If the user hands you a diff or patch file, read that. Read the
   whole diff, not the commit subjects: the subjects are the author's summary and the diff is
   the fact.

2. **Work out the one reason for the change.** A linked issue, the user's words, or the
   commit bodies. If none of them says why, write what the change does and put
   `Why: not stated — add the reason or the issue link` at the top of the body. Don't
   make up a motive, an issue number or a customer.

3. **Write the title.** Imperative mood, 72 characters or fewer, naming the behaviour that
   changes. ✅ "Retry webhook delivery on 5xx with backoff". ❌ "Fix bug". ❌ "Updates to
   webhook.py". Keep a `feat:` / `fix:` prefix only if the repository's history uses one.

4. **Write the body in this order**, leaving out a section that has nothing true to say:
   - **Why**: one or two sentences. The problem, not the solution.
   - **What changed**: three to six bullets on behaviour, grouped by what a user or caller
     would notice. No file-by-file tour.
   - **How it was tested**: only checks that were run, with the command or the evidence
     ("`pytest tests/webhooks -q`: 14 passed", "new test `test_retry_on_503`"). If you ran
     nothing and were told nothing, write `Not run` and list the checks worth running.
   - **Where to look first**: the one or two places a reviewer should spend their time, and
     why. Name files and functions.
   - **Risk and rollback**: what breaks if this is wrong, who notices, and how to undo it
     (revert, feature flag, migration down). Say plainly when a rollback is not clean.
   - **Not in this PR**: follow-ups the diff deliberately leaves out, if the commits or the
     user mention any.

5. **Report what the diff has that the commits don't mention.** Check for: a dependency or
   lockfile change, a deleted or skipped test, a schema or data migration, a changed public
   API or config default, a new secret or environment variable, files unrelated to the
   stated purpose, and leftover debug output. Put each one under **Reviewer notes** in the
   body, and repeat the list in your reply. A breaking change goes in the title or the first
   line of the body.

6. **Say when it should be more than one PR.** Two unrelated purposes in one diff, or a
   refactor mixed with a behaviour change, gets one line: what to split and where. Still
   write the description for the change as it stands.

7. **Hand it over.** Print the title and the body as Markdown, ready to paste. Don't open,
   edit or push the pull request unless the user asked for that.

**With no change to read** (no repository, no diff, no description of the change), say so in
one line and ask for the diff or the branch. With a described change and no diff, write the
description from the description, and state at the top that it was written without the diff.

## Quality bar

- **Everything traces to the diff, the commits or the user.** No invented issue numbers,
  metrics, reviewers or test results.
- **The test section is honest.** A check that wasn't run is listed as not run.
- **A reviewer learns where to look.** The body names the riskiest part of the diff.
- **Surprises are surfaced.** A dependency bump, deleted test, migration or API change that
  the commits skip appears under Reviewer notes.
- **Claims about the code are checked.** Before saying a test does or doesn't cover a
  change, or that two changes are independent, work it through against the diff (run the
  arithmetic, trace the call). If you can't confirm it, leave the claim out.
- **Short.** The body fits on one screen. A long PR gets a tighter summary, not a longer one.

## When to use this skill

- ✅ A branch is ready and needs a pull or merge request description
- ✅ A diff or patch file needs writing up for review
- ✅ An existing thin description ("fixes stuff") needs replacing before review

## When NOT to use this skill

- ❌ Notes for a whole release or a changelog entry across many changes. Use `release-notes`.
- ❌ Deciding whether the change is safe to merge. Use `pre-merge-review`.
- ❌ Designing the tests the change needs. Use `test-plan-generator`.

## Anti-patterns to avoid

- ❌ **Restating commit subjects as bullets.** The reviewer can read `git log`.
- ❌ **"Tested locally."** Name the command and the result, or write "Not run".
- ❌ **A file-by-file tour.** Group by behaviour; the diff already lists the files.
- ❌ **Inventing the why.** A missing reason is stated as missing.
- ❌ **Hiding a breaking change in the middle.** It leads.
- ❌ **Speculative reviewer notes.** A note that turns out wrong costs the reviewer more
  than no note. Report what the diff shows, not what it might imply.
- ❌ **Showing the machinery.** The description is for the reviewer: no mention of this
  skill, its files, or how the description was produced.

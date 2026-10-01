---
name: release-notes
description: Turn git history between two refs into release notes — a customer-facing version written in reader benefits and an internal Keep-a-Changelog version with commit traceability, breaking changes always first. Use when the user wants release notes, a changelog, "what's in this release", a deploy announcement, or to summarize changes since the last tag.
---

# release-notes

Converts commit history into two artifacts with different readers: **customer-facing release notes** (benefits, no commit-speak) and an **internal changelog** (Keep a Changelog format, every line traceable to a commit). The rule that drives everything: write for the reader who didn't make the change.

## How to respond

1. **Resolve the range.** Default: last tag to HEAD (`git describe --tags --abbrev=0`). If no tags exist, ask for a start ref or take the user's two refs. State the resolved range at the top of the output: "`v1.4.0..HEAD`, 37 commits, 2026-05-02 → 2026-06-10".

2. **Gather the raw material.** `git log <range> --no-merges --pretty='%h|%s|%an|%ad' --date=short` for the commit list; `git log <range> --stat` only when a subject line is too vague to classify. Where the `gh` CLI is available and the repo uses PRs, prefer PR titles over commit subjects (`gh pr list --state merged --search "merged:>={date}"`) — they're written closer to reader language. Don't require `gh`; commits alone are enough.

3. **Classify every change** into Keep-a-Changelog categories plus one local bucket:
   - **Added / Changed / Fixed / Deprecated / Removed / Security** — reader-visible
   - **Internal** — refactors, CI, deps, tests; appears in the internal changelog, never in customer notes
   - **Needs review** — can't tell what it does from the commit; goes in a list for the user, never guessed into customer notes

4. **Hoist breaking changes and migrations to the top** of both artifacts, each with an **Action required** line. A breaking change buried under "Changed" is the cardinal failure of release notes. Detect via `BREAKING`, `!:` conventional-commit markers, migration files, major dependency bumps, and removed public API — and say which signal triggered the flag.

5. **Rewrite, don't transcribe.** Each customer-facing line states what the reader can now do or no longer suffers. ✅ *"Fixed a crash when exporting reports with more than 10,000 rows"* — ❌ *"fix NPE in ReportExporter.flush()"*. Drop ticket numbers and author names from customer notes; keep both in the internal changelog with the short hash on every line.

6. **Emit both artifacts** with [`templates/release-notes.md`](templates/release-notes.md): customer notes first, internal changelog second, then the **Needs review** list. If the user wants only one artifact, emit that one — but the needs-review list is never optional.

## Useful references in this skill

- [`templates/release-notes.md`](templates/release-notes.md) — both artifact skeletons plus the classification cheat-sheet

## Quality bar

- **Breaking changes are first, with an action.** Every breaking entry has "Action required: …" a reader can execute. No action identifiable → it goes to Needs review, not to the top section unverified.
- **No commit-speak in customer notes.** Class names, function names, internal service names, and ticket IDs are all signals the line wasn't rewritten.
- **Every internal-changelog line ends in a short hash** (and PR number when available). A claim nobody can trace is a claim nobody can verify.
- **Internal noise stays internal.** Dependency bumps, refactors, CI, and test-only changes never appear in customer notes — not even as "various improvements".
- **Nothing is guessed.** A vague commit ("fix stuff", "wip") lands in Needs review with its hash; the skill never invents a user-facing meaning for it.
- **The range is stated.** Refs, commit count, and date span at the top — so a reader knows exactly what window the notes cover.

## When to use this skill

- ✅ Cutting a release and writing "what's new" for users or customers
- ✅ Maintaining `CHANGELOG.md` between versions
- ✅ A deploy/release announcement for internal stakeholders
- ✅ "Summarize everything merged since the last tag"

## When NOT to use this skill

- ❌ A single PR description — that's one change, just write it
- ❌ Reviewing the changes for quality or risk — that's `devils-advocate` / `sonar-review`
- ❌ Stakeholder narrative about *why* the release matters strategically — feed the notes to `exec-summary`
- ❌ Generating commit messages going forward — this skill reads history, it doesn't write it

## Anti-patterns to avoid

- ❌ **Transcribing commit subjects with bullets in front.** That's `git log` with extra steps — the rewrite into reader language is the entire job.
- ❌ **"Various bug fixes and improvements."** Either the fix is worth a line or it's internal; the vague catch-all is neither.
- ❌ **Burying a breaking change** in the middle of "Changed" because the commit didn't shout about it. The detection signals exist precisely for quiet breaks.
- ❌ **Padding a thin release.** Two real changes get two lines. Inflating with internal noise to look substantial erodes trust in every future release note.
- ❌ **Marketing adjectives.** "Blazing-fast", "completely redesigned", "supercharged" — state the measurable change ("export is ~3× faster on large reports") or state nothing.
- ❌ **Silently skipping unparseable commits.** They go to Needs review; the count of skipped commits is part of the output.

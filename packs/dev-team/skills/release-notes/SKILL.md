---
name: release-notes
description: Write release notes from a git log, a list of merged PRs or rough notes about what changed — for the audience and in the format the user names (a customer changelog page, an email, an in-app "what's new", store text, a CHANGELOG.md entry). Says nothing the input doesn't, writes a vague change only as far as it was described, puts breaking changes and anything the reader must do first, and keeps internal noise and working notes out of the text. Use when the user wants release notes, a changelog entry, "what's in this release", a deploy announcement, or to summarise changes since the last tag.
---

# release-notes

**The rule: nothing goes in the notes that the log or the user didn't say.** A release note is
read as a promise. The agent's habit is to make a vague commit sound finished: "tweaked onboarding"
becomes "onboarding is now simpler", a half-remembered fix gets a symptom, a reverted feature
gets announced because its commit is in the range. Each of those reads exactly like a real
change, and a customer will hold you to it. This skill's job is to write only what the input
supports, as far as it supports it.

## How to respond

1. **Find out what actually shipped.** Read the whole range or list before writing a line.
   - A change that was reverted later in the same range did not ship. Leave it out.
   - A later commit can narrow or contradict an earlier one ("partial fix", a figure revised,
     a date moved). Write the final state, not the first claim.
   - Where you have a repo and no list, take the range from the last tag to HEAD
     (`git describe --tags --abbrev=0`, then `git log <tag>..HEAD --no-merges`). Read a commit's
     body or diff only when its subject is too vague to tell what it does.

2. **Find what breaks or needs action, wherever it is said.** A breaking change is often not
   marked: a removed option in a PR description, a renamed setting in a commit body, an old
   endpoint "no longer accepted". Each one goes first, with the step the reader has to take,
   written for how this audience gets the release. Customers of a hosted service upgrade
   nothing; they need to know what stops working and what to do instead. A library's users
   need the version and the migration.

3. **Write only as far as each change was described.** "Fixed a bug in exports" stays that
   vague if that's all the input says. Don't add a symptom, a cause, a number, a date, a
   version, a PR number or a count the input doesn't give. A change you can't tell the meaning
   of stays out of the notes and goes in the short list in step 6.

4. **Write for this reader, in this format.** Use the channel, length and tone the user asked
   for: a customer changelog page, an email, a pop-up of a few lines, store text with a
   character limit, or the repo's own CHANGELOG style if there is one. Say what the reader can
   now do or no longer suffers ✅ *"Exports with more than 10,000 rows no longer fail"*, not
   what the code does ❌ *"fix NPE in ReportExporter.flush()"*. Use the product name only if
   you were given it.

5. **Leave internal work out of anything a customer reads.** CI, refactors, tests, dependency
   bumps, typo fixes and tooling are not news, not even as "various improvements". In an
   internal changelog they may appear if the repo's existing style includes them.

6. **Hand back the notes, then at most a few lines for the user.** The notes are clean: no
   commit range, commit count, hashes, "flagged by" notes, or review lists inside them unless
   the user's format asks for hashes (an internal CHANGELOG often does). After the notes, list
   once, briefly, what you left out and why: changes too vague to describe, claims the log
   contradicts, anything the user should confirm before publishing.

7. **Deliver from what you have.** With a log, a list or notes, write the notes and state any
   assumption about audience or format in one line. Ask first only when there is nothing to
   work from.

## Quality bar

- **Nothing in the notes goes beyond the input.** No invented feature, behaviour, symptom,
  figure, date, version, PR number or count.
- **Reverted and superseded changes don't appear;** the final state does.
- **Breaking changes and required actions come first,** found from the text as well as the
  markers, with an action that fits how the audience gets the release.
- **Internal noise is absent from customer text.**
- **The format, length and tone are the ones the user asked for,** and the notes carry no
  working notes.
- **Vague items are left out or kept vague, and named once to the user.**

## When to use this skill

- ✅ Cutting a release and writing "what's new" for users or customers
- ✅ A `CHANGELOG.md` entry between versions
- ✅ A deploy or release announcement for internal stakeholders
- ✅ "Summarise everything merged since the last tag"

## When NOT to use this skill

- ❌ A single PR description — that's one change; use `pr-description-writer`
- ❌ Reviewing the changes for quality or risk — that's `devils-advocate` / `sonar-review`
- ❌ A narrative about *why* the release matters strategically — feed the notes to `exec-summary`
- ❌ Writing commit messages going forward — this skill reads history, it doesn't write it

## Anti-patterns to avoid

- ❌ **Finishing a vague change.** "Looked at the search thing" becomes "search is faster".
  Keep it as vague as it was, or leave it out and say so.
- ❌ **Announcing reverted work.** A commit in the range is not a change that shipped.
- ❌ **Burying a quiet break.** No `!:` marker doesn't mean nothing broke; read the bodies.
- ❌ **"Various bug fixes and improvements."** Either a fix is worth a line or it's internal.
- ❌ **The working notes in the text.** Ranges, counts, hashes, "flagged by", a "Needs review"
  table in a customer email.
- ❌ **A changelog where an email was asked for.** Headings and bullets in a two-paragraph
  member update.
- ❌ **Marketing adjectives.** "Blazing-fast", "completely redesigned": state the measured
  change the input gives, or nothing.

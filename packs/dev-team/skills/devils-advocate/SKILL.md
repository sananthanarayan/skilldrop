---
name: devils-advocate
description: Adversarial review of a code change before it merges — the real bugs, most consequential first, each checked against the code before it is reported, with a fix that works. A passing test or clean local run counts as evidence only once you've said whether it would have caught the bug; when it couldn't, the review says why it passed and names the test that would have failed. Sized to the ask ("top 3", "skip the nits", "just security"); invents nothing about the codebase. Use right after a feature is declared done — before merging, before declaring "done", before moving to the next ticket.
---

# devils-advocate

**The rule: a green test is not evidence until you've said why it would have failed with the
bug.** Changes arrive with "tests pass" or "ran it locally, fine". The agent's habit is to
take that as support, or to ignore it. Both miss the most useful thing a reviewer can say:
*why* the test passed anyway. A fixture that happens to dodge the bug, a table that was empty
on the laptop, a test that runs the job once when the bug only shows on the second run, an
assertion that one bug cancels out. For each bug you find, say whether the cited tests or run
could have caught it, and if not, why it passed and the one test that would have failed:
✅ *"`test_refill` passes because it waits 2 s against a rate of 1/s, so it never sees the
partial-token case. Assert `allow()` is false at 0.5 s."*

A second rule: **report only what survives checking.** Before a finding goes in, trace it
through the code. Does an earlier guard already handle the case? Is the query actually
parameterised? Does the stated business rule make this behaviour correct? Does your own fix
do what you say it does? A false finding costs the reader more than a missed nit.

## How to respond

1. **Answer the question first.** Open with a plain answer to what they asked, usually
   whether it's safe to merge, and the worst problem in one sentence.

2. **Review the change, not the repo.** The diff, the files they named, or `git diff` of the
   working tree. Read the tests that came with it.

3. **Find what would bite, most consequential first.** Wrong results, data loss, security
   holes, failures on real data that the dev setup hides, retries and concurrency, then
   fragility. For a large or unfamiliar change, the checklists in
   [`lenses/edge-cases.md`](lenses/edge-cases.md),
   [`lenses/future-proofing.md`](lenses/future-proofing.md),
   [`lenses/adversarial-review.md`](lenses/adversarial-review.md) and
   [`lenses/test-coverage.md`](lenses/test-coverage.md) are a sweep to run privately; they are
   not sections of the reply.

4. **Each finding:** where (`file:line`), what goes wrong in one concrete scenario ("when
   `tz` is `None`, line 47 raises `TypeError`"), and the fix. When the fix is small,
   give it as code they can paste. When the change is a script or migration, give the
   corrected version.

5. **Say what the tests prove.** Apply the rule to every test or run the user cites, and name
   the missing tests as scenarios: ✅ *"No test runs the job twice; add one asserting the reminder
   email is sent once."*

6. **Size to the ask.** "Top 3" gets three. "Skip the nits" gets none. "Just security" gets
   security. Without a limit, report what would actually bite; leave style out unless asked.
   No severity counts, verdict labels or praise sections unless they asked.

7. **Invent nothing about the codebase.** No row counts, traffic, run times, callers,
   column contents or config you weren't shown. Where a finding depends on one, say what to
   check: "if `orders` already has rows in production, this migration fails".

8. **Deliver from what you have.** With code to review, review it. With nothing, ask for the
   diff in one sentence and name the three or four things you'll check in it.

## Useful references in this skill

- [`examples/rate-limiter-review.md`](examples/rate-limiter-review.md) — a change with "tests pass", and a review that says why they passed

## Quality bar

- **Every cited test or run is judged:** could it have caught each bug, and if not, why did it
  pass and what test would fail.
- **Every finding survives a trace through the code and the stated rules.** No false
  positives.
- **The answer to "can this merge?" comes first;** findings are ordered by consequence.
- **Fixes work,** and are code when the change is small.
- **The scope asked for is respected.**
- **Nothing about the codebase is invented.**

## When NOT to use this skill

- ❌ For greenfield prototype or spike code that's about to be thrown away.
- ❌ For one-line or trivial changes.
- ❌ As a substitute for human code review — it's a pre-pass.
- ❌ For *evaluating the choice of approach* before code exists. That's a design conversation: `design-doc`, then `doc-critique`.
- ❌ For code in a language you can't reason about line by line. Refuse rather than fabricate findings.

## Anti-patterns to avoid

- ❌ **"Tests pass" taken at face value,** or ignored. Say what they prove.
- ❌ **The plausible false positive.** SQL injection in a parameterised query; a bug in
  behaviour the business rule asks for; a CRLF issue text mode already handles.
- ❌ **Padding to fill sections.** Marginal findings are where the errors are.
- ❌ **A count that disagrees with the list.** Don't print counts.
- ❌ **Describing a fix instead of giving it** when it fits in a few lines.
- ❌ **Facts about production you weren't given.** Row counts, lock times, what a column holds.
- ❌ **Redesigning.** Stay on what's missing given this approach.

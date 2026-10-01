---
name: test-plan-generator
description: Generate a risk-based test plan for a feature, PR, or release — risks ranked by likelihood × impact, test cases pushed to the lowest pyramid level that catches the failure, every acceptance criterion mapped to a test, and an explicit "not tested" list. Use when the user asks for a test plan, test cases, a QA strategy for a change, "how should we test this", or pre-release test coverage.
---

# test-plan-generator

Produces a test plan that says what to test *first*, what to test *where* (unit vs integration vs e2e), and — the part most plans omit — what is deliberately not tested and why. Downstream of `user-story-splitter` (its ACs map straight into the coverage table); sibling of `feature-implement-loop` (which writes the tests this plan prioritizes).

## How to respond

1. **Ingest the change.** Accepts any of: a story/brief with acceptance criteria, a diff or PR, a release scope, or a prose feature description. If given a diff, read it before planning — the plan must name the actual surfaces touched, not generic areas. Ask at most 2 clarifying questions; tag every other unknown `[assumption]`.

2. **Rank risks before writing a single test case.** Build the risk table first: for each area the change touches, what could go wrong, likelihood (H/M/L), impact (H/M/L), and the resulting priority — **P1** (H/H or H/M), **P2** (M/M or H/L), **P3** (everything else). Test-case effort follows priority: P1 gets concrete cases, P2 gets cases or charters, P3 gets a one-line exploratory note or an explicit "accept the risk".

3. **Push each test to the lowest pyramid level that can catch the failure.** Unit if the logic is reachable in isolation; integration if the failure lives in a boundary (DB, queue, API contract); e2e only for journeys that genuinely cross systems. ✅ *"Discount rounding — unit test on the pricing function"* — ❌ *"Discount rounding — e2e checkout test"* (slow, flaky, and the assert is three layers from the bug).

4. **Map every acceptance criterion to at least one test case.** Emit the AC → test coverage table; an AC with no row is a finding, not an omission. Where the input has no formal ACs, derive them from the described behavior and tag them `[derived]`.

5. **Sweep the edge-case taxonomy against P1/P2 areas** — boundaries (0, 1, max, max+1), empty/null/missing, duplicates and idempotency, concurrent access, permission denied, dependency down or slow, clock/timezone/DST, oversized input, unicode. Only write cases for the ones that apply; name the ones skipped as not applicable so the reader sees the sweep happened.

6. **Write observable entry/exit criteria.** Entry: what must be true to start (env up, test data loaded, feature flag state). Exit: pass/fail conditions a release manager can verdict — ✅ *"All P1 cases pass; no open defects of severity major+ in the touched areas"* — ❌ *"QA signs off"*.

7. **Emit the plan with [`templates/test-plan.md`](templates/test-plan.md)** in one message: scope (in/out), risk table, AC coverage table, test cases grouped by pyramid level, test data + environment needs, entry/exit criteria, and **Not tested — accepted risks** with a one-line justification each.

## Useful references in this skill

- [`templates/test-plan.md`](templates/test-plan.md) — the full plan skeleton with the risk and coverage tables

## Quality bar

- **Risk table precedes test cases, and effort tracks priority.** A plan that gives equal depth to every area was written by coverage habit, not risk.
- **Every test case has a concrete expected result.** ✅ *"Then the response is 422 with error code `DUPLICATE_SKU`"* — ❌ *"Then an appropriate error is shown"*.
- **Every AC appears in the coverage table.** Uncovered ACs are listed as gaps at the top of the plan, never silently absent.
- **The "Not tested" section is non-empty.** A plan that tests everything is a plan that prioritized nothing — naming accepted risks is the deliverable.
- **Pyramid placement is justified by failure location**, not by what's easiest to write. Each e2e case states why no lower level could catch it.

## When to use this skill

- ✅ A feature/story is ready for test planning before or during implementation
- ✅ A PR or release needs a documented QA pass and exit criteria
- ✅ "How should we test this?" for a risky change (migration, payment flow, auth)
- ✅ Turning `user-story-splitter` output into a test strategy for the sprint

## When NOT to use this skill

- ❌ Writing the test code itself — hand the plan to `feature-implement-loop` or a human
- ❌ Adversarial review of code already written — that's `devils-advocate`
- ❌ Static-analysis or quality-gate findings — that's `sonar-review`
- ❌ A trivial change (typo, copy edit) — the plan would cost more than the risk

## Anti-patterns to avoid

- ❌ **Coverage theater.** Fifty shallow cases that all walk the happy path while the one migration risk gets a single line.
- ❌ **"Verify it works correctly" as an expected result.** If a new tester couldn't verdict pass/fail from the words alone, rewrite it.
- ❌ **Everything at e2e level.** The slowest, flakiest layer should hold the fewest tests, not the whole plan.
- ❌ **Omitting the not-tested list** because it feels like admitting weakness. Unstated gaps get discovered in production; stated ones get a conscious decision.
- ❌ **Test data as an afterthought.** "Use prod-like data" is not a data plan — name the records, states, and volumes the P1 cases need.
- ❌ **Exit criteria that name people instead of conditions.** Sign-off follows the criteria; it isn't one.

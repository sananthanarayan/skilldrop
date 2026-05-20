---
name: devils-advocate
description: Adversarial review of just-generated code, run *after* an agent (or human) declares a feature done. Challenges the implementation through four lenses — edge cases the first pass missed, baked-in assumptions that won't survive future requirements, what a staff engineer would push back on in code review, and test-coverage gaps for the new code paths. Produces severity-tagged findings (blocker / major / minor / nit) with file:line evidence and concrete fixes or missing test cases. Use immediately after a feature implementation or generation pass — before merging, before declaring "done", before moving to the next ticket.
---

# devils-advocate

You play the role of a **senior engineer in code review who is trying to find what the implementation missed**. Code that "works on the happy path" is the default state of newly-generated code — your job is to challenge it through four lenses and surface what the first pass didn't think about.

This skill is the **code counterpart to [`doc-critique`](../doc-critique/SKILL.md)** — same adversarial framing, applied to code instead of artifacts.

## When this skill runs

The trigger is **right after an agent (or human) has declared a feature done**. The implementation exists, the happy path likely works, tests may even pass — and that's exactly the moment the skill is most useful, because that's the moment everyone stops looking.

Specifically:
- ✅ After AI code generation for a feature ("here's the implementation")
- ✅ Before opening a PR / before requesting human review
- ✅ Before merging
- ✅ When the user asks "anything I might have missed?" or "is this ready to ship?"
- ❌ For a one-line fix or trivial change — overkill
- ❌ For greenfield exploration / spikes — adversarial review wastes effort on code that will be thrown away
- ❌ As a substitute for actual code review by a human — this is a *pre-pass*, not a replacement

## How to respond

1. **Identify the change under review.** In order of preference:
   - The agent / user has just shown you a diff — review that diff.
   - Git working tree has unstaged changes — `git diff` is the scope.
   - User points to specific files / a PR / a recent commit — that's the scope.
   - User says "the feature I just built" with no diff — ask which files, or run `git diff HEAD~1` if a commit was just made.

   **Don't review the whole repo.** The scope is the *just-generated* code. Touched files only.

2. **Classify the code shape.** What you challenge depends on what was built. Map to one or more:

   | Shape | Lens emphasis |
   |---|---|
   | HTTP / RPC endpoint, API handler | edge-cases (input validation, auth), adversarial (rate limit, error mapping) |
   | Async handler / queue consumer | edge-cases (retries, idempotency, poison messages), future-proofing (ordering) |
   | DB migration / schema change | future-proofing (rollback, online-safe), adversarial (locking, big-table risk) |
   | State machine / workflow | edge-cases (impossible transitions, concurrent updates) |
   | Parser / data transformation | edge-cases (malformed, encoding, huge inputs) |
   | CLI tool / script | edge-cases (missing flags, env, partial runs) |
   | UI component | edge-cases (loading/empty/error states, a11y) |
   | Background job / cron | edge-cases (overlap, missed runs, partial completion) |
   | Library / pure function | edge-cases (boundary inputs), future-proofing (API stability) |
   | Config / infra change | adversarial (blast radius), future-proofing (drift) |

   Multiple shapes is common — a PR can be "endpoint + migration + UI." Apply each lens to the right slice.

3. **Sweep the four lenses in order.** Each lens has its own checklist — read it, apply it, write findings. Don't merge lenses; each surfaces a different category of risk.

   | Lens | File | Asks |
   |---|---|---|
   | 1. Edge cases | [`lenses/edge-cases.md`](lenses/edge-cases.md) | What inputs / states / timings break this? |
   | 2. Future-proofing | [`lenses/future-proofing.md`](lenses/future-proofing.md) | What assumptions won't survive the next 6 months? |
   | 3. Adversarial review | [`lenses/adversarial-review.md`](lenses/adversarial-review.md) | What would a staff engineer push back on in review? |
   | 4. Test coverage | [`lenses/test-coverage.md`](lenses/test-coverage.md) | Which new code paths have no test, and which scenarios are missing tests? |

4. **Categorize every finding by severity:**

   | Severity | Meaning |
   |---|---|
   | 🟥 **Blocker** | This will ship a bug or a security issue. Examples: SQL injection, unhandled `null`, race condition on shared state, migration that locks a 10M-row table, missing auth check, infinite retry loop. |
   | 🟧 **Major** | This will hurt within months. Examples: hard-coded limits that 2× growth will hit, no idempotency on a retryable operation, error swallowed silently, no observability for a load-bearing path, magic constants. |
   | 🟨 **Minor** | Good craft. Examples: missing edge-case test, suboptimal log level, naming that won't age well, a comment that explains *what* instead of *why*. |
   | ⚪ **Nit** | Style, formatting, micro-preference. Optional. |

   When in doubt between two severities, **downgrade**. Inflated severity makes the report unreadable. If your output has more blockers than major findings, you're inflating.

5. **For every finding, write four parts:**

   - **Where:** `file:line` (e.g. `src/api/checkout.ts:47`) — and quote 5–15 chars of the offending line.
   - **What's wrong:** one sentence — which lens fired and why.
   - **Concrete scenario:** ✅ "When `discount=null` reaches line 47, `applyDiscount` throws `TypeError`." — ❌ "Doesn't handle null." A scenario the first pass can reproduce.
   - **Fix:** ✅ "Add `if (discount == null) return 0;` at the top of `applyDiscount` — or thread the null through to skip the line item entirely (preferred — see how `applyTax` handles it at line 102)." — ❌ "Add null handling."

6. **Open with a verdict, not the findings.** First thing the user sees:

   ```
   Verdict: SHIP WITH FIXES — 2 blockers, 5 major, 4 minor, 3 nits.

   The endpoint validates auth and the happy path but doesn't bound the request body (blocker — DoS via 1GB payload), and the new migration adds a NOT NULL column without a default on a table the migration script doesn't backfill (blocker — will fail on first deploy). Of the 5 major findings, 3 are around idempotency on the retry path. Test coverage misses the new error branches at api/checkout.ts:71–88 entirely.
   ```

   Verdicts: `SHIP IT` · `SHIP WITH FIXES` · `DO NOT MERGE` · `RECONSIDER APPROACH`. The last is for when the implementation works but solved the wrong problem (e.g. building a custom retry queue when the framework already has one).

7. **Output structure** — use [`templates/challenge.md`](templates/challenge.md):

   ```markdown
   # Devil's advocate: {feature name / PR title}
   _Scope: {N files, M lines changed} · Reviewed: {YYYY-MM-DD}_

   ## Verdict
   {one-liner} — {N} blocker · {N} major · {N} minor · {N} nit
   {3-sentence summary, lead with the worst}

   ## Findings by lens

   ### 1. Edge cases
   ### 2. Future-proofing
   ### 3. Adversarial review
   ### 4. Test coverage

   ## What's solid
   - {2–4 things the implementation got right — not flattery, real patterns to preserve}

   ## Suggested order to address
   1. Fix blockers
   2. Add the missing tests in §4 (they double as regression catches)
   3. Major findings in priority order
   ```

8. **End with "what's solid"**, not more criticism. The user (or the next agent) often needs to know what to *keep* and what *patterns to reuse* elsewhere in the change.

## Quality bar

- **Every finding has a reproducible scenario.** A senior engineer reading the finding should be able to reproduce the bug or violation in their head. "Doesn't handle null" is not a finding; "When `discount=null` reaches line 47, …" is.
- **Severity is calibrated.** More blockers than major ⇒ inflating ⇒ demote.
- **Findings cite `file:line`.** Reviewers must be able to jump to the spot. Section names aren't enough for code.
- **Fixes are concrete and paste-able where possible.** When you can suggest a one-line patch, do; when you can't, suggest the *approach* in one sentence — not "improve error handling."
- **Don't redesign.** This isn't your chance to push a different architecture. Stay in the lane of "given this approach, what's missing." If the approach itself is wrong, that's a single `RECONSIDER APPROACH` verdict, not a wholesale rewrite suggestion.
- **Test-coverage findings reference scenarios, not files.** ❌ "No test for `applyDiscount`." ✅ "No test covers `applyDiscount(null)` — add a case that asserts the function returns 0 (or skips) without throwing."

## When NOT to use this skill

- ❌ For greenfield prototype / spike code that's about to be thrown away.
- ❌ For one-line / trivial changes — overkill, and the noise drowns out real signal.
- ❌ As a substitute for human code review — it's a pre-pass, not a replacement.
- ❌ For *evaluating the choice of approach* before code exists. That's a design conversation, not a code challenge. Use `design-doc` + `doc-critique` for that loop.
- ❌ For generated code in a language you can't reason about line-by-line. Better to refuse than fabricate findings.

## Anti-patterns to avoid

- ❌ **Severity inflation.** If everything is a blocker, the report is unreadable. Most findings are major or minor.
- ❌ **Vague findings.** "Handle errors better" / "Consider edge cases" — the whole point of this skill is to *name* the missed cases. If you can't name a specific scenario, drop the finding.
- ❌ **Restating the lens.** ❌ "Code should be future-proof." ✅ "Hard-coded 100ms timeout on line 53 won't survive p99 growth — make it configurable."
- ❌ **Lecturing on style** when there's a real bug to flag. Style notes go in the Nits section, not on top.
- ❌ **Reviewing untouched code.** Out-of-scope. The skill challenges the *change*, not the codebase.
- ❌ **Demanding tests for *everything* the change touches.** Only the new logic and new error paths. Don't insist on backfilling tests for previously-untested neighbouring code.
- ❌ **Skipping "what's solid".** Trains the user (or downstream agent) to dread the skill. End on signal that's actionable in the other direction.

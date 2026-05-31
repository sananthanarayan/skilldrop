---
name: feature-implement-loop
description: Implement a feature or story so it ends up *verified*, not just generated. Takes a description + acceptance criteria, writes code and tests, then runs an adversarial review pass that hunts for gaps (broken edge cases, baked-in assumptions, uncovered acceptance criteria), and re-generates to close them — looping until the review is clean or a 3-round cap is hit. Use when handed a ticket / story / feature spec with acceptance criteria and the goal is shippable, self-checked code — not a first draft.
---

# feature-implement-loop

You drive a feature from spec to *verified* implementation through a self-correcting loop. The differentiator over plain code generation: you don't stop at "here's the code." You implement, adversarially challenge what you wrote, and regenerate to close the gaps — until every acceptance criterion has a passing test and the review surfaces no blocker/major findings, or a hard 3-round cap stops you and you report what's still open.

This is the **dev-workflow loop** counterpart to the artifact pipeline. It composes the [`devils-advocate`](../devils-advocate/SKILL.md) review *philosophy* into a build cycle — but at the human's invocation layer it stands alone: hand it a spec, get back checked code.

## Input

A feature/story with two parts:
- **Description** — what to build and why.
- **Acceptance criteria** — the conditions that define "done." If the user gives prose without explicit criteria, extract the implicit criteria first and **echo them back as a numbered list before writing any code.** No criteria, no loop — the criteria are the gate.

If acceptance criteria are missing and can't be inferred, ask for them (one question). Don't invent a gate the user didn't agree to.

## How to respond

1. **Restate the spec as a criteria checklist.** Number every acceptance criterion. This list is the contract the loop closes against — each criterion must end the run mapped to a test.

2. **Plan the verification first.** For each criterion, name the test that will prove it (unit / integration / e2e, and the assertion). Surface criteria that *can't* be tested automatically (e.g. "looks good on mobile") and flag them as **manual-verify** up front — they don't block the loop but must appear in the final report.

3. **Generate code + tests together.** Write the implementation and the tests that cover the criteria in the same pass. Follow the repo's existing conventions, language, and test framework — read a neighbouring file first; don't impose a new style.

4. **Run the adversarial review pass.** This is the heart of the loop. Challenge what you just wrote:
   - **In Claude Code (or any tool with subagents):** delegate to the `devils-advocate` subagent on the generated diff.
   - **Everywhere else (Codex, Cursor, Aider, …):** run the review inline, sweeping the four lenses yourself:
     1. **Edge cases** — empty/null/zero/negative/max/Unicode/concurrent/partial-failure inputs the code mishandles.
     2. **Assumptions** — hard-coded limits, ordering assumed, single-tenant baked in — that the spec or near-future will break.
     3. **Staff-engineer pushback** — concurrency, error handling, security (authz/injection/secrets), observability, blast radius, idempotency.
     4. **Acceptance-criteria coverage** — for each numbered criterion: is there a test, and does it actually assert the criterion (not just exercise the code)?
   - Tag findings 🟥 blocker · 🟧 major · 🟨 minor · ⚪ nit, each with `file:line` and a concrete fix or the missing test case.

5. **Apply the gate.** Compute whether gaps remain:
   - **Gap = any 🟥 blocker, OR any 🟧 major, OR any acceptance criterion without a passing, asserting test.**
   - 🟨 minor / ⚪ nit findings do **not** force another round — list them, don't loop on them.

6. **Loop or stop.**
   - **Gaps remain and rounds used < 3** → regenerate to close *only* the gap findings (don't churn unrelated code), then go back to step 4. Increment the round counter.
   - **No gaps** → stop: the implementation is verified. Go to the report.
   - **Gaps remain and rounds == 3** → stop anyway. Do **not** loop further. Report the remaining gaps explicitly as open — never silently declare done.

7. **Report.** Always end with:
   - **Status:** `VERIFIED` (clean) · `VERIFIED WITH OPEN ITEMS` (cap hit, gaps remain) · `BLOCKED` (couldn't generate / couldn't run tests).
   - **Acceptance-criteria table:** every criterion → ✅ covered (test name) · ⚠️ manual-verify · ❌ open (why).
   - **Round log:** what each round found and fixed (1 → 2 → 3). This is the proof of work — it shows the loop did something.
   - **Open items:** any remaining gaps after the cap, with the finding and why it wasn't auto-closable, so a human can finish it.

## Quality bar

- **Every acceptance criterion maps to a test by the final report.** A criterion with no asserting test is an ❌ open item — not a pass. This is the rule that makes the skill more than codegen.
- **The review challenges the code; it doesn't rubber-stamp it.** A round-1 review that finds nothing on a non-trivial feature is a smell — re-run it adversarially, assuming the first pass missed something (it usually did).
- **Tests assert behavior, not just execution.** ❌ a test that calls the function and checks it didn't throw. ✅ a test that asserts the criterion's expected output. Catch assertion theater in the review.
- **Regeneration is targeted.** Each round fixes the named gaps and leaves passing code alone. Don't rewrite the whole feature every round — that loses ground and never converges.
- **The cap is real.** 3 rounds, then stop and report. A loop that "just one more round"s past 3 is a bug. If it can't converge in 3, a human needs to see why.
- **The round log is honest.** If round 2 found nothing new, say so. If a gap was downgraded rather than fixed, say why. The log is the audit trail.

## When to use this skill

- ✅ A ticket / story / feature spec arrives **with acceptance criteria** and the goal is shippable, self-checked code.
- ✅ When the user says "implement this and make sure it actually meets the criteria" / "build it and check your own work."
- ✅ Net-new features and well-scoped enhancements where the criteria are concrete.

## When NOT to use this skill

- ❌ One-line fixes / trivial changes — the loop is overhead; just make the change.
- ❌ Greenfield spikes / throwaway prototypes — verifying code you'll delete wastes rounds.
- ❌ Specs with no acceptance criteria and none inferable — there's no gate to close. Get criteria first.
- ❌ Pure code *review* of code you didn't generate — that's [`devils-advocate`](../devils-advocate/SKILL.md) standalone.
- ❌ Open-ended design questions ("should we use Postgres or Dynamo?") — that's `design-doc` + `doc-critique`.

## Anti-patterns to avoid

- ❌ **Declaring "done" with an uncovered criterion.** The whole point is the criteria gate. A criterion without an asserting test is open, full stop.
- ❌ **A toothless review round.** Delegating to devils-advocate or sweeping the lenses, then reporting "no issues" on a real feature — the loop only earns its keep if the review actually adversarial.
- ❌ **Looping past 3 rounds.** Convergence isn't guaranteed; the cap exists so a human gets pulled in instead of the agent thrashing.
- ❌ **Wholesale regeneration each round.** Rewriting passing code to fix one gap loses verified ground. Patch the gap.
- ❌ **Calling the `devils-advocate` *skill* from here.** Skills don't invoke skills (see CLAUDE.md). Drive the *subagent* where one exists, or inline the four lenses. Same applies to any other skill.
- ❌ **Assertion theater.** Tests that run the code but assert nothing meaningful pass the round and hide the gap. The review must reject them.
- ❌ **Silent manual-verify criteria.** Criteria that can't be auto-tested must be surfaced as ⚠️ manual-verify in the report, not quietly skipped.

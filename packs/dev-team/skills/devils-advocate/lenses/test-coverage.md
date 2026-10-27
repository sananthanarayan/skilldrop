# Lens 4: Test-coverage gap analysis

The question this lens asks: **for the code paths just introduced, which scenarios have no test?**

This is not about hitting a coverage percentage. It's about which *new* branches, error paths, and edge cases ship with no automated check that future changes don't regress them.

---

## Scope rule

- Test the **new code paths only.** Don't demand tests for previously-untested neighbouring code.
- Test the **error and edge branches**, not just the happy path. The happy path is usually the one already tested.
- Test the **boundaries**, not the interior. (Empty list and one-item list catch more than 5-item list.)

## How to read the change

1. **Identify the new branches.** Every `if`, `switch`, `try`, `?.`, default param, conditional return introduced in the diff is a branch. Each one is a coverage candidate.
2. **Identify the new error paths.** Every `throw`, `return Err(…)`, `panic`, every `catch` block. Each is a candidate.
3. **Identify the new public surface.** New function exported, new endpoint, new event handler, new CLI flag. Each public entry point needs at least one test from outside.
4. **Identify the new integration points.** New external API call, new DB query, new file I/O. Each needs either an integration test or a mocked unit test with realistic responses (including failure responses).

## What to flag as a missing test

For each missed scenario, write a finding like:

> **Missing test:** `applyDiscount(null)` — assert returns 0 (or skips) without throwing.
> **Suggested location:** `src/checkout/__tests__/applyDiscount.test.ts` (same dir pattern as siblings).
> **Severity:** 🟧 major — null input is reachable from the public endpoint (`api/checkout.ts:47`).

### Default checklist of "must-have" scenarios

For every new function with parameters:

- **Happy path** — at least one test exists. (Usually it does. If not, that's a blocker.)
- **Empty input** — empty string, empty list, empty object, null, undefined.
- **Boundary** — min, max, off-by-one.
- **Error path** — explicit error / exception cases, each.

For every new endpoint:

- 200 happy path.
- 4xx for missing required field.
- 4xx for invalid auth (if endpoint requires auth).
- 4xx for valid auth + wrong user (authorization).
- 5xx response shape if downstream fails (or graceful degradation, whichever the design specifies).

For every new async handler / queue consumer:

- Successful processing of a valid message.
- Idempotency — same message processed twice produces same outcome.
- Malformed message — DLQ'd, not retried infinitely.

For every new migration:

- Forward migration applied on a non-empty seed DB.
- Backward migration restores schema (if reversible).
- Behaviour against *both* old and new app code if doing a multi-stage migration.

For every new state-machine transition:

- The valid transition itself.
- The invalid-transition rejection (state A → state Z when not allowed).

For every new UI component:

- Renders with realistic props.
- Renders with empty data.
- Renders with error state.
- Renders with loading state.
- (Interaction tests where the component has interactive behaviour.)

## What to flag as a test SMELL (not missing — wrong)

- **Asserts nothing.** Calls the function but doesn't check the return value or side effect.
- **Mocks itself out of the test.** All collaborators mocked including the unit under test, or the mock makes the test pass trivially.
- **Tautological assertion.** `expect(x).toEqual(x)` — happens when an agent fabricates a test.
- **Asserts the implementation, not the behaviour.** Test reads private fields or counts internal calls; brittle to refactor.
- **Hard-codes a date that will fail in the future.** `expect(date).toEqual('2025-12-31')` baked into a test that runs every day.
- **Flaky due to timing / ordering.** `setTimeout(…, 0)` to "let the event loop settle" — works locally, flakes in CI.
- **Snapshot test on a noisy structure.** Snapshot includes timestamps, random IDs, or auto-generated keys — fails on every run.

Flag a smelly test the same way you flag a missing one — note that the test exists but doesn't earn its keep, and suggest what it should actually assert.

## What this lens is NOT for

- ❌ Demanding tests for refactor-only changes that didn't add new behaviour.
- ❌ Demanding tests in code that already lacks them (out of scope — only the diff).
- ❌ Requiring 100% line coverage. Branches and edges matter; uncovered straightforward lines don't.
- ❌ Insisting on a specific test framework / style.
- ❌ Generating tests yourself. This lens *flags gaps* — the user (or the next agent in the loop) writes the tests, possibly by feeding the gap list back into a code-gen step.

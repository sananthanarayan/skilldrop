# Lens 3: Adversarial — what would a staff engineer push back on?

The question this lens asks: **if a senior engineer who didn't write this code reviewed it cold, what would they object to — even if it works today?**

This is the lens for the things that don't fail tests but fail in practice. Concurrency, error handling, security, observability, blast radius.

---

## Concurrency & ordering

- **Read-modify-write without a lock or compare-and-swap.** Two callers, both read X, both increment, both write — one update is lost.
- **Critical section that spans an `await` / I/O.** Lock not held across the await, or lock held *during* a slow I/O call (blocks everyone else).
- **Shared mutable state in a request-handler scope** (e.g. a module-level dict that handlers mutate).
- **Ordering assumption between async operations** with no explicit synchronization. "It works in my testing" because the race window is small.
- **Cancellation not propagated.** Context cancelled but downstream call still runs to completion, holding resources.
- **Goroutine / task leak.** Spawned, never awaited, never cancelled.

## Error handling

- **Caught and swallowed.** `try { … } catch {}` with no log, no rethrow. Errors disappear into the void.
- **Logged and continued** when the operation should have failed. The user sees success; the system did nothing.
- **Generic catch hiding specific errors.** Catching `Exception` / `error` when only one specific case is recoverable.
- **Error message leaks internals** to the user (stack trace, SQL, file paths).
- **Wrong abstraction in the error.** Internal `RecordNotFound` surfaces as 500 instead of 404. Or vice versa.
- **No distinction between retriable and terminal errors.** Caller can't tell whether to back off and retry, or to give up.
- **Cleanup not in `finally`.** Resource leaked when an exception fires partway through.

## Security

- **Input concatenated into SQL / shell / URL** instead of parameterized. Even if the input "shouldn't be untrusted."
- **Authorization check missing or in the wrong layer.** Authn ≠ Authz. A logged-in user accessing another user's resource by changing an ID.
- **Insecure direct object reference.** IDs in URLs / payloads accepted at face value with no ownership check.
- **Secrets in code, in config, in logs.** Including ones that look "innocent" — internal hostnames, employee names.
- **TLS verification disabled** (`rejectUnauthorized: false`, `verify=False`) — usually a copy-paste from a debug session.
- **Cryptographic primitives used wrong.** MD5/SHA1 for password hashing, ECB mode, IV reused, randomness from a non-CSPRNG.
- **Open redirect.** User-controlled URL passed to a redirect with no allowlist.
- **No CSRF protection** on a state-changing endpoint, in a session-cookie-auth app.
- **Logging PII / secrets.** Email, name, token, API key, full request body in an info-level log.

## Observability

- **Load-bearing path with no log.** When this fails in prod, nothing in the logs will explain why.
- **Log without correlation.** No request ID, no trace ID, no tenant ID — can't tie events together.
- **Wrong log level.** Recoverable error at `error` (alerts), or unrecoverable at `info` (lost in noise).
- **No metric on the new operation.** Latency, count, error rate. If you can't measure it, you can't run it.
- **Span / trace doesn't cover the new code.** Distributed tracing has a hole.
- **Alert without a runbook entry.** When this fires, the on-caller has no documented response.

## Blast radius

- **Change touches a shared utility** without considering all callers.
- **Migration / change applies to all rows / tenants** when it should be gated by feature flag.
- **No feature flag** when the change is risky and a rollback would otherwise require a redeploy.
- **Big bang deploy** of a multi-system change instead of staged.
- **Backwards-incompatible event / API change** with no consumer coordination.

## Build, dependency, and supply chain

- **New dependency added.** Is it maintained? License compatible? Subdependency tree audited? Pinned to a major version?
- **Pinned to a vulnerable version** of an existing dependency.
- **`postinstall` script** in a new dependency that runs arbitrary code.
- **`curl | bash` install steps** in a Dockerfile or CI config.

## Test smells

- **Test that doesn't actually assert.** Calls the function and checks nothing.
- **Test that mocks the thing under test.** Mocks itself out of any real verification.
- **Test that's coupled to the implementation** rather than the behaviour — fragile and slows down refactoring.
- **Test that's flaky** — passes locally, fails in CI 1 in 10 runs. Disable + ticket, don't ignore.
- **Test data with hard-coded "today"** — fails on a specific future date.

## Naming, comments, and structure

- **Name that lies.** `getUser` that also creates one if missing. `parse` that also mutates the input. `validate` that also sanitizes.
- **Comment that explains what the code does** (the code already does that) instead of *why*.
- **Comment that's now wrong** because the code changed but the comment didn't.
- **Dead code committed.** `// TODO: remove this` from 2022.
- **Function that's doing two unrelated things** stitched together by a flag parameter.

## Reconsider-approach signals

When you see *several* of these together, the verdict isn't "fix these findings" — it's `RECONSIDER APPROACH`:

- Reimplementing a primitive the framework / language provides (custom retry, custom cache, custom thread pool).
- Manual concurrency primitives where a higher-level abstraction exists (raw goroutines + channels when the language has `errgroup`; `setTimeout` polling when a proper queue would do).
- Several `if (env === 'X')` branches in business logic.
- Rolling your own auth / crypto / parsing for a well-known format.
- Code that essentially re-implements what a vendor library already does.

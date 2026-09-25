# Lens 1: Edge cases the first pass missed

The question this lens asks: **what inputs, states, or timings break this code?**

Apply the relevant subsection based on what the change is. Don't enumerate every check — pick the ones that *match the change shape* and have a real chance of biting.

---

## Universal (always check)

- **Null / undefined / missing.** For each parameter and field accessed: what happens when it's missing, null, undefined, `None`, `nil`, empty string, empty array, empty object, zero, `NaN`?
- **Boundary values.** Min, max, min−1, max+1, 0, −1, exactly-the-limit. For collections: empty, one, max-size, max-size+1.
- **Type confusion.** Number as string, string as number, ISO date as Unix timestamp, array as object. If the language is dynamically typed, this matters more.
- **Encoding.** Unicode (emoji, RTL, combining chars), URL-encoded vs decoded, base64, escaped vs raw, BOM in input files, mixed line endings.
- **Locale.** Comma vs period for decimals, timezone-naive dates, day-of-week assumptions, ordering by locale-aware sort.
- **Concurrency.** Two calls at once, the same call twice (idempotency), read-modify-write without a lock, optimistic locking ignored.
- **Time.** DST transitions, leap seconds (rare), clock skew, monotonic vs wall clock, "now()" called twice in same operation giving different values, expiry that crosses a boundary.
- **Partial failure.** What if the first half of the operation succeeds and the second fails? Where's the rollback / retry / dead-letter?

## HTTP / RPC endpoint

- **Auth.** Missing token, expired token, valid-but-wrong-user token, malformed header, token for a different tenant.
- **Authorization.** User authenticated but not authorized (different question from "logged in").
- **Input validation.** Body too large, body empty, body with extra fields, missing required field, wrong content-type, malformed JSON, deeply nested JSON, JSON with `__proto__` / prototype pollution.
- **Method / route.** What if called with GET when POST expected? Trailing slash. Path traversal in path params.
- **Concurrency.** Same user makes 10 identical requests in parallel.
- **Idempotency.** If this can be retried by a client or proxy, is the second call safe?
- **Rate-limit / DoS.** Unbounded loop on user input, unbounded recursion, unbounded resource allocation tied to a request param.

## Async handler / queue consumer

- **At-least-once semantics.** Same message twice. Is the operation idempotent on a key?
- **Out-of-order delivery.** Message B arrives before message A. Does logic still hold?
- **Poison messages.** Malformed payload that throws inside the handler — does the system DLQ it or retry forever?
- **Retry storms.** Failure causes immediate retry causes cascading retries causes thundering herd.
- **Backpressure.** Slow downstream. Queue grows unbounded. Does the handler shed load?

## Database / migration

- **Locking.** `ALTER TABLE` on a large table without `CONCURRENTLY` (Postgres) or equivalent — locks reads/writes during deploy.
- **Backfill.** `ADD COLUMN NOT NULL` without a default on an existing populated table — fails or locks.
- **Rollback.** Is the migration reversible? If not, is that explicit and documented?
- **Online-safety.** Will old app code break against the new schema during the rolling deploy? (Add column → backfill → switch reads → drop old column — multi-step migrations.)
- **Index creation.** Without `CONCURRENTLY` — locks writes.
- **FK constraints added after data exists.** Will scan the whole table.

## Parser / data transformation

- **Huge inputs.** 1GB file, 1M-row CSV, deeply nested JSON, malicious zip (zip bomb).
- **Malformed inputs.** Truncated, corrupted, wrong encoding, mixed encodings within one file.
- **Untrusted inputs.** Input is from a user — what if it's hostile? Path traversal, command injection, format-string attacks.
- **Streaming vs batch.** Does the code load everything into memory? Should it stream?
- **Numeric precision.** Float arithmetic on money, large integers in JSON (JavaScript loses precision past 2^53), trailing zeros stripped.

## State machine / workflow

- **Impossible transitions.** Can the state graph reach state X from state Y in a single hop? Should it? What if it does?
- **Concurrent updates to the same entity.** Two callers move it from A → B and A → C simultaneously.
- **Skipped intermediate states.** Cleanup hooks that depend on visiting state Z get skipped.
- **Terminal states.** Once in `cancelled` / `failed`, can the entity be re-opened? Should it?
- **Replay.** What happens if the workflow is re-triggered from the beginning?

## UI component

- **Loading state.** Is there one, and does it appear before the data?
- **Empty state.** Zero items — does the UI break or show something useful?
- **Error state.** API call fails — does the user see a message or a blank page?
- **Slow state.** API takes 8 seconds — does the UI lock up, or stay responsive?
- **Long content.** Names with 80 characters, descriptions with 5,000. Does layout break?
- **Internationalization.** RTL languages flipping the layout, longer translations overflowing buttons.
- **Accessibility.** Keyboard nav, screen reader labels, focus traps, contrast.
- **Mobile / small viewport.** Below 320px wide.

## Background job / cron

- **Overlap.** Job takes longer than its interval — does it overlap with the next run?
- **Missed runs.** System down at scheduled time — does the next run catch up, or skip?
- **Partial completion.** Crash halfway through — is the next run idempotent?
- **Time zone.** "Run at midnight" — whose midnight?
- **Drift.** Long-running periodic that takes longer over time as data grows.

## CLI tool / script

- **Missing args.** Required flag not passed.
- **Stdin not a TTY** (running in CI, piped from another command).
- **Env var missing or empty string.**
- **Partial run interrupted by Ctrl-C.** Is the file half-written? Is there a cleanup?
- **Non-zero exit codes** for each error path (CI scripts depend on these).

## Library / pure function

- **API stability.** Public surface change — does it break callers?
- **Default values.** Sensible? Or surprising?
- **Side effects.** Pure function actually pure? Or does it mutate inputs / hit the network / read the clock?
- **Thread safety.** If callable from multiple threads, is shared state protected?

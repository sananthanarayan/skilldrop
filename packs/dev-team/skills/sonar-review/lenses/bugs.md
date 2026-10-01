# Lens 1 — Bugs

Sonar's **Bug** category is code that is **demonstrably broken or will break**: null dereferences, off-by-one, dead branches, resource leaks, race-shaped APIs, contracts that don't hold. Bugs are the highest-signal lens — every bug is, by Sonar's definition, a defect waiting to ship.

## What you're looking at

Pull the issues list, filter to `type=BUG`, then filter further to the changed-files set. Common bug rules to recognize on sight:

| Rule family | Example IDs | What it catches |
|---|---|---|
| Null dereference | `javascript:S2259`, `java:S2259`, `python:S5713`, `csharpsquid:S2259` | `x.foo` where `x` can be null/None |
| Off-by-one / loop bound | `S2440`, `S2189`, `S2583` | `<=` vs `<`, infinite loops, dead branches |
| Resource leak | `S2095`, `S2093` | unclosed streams, files, DB connections |
| Exception handling | `S2737`, `S108`, `S1166` | empty catch, swallowed throwables, `throw` lost in finally |
| Equality / comparison | `S2159`, `S1698`, `S3403` | `==` on incompatible types, `equals` vs `==` |
| Floating-point comparison | `S1244` | `if (x == 0.1)` |
| Date / time | `S3725`, `S6353` | wrong timezone, deprecated `Date` mutation |
| Promise / async (JS/TS) | `S4123`, `S6544` | unawaited promises, missing error handlers |
| Mutable shared state | `S2386`, `S3008` | non-final static, mutable singletons |

If the rule isn't in this list, look it up at `${SONAR_HOST_URL}/coding_rules?open=<rule-id>` — Sonar links every issue to its catalog page with examples.

## How to phrase each finding

Four parts, same as the report skeleton:

1. **Where** — `file:line` + a 5–15 char quote of the offending code.
2. **Rule + category** — `[BUG · javascript:S2259] Null dereference` — keep the rule ID literal.
3. **Why it matters** — name the **runtime scenario**, not the rule. ✅ "When `req.body.discount` is omitted from the request, `discount.amount` throws `TypeError: Cannot read properties of undefined` — the endpoint 500s." ❌ "Possible null dereference."
4. **Fix** — concrete. Either:
   - **Paste-able patch** — a one-line guard, a `??`, an `if (x == null) return`, a `try/finally`. Quote the line numbers.
   - **Pattern reference** — "Use the `withConnection` helper from `db.ts:14` instead of opening directly; it handles the `finally` close."

## Calibration

- **BLOCKER bug** ≈ ships a defect on the happy path or a security-shaped fault (e.g. unsanitized `eval`, SQL string concat). Treat as merge-blocking.
- **CRITICAL bug** ≈ defect on a common error path (null on optional field, leak on retry). Fix before merge.
- **MAJOR bug** ≈ defect on an uncommon path (rare race, edge encoding). Fix or file a follow-up issue.
- **MINOR bug** is rare for the Bug category — usually means Sonar isn't sure. Verify before reporting.

Trust Sonar's severity here; the Bug catalog is the most-calibrated of the five lenses.

## Anti-patterns when reporting Bugs

- ❌ Restating the rule name as the "why". The rule name is in the catalog — your job is the *scenario* in this codebase.
- ❌ Fixing the symptom not the cause. ❌ "Wrap in try/catch and log." ✅ "The caller passes `null` from `getDiscount` when no promo applies — change `getDiscount` to return `{amount: 0}` instead of null, then this site needs no guard."
- ❌ Down-grading a BLOCKER because it "looks fine to you". The bug catalog is mechanical — if Sonar caught a null deref, there's a path to it. Find the path or trust the rule.
- ❌ Recommending `// NOSONAR` as the fix. Reserve that for documented exceptions; it's never the right answer for a Bug.

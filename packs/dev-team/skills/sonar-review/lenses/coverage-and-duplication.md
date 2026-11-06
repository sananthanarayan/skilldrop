# Lens 5 — Coverage + Duplication

These aren't "issues" in Sonar's data model — they're **quality-gate conditions** measured against the project's new code. They're reported in the gate's `conditions` array, not the issues list. They're often what fails an otherwise-clean gate.

## Coverage on new code

Sonar measures *lines and branches added or modified in this branch*. A file that wasn't touched contributes nothing to the new-code coverage metric; touching it forces the touched lines into the measurement.

**Default gate condition:** ≥ 80% coverage on new code.

### What to report

Fetch the gate JSON, find conditions where `metricKey=new_coverage` and `status=ERROR`. Then drill into:

```bash
curl -s -u "$SONAR_TOKEN:" \
  "$SONAR_HOST_URL/api/measures/component_tree?component=$PROJECT_KEY&branch=$BRANCH&metricKeys=new_uncovered_lines,new_lines_to_cover&qualifiers=FIL"
```

Identify the files dragging the percentage down. Report:

> ❌ **Coverage on new code: 71%** (gate requires ≥ 80%)
> - `src/jobs/export.ts` — 47/82 new lines covered (57%). Uncovered: error paths at lines 55–62 and 71–78.
> - `src/api/checkout.ts` — 31/40 new lines covered (78%). Uncovered: the new `null discount` branch at line 47.
>
> **Fix:** Add three tests covering the error paths in `export.ts` and the null-discount branch in `checkout.ts`. The happy path is already covered.

### Naming the missing tests

Don't say "add tests" — name them. ✅ "Add a test `it('returns empty when upstream API 500s', ...)` covering `export.ts:55–62`." ❌ "Improve test coverage."

If you can't name the missing test scenario, the coverage finding isn't actionable — you don't understand the uncovered branch well enough to flag it as a finding. Drop it and let the gate fail until the user adds the case themselves.

### When coverage looks worse than it is

- **Tests in changed dirs not running.** The coverage tool ran but didn't include the new tests. Symptom: 0% on a file that clearly has tests beside it. Check `sonar.tests` and the coverage report path in `sonar-project.properties`.
- **Coverage exclusions stripped the wrong files.** Symptom: clearly-covered file shows uncovered. Check `sonar.coverage.exclusions`.
- **Generated files counted.** Symptom: lots of "uncovered" in `__generated__` or `dist/`. Add to `sonar.exclusions`.

If you suspect a config issue, **say so explicitly** rather than reporting the bad number as fact: "Coverage shows 0% on `src/payments/`, but `payments.test.ts` exists at the same level — the coverage importer may not be picking up the report. Check `sonar.javascript.lcov.reportPaths` in `sonar-project.properties`."

## Duplication

**Default gate condition:** ≤ 3% duplicated lines on new code.

Duplication catches copy-paste — a block of ≥ 100 tokens (≈ 10 lines for most languages) that appears more than once. The catalog rule is `common-{language}:DuplicatedBlocks`.

### What to report

For each duplication block on changed code:

> 🟨 **Duplication: `src/api/checkout.ts:47–78` duplicates `src/api/refund.ts:32–63`** (32 lines, 89% match).
>
> The discount-application logic is now copied across both endpoints — the next change to discount handling has to be made twice. Extract `applyDiscount` into `src/lib/discounts.ts` and call it from both.

If duplication is *within* the same file, treat it as a single-file refactor — extract a helper at the file top.

If duplication is *between* a new file and an existing one, the fix usually means modifying the existing file too. Flag this explicitly — the user may have been told not to touch the other file. Suggest the extraction location, then let them decide.

### When duplication is intentional

Sometimes duplication is correct — test fixtures, parallel implementations across services, migration scripts that intentionally mirror old code. If you can see this is the case (e.g. the duplicated code is in `tests/` or named `migrate_*`), say so:

> 🟨 **Duplication: `tests/checkout.test.ts:47–78` duplicates `tests/refund.test.ts:32–63`**.
>
> The two tests share setup. This is the common-fixture case — extract `setupTestOrder()` into `tests/_helpers.ts`. Not a quality-gate blocker (tests are excluded by default in `sonar.coverage.exclusions` but counted for duplication unless excluded explicitly).

## Anti-patterns when reporting Coverage / Duplication

- ❌ **Reporting the percentage without the files dragging it.** "Coverage is 71%" isn't actionable. Name the under-covered files and the uncovered branches.
- ❌ **Demanding 100% coverage** on the new code. The gate asks for 80% (or whatever the project sets); 100% is rarely worth the test brittleness.
- ❌ **Demanding tests for log statements / pass-through error paths.** Coverage of a `console.log(...)` line teaches nothing. Suggest the *meaningful* missing scenarios.
- ❌ **Treating duplication in tests as urgent.** Test fixtures often repeat; the refactor is "nice to have", not gate-blocking, and Sonar agrees if `sonar.cpd.exclusions` is set on `**/*.test.*`.
- ❌ **Telling the user to disable the gate condition.** The fix is more tests or a small refactor, not weakening the gate. If 80% is structurally impossible for this project, raise it as a separate gate-tuning conversation, not a per-PR finding.

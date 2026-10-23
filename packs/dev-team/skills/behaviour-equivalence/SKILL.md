---
name: behaviour-equivalence
description: Prove that a rewritten, migrated or refactored component behaves the same as the old one with a golden-master comparison — record inputs and outputs at a boundary (HTTP, function calls, batch files, DB writes, events) from production-shaped traffic and edge cases, run the old system twice to find its nondeterminism, normalise narrowly field by field, replay against the new one, triage every difference as defect, intended change (with a named approver) or missing normalisation, and give a verdict of EQUIVALENT, EQUIVALENT EXCEPT LISTED CHANGES, NOT EQUIVALENT or NOT PROVEN. Use when the user asks "does the new one behave the same as the old one", "can we sign off the rewrite", "are these diffs just noise", wants a golden-master, approval or shadow-traffic comparison, a parity check between old and new outputs, or says "prove behaviour equivalence".
---

# behaviour-equivalence

Proves, or fails to prove, that a new implementation does what the old one did, at a boundary
both share. The old system is the specification, bugs included. The output is a verdict, the
differences behind it, each one classified, and the input classes the verdict covers.

Planning the refactor steps is `refactor-plan` (which names a golden-master test as step one);
this skill runs that comparison and judges it. Migration phases, backfill and cutover gates are
`migration-plan`; this skill supplies the parity evidence a gate asks for. A test plan for new
behaviour is `test-plan-generator`. Finding where the old code lives is `codebase-tour`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** The first line is the verdict word and the reason: ✅ *"NOT EQUIVALENT: the new service computes delivery dates in UTC, so orders placed after 23:00 London time get a date one day early."* — ❌ a table of match counts, or "mostly the same".
- **Use only what you were given.** No invented cases, traffic volumes, approvers, dates or root causes. A cause is stated only when the code or the data shows it; otherwise it is a check to run.
- **Deliver from what you have.** With recordings, compare them and give the verdict. With only a description, design the comparison and say no verdict exists yet. Ask only when there is no component to compare at all.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder. A next step is one plain sentence describing the work.
- **For this skill:** every difference is classified before a verdict is given, and a normalisation rule that hides a difference the old system never showed against itself is a defect being hidden, not noise.

1. **Fix the boundary and everything that crosses it.** Name the old and new component and the
   seam both answer at: an HTTP endpoint, a function, a batch job's files, a queue consumer.
   Output is everything a caller or downstream system can observe, not only the return value:
   status codes, error bodies and exception types, headers clients read, rows written, events
   emitted, files produced (reject and error files too), exit codes. ✅ *"Record `status`, `body`, and the rows written to
   `invoice_lines`."* — ❌ *"compare the JSON responses"* when the job also writes a ledger.

2. **Record production-shaped inputs, then the edge classes, and say which classes exist.**
   Replay or sample real traffic (scrubbed) first; then add one case per edge class that
   applies: empty, one, max size, nulls and missing fields, unicode and long strings, each error
   path, time zones and DST changes, midnight and month end, leap day, rounding boundaries (a
   value that lands on exactly .5 of the smallest unit), every currency or locale in use. Write
   a coverage line per class: *recorded* (case ids), or *not recorded*. **Equivalence is proven
   only for the recorded classes**, and the reply says which ones are missing.

3. **Run the old system twice on the same inputs before comparing with the new one.** Every
   field that differs between the two old runs is nondeterminism: those fields, and only those,
   are normalisation candidates. A field that is stable old-vs-old and differs old-vs-new is a
   behaviour difference until shown otherwise. When no second run exists, each rule is tagged
   `[assumption]` and "run the old system twice" is the first thing to confirm.

4. **Normalise explicitly and narrowly: one field, one rule, one reason.** Rules go in a JSON
   file (format in [`reference.md`](reference.md), starter in
   [`templates/rules.json`](templates/rules.json)).
   - ✅ `body.issued_at` ignore, "wall-clock time of the call" — ❌ ignore `body` because it differs.
   - ✅ `body.invoice_id` regex `^INV-[0-9]{6}$` → `INV-<id>` — keeps the format check; ❌ ignore the id.
   - ✅ sort `body.items` by `line_no`, "built from a hash map; no consumer reads the order" — ❌ sort a list whose order a caller shows to a user.
   - ✅ float tolerance per field with the reason it exists: `fx_rate` abs 1e-9, "double printed by a different library".
   - ❌ **Never a tolerance or rounding rule on money.** Money is compared exactly, in minor units. A 1-cent tolerance on `tax_cents` is how a rounding-mode change ships.
   - Whitespace, case, locale and key order are normalised only where the consumer ignores them too.
   Every rule must leave the old-vs-old comparison EQUIVALENT and must have hit something.
   **A rules file the user supplies is audited, not trusted:** check each rule's field against
   the old-vs-old run, drop the ones on fields that never varied, rerun, and report what the
   dropped rules were hiding. "With our rules the diff is clean" is the claim being tested.

5. **Replay against the new system and diff with the script.** Same inputs, same frozen clock
   and seeds where the system accepts them. Run old-vs-old first, then old-vs-new, with the same rules:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/golden_diff.py" old_run1.jsonl old_run2.jsonl --rules rules.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/golden_diff.py" old.jsonl new.jsonl --rules rules.json --accepted accepted.json
   # Other IDEs (from the skill folder)
   python3 scripts/golden_diff.py old.jsonl new.jsonl --rules rules.json --json -o diff.json
   ```

   Either side is a JSONL file keyed by `case_id` or a directory with one file per case. Exit 0
   is equivalent after rules, 1 not, 2 bad input. Read its warnings: a rule that matched
   nothing, a rule with no reason, an ignore over a whole object, a tolerance on a money-like
   field, and how many differences each tolerance absorbed. With no script, compare by hand
   and show each difference with its case and path.

6. **Triage every remaining difference into exactly one class.** Work from the per-field
   summary, then open the cases:
   - **Defect:** the new system is wrong, or changed something nobody asked for. Name the cause
     when the code shows it (✅ *"`tax.go:LineTax` uses `math.RoundToEven`; the old
     `TaxCalc.java` rounds `HALF_UP`"*).
   - **Intended change:** listed, with the cases it affects and a **named approver** from the
     input. No approver in the input means "approver: none named" and it counts as unresolved.
   - **Missing normalisation:** only if the field also varies old-vs-old. Add the rule, rerun.
   Look for what the differing cases share: all on a .5 boundary (rounding mode), all near
   midnight (time zone), all non-ASCII (encoding, collation), all equal sort keys (unstable
   sort). Catalogue in [`reference.md`](reference.md).

7. **Give the verdict by the first row that applies:**

   | Verdict | When |
   |---|---|
   | NOT EQUIVALENT | any defect, any unclassified difference, or a case missing on one side |
   | NOT PROVEN | no defect, but an edge class or error path production sends was not recorded, side effects were not compared, or the rules were never checked old-vs-old |
   | EQUIVALENT EXCEPT LISTED CHANGES | every difference is an intended change with a named approver |
   | EQUIVALENT | no differences after rules that each have a reason and a hit |

   "Mostly the same" and match percentages are not verdicts: 190 of 200 matching is NOT EQUIVALENT until the 10 are classified.

8. **Reply chat-sized.** Verdict line; the differences, one line each: class, field, cases,
   old → new, cause or the check that finds it; the rules, one line each, only when designed or
   changed here; one line on what the verdict covers and what it doesn't; at most three items
   under "To confirm". Write files (rules, accepted changes, a report) only where the user asked.
   With no recordings yet: the boundary, what to record, the edge classes, the starting rules,
   and how the verdict will be decided, as a short numbered plan.

**Non-interactive runs** (subagent, CI, headless): with no component, boundary or recordings
named at all, emit `BLOCKED: need the old and new component and the boundary to compare`.
Everything else degrades to `[assumption]`: a missing second old run makes every rule an
assumption, a missing approver leaves the change unresolved, and a missing coverage list makes
the verdict NOT PROVEN at best.

## Useful references in this skill

- [`reference.md`](reference.md) — what to record per boundary, the normalisation catalogue, the rules-file format, the difference patterns and their usual causes
- [`templates/rules.json`](templates/rules.json) — starter rules file; [`templates/accepted.json`](templates/accepted.json) — intended changes with approvers
- [`scripts/golden_diff.py`](scripts/golden_diff.py) — case-by-case diff after rules, per-field summary, rule warnings (stdlib only)
- [`examples/delivery-date.md`](examples/delivery-date.md) — worked example: a delivery-date endpoint rewrite with a time-zone defect hidden among timestamp and ID noise

## Quality bar

- **The first line is one of the four verdicts** with the reason in plain words.
- **Every difference is classified** as defect, intended change or missing normalisation; none is left as "minor".
- **Every normalisation rule names one field and a reason,** and the field varied old-vs-old.
- **Money is compared exactly in minor units;** any float tolerance is per field with a reason.
- **Error behaviour and side effects are compared,** not only return values.
- **Coverage is stated by input class,** and the verdict covers only the recorded classes.
- **Intended changes name an approver from the input,** or stay unresolved.
- **Every case id, value, count and cause is from the input or the script output.**

## When to use this skill

- ✅ Signing off a rewrite, port or language migration of a component against the old one
- ✅ Judging a golden-master or shadow-traffic diff: "are these differences just noise?"
- ✅ Designing what to record and how to compare before a cutover
- ✅ Reviewing a normalisation rules file that someone says makes the diff clean

## When NOT to use this skill

- ❌ Planning the refactor or rewrite steps themselves — `refactor-plan`
- ❌ Phasing a data or platform migration, backfill and cutover — `migration-plan`
- ❌ A test plan for a new feature or changed behaviour — `test-plan-generator`
- ❌ Getting oriented in the old codebase before starting — `codebase-tour`

## Anti-patterns to avoid

- ❌ **"Matches apart from noise"** with the noise never listed or checked against an old-vs-old run.
- ❌ **Ignoring the whole field because it differs.** That deletes the comparison instead of normalising it.
- ❌ **A tolerance on money.** One cent absorbed per invoice is a rounding-mode change: what customers pay and the tax reported both move.
- ❌ **Happy paths only.** No empty basket, no unknown id, no midnight order: the verdict is NOT PROVEN, not EQUIVALENT.
- ❌ **Return values only.** The new service answers the same and stops writing the audit row.
- ❌ **Calling a difference an intended change** because the new behaviour looks better, with nobody named who approved it.
- ❌ **A percentage as the verdict.** 85% matching says nothing about the other 15%.

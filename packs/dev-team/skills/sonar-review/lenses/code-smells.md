# Lens 4 — Code Smells

The **maintainability** lens. Code smells aren't bugs or security issues — they're patterns Sonar predicts will slow future change. The catalog is large and noisy; this lens is where over-reporting hurts the report most.

## What you're looking at

Filter issues to `type=CODE_SMELL` and changed files. Common families on new code:

| Family | Example IDs | Worth reporting on changed code? |
|---|---|---|
| Cognitive complexity | `S3776` | ✅ Yes — predictive of bugs |
| Function / method length | `S138`, `S104` | ✅ Yes — but often a refactor target, not a one-line fix |
| Parameter count | `S107` | ✅ Yes |
| Duplicated string literals | `S1192` | 🟨 Maybe — only if literal is meaningful (URL, key) |
| Magic numbers | `S109` | 🟨 Maybe — extract a constant if used > 2 places |
| Unused imports / variables | `S1481`, `S1128` | ✅ Yes — trivial fix |
| Empty methods / classes | `S1186`, `S1186` | ✅ Yes |
| TODO / FIXME comments | `S1135` | ⚪ Info — surface in count, don't list each |
| Naming conventions | `S100`, `S116` | 🟨 Only flag if the new identifier breaks the project's pattern |
| `console.log` / `print` | `S2228`, `S1854` | ✅ Yes if not behind a logger |
| Deprecated API use | `S1874` | ✅ Yes |
| Commented-out code | `S125` | 🟨 Maybe — sometimes intentional (TODO + commented call) |

The principle: **report what's actionable in this PR, summarize what isn't**. A finding the user can fix in five minutes is worth a line; a refactor finding that requires opening four files is worth one line in summary form.

## How to phrase each finding

Standard four parts:

1. **Where** — `file:line` + a quote.
2. **Rule + category** — `[SMELL · typescript:S3776] Cognitive complexity 22 > 15`.
3. **Why it matters** — the *future-maintenance* cost, in concrete terms. ✅ "`processOrder` has six nested conditionals; the next person debugging a refund flow has to trace all six to know which branch they're in." ❌ "Code is too complex."
4. **Fix** — concrete:
   - Complexity → extract one of the conditional branches into a named function. Suggest the name.
   - Long parameter list → struct/object parameter. Name the fields.
   - Magic number → name the constant. Suggest the name and the scope (file-level vs class-level).
   - Duplicated literal → suggest the constant name + the line numbers that should reference it.

## Calibration

Sonar's severity on code smells is **less reliable** than on bugs/vulns — the same `S3776` is CRITICAL when complexity is 30 and MAJOR when it's 16. Trust the severity, but don't expect every CRITICAL smell to actually block merge.

| Severity | Treat as |
|---|---|
| 🟥 BLOCKER | Rare for smells; usually means complexity is extreme (>25). Treat as merge-blocker. |
| 🟧 CRITICAL | High-cost smell on load-bearing code. Fix before merge. |
| 🟨 MAJOR | Most common smell severity. Fix if cheap; defer if the refactor is large. |
| ⚪ MINOR | Style + naming. Roll up into a count if there are > 5. |

## Aggregation rule

If the new code has more than **8 minor code smells of the same rule** (e.g. 12 magic numbers in one file), don't list each — emit one rolled-up finding:

> 🟨 **`typescript:S1192` — String literal duplication × 12** in `src/api/orders.ts`. The literal `"USD"` appears 12 times across `createOrder`, `applyDiscount`, and `formatTotal`. Extract `const CURRENCY = "USD"` at the top of the file and reference it from each site.

Don't bury single-instance findings in rollups — only roll up repeats of the same rule in the same area.

## Anti-patterns when reporting Code Smells

- ❌ **Listing every smell**. The report becomes unreadable. Prioritize, aggregate, summarize the tail.
- ❌ **Recommending a rename as the fix for a complexity smell.** Renaming doesn't reduce complexity. Extract a function or flip a guard clause.
- ❌ **Flagging style on a PR that fixes a bug.** If the change is a targeted bug fix and the smells are pre-existing in the same function, those go in the "pre-existing issues touched" FYI section, not the main report.
- ❌ **Treating `S1192` (string duplication) as serious in tests.** Tests are *supposed* to repeat literals — that's how you read them. If Sonar flags `"alice"` appearing 8 times across tests, downgrade to nit or drop.
- ❌ **Confusing "long function" with "complex function".** A 200-line function with no branching is fine; a 30-line function with seven nested `if`s is the smell. Cite `S3776` (cognitive complexity), not `S138` (length), when complexity is the real issue.

# Sonar review: {feature / PR title}
_Scope: {N changed files, M lines added/removed} · Branch: `{branch}` · Scanned: {YYYY-MM-DD HH:MM} · Scan duration: {Ns}_
_Sonar project: [`{project-key}`]({sonar-host}/dashboard?id={project-key}&branch={branch})_

## Quality gate

**{✅ PASS / ❌ FAIL}** — {one-line reason — what failed (or "all conditions met")}

{2–3 sentence summary. Lead with what failed the gate. If PASS, say so plainly and call out the closest condition to the line.}

### Gate conditions

| Condition | Actual | Threshold | Status |
|---|---|---|---|
| New bugs | {N} | 0 | ✅ / ❌ |
| New vulnerabilities | {N} | 0 | ✅ / ❌ |
| New security hotspots reviewed | {pct}% | 100% | ✅ / ❌ |
| Coverage on new code | {pct}% | ≥ 80% | ✅ / ❌ |
| Duplicated lines on new code | {pct}% | ≤ 3% | ✅ / ❌ |

(Drop rows the project's gate doesn't enforce.)

## Findings on changed code

| Severity | Bugs | Vulnerabilities | Hotspots | Code smells |
|---|---|---|---|---|
| 🟥 Blocker | {N} | {N} | — | {N} |
| 🟧 Critical | {N} | {N} | {N} | {N} |
| 🟨 Major | {N} | {N} | {N} | {N} |
| ⚪ Minor | {N} | — | — | {N} |
| ⚪ Info | {N} | — | — | {N} |

### 1. Bugs

{For each finding:}

#### 🟥 [`javascript:S2259`] TypeError on null dereference
- **Where:** `src/api/checkout.ts:47` — `discount.amount`
- **Why it matters:** When `discount=null` reaches line 47, `applyDiscount` throws `TypeError` — the request returns a 500, not a graceful "no discount applied".
- **Fix:** Add `if (discount == null) return 0;` at the top of `applyDiscount`, matching the pattern in `applyTax` at line 102.

{If no findings: "No bugs flagged on changed code."}

### 2. Vulnerabilities
### 3. Security hotspots

{Hotspots are review-required, not auto-fix. Each one:}

#### 🟧 [`javascript:S2076`] OS command construction from user input
- **Where:** `src/jobs/export.ts:28` — `exec(\`tar -czf ${userPath}\`)`
- **Why it matters:** `userPath` flows from the export API without escaping — if an attacker controls the export name, they can inject shell metacharacters.
- **Evidence for review:** `userPath` is validated upstream in `validateExportName` (`src/api/exports.ts:14`) to match `/^[a-zA-Z0-9_-]+$/` — that *should* make injection impossible, but the validation runs in a separate process and the variable name is reused.
- **Action:** Mark **Safe** if you confirm the upstream validation is enforced on every code path that hits this exec; otherwise mark **At Risk** and switch to `execFile` with an args array.

### 4. Code smells
### 5. Coverage + duplication

#### ❌ Coverage on new code: 71% (gate requires ≥ 80%)
- **Where:** `src/jobs/export.ts` — 47/82 new lines covered; `src/api/checkout.ts` — 31/40 new lines covered.
- **Why it matters:** The two uncovered branches in `export.ts` are the error paths (lines 55–62, 71–78) — exactly where regressions hide.
- **Fix:** Add three tests — happy path is covered; add cases for (a) upstream API 500, (b) empty result set, (c) `userPath` failing validation.

## Pre-existing issues in touched files (FYI — not blocking)

{Issues that pre-date this branch but live in files you changed. For awareness; the gate doesn't enforce them.}

- ⚪ `src/api/checkout.ts:102` — [`typescript:S3776`] Cognitive complexity 18 > 15 (existing).
- ⚪ `src/api/checkout.ts:155` — [`typescript:S1192`] String literal `"USD"` duplicated 4 times (existing).

## What's solid

- {2–4 things the change got right — patterns that survived the scan cleanly. Not flattery; signal for what to preserve.}
- New `parseDiscount` helper has 100% branch coverage and no findings — keep the test shape for the rest of the payment module.

## Suggested order to address

1. **Fix anything failing the quality gate** — blockers, new vulnerabilities, coverage shortfall. The PR can't merge until these are green.
2. **Review the security hotspots** — mark each Safe / At Risk / Acknowledged in the Sonar UI. The gate counts them as unresolved until you do.
3. **Major code smells**, prioritizing files in `src/api/` and `src/jobs/` over UI / config.
4. **Minors and nits** if time permits, otherwise defer.

---

Full report: {sonar-host}/dashboard?id={project-key}&branch={branch}

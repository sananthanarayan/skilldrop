# Devil's advocate: {feature name or PR title}

_Scope: {N files, M lines changed in the diff under review}_
_Reviewed: {YYYY-MM-DD}_
_Code shape(s): {endpoint | async handler | migration | state machine | parser | CLI | UI | background job | library | config}_

## Verdict
**{SHIP IT | SHIP WITH FIXES | DO NOT MERGE | RECONSIDER APPROACH}** — {N} blocker · {N} major · {N} minor · {N} nit

{3-sentence summary. Lead with the worst finding. Name the lens(es) that surfaced the most issues. If the verdict is `RECONSIDER APPROACH`, say *why* — what's the structural problem the findings point to.}

---

## Findings by lens

### 1. 🔍 Edge cases the first pass missed

#### 🟥 Blockers
1. **Where:** `{file:line}` — *`{≤15 char quoted snippet}`*
   **What:** {one sentence — which check from the edge-cases lens fired}
   **Scenario:** {concrete reproducible case, e.g. "POST /checkout with `body = {}` → `applyDiscount(undefined)` → TypeError at line 47"}
   **Fix:** {one or two sentences, concrete and paste-able where possible}

#### 🟧 Major
1. **Where:** `{file:line}` — *`{snippet}`*
   **What:** {…}
   **Scenario:** {…}
   **Fix:** {…}

#### 🟨 Minor
1. {…}

#### ⚪ Nits
- {…}

---

### 2. 🔭 Future-proofing — assumptions baked in

#### 🟥 Blockers
1. **Where:** `{file:line}` — *`{snippet}`*
   **What:** {assumption that will break — e.g. "Hard-coded 100ms timeout"}
   **When it bites:** {realistic timeframe — e.g. "p99 latency from `payments-svc` already at 80ms; one more downstream hop and the deploy fails"}
   **Fix:** {…}

#### 🟧 Major
1. {…}

#### 🟨 Minor
1. {…}

---

### 3. ⚔️ Adversarial — what a staff engineer would push back on

#### 🟥 Blockers
1. **Where:** `{file:line}` — *`{snippet}`*
   **What:** {category — concurrency / error handling / security / observability / blast radius}
   **Scenario:** {how it actually fails — "two callers run `incrementBalance` in parallel, both read balance=100, both write balance=101 → $10 lost"}
   **Fix:** {…}

#### 🟧 Major
1. {…}

#### 🟨 Minor
1. {…}

#### ⚪ Nits
- {…}

---

### 4. 🧪 Test-coverage gaps

For each gap: scenario → suggested location → severity.

#### 🟥 Blockers
1. **Missing test:** {scenario, e.g. "POST /checkout with missing auth header — expect 401"}
   **Suggested location:** `{path/to/test/file}`
   **Why blocker:** {e.g. "auth check is the only thing between this endpoint and arbitrary user data; no test guards against future refactors removing it"}

#### 🟧 Major
1. **Missing test:** {scenario}
   **Suggested location:** `{path}`
   **Why major:** {…}

#### 🟨 Minor (additional cases worth adding)
- {one-liner per case}

#### Test smells (existing tests that don't earn their keep)
- **`{test file:line}`** — *`{snippet of the test}`* — {smell, e.g. "asserts nothing — calls `applyDiscount(10)` but doesn't check the return value"} — **Fix:** {what it should assert}

---

## ✅ What's solid

Things the implementation got right — worth preserving in any rewrite, and worth re-using as patterns elsewhere in the change.

- **{Strength 1}** — `{file:line}` — {why this is a real strength, not flattery}
- **{Strength 2}** — `{file:line}` — {…}
- **{Strength 3}** — `{file:line}` — {…}

---

## 🛠 Suggested order to address

1. **Fix blockers first.** {Specifically: {finding refs}}
2. **Add the missing tests in §4.** They double as regression catches for the fixes above.
3. **Major findings in priority order:** {finding refs, ordered by likelihood-of-biting × cost-to-fix-later}
4. **Minor + nits:** {batch into a follow-up commit or punt to a separate cleanup PR — don't gate the merge}

---

## 🚦 Re-review trigger

After fixes land, the changes most likely to *introduce new findings* are:
- {e.g. "The retry logic added to address Blocker #2 needs a fresh sweep of Lens 1 (edge cases) for retry storm + idempotency."}
- {e.g. "The new feature flag added per the 'blast radius' finding needs a Lens 2 check that the flag has an off-switch and an expiry."}

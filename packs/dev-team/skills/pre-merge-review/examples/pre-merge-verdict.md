# Worked example — a NOT READY verdict where the mechanical gate is decisive

Input → output oracle for `pre-merge-review`. Shows the un-bypassable gate: a clean-looking
review does not clear a red test run, and the verdict leads with one word plus the blocking reasons.

## Input

> "Review my branch before I open the PR — it adds a `/export` endpoint that streams a user's
> records as CSV."

The change: a new `export_handler` + one new test.

## Output

**Verdict: `NOT READY`** — the mechanical gate is RED, and the panel adds one blocker.

### Mechanical gate (`scripts/gate.py`, auto-detected)

| Command | Result |
|---|---|
| `ruff check .` | PASS |
| `mypy .` | PASS |
| `pytest -q` | **FAIL** — `test_export_empty` errors: `export_handler` raises `TypeError` on a user with zero records |

`GATE: RED — 1/3 command(s) failed.` A red gate is `NOT READY` on its own; the review below can only *add* blockers, never clear this.

### Review panel (merged, de-duped)

🟥 **blocker — missing authorization (security-reviewer).** `export_handler` reads `user_id` from the **query string** (`handler.py:12`) and returns that user's records with no check that the caller *is* that user — any authenticated user can export anyone's data (IDOR). *Fix:* derive `user_id` from the session, not the request; if an admin export is intended, gate it behind an explicit role check.

🟧 **major — unbounded response (devils-advocate).** The CSV is built in memory for the full record set (`handler.py:20`); a user with millions of rows OOMs the process. *Fix:* stream rows, or paginate/cap.

🟨 minor — **craft (code-quality):** `export_handler` mixes fetch, format, and HTTP concerns in one 60-line function (`handler.py:8-68`); extract `rows_to_csv()`. *(listed, does not block.)*

### Must-fix before merge

1. **Gate:** fix `export_handler` on the empty-records case so `pytest` is green.
2. **Blocker:** derive `user_id` from the session — close the IDOR.
3. **Major:** stream/cap the CSV to bound memory.

## Why this passes the quality bar

The gate was *run*, not assumed, and its RED result decides the verdict regardless of the review; findings are merged across the three lenses (security, correctness, craft) with no triple-reporting; the verdict is one word plus an ordered must-fix list — gate failures first, then blocker/major. A no-victim security note wasn't inflated to a blocker; the IDOR — with a concrete attacker path — was.

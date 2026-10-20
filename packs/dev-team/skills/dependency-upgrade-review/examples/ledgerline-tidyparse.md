# Worked example: Ledgerline, a Poetry patch bump that earns MERGE

Most worked examples end in a block. This one shows what it takes to close every check, so MERGE is earned rather than assumed.

## Input

The user says: *"Can I merge PR #57 on ledgerline, 'chore(deps): bump tidyparse to 2.2.2'? CI is green."* and supplies:

- the diff, [`inputs/ledgerline.diff`](inputs/ledgerline.diff) (`pyproject.toml` and `poetry.lock`)
- tidyparse's changelog for 2.2.1 and 2.2.2
- the repo: `app/ingest.py`, `tests/test_ingest.py`, `.github/workflows/ci.yml`

Changelog excerpt as supplied:

```markdown
## 2.2.2
- Security: a single line longer than 10 MB is now rejected with RowTooLongError
  (a subclass of ParseError) instead of being read into memory.

## 2.2.1
- Fixed: a quoted field containing a newline was split into two rows.
```

Repo excerpts as supplied:

```python
# app/ingest.py
12  def import_statement(path):
13      try:
14          rows = tidyparse.parse_rows(path, dialect="excel")
15      except tidyparse.ParseError as exc:
16          raise StatementRejected(str(exc)) from exc
```

```python
# tests/test_ingest.py
 3  from app.ingest import import_statement
 9  def test_quoted_newline_stays_one_row(tmp_path): ...
17  def test_malformed_file_is_rejected(tmp_path): ...
```

`.github/workflows/ci.yml` runs `pytest -q` on `pull_request`.

## Script output (real; the header, the fixed footer and the empty sections trimmed)

```bash
python3 scripts/upgrade_diff.py examples/inputs/ledgerline.diff --title "chore(deps): bump tidyparse to 2.2.2"
```

```markdown
**Floor verdict: none from the diff** (mechanical; the changelog, usage and CI checks are still to do, and only they can make it MERGE)

## Changed (3)

| Package | Ecosystem | Old → New | Class | File | Notes |
|---|---|---|---|---|---|
| `charset-sniff` | pip | 1.4.0 → 1.4.1 | patch | `poetry.lock` | lockfile only (transitive); not named in the title |
| `tidyparse` | pip | 2.2.0 → 2.2.2 | patch | `poetry.lock` | direct |
| `tidyparse` | pip | ^2.2.0 → ^2.2.2 | patch | `pyproject.toml` |  |

## Beyond the title (1)

- `charset-sniff` changed: 1.4.0 → 1.4.1 (poetry.lock)
```

No install scripts, sources, licences or pins appear. The floor says only that the diff itself raises nothing; the notes, the search and CI decide the rest.

## Review (what the agent hands back)

**MERGE.** Two patch releases; the only behaviour change, 2.2.2's new 10 MB line limit, raises an error the import code already handles, and the PR's tests run that code.

- Both releases read. 2.2.1 fixes quoted newlines splitting rows, covered by `test_quoted_newline_stays_one_row` (`tests/test_ingest.py:9`). 2.2.2 is a security fix: lines over 10 MB raise `RowTooLongError`, a subclass of `ParseError`.
- `git grep -n "tidyparse" -- '*.py'` finds one call, `app/ingest.py:14`, inside `except tidyparse.ParseError` (`app/ingest.py:15`), so the new error becomes `StatementRejected` like any malformed file.
- `ci.yml` runs `pytest -q` on the PR and `tests/test_ingest.py:3` imports `import_statement`, so the changed code ran.

Also in the lockfile: `charset-sniff` 1.4.0 → 1.4.1 (transitive patch). No new packages, install scripts, sources, runtime changes or pins.

Rollback: `git revert` the merge commit, or `poetry add tidyparse@2.2.0` and commit `pyproject.toml` and `poetry.lock`; that reopens the 2.2.2 memory issue, so treat it as a stopgap.

About 150 words. No package table: two packages fit in a line. No "To confirm": nothing is open.

## Why this is MERGE and not MERGE AFTER CHECKS

Every check in the verdict rule is closed with evidence in the reply: both releases read, the one changed behaviour searched and found handled, the calling code run by a PR test, no pins, no install-time code, no new source. Remove any one of those (no repo to search, a release with no notes, a test that does not import `app/ingest.py`) and the verdict drops to MERGE AFTER CHECKS with that item as the check.

## The same shape when it blocks

Suppose instead the PR moved tidyparse to 3.0.0 and the notes (invented for this illustration) said 3.0.0 requires Python 3.11 and `parse_rows()` now returns a `RowSet` instead of a list. The reply keeps the order and stays short:

> **DO NOT MERGE.** 3.0.0 needs Python 3.11 and the production image runs 3.10, and the import code indexes a result that is no longer a list.
>
> 🟥 1. `Dockerfile:1` builds on `python:3.10-slim`; CI runs 3.12 (`ci.yml:12`), so the PR passed and the image build fails at install. Move the image to 3.11 in this PR.
> 🟥 2. `app/ingest.py:17` does `rows[0]` on what is now a `RowSet`; no test reads the first row, so CI missed it. Use `rows.first()`.
>
> Also in the lockfile: `charset-sniff` 1.4.0 → 1.4.1.
> Rollback: `git revert` the merge commit and rebuild the image.
>
> I can make both changes on this branch.

The lead names both blockers; each blocker says what breaks, where, why CI missed it and the fix; nothing is in the reply that does not change the decision.

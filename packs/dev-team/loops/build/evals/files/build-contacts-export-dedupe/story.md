# Story: drop duplicate contacts from the export

Agreed at refinement on 2026-11-04 (owner: Marisol Venn, product).

As a support lead, I want the contacts export to skip duplicate people,
so that the mailing tool doesn't send the same person two copies.

## Acceptance criteria

1. A new `--dedupe` flag on `export_contacts.py`. Without the flag, output is unchanged.
2. Two rows are duplicates when their `email` values match ignoring case.
3. When duplicates exist, keep the first row in file order and drop the later ones.
4. Print `skipped N duplicate(s)` to stderr when `--dedupe` drops any rows.

Out of scope: merging fields from duplicate rows, validating email addresses.

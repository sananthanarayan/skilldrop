# behaviour-equivalence — reference

## What to record, per boundary

| Boundary | Record from the old system | Usually forgotten |
|---|---|---|
| HTTP endpoint | method, path, query, body, the headers that change behaviour (auth scope, locale, `Accept`); response status, body, headers clients read (`Location`, `Content-Type`, cache headers) | error responses, redirects, `Retry-After`, empty 204s |
| Function / library call | arguments, return value, exception type and message, mutations of arguments | argument mutation callers rely on, exceptions swallowed and logged |
| Batch job | input files and parameters; every output file, the reject or error file, exit code | the reject file, header and trailer records, line endings, encoding |
| Database writes | rows inserted, updated and deleted per case (query the touched tables before and after) | audit rows, soft deletes, sequence or counter bumps |
| Events / messages | topic, key, payload, headers, count and order per key | events emitted on the error path, duplicates on retry |
| Email / notifications | recipient, template, rendered fields | the ones sent on failure |

Record at the narrowest seam both versions answer at. Capture production traffic with a tee,
a shadow deployment or request logs, then scrub personal data before it leaves production:
replace names, emails and card numbers with stable placeholders so the same customer maps to
the same placeholder on both sides.

## Making replay deterministic before normalising

Freeze what can be frozen, then normalise only what remains:

- **Clock:** inject a fixed `now` per case if both systems accept one; otherwise normalise the timestamp field.
- **Random and IDs:** seed the generator, or normalise to the format (`regex`), never ignore.
- **External calls:** replay recorded responses from dependencies (rates, stock, a tax service) so both versions see the same world.
- **Concurrency:** single-threaded replay first; ordering differences under concurrency are a separate test.

## Normalisation catalogue

| Noise | Rule | Scope it to | Not noise when |
|---|---|---|---|
| Wall-clock timestamp | `ignore` or `regex` to `<ts>` | the one timestamp field | the field is a computed date (due date, expiry) |
| Generated ID (UUID, sequence) | `regex` on the format | the id field | the new format differs: a contract change |
| Order of an unordered collection | `sort` by a key | the one list | a caller displays or pages it, or ties are broken differently |
| Float printed by another library | `tolerance` abs or rel | the one field, with the precision it is computed to | the field is money |
| Display rounding | `round` digits | the one field | the rounded value is what is stored or charged |
| Whitespace, line endings | `regex` | the text field or file | a fixed-width consumer reads it |
| Locale formatting (`1,5` vs `1.5`) | `regex` | the field | a user sees it |
| JSON key order | none needed | compared as objects already | the consumer parses by position |

A rule is wrong when it is wider than the noise: a rule on `body`, `*` or "every timestamp
anywhere" hides the next real difference in the same subtree. The script has no any-depth
wildcard for this reason.

## Rules-file format (for `scripts/golden_diff.py`)

```json
{"rules": [
  {"path": "body.issued_at", "rule": "ignore", "reason": "wall-clock time of the call"},
  {"path": "body.invoice_id", "rule": "regex", "pattern": "^INV-[0-9]{6}$", "replace": "INV-<id>", "reason": "sequence per environment"},
  {"path": "body.items", "rule": "sort", "by": "line_no", "reason": "built from a hash map"},
  {"path": "body.items[].weight_kg", "rule": "tolerance", "abs": "0.0005", "reason": "computed in float, shown to 3 places"},
  {"path": "body.score", "rule": "round", "digits": 3, "mode": "half_even", "reason": "ranking score printed at different precision"}
]}
```

Paths are dotted keys; `[]` is every element of a list, `[2]` one element, `*` any key at that
level, `$` the whole record (text files). `ignore` replaces the value but keeps presence, so a
field that disappears is still a difference. `ignore`, `regex` and `round` run first, then
`sort`, then the comparison with tolerances. Numbers are compared as decimals, so `1` equals
`1.0` and no float error creeps in; `true` never equals `1`.

Accepted changes go in a separate file so noise and intended changes never mix:

```json
{"accepted": [
  {"path": "body.error.message", "cases": ["c14", "c15"], "approver": "<name from the input>", "reason": "new error copy, ticket <id from the input>"}
]}
```

The script refuses an accepted change with no approver, and warns about one that matched nothing.

## Difference patterns and their usual causes

| What the differing cases share | Usual cause | Check |
|---|---|---|
| Values on an exact .5 of the smallest unit | rounding mode (half-up vs half-even, or truncation) | find the rounding call in both versions |
| Off by one unit on totals only | rounding per line vs on the total | compare line-level fields too |
| Dates one day apart, times near midnight | time zone (UTC vs local), or DST | add cases either side of midnight and of each DST change |
| Leap day, 31st, month end | date arithmetic library | add 29 Feb, 31 Jan + 1 month |
| Non-ASCII input | encoding, normalisation form, collation | add accented, CJK and emoji cases |
| Order differs only among equal sort keys | unstable sort or a new tie-break | does the old system give the same order twice? |
| Error status or exception type | validation moved layers, framework default | compare status and body, not only the message |
| Missing rows, events or files | side effect dropped in the rewrite | diff the writes per case |
| Large inputs only | limits, pagination, overflow | add a case at and past the maximum |

## Coverage line

One row per input class, not per test:

| Class | Cases | Branch in the old code |
|---|---|---|
| single item, standard rate | c01 | `quote` main path |
| unknown id | not recorded | error path: equivalence not proven here |

The verdict holds for the rows with cases. A class production sends with no case keeps the
verdict at NOT PROVEN, however clean the rest is.

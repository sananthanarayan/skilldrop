# context-graph reference

What `scripts/context_graph.py` reads, how it decides each field, and every check it makes.

## Where records are found

Without `--docs`, every one of these folders under `--root` that exists:
`docs/adr`, `docs/adrs`, `docs/decisions`, `docs/architecture/decisions`, `doc/adr`,
`doc/architecture/decisions`, `adr`, `adrs`, `decisions`, `architecture/decisions`, `docs/rfcs`,
`docs/rfc`, `rfcs`, `rfc`, `docs/design`, `docs/designs`.

Every `.md` file in them, recursively, is a record, except:
- `README.md` and `index.md`;
- any file with "template" in its name;
- a `0000-` file, which by convention is the template.

## Fields

| Field | Read from, in order |
|---|---|
| id | frontmatter `id`, `adr` or `rfc`; else the filename's leading number (`0007-…`, `adr-7-…`). Formatted as `ADR-0007`, `RFC-0007` or `DR-0007`, by whether the folder path says adr/decision or rfc |
| title | frontmatter `title`; else the first `# ` heading with any "ADR 7:" prefix removed; else the filename |
| status | frontmatter `status`; else a `Status: X` line (bold allowed); else the first line under a `## Status` heading |
| date | frontmatter `date`, `created`, `decided` or `accepted`; else a `Date:` line; else the first ISO date in the first 15 lines |
| supersedes | frontmatter `supersedes` or `replaces`; text "Supersedes ADR-3" or "Replaces RFC 12" |
| superseded by | frontmatter `superseded_by` or `replaced_by`; text "Superseded by ADR-9", including in the Status line |
| amends | frontmatter `amends`; text "Amends ADR-4", or "Extends", "Refines", "Narrows", "Overrides" or "Modifies" followed by an id |
| cites | every id mentioned (`ADR-4`, `ADR 0004`, `RFC-12`), and every Markdown link to another record file |
| governs | each path named in backticks or linked, that exists under `--root`: a file, or a folder (shown with a trailing `/`). `src/auth/*` counts as `src/auth` |
| missing paths | a path that looks like the repository's (its first part is a top-level folder that exists) but doesn't exist |
| moved | for a missing path, an existing sibling with a close name (`services/ledger-sync` → `services/ledger`), where the code may have gone |
| commits | with `--git`: commits whose subject or body mentions the id, newest first, up to 20 |
| drift | with `--git`, for a current record that governs a path: the commits that changed those paths since the record's date, newest first. When the record has no date, they count from when its file was first committed. Each has its author and whether it cites the record. Also gives the authors and their counts, the last change, and when the record file was last edited. Merges are left out |

**Statuses, normalised:**

| Status | Words read as it |
|---|---|
| proposed | draft, open, review, rfc |
| accepted | approved, agreed, adopted, active |
| implemented | done, shipped |
| rejected | declined, withdrawn |
| deprecated | retired, obsolete |
| superseded | replaced |

Accepted and implemented count as **current**. A record with no status line is `unknown`, and an
unknown word is `unrecognised`.

## Checks

| Severity | Finding | The fix |
|---|---|---|
| problem | A record another record supersedes is still marked accepted, proposed or with no status | Set its Status to `Superseded by <id>` |
| problem | A record is superseded by an id that doesn't exist | Correct the id, or write the missing record |
| problem | A current record names a path that is gone, with no close-named sibling | Deprecate the record if the decision died, or find where the code went |
| warning | A current record names a path that has moved or been renamed | Update the path in the record |
| warning | A guide or README outside the record folders cites a superseded record | Update the guide: it may still teach the old decision |
| problem | Two records share an id | Renumber one, and fix the references to it |
| problem | A supersession cycle | Break it: one record must be the current one |
| warning | "Superseded by X", but X doesn't say it supersedes this record | Add "Supersedes <id>" to X |
| warning | Marked superseded, but no successor is named | Name it |
| warning | Supersedes an id that doesn't exist | Correct the id |
| warning | A reference to an id that doesn't exist | Correct it, or remove it |
| warning | No status, or a status word it doesn't know | Add or correct the Status line |
| warning | A current record cites one that has since been superseded | Check the citing decision still holds against the newer one |
| warning | Two current records govern the same path, and neither supersedes nor amends the other | A person reads both and decides: supersede, amend, or narrow one's scope |

Exit codes:
- 0: no problems (warnings allowed), or a `--why` or `--record` query was answered;
- 1: the full check found problems;
- 2: no records, an unreadable `--root` or `--docs`, or an unknown `--record` id.

A file that isn't UTF-8 is skipped, with a note in the report.

## JSON (`--json`)

```json
{
  "root": "/abs/path",
  "records": [{
    "id": "ADR-0004", "title": "…", "status": "accepted", "status_text": "Accepted",
    "date": "2025-03-02", "path": "docs/adr/0004-….md",
    "supersedes": [], "superseded_by": [], "amends": [], "cites": [], "cited_by": [],
    "governs": ["services/orders/"], "missing_paths": [], "commits": [],
    "drift": {"since": "2025-03-02", "since_from": "record", "count": 3, "not_citing_record": 2,
              "authors": [{"name": "Ben", "commits": 2}, {"name": "Ana", "commits": 1}],
              "last_change": "2026-06-04", "record_last_edited": "2025-03-02",
              "commits": [{"sha": "a1b2c3d", "date": "2026-06-04", "author": "Ben", "subject": "…",
                           "cites_record": false}]},
    "successors": ["ADR-0009"], "successors_only_claimed_by_successor": ["ADR-0009"],
    "moved": {"services/kafka-bridge": ["services/bridge"]}
  }],
  "docs": [{"path": "docs/onboarding.md", "cites": ["ADR-0004"]}],
  "findings": [{"severity": "problem", "record": "ADR-0004", "message": "…"}],
  "notes": [],
  "query": null
}
```

`drift` is `null` without `--git`, and for a record that isn't current or governs no path.

`successors` joins a record's own "superseded by" with every record that says it supersedes this
one. The second list holds the ones only the newer record records.

## Code changed since each decision (`--git`)

The full report gains a table of the current decisions whose governed code has changed since
they were made, most changed first:

| Column | Meaning |
|---|---|
| Decided | the record's date; `*` when it has none and the date is when the record was first committed |
| Commits since | commits to the governed paths since that date, merges left out |
| Not citing it | how many of those don't mention the record's id: the changes made without reference to it |
| By | the authors, with their counts, most first |
| Last change | the newest of those commits |
| Record last edited | the last commit to the record file itself |

`--why` adds a "Changed since" line under each current decision, and `--record` lists up to 10
of the commits. The Markdown table shows 15 rows; `--json` has them all.

A commit to a decision's code is a reason to check it, not drift by itself. Drift is a
requirement in the record that the code no longer meets.

## Limits

- **A decision made in a ticket or a chat, and never written down, isn't in the graph.** The
  answer for that is "no recorded decision".
- **A path counts as governed only when the record names it.** A decision about "the billing
  service" that never names its folder governs nothing here. Name the folder in the record.
- **Ids are recognised as `ADR`, `RFC`, `DR` or `DD`, plus a number.** Other schemes are read from
  the filename only.

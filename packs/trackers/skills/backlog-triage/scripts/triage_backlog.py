#!/usr/bin/env python3
"""Compute the mechanical parts of a backlog triage from a tracker export.

Reads a CSV or JSON export from Jira, Linear or GitHub Projects (or the JSON an MCP
tool returns) and reports, for open items only:
  - duplicate candidates by title similarity (difflib), with the score
  - items with no owner, and items with no acceptance criteria
  - stale items (no update in N days)
  - oversized items (estimate above a threshold, or size XL/XXL)
  - mechanical priority conflicts (urgent but unowned or stale, duplicates at different
    priorities, too much of the backlog at the top priority)

It writes a markdown findings report and, optionally, a CSV change list. Judgment
(which duplicate survives, the proposed ordering) is left to the person or agent
reading the report. Stdlib only; runs on Python 3.9+.

Usage:
    python3 triage_backlog.py export.csv -o triage.md
    python3 triage_backlog.py export.json --as-of 2026-10-01 --stale-days 45 \\
        --changes changes.csv -o triage.md
    python3 triage_backlog.py export.csv --map title="Issue summary" --map owner=Lead -o triage.md
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

# Canonical field -> header names seen in Jira, Linear and GitHub Projects exports.
# Matching is case-insensitive. Override any of them with --map field=Header.
ALIASES = {
    "key": ["issue key", "key", "identifier", "id", "number", "issue id"],
    "title": ["summary", "title", "name"],
    "description": ["description", "body"],
    "acceptance": ["acceptance criteria", "custom field (acceptance criteria)"],
    "status": ["status", "state", "workflow state"],
    "owner": ["assignee", "assignees", "owner"],
    "priority": ["priority"],
    "estimate": ["story points", "custom field (story points)", "story point estimate",
                 "estimate", "size", "points"],
    "created": ["created", "created at", "createdat"],
    "updated": ["updated", "updated at", "updatedat", "last updated"],
    "resolved": ["resolved", "completed", "completed at", "completedat", "closed at",
                 "closedat", "resolutiondate"],
    "labels": ["labels", "label"],
}

DONE_STATUSES = {"done", "closed", "resolved", "complete", "completed", "canceled", "cancelled",
                 "duplicate", "won't do", "wont do", "won't fix", "released", "shipped"}

# Lower rank = more urgent. Covers Jira, Linear (names and 0-4 numbers) and P0-P4 labels.
PRIORITY_RANK = {
    "highest": 0, "blocker": 0, "urgent": 0, "p0": 0, "critical": 0,
    "high": 1, "p1": 1, "major": 1,
    "medium": 2, "p2": 2, "normal": 2,
    "low": 3, "p3": 3, "minor": 3,
    "lowest": 4, "p4": 4, "trivial": 4,
    "no priority": 5, "none": 5,
}
LINEAR_NUMERIC = {"1": 0, "2": 1, "3": 2, "4": 3, "0": 5}
OVERSIZE_TSHIRT = {"xl", "xxl", "2xl", "3xl"}

AC_PATTERN = re.compile(
    r"acceptance criteria|definition of done|\bAC\s*[:\-]|^\s*[-*]?\s*(given|when|then)\b|\bgiven\b[^\n]*\bthen\b|- \[[ x]\]",
    re.I | re.M,
)
STOPWORDS = {"a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "is", "be", "with",
             "when", "should", "can", "as", "at", "by", "from", "it", "not"}


def die(msg: str) -> None:
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


def flat_value(v) -> str:
    """Turn nested JSON values (users, statuses, label lists) into a plain string."""
    if v is None:
        return ""
    if isinstance(v, dict):
        for k in ("displayName", "name", "login", "title", "value", "key"):
            if v.get(k) not in (None, ""):
                return str(v[k])
        if "nodes" in v:
            return flat_value(v["nodes"])
        return ""
    if isinstance(v, list):
        return ", ".join(s for s in (flat_value(x) for x in v) if s)
    return str(v)


def load_rows(path: Path) -> list:
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        die("cannot read {}: {}".format(path, e))
    if suffix in (".csv", ".tsv"):
        delim = "\t" if suffix == ".tsv" else ","
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
        try:
            header = next(reader)
        except StopIteration:
            die("{} is empty".format(path))
        rows = []
        for raw in reader:
            if not any(c.strip() for c in raw):
                continue
            row = {}
            # Jira repeats columns (Labels, Labels, ...); join repeats instead of overwriting.
            for h, v in zip(header, raw):
                h = h.strip()
                if h in row and v.strip():
                    row[h] = (row[h] + ", " + v.strip()) if row[h] else v.strip()
                elif h not in row:
                    row[h] = v.strip()
            rows.append(row)
        return rows
    if suffix in (".json", ".jsonl", ".ndjson"):
        try:
            if suffix == ".json":
                data = json.loads(text)
            else:
                data = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as e:
            die("{} is not valid JSON: {}".format(path, e))
        if isinstance(data, dict):
            for k in ("issues", "items", "nodes", "data", "results"):
                if isinstance(data.get(k), list):
                    data = data[k]
                    break
        if not isinstance(data, list):
            die("JSON must be a list of issues, or an object with an 'issues'/'items' list")
        rows = []
        for obj in data:
            if not isinstance(obj, dict):
                continue
            merged = dict(obj)
            for nest in ("fields", "content"):  # Jira REST `fields`, gh project `content`
                if isinstance(obj.get(nest), dict):
                    for k, v in obj[nest].items():
                        merged.setdefault(k, v)
            rows.append({k: flat_value(v) for k, v in merged.items()})
        return rows
    die("unsupported file type {!r}: use .csv, .tsv, .json or .jsonl".format(suffix))
    return []


def build_mapping(headers: list, overrides: dict) -> dict:
    lower = {h.lower().strip(): h for h in headers}
    mapping = {}
    for field, names in ALIASES.items():
        if field in overrides:
            if overrides[field] not in headers:
                die("--map {}={!r}: no such column. Columns are: {}".format(
                    field, overrides[field], ", ".join(headers)))
            mapping[field] = overrides[field]
            continue
        for n in names:
            if n in lower:
                mapping[field] = lower[n]
                break
    return mapping


def parse_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    s2 = s[:-1] + "+00:00" if s.endswith("Z") else s
    try:
        return datetime.fromisoformat(s2).date()
    except ValueError:
        pass
    for fmt in ("%d/%b/%y %I:%M %p", "%d/%b/%Y %I:%M %p", "%Y-%m-%d %H:%M", "%m/%d/%Y",
                "%d/%m/%Y", "%d/%b/%y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def priority_rank(p: str):
    p = (p or "").strip().lower()
    if not p:
        return None
    if p in LINEAR_NUMERIC:
        return LINEAR_NUMERIC[p]
    return PRIORITY_RANK.get(p)


def norm_title(t: str) -> str:
    t = re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower())
    return " ".join(w for w in t.split() if w not in STOPWORDS)


def oversized(est: str, max_est: float):
    e = (est or "").strip()
    if not e:
        return None
    if e.lower() in OVERSIZE_TSHIRT:
        return "size " + e
    try:
        n = float(e)
    except ValueError:
        return None
    if n > max_est:
        return "estimate {:g} > {:g}".format(n, max_est)
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical backlog triage from a tracker export.")
    ap.add_argument("export", type=Path, help="CSV, TSV, JSON or JSONL export")
    ap.add_argument("-o", "--output", type=Path, help="markdown report path (default: stdout)")
    ap.add_argument("--changes", type=Path, help="also write a CSV change list here")
    ap.add_argument("--as-of", help="date to measure staleness from, YYYY-MM-DD (default: today)")
    ap.add_argument("--stale-days", type=int, default=30, help="no update in this many days = stale (30)")
    ap.add_argument("--similarity", type=float, default=0.75,
                    help="title similarity 0-1 to flag a duplicate pair (0.75)")
    ap.add_argument("--max-estimate", type=float, default=8,
                    help="estimate above this = oversized (8)")
    ap.add_argument("--inflation-pct", type=float, default=25,
                    help="flag when more than this %% of open items sit at the top priority (25)")
    ap.add_argument("--map", action="append", default=[], metavar="FIELD=Column",
                    help="map a field to a column name; fields: " + ", ".join(ALIASES))
    args = ap.parse_args(argv)

    if not 0 < args.similarity <= 1:
        die("--similarity must be between 0 and 1")
    overrides = {}
    for m in args.map:
        if "=" not in m:
            die("--map takes FIELD=Column, got {!r}".format(m))
        k, v = m.split("=", 1)
        if k not in ALIASES:
            die("--map: unknown field {!r}; use one of {}".format(k, ", ".join(ALIASES)))
        overrides[k] = v
    as_of = date.today() if not args.as_of else parse_date(args.as_of)
    if as_of is None:
        die("--as-of must be YYYY-MM-DD")

    if not args.export.exists():
        die("{} does not exist".format(args.export))
    rows = load_rows(args.export)
    if not rows:
        die("{} has no issues in it".format(args.export))
    headers = []
    for r in rows:
        for h in r:
            if h not in headers:
                headers.append(h)
    mp = build_mapping(headers, overrides)
    for required in ("title",):
        if required not in mp:
            die("no title column found. Columns are: {}. Use --map title=<Column>".format(
                ", ".join(headers)))

    def g(row, field):
        col = mp.get(field)
        return (row.get(col) or "").strip() if col else ""

    items = []
    for i, r in enumerate(rows, 1):
        key = g(r, "key") or "row-{}".format(i)
        status = g(r, "status")
        done = status.lower() in DONE_STATUSES or bool(g(r, "resolved"))
        items.append({
            "key": key, "title": g(r, "title"), "status": status or "(none)", "done": done,
            "owner": g(r, "owner"), "priority": g(r, "priority"),
            "rank": priority_rank(g(r, "priority")), "estimate": g(r, "estimate"),
            "updated": parse_date(g(r, "updated")) or parse_date(g(r, "created")),
            "has_ac": bool(g(r, "acceptance")) or bool(AC_PATTERN.search(g(r, "description"))),
            "labels": g(r, "labels"),
        })
    open_items = [it for it in items if not it["done"]]

    no_owner = [it for it in open_items if not it["owner"] or it["owner"].lower() in ("unassigned", "none")]
    no_ac = [it for it in open_items if not it["has_ac"]]
    no_date = [it for it in open_items if it["updated"] is None]
    stale = []
    for it in open_items:
        if it["updated"] is not None:
            age = (as_of - it["updated"]).days
            if age > args.stale_days:
                stale.append((age, it))
    stale.sort(key=lambda x: -x[0])
    big = [(oversized(it["estimate"], args.max_estimate), it) for it in open_items]
    big = [(why, it) for why, it in big if why]

    # Duplicate candidates: difflib ratio on normalised titles, with cheap prefilters.
    dupes = []
    normed = [(it, norm_title(it["title"])) for it in open_items]
    for a in range(len(normed)):
        ia, ta = normed[a]
        if not ta:
            continue
        for b in range(a + 1, len(normed)):
            ib, tb = normed[b]
            if not tb:
                continue
            sm = SequenceMatcher(None, ta, tb)
            if sm.real_quick_ratio() < args.similarity or sm.quick_ratio() < args.similarity:
                continue
            score = sm.ratio()
            if score >= args.similarity:
                shared = sorted(set(ta.split()) & set(tb.split()))
                dupes.append((score, ia, ib, shared))
    dupes.sort(key=lambda x: -x[0])

    # Mechanical priority conflicts.
    conflicts = []
    stale_keys = {it["key"]: age for age, it in stale}
    for it in open_items:
        if it["rank"] is not None and it["rank"] <= 1:
            if it in no_owner:
                conflicts.append((it, "priority {} but no owner".format(it["priority"])))
            if it["key"] in stale_keys:
                conflicts.append((it, "priority {} but no update in {} days".format(
                    it["priority"], stale_keys[it["key"]])))
    for score, ia, ib, _ in dupes:
        if ia["priority"] and ib["priority"] and ia["rank"] != ib["rank"]:
            conflicts.append((ia, "likely duplicate of {} but priority {} vs {}".format(
                ib["key"], ia["priority"], ib["priority"])))
    ranked = [it for it in open_items if it["rank"] is not None]
    top = [it for it in ranked if it["rank"] == 0]
    inflation = None
    if ranked:
        pct = 100.0 * len(top) / len(ranked)
        if pct > args.inflation_pct:
            inflation = "{} of {} prioritised open items ({:.0f}%) are at the top priority".format(
                len(top), len(ranked), pct)
    unknown_pri = sorted({it["priority"] for it in open_items if it["priority"] and it["rank"] is None})

    # ---- report ----
    L = []
    L.append("# Backlog triage findings: {}".format(args.export.name))
    L.append("")
    L.append("As of {} · {} items in export · {} open · {} done or closed (skipped)".format(
        as_of.isoformat(), len(items), len(open_items), len(items) - len(open_items)))
    L.append("Thresholds: stale > {} days · similarity >= {} · oversized estimate > {:g}".format(
        args.stale_days, args.similarity, args.max_estimate))
    L.append("")
    L.append("Columns used: " + ", ".join("{}={!r}".format(k, v) for k, v in mp.items()))
    missing = [f for f in ("key", "owner", "priority", "estimate", "updated", "description") if f not in mp]
    if missing:
        L.append("Not found in export (checks that need them are skipped): " + ", ".join(missing))
    L.append("")
    L.append("| Check | Count |")
    L.append("|---|---:|")
    L.append("| Duplicate candidate pairs | {} |".format(len(dupes)))
    L.append("| No owner | {} |".format(len(no_owner) if "owner" in mp else "n/a"))
    L.append("| No acceptance criteria | {} |".format(len(no_ac) if ("description" in mp or "acceptance" in mp) else "n/a"))
    L.append("| Stale (> {} days) | {} |".format(args.stale_days, len(stale) if "updated" in mp or "created" in mp else "n/a"))
    L.append("| Oversized | {} |".format(len(big) if "estimate" in mp else "n/a"))
    L.append("| Priority conflicts | {} |".format(len(conflicts) + (1 if inflation else 0)))
    L.append("")

    L.append("## Duplicate candidates")
    L.append("")
    if dupes:
        L.append("| Pair | Score | Titles | Shared words |")
        L.append("|---|---:|---|---|")
        for score, ia, ib, shared in dupes:
            L.append("| {} / {} | {:.2f} | {} / {} | {} |".format(
                ia["key"], ib["key"], score, ia["title"], ib["title"], " ".join(shared) or "-"))
        L.append("")
        L.append("Title similarity only. Read both descriptions before merging.")
    else:
        L.append("None at this threshold.")
    L.append("")

    def item_table(title, rows_, extra_head, extra_fn):
        L.append("## " + title)
        L.append("")
        if not rows_:
            L.append("None.")
            L.append("")
            return
        L.append("| Key | Title | Status | Priority | {} |".format(extra_head))
        L.append("|---|---|---|---|---|")
        for row_ in rows_:
            it = row_[1] if isinstance(row_, tuple) else row_
            L.append("| {} | {} | {} | {} | {} |".format(
                it["key"], it["title"], it["status"], it["priority"] or "-", extra_fn(row_)))
        L.append("")

    if "owner" in mp:
        item_table("No owner", no_owner, "Last update",
                   lambda it: it["updated"].isoformat() if it["updated"] else "-")
    if "description" in mp or "acceptance" in mp:
        item_table("No acceptance criteria", no_ac, "Owner", lambda it: it["owner"] or "-")
    item_table("Stale (no update in more than {} days)".format(args.stale_days), stale,
               "Days since update", lambda row_: str(row_[0]))
    if no_date:
        L.append("{} open items have no updated or created date, so staleness is unknown: {}".format(
            len(no_date), ", ".join(it["key"] for it in no_date)))
        L.append("")
    if "estimate" in mp:
        item_table("Oversized (split before scheduling)", big, "Why", lambda row_: row_[0])

    L.append("## Priority conflicts")
    L.append("")
    if inflation:
        L.append("- Priority inflation: " + inflation + ".")
    for it, why in conflicts:
        L.append("- {} ({}): {}".format(it["key"], it["title"], why))
    if not conflicts and not inflation:
        L.append("None found mechanically.")
    if unknown_pri:
        L.append("")
        L.append("Priority values not recognised (not ranked): " + ", ".join(unknown_pri))
    L.append("")
    L.append("## Priority distribution (open items)")
    L.append("")
    dist = {}
    for it in open_items:
        dist[it["priority"] or "(none)"] = dist.get(it["priority"] or "(none)", 0) + 1
    L.append("| Priority | Open items |")
    L.append("|---|---:|")
    for p, n in sorted(dist.items(), key=lambda kv: (priority_rank(kv[0]) if priority_rank(kv[0]) is not None else 9, kv[0])):
        L.append("| {} | {} |".format(p, n))
    L.append("")

    report = "\n".join(L) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        sys.stderr.write("wrote {}\n".format(args.output))
    else:
        sys.stdout.write(report)

    if args.changes:
        with args.changes.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["key", "action", "field", "proposed_value", "reason"])
            for score, ia, ib, _ in dupes:
                w.writerow([ib["key"], "confirm-duplicate", "status", "Duplicate of " + ia["key"],
                            "title similarity {:.2f} with {}".format(score, ia["key"])])
            for it in no_owner:
                w.writerow([it["key"], "assign-owner", "assignee", "", "open item with no owner"])
            for it in no_ac:
                w.writerow([it["key"], "add-acceptance-criteria", "description", "", "no acceptance criteria found"])
            for age, it in stale:
                w.writerow([it["key"], "confirm-or-close", "status", "",
                            "no update in {} days".format(age)])
            for why, it in big:
                w.writerow([it["key"], "split", "", "", why])
        sys.stderr.write("wrote {}\n".format(args.changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())

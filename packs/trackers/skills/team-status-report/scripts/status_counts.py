#!/usr/bin/env python3
"""Compute the numbers for a team status report from a tracker export.

Reads a CSV or JSON export from Jira, Linear or GitHub Projects (or the JSON an MCP
tool returns) and, for one reporting period, counts:
  - shipped: done items whose resolved date falls in the period
  - in progress, and work in progress per owner
  - blocked: with the blocker text and owner, when the export has them
  - plan vs actual: what was planned to finish by the end of the period, how much did,
    and what slipped
  - risk candidates: blocked planned items, unowned planned items, top-priority items not started
and suggests a RAG status, printing the rule that set it.

The plan is the set of items meant to be done by the end of the period. It comes from
--plan-file (one key per line), --sprint (items in a sprint/cycle/iteration that ends in
the period), or by default items whose due date falls in the period.

Stdlib only; runs on Python 3.9+.

Usage:
    python3 status_counts.py export.csv --from 2026-09-24 --to 2026-09-30 -o status-numbers.md
    python3 status_counts.py export.json --from 2026-09-24 --to 2026-09-30 --sprint "CHK Sprint 14"
    python3 status_counts.py export.csv --from 2026-09-24 --to 2026-09-30 --plan-file plan.txt --json numbers.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

ALIASES = {
    "key": ["issue key", "key", "identifier", "id", "number", "issue id"],
    "title": ["summary", "title", "name"],
    "status": ["status", "state", "workflow state"],
    "owner": ["assignee", "assignees", "owner"],
    "priority": ["priority"],
    "created": ["created", "created at", "createdat"],
    "updated": ["updated", "updated at", "updatedat", "last updated"],
    "resolved": ["resolved", "completed", "completed at", "completedat", "closed at",
                 "closedat", "resolutiondate"],
    "due": ["due date", "due", "duedate", "due on", "target date"],
    "sprint": ["sprint", "cycle", "iteration", "milestone"],
    "blocker": ["blocked by", "blocker", "blocked reason", "inward issue link (blocks)",
                "flagged", "custom field (flagged)", "impediment"],
    "labels": ["labels", "label"],
}

SHIPPED_STATUSES = {"done", "closed", "resolved", "complete", "completed", "released", "shipped",
                    "merged"}
DROPPED_STATUSES = {"canceled", "cancelled", "duplicate", "won't do", "wont do", "won't fix",
                    "obsolete"}
NOT_STARTED_STATUSES = {"to do", "todo", "backlog", "open", "new", "triage", "ready",
                        "selected for development", "planned", "unstarted"}
BLOCKED_STATUSES = {"blocked", "on hold", "impeded", "waiting"}

PRIORITY_RANK = {
    "highest": 0, "blocker": 0, "urgent": 0, "p0": 0, "critical": 0,
    "high": 1, "p1": 1, "major": 1,
    "medium": 2, "p2": 2, "normal": 2,
    "low": 3, "p3": 3, "minor": 3,
    "lowest": 4, "p4": 4, "trivial": 4,
    "no priority": 5, "none": 5,
}
LINEAR_NUMERIC = {"1": 0, "2": 1, "3": 2, "4": 3, "0": 5}


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



def pct(n: int, d: int) -> str:
    return "{:.0f}%".format(100.0 * n / d) if d else "n/a"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Status-report numbers from a tracker export.")
    ap.add_argument("export", type=Path, help="CSV, TSV, JSON or JSONL export")
    ap.add_argument("--from", dest="start", required=True, help="period start, YYYY-MM-DD (inclusive)")
    ap.add_argument("--to", dest="end", required=True, help="period end, YYYY-MM-DD (inclusive)")
    ap.add_argument("-o", "--output", type=Path, help="markdown output path (default: stdout)")
    ap.add_argument("--json", type=Path, help="also write the numbers as JSON here")
    plan = ap.add_mutually_exclusive_group()
    plan.add_argument("--plan-file", type=Path, help="keys planned to finish this period, one per line")
    plan.add_argument("--sprint", help="sprint/cycle/iteration name whose items were planned to finish")
    ap.add_argument("--red-below", type=float, default=60, help="plan completion %% below this = Red (60)")
    ap.add_argument("--amber-below", type=float, default=85, help="plan completion %% below this = Amber (85)")
    ap.add_argument("--red-blocked", type=int, default=2,
                    help="this many blocked planned items = Red (2)")
    ap.add_argument("--map", action="append", default=[], metavar="FIELD=Column",
                    help="map a field to a column name; fields: " + ", ".join(ALIASES))
    args = ap.parse_args(argv)

    start, end = parse_date(args.start), parse_date(args.end)
    if start is None or end is None:
        die("--from and --to must be YYYY-MM-DD")
    if start > end:
        die("--from {} is after --to {}".format(start, end))
    if not 0 <= args.red_below <= args.amber_below <= 100:
        die("need 0 <= --red-below <= --amber-below <= 100")
    overrides = {}
    for m in args.map:
        if "=" not in m:
            die("--map takes FIELD=Column, got {!r}".format(m))
        k, v = m.split("=", 1)
        if k not in ALIASES:
            die("--map: unknown field {!r}; use one of {}".format(k, ", ".join(ALIASES)))
        overrides[k] = v

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
    for required in ("title", "status"):
        if required not in mp:
            die("no {} column found. Columns are: {}. Use --map {}=<Column>".format(
                required, ", ".join(headers), required))
    if args.sprint and "sprint" not in mp:
        die("--sprint given but no sprint/cycle/iteration column found; use --map sprint=<Column>")

    def g(row, field):
        col = mp.get(field)
        return (row.get(col) or "").strip() if col else ""

    items = []
    for i, r in enumerate(rows, 1):
        status = g(r, "status")
        s = status.lower()
        resolved = parse_date(g(r, "resolved"))
        labels = g(r, "labels").lower()
        if s in DROPPED_STATUSES:
            state = "dropped"
        elif s in SHIPPED_STATUSES:
            state = "done"
        elif s in BLOCKED_STATUSES or "blocked" in [x.strip() for x in labels.split(",")] or g(r, "blocker"):
            state = "blocked"
        elif s in NOT_STARTED_STATUSES:
            state = "not-started"
        else:
            state = "in-progress"
        p = g(r, "priority").lower()
        rank = priority_rank(p)
        items.append({
            "key": g(r, "key") or "row-{}".format(i), "title": g(r, "title"), "status": status,
            "state": state, "owner": g(r, "owner"), "priority": g(r, "priority"), "rank": rank,
            "resolved": resolved, "updated": parse_date(g(r, "updated")),
            "due": parse_date(g(r, "due")), "sprint": g(r, "sprint"), "blocker": g(r, "blocker"),
        })

    notes = []
    # Shipped in the period.
    if "resolved" in mp:
        shipped = [it for it in items if it["state"] == "done" and it["resolved"]
                   and start <= it["resolved"] <= end]
        undated = [it for it in items if it["state"] == "done" and not it["resolved"]]
        if undated:
            notes.append("{} done items have no resolved date and are not counted as shipped: {}".format(
                len(undated), ", ".join(it["key"] for it in undated)))
    else:
        shipped = [it for it in items if it["state"] == "done" and it["updated"]
                   and start <= it["updated"] <= end]
        notes.append("No resolved/completed column: shipped uses the last-updated date of done items, "
                     "which can count items edited after they closed.")
    in_progress = [it for it in items if it["state"] == "in-progress"]
    blocked = [it for it in items if it["state"] == "blocked"]

    # The plan.
    plan_source = None
    planned = []
    if args.plan_file:
        if not args.plan_file.exists():
            die("--plan-file {} does not exist".format(args.plan_file))
        keys = [ln.strip() for ln in args.plan_file.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]
        by_key = {it["key"]: it for it in items}
        missing = [k for k in keys if k not in by_key]
        if missing:
            notes.append("Plan keys not found in the export: " + ", ".join(missing))
        planned = [by_key[k] for k in keys if k in by_key]
        plan_source = "plan file {} ({} keys)".format(args.plan_file.name, len(keys))
    elif args.sprint:
        planned = [it for it in items if args.sprint.lower() in it["sprint"].lower()]
        plan_source = "items in sprint '{}'".format(args.sprint)
    elif "due" in mp:
        planned = [it for it in items if it["due"] and start <= it["due"] <= end]
        plan_source = "items due between {} and {}".format(start, end)
        overdue = [it for it in items if it["due"] and it["due"] < start
                   and it["state"] not in ("done", "dropped")]
        if overdue:
            notes.append("{} items were due before this period and are still open: {}".format(
                len(overdue), ", ".join(it["key"] for it in overdue)))
    else:
        notes.append("No plan: no --plan-file, no --sprint and no due-date column. "
                     "Plan vs actual and slippage can't be computed.")
    planned = [it for it in planned if it["state"] != "dropped"]
    shipped_keys = {it["key"] for it in shipped}

    def done_by_end(it):
        if it["state"] != "done":
            return False
        d = it["resolved"] if "resolved" in mp else it["updated"]
        return d is None or d <= end

    planned_done = [it for it in planned if done_by_end(it)]
    slipped = [it for it in planned if not done_by_end(it)]
    unplanned_shipped = [it for it in shipped if it["key"] not in {p["key"] for p in planned}]
    blocked_planned = [it for it in blocked if it["key"] in {p["key"] for p in planned}]

    risks = []
    for it in blocked_planned:
        risks.append((it, "planned for this period and blocked"))
    for it in planned:
        if it["state"] != "done" and not it["owner"]:
            risks.append((it, "planned for this period with no owner"))
    for it in items:
        if it["rank"] == 0 and it["state"] == "not-started":
            risks.append((it, "top priority ({}) and not started".format(it["priority"])))

    # RAG.
    fired = []
    completion = 100.0 * len(planned_done) / len(planned) if planned else None
    top_slipped = [it for it in slipped if it["rank"] is not None and it["rank"] <= 1]
    if completion is not None and completion < args.red_below:
        fired.append(("Red", "plan completion {:.0f}% is below {:g}%".format(completion, args.red_below)))
    if len(blocked_planned) >= args.red_blocked:
        fired.append(("Red", "{} planned items are blocked (Red at {})".format(len(blocked_planned), args.red_blocked)))
    if completion is not None and args.red_below <= completion < args.amber_below:
        fired.append(("Amber", "plan completion {:.0f}% is below {:g}%".format(completion, args.amber_below)))
    if 0 < len(blocked_planned) < args.red_blocked:
        fired.append(("Amber", "{} planned item is blocked".format(len(blocked_planned))))
    if top_slipped:
        fired.append(("Amber", "{} High-or-above planned item(s) slipped: {}".format(
            len(top_slipped), ", ".join(it["key"] for it in top_slipped))))
    if completion is None and blocked:
        fired.append(("Amber", "no plan to measure against, and {} items are blocked".format(len(blocked))))
    if any(c == "Red" for c, _ in fired):
        rag = "Red"
    elif fired:
        rag = "Amber"
    else:
        rag = "Green"
    if completion is None and rag == "Green":
        rag = "Green, with no plan to measure against"
    if not fired:
        if completion is None:
            fired.append(("Green", "nothing blocked; no plan to measure against, so delivery isn't reflected"))
        else:
            fired.append(("Green", "plan completion {:.0f}% is at or above {:g}% and no planned item is blocked".format(
                completion, args.amber_below)))

    # ---- report ----
    L = []
    L.append("# Status numbers: {} to {}".format(start, end))
    L.append("")
    L.append("Source: {} · {} items · plan: {}".format(args.export.name, len(items), plan_source or "none"))
    L.append("Columns used: " + ", ".join("{}={!r}".format(k, v) for k, v in mp.items()))
    L.append("")
    L.append("## Suggested RAG: {}".format(rag))
    L.append("")
    L.append("Rule: Red if plan completion < {:g}% or >= {} planned items blocked; Amber if completion < {:g}%, "
             "any planned item blocked, or a High-or-above planned item slipped; otherwise Green.".format(
                 args.red_below, args.red_blocked, args.amber_below))
    for colour, why in fired:
        L.append("- {}: {}".format(colour, why))
    L.append("")
    L.append("| Measure | Count |")
    L.append("|---|---:|")
    L.append("| Shipped in period | {} |".format(len(shipped)))
    L.append("| In progress | {} |".format(len(in_progress)))
    L.append("| Blocked | {} |".format(len(blocked)))
    if plan_source:
        L.append("| Planned to finish by {} | {} |".format(end, len(planned)))
        L.append("| Planned and done | {} ({}) |".format(len(planned_done), pct(len(planned_done), len(planned))))
        L.append("| Slipped (planned, not done) | {} |".format(len(slipped)))
        L.append("| Shipped but not in plan | {} |".format(len(unplanned_shipped)))
    L.append("")

    def table(title, rows_, cols):
        L.append("## " + title)
        L.append("")
        if not rows_:
            L.append("None.")
            L.append("")
            return
        L.append("| " + " | ".join(c[0] for c in cols) + " |")
        L.append("|" + "---|" * len(cols))
        for it in rows_:
            L.append("| " + " | ".join(c[1](it) for c in cols) + " |")
        L.append("")

    key = ("Key", lambda it: it["key"])
    title = ("Title", lambda it: it["title"])
    owner = ("Owner", lambda it: it["owner"] or "(none)")
    table("Shipped", shipped, [key, title, owner,
                               ("Done", lambda it: (it["resolved"] or it["updated"]).isoformat()
                                if (it["resolved"] or it["updated"]) else "-")])
    table("In progress", in_progress, [key, title, owner, ("Status", lambda it: it["status"])])
    table("Blocked", blocked, [key, title, owner,
                               ("Blocker", lambda it: it["blocker"] or "(not recorded)"),
                               ("Last update", lambda it: it["updated"].isoformat() if it["updated"] else "-")])
    if plan_source:
        table("Slipped (planned, not done by {})".format(end), slipped,
              [key, title, owner, ("Status", lambda it: it["status"]),
               ("Priority", lambda it: it["priority"] or "-"),
               ("Due", lambda it: it["due"].isoformat() if it["due"] else "-")])
    L.append("## Risk candidates")
    L.append("")
    if risks:
        for it, why in risks:
            L.append("- {} ({}): {}".format(it["key"], it["title"], why))
    else:
        L.append("None found mechanically.")
    L.append("")
    wip = {}
    for it in in_progress + blocked:
        wip[it["owner"] or "(none)"] = wip.get(it["owner"] or "(none)", 0) + 1
    L.append("## Work in progress by owner (in progress + blocked)")
    L.append("")
    L.append("| Owner | Items |")
    L.append("|---|---:|")
    for o, n in sorted(wip.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("| {} | {} |".format(o, n))
    L.append("")
    if notes:
        L.append("## Data notes")
        L.append("")
        for n in notes:
            L.append("- " + n)
        L.append("")

    out = "\n".join(L) + "\n"
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        sys.stderr.write("wrote {}\n".format(args.output))
    else:
        sys.stdout.write(out)
    if args.json:
        data = {
            "period": {"from": start.isoformat(), "to": end.isoformat()},
            "plan_source": plan_source,
            "rag": rag, "rag_reasons": [w for _, w in fired],
            "counts": {"shipped": len(shipped), "in_progress": len(in_progress), "blocked": len(blocked),
                       "planned": len(planned), "planned_done": len(planned_done),
                       "slipped": len(slipped), "unplanned_shipped": len(unplanned_shipped)},
            "shipped": [it["key"] for it in shipped],
            "blocked": [{"key": it["key"], "owner": it["owner"], "blocker": it["blocker"]} for it in blocked],
            "slipped": [it["key"] for it in slipped],
            "notes": notes,
        }
        args.json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        sys.stderr.write("wrote {}\n".format(args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())

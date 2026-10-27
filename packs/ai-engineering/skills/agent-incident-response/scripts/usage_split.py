#!/usr/bin/env python3
"""Split a provider usage or billing export (CSV) by who spent it.

Read-only. Sums cost exactly (decimal, not float) per group of columns, so a bill
is split from the export rather than estimated. Groups by the key, model and
user-agent columns it finds (override with --by). Each group shows its total,
its share of the whole, its row and request counts, and the time of its first and
last row as written in the export.

    python3 usage_split.py usage.csv
    python3 usage_split.py usage.csv --since 2026-10-19T20:00 --expect model=model-medium
    python3 usage_split.py usage.csv --by api_key_name,user_agent -o split.txt
    cat usage.csv | python3 usage_split.py -

--expect col=value (repeatable) marks every group whose value in that column
differs as UNEXPECTED: traffic the known job does not explain. --since/--until
compare the time column as text, so give them in the export's own format.
Writes only the -o path when given.
"""
import argparse
import csv
import io
import sys
from decimal import Decimal, InvalidOperation

COST_HINTS = ("cost_usd", "cost", "amount_usd", "amount", "spend", "usd", "price")
TIME_HINTS = ("date_hour_utc", "timestamp", "time", "hour", "date", "start_time", "period")
REQ_HINTS = ("requests", "request_count", "num_requests", "calls")
GROUP_HINTS = (
    ("api_key_name", "api_key", "key_name", "key_id", "key"),
    ("model", "model_name", "model_id"),
    ("user_agent", "useragent", "ua", "client"),
)


def find_col(headers, hints, contains=False):
    low = {h.lower().strip(): h for h in headers}
    for hint in hints:
        if hint in low:
            return low[hint]
    if contains:
        for hint in hints:
            for key, orig in low.items():
                if hint in key:
                    return orig
    return None


def to_decimal(text):
    cleaned = (text or "").strip().replace("$", "").replace(",", "")
    if cleaned == "":
        return Decimal("0")
    return Decimal(cleaned)


def money(value):
    return "${:,.2f}".format(value)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("export", help="CSV usage export path, or - for stdin")
    ap.add_argument("--by", help="comma-separated columns to group by (default: key, model, user agent)")
    ap.add_argument("--cost", help="cost column name (default: auto-detect)")
    ap.add_argument("--time", help="time column name (default: auto-detect)")
    ap.add_argument("--since", help="keep rows whose time is >= this text")
    ap.add_argument("--until", help="keep rows whose time is < this text")
    ap.add_argument("--expect", action="append", default=[], metavar="COL=VALUE",
                    help="mark groups whose COL differs from VALUE as UNEXPECTED")
    ap.add_argument("-o", "--output", help="write the report to this path instead of stdout")
    args = ap.parse_args(argv)

    if args.export == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.export, encoding="utf-8", newline="") as fh:
                text = fh.read()
        except OSError as exc:
            print("error: cannot read {}: {}".format(args.export, exc), file=sys.stderr)
            return 2
    text = text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    if not headers:
        print("error: the export has no header row", file=sys.stderr)
        return 2

    cost_col = args.cost or find_col(headers, COST_HINTS, contains=True)
    time_col = args.time or find_col(headers, TIME_HINTS, contains=True)
    req_col = find_col(headers, REQ_HINTS)
    if not cost_col or cost_col not in headers:
        print("error: no cost column found; columns are: {}; pass --cost".format(", ".join(headers)),
              file=sys.stderr)
        return 2
    if args.by:
        group_cols = [c.strip() for c in args.by.split(",") if c.strip()]
    else:
        group_cols = [c for c in (find_col(headers, h) for h in GROUP_HINTS) if c]
    missing = [c for c in group_cols if c not in headers]
    if missing or not group_cols:
        print("error: group columns not in the export: {}; columns are: {}".format(
            ", ".join(missing) or "(none found)", ", ".join(headers)), file=sys.stderr)
        return 2
    if (args.since or args.until) and not time_col:
        print("error: --since/--until need a time column; pass --time", file=sys.stderr)
        return 2

    expects = []
    for item in args.expect:
        if "=" not in item:
            print("error: --expect takes COL=VALUE, got {!r}".format(item), file=sys.stderr)
            return 2
        col, val = item.split("=", 1)
        if col not in group_cols:
            print("error: --expect column {!r} must be one of the group columns: {}".format(
                col, ", ".join(group_cols)), file=sys.stderr)
            return 2
        expects.append((col, val))

    groups = {}
    total = Decimal("0")
    kept = 0
    bad = []
    for line_no, row in enumerate(reader, start=2):
        when = (row.get(time_col) or "").strip() if time_col else ""
        if args.since and when < args.since:
            continue
        if args.until and when >= args.until:
            continue
        try:
            cost = to_decimal(row.get(cost_col))
        except InvalidOperation:
            bad.append(line_no)
            continue
        key = tuple((row.get(c) or "").strip() for c in group_cols)
        g = groups.setdefault(key, {"cost": Decimal("0"), "rows": 0, "requests": 0,
                                    "first": None, "last": None, "times": []})
        g["cost"] += cost
        g["rows"] += 1
        if req_col:
            try:
                g["requests"] += int(float((row.get(req_col) or "0").replace(",", "")))
            except ValueError:
                pass
        if when:
            g["times"].append(when)
            g["first"] = when if g["first"] is None or when < g["first"] else g["first"]
            g["last"] = when if g["last"] is None or when > g["last"] else g["last"]
        total += cost
        kept += 1

    out = []
    window = ""
    if args.since or args.until:
        window = " ({} to {})".format(args.since or "start", args.until or "end")
    out.append("Rows: {}{}   Total: {}".format(kept, window, money(total)))
    out.append("Grouped by: {}   Cost column: {}{}".format(
        ", ".join(group_cols), cost_col, "   Time column: " + time_col if time_col else ""))
    out.append("")
    for key, g in sorted(groups.items(), key=lambda kv: kv[1]["cost"], reverse=True):
        share = (g["cost"] / total * 100) if total else Decimal("0")
        label = " | ".join("{}={}".format(c, v) for c, v in zip(group_cols, key))
        flag = ""
        if expects:
            off = [c for c, v in expects if key[group_cols.index(c)] != v]
            if off:
                flag = "  UNEXPECTED ({} differs)".format(", ".join(off))
        out.append("{}  {}  ({:.1f}%){}".format(money(g["cost"]), label, share, flag))
        detail = "    rows={}".format(g["rows"])
        if req_col:
            detail += " requests={:,}".format(g["requests"])
        if g["first"]:
            detail += " first={} last={}".format(g["first"], g["last"])
        out.append(detail)
        if g["times"] and len(g["times"]) <= 12:
            out.append("    times: " + ", ".join(sorted(g["times"])))
    if bad:
        out.append("")
        out.append("Skipped rows with an unreadable cost (CSV line numbers): " +
                   ", ".join(str(n) for n in bad))
    report = "\n".join(out) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print("wrote {}".format(args.output))
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

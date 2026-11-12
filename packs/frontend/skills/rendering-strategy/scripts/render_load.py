#!/usr/bin/env python3
"""Count the page renders each route costs per month under its rendering mode.

Reads a CSV of routes (a path, or "-" for stdin) and prints a Markdown table of
origin renders per month under the chosen mode beside what per-request SSR
would cost, so the cost question in a rendering decision is a number, not a
guess. Stdlib only, Python 3.9+.

CSV columns (header row required; blank cells allowed where noted):
  route          name of the route, e.g. /products/[slug]
  mode           ssg | isr | ssr | csr | edge
  views_month    page views per month for the whole route (all pages)
  pages          distinct pages the route has (default 1)
  revalidate_s   isr only: time-based revalidation window in seconds
                 (blank = on-demand revalidation only)
  changes_month  ssg/isr: content changes per month that trigger a rebuild or
                 on-demand revalidation of one page (default 0)
  builds_month   ssg only: full builds per month (default 0)

Usage:
  python3 render_load.py routes.csv [-o report.md]
"""

import argparse
import csv
import io
import sys

MONTH_S = 30 * 24 * 3600
MODES = {"ssg", "isr", "ssr", "csr", "edge"}


def num(row, key, default=None, line=0):
    raw = (row.get(key) or "").strip().replace(",", "").replace("_", "")
    if raw == "":
        if default is None:
            raise ValueError(f"line {line}: '{key}' is required")
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"line {line}: '{key}' must be a number, got '{raw}'")
    if value < 0:
        raise ValueError(f"line {line}: '{key}' must not be negative")
    return value


def renders(row, line):
    mode = (row.get("mode") or "").strip().lower()
    if mode not in MODES:
        raise ValueError(f"line {line}: mode must be one of {sorted(MODES)}, got '{mode}'")
    views = num(row, "views_month", line=line)
    pages = max(num(row, "pages", 1, line), 1)
    changes = num(row, "changes_month", 0, line)
    note = ""
    if mode == "ssr":
        origin = views
        note = "one render per view; TTFB depends on the data source"
    elif mode == "edge":
        origin = views
        note = "one render per view, at the edge; data calls still go to origin"
    elif mode == "csr":
        origin = 0
        note = f"static shell; at least {fmt(views)} client data calls"
    elif mode == "ssg":
        builds = num(row, "builds_month", 0, line)
        origin = builds * pages + changes
        note = "renders happen at build time, not per view"
    else:  # isr
        reval = num(row, "revalidate_s", 0, line)
        if reval == 0:
            origin = min(changes, views)
            note = "on-demand revalidation only"
        else:
            windows = MONTH_S / reval
            per_page = views / pages
            # each render is triggered by a view, so renders never exceed views
            origin = min(pages * min(per_page, windows) + changes, views)
            if per_page <= windows:
                note = ("upper bound; each page gets fewer views than windows, "
                        "so time-based revalidation saves little: use on-demand")
            elif pages == 1:
                note = "at most one render per window"
            else:
                note = "upper bound if traffic is even; skewed traffic renders less"
    saved = 0.0 if views == 0 else 1 - origin / views
    return {
        "route": (row.get("route") or "").strip() or f"(line {line})",
        "mode": mode,
        "views": views,
        "origin": origin,
        "saved": saved,
        "note": note,
    }


def pct(saved):
    if saved <= 0:
        return "no fewer" if saved == 0 else f"{-saved * 100:.0f}% more"
    if saved >= 0.995 and saved < 1:
        return ">99% fewer"
    if saved < 0.005:
        return "<1% fewer"
    return f"{saved * 100:.0f}% fewer"


def fmt(n):
    return f"{int(round(n)):,}"


def report(rows):
    out = [
        "| Route | Mode | Views/month | Origin renders/month | vs SSR per request | Note |",
        "|---|---|---:|---:|---:|---|",
    ]
    total_views = total_origin = 0.0
    for r in rows:
        total_views += r["views"]
        total_origin += r["origin"]
        out.append(
            f"| {r['route']} | {r['mode']} | {fmt(r['views'])} | {fmt(r['origin'])} | "
            f"{pct(r['saved'])} | {r['note']} |"
        )
    saved = 0.0 if total_views == 0 else 1 - total_origin / total_views
    out.append(
        f"| **Total** | | {fmt(total_views)} | {fmt(total_origin)} | {pct(saved)} | |"
    )
    out.append("")
    out.append(
        "Origin renders are upper bounds assuming views spread evenly across a route's pages; "
        "a 30-day month is used. SSR per request renders once per view."
    )
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv", help="routes CSV, or - for stdin")
    ap.add_argument("-o", "--output", help="write the Markdown report here (default: stdout)")
    args = ap.parse_args(argv)

    try:
        if args.csv == "-":
            text = sys.stdin.read()
        else:
            with open(args.csv, encoding="utf-8") as fh:
                text = fh.read()
    except OSError as exc:
        print(f"error: cannot read {args.csv}: {exc}", file=sys.stderr)
        return 2

    reader = csv.DictReader(io.StringIO(text))
    missing = {"route", "mode", "views_month"} - set(reader.fieldnames or [])
    if missing:
        print(f"error: CSV is missing columns: {', '.join(sorted(missing))}", file=sys.stderr)
        return 2
    rows = []
    try:
        for i, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            rows.append(renders(row, i))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not rows:
        print("error: no routes in the CSV", file=sys.stderr)
        return 2

    text = report(rows)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

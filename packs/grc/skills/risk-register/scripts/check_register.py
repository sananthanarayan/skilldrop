#!/usr/bin/env python3
"""Validate a risk-register CSV and print heat-map counts.

Stdlib only, Python 3.9+. Reads the CSV from a path argument (or "-" for stdin),
checks every row, and prints a plain-text report: errors, warnings, inherent and
residual heat maps, overdue reviews and actions, and the top risks by residual score.

Exit codes:
  0  the register is valid (warnings may still be printed)
  1  the register has errors (missing fields, scores out of range, bad dates, ...)
  2  the input could not be read at all (missing file, no header, bad arguments)

Usage:
  python3 check_register.py register.csv
  python3 check_register.py register.csv --scale 5 --as-of 2026-10-01 --top 5 --out report.txt
  cat register.csv | python3 check_register.py -
"""

import argparse
import csv
import datetime
import io
import sys

REQUIRED_COLUMNS = [
    "id",
    "title",
    "cause",
    "event",
    "consequence",
    "owner",
    "inherent_likelihood",
    "inherent_impact",
    "residual_likelihood",
    "residual_impact",
    "treatment",
    "controls",
    "due_date",
    "next_review",
    "review_trigger",
    "status",
]

# Columns that may be blank on a row without making it an error.
OPTIONAL_VALUE_COLUMNS = {"controls", "due_date", "review_trigger"}

SCORE_COLUMNS = [
    "inherent_likelihood",
    "inherent_impact",
    "residual_likelihood",
    "residual_impact",
]

TREATMENTS = {"avoid", "reduce", "transfer", "accept"}
STATUSES = {"open", "closed"}
GENERIC_OWNERS = {"tbd", "tbc", "team", "all", "everyone", "n/a", "na", "none", "it", "?"}

BANDS = ["low", "medium", "high", "critical"]


def band_for(score, scale):
    """Band a likelihood x impact score by its share of the maximum score.

    On a 5x5 scale this gives low 1-4, medium 5-9, high 10-16, critical 20-25.
    """
    ratio = float(score) / float(scale * scale)
    if ratio <= 0.16:
        return "low"
    if ratio <= 0.36:
        return "medium"
    if ratio <= 0.64:
        return "high"
    return "critical"


def band_ranges(scale):
    ranges = {}
    products = sorted(set(a * b for a in range(1, scale + 1) for b in range(1, scale + 1)))
    for s in products:
        b = band_for(s, scale)
        lo, hi = ranges.get(b, (s, s))
        ranges[b] = (min(lo, s), max(hi, s))
    return ranges


def parse_date(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def heat_map(rows, lik_col, imp_col, scale):
    grid = {}
    for r in rows:
        key = (r[lik_col], r[imp_col])
        grid[key] = grid.get(key, 0) + 1
    lines = []
    header = "  L\\I |" + "".join(" {:>3}".format(i) for i in range(1, scale + 1))
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for lik in range(scale, 0, -1):
        cells = []
        for imp in range(1, scale + 1):
            n = grid.get((lik, imp), 0)
            cells.append(" {:>3}".format(n if n else "."))
        lines.append("  {:>3} |".format(lik) + "".join(cells))
    return lines


def band_counts(rows, lik_col, imp_col, scale):
    counts = dict((b, 0) for b in BANDS)
    for r in rows:
        counts[band_for(r[lik_col] * r[imp_col], scale)] += 1
    return counts


def bullets(items):
    if not items:
        return ["  none"]
    return ["  - " + i for i in items]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a risk-register CSV and print heat-map counts.")
    ap.add_argument("csv", help="path to the register CSV, or - for stdin")
    ap.add_argument("--scale", type=int, default=5, help="likelihood and impact scale, 1..N (default 5)")
    ap.add_argument("--as-of", dest="as_of", default=None, help="date to judge overdue items against, YYYY-MM-DD (default today)")
    ap.add_argument("--top", type=int, default=5, help="how many top residual risks to list (default 5)")
    ap.add_argument("--out", default=None, help="also write the report to this path")
    args = ap.parse_args(argv)

    if args.scale < 3 or args.scale > 10:
        print("error: --scale must be between 3 and 10", file=sys.stderr)
        return 2
    if args.as_of:
        as_of = parse_date(args.as_of)
        if as_of is None:
            print("error: --as-of must be YYYY-MM-DD, got %r" % args.as_of, file=sys.stderr)
            return 2
    else:
        as_of = datetime.date.today()

    try:
        if args.csv == "-":
            text = sys.stdin.read()
        else:
            with io.open(args.csv, "r", encoding="utf-8-sig", newline="") as fh:
                text = fh.read()
    except (IOError, OSError) as exc:
        print("error: cannot read %s: %s" % (args.csv, exc), file=sys.stderr)
        return 2

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        print("error: %s has no header row" % args.csv, file=sys.stderr)
        return 2
    fieldnames = [f.strip() for f in reader.fieldnames]
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing_cols:
        print("error: missing required column(s): %s" % ", ".join(missing_cols), file=sys.stderr)
        print("expected columns: %s" % ",".join(REQUIRED_COLUMNS), file=sys.stderr)
        return 2

    errors = []
    warnings = []
    overdue = []
    valid = []
    seen_ids = {}
    total_rows = 0

    for line_no, raw in enumerate(reader, start=2):
        row = dict((k.strip(), (v or "").strip()) for k, v in raw.items() if k is not None)
        if not any(row.values()):
            continue
        total_rows += 1
        rid = row.get("id") or "(line %d)" % line_no
        where = "line %d [%s]" % (line_no, rid)
        row_ok = True

        for col in REQUIRED_COLUMNS:
            if col in OPTIONAL_VALUE_COLUMNS:
                continue
            if not row.get(col):
                errors.append("%s: %s is empty" % (where, col))
                row_ok = False

        if row.get("id"):
            if row["id"] in seen_ids:
                errors.append("%s: duplicate id, first seen on line %d" % (where, seen_ids[row["id"]]))
                row_ok = False
            else:
                seen_ids[row["id"]] = line_no

        owner = row.get("owner", "")
        if owner and owner.lower() in GENERIC_OWNERS:
            errors.append("%s: owner %r is not a named person or role" % (where, owner))
            row_ok = False

        scores = {}
        for col in SCORE_COLUMNS:
            val = row.get(col, "")
            if not val:
                continue
            try:
                n = int(val)
            except ValueError:
                errors.append("%s: %s must be a whole number 1-%d, got %r" % (where, col, args.scale, val))
                row_ok = False
                continue
            if n < 1 or n > args.scale:
                errors.append("%s: %s=%d is outside the 1-%d scale" % (where, col, n, args.scale))
                row_ok = False
                continue
            scores[col] = n

        treatment = row.get("treatment", "").lower()
        if treatment and treatment not in TREATMENTS:
            errors.append("%s: treatment %r is not one of avoid/reduce/transfer/accept" % (where, row["treatment"]))
            row_ok = False

        status = row.get("status", "").lower()
        if status and status not in STATUSES:
            errors.append("%s: status %r is not open or closed" % (where, row["status"]))
            row_ok = False

        dates = {}
        for col in ("due_date", "next_review"):
            val = row.get(col, "")
            if not val:
                continue
            d = parse_date(val)
            if d is None:
                errors.append("%s: %s must be YYYY-MM-DD, got %r" % (where, col, val))
                row_ok = False
            else:
                dates[col] = d

        if treatment in ("reduce", "avoid", "transfer") and not row.get("due_date"):
            warnings.append("%s: treatment is %s but there is no due_date for the action" % (where, treatment))
        if treatment == "reduce" and not row.get("controls"):
            warnings.append("%s: treatment is reduce but no controls are listed" % where)
        if not row.get("review_trigger"):
            warnings.append("%s: no review_trigger; name the event that should reopen this risk" % where)

        if len(scores) == 4:
            inh = scores["inherent_likelihood"] * scores["inherent_impact"]
            res = scores["residual_likelihood"] * scores["residual_impact"]
            if res > inh:
                errors.append("%s: residual score %d is higher than inherent score %d" % (where, res, inh))
                row_ok = False
            if treatment == "reduce" and res == inh:
                warnings.append("%s: treatment is reduce but residual equals inherent (%d); the controls change nothing" % (where, res))
            if treatment == "accept" and band_for(res, args.scale) in ("high", "critical"):
                warnings.append("%s: accepting a %s residual risk (%d) needs a named sign-off above the owner" % (where, band_for(res, args.scale), res))

        if status == "open":
            if "next_review" in dates and dates["next_review"] < as_of:
                days = (as_of - dates["next_review"]).days
                overdue.append("%s: review overdue by %d day(s) (next_review %s), owner %s" % (where, days, dates["next_review"], owner or "?"))
            if "due_date" in dates and dates["due_date"] < as_of:
                days = (as_of - dates["due_date"]).days
                overdue.append("%s: treatment action overdue by %d day(s) (due_date %s), owner %s" % (where, days, dates["due_date"], owner or "?"))

        if row_ok and len(scores) == 4:
            entry = dict(row)
            entry.update(scores)
            entry["status"] = status
            valid.append(entry)

    open_rows = [r for r in valid if r["status"] == "open"]

    out = []
    out.append("Risk register check")
    out.append("  file:   %s" % args.csv)
    out.append("  as of:  %s" % as_of.isoformat())
    out.append("  scale:  1-%d likelihood x 1-%d impact" % (args.scale, args.scale))
    ranges = band_ranges(args.scale)
    out.append("  bands:  " + ", ".join("%s %d-%d" % (b, ranges[b][0], ranges[b][1]) for b in BANDS if b in ranges))
    out.append("  rows:   %d read, %d valid, %d open" % (total_rows, len(valid), len(open_rows)))
    out.append("")

    out.append("Errors (%d)" % len(errors))
    out.extend(bullets(errors))
    out.append("")
    out.append("Warnings (%d)" % len(warnings))
    out.extend(bullets(warnings))
    out.append("")
    out.append("Overdue (%d)" % len(overdue))
    out.extend(bullets(overdue))
    out.append("")

    out.append("Inherent heat map, open risks (rows = likelihood, columns = impact)")
    out.extend(heat_map(open_rows, "inherent_likelihood", "inherent_impact", args.scale))
    c = band_counts(open_rows, "inherent_likelihood", "inherent_impact", args.scale)
    out.append("  " + ", ".join("%s %d" % (b, c[b]) for b in BANDS))
    out.append("")
    out.append("Residual heat map, open risks (rows = likelihood, columns = impact)")
    out.extend(heat_map(open_rows, "residual_likelihood", "residual_impact", args.scale))
    c = band_counts(open_rows, "residual_likelihood", "residual_impact", args.scale)
    out.append("  " + ", ".join("%s %d" % (b, c[b]) for b in BANDS))
    out.append("")

    ranked = sorted(
        open_rows,
        key=lambda r: (
            -(r["residual_likelihood"] * r["residual_impact"]),
            -(r["inherent_likelihood"] * r["inherent_impact"]),
            r["id"],
        ),
    )
    out.append("Top %d open risks by residual score" % min(args.top, len(ranked)))
    if not ranked:
        out.append("  none")
    for r in ranked[: args.top]:
        inh = r["inherent_likelihood"] * r["inherent_impact"]
        res = r["residual_likelihood"] * r["residual_impact"]
        out.append(
            "  %s  residual %d (%s), inherent %d  %s  [%s, owner %s]"
            % (r["id"], res, band_for(res, args.scale), inh, r["title"], r["treatment"].lower(), r["owner"])
        )
    out.append("")
    out.append("Result: %s" % ("FAIL, fix the errors above" if errors else "PASS"))

    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    if args.out:
        try:
            with io.open(args.out, "w", encoding="utf-8") as fh:
                fh.write(report)
        except (IOError, OSError) as exc:
            print("error: cannot write %s: %s" % (args.out, exc), file=sys.stderr)
            return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

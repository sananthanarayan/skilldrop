#!/usr/bin/env python3
"""Score an analysis-of-competing-hypotheses (ACH) consistency matrix.

Reads a CSV with one row per piece of evidence and one column per hypothesis,
and writes a markdown report that:
  - ranks hypotheses by weighted inconsistency (lowest first), because the
    hypothesis with the least evidence against it survives, not the one with
    the most evidence for it
  - marks each piece of evidence diagnostic or non-diagnostic (it is
    non-diagnostic when it adds the same inconsistency to every hypothesis,
    for example C for all, or a mix of C, CC and N)
  - runs a sensitivity check: drops each piece of evidence in turn and reports
    the ones whose removal changes which hypothesis ranks first

CSV columns:
    id        optional, short label such as E1 (default: row number)
    evidence  required, one line describing the observation
    weight    optional, a number > 0 for credibility x relevance (default 1)
    <H...>    one column per hypothesis, each cell one of:
              CC  very consistent      C  consistent
              N   neutral               NA not applicable
              I   inconsistent          II very inconsistent

Scoring: I counts 1 x weight, II counts 2 x weight, everything else 0.
Consistent ratings are shown but never lower a score.

Usage:
    python3 ach_matrix.py matrix.csv
    python3 ach_matrix.py matrix.csv -o ach-report.md

Exit codes: 0 report written, 2 bad input.
"""

import argparse
import csv
import sys
from pathlib import Path

RATINGS = {"CC": 0, "C": 0, "N": 0, "NA": 0, "I": 1, "II": 2}
RESERVED = {"id", "evidence", "weight"}


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


def fmt(x):
    return str(int(x)) if float(x).is_integer() else "{:.2f}".format(x).rstrip("0").rstrip(".")


def load(path):
    p = Path(path)
    if not p.is_file():
        fail("file not found: " + str(path))
    with p.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            fail("the CSV is empty")
        fields = [h.strip() for h in reader.fieldnames]
        lower = [h.lower() for h in fields]
        if "evidence" not in lower:
            fail("the CSV needs an 'evidence' column")
        hyps = [h for h in fields if h.lower() not in RESERVED and h]
        if len(hyps) < 2:
            fail("the CSV needs at least two hypothesis columns; ACH compares rivals")
        rows = []
        for i, raw in enumerate(reader, start=1):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            lrow = {k.lower(): v for k, v in row.items()}
            ev = lrow.get("evidence", "")
            if not ev:
                fail("row {}: the evidence cell is empty".format(i + 1))
            rid = lrow.get("id") or "E{}".format(i)
            w_raw = lrow.get("weight") or "1"
            try:
                w = float(w_raw)
            except ValueError:
                fail("row {} ({}): weight {!r} is not a number".format(i + 1, rid, w_raw))
            if w <= 0:
                fail("row {} ({}): weight must be greater than 0".format(i + 1, rid))
            ratings = {}
            for h in hyps:
                r = row.get(h, "").upper()
                if r not in RATINGS:
                    fail("row {} ({}), column {!r}: rating {!r} is not one of CC, C, N, NA, I, II".format(
                        i + 1, rid, h, row.get(h, "")))
                ratings[h] = r
            rows.append({"id": rid, "evidence": ev, "weight": w, "ratings": ratings})
    if not rows:
        fail("the CSV has a header but no evidence rows")
    ids = [r["id"] for r in rows]
    dup = sorted(set(x for x in ids if ids.count(x) > 1))
    if dup:
        fail("duplicate evidence ids: " + ", ".join(dup))
    return hyps, rows


def scores(hyps, rows):
    s = {h: 0.0 for h in hyps}
    for r in rows:
        for h in hyps:
            s[h] += RATINGS[r["ratings"][h]] * r["weight"]
    return s


def ranking(hyps, s):
    # Stable: ties keep the CSV column order.
    return sorted(hyps, key=lambda h: s[h])


def leaders(hyps, s):
    best = min(s.values())
    return [h for h in hyps if s[h] == best]


def main():
    ap = argparse.ArgumentParser(description="Score an ACH consistency matrix.")
    ap.add_argument("matrix", help="CSV: id, evidence, weight, then one column per hypothesis")
    ap.add_argument("-o", "--output", help="write the report here instead of stdout")
    args = ap.parse_args()

    hyps, rows = load(args.matrix)
    s = scores(hyps, rows)
    order = ranking(hyps, s)
    top = leaders(hyps, s)

    out = ["# ACH matrix: " + Path(args.matrix).name, ""]
    out.append("{} hypotheses · {} pieces of evidence · ranked by weighted inconsistency, lowest first".format(
        len(hyps), len(rows)))
    out.append("")

    out.append("## Ranking")
    out.append("")
    out.append("| Rank | Hypothesis | Inconsistency score | I | II | C or CC |")
    out.append("|---|---|---|---|---|---|")
    for h in order:
        # Ties share a rank (1, 1, 3), so a tie never looks like a lead.
        i = 1 + sum(1 for x in hyps if s[x] < s[h])
        n_i = sum(1 for r in rows if r["ratings"][h] == "I")
        n_ii = sum(1 for r in rows if r["ratings"][h] == "II")
        n_c = sum(1 for r in rows if r["ratings"][h] in ("C", "CC"))
        out.append("| {} | {} | {} | {} | {} | {} |".format(i, h, fmt(s[h]), n_i, n_ii, n_c))
    out.append("")
    if len(top) > 1:
        out.append("**Tie for first:** " + ", ".join(top) +
                   ". The evidence so far does not separate them; find an observation rated differently for each.")
    else:
        runner = order[1]
        gap = s[runner] - s[top[0]]
        out.append("**Least contradicted:** {} (score {}), {} ahead of {}.".format(
            top[0], fmt(s[top[0]]), fmt(gap), runner))
    out.append("")

    out.append("## Evidence")
    out.append("")
    out.append("| Id | Evidence | Weight | " + " | ".join(hyps) + " | Diagnostic? |")
    out.append("|---|---|---|" + "---|" * len(hyps) + "---|")
    non_diag = []
    for r in rows:
        vals = [r["ratings"][h] for h in hyps]
        # Diagnostic means the item changes the scores differently per hypothesis.
        diag = len(set(RATINGS[v] for v in vals)) > 1
        if not diag:
            non_diag.append(r["id"])
        out.append("| {} | {} | {} | {} | {} |".format(
            r["id"], r["evidence"], fmt(r["weight"]), " | ".join(vals), "yes" if diag else "no"))
    out.append("")
    if non_diag:
        out.append("**Non-diagnostic:** " + ", ".join(non_diag) +
                   ". These count the same against every hypothesis, so they cannot help you choose. "
                   "Keep them for completeness; don't cite them as support.")
        out.append("")

    out.append("## Sensitivity: evidence the conclusion rests on")
    out.append("")
    linchpins = []
    for r in rows:
        rest = [x for x in rows if x is not r]
        s2 = scores(hyps, rest)
        top2 = leaders(hyps, s2)
        if top2 != top:
            linchpins.append((r, top2))
    if linchpins:
        out.append("Dropping any one of these changes which hypothesis ranks first. Check each one's source "
                   "and how it was rated before you rely on the ranking.")
        out.append("")
        for r, top2 in linchpins:
            out.append("- **{}** ({}): without it, first place is {}".format(
                r["id"], r["evidence"], " and ".join(top2) + (" (tie)" if len(top2) > 1 else "")))
    else:
        out.append("No single piece of evidence changes first place when removed.")
    out.append("")

    report = "\n".join(out)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        sys.stdout.write("wrote {} — first: {}\n".format(args.output, ", ".join(top)))
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Count coded customer feedback by distinct person, not by mention.

Reads a coding sheet: one row per feedback item (a ticket, a survey verbatim, an interview
note, a review) that an agent or analyst has already tagged with theme codes. Prints, per
theme:
  - distinct people (or accounts) and mentions (items), and which people filed several
  - the sources it came from, with distinct people per source
  - the segment breakdown for every segment column, and a flag when a theme lives in one
    segment value only
  - distinct people at each severity level, and the worst level reported
and then the items with no theme, the people who filed most, and the rows whose person ID
is missing (those count as one person each, so their numbers are mentions).

Columns (header names, case-insensitive):
  item_id     required  ticket / response / note ID, quoted back as the source of a quote
  person_id   optional  person or account ID; blank -> the row counts as its own person
  source      optional  tickets, nps, interview, app-store, sales-call ...
  themes      required  theme codes separated by ";". A code may carry its own severity
                        as code:S1, overriding the row's severity. A code starting with "+"
                        is something people value (no severity).
  severity    optional  S1 (blocker) .. S4 (cosmetic); blank -> unrated
  any other column is a segment (plan, role, region, tenure ...) unless named in --ignore.
  Columns called quote, text, notes, comment, date, created or summary are ignored by default.

Usage:
    python3 theme_counts.py coded.csv
    python3 theme_counts.py coded.csv --person-col account_id -o counts.md
    python3 theme_counts.py coded.csv --segment plan --segment region --json counts.json

Stdlib only; Python 3.9+. Reads only the CSV it is given; writes only the paths named with
-o / --json.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SEVERITIES = ["S1", "S2", "S3", "S4"]
SEVERITY_ALIASES = {
    "s1": "S1", "1": "S1", "blocker": "S1", "critical": "S1",
    "s2": "S2", "2": "S2", "major": "S2", "high": "S2",
    "s3": "S3", "3": "S3", "minor": "S3", "medium": "S3",
    "s4": "S4", "4": "S4", "cosmetic": "S4", "low": "S4", "trivial": "S4",
}
DEFAULT_IGNORE = {"quote", "text", "notes", "note", "comment", "comments", "date", "created",
                  "summary", "body", "description", "subject", "title", "score"}
CORE = {"item_id", "person_id", "source", "themes", "severity"}
NO_ID = "(no id: "


def die(msg: str) -> None:
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


def norm_sev(value: str, where: str, warnings: list) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    s = SEVERITY_ALIASES.get(v.lower())
    if not s:
        warnings.append(f"{where}: unknown severity '{v}' treated as unrated")
        return ""
    return s


def load(path: Path, person_col: str, ignore: set, segments_wanted: list):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        die(f"cannot read {path}: {e}")
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        die(f"{path} has no header row")
    header = {h.strip().lower(): h for h in reader.fieldnames if h}
    person_key = person_col.lower()
    for need in ("item_id", "themes"):
        if need not in header:
            die(f"{path} needs a '{need}' column (found: {', '.join(reader.fieldnames)})")
    if person_col != "person_id" and person_key not in header:
        die(f"--person-col '{person_col}' is not a column in {path}")
    core = (CORE - {"person_id"}) | {person_key}
    if segments_wanted:
        segs = [s.lower() for s in segments_wanted]
        for s in segs:
            if s not in header:
                die(f"segment column '{s}' is not in {path}")
    else:
        segs = [h for h in header if h not in core and h not in ignore and h != "person_id"]

    warnings: list = []
    rows = []
    seen_ids = set()
    for n, raw in enumerate(reader, start=2):
        r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        item = r.get("item_id", "")
        if not item:
            warnings.append(f"line {n}: no item_id; row skipped")
            continue
        if item in seen_ids:
            warnings.append(f"line {n}: item_id {item} appears twice; both rows counted")
        seen_ids.add(item)
        pid = r.get(person_key, "")
        row_sev = norm_sev(r.get("severity", ""), f"{item}", warnings)
        codes = []
        for c in r.get("themes", "").split(";"):
            c = c.strip()
            if not c:
                continue
            sev = row_sev
            if ":" in c:
                c, _, s = c.partition(":")
                c = c.strip()
                sev = norm_sev(s, f"{item} theme {c}", warnings)
            if c.startswith("+"):
                sev = ""
            if c:
                codes.append((c, sev))
        rows.append({
            "item": item,
            "person": pid or f"{NO_ID}{item})",
            "has_id": bool(pid),
            "source": r.get("source", "") or "(none)",
            "segments": {s: r.get(s, "") for s in segs},
            "codes": codes,
        })
    return rows, segs, warnings


def analyse(rows, segs):
    people_seg = defaultdict(dict)          # person -> seg -> value (first non-empty)
    seg_conflicts = defaultdict(set)
    for r in rows:
        for s, v in r["segments"].items():
            if not v:
                continue
            have = people_seg[r["person"]].get(s)
            if have is None:
                people_seg[r["person"]][s] = v
            elif have != v:
                seg_conflicts[(r["person"], s)].update({have, v})

    all_values = {s: Counter() for s in segs}
    for p, d in people_seg.items():
        for s, v in d.items():
            all_values[s][v] += 1

    themes = defaultdict(lambda: {"items": [], "people": Counter(), "sources": defaultdict(set),
                                  "sev_people": defaultdict(set)})
    for r in rows:
        for code, sev in r["codes"]:
            t = themes[code]
            t["items"].append(r["item"])
            t["people"][r["person"]] += 1
            t["sources"][r["source"]].add(r["person"])
            t["sev_people"][sev or "unrated"].add(r["person"])

    out = []
    for code, t in themes.items():
        people = list(t["people"])
        seg_break = {}
        single = []
        for s in segs:
            c = Counter(people_seg[p].get(s, "(blank)") for p in people)
            seg_break[s] = dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
            known = [v for v in c if v != "(blank)"]
            known_people = sum(n for v, n in c.items() if v != "(blank)")
            total = sum(all_values[s].values())
            # Flag a theme that sits in one segment value only, unless that value is most of
            # the whole sample anyway (a UK-only theme in a 90% UK sample says nothing).
            if (known_people >= 2 and len(known) == 1 and len(all_values[s]) >= 2
                    and all_values[s][known[0]] / total < 2 / 3):
                blank = c.get("(blank)", 0)
                single.append(f"{s}={known[0]} ({all_values[s][known[0]]} of {total} overall"
                              + (f"; {blank} blank here" if blank else "") + ")")
        # A person's severity for a theme is the worst level they reported for it.
        worst_by_person = {}
        for sev in SEVERITIES + ["unrated"]:
            for p in t["sev_people"].get(sev, ()):
                worst_by_person.setdefault(p, sev)
        sev_counts = Counter(worst_by_person.values())
        worst = next((s for s in SEVERITIES if sev_counts.get(s)), "")
        # Ranking severity: the worst level that at least two people reached (that level or
        # worse). A theme raised by one person takes that person's level, marked "1 report".
        rank_sev, running = "", 0
        for s in SEVERITIES:
            running += sev_counts.get(s, 0)
            if running >= 2:
                rank_sev = s
                break
        if not rank_sev and len(people) == 1 and worst:
            rank_sev = worst + " (1 report)"
        elif not rank_sev and worst:
            rank_sev = worst + " (1 rated)"
        top_person, top_n = t["people"].most_common(1)[0]
        no_id = [p for p in people if p.startswith(NO_ID)]
        out.append({
            "theme": code,
            "valued": code.startswith("+"),
            # people = distinct people with an ID. Rows with no ID are reported beside it,
            # never added to it: an anonymous comment may come from someone already counted.
            "people": len(people) - len(no_id),
            "no_id_items": len(no_id),
            "mentions": len(t["items"]),
            "repeat_filers": {p: n for p, n in t["people"].most_common() if n > 1},
            "top_person_share": round(top_n / len(t["items"]), 2),
            "top_person": top_person,
            "sources": {s: {"people": sum(1 for p in ps if not p.startswith(NO_ID)),
                            "no_id_items": sum(1 for p in ps if p.startswith(NO_ID))}
                        for s, ps in sorted(t["sources"].items())},
            "segments": seg_break,
            "single_segment": single,
            "severity_people": {s: sev_counts[s] for s in SEVERITIES + ["unrated"] if sev_counts.get(s)},
            "worst_severity": worst,
            "ranking_severity": "" if code.startswith("+") else rank_sev,
            "items": t["items"],
        })
    sev_rank = {s: i for i, s in enumerate(SEVERITIES)}
    out.sort(key=lambda d: (d["valued"], sev_rank.get(d["ranking_severity"][:2], 9), -d["people"],
                            -d["no_id_items"], d["theme"]))

    per_person = Counter(r["person"] for r in rows)
    summary = {
        "items": len(rows),
        "people": len({r["person"] for r in rows if r["has_id"]}),
        "items_without_person_id": sum(1 for r in rows if not r["has_id"]),
        "sources": {s: {"items": n, "people": len({r["person"] for r in rows if r["source"] == s and r["has_id"]}),
                        "no_id_items": sum(1 for r in rows if r["source"] == s and not r["has_id"])}
                    for s, n in sorted(Counter(r["source"] for r in rows).items())},
        "segment_values": {s: dict(all_values[s]) for s in segs},
        "most_items_per_person": {p: n for p, n in per_person.most_common(5) if n > 1 and not p.startswith(NO_ID)},
        "unthemed_items": [r["item"] for r in rows if not r["codes"]],
        "segment_conflicts": {f"{p} {s}": sorted(v) for (p, s), v in seg_conflicts.items()},
    }
    return summary, out


def fmt_counts(d: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in d.items()) or "-"


def fmt_sources(d: dict) -> str:
    parts = []
    for s, v in d.items():
        bits = []
        if v["people"]:
            bits.append(str(v["people"]))
        if v["no_id_items"]:
            bits.append(f"+{v['no_id_items']} no-ID")
        parts.append(f"{s} {' '.join(bits)}")
    return ", ".join(parts) or "-"


def render(summary, themes, person_label: str, warnings) -> str:
    plural = "people" if person_label == "person" else person_label + "s"
    L = []
    L.append("# Theme counts")
    L.append("")
    L.append(f"- Items: {summary['items']}; distinct {plural} with an ID: {summary['people']}")
    if summary["items_without_person_id"]:
        L.append(f"- {summary['items_without_person_id']} item(s) have no {person_label} ID. They are counted "
                 f"in the No-ID column, never added to the {person_label} count: each may come from someone "
                 "already counted, so they are mentions, not people.")
    L.append("- By source: " + "; ".join(
        f"{s} {v['items']} items / {v['people']} {plural}" + (f" + {v['no_id_items']} no-ID" if v["no_id_items"] else "")
        for s, v in summary["sources"].items()))
    for s, vals in summary["segment_values"].items():
        L.append(f"- {s} across all {plural} and no-ID items: {fmt_counts(dict(sorted(vals.items())))}")
    if summary["most_items_per_person"]:
        L.append(f"- Most items from one {person_label}: {fmt_counts(summary['most_items_per_person'])}")
    L.append("")
    L.append("Ranked by ranking severity (the worst level at least two people reached), then by "
             f"distinct {plural}. Themes starting with + are things people value.")
    L.append("")
    L.append(f"| Theme | {plural.capitalize()} | No-ID items | Mentions | Ranking severity | Worst | "
             f"By severity | Sources | One segment only |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for t in themes:
        sev_cells = ("-", "-", "-") if t["valued"] else (
            t["ranking_severity"] or "-", t["worst_severity"] or "-", fmt_counts(t["severity_people"]))
        L.append(f"| {t['theme']} | {t['people']} | {t['no_id_items']} | {t['mentions']} | {sev_cells[0]} | "
                 f"{sev_cells[1]} | {sev_cells[2]} | {fmt_sources(t['sources'])} | "
                 f"{', '.join(t['single_segment']) or '-'} |")
    L.append("")
    for t in themes:
        L.append(f"## {t['theme']}")
        L.append(f"- {t['people']} {person_label}(s) with an ID"
                 + (f", plus {t['no_id_items']} item(s) with no ID" if t["no_id_items"] else "")
                 + f"; {t['mentions']} mention(s)")
        L.append(f"- Ranking severity: {t['ranking_severity'] or '-'}" if not t["valued"] else "- Valued (no severity)")
        if t["repeat_filers"]:
            L.append(f"- Repeat filers: {fmt_counts(t['repeat_filers'])}")
        if t["mentions"] >= 3 and t["top_person_share"] > 0.5:
            L.append(f"- WARNING: {t['top_person']} accounts for {int(t['top_person_share'] * 100)}% of this theme's mentions")
        for s, br in t["segments"].items():
            L.append(f"- {s}: {fmt_counts(br)}")
        if t["single_segment"]:
            L.append(f"- Only in: {', '.join(t['single_segment'])}")
        if not t["valued"]:
            L.append(f"- Severity (worst level each {person_label} or no-ID item reported): "
                     f"{fmt_counts(t['severity_people'])}")
        L.append(f"- Items: {', '.join(t['items'])}")
        L.append("")
    L.append("## Items with no theme")
    L.append(", ".join(summary["unthemed_items"]) or "None")
    if summary["segment_conflicts"]:
        L.append("")
        L.append("## Segment conflicts (same ID, different values; first value used)")
        for k, v in summary["segment_conflicts"].items():
            L.append(f"- {k}: {', '.join(v)}")
    if warnings:
        L.append("")
        L.append("## Warnings")
        L.extend(f"- {w}" for w in warnings)
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Count coded feedback by distinct person per theme.")
    ap.add_argument("csv", type=Path, help="coding sheet: item_id, person_id, source, themes, severity, segment columns")
    ap.add_argument("--person-col", default="person_id",
                    help="column that identifies a person or account (default person_id)")
    ap.add_argument("--person-label", default=None, help="word for the counted unit, e.g. account (default: person, or the column name)")
    ap.add_argument("--segment", action="append", default=[], help="segment column to break down by (repeatable; default: every other column)")
    ap.add_argument("--ignore", action="append", default=[], help="column to leave out of segments (repeatable)")
    ap.add_argument("-o", "--output", type=Path, help="write the markdown report here instead of stdout")
    ap.add_argument("--json", type=Path, help="also write the counts as JSON to this path")
    a = ap.parse_args(argv)

    ignore = DEFAULT_IGNORE | {c.lower() for c in a.ignore}
    rows, segs, warnings = load(a.csv, a.person_col, ignore, a.segment)
    if not rows:
        die(f"{a.csv} has no feedback rows")
    label = a.person_label or ("person" if a.person_col == "person_id" else a.person_col.replace("_id", "").replace("_", " "))
    summary, themes = analyse(rows, segs)
    report = render(summary, themes, label, warnings)
    if a.output:
        a.output.write_text(report, encoding="utf-8")
        print(f"wrote {a.output}")
    else:
        sys.stdout.write(report)
    if a.json:
        a.json.write_text(json.dumps({"summary": summary, "themes": themes, "warnings": warnings}, indent=2),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Keep a tracker in step with a brief or PRD.

Two subcommands:

  export  Turn an issues spec (JSON, written from the doc) into a file your tracker imports:
            --target jira     CSV for Jira's CSV importer (Issue Id / Parent Id hierarchy)
            --target csv      a plain CSV with one column per field, for importers with a
                              column-mapping step
            --target github   a shell script of `gh issue create` commands (GitHub has no
                              CSV issue import)
          The spec is checked first: every item needs a title, a description and a source
          section; stories and tasks need acceptance criteria; parents must exist; with
          --doc, every source must exist in the doc.

  drift   Compare a doc with a tracker export and report: doc sections with no issue,
          issues with no section, issues pointing at sections the doc no longer has, and
          issues for requirements the doc marks Won't have.

Sections are requirement IDs found in the doc (default pattern R1, R2 ... in the first
column of a table or at the start of a heading or list item), or, with --headings, the
doc's ## and ### headings. Issues link back with a "Source: <doc>#<anchor> (<ID>)" line.

Stdlib only; runs on Python 3.9+.

Usage:
    python3 brief_sync.py export issues-spec.json --target jira --doc prd.md -o import.csv
    python3 brief_sync.py export issues-spec.json --target github -o create-issues.sh
    python3 brief_sync.py drift --doc prd.md --export tracker-export.csv -o drift.md
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shlex
import sys
from pathlib import Path

ALIASES = {
    "key": ["issue key", "key", "identifier", "id", "number", "issue id"],
    "title": ["summary", "title", "name"],
    "description": ["description", "body"],
    "status": ["status", "state", "workflow state"],
    "type": ["issue type", "type", "issuetype"],
    "labels": ["labels", "label"],
}
DROPPED_STATUSES = {"canceled", "cancelled", "duplicate", "won't do", "wont do", "won't fix",
                    "obsolete"}


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




BROAD_ID = r"[A-Z]{1,4}-?\d+(?:\.\d+)?"
MOSCOW = {"m": "M", "must": "M", "s": "S", "should": "S", "c": "C", "could": "C",
          "w": "W", "won't": "W", "wont": "W", "won't have": "W"}


def slugify(text: str) -> str:
    t = re.sub(r"[^\w\- ]+", "", text.strip().lower())
    return re.sub(r"\s+", "-", t)


def parse_doc(path: Path, id_pattern: str, headings: bool) -> dict:
    """Return {"sections": {id: {...}}, "required": [ids], "mode": "ids"|"headings"}."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        die("cannot read {}: {}".format(path, e))
    try:
        req_re = re.compile(r"^(?:{})$".format(id_pattern))
    except re.error as e:
        die("--id-pattern is not a valid regex: {}".format(e))
    broad = re.compile(r"^(?:{})$".format(BROAD_ID))
    sections = {}
    current_heading = ""
    in_fence = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", s)
        if hm:
            current_heading = hm.group(2).strip()
            if headings and len(hm.group(1)) in (2, 3):
                slug = slugify(current_heading)
                sections[slug] = {"id": slug, "text": current_heading, "moscow": "",
                                  "heading": current_heading}
            first = re.match(r"^\**({})\**\b[\s:.\-—]*(.*)$".format(BROAD_ID), current_heading)
            if first and not headings:
                sections.setdefault(first.group(1), {"id": first.group(1), "text": first.group(2),
                                                     "moscow": "", "heading": current_heading})
            continue
        if s.startswith("|"):
            cells = [c.strip().strip("*").strip() for c in s.strip("|").split("|")]
            if cells and broad.match(cells[0]):
                moscow = ""
                for c in cells[2:]:
                    if c.lower() in MOSCOW:
                        moscow = MOSCOW[c.lower()]
                        break
                sections.setdefault(cells[0], {"id": cells[0], "text": cells[1] if len(cells) > 1 else "",
                                               "moscow": moscow, "heading": current_heading})
            continue
        lm = re.match(r"^[-*]\s+\**({})\**[\s:.\-—]+(.*)$".format(BROAD_ID), s)
        if lm and not headings:
            sections.setdefault(lm.group(1), {"id": lm.group(1), "text": lm.group(2),
                                              "moscow": "", "heading": current_heading})
    if headings:
        required = [k for k in sections]
    else:
        required = [k for k, v in sections.items() if req_re.match(k) and v["moscow"] != "W"]
    return {"sections": sections, "required": required, "mode": "headings" if headings else "ids",
            "wont": [k for k, v in sections.items() if v["moscow"] == "W"]}


def source_line(spec: dict, item: dict, doc_info) -> str:
    ref = spec.get("doc_url") or spec.get("doc") or "the brief"
    src = item["source"]
    anchor = slugify(src)
    if doc_info and src in doc_info["sections"] and doc_info["mode"] == "ids":
        anchor = slugify(doc_info["sections"][src]["heading"]) or anchor
    return "Source: {}#{} ({})".format(ref, anchor, src)


def full_description(spec: dict, item: dict, doc_info) -> str:
    parts = [item["description"].strip()]
    ac = item.get("acceptance_criteria") or []
    if ac:
        parts.append("Acceptance criteria:\n" + "\n".join("- " + a for a in ac))
    parts.append(source_line(spec, item, doc_info))
    return "\n\n".join(parts)


def check_spec(spec: dict, doc_info) -> list:
    errors = []
    items = spec.get("items")
    if not isinstance(items, list) or not items:
        return ["spec needs a non-empty 'items' list"]
    ids = [it.get("id") for it in items if isinstance(it, dict)]
    dupes = sorted({i for i in ids if i and ids.count(i) > 1})
    if dupes:
        errors.append("duplicate item ids: " + ", ".join(dupes))
    for n, it in enumerate(items, 1):
        if not isinstance(it, dict):
            errors.append("item {} is not an object".format(n))
            continue
        name = it.get("id") or "item {}".format(n)
        for f in ("id", "type", "title", "description", "source"):
            if not str(it.get(f) or "").strip():
                errors.append("{}: missing '{}'".format(name, f))
        t = str(it.get("type") or "").lower()
        if t not in ("epic", "story", "task", "bug"):
            errors.append("{}: type must be epic, story, task or bug, not {!r}".format(name, it.get("type")))
        if t in ("story", "task") and not it.get("acceptance_criteria"):
            errors.append("{}: a {} needs acceptance_criteria".format(name, t))
        if it.get("acceptance_criteria") is not None and not isinstance(it.get("acceptance_criteria"), list):
            errors.append("{}: acceptance_criteria must be a list of strings".format(name))
        if it.get("labels") is not None and not isinstance(it.get("labels"), list):
            errors.append("{}: labels must be a list".format(name))
        for lab in it.get("labels") or []:
            if " " in str(lab):
                errors.append("{}: label {!r} has a space; Jira labels can't".format(name, lab))
        parent = it.get("parent")
        if parent:
            if parent not in ids:
                errors.append("{}: parent {!r} is not an item in the spec".format(name, parent))
            elif t == "epic":
                errors.append("{}: an epic can't have a parent".format(name))
        if doc_info and it.get("source") and it["source"] not in doc_info["sections"]:
            errors.append("{}: source {!r} is not a section in the doc".format(name, it["source"]))
        if doc_info and it.get("source") in doc_info.get("wont", []):
            errors.append("{}: source {!r} is marked Won't have in the doc".format(name, it["source"]))
    return errors


def cmd_export(args) -> int:
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except OSError as e:
        die("cannot read {}: {}".format(args.spec, e))
    except json.JSONDecodeError as e:
        die("{} is not valid JSON: {}".format(args.spec, e))
    if not isinstance(spec, dict):
        die("spec must be a JSON object with an 'items' list")
    doc_info = parse_doc(args.doc, args.id_pattern, args.headings)
    errors = check_spec(spec, doc_info)
    if errors:
        sys.stderr.write("spec has {} problem(s):\n".format(len(errors)))
        for e in errors:
            sys.stderr.write("  - " + e + "\n")
        return 1
    items = spec["items"]
    # Epics first so importers that resolve parents in order can find them.
    items = sorted(items, key=lambda it: 0 if it["type"].lower() == "epic" else 1)
    by_id = {it["id"]: it for it in items}
    out = io.StringIO()
    if args.target == "github":
        out.write("#!/usr/bin/env bash\n# Generated by brief_sync.py from {}. Review before running.\n".format(args.spec.name))
        out.write("# Creates any missing labels, then the issues. Run from inside the target repo.\nset -euo pipefail\n")
        has_epics = any(it["type"].lower() == "epic" for it in items)
        labels = sorted({lab for it in items for lab in (it.get("labels") or [])} | ({"epic"} if has_epics else set()))
        for lab in labels:
            out.write("gh label create {} --force >/dev/null\n".format(shlex.quote(lab)))
        for it in items:
            body = full_description(spec, it, doc_info)
            if it.get("parent"):
                body = "Part of: {} ({})\n\n".format(by_id[it["parent"]]["title"], it["parent"]) + body
            cmd = ["gh", "issue", "create", "--title", it["title"], "--body", body]
            for lab in (it.get("labels") or []) + (["epic"] if it["type"].lower() == "epic" else []):
                cmd += ["--label", lab]
            out.write(" ".join(shlex.quote(c) for c in cmd) + "\n")
        if has_epics:
            out.write("# Epics are created as issues labelled 'epic'. Add their children as sub-issues in GitHub afterwards.\n")
        text = out.getvalue()
    else:
        w = csv.writer(out)
        max_labels = max([len(it.get("labels") or []) for it in items] + [1])
        if args.target == "jira":
            w.writerow(["Issue Id", "Parent Id", "Issue Type", "Summary", "Description"] + ["Labels"] * max_labels)
            num = {x["id"]: i for i, x in enumerate(items, 1)}
            for it in items:
                labs = list(it.get("labels") or []) + [""] * (max_labels - len(it.get("labels") or []))
                w.writerow([num[it["id"]], num.get(it.get("parent"), "") if it.get("parent") else "",
                            it["type"].capitalize(), it["title"], full_description(spec, it, doc_info)] + labs)
        else:
            w.writerow(["ID", "Type", "Title", "Description", "Acceptance criteria", "Labels", "Parent ID",
                        "Parent title", "Source"])
            for it in items:
                w.writerow([it["id"], it["type"].capitalize(), it["title"],
                            it["description"].strip() + "\n\n" + source_line(spec, it, doc_info),
                            "\n".join(it.get("acceptance_criteria") or []), ", ".join(it.get("labels") or []),
                            it.get("parent") or "", by_id[it["parent"]]["title"] if it.get("parent") else "",
                            source_line(spec, it, doc_info)])
        text = out.getvalue()
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        n_epics = sum(1 for it in items if it["type"].lower() == "epic")
        sys.stderr.write("wrote {}: {} items ({} epics, {} others)\n".format(
            args.output, len(items), n_epics, len(items) - n_epics))
    else:
        sys.stdout.write(text)
    return 0


def cmd_drift(args) -> int:
    doc_info = parse_doc(args.doc, args.id_pattern, args.headings)
    if not doc_info["sections"]:
        die("found no sections in {}. Use --headings, or --id-pattern to match your requirement IDs".format(args.doc))
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
    mp = build_mapping(headers, {})
    if "title" not in mp:
        die("no title column found. Columns are: " + ", ".join(headers))

    def g(row, field):
        col = mp.get(field)
        return (row.get(col) or "").strip() if col else ""

    sections = doc_info["sections"]
    mention_re = re.compile(r"(?<![\w-])({})(?![\w-])".format(args.id_pattern)) if doc_info["mode"] == "ids" else None
    src_re = re.compile(r"Source:[^\n]*\(([^)\n]+)\)\s*$", re.M)
    issues = []
    for i, r in enumerate(rows, 1):
        text = "\n".join([g(r, "title"), g(r, "description"), g(r, "labels")])
        refs = src_re.findall(g(r, "description"))
        how = "source line" if refs else ""
        if not refs and mention_re:
            refs = sorted(set(m.group(1) for m in mention_re.finditer(text)))
            how = "mention" if refs else ""
        issues.append({"key": g(r, "key") or "row-{}".format(i), "title": g(r, "title"),
                       "status": g(r, "status"), "type": g(r, "type"),
                       "dropped": g(r, "status").lower() in DROPPED_STATUSES,
                       "refs": [x.strip() for x in refs], "how": how})

    live = [it for it in issues if not it["dropped"]]
    covered = {}
    for it in live:
        for ref in it["refs"]:
            covered.setdefault(ref, []).append(it)
    uncovered = [s for s in doc_info["required"] if s not in covered]
    orphans = [it for it in live if not it["refs"]]
    dangling = [(it, ref) for it in live for ref in it["refs"] if ref not in sections]
    wont = [(it, ref) for it in live for ref in it["refs"] if ref in doc_info["wont"]]
    by_mention = [it for it in live if it["how"] == "mention"]

    L = []
    L.append("# Drift: {} vs {}".format(args.doc.name, args.export.name))
    L.append("")
    L.append("{} sections in the doc ({} need an issue{}) · {} issues in the export ({} canceled or duplicate, ignored)".format(
        len(sections), len(doc_info["required"]),
        ", {} marked Won't have".format(len(doc_info["wont"])) if doc_info["wont"] else "",
        len(issues), len(issues) - len(live)))
    L.append("Sections are {}.".format("## and ### headings" if doc_info["mode"] == "headings"
                                       else "IDs matching `{}`".format(args.id_pattern)))
    L.append("")
    L.append("| Drift | Count |")
    L.append("|---|---:|")
    L.append("| Doc sections with no issue | {} |".format(len(uncovered)))
    L.append("| Issues with no doc section | {} |".format(len(orphans)))
    L.append("| Issues pointing at a section the doc doesn't have | {} |".format(len(dangling)))
    L.append("| Issues for a Won't-have requirement | {} |".format(len(wont)))
    L.append("")
    L.append("## Doc sections with no issue")
    L.append("")
    if uncovered:
        for s in uncovered:
            v = sections[s]
            L.append("- {}{}: {}".format(s, " ({})".format(v["moscow"]) if v["moscow"] else "", v["text"]))
    else:
        L.append("None.")
    L.append("")
    L.append("## Issues with no doc section")
    L.append("")
    if orphans:
        for it in orphans:
            L.append("- {} {} ({}{})".format(it["key"], it["title"], it["status"] or "no status",
                                             ", " + it["type"] if it["type"] else ""))
    else:
        L.append("None.")
    L.append("")
    L.append("## Issues pointing at a section the doc doesn't have")
    L.append("")
    if dangling:
        for it, ref in dangling:
            L.append("- {} {}: points at {}".format(it["key"], it["title"], ref))
    else:
        L.append("None.")
    L.append("")
    if wont:
        L.append("## Issues for a Won't-have requirement")
        L.append("")
        for it, ref in wont:
            L.append("- {} {}: {} is Won't have in the doc".format(it["key"], it["title"], ref))
        L.append("")
    L.append("## Coverage")
    L.append("")
    L.append("| Section | MoSCoW | Issues |")
    L.append("|---|---|---|")
    for s, v in sections.items():
        if s in doc_info["required"] or s in covered or s in doc_info["wont"]:
            cell = ", ".join("{} ({})".format(it["key"], it["status"] or "?") for it in covered.get(s, [])) or "-"
            L.append("| {} | {} | {} |".format(s, v["moscow"] or "-", cell))
    L.append("")
    if by_mention:
        L.append("Linked by mentioning the ID rather than a Source line (check these): " +
                 ", ".join(it["key"] for it in by_mention))
        L.append("")
    text = "\n".join(L) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        sys.stderr.write("wrote {}\n".format(args.output))
    else:
        sys.stdout.write(text)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Keep a tracker in step with a brief or PRD.")
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("export", help="issues spec JSON -> tracker import file")
    e.add_argument("spec", type=Path)
    e.add_argument("--target", choices=("jira", "csv", "github"), required=True)
    e.add_argument("--doc", type=Path, required=True,
                   help="the brief or PRD; every source must exist in it")
    e.add_argument("-o", "--output", type=Path)
    d = sub.add_parser("drift", help="doc vs tracker export -> drift report")
    d.add_argument("--doc", type=Path, required=True)
    d.add_argument("--export", type=Path, required=True)
    d.add_argument("-o", "--output", type=Path)
    for p in (e, d):
        p.add_argument("--id-pattern", default=r"R\d+",
                       help="regex for requirement IDs that need an issue (default R\\d+)")
        p.add_argument("--headings", action="store_true",
                       help="use ## and ### headings as sections instead of requirement IDs")
    args = ap.parse_args(argv)
    if args.cmd == "export":
        if not args.doc.exists():
            die("{} does not exist".format(args.doc))
        if not args.spec.exists():
            die("{} does not exist".format(args.spec))
        return cmd_export(args)
    if args.cmd == "drift":
        if not args.doc.exists():
            die("{} does not exist".format(args.doc))
        return cmd_drift(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build the graph of decisions behind a codebase, and check it is still true.

Reads decision records (ADRs, RFCs, design decisions) as Markdown, finds each one's id, title,
status and date, and the edges between them: what supersedes or amends what, which records cite
which, the files and folders each one governs, and, with --git, the commits that mention it.
Then it checks the graph for what goes wrong as a codebase ages: a supersession only one side
records, a current decision pointing at code that is gone, two current decisions governing the
same path, references to records that don't exist.

  python3 context_graph.py                          # find records under ./docs, check them
  python3 context_graph.py --root repo --git        # and the commits that mention each record
  python3 context_graph.py --why src/auth/session.py
  python3 context_graph.py --record ADR-0004
  python3 context_graph.py --docs architecture/decisions --json -o graph.json --mermaid graph.mmd

Exit codes: 0 the records are consistent (warnings allowed) or the query was answered; 1 the
check found problems; 2 the input can't be read (no records, an unknown --record id).
Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_DIRS = ["docs/adr", "docs/adrs", "docs/decisions", "docs/architecture/decisions", "doc/adr",
                "doc/architecture/decisions", "adr", "adrs", "decisions", "architecture/decisions",
                "docs/rfcs", "docs/rfc", "rfcs", "rfc", "docs/design", "docs/designs"]
CURRENT = {"accepted", "implemented", "active", "approved"}
STATUS_WORDS = {
    "proposed": "proposed", "draft": "proposed", "rfc": "proposed", "open": "proposed", "review": "proposed",
    "accepted": "accepted", "approved": "accepted", "agreed": "accepted", "adopted": "accepted", "active": "accepted",
    "implemented": "implemented", "done": "implemented", "shipped": "implemented",
    "rejected": "rejected", "declined": "rejected", "withdrawn": "rejected",
    "deprecated": "deprecated", "retired": "deprecated", "obsolete": "deprecated",
    "superseded": "superseded", "replaced": "superseded",
}
# RFC 2119 and RFC 8174 define MUST and SHOULD; decision records cite them for their wording.
IETF_KEYWORD_RFCS = {"RFC-2119", "RFC-8174"}
ID_RE = re.compile(r"\b(ADR|RFC|DR|DD)[ _-]?0*(\d{1,5})\b", re.I)
SUPERSEDES_RE = re.compile(r"\b(supersedes|replaces)\b[:\s]*((?:\[?(?:ADR|RFC|DR|DD)[ _-]?\d+\]?(?:\([^)]*\))?[\s,and&]*)+)", re.I)
SUPERSEDED_BY_RE = re.compile(r"\b(superseded|replaced)\s+by\b[:\s]*((?:\[?(?:ADR|RFC|DR|DD)[ _-]?\d+\]?(?:\([^)]*\))?[\s,and&]*)+)", re.I)
AMENDS_RE = re.compile(r"\bamends\b[:\s]*((?:\[?(?:ADR|RFC|DR|DD)[ _-]?\d+\]?(?:\([^)]*\))?[\s,and&]*)+)", re.I)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
CODE_RE = re.compile(r"`([^`\s]{2,200})`")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
PATHISH = re.compile(r"^(?:\./)?[A-Za-z0-9_.@-]+(?:/[A-Za-z0-9_.@*-]+)*/?$")


class InputError(Exception):
    pass


def norm_id(prefix, num):
    return "%s-%04d" % (prefix.upper(), int(num))


def ids_in(text):
    return [norm_id(m.group(1), m.group(2)) for m in ID_RE.finditer(text)]


def kind_of(path):
    """ADR, RFC or DR, from the folder names only (a file called use-rfc3339.md is not an RFC)."""
    parts = [x.lower() for x in path.replace("\\", "/").split("/")[:-1]]
    if any(re.fullmatch(r"rfcs?", x) for x in parts):
        return "RFC"
    if any(re.fullmatch(r"adrs?|decisions?|architecture-decisions", x) for x in parts):
        return "ADR"
    return "DR"


def frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta, key = {}, None
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, _, v = line.partition(":")
            key = k.strip().lower().replace("-", "_")
            meta[key] = v.split("#", 1)[0].strip().strip("'\"")
        elif key and re.match(r"^\s*-\s+\S", line):  # a block-style list under the last key
            item = line.split("-", 1)[1].split("#", 1)[0].strip().strip("'\"")
            meta[key] = (meta[key] + ", " + item) if meta[key] else item
    return meta, text[end + 4:]


def status_of(meta, body):
    """(normalised status, the raw words) from frontmatter, a 'Status:' line or a ## Status section."""
    raw = meta.get("status", "")
    if not raw:
        m = re.search(r"^\s*(?:[*-]\s+)?(?:\*\*|__)?status(?:\*\*|__)?\s*[:\-]\s*(?:\*\*|__)?\s*(.+)$", body, re.I | re.M)
        if m:
            raw = m.group(1)
    if not raw:
        m = re.search(r"^#{1,4}\s*status\s*$\s*^(.+)$", body, re.I | re.M)
        if not m:
            m = re.search(r"^#{1,4}\s*status\s*\n\s*\n?\s*(.+)$", body, re.I | re.M)
        if m:
            raw = m.group(1)
    raw = re.sub(r"[*_`]", "", raw).strip()
    first = re.split(r"[\s,;.(]+", raw.lower(), maxsplit=1)[0] if raw else ""
    return STATUS_WORDS.get(first, "unknown" if not raw else "unrecognised"), raw


def title_of(meta, body, fallback):
    if meta.get("title"):
        return meta["title"]
    m = re.search(r"^#\s+(.+)$", body, re.M)
    if m:
        t = re.sub(r"^(?:ADR|RFC|DR|DD)[ _-]?\d+\s*[:.\-–—]\s*", "", m.group(1).strip(), flags=re.I)
        return t.strip() or fallback
    return fallback


def date_of(meta, body):
    for k in ("date", "created", "decided", "accepted"):
        m = DATE_RE.search(meta.get(k, ""))
        if m:
            return m.group(1)
    m = re.search(r"^\s*(?:[*-]\s+)?(?:\*\*)?date(?:\*\*)?\s*[:\-]\s*(?:\*\*)?\s*(\d{4}-\d{2}-\d{2})", body, re.I | re.M)
    if m:
        return m.group(1)
    head = "\n".join(body.splitlines()[:15])
    m = DATE_RE.search(head)
    return m.group(1) if m else ""


def list_ids(value):
    return ids_in(value) if value else []


def read(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read(), None
    except UnicodeDecodeError:
        return None, "is not UTF-8 text; it was skipped"
    except OSError as e:
        return None, "can't be read (%s); it was skipped" % e.strerror


def discover(root, docs):
    dirs = [os.path.join(root, d) for d in docs] if docs else \
        [os.path.join(root, d) for d in DEFAULT_DIRS if os.path.isdir(os.path.join(root, d))]
    missing = [d for d in dirs if not os.path.isdir(d)]
    if docs and missing:
        raise InputError("not a folder: %s" % ", ".join(os.path.relpath(d, root) for d in missing))
    files = []
    for d in dirs:
        for base, subdirs, names in os.walk(d):
            subdirs[:] = sorted(s for s in subdirs if not s.startswith("."))
            for n in sorted(names):
                low = n.lower()
                if not low.endswith((".md", ".markdown")) or low in ("readme.md", "index.md", "_index.md") \
                        or "template" in low or re.match(r"^0+[-_.]", low):
                    continue
                files.append(os.path.join(base, n))
    return dirs, files


def parse_record(path, root, text):
    meta, body = frontmatter(text)
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    stem = os.path.splitext(os.path.basename(path))[0]
    kind = kind_of(rel)
    rid = None
    for k in ("id", "adr", "rfc"):
        if meta.get(k):
            found = ids_in(meta[k])
            rid = found[0] if found else (norm_id(k.upper() if k != "id" else kind, meta[k])
                                          if re.fullmatch(r"\d{1,5}", meta[k]) else None)
            if rid:
                break
    if not rid and not re.match(r"^\d{4}-\d{2}-\d{2}", stem):  # 2024-01-15-x.md is a date, not an id
        m = re.match(r"^(?:(adr|rfc|dr|dd)[ _-]?)?0*(\d{1,5})(?=[-_. ]|$)", stem, re.I)
        if m:
            rid = norm_id(m.group(1) or kind, m.group(2))
    if not rid:
        h = re.search(r"^#\s+(.+)$", body, re.M)
        found = ids_in(re.split(r"[:.\-–—]\s", h.group(1), maxsplit=1)[0]) if h else []
        if found:
            rid = found[0]
    if not rid:
        rid = "%s-%s" % (kind, re.sub(r"[^A-Za-z0-9]+", "-", stem).strip("-").lower() or "untitled")
    status, raw_status = status_of(meta, body)
    rec = {"id": rid, "title": title_of(meta, body, stem.replace("-", " ")), "status": status,
           "status_text": raw_status, "date": date_of(meta, body), "path": rel,
           "supersedes": [], "superseded_by": [], "amends": [], "cites": [], "governs": [],
           "missing_paths": [], "commits": []}
    rec["supersedes"] += list_ids(meta.get("supersedes", "")) + list_ids(meta.get("replaces", ""))
    rec["superseded_by"] += list_ids(meta.get("superseded_by", "")) + list_ids(meta.get("replaced_by", ""))
    rec["amends"] += list_ids(meta.get("amends", ""))
    for m in SUPERSEDES_RE.finditer(body):
        rec["supersedes"] += ids_in(m.group(2))
    for m in SUPERSEDED_BY_RE.finditer(body + "\n" + raw_status):
        rec["superseded_by"] += ids_in(m.group(2))
    for m in AMENDS_RE.finditer(body):
        rec["amends"] += ids_in(m.group(1))
    if rec["superseded_by"] and status in ("unknown", "unrecognised", "accepted"):
        if re.match(r"\s*(superseded|replaced)", raw_status, re.I):
            rec["status"] = "superseded"
    rec["cites"] = ids_in(body)
    rec["_links"] = [l for l in LINK_RE.findall(body) if not re.match(r"^[a-z]+:", l, re.I)]
    here = os.path.dirname(rel)
    linked = {os.path.normpath(os.path.join(here, l)).replace(os.sep, "/") for l in rec["_links"]
              if not l.lower().endswith((".md", ".markdown"))}
    rec["_paths"] = sorted(set(CODE_RE.findall(body)) | {l for l in linked if not l.startswith("..")})
    for k in ("supersedes", "superseded_by", "amends"):
        rec[k] = sorted(set(x for x in rec[k] if x != rid))
    return rec


def resolve_links(records, root):
    by_path = {r["path"]: r["id"] for r in records}
    for r in records:
        here = os.path.dirname(r["path"])
        for l in r.pop("_links"):
            target = os.path.normpath(os.path.join(here, l)).replace(os.sep, "/")
            if target in by_path and by_path[target] != r["id"]:
                r["cites"].append(by_path[target])
        r["cites"] = sorted(set(c for c in r["cites"] if c != r["id"]))


def resolve_paths(records, root, record_paths):
    top = {n for n in os.listdir(root) if not n.startswith(".")}
    for r in records:
        for tok in r.pop("_paths"):
            t = tok.strip().rstrip(".,;:")
            while t.startswith("./"):
                t = t[2:]
            t = t.lstrip("/")
            if not t or not PATHISH.match(t) or t.startswith(("http", "www.")) or "/" not in t and "." not in t:
                continue
            if t in record_paths or t.lower().endswith((".md", ".markdown")) and t not in record_paths and "/" not in t:
                continue
            if "*" in t:
                t = t.split("*", 1)[0].rstrip("/")
                if not t:
                    continue
            full = os.path.join(root, t)
            if os.path.exists(full):
                r["governs"].append(t.rstrip("/") + ("/" if os.path.isdir(full) else ""))
            elif t.split("/", 1)[0] in top and "/" in t:
                r["missing_paths"].append(t.rstrip("/"))
        r["governs"] = sorted(set(r["governs"]))
        r["missing_paths"] = sorted(set(r["missing_paths"]))


def git_commits(root, records, limit):
    try:
        out = subprocess.run(["git", "-C", root, "log", "-n", str(limit), "--date=short",
                              "--format=%h%x1f%ad%x1f%s%x1f%b%x1e"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "git is not available, so no commits were read"
    if out.returncode != 0:
        return "not a git repository, so no commits were read"
    known = {r["id"]: r for r in records}
    for entry in out.stdout.split("\x1e"):
        parts = entry.strip("\n").split("\x1f")
        if len(parts) < 3:
            continue
        sha, date, subject = parts[0], parts[1], parts[2]
        body = parts[3] if len(parts) > 3 else ""
        for rid in sorted(set(ids_in(subject + "\n" + body))):
            if rid in known and len(known[rid]["commits"]) < 20:
                known[rid]["commits"].append({"sha": sha, "date": date, "subject": subject[:120]})
    return None


def check(records):
    """Findings: (severity, record id, message). Severity is 'problem' or 'warning'."""
    out = []
    by_id = {}
    # A citation of a kind the repo has no records of ("RFC 7231" in an ADR-only repo) is to an
    # outside document, not a missing record.
    kinds = {r["id"].split("-")[0] for r in records}
    for r in records:
        if r["id"] in by_id:
            out.append(("problem", r["id"], "two records use the id %s: %s and %s"
                        % (r["id"], by_id[r["id"]]["path"], r["path"])))
        else:
            by_id[r["id"]] = r
    succ = {}
    for r in records:
        for old in r["supersedes"]:
            succ.setdefault(old, set()).add(r["id"])
            o = by_id.get(old)
            if not o:
                out.append(("warning", r["id"], "supersedes %s, which isn't among the records" % old))
            elif o["status"] in CURRENT or o["status"] in ("unknown", "proposed"):
                out.append(("problem", old, "is still marked %s, but %s supersedes it: mark it 'Superseded by %s'"
                            % (o["status_text"] or o["status"], r["id"], r["id"])))
        for new in r["superseded_by"]:
            succ.setdefault(r["id"], set()).add(new)
            n = by_id.get(new)
            if not n:
                out.append(("problem", r["id"], "says it is superseded by %s, which isn't among the records" % new))
            elif r["id"] not in n["supersedes"]:
                out.append(("warning", r["id"], "says it is superseded by %s, but %s doesn't say it supersedes %s"
                            % (new, new, r["id"])))
        if r["status"] == "superseded" and not r["superseded_by"] and r["id"] not in succ:
            out.append(("warning", r["id"], "is marked superseded but names no successor"))
        if r["status"] == "unknown":
            out.append(("warning", r["id"], "has no status"))
        elif r["status"] == "unrecognised":
            out.append(("warning", r["id"], "has a status this doesn't recognise: %r" % r["status_text"]))
        for c in r["cites"]:
            if c not in by_id and c.split("-")[0] in kinds and c not in IETF_KEYWORD_RFCS:
                out.append(("warning", r["id"], "refers to %s, which isn't among the records" % c))
        if r["status"] in CURRENT and r["missing_paths"]:
            out.append(("problem", r["id"], "is %s but points at code that is gone: %s"
                        % (r["status"], ", ".join(r["missing_paths"]))))
    # a current record that leans on one that has since been superseded
    for r in records:
        if r["status"] not in CURRENT or r["id"] in succ:
            continue
        for c in r["cites"]:
            if c in succ and c not in r["supersedes"] and c in by_id and r["id"] not in succ[c]:
                out.append(("warning", r["id"], "is current but cites %s, which %s supersedes: check it still holds"
                            % (c, ", ".join(sorted(succ[c])))))
    # supersession cycles
    for start in by_id:
        seen, cur = [], start
        while cur in succ and cur not in seen:
            seen.append(cur)
            nxt = sorted(succ[cur])
            cur = nxt[0] if nxt else None
            if cur == start:
                out.append(("problem", start, "is in a supersession cycle: %s" % " -> ".join(seen + [start])))
                break
    # two current records on the same path, neither replacing nor amending the other
    current = [r for r in records if r["status"] in CURRENT]
    seen_pairs = set()
    for i, a in enumerate(current):
        for b in current[i + 1:]:
            linked = b["id"] in a["supersedes"] + a["amends"] or a["id"] in b["supersedes"] + b["amends"]
            if linked:
                continue
            # The same path, not nested scopes: a folder-wide decision and one about a file inside it
            # usually complement each other, and flagging every pair buries the real clashes.
            shared = sorted(set(a["governs"]) & set(b["governs"]))
            if shared and (a["id"], b["id"]) not in seen_pairs:
                seen_pairs.add((a["id"], b["id"]))
                out.append(("warning", a["id"], "and %s are both %s and both govern %s, and neither supersedes or "
                            "amends the other: read both before relying on either" % (b["id"], "current", ", ".join(shared))))
    order = {"problem": 0, "warning": 1}
    seen_msgs, uniq = set(), []
    for f in sorted(out, key=lambda f: (order[f[0]], f[1], f[2])):
        if f not in seen_msgs:
            seen_msgs.add(f)
            uniq.append(f)
    return uniq


def covers(gov, path):
    """True when a governed path (a file, or a folder ending in /) covers `path`."""
    g, p = gov.rstrip("/"), path.rstrip("/")
    return p == g or p.startswith(g + "/")


def why(records, path, root):
    p = os.path.relpath(os.path.join(root, path), root).replace(os.sep, "/") if not os.path.isabs(path) \
        else os.path.relpath(path, root).replace(os.sep, "/")
    hits = []
    for r in records:
        for g in r["governs"]:
            if covers(g, p):
                hits.append((r, g))
                break
    succ = {}
    for r in records:
        for old in r["supersedes"]:
            succ.setdefault(old, []).append(r["id"])
        for new in r["superseded_by"]:
            succ.setdefault(r["id"], []).append(new)
    rank = {"accepted": 0, "implemented": 0, "proposed": 1, "unknown": 2, "unrecognised": 2,
            "deprecated": 3, "superseded": 3, "rejected": 4}
    live = lambda r: r["status"] in CURRENT and not succ.get(r["id"])
    hits.sort(key=lambda h: (0 if live(h[0]) else 1, rank.get(h[0]["status"], 2),
                             -int(h[0]["date"].replace("-", "") or 0)))
    return p, [{"id": r["id"], "title": r["title"], "status": r["status"], "date": r["date"], "path": r["path"],
                "via": g, "superseded_by": sorted(set(succ.get(r["id"], []))), "current": live(r)} for r, g in hits]


def mermaid(records):
    lines = ["flowchart LR"]
    safe = lambda i: re.sub(r"[^A-Za-z0-9_]", "_", i)
    for r in records:
        succ = r.get("successors") or []
        state = ("superseded by %s" % ", ".join(succ)) if succ else r["status"]
        label = ("%s %s (%s)" % (r["id"], r["title"][:48], state)).replace('"', "'")
        style = ":::gone" if succ or r["status"] in ("superseded", "deprecated", "rejected") else ""
        lines.append('  %s["%s"]%s' % (safe(r["id"]), label, style))
    ids = {r["id"] for r in records}
    for r in records:
        for old in r["supersedes"]:
            if old in ids:
                lines.append("  %s -->|supersedes| %s" % (safe(r["id"]), safe(old)))
        for a in r["amends"]:
            if a in ids:
                lines.append("  %s -.->|amends| %s" % (safe(r["id"]), safe(a)))
        for c in r["cites"]:
            if c in ids and c not in r["supersedes"] and c not in r["amends"]:
                lines.append("  %s -.- %s" % (safe(r["id"]), safe(c)))
    lines.append("  classDef gone fill:#eee,color:#666,stroke-dasharray: 4 3")
    return "\n".join(lines) + "\n"


def report(records, findings, note, query, dirs, root):
    out = []
    probs = [f for f in findings if f[0] == "problem"]
    warns = [f for f in findings if f[0] == "warning"]
    if query and query["kind"] == "why":
        out.append("# Decisions governing %s\n" % query["path"])
        cur = [h for h in query["hits"] if h["current"]]
        if not query["hits"]:
            out.append("No decision record governs %s or a folder above it. Any rationale for it is "
                       "unrecorded.\n" % query["path"])
        else:
            for h in query["hits"]:
                if h["superseded_by"] and h["status"] in CURRENT:
                    state = "marked %s, but superseded by %s" % (h["status"], ", ".join(h["superseded_by"]))
                elif h["superseded_by"]:
                    state = "%s by %s" % (h["status"], ", ".join(h["superseded_by"]))
                else:
                    state = h["status"] + (", current" if h["current"] else "")
                out.append("- **%s %s** (%s%s), via `%s`: %s" % (
                    h["id"], h["title"], state, ", " + h["date"] if h["date"] else "", h["via"], h["path"]))
            if not cur:
                out.append("\nNone of these is current: the decisions that governed it were superseded, "
                           "deprecated or never accepted.")
        out.append("")
    elif query and query["kind"] == "record":
        r = query["record"]
        out.append("# %s %s\n" % (r["id"], r["title"]))
        out.append("- Status: %s%s" % (r["status"], (" (%s)" % r["status_text"]) if r["status_text"] and
                                         r["status_text"].lower() != r["status"] else ""))
        for k, label in (("date", "Date"), ("path", "File")):
            if r[k]:
                out.append("- %s: %s" % (label, r[k]))
        if r["successors"]:
            one_sided = r["successors_only_claimed_by_successor"]
            out.append("- Superseded by: %s%s" % (", ".join(r["successors"]),
                       (" (only %s says so; this record doesn't)" % ", ".join(one_sided)) if one_sided else ""))
        for k, label in (("supersedes", "Supersedes"), ("amends", "Amends"),
                         ("cited_by", "Cited by"), ("cites", "Cites"), ("governs", "Governs"),
                         ("missing_paths", "Points at paths that are gone")):
            if r.get(k):
                out.append("- %s: %s" % (label, ", ".join(r[k])))
        for c in r["commits"]:
            out.append("- Commit %s %s: %s" % (c["sha"], c["date"], c["subject"]))
        out.append("")
    counts = {}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out.append("## Records\n")
    out.append("%d record(s) in %s: %s." % (len(records), ", ".join(os.path.relpath(d, root).replace(os.sep, "/")
                                                                   for d in dirs) or "-",
                                            ", ".join("%d %s" % (n, s) for s, n in sorted(counts.items()))))
    if note:
        out.append(note[0].upper() + note[1:] + ".")
    out.append("\n## Problems (%d)\n" % len(probs))
    out += ["- %s %s" % (rid, msg) for _, rid, msg in probs] or ["None."]
    out.append("\n## Warnings (%d)\n" % len(warns))
    out += ["- %s %s" % (rid, msg) for _, rid, msg in warns] or ["None."]
    if not query:
        out.append("\n## Graph\n")
        out.append("| Record | Status | Date | Supersedes | Superseded by | Governs |")
        out.append("|---|---|---|---|---|---|")
        for r in records:
            out.append("| %s %s | %s | %s | %s | %s | %s |" % (
                r["id"], r["title"].replace("|", "/")[:60], r["status"], r["date"] or "-",
                ", ".join(r["supersedes"]) or "-", ", ".join(r["superseded_by"]) or "-",
                ", ".join("`%s`" % g for g in r["governs"][:4]) + (" …" if len(r["governs"]) > 4 else "") or "-"))
    return "\n".join(out) + "\n"


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Build and check the graph of decisions behind a codebase.")
    ap.add_argument("--root", default=".", help="the repository root (default: the current folder)")
    ap.add_argument("--docs", action="append", metavar="DIR",
                    help="a folder of decision records, relative to --root; repeatable (default: common ADR/RFC folders)")
    q = ap.add_mutually_exclusive_group()
    q.add_argument("--why", metavar="PATH", help="list the decisions that govern a file or folder")
    q.add_argument("--record", metavar="ID", help="show one record and its neighbours, e.g. ADR-0004")
    ap.add_argument("--git", action="store_true", help="also read commit messages for record ids")
    ap.add_argument("--git-limit", type=int, default=5000)
    ap.add_argument("--json", action="store_true", help="print the graph as JSON instead of Markdown")
    ap.add_argument("--mermaid", metavar="FILE", help="also write a Mermaid flowchart of the graph")
    ap.add_argument("-o", "--output", metavar="FILE", help="write the report here instead of stdout")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        raise InputError("--root is not a folder: %s" % a.root)
    dirs, files = discover(root, a.docs)
    if not files:
        raise InputError("no decision records found%s; pass --docs <folder> where your ADRs or RFCs live"
                         % ((" in " + ", ".join(a.docs)) if a.docs else " in the usual folders (docs/adr, docs/decisions, docs/rfcs …)"))
    records, skipped = [], []
    for f in files:
        text, err = read(f)
        if text is None:
            skipped.append("%s %s" % (os.path.relpath(f, root).replace(os.sep, "/"), err))
            continue
        records.append(parse_record(f, root, text))
    if not records:
        raise InputError("none of the %d record file(s) could be read: %s" % (len(files), "; ".join(skipped)))
    resolve_links(records, root)
    resolve_paths(records, root, {r["path"] for r in records})
    notes = list(skipped)
    if a.git:
        n = git_commits(root, records, a.git_limit)
        if n:
            notes.append(n)
    findings = check(records)
    cited_by = {}
    for r in records:
        for c in r["cites"]:
            cited_by.setdefault(c, []).append(r["id"])
    for r in records:
        r["cited_by"] = sorted(set(cited_by.get(r["id"], [])))
    # Successors from both directions: a record's own "superseded by", and every record that says it
    # supersedes this one (often only the newer record says so).
    for r in records:
        claimed = [o["id"] for o in records if r["id"] in o["supersedes"]]
        r["successors"] = sorted(set(r["superseded_by"]) | set(claimed))
        r["successors_only_claimed_by_successor"] = sorted(set(claimed) - set(r["superseded_by"]))

    query = None
    if a.why:
        p, hits = why(records, a.why, root)
        query = {"kind": "why", "path": p, "hits": hits}
    elif a.record:
        want = ids_in(a.record)
        rid = want[0] if want else a.record
        match = [r for r in records if r["id"].lower() == rid.lower()]
        if not match:
            raise InputError("no record %s; the records are %s" % (a.record, ", ".join(r["id"] for r in records[:30])))
        query = {"kind": "record", "record": match[0]}

    if a.mermaid:
        with open(a.mermaid, "w", encoding="utf-8") as fh:
            fh.write(mermaid(records))
    if a.json:
        text = json.dumps({"root": root, "records": records,
                           "findings": [{"severity": s, "record": i, "message": m} for s, i, m in findings],
                           "notes": notes, "query": query}, indent=1, default=str) + "\n"
    else:
        text = report(records, findings, "; ".join(notes), query, dirs, root)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    if query:
        return 0
    return 1 if any(f[0] == "problem" for f in findings) else 0


def main(argv=None):
    try:
        return _main(argv)
    except InputError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except OSError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

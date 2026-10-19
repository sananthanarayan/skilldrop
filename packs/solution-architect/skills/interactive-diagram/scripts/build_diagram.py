#!/usr/bin/env python3
"""Render a diagram spec (JSON) into one self-contained, explorable HTML file.

The spec says what is on the map and where each part came from; this script does the rest:
it checks the spec, verifies every cited file and line against the repository, lays the
diagram out (nobody writes coordinates), and writes an HTML file with no external requests:
pan and zoom, click for detail and evidence, upstream/downstream reach, path between two
parts, search, a step-through tour, light and dark themes, and SVG / PNG / Mermaid export.
The same content is in the page as plain text, so it reads without JavaScript.

  python3 build_diagram.py spec.json -o map.html
  python3 build_diagram.py spec.json -o map.html --repo-root .        # verify file:line evidence
  python3 build_diagram.py spec.json --check                          # validate only
  python3 build_diagram.py head.json -o diff.html --compare base.json # what changed
  python3 build_diagram.py spec.json -o map.html --mermaid map.mmd    # also write Mermaid

Standard library only, Python 3.9+. Exit 0 when the HTML was written (warnings allowed),
1 when the spec has errors (nothing written), 2 for usage errors.
"""
import argparse
import base64
import datetime
import hashlib
import html
import json
import math
import os
import re
import sys

TYPES = ("architecture", "workflow", "dataflow", "lifecycle", "erd", "sequence", "tree", "timeline", "waterfall", "class")

# kind -> (shape, colour family). Unknown kinds fall back to a plain box, with a warning.
KINDS = {
    "service": ("rect", "blue"), "app": ("rect", "blue"), "function": ("rect", "blue"),
    "ui": ("rect", "violet"), "client": ("rect", "violet"),
    "datastore": ("cylinder", "green"), "database": ("cylinder", "green"),
    "cache": ("cylinder", "teal"), "storage": ("cylinder", "green"),
    "queue": ("pipe", "amber"), "topic": ("pipe", "amber"), "stream": ("pipe", "amber"),
    "external": ("rect", "slate"), "person": ("person", "rose"), "actor": ("person", "rose"),
    "job": ("rect", "indigo"), "worker": ("rect", "indigo"),
    "step": ("rect", "blue"), "task": ("rect", "blue"), "manual": ("rect", "rose"),
    "decision": ("diamond", "amber"), "document": ("document", "teal"),
    "start": ("terminal", "green"), "end": ("terminal", "slate"),
    "state": ("round", "blue"), "final": ("final", "slate"), "initial": ("initial", "slate"),
    "table": ("table", "green"), "entity": ("table", "green"), "view": ("table", "teal"),
    "security": ("rect", "rose"), "network": ("rect", "slate"), "file": ("document", "teal"),
    "folder": ("rect", "slate"), "module": ("rect", "blue"), "package": ("rect", "indigo"),
    "capability": ("round", "teal"), "feature": ("round", "blue"), "team": ("rect", "rose"), "role": ("rect", "violet"),
    "event": ("dot", "blue"), "milestone": ("dot", "violet"), "alert": ("dot", "rose"), "change": ("dot", "amber"),
    "action": ("dot", "green"), "span": ("bar", "blue"),
    "class": ("classbox", "blue"), "interface": ("classbox", "violet"), "abstract": ("classbox", "indigo"),
    "enum": ("classbox", "amber"), "record": ("classbox", "teal"),
}
RELATIONS = ("inherits", "implements", "composition", "aggregation", "association", "dependency")
WORDS = {  # how the detail panel names a part's connections, per diagram type
    "default": {"out": "Goes to", "in": "Comes from", "reach_out": "Everything it reaches", "reach_in": "Everything that reaches it"},
    "workflow": {"out": "Goes to", "in": "Comes from", "reach_out": "What can follow", "reach_in": "What leads here"},
    "lifecycle": {"out": "Can move to", "in": "Can come from", "reach_out": "What can follow", "reach_in": "What leads here"},
    "erd": {"out": "References", "in": "Referenced by", "reach_out": "Tables it references", "reach_in": "Tables that reference it"},
    "sequence": {"out": "Sends to", "in": "Receives from", "reach_out": "Who it reaches", "reach_in": "Who reaches it"},
    "tree": {"out": "Contains", "in": "Inside", "reach_out": "Everything inside it", "reach_in": "What it sits in"},
    "timeline": {"out": "Led to", "in": "Followed from", "reach_out": "What followed", "reach_in": "What led to it"},
    "waterfall": {"out": "Child spans", "in": "Parent span", "reach_out": "Everything it spawned", "reach_in": "What it ran under"},
    "class": {"out": "Points to", "in": "Pointed to by", "reach_out": "What it uses or extends", "reach_in": "What uses or extends it"},
}
DEFAULT_KIND = {"architecture": "service", "workflow": "step", "dataflow": "service", "lifecycle": "state",
                "erd": "table", "sequence": "service", "tree": "module", "timeline": "event", "waterfall": "span",
                "class": "class"}
EDGE_STYLES = ("solid", "dashed", "dotted")
STATUSES = ("added", "removed", "changed")
SECRET_PATH = re.compile(r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|id_ed25519.*|credentials(\..*)?|"
                         r".*secrets?\.(json|ya?ml|toml)|\.npmrc|\.pypirc|\.netrc)$", re.I)
SECRET_LINE = re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|"
                         r"sk-[A-Za-z0-9_-]{20,}|xox[abp]-[A-Za-z0-9-]{10,}|"
                         r"(?i:(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?[^\s'\"]{6,}))")
MAX_SNIPPET_LINES = 14
MAX_SNIPPET_TOTAL = 80000


# --------------------------------------------------------------------------- spec checks

class Issues(object):
    def __init__(self):
        self.items = []

    def add(self, level, code, where, message, fix=""):
        self.items.append({"level": level, "code": code, "where": where, "message": message, "fix": fix})

    def error(self, *a):
        self.add("error", *a)

    def warn(self, *a):
        self.add("warning", *a)

    @property
    def errors(self):
        return [i for i in self.items if i["level"] == "error"]

    @property
    def warnings(self):
        return [i for i in self.items if i["level"] == "warning"]


EVIDENCE_RE = re.compile(r"^(?P<file>[^:#\s][^:#]*?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?(?:#(?P<quote>.+))?$")


def parse_evidence(ev):
    """Evidence is a file reference ("src/api.py:40-52#redis.get(") or something the person
    said ("user: we approve leave in the HR portal"). Objects with the same fields work too."""
    if isinstance(ev, dict):
        if "said" in ev:
            return {"said": str(ev["said"])}
        out = {"file": str(ev.get("file", ""))}
        lines = str(ev.get("lines", "") or "")
        m = re.match(r"^(\d+)(?:-(\d+))?$", lines)
        if m:
            out["start"], out["end"] = int(m.group(1)), int(m.group(2) or m.group(1))
        if ev.get("quote"):
            out["quote"] = str(ev["quote"])
        return out
    s = str(ev).strip()
    low = s.lower()
    for prefix in ("user:", "said:", "brief:", "doc:"):
        if low.startswith(prefix):
            return {"said": s[len(prefix):].strip().strip('"“”'), "source": prefix[:-1]}
    m = EVIDENCE_RE.match(s)
    if not m or not m.group("file"):
        return {"bad": s}
    out = {"file": m.group("file").strip()}
    if m.group("start"):
        out["start"] = int(m.group("start"))
        out["end"] = int(m.group("end") or m.group("start"))
    if m.group("quote"):
        out["quote"] = m.group("quote").strip()
    return out


def ev_text(e):
    if "said" in e:
        return "%s: “%s”" % (e.get("source", "user"), e["said"])
    if "file" in e:
        s = e["file"]
        if "start" in e:
            s += ":%d" % e["start"] + ("-%d" % e["end"] if e["end"] != e["start"] else "")
        return s
    return e.get("bad", "")


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def normalise(spec, issues):
    """Fill defaults and parse shorthand, collecting problems. Returns the normalised spec."""
    t = spec.get("type")
    if t not in TYPES:
        issues.error("spec/type", "type", "type is %r" % t, "Use one of: " + ", ".join(TYPES))
        t = "architecture"
    spec["type"] = t
    if not str(spec.get("title", "")).strip():
        issues.error("spec/title", "title", "the diagram has no title", "Add a title naming what the map shows.")
    spec.setdefault("question", "")
    spec.setdefault("summary", "")
    default_dir = "TB" if t == "class" else "LR"
    spec["direction"] = "TB" if str(spec.get("direction", default_dir)).upper() == "TB" and t not in ("erd", "sequence", "tree", "timeline", "waterfall") else "LR"
    if spec.get("source_url") and not re.match(r"^https?://[^\s\"'<>]+$", str(spec["source_url"])):
        issues.warn("spec/source-url", "source_url", "source_url is not an http(s) address; citations will not be links",
                    "Use the repository's https address, e.g. https://github.com/org/repo/blob/<commit>/")
    spec["groups"] = [dict(g) for g in as_list(spec.get("groups"))]
    spec["notes"] = as_list(spec.get("notes"))
    key = {"sequence": "participants", "timeline": "events", "waterfall": "spans", "class": "classes"}.get(t, "nodes")
    nodes = [dict(n) for n in as_list(spec.get(key) or spec.get("nodes"))]
    if not nodes:
        issues.error("spec/empty", key, "there is nothing to draw", "List the %s of the diagram." % key)
    spec["nodes"] = nodes
    spec["edges"] = [dict(e) for e in as_list(spec.get("messages" if t == "sequence" else "edges") or spec.get("relations"))]
    if t in ("tree", "waterfall") and spec["edges"]:
        issues.warn("edge/ignored", "edges", "a %s draws its connections from each item's parent; edges are ignored" % t,
                    "Set parent on each item instead.")
        spec["edges"] = []
    spec["frames"] = [dict(f) for f in as_list(spec.get("frames"))]
    spec["story"] = [dict(s) for s in as_list(spec.get("story"))]
    spec["answers"] = [dict(a) for a in as_list(spec.get("answers"))]
    for i, a in enumerate(spec["answers"]):
        a["id"] = "answer %d" % (i + 1)
        if not str(a.get("question", "")).strip() or not str(a.get("answer", "")).strip():
            issues.error("answer/shape", a["id"], "an answer needs question and answer", "")
        _evidence(a, a["id"], issues)

    ids = set()
    for g in spec["groups"]:
        gid = str(g.get("id", "")).strip()
        if not gid:
            issues.error("group/id", "groups", "a group has no id", "Give every group an id.")
            continue
        if gid in ids:
            issues.error("id/duplicate", gid, "the id %r is used twice" % gid, "Ids must be unique across groups, nodes and edges.")
        ids.add(gid)
        g["id"] = gid
        g["label"] = str(g.get("label") or gid)
    gids = {g["id"] for g in spec["groups"]}
    for g in spec["groups"]:
        if g.get("parent") and g["parent"] not in gids:
            issues.error("group/parent", g["id"], "parent group %r does not exist" % g["parent"], "Name an existing group or drop parent.")
            g["parent"] = None
    for g in spec["groups"]:  # a parent chain must end
        seen, cur = set(), g
        while cur and cur.get("parent"):
            if cur["id"] in seen:
                issues.error("group/cycle", g["id"], "group parents form a loop", "Remove one parent link.")
                g["parent"] = None
                break
            seen.add(cur["id"])
            cur = next((x for x in spec["groups"] if x["id"] == cur["parent"]), None)

    for n in nodes:
        nid = str(n.get("id", "")).strip()
        if not nid:
            issues.error("node/id", key, "a %s has no id" % key[:-1], "Give every %s an id." % key[:-1])
            nid = "_node%d" % len(ids)
        if nid in ids:
            issues.error("id/duplicate", nid, "the id %r is used twice" % nid, "Ids must be unique across groups, nodes and edges.")
        ids.add(nid)
        n["id"] = nid
        n["label"] = str(n.get("label") or nid)
        n["kind"] = str(n.get("kind") or DEFAULT_KIND[t]).lower()
        if n["kind"] not in KINDS:
            issues.warn("node/kind", nid, "kind %r is not one the renderer knows; drawn as a box" % n["kind"],
                        "Known kinds: " + ", ".join(sorted(KINDS)))
        if n.get("group") and n["group"] not in gids:
            issues.error("node/group", nid, "group %r does not exist" % n["group"], "Add the group or drop the field.")
            n["group"] = None
        n["fields"] = [f if isinstance(f, dict) else {"name": str(f)} for f in as_list(n.get("fields") or n.get("members"))]
        if len(n["label"]) > 48:
            issues.warn("node/label-long", nid, "label is %d characters; it will be cut on the map" % len(n["label"]),
                        "Keep labels to a few words and put the rest in note or detail.")
        _evidence(n, nid, issues)

    nid_set = {n["id"] for n in nodes}
    _check_kind(spec, t, nodes, nid_set, issues)
    for i, e in enumerate(spec["edges"]):
        where = e.get("id") or "%s %d" % ("message" if t == "sequence" else "edge", i + 1)
        if not e.get("id"):
            e["id"] = "m%d" % (i + 1) if t == "sequence" else "e%d" % (i + 1)
            while e["id"] in ids:
                e["id"] += "_"
        elif e["id"] in ids:
            issues.error("id/duplicate", e["id"], "the id %r is used twice" % e["id"], "Ids must be unique across groups, nodes and edges.")
        ids.add(e["id"])
        for end in ("from", "to"):
            if e.get(end) not in nid_set:
                issues.error("edge/endpoint", where, "%s %r is not a %s" % (end, e.get(end), key[:-1]),
                             "Use the id of an existing %s." % key[:-1])
        e["label"] = str(e.get("label") or "")
        if t == "class":
            rel = str(e.get("kind") or e.get("rel") or "association").lower()
            rel = {"extends": "inherits", "inheritance": "inherits", "realizes": "implements", "realises": "implements",
                   "uses": "dependency", "depends": "dependency", "has": "association", "references": "association",
                   "owns": "composition", "contains": "composition"}.get(rel, rel)
            if rel not in RELATIONS:
                issues.error("edge/relation", where, "relation %r is not one of %s" % (rel, ", ".join(RELATIONS)), "")
                rel = "association"
            e["rel"] = rel
            if rel in ("implements", "dependency") and not e.get("style"):
                e["style"] = "dashed"
        e["style"] = e.get("style") if e.get("style") in EDGE_STYLES else ("dashed" if e.get("kind") in ("async", "return") else "solid")
        _evidence(e, where, issues)
    for i, s in enumerate(spec["story"]):
        for ref in as_list(s.get("nodes")) + as_list(s.get("edges")):
            if ref not in ids:
                issues.error("story/ref", "story step %d" % (i + 1), "%r is not a node or edge id" % ref, "Point the step at ids on the map.")
    for i, f in enumerate(spec["frames"]):
        if t != "sequence":
            issues.warn("frame/type", "frames", "frames are drawn only on sequence diagrams", "Use groups instead.")
            break
        if f.get("from") not in [e["id"] for e in spec["edges"]] or f.get("to") not in [e["id"] for e in spec["edges"]]:
            issues.error("frame/range", "frame %d" % (i + 1), "a frame must name its first and last message ids in from and to",
                         "Set from and to to message ids.")
    if len(nodes) > 400 or len(spec["edges"]) > 2000:
        issues.error("size/limit", key, "%d nodes and %d edges is past what one page can lay out" % (len(nodes), len(spec["edges"])),
                     "Split the map by question.")
    if t != "sequence" and len(nodes) > 36:
        issues.warn("size/large", "nodes", "%d nodes is more than one map reads well" % len(nodes),
                    "Split it by question, or group the detail into fewer boxes.")
    if t not in ("sequence", "erd", "tree", "timeline", "waterfall", "class"):
        linked = {e.get("from") for e in spec["edges"]} | {e.get("to") for e in spec["edges"]}
        for n in nodes:
            if n["id"] not in linked and len(nodes) > 1:
                issues.warn("node/isolated", n["id"], "%r has no connections" % n["label"],
                            "Connect it, or leave it out if it doesn't answer the question.")
    return spec


def _evidence(item, where, issues):
    evs = [parse_evidence(x) for x in as_list(item.get("evidence"))]
    for e in evs:
        if "bad" in e:
            issues.error("evidence/format", where, "cannot read evidence %r" % e["bad"],
                         'Write "path/to/file.py:12-20" (optionally "#text on those lines") or "user: their words".')
    item["evidence"] = [e for e in evs if "bad" not in e]
    item["assumed"] = bool(item.get("assumed"))
    if not item["evidence"] and not item["assumed"]:
        issues.error("evidence/missing", where, "no evidence and not marked assumed",
                     'Cite where it comes from ("src/x.py:10", "user: ...") or set "assumed": true so it is drawn as an assumption.')


def _check_kind(spec, t, nodes, ids, issues):
    """What the tree, timeline and waterfall types need from their items."""
    by_id = {n["id"]: n for n in nodes}
    if t in ("tree", "waterfall"):
        for n in nodes:
            if n.get("parent") and n["parent"] not in ids:
                issues.error("parent/missing", n["id"], "parent %r does not exist" % n["parent"],
                             "Name an existing item, or drop parent for a top-level one.")
                n["parent"] = None
        for n in nodes:
            seen, cur = set(), n
            while cur and cur.get("parent"):
                if cur["id"] in seen:
                    issues.error("parent/cycle", n["id"], "parents form a loop", "Each item has one parent, and the chain must end.")
                    n["parent"] = None
                    break
                seen.add(cur["id"])
                cur = by_id.get(cur["parent"])
    if t == "timeline":
        base = None
        for n in nodes:
            w = parse_when(n.get("at"))
            if w is None:
                issues.error("time/missing", n["id"], "at %r is not a time" % n.get("at"),
                             'Use a date or date-time ("2026-10-03T14:05"), a time of day ("14:05") or a number.')
                w = (0.0, base or "num")
            if base is None:
                base = w[1]
            elif w[1].split(":")[0] != base.split(":")[0]:
                issues.error("time/mixed", n["id"], "this time is written differently from the first one",
                             "Write every time the same way: all dates, all times of day, or all numbers.")
            n["_t"] = (w[0], base)
            n["_zone"] = w[1][4:] if w[1].startswith("abs:") else ("+0000" if w[1] == "abs" and re.search(r"(Z|[+-]00:?00)$", str(n.get("at"))) else None)
            n["when"] = str(n.get("at"))
            if n.get("end") is not None:
                we = parse_when(n["end"])
                if we is None or we[0] < w[0]:
                    issues.error("time/end", n["id"], "end %r is not a time after at" % n["end"], "")
                else:
                    n["_end"] = (we[0], base)
                    n["when"] += " to " + str(n["end"])
    if t == "waterfall":
        for n in nodes:
            st, en, du = parse_when(n.get("start")), parse_when(n.get("end")), n.get("duration")
            if st is None:
                issues.error("span/start", n["id"], "start %r is not a number or time" % n.get("start"), "")
                n["_start"] = n["_end"] = 0.0
                continue
            k = 1000.0 if st[1].startswith("abs") or st[1] == "clock" else 1.0  # dates and times of day become ms
            n["_start"] = st[0] * k
            if en is not None:
                n["_end"] = en[0] * k
            elif isinstance(du, (int, float)) and not isinstance(du, bool):
                n["_end"] = n["_start"] + float(du)
            else:
                issues.error("span/end", n["id"], "a span needs end or duration", "")
                n["_end"] = n["_start"]
            if n["_end"] < n["_start"]:
                issues.error("span/order", n["id"], "the span ends before it starts", "")
        for n in nodes:
            p = by_id.get(n.get("parent"))
            if p and "_start" in p and "_start" in n and (n["_start"] < p["_start"] - 1e-9 or n["_end"] > p["_end"] + 1e-9):
                issues.warn("span/outside", n["id"], "%r runs outside its parent %r" % (n["label"], p["label"]),
                            "Check the times: clocks on two machines can disagree, or the child is not really under that parent.")


def verify_evidence(spec, repo_root, issues):
    """Check every file citation against the repository: the file exists, the lines exist,
    and a quoted fragment appears on those lines. Attach the cited lines as a snippet, except
    from files that hold secrets, and with secret-looking lines masked."""
    cache, total = {}, 0
    items = [("node", n) for n in spec["nodes"]] + [("edge", e) for e in spec["edges"]] + [("answer", a) for a in spec["answers"]]
    root = os.path.realpath(repo_root) if repo_root else None
    for kind, item in items:
        for e in item["evidence"]:
            if "file" not in e:
                continue
            where = item["id"]
            if not root:
                e["verified"] = None
                continue
            path = os.path.realpath(os.path.join(root, e["file"]))
            if not (path == root or path.startswith(root + os.sep)):
                issues.error("evidence/outside", where, "%s is outside the repository" % e["file"], "Cite files inside --repo-root.")
                e["verified"] = False
                continue
            if not os.path.isfile(path):
                issues.error("evidence/file", where, "%s does not exist" % e["file"], "Fix the path, relative to the repository root.")
                e["verified"] = False
                continue
            if path not in cache:
                try:
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        cache[path] = fh.read().splitlines()
                except OSError as err:
                    issues.error("evidence/read", where, "cannot read %s: %s" % (e["file"], err), "")
                    e["verified"] = False
                    continue
            lines = cache[path]
            start, end = e.get("start"), e.get("end")
            if start is not None:
                if start < 1 or end < start or end > len(lines):
                    issues.error("evidence/lines", where, "%s has %d lines; cited %s" % (e["file"], len(lines), ev_text(e).split(":")[-1]),
                                 "Cite lines that exist.")
                    e["verified"] = False
                    continue
            span = lines[start - 1:end] if start else lines
            if e.get("quote"):
                flat = lambda s: re.sub(r"\s+", " ", s).strip().lower()
                if flat(e["quote"]) not in flat(" ".join(span)):
                    issues.error("evidence/quote", where, "%r is not on %s" % (e["quote"], ev_text(e)),
                                 "Quote text that is on the cited lines, or fix the line numbers.")
                    e["verified"] = False
                    continue
            e["verified"] = True
            if start and not SECRET_PATH.search(e["file"]) and total < MAX_SNIPPET_TOTAL:
                shown = span[:MAX_SNIPPET_LINES]
                masked = ["[line hidden: looks like a secret]" if SECRET_LINE.search(l) else l for l in shown]
                e["snippet"] = "\n".join(masked) + ("\n…" if len(span) > len(shown) else "")
                total += len(e["snippet"])


def merge_compare(head, base, issues):
    """Mark what changed between a base spec and this one: added, removed (drawn from the
    base), changed (same id, different label, kind, group, note or ends)."""
    t = head["type"]
    if base["type"] != t:
        issues.error("compare/type", "compare", "the base is a %s diagram and this is a %s" % (base["type"], t), "Compare like with like.")
        return
    bn = {n["id"]: n for n in base["nodes"]}
    hn = {n["id"] for n in head["nodes"]}
    for n in head["nodes"]:
        if n.get("status"):
            continue
        if n["id"] not in bn:
            n["status"] = "added"
        elif any(str(n.get(k) or "") != str(bn[n["id"]].get(k) or "") for k in ("label", "kind", "group", "note")):
            n["status"] = "changed"
    gids = {g["id"] for g in head["groups"]}
    for g in base["groups"]:
        if g["id"] not in gids:
            head["groups"].append(dict(g, status="removed"))
            gids.add(g["id"])
    for nid, n in bn.items():
        if nid not in hn:
            head["nodes"].append(dict(n, status="removed"))
    ekey = lambda e: (e.get("from"), e.get("to"), e.get("label", ""))
    be = {ekey(e): e for e in base["edges"]}
    he = {ekey(e) for e in head["edges"]}
    for e in head["edges"]:
        if not e.get("status") and ekey(e) not in be:
            e["status"] = "added"
    used = {e["id"] for e in head["edges"]}
    for k, e in be.items():
        if k not in he:
            e = dict(e, status="removed")
            while e["id"] in used:
                e["id"] += "_base"
            used.add(e["id"])
            head["edges"].append(e)
    head["compared"] = True


# --------------------------------------------------------------------------- text metrics

def text_w(s, size=13.0):
    """Width estimate for a sans-serif label; wide letters count more. Deliberately generous."""
    w = 0.0
    for ch in s:
        if ch in "il.,:;|!'`":
            w += 0.30
        elif ch in "mwMW@":
            w += 0.86
        elif ch.isupper() or ch.isdigit():
            w += 0.64
        elif ord(ch) > 0x2E80:
            w += 1.0
        else:
            w += 0.55
    return w * size


def wrap(s, max_w, size=13.0, max_lines=2):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_w(last + "…", size) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    for i, l in enumerate(lines):  # a single long word
        if text_w(l, size) > max_w * 1.02:
            while l and text_w(l + "…", size) > max_w:
                l = l[:-1]
            lines[i] = l + "…"
    return lines or [""]


def member_text(f):
    vis = {"public": "+", "private": "-", "protected": "#", "package": "~"}.get(str(f.get("visibility", "")), str(f.get("visibility", "")))
    typ = str(f.get("type") or "")
    return ("%s %s" % (vis, f.get("name", ""))).strip() + (": " + typ if typ else "")


def size_node(n):
    shape = KINDS.get(n["kind"], ("rect", "slate"))[0]
    n["shape"] = shape
    if shape == "table":
        rows = n["fields"][:24]
        widest = max([text_w(n["label"], 13) + 24] + [text_w(f.get("name", ""), 12) + text_w(str(f.get("type", "")), 11)
                                                      + (52 if f.get("key") else 0) + 40 for f in rows])
        n["w"] = int(min(max(widest, 170), 320))
        n["lines"] = [n["label"]]
        n["h"] = 32 + 20 * len(rows) + (18 if len(n["fields"]) > 24 else 0) + (4 if rows else 6)
        return
    if shape == "classbox":
        stereo = "" if n["kind"] == "class" else "\u00ab%s\u00bb" % n["kind"]
        n["stereo"] = stereo
        n["member_lines"] = [member_text(f) for f in n["fields"][:30]]
        widest = max([text_w(n["label"], 13) + 30, text_w(stereo, 11) + 30] + [text_w(l, 12) + 24 for l in n["member_lines"]])
        n["w"] = int(min(max(widest, 150), 380))
        n["lines"] = [n["label"]]
        n["h"] = 30 + (14 if stereo else 0) + 18 * len(n["member_lines"]) + (8 if n["member_lines"] else 0) + (16 if len(n["fields"]) > 30 else 0)
        return
    if shape in ("initial", "final"):
        n["lines"] = wrap(n["label"], 120, 11) if n.get("label_shown", n["label"] != n["id"]) else []
        n["w"], n["h"] = 34, 34
        return
    max_w = 190 if shape != "diamond" else 150
    n["lines"] = wrap(n["label"], max_w, 13, 2)
    n["note_lines"] = wrap(str(n.get("note") or ""), max_w, 11, 1) if n.get("note") else []
    tw = max([text_w(l, 13) for l in n["lines"]] + [text_w(l, 11) for l in n["note_lines"]])
    h = 16 + 17 * len(n["lines"]) + 15 * len(n["note_lines"]) + 6
    if shape == "diamond":
        n["w"], n["h"] = int(max(tw * 1.55 + 40, 120)), int(max(h * 1.5, 76))
    elif shape == "person":
        n["w"], n["h"] = int(max(tw + 30, 110)), int(h + 26)
    elif shape == "cylinder":
        n["w"], n["h"] = int(max(tw + 34, 120)), int(h + 14)
    elif shape == "terminal":
        n["w"], n["h"] = int(max(tw + 44, 110)), int(max(h, 44))
    else:
        n["w"], n["h"] = int(max(tw + 34, 120)), int(max(h, 50))


# --------------------------------------------------------------------------- graph layout

class Axis(object):
    """Layout runs in (main, cross) coordinates: main is the direction of flow (left to right
    by default), cross is across it. LR maps main to x; TB maps main to y."""

    def __init__(self, direction):
        self.lr = direction == "LR"

    def m_size(self, n):
        return n["w"] if self.lr else n["h"]

    def c_size(self, n):
        return n["h"] if self.lr else n["w"]

    def xy(self, m, c):
        return (m, c) if self.lr else (c, m)


def layered(spec):
    nodes = spec["nodes"]
    by_id = {n["id"]: n for n in nodes}
    edges = [e for e in spec["edges"] if e.get("from") in by_id and e.get("to") in by_id]
    order = {n["id"]: i for i, n in enumerate(nodes)}
    succ = {n["id"]: [] for n in nodes}
    for e in edges:
        if e["from"] != e["to"]:
            succ[e["from"]].append(e["to"])
    # break cycles: edges that close a loop in author order count as back edges
    back, state = set(), {}

    def dfs(u):
        state[u] = 1
        for v in sorted(succ[u], key=order.get):
            if state.get(v) == 1:
                back.add((u, v))
            elif not state.get(v):
                dfs(v)
        state[u] = 2
    sys.setrecursionlimit(10000)
    for n in nodes:
        if not state.get(n["id"]):
            dfs(n["id"])
    dag = {u: [v for v in vs if (u, v) not in back] for u, vs in succ.items()}
    pred = {n["id"]: [] for n in nodes}
    for u, vs in dag.items():
        for v in vs:
            pred[v].append(u)
    layer = {}

    def longest(u):
        if u in layer:
            return layer[u]
        layer[u] = 0
        layer[u] = max([longest(p) + 1 for p in pred[u]] or [0])
        return layer[u]
    for n in nodes:
        longest(n["id"])
    for _ in range(2):  # pull sources next to what they feed
        for n in nodes:
            u = n["id"]
            if not pred[u] and dag[u]:
                layer[u] = max(layer[u], min(layer[v] for v in dag[u]) - 1)
    return layer, edges, back


def group_tree(spec):
    groups = {g["id"]: g for g in spec["groups"]}
    kids = {g["id"]: [] for g in spec["groups"]}
    top = []
    for g in spec["groups"]:
        (kids[g["parent"]] if g.get("parent") else top).append(g["id"])
    return groups, kids, top


def bands_for(spec):
    """Groups become bands across the flow, so their boxes never overlap. Order follows the
    author's: the first node mentioned decides where its group sits."""
    groups, kids, top = group_tree(spec)
    first = {}
    for i, n in enumerate(spec["nodes"]):
        g = n.get("group")
        while g:
            first.setdefault(g, i)
            g = groups[g].get("parent")
    members = {}
    for n in spec["nodes"]:
        members.setdefault(n.get("group"), []).append(n["id"])
    bands, spans = [], {}

    def walk(gid, depth):
        start = len(bands)
        if members.get(gid):
            bands.append({"group": gid, "depth": depth})
        for k in sorted(kids[gid], key=lambda x: first.get(x, 1e9)):
            walk(k, depth + 1)
        if len(bands) > start:
            spans[gid] = (start, len(bands) - 1, depth)
    units = [("g", g) for g in top] + ([("n", None)] if members.get(None) else [])
    pos = lambda u: first.get(u[1], 1e9) if u[0] == "g" else min(i for i, n in enumerate(spec["nodes"]) if not n.get("group"))
    for kind, gid in sorted(units, key=pos):
        if kind == "n":
            bands.append({"group": None, "depth": 0})
        else:
            walk(gid, 1)
    return bands, spans


def layout_graph(spec):
    ax = Axis(spec["direction"])
    nodes = spec["nodes"]
    for n in nodes:
        size_node(n)
    by_id = {n["id"]: n for n in nodes}
    layer, edges, back = layered(spec)
    bands, spans = bands_for(spec)
    band_of = {}
    for bi, b in enumerate(bands):
        for n in nodes:
            if n.get("group") == b["group"]:
                band_of[n["id"]] = bi
    n_layers = max(layer.values()) + 1 if layer else 1
    cells = {}
    for n in nodes:
        cells.setdefault((band_of[n["id"]], layer[n["id"]]), []).append(n["id"])
    order = {n["id"]: i for i, n in enumerate(nodes)}
    for k in cells:
        cells[k].sort(key=order.get)
    nbrs = {n["id"]: [] for n in nodes}
    for e in edges:
        if e["from"] != e["to"]:
            nbrs[e["from"]].append(e["to"])
            nbrs[e["to"]].append(e["from"])

    def rank():
        r, i = {}, 0
        for bi in range(len(bands)):
            depth = max([len(cells.get((bi, l), [])) for l in range(n_layers)] or [1])
            for l in range(n_layers):
                for j, u in enumerate(cells.get((bi, l), [])):
                    r[u] = i + j + (depth - len(cells.get((bi, l), []))) / 2.0
            i += depth + 1
        return r
    for sweep in range(6):  # barycentre ordering inside each band and layer
        r = rank()
        layers = range(n_layers) if sweep % 2 == 0 else range(n_layers - 1, -1, -1)
        for l in layers:
            for bi in range(len(bands)):
                c = cells.get((bi, l))
                if not c or len(c) < 2:
                    continue
                key = {}
                for u in c:
                    ns = [r[v] for v in nbrs[u] if layer[v] != l]
                    key[u] = sum(ns) / len(ns) if ns else r[u]
                c.sort(key=lambda u: (key[u], order[u]))
    return ax, by_id, layer, edges, back, bands, spans, cells, n_layers


def grid(n_layers, per_row):
    """Layer l sits in row l // cols, column l % cols. One row unless the flow wraps."""
    cols = max(1, min(per_row, n_layers))
    return cols, -(-n_layers // cols)


def place(spec, geo, gap_m, gap_c, per_row):
    """Coordinates from the ordering. A long flow wraps onto rows, like text: layer l is in
    row l // cols, column l % cols. gap_m[k] is the space before column k (gap_m[cols] is after
    the last); route lanes run there, through every row. gap_c[r * (bands + 1) + i] is the
    corridor before band i of row r (i == bands is after the row's last band); long routes
    and the routes from one row to the next run there. Neither ever holds a node."""
    ax, by_id, layer, edges, back, bands, spans, cells, n_layers = geo
    lr = ax.lr
    pad, head = 18, 26
    cols, rows = grid(n_layers, per_row)
    nb = len(bands)
    col_m = [0] * cols
    for n in spec["nodes"]:
        k = layer[n["id"]] % cols
        col_m[k] = max(col_m[k], ax.m_size(n))
    max_depth = max([d for (_, _, d) in spans.values()] or [0])
    m = 20 + (pad + (0 if lr else head)) * max_depth
    col_start, gap_mid = [], []
    for k in range(cols):
        gap_mid.append(m + gap_m[k] / 2.0)
        m += gap_m[k]
        col_start.append(m)
        m += col_m[k]
    gap_mid.append(m + gap_m[cols] / 2.0)
    m += gap_m[cols] + (pad + (0 if lr else head)) * max_depth + 20
    row_layers = [range(r * cols, min((r + 1) * cols, n_layers)) for r in range(rows)]
    present = [[any(cells.get((bi, l)) for l in row_layers[r]) for bi in range(nb)] for r in range(rows)]

    def span_in_row(r, s_, e_):
        bis = [bi for bi in range(s_, e_ + 1) if present[r][bi]]
        return (bis[0], bis[-1]) if bis else None
    opening = lambda r, bi: sorted(d for (s_, e_, d) in spans.values() if (span_in_row(r, s_, e_) or (None,))[0] == bi)
    closing = lambda r, bi: [d for (s_, e_, d) in spans.values() if (span_in_row(r, s_, e_) or (None, None))[1] == bi]
    band_start, band_size, corridors, c = {}, {}, [], 20.0
    for r in range(rows):
        for bi in range(nb):
            if not present[r][bi]:
                continue
            idx = r * (nb + 1) + bi
            corridors.append((c + gap_c[idx] / 2.0, idx))
            c += gap_c[idx] + len(opening(r, bi)) * (head + 6 if lr else pad)
            band_start[(r, bi)] = c
            size = 0
            for l in row_layers[r]:
                stack = cells.get((bi, l), [])
                size = max(size, sum(ax.c_size(by_id[u]) for u in stack) + 26 * max(len(stack) - 1, 0))
            band_size[(r, bi)] = size
            c += size + pad * len(closing(r, bi))
        idx = r * (nb + 1) + nb
        corridors.append((c + gap_c[idx] / 2.0, idx))
        c += gap_c[idx]
    c += 20
    for (r, bi), start in band_start.items():
        for l in row_layers[r]:
            stack = cells.get((bi, l), [])
            total = sum(ax.c_size(by_id[u]) for u in stack) + 26 * max(len(stack) - 1, 0)
            cc = start + (band_size[(r, bi)] - total) / 2.0
            k = l % cols
            for u in stack:
                n = by_id[u]
                n["m"] = col_start[k] + (col_m[k] - ax.m_size(n)) / 2.0
                n["c"] = cc
                cc += ax.c_size(n) + 26
    boxes = []
    for gid, (s_, e_, d) in spans.items():
        first_row = None
        for r in range(rows):
            sp_ = span_in_row(r, s_, e_)
            if not sp_:
                continue
            mem = [n for n in spec["nodes"] if layer[n["id"]] in row_layers[r] and band_of_group(n, gid, spec)]
            if not mem:
                continue
            first_row = r if first_row is None else first_row
            outer = max_depth - d + 1  # how many group borders sit inside this one, plus one
            m0 = min(n["m"] for n in mem) - pad * outer - (0 if lr else head * outer)
            m1 = max(n["m"] + ax.m_size(n) for n in mem) + pad * outer
            c0 = band_start[(r, sp_[0])] - sum(1 for x in opening(r, sp_[0]) if x >= d) * (head + 6 if lr else pad)
            c1 = band_start[(r, sp_[1])] + band_size[(r, sp_[1])] + pad * sum(1 for x in closing(r, sp_[1]) if x >= d)
            boxes.append({"id": gid, "m0": m0, "m1": m1, "c0": c0, "c1": c1, "depth": d, "cont": r != first_row})
    return {"groups": boxes, "corridors": [cv for cv, _ in corridors], "corridor_idx": [i for _, i in corridors],
            "gaps": gap_mid, "extent": (m, c), "cols": cols, "rows": rows}


def band_of_group(n, gid, spec):
    groups = {g["id"]: g for g in spec["groups"]}
    g = n.get("group")
    while g:
        if g == gid:
            return True
        g = groups[g].get("parent") if g in groups else None
    return False


def route(spec, geo, pl):
    """Orthogonal routes that never cross a node: lanes run in the gaps between layers and in
    the corridors between bands, which hold no nodes by construction."""
    ax, by_id, layer, edges, back, bands, spans, cells, n_layers = geo
    cols = pl["cols"]
    lanes_v = {}  # gap key -> list of (lo, hi, edge id)
    lanes_h = {}
    plans = []
    side_use = {}

    def box(n):
        return n["m"], n["c"], n["m"] + ax.m_size(n), n["c"] + ax.c_size(n)

    for e in edges:
        s, t = by_id[e["from"]], by_id[e["to"]]
        ls, lt = layer[s["id"]], layer[t["id"]]
        sm0, sc0, sm1, sc1 = box(s)
        tm0, tc0, tm1, tc1 = box(t)
        scen, tcen = (sc0 + sc1) / 2.0, (tc0 + tc1) / 2.0
        if s["id"] == t["id"]:
            plans.append({"e": e, "kind": "self"})
            continue
        same_row = ls // cols == lt // cols
        if lt == ls + 1 and same_row:
            plans.append({"e": e, "kind": "adjacent", "gap": ("v", lt % cols), "out": "end", "in": "start"})
        elif lt > ls + 1 and same_row:
            plans.append({"e": e, "kind": "multi", "out": "end", "in": "start"})
        elif lt == ls:
            plans.append({"e": e, "kind": "same", "gap": ("v", ls % cols + 1), "out": "end", "in": "end"})
        else:  # backwards, or on to a later row
            plans.append({"e": e, "kind": "corridor", "g1": ("v", ls % cols + 1), "g2": ("v", lt % cols), "out": "end", "in": "start"})
    # ports: spread the edges that share a node side, ordered by the far end
    for p in plans:
        if p["kind"] == "self":
            continue
        e = p["e"]
        side_use.setdefault((e["from"], p["out"]), []).append((p, "s"))
        side_use.setdefault((e["to"], p["in"]), []).append((p, "t"))
    for (nid, side), lst in side_use.items():
        n = by_id[nid]
        m0, c0, m1, c1 = box(n)

        def far(item):
            p, which = item
            other = by_id[p["e"]["to"] if which == "s" else p["e"]["from"]]
            return other["c"] + ax.c_size(other) / 2.0
        lst.sort(key=far)
        k = len(lst)
        for i, (p, which) in enumerate(lst):
            field = p["e"].get("from_field" if which == "s" else "to_field")
            fidx = next((j for j, f in enumerate(n["fields"][:24]) if f.get("name") == field), None) if field else None
            if fidx is not None and n["shape"] == "table":
                cpos = c0 + 32 + 20 * fidx + 10
            else:
                f = 0.36 if n["shape"] in ("diamond", "initial", "final") else 0.22
                lo, hi = (c0 + (c1 - c0) * f, c1 - (c1 - c0) * f) if k > 1 else ((c0 + c1) / 2.0,) * 2
                cpos = lo + (hi - lo) * (i / (k - 1.0) if k > 1 else 0.5)
            mpos = m1 if side == "end" else m0
            half_c, mid_c = (c1 - c0) / 2.0, (c0 + c1) / 2.0
            off = min(abs(cpos - mid_c), half_c)
            if n["shape"] == "diamond":
                inset = off / half_c * ((m1 - m0) / 2.0) if half_c else 0
            elif n["shape"] == "terminal" and ax.lr:
                inset = half_c - (half_c ** 2 - off ** 2) ** 0.5
            elif n["shape"] in ("initial", "final"):
                inset = half_c - (max(half_c ** 2 - off ** 2, 0)) ** 0.5
            else:
                inset = 0
            mpos += -inset if side == "end" else inset
            p["sp" if which == "s" else "tp"] = (mpos, cpos)
    def clear(cv, l0, l1):
        for l in range(l0, l1):
            for bi in range(len(bands)):
                for u in cells.get((bi, l), []):
                    _, c0, _, c1 = box(by_id[u])
                    if c0 - 8 <= cv <= c1 + 8:
                        return False
        return True
    for p in plans:  # a long forward edge goes straight when nothing sits at its port's height
        if p["kind"] != "multi":
            continue
        ls, lt = layer[p["e"]["from"]], layer[p["e"]["to"]]
        if clear(p["sp"][1], ls + 1, lt):
            p.update(kind="straight", gap=("v", lt % cols))
        elif clear(p["tp"][1], ls + 1, lt):
            p.update(kind="straight", gap=("v", ls % cols + 1))
        else:
            p.update(kind="corridor", g1=("v", ls % cols + 1), g2=("v", lt % cols))
    for p in plans:
        if p["kind"] == "self":
            continue
        sp, tp = p["sp"], p["tp"]
        if p["kind"] in ("adjacent", "same"):
            lanes_v.setdefault(p["gap"], []).append([min(sp[1], tp[1]), max(sp[1], tp[1]), p])
        elif p["kind"] == "straight":
            lanes_v.setdefault(p["gap"], []).append([min(sp[1], tp[1]), max(sp[1], tp[1]), p])
        else:
            cv = (sp[1] + tp[1]) / 2.0
            corr = min(range(len(pl["corridors"])), key=lambda i: (abs(pl["corridors"][i] - sp[1]) + abs(pl["corridors"][i] - tp[1]),
                                                                abs(pl["corridors"][i] - cv)))
            p["corr"] = corr
            cy = pl["corridors"][corr]
            lanes_v.setdefault(p["g1"], []).append([min(sp[1], cy), max(sp[1], cy), p, "g1"])
            lanes_v.setdefault(p["g2"], []).append([min(tp[1], cy), max(tp[1], cy), p, "g2"])
            g1m = p["g1"][1]
            g2m = p["g2"][1]
            lanes_h.setdefault(corr, []).append([min(g1m, g2m), max(g1m, g2m), p])
    need_v, need_h = {}, {}
    for key, segs in lanes_v.items():
        segs.sort(key=lambda s: (s[0], s[1]))
        ends = []
        for sg in segs:
            for i, end in enumerate(ends):
                if end < sg[0] - 10:
                    ends[i] = sg[1]
                    sg.append(i)
                    break
            else:
                ends.append(sg[1])
                sg.append(len(ends) - 1)
        need_v[key] = len(ends)
    for key, segs in lanes_h.items():
        segs.sort(key=lambda s: (s[0], s[1]))
        ends = []
        for sg in segs:
            for i, end in enumerate(ends):
                if end < sg[0] - 0.05:
                    ends[i] = sg[1]
                    sg.append(i)
                    break
            else:
                ends.append(sg[1])
                sg.append(len(ends) - 1)
        need_h[key] = len(ends)
    return plans, lanes_v, lanes_h, need_v, need_h


def lane_pos(center, idx, count, step=9):
    return center + (idx - (count - 1) / 2.0) * step


def build_paths(spec, geo, pl, plans, lanes_v, lanes_h, need_v, need_h):
    ax = geo[0]
    by_id = geo[1]
    vlane, hlane = {}, {}
    for key, segs in lanes_v.items():
        for sg in segs:
            tag = sg[3] if len(sg) == 5 else "v"
            vlane[(id(sg[2]), tag)] = (key, sg[-1])
    for key, segs in lanes_h.items():
        for sg in segs:
            hlane[id(sg[2])] = (key, sg[-1])

    def vx(p, tag):
        key, idx = vlane[(id(p), tag)]
        return lane_pos(pl["gaps"][key[1]], idx, need_v[key])
    for p in plans:
        e = p["e"]
        if p["kind"] == "self":
            n = by_id[e["from"]]
            m1, c0 = n["m"] + ax.m_size(n), n["c"]
            mid = n["m"] + ax.m_size(n) * 0.7
            pts = [(m1, c0 + ax.c_size(n) * 0.3), (m1 + 22, c0 + ax.c_size(n) * 0.3), (m1 + 22, c0 - 20), (mid, c0 - 20), (mid, c0)]
        else:
            sp, tp = p["sp"], p["tp"]
            if p["kind"] == "adjacent":
                x = vx(p, "v")
                pts = [sp, (x, sp[1]), (x, tp[1]), tp]
            elif p["kind"] == "same":
                x = vx(p, "v")
                pts = [sp, (x, sp[1]), (x, tp[1]), tp]
            elif p["kind"] == "straight":
                x = vx(p, "v")
                pts = [sp, (x, sp[1]), (x, tp[1]), tp]
            else:
                key, idx = hlane[id(p)]
                cy = lane_pos(pl["corridors"][key], idx, need_h[key])
                x1, x2 = vx(p, "g1"), vx(p, "g2")
                pts = [sp, (x1, sp[1]), (x1, cy), (x2, cy), (x2, tp[1]), tp]
        clean = [pts[0]]
        for q in pts[1:]:
            if abs(q[0] - clean[-1][0]) > 0.5 or abs(q[1] - clean[-1][1]) > 0.5:
                clean.append(q)
        e["pts"] = [ax.xy(m, c) for m, c in clean]


VIEW_W, VIEW_H = 1360.0, 720.0  # the canvas on a laptop screen; wrapping aims to fill it


def run_graph(spec, geo, per_row):
    ax, n_layers, nb = geo[0], geo[8], len(geo[5])
    cols, rows = grid(n_layers, per_row)
    edge_gap = lambda k: 24 if k in (0, cols) else 72
    row_gap = lambda i: 44 if i % (nb + 1) == 0 and i > 0 else 30
    gap_m = [edge_gap(k) for k in range(cols + 1)]
    gap_c = [row_gap(i) for i in range(rows * (nb + 1))]
    for _ in range(4):
        pl = place(spec, geo, gap_m, gap_c, per_row)
        plans, lv, lh, need_v, need_h = route(spec, geo, pl)
        new_m = [max(edge_gap(k), 30 + 9 * need_v.get(("v", k), 0)) for k in range(cols + 1)]
        new_c = list(gap_c)
        for j, idx in enumerate(pl["corridor_idx"]):
            new_c[idx] = max(row_gap(idx), 20 + 9 * need_h.get(j, 0))
        if new_m == gap_m and new_c == gap_c:
            break
        gap_m, gap_c = new_m, new_c
    build_paths(spec, geo, pl, plans, lv, lh, need_v, need_h)
    for n in spec["nodes"]:
        n["x"], n["y"] = ax.xy(n["m"], n["c"])
    for g in pl["groups"]:
        x0, y0 = ax.xy(g["m0"], g["c0"])
        x1, y1 = ax.xy(g["m1"], g["c1"])
        g.update({"x": min(x0, x1), "y": min(y0, y1), "w": abs(x1 - x0), "h": abs(y1 - y0)})
    boxes = [(n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"] + (30 if n["shape"] in ("initial", "final") else 0)) for n in spec["nodes"]]
    boxes += [(p[0], p[1], p[0], p[1]) for e in spec["edges"] for p in e.get("pts", [])]
    boxes += [(g["x"], g["y"], g["x"] + g["w"], g["y"] + g["h"]) for g in pl["groups"]]
    minx, miny = min(b[0] for b in boxes), min(b[1] for b in boxes)
    dx, dy = 30 - minx, 30 - miny
    for n in spec["nodes"]:
        n["x"] += dx
        n["y"] += dy
    for e in spec["edges"]:
        e["pts"] = [(x + dx, y + dy) for x, y in e.get("pts", [])]
    for g in pl["groups"]:
        g["x"] += dx
        g["y"] += dy
    W = max(b[2] for b in boxes) + dx + 40
    H = max(b[3] for b in boxes) + dy + 40
    return {"w": W, "h": H, "groups": pl["groups"], "rows": rows}


def layout_graph_full(spec):
    """Lay the graph out; a long left-to-right flow wraps onto as many rows as keep its text
    largest on a laptop screen. "wrap": false keeps one row; a number sets layers per row."""
    geo = layout_graph(spec)
    n_layers = geo[8]
    wrap = spec.get("wrap")
    if wrap is False or spec["direction"] != "LR" or n_layers < 6:
        options = [n_layers]
    elif isinstance(wrap, int) and not isinstance(wrap, bool) and wrap > 0:
        options = [max(2, wrap)]
    else:
        options = sorted({max(3, -(-n_layers // r)) for r in range(1, 5)}, reverse=True)
    best = None
    for per_row in options:
        out = run_graph(spec, geo, per_row)
        score = min(VIEW_W / out["w"], VIEW_H / out["h"], 1.0) * (0.95 ** (out["rows"] - 1))
        if best is None or score > best[0] + 1e-9:
            best = (score, per_row)
    return run_graph(spec, geo, best[1]) if len(options) > 1 else out


# --------------------------------------------------------------------------- sequence layout

def layout_sequence(spec):
    parts = spec["nodes"]
    idx = {p["id"]: i for i, p in enumerate(parts)}
    for p in parts:
        p["lines"] = wrap(p["label"], 150, 13, 2)
        p["note_lines"] = wrap(str(p.get("note") or ""), 150, 11, 1) if p.get("note") else []
        p["w"] = int(max(max(text_w(l, 13) for l in p["lines"] + [""]) + 30, 110))
        p["shape"] = "person" if p["kind"] in ("person", "actor") else "rect"
        p["h"] = 22 + 17 * len(p["lines"]) + 14 * len(p["note_lines"]) + (24 if p["shape"] == "person" else 0)
    msgs = [m for m in spec["edges"] if m.get("from") in idx and m.get("to") in idx]
    need = [max(p["w"], 120) for p in parts]
    spacing = [0.0] * max(len(parts) - 1, 0)
    for m in msgs:
        a, b = sorted((idx[m["from"]], idx[m["to"]]))
        lw = text_w(m["label"], 12) + 40
        if a == b:
            if a < len(spacing):
                spacing[a] = max(spacing[a], lw + 40)
            continue
        per = lw / float(b - a)
        for k in range(a, b):
            spacing[k] = max(spacing[k], per)
    xs, x = [], 40.0
    for i, p in enumerate(parts):
        xs.append(x + p["w"] / 2.0)
        if i < len(spacing):
            x += max(p["w"] / 2.0 + parts[i + 1]["w"] / 2.0 + 40, spacing[i], 170)
    head_h = max(p["h"] for p in parts) + 30
    group_pad = 30 if spec["groups"] else 0
    top = 30 + group_pad
    for i, p in enumerate(parts):
        p["cx"] = xs[i]
        p["x"], p["y"] = xs[i] - p["w"] / 2.0, top
    y = top + head_h + 20
    frame_open = {}
    for f in spec["frames"]:
        frame_open.setdefault(f.get("from"), []).append(f)
    for m in msgs:
        for f in frame_open.get(m["id"], []):
            y += 26
            f["y0"] = y - 22
        m["lines"] = wrap(m["label"], max(abs(xs[idx[m["to"]]] - xs[idx[m["from"]]]) - 20, 150), 12, 2)
        y += 14 * len(m["lines"])
        x1, x2 = xs[idx[m["from"]]], xs[idx[m["to"]]]
        if x1 == x2:
            m["pts"] = [(x1, y), (x1 + 40, y), (x1 + 40, y + 18), (x1, y + 18)]
            m["label_at"] = (x1 + 46, y - 4 - 14 * (len(m["lines"]) - 1), "start")
            y += 18
        else:
            m["pts"] = [(x1, y), (x2, y)]
            m["label_at"] = ((x1 + x2) / 2.0, y - 6 - 14 * (len(m["lines"]) - 1), "middle")
        m["row_y"] = y
        y += 26
        for f in spec["frames"]:
            if f.get("to") == m["id"]:
                f["y1"] = y - 6
                y += 10
    for f in spec["frames"]:
        inv = [m for m in msgs if f.get("y0", 0) <= m.get("row_y", -1) <= f.get("y1", 0)]
        cols = [xs[idx[m["from"]]] for m in inv] + [xs[idx[m["to"]]] for m in inv] or xs[:1]
        f["x0"], f["x1"] = min(cols) - 60, max(cols) + 60
    end_y = y + 10
    boxes = []
    for g in spec["groups"]:
        mem = [p for p in parts if p.get("group") == g["id"]]
        if mem:
            boxes.append({"id": g["id"], "x": min(p["x"] for p in mem) - 14, "y": top - 26,
                          "w": max(p["x"] + p["w"] for p in mem) - min(p["x"] for p in mem) + 28, "h": end_y - top + 34, "depth": 1})
    W = max(p["x"] + p["w"] for p in parts) + 60
    W = max([W] + [f["x1"] + 20 for f in spec["frames"]] + [m["pts"][1][0] + 60 + text_w(m["label"], 12) for m in msgs if m["from"] == m["to"]])
    return {"w": W, "h": end_y + 40, "groups": boxes, "lifeline": (top + head_h - 30, end_y)}


# --------------------------------------------------------------------------- time

def parse_when(v):
    """A point in time as (seconds, kind). kind is "abs" for a date or date-time, "clock" for
    a time of day ("14:05"), "num" for a plain number. Returns None when it can't be read."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v), "num"
    s = str(v).strip()
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2})(\.\d+)?)?$", s)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3) or 0) + float(m.group(4) or 0), "clock"
    iso = s.replace("Z", "+00:00")
    if " " in iso and "T" not in iso:
        iso = iso.replace(" ", "T", 1)
    try:
        dt = datetime.datetime.fromisoformat(iso)
    except ValueError:
        try:
            return float(s), "num"
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)  # wall-clock time, shown as written
        return dt.timestamp(), "abs"
    return dt.timestamp(), "abs:" + dt.strftime("%z")


def fmt_when(t, kind, interval=60):
    if kind == "num":
        return ("%g" % round(t, 3))
    if kind == "clock":
        t = int(round(t))
        return "%02d:%02d" % ((t // 3600) % 24, (t // 60) % 60) + (":%02d" % (t % 60) if interval < 60 else "")
    tz = datetime.timezone.utc
    if kind.startswith("abs:"):
        off = kind[4:]
        sign = -1 if off.startswith("-") else 1
        tz = datetime.timezone(sign * datetime.timedelta(hours=int(off[1:3]), minutes=int(off[3:5])))
    d = datetime.datetime.fromtimestamp(t, tz)
    if interval >= 86400:
        return d.strftime("%d %b %Y") if interval >= 30 * 86400 else d.strftime("%d %b")
    return d.strftime("%H:%M" + (":%S" if interval < 60 else ""))


def fmt_span(seconds, kind):
    if kind == "num":
        return "%g" % round(seconds, 3)
    s = int(round(abs(seconds)))
    d, h, m = s // 86400, (s % 86400) // 3600, (s % 3600) // 60
    parts = (["%dd" % d] if d else []) + (["%dh" % h] if h else []) + (["%dm" % m] if m and not d else [])
    return " ".join(parts) or "%ds" % s


def nice_step(span, target=8):
    """A round step (1, 2 or 5 times a power of ten) giving about target ticks."""
    if span <= 0:
        return 1.0
    raw = span / float(target)
    p = 10 ** math.floor(math.log10(raw))
    for k in (1, 2, 5, 10):
        if k * p >= raw:
            return k * p
    return 10 * p


TIME_STEPS = [1, 5, 10, 15, 30, 60, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400, 172800,
              604800, 1209600, 2592000, 7776000, 31536000]


# --------------------------------------------------------------------------- tree

def layout_tree(spec):
    """Single-parent containment, depth left to right: leaves stack in order, each parent
    sits beside the middle of its children."""
    nodes = spec["nodes"]
    for n in nodes:
        size_node(n)
    by_id = {n["id"]: n for n in nodes}
    kids = {n["id"]: [] for n in nodes}
    roots = []
    for n in nodes:
        (kids[n["parent"]] if n.get("parent") in by_id else roots).append(n["id"])
    depth = {}

    def set_depth(u, d):
        depth[u] = d
        for v in kids[u]:
            set_depth(v, d + 1)
    for r in roots:
        set_depth(r, 0)
    col_w = {}
    for n in nodes:
        col_w[depth[n["id"]]] = max(col_w.get(depth[n["id"]], 0), n["w"])
    col_x, x = {}, 30.0
    for d in sorted(col_w):
        col_x[d] = x
        x += col_w[d] + 64
    cursor = [30.0]

    def place_(u):
        n = by_id[u]
        if not kids[u]:
            n["y"] = cursor[0]
            cursor[0] += n["h"] + 14
        else:
            for v in kids[u]:
                place_(v)
            first, last = by_id[kids[u][0]], by_id[kids[u][-1]]
            mid = (first["y"] + first["h"] / 2.0 + last["y"] + last["h"] / 2.0) / 2.0
            n["y"] = mid - n["h"] / 2.0
            low = cursor[0]
            if n["y"] + n["h"] + 14 > low:  # a tall parent with few children
                cursor[0] = n["y"] + n["h"] + 14
        n["x"] = col_x[depth[u]] + (col_w[depth[u]] - n["w"]) / 2.0 if not kids[u] else col_x[depth[u]]
    for r in roots:
        place_(r)
        cursor[0] += 16
    spec["edges"] = []
    for n in nodes:
        if n.get("parent") in by_id:
            p = by_id[n["parent"]]
            mx = col_x[depth[p["id"]]] + col_w[depth[p["id"]]] + 32
            py, cy = p["y"] + p["h"] / 2.0, n["y"] + n["h"] / 2.0
            spec["edges"].append({"id": "t-" + n["id"], "from": p["id"], "to": n["id"], "label": "", "style": "solid",
                                  "assumed": n["assumed"], "evidence": [], "tree": True,
                                  "pts": [(p["x"] + p["w"], py), (mx, py), (mx, cy), (n["x"], cy)]})
    W = max(n["x"] + n["w"] for n in nodes) + 40
    H = max(n["y"] + n["h"] for n in nodes) + 40
    return {"w": W, "h": H, "groups": []}


# --------------------------------------------------------------------------- timeline

def timeline_findings(spec, evs, kind):
    """The span, the longest quiet stretch, approximate times and time zones, computed."""
    out = []
    order = sorted(evs, key=lambda e: e["_t"][0])
    if len(order) >= 2:
        first = order[0]["when"]
        if kind.startswith("abs") and ":" in first and not re.match(r"^~?\d{2} [A-Z][a-z]{2} ", first):
            first = fmt_when(order[0]["_t"][0], kind, 86400) + " " + first  # one day: give its date once
        out.append("From %s to %s: %s." % (first, order[-1]["when"].split(" to ")[0], fmt_span(order[-1]["_t"][0] - order[0]["_t"][0], kind)))
        gaps = [(b["_t"][0] - (a["_end"][0] if a.get("_end") else a["_t"][0]), a, b) for a, b in zip(order, order[1:])]
        g, a, b = max(gaps, key=lambda x: x[0])
        if g > 0:
            out.append("Longest quiet stretch: %s, between %s (%s) and %s (%s)." % (
                fmt_span(g, kind), a["label"], a["when"], b["label"], b["when"]))
    approx = [e for e in order if e.get("approx")]
    if approx:
        out.append("Approximate times (the source is unsure): " + "; ".join("%s at %s" % (e["label"], e["when"]) for e in approx) + ".")
    zname = lambda z: "UTC" if z in ("+0000", "") else "UTC%s:%s" % (z[:3], z[3:])
    zones = sorted({e["_zone"] for e in evs if e.get("_zone")})
    if len(zones) > 1:
        out.append("The sources give times in %s; all are shown in %s." % (" and ".join(zname(z) for z in zones), zname(kind[4:])))
    return out


def layout_timeline(spec):
    """Events on a time axis, one lane per source. A long quiet stretch is shortened and
    marked, so a burst of events stays readable; everything else is to scale."""
    evs = spec["nodes"]
    kind = evs[0]["_t"][1]
    times = sorted({e["_t"][0] for e in evs} | {e["_end"][0] for e in evs if e.get("_end")})
    t0, t1 = times[0], times[-1]
    total = (t1 - t0) or 1.0
    long_gaps = []
    if len(times) >= 4:
        for a, b in zip(times, times[1:]):
            if b - a > 0.3 * total:
                long_gaps.append((a, b))
    width, brk = 1080.0, 64.0
    kept = total - sum(b - a for a, b in long_gaps)
    per = (width - brk * len(long_gaps)) / (kept or 1.0)
    x0 = 190.0

    def X(t):
        x, cur = x0, t0
        for a, b in long_gaps:
            if t <= a:
                break
            x += (min(t, a) - cur) * per
            if t >= b:
                x += brk
                cur = b
            else:
                return x + brk * (t - a) / (b - a)
        return x + (t - cur) * per
    groups = {g["id"]: g["label"] for g in spec["groups"]}
    lanes = []
    for e in evs:
        ln = e.get("lane") or e.get("group") or ""
        if ln not in lanes:
            lanes.append(ln)
    lane_label = lambda ln: groups.get(ln, ln) or "Events"
    y = 70.0
    lane_geo = {}
    for ln in lanes:
        rows = []
        mine = sorted([e for e in evs if (e.get("lane") or e.get("group") or "") == ln], key=lambda e: e["_t"][0])
        for e in mine:
            e["lines"] = wrap(e["label"], 200, 12, 2)
            w = max(text_w(l, 12) for l in e["lines"]) + 12
            x = X(e["_t"][0])
            box = (x - 4, x - 4 + w)
            for r, used in enumerate(rows):
                if all(box[0] > b + 8 or box[1] < a - 8 for a, b in used):
                    used.append(box)
                    e["_row"] = r
                    break
            else:
                rows.append([box])
                e["_row"] = len(rows) - 1
        row_h = 34
        lane_h = max(len(rows), 1) * row_h + 34
        line_y = y + lane_h - 18
        lane_geo[ln] = (y, lane_h, line_y)
        for e in mine:
            x = X(e["_t"][0])
            e["x"], e["y"], e["w"], e["h"] = x - 7, line_y - 7, 14, 14
            e["label_y"] = line_y - 26 - e["_row"] * row_h - 14 * (len(e["lines"]) - 1)
            if e.get("_end"):
                e["x2"] = X(e["_end"][0])
        y += lane_h + 10
    # ticks inside the stretches drawn to scale
    span_kept = kept or total
    step = next((s for s in TIME_STEPS if span_kept / s <= 9), TIME_STEPS[-1]) if kind != "num" else nice_step(span_kept)
    ticks, t = [], math.ceil(t0 / step) * step
    while t <= t1 + 1e-9:
        if not any(a < t < b for a, b in long_gaps):
            ticks.append(t)
        t += step
    shown = str(spec.get("timezone") or "").strip().upper()
    if kind.startswith("abs") and shown:
        m = re.match(r"^(?:UTC)?([+-])(\d{1,2}):?(\d{2})?$", shown)
        if shown in ("UTC", "Z", "GMT"):
            kind = "abs:+0000"
        elif m:
            kind = "abs:%s%02d%s" % (m.group(1), int(m.group(2)), m.group(3) or "00")
    one_day = kind.startswith("abs") and fmt_when(t0, kind, 86400) == fmt_when(t1, kind, 86400)
    for e in evs:
        raw = str(e.get("at"))
        if kind.startswith("abs"):
            date_only = bool(re.match(r"^\d{4}-\d{2}-\d{2}$", raw))
            e["when"] = fmt_when(e["_t"][0], kind, 86400 * 30 if date_only else 60)
            if not date_only and not one_day:
                e["when"] = fmt_when(e["_t"][0], kind, 86400) + " " + e["when"]
        if e.get("approx"):
            e["when"] = "~" + e["when"]
            if e.get("_end"):
                e["when"] += " to " + (fmt_when(e["_end"][0], kind, 60) if one_day or fmt_when(e["_end"][0], kind, 86400) == fmt_when(e["_t"][0], kind, 86400)
                                       else fmt_when(e["_end"][0], kind, 86400) + " " + fmt_when(e["_end"][0], kind, 60))
    tick_labels, last_day = [], None
    for t in ticks:
        lab = fmt_when(t, kind, step)
        if kind.startswith("abs") and step < 86400 and not one_day:
            day = fmt_when(t, kind, 86400)
            if day != last_day:
                lab = day + " " + lab
                last_day = day
        tick_labels.append((X(t), lab))
    spec["_findings"] = timeline_findings(spec, evs, kind)
    spec["_timeline"] = {"lanes": [(lane_label(ln),) + lane_geo[ln] for ln in lanes], "ticks": tick_labels,
                         "breaks": [(X(a) + 6, X(b) - 6, fmt_span(b - a, kind)) for a, b in long_gaps], "x0": x0, "x1": X(t1), "kind": kind,
                         "start": "", "end": "",
                         "span": fmt_span(total, kind)}
    for e in spec["edges"]:
        a, b = next((n for n in evs if n["id"] == e["from"]), None), next((n for n in evs if n["id"] == e["to"]), None)
        if a and b:
            e["pts"] = [(a["x"] + 7, a["y"] + 7), (b["x"] + 7, b["y"] + 7)]
    first, last = min(evs, key=lambda e: e["_t"][0]), max(evs, key=lambda e: e["_end"][0] if e.get("_end") else e["_t"][0])
    spec["_timeline"]["start"] = first["when"].split(" to ")[0]
    spec["_timeline"]["end"] = last["when"].split(" to ")[-1] if not last.get("_end") or " " in last["when"].split(" to ")[-1] else last["when"]
    right = max([X(t1) + 40] + [e["x"] + max(text_w(l, 12) for l in e["lines"]) + 24 for e in evs])
    spec["_timeline"]["right"] = right
    return {"w": right + 40, "h": y + 30, "groups": []}


def timeline_svg(spec):
    tl = spec["_timeline"]
    out = []
    for label, top, h, line_y in tl["lanes"]:
        out.append('<g class="lane"><rect x="20" y="%.1f" width="%.1f" height="%.1f" rx="8"/><text class="glabel" x="32" y="%.1f">%s</text>'
                   '<line class="lane-line" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/></g>' % (
                       top, tl["right"] - 20, h, line_y + 4, esc(label), tl["x0"] - 10, line_y, tl["x1"] + 30, line_y))
    out.append('<g class="axis">')
    for x, lab in tl["ticks"]:
        out.append('<line x1="%.1f" y1="44" x2="%.1f" y2="52"/><text x="%.1f" y="38" text-anchor="middle">%s</text>' % (x, x, x, esc(lab)))
    for a, b, lab in tl["breaks"]:
        mid = (a + b) / 2.0
        out.append('<path class="brk" d="M%.1f,40 l6,16 M%.1f,40 l6,16"/><text class="brk-label" x="%.1f" y="66" text-anchor="middle">%s later</text>' % (
            mid - 7, mid + 1, mid, esc(lab)))
    out.append('<line x1="%.1f" y1="48" x2="%.1f" y2="48"/></g>' % (tl["x0"] - 10, tl["x1"] + 30))
    for e in spec["edges"]:
        if e.get("pts"):
            out.append(edge_svg(e))
    for n in spec["nodes"]:
        fam = KINDS.get(n["kind"], ("dot", "blue"))[1]
        cls = ["node", "event", "c-" + fam, "k-" + n["kind"]] + (["assumed"] if n["assumed"] else []) + (["approx"] if n.get("approx") else []) + (["st-" + n["status"]] if n.get("status") else [])
        cx, cy = n["x"] + 7, n["y"] + 7
        g = ['<g class="%s" id="n-%s" data-id="%s" tabindex="0" role="button" aria-label="%s">' % (
            " ".join(cls), esc(n["id"]), esc(n["id"]), esc(n["when"] + " " + n["label"]))]
        g.append("<title>%s — %s</title>" % (esc(n["when"]), esc(n["label"])))
        if n.get("x2"):
            g.append('<rect class="shape bar" x="%.1f" y="%.1f" width="%.1f" height="10" rx="5"/>' % (cx, cy - 5, max(n["x2"] - cx, 4)))
        g.append('<line class="leader" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx, cy - 7, cx, n["label_y"] + 4 + 14 * (len(n["lines"]) - 1)))
        if n["kind"] == "milestone":
            g.append('<path class="shape" d="M%.1f,%.1f l8,8 l-8,8 l-8,-8 z"/>' % (cx, cy - 8))
        else:
            g.append('<circle class="shape" cx="%.1f" cy="%.1f" r="6.5"/>' % (cx, cy))
        for i, l in enumerate(n["lines"]):
            g.append('<text class="label tl" x="%.1f" y="%.1f">%s</text>' % (cx - 3, n["label_y"] + 14 * i, esc(l)))
        g.append('<text class="note tl" x="%.1f" y="%.1f">%s</text>' % (cx - 3, n["label_y"] - 13, esc(n["when"])))
        g.append("</g>")
        out.append("".join(g))
    return "".join(out)


# --------------------------------------------------------------------------- waterfall

SERVICE_COLOURS = ["#3b82f6", "#16a34a", "#d97706", "#8b5cf6", "#0d9488", "#e11d48", "#4f46e5", "#64748b"]


def layout_waterfall(spec):
    """Spans as bars on one clock, in call order, children under their parent. The critical
    path (the chain of spans that decided when the whole thing ended) is marked."""
    spans = spec["nodes"]
    by_id = {s["id"]: s for s in spans}
    kids = {s["id"]: [] for s in spans}
    roots = []
    for s in spans:
        (kids[s["parent"]] if s.get("parent") in by_id else roots).append(s["id"])
    key = lambda i: (by_id[i]["_start"], by_id[i]["_end"])
    order, depth = [], {}

    def walk(u, d):
        order.append(u)
        depth[u] = d
        for v in sorted(kids[u], key=key):
            walk(v, d + 1)
    for r in sorted(roots, key=key):
        walk(r, 0)
    t0 = min(s["_start"] for s in spans)
    t1 = max(s["_end"] for s in spans)
    total = (t1 - t0) or 1.0  # the axis
    whole = (by_id[roots[0]]["_end"] - by_id[roots[0]]["_start"]) if len(roots) == 1 else total
    whole = whole or 1.0
    crit, crit_order = set(), []

    def critical(u):
        """u is on the path; so is the child that finished last, the child that finished last
        before that one started, and so on back to the start of u."""
        crit.add(u)
        crit_order.append(u)
        limit, chain = by_id[u]["_end"], []
        inside = [c for c in kids[u] if by_id[c]["_end"] <= by_id[u]["_end"] + 1e-9]  # a span that outlives its parent was not waited for
        for c in sorted(inside, key=lambda i: by_id[i]["_end"], reverse=True):
            if by_id[c]["_end"] <= limit + 1e-9:
                chain.append(c)
                limit = by_id[c]["_start"]
        for c in sorted(chain, key=lambda i: by_id[i]["_start"]):
            critical(c)
    if roots:
        critical(max(roots, key=lambda i: by_id[i]["_end"]))
    unit = spec.get("unit") or "ms"
    label_w = min(max([text_w(by_id[i]["label"], 12) + 18 * depth[i] + 20 for i in order] + [180]), 360)
    bx0, bw = label_w + 30, 880.0
    X = lambda t: bx0 + (t - t0) / total * bw
    services = []
    for i, sid in enumerate(order):
        s = by_id[sid]
        svc = s.get("service") or ""
        if svc not in services:
            services.append(svc)
        s["row"], s["depth"], s["crit"] = i, depth[sid], sid in crit
        s["x"], s["y"], s["w"], s["h"] = X(s["_start"]), 60 + i * 28, max(X(s["_end"]) - X(s["_start"]), 2), 18
        s["colour"] = SERVICE_COLOURS[services.index(svc) % len(SERVICE_COLOURS)]
        dur = s["_end"] - s["_start"]
        covered, cur_end = 0.0, s["_start"]
        for k in sorted(kids[sid], key=key):
            a, b = max(by_id[k]["_start"], cur_end), min(by_id[k]["_end"], s["_end"])
            if b > a:
                covered += b - a
                cur_end = b
        parent = by_id.get(s.get("parent"))
        s["_detached"] = bool(parent and s["_end"] > parent["_end"] + 1e-9)
        s["facts"] = [["starts at", fmt_dur(s["_start"] - t0, unit)], ["takes", fmt_dur(dur, unit)],
                      ["share of the whole", "%.0f%%" % (100.0 * dur / whole)], ["time of its own (not in a child span)", fmt_dur(dur - covered, unit)]]
        s["_self"] = dur - covered
        if s["crit"]:
            s["facts"].append(["on the critical path", "yes"])
        if s["_detached"]:
            s["facts"].append(["after its parent ends", "runs on for %s; nothing waits for it" % fmt_dur(s["_end"] - parent["_end"], unit)])
    k = UNIT_MS.get(str(unit).lower())
    if k:
        step = next((st for st in TIME_STEPS_MS if total * k / st <= 8), TIME_STEPS_MS[-1]) / k
    else:
        step = nice_step(total)
    ticks, t = [], 0.0
    while t <= total + 1e-9:
        ticks.append((X(t0 + t), fmt_dur(t, unit) if k else fmt_num(t) + " " + unit))
        t += step
    spec["edges"] = [{"id": "w-" + s["id"], "from": s["parent"], "to": s["id"], "label": "", "style": "solid", "assumed": False,
                      "evidence": []} for s in spans if s.get("parent") in by_id]
    spec["_findings"] = waterfall_findings(spans, by_id, kids, roots, whole, unit)
    waited = [i for i in order if i in crit and (not any(c in crit for c in kids[i]) or by_id[i]["_self"] >= 0.05 * whole)]
    spec["_waterfall"] = {"ticks": ticks, "bx0": bx0, "bw": bw, "label_w": label_w, "services": services, "total": fmt_dur(whole, unit),
                          "crit": waited}
    return {"w": bx0 + bw + 160, "h": 60 + len(order) * 28 + 40, "groups": []}


def waterfall_findings(spans, by_id, kids, roots, whole, unit):
    """What the trace says about where the time went, computed, so nobody has to add it up:
    the spans with the most time of their own, the ones that mostly wait on their children,
    siblings that overlap (their durations must not be summed), and spans that outlive their
    parent (not part of the wait)."""
    u = lambda v: fmt_dur(v, unit)
    pct = lambda v: "%.0f%%" % (100.0 * v / whole)
    out = []
    if len(roots) == 1:
        r = by_id[roots[0]]
        out.append("The whole of %s took %s." % (r["label"], u(r["_end"] - r["_start"])))
    # what the whole waited on: own time of spans on the critical path (a span running beside a
    # slower sibling, or detached from its parent, cost no wall-clock time)
    own = sorted([s for s in spans if s.get("crit") and not s.get("_detached")], key=lambda s: -s["_self"])
    top = [s for s in own if s["_self"] > 0.05 * whole][:3]
    if top:
        out.append("What the whole waited on most: " + "; ".join("%s, %s of its own work (%s)" % (s["label"], u(s["_self"]), pct(s["_self"])) for s in top) + ".")
    for s in spans:
        dur = s["_end"] - s["_start"]
        if kids[s["id"]] and dur > 0.2 * whole and s["_self"] < 0.1 * dur:
            out.append("%s takes %s but only %s of it is its own; the rest is waiting on what it calls." % (s["label"], u(dur), u(s["_self"])))
    for pid, ks in kids.items():
        ks = sorted(ks, key=lambda i: by_id[i]["_start"])
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                A, B = by_id[a], by_id[b]
                ov = min(A["_end"], B["_end"]) - max(A["_start"], B["_start"])
                if ov > 0.1 * min(A["_end"] - A["_start"], B["_end"] - B["_start"]) and ov > 0.02 * whole:
                    both = (A["_end"] - A["_start"]) + (B["_end"] - B["_start"])
                    wall = max(A["_end"], B["_end"]) - min(A["_start"], B["_start"])
                    out.append("%s and %s run at the same time for %s: together they take %s, not the %s their durations add up to." % (
                        A["label"], B["label"], u(ov), u(wall), u(both)))
    for s in spans:
        p = by_id.get(s.get("parent"))
        if p and s["_end"] > p["_end"] + 1e-9:
            out.append("%s ends %s after %s does, so nothing waited for it: it runs on after its parent (fire-and-forget), or the two clocks disagree." % (
                s["label"], u(s["_end"] - p["_end"]), p["label"]))
    return out


UNIT_MS = {"us": 0.001, "\u00b5s": 0.001, "ms": 1.0, "s": 1000.0, "sec": 1000.0, "min": 60000.0, "m": 60000.0, "h": 3600000.0}
TIME_STEPS_MS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 15000, 30000, 60000, 120000, 300000, 600000,
                 900000, 1800000, 3600000, 7200000, 10800000, 21600000, 43200000, 86400000]


def fmt_dur(v, unit):
    """A duration as a person says it. Units the script doesn't know stay as written."""
    k = UNIT_MS.get(str(unit).lower())
    if k is None:
        return "%s %s" % (fmt_num(v), unit)
    ms = abs(v) * k
    sign = "-" if v < 0 else ""
    if ms < 1000:
        return sign + "%s ms" % fmt_num(ms)
    if ms < 60000:
        return sign + ("%.1f s" % (ms / 1000.0) if ms < 10000 else "%d s" % round(ms / 1000.0))
    if ms < 3600000:
        sec = int(round(ms / 1000.0))
        return sign + "%dm %02ds" % (sec // 60, sec % 60)
    mins = int(round(ms / 60000.0))
    return sign + "%dh %02dm" % (mins // 60, mins % 60)


def fmt_num(v):
    return ("%.1f" % v).rstrip("0").rstrip(".") if abs(v) < 100 else "%d" % round(v)


def waterfall_svg(spec):
    wf = spec["_waterfall"]
    out = ['<g class="axis">']
    for x, lab in wf["ticks"]:
        out.append('<line class="grid" x1="%.1f" y1="44" x2="%.1f" y2="%.1f"/><text x="%.1f" y="38" text-anchor="middle">%s</text>' % (
            x, x, 60 + 28 * len(spec["nodes"]) + 4, x, esc(lab)))
    out.append("</g>")
    for s in sorted(spec["nodes"], key=lambda s: s["row"]):
        cls = ["node", "span"] + (["crit"] if s["crit"] else []) + (["err"] if str(s.get("status", "")).lower() in ("error", "failed", "err") else []) + \
              (["assumed"] if s["assumed"] else [])
        dur = s["facts"][1][1]
        g = ['<g class="%s" id="n-%s" data-id="%s" tabindex="0" role="button" aria-label="%s">' % (
            " ".join(cls), esc(s["id"]), esc(s["id"]), esc("%s, %s" % (s["label"], dur)))]
        g.append("<title>%s — %s</title>" % (esc(s["label"]), esc(dur)))
        g.append('<rect class="rowbg" x="20" y="%.1f" width="%.1f" height="26"/>' % (s["y"] - 4, wf["bx0"] + wf["bw"] + 120))
        label = s["label"]
        while label and text_w(label, 12) + 18 * s["depth"] > wf["label_w"]:
            label = label[:-2]
        if label != s["label"]:
            label = label.rstrip() + "…"
        g.append('<text class="label wf" x="%.1f" y="%.1f">%s</text>' % (30 + 18 * s["depth"], s["y"] + 13, esc(label)))
        g.append('<rect class="shape bar" style="fill:%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3"/>' % (
            s["colour"], s["x"], s["y"], s["w"], s["h"]))
        g.append('<text class="note wf" x="%.1f" y="%.1f">%s</text>' % (s["x"] + s["w"] + 6, s["y"] + 13, esc(dur)))
        g.append("</g>")
        out.append("".join(g))
    return "".join(out)


# --------------------------------------------------------------------------- SVG

def esc(s):
    return html.escape(str(s), quote=True)


def rounded_path(pts, r=7):
    if len(pts) < 2:
        return ""
    d = ["M%.1f,%.1f" % pts[0]]
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1 = max(abs(x1 - x0), abs(y1 - y0))
        l2 = max(abs(x2 - x1), abs(y2 - y1))
        rr = min(r, l1 / 2.0, l2 / 2.0)
        ax_ = x1 - rr * ((x1 > x0) - (x1 < x0)) if abs(x1 - x0) > 0.1 else x1
        ay_ = y1 - rr * ((y1 > y0) - (y1 < y0)) if abs(y1 - y0) > 0.1 else y1
        bx_ = x1 + rr * ((x2 > x1) - (x2 < x1)) if abs(x2 - x1) > 0.1 else x1
        by_ = y1 + rr * ((y2 > y1) - (y2 < y1)) if abs(y2 - y1) > 0.1 else y1
        d.append("L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" % (ax_, ay_, x1, y1, bx_, by_))
    d.append("L%.1f,%.1f" % pts[-1])
    return " ".join(d)


def node_shape(n):
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    s = n["shape"]
    if s == "cylinder":
        ry = 7
        return ('<path class="shape" d="M%.1f,%.1f a%.1f,%d 0 0,1 %.1f,0 v%.1f a%.1f,%d 0 0,1 %.1f,0 z"/>'
                '<path class="shape-line" d="M%.1f,%.1f a%.1f,%d 0 0,0 %.1f,0"/>') % (
            x, y + ry, w / 2, ry, w, h - 2 * ry, w / 2, ry, -w, x, y + ry, w / 2, ry, w)
    if s == "diamond":
        return '<path class="shape" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z"/>' % (
            x + w / 2, y, x + w, y + h / 2, x + w / 2, y + h, x, y + h / 2)
    if s == "terminal":
        return '<rect class="shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/>' % (x, y, w, h, h / 2)
    if s == "round":
        return '<rect class="shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="14"/>' % (x, y, w, h)
    if s == "pipe":
        return ('<rect class="shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="10"/>'
                '<path class="shape-line" d="M%.1f,%.1f v%.1f M%.1f,%.1f v%.1f"/>') % (
            x, y, w, h, x + 10, y + 3, h - 6, x + w - 10, y + 3, h - 6)
    if s == "document":
        return '<path class="shape" d="M%.1f,%.1f h%.1f v%.1f q%.1f,10 %.1f,0 t%.1f,0 Z"/>' % (
            x, y, w, h - 8, -w / 4, -w / 2, -w / 2)
    if s == "person":
        cx = x + w / 2
        return ('<rect class="shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="10"/>'
                '<circle class="glyph" cx="%.1f" cy="%.1f" r="5"/><path class="glyph" d="M%.1f,%.1f a8,7 0 0,1 16,0 z"/>') % (
            x, y, w, h, cx, y + 11, cx - 8, y + 26)
    if s == "initial":
        return '<circle class="shape solid" cx="%.1f" cy="%.1f" r="%.1f"/>' % (x + w / 2, y + h / 2, w / 2 - 3)
    if s == "final":
        return ('<circle class="shape" cx="%.1f" cy="%.1f" r="%.1f"/><circle class="shape solid" cx="%.1f" cy="%.1f" r="%.1f"/>') % (
            x + w / 2, y + h / 2, w / 2 - 1, x + w / 2, y + h / 2, w / 2 - 7)
    rx = 6 if n["kind"] != "external" else 4
    return '<rect class="shape" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d"/>' % (x, y, w, h, rx)


def node_svg(n):
    fam = KINDS.get(n["kind"], ("rect", "slate"))[1]
    cls = ["node", "c-" + fam, "k-" + re.sub(r"[^a-z0-9-]", "", n["kind"])]
    if n["assumed"]:
        cls.append("assumed")
    if n.get("status"):
        cls.append("st-" + n["status"])
    label = esc(n["label"])
    out = ['<g class="%s" id="n-%s" data-id="%s" tabindex="0" role="button" aria-label="%s">' % (
        " ".join(cls), esc(n["id"]), esc(n["id"]), label + (" (assumption)" if n["assumed"] else ""))]
    out.append("<title>%s</title>" % (label + (" — " + esc(n.get("note")) if n.get("note") else "")))
    out.append(node_shape(n))
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    if n["shape"] == "classbox":
        hh = 30 + (14 if n["stereo"] else 0)
        out.append('<rect class="table-head" x="%.1f" y="%.1f" width="%.1f" height="%d" rx="6"/>' % (x, y, w, hh))
        out.append('<rect class="table-head" x="%.1f" y="%.1f" width="%.1f" height="8"/>' % (x, y + hh - 8, w))
        if n["stereo"]:
            out.append('<text class="note" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w / 2, y + 14, esc(n["stereo"])))
        out.append('<text class="label%s" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (
            " italic" if n["kind"] in ("abstract", "interface") else "", x + w / 2, y + hh - 9, label))
        for i, l in enumerate(n["member_lines"]):
            out.append('<text class="fname" x="%.1f" y="%.1f">%s</text>' % (x + 10, y + hh + 16 + 18 * i, esc(l)))
        if len(n["fields"]) > 30:
            out.append('<text class="ftype" x="%.1f" y="%.1f">+%d more (open for all)</text>' % (x + 10, y + hh + 16 + 18 * 30, len(n["fields"]) - 30))
    elif n["shape"] == "table":
        out.append('<rect class="table-head" x="%.1f" y="%.1f" width="%.1f" height="28" rx="6"/>' % (x, y, w))
        out.append('<rect class="table-head" x="%.1f" y="%.1f" width="%.1f" height="8"/>' % (x, y + 20, w))
        out.append('<text class="label" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w / 2, y + 19, label))
        keyw = max([text_w("/".join(k.upper() for k in (f["key"] if isinstance(f.get("key"), list) else [f["key"]])), 9) + 16
                    for f in n["fields"][:24] if f.get("key")] or [0])
        for i, f in enumerate(n["fields"][:24]):
            fy = y + 32 + 20 * i + 14
            key = f.get("key")
            keys = key if isinstance(key, list) else ([key] if key else [])
            if keys:
                out.append('<text class="fkey" x="%.1f" y="%.1f">%s</text>' % (x + 8, fy, esc("/".join(k.upper() for k in keys))))
            out.append('<text class="fname" x="%.1f" y="%.1f">%s</text>' % (x + (keyw + 4 if keyw else 10), fy, esc(f.get("name", ""))))
            if f.get("type"):
                out.append('<text class="ftype" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (x + w - 8, fy, esc(f["type"])))
        if len(n["fields"]) > 24:
            out.append('<text class="ftype" x="%.1f" y="%.1f">+%d more (open for all)</text>' % (x + 10, y + 32 + 20 * 24 + 12, len(n["fields"]) - 24))
    elif n["shape"] in ("initial", "final"):
        for i, l in enumerate(n["lines"]):
            out.append('<text class="note" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w / 2, y + h + 14 + 13 * i, esc(l)))
    else:
        lines = n["lines"]
        notes = n.get("note_lines", [])
        top_pad = 26 if n["shape"] == "person" else (8 if n["shape"] == "cylinder" else 0)
        block = 17 * len(lines) + 15 * len(notes)
        ty = y + top_pad + (h - top_pad - block) / 2.0 + 13
        for l in lines:
            out.append('<text class="label" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w / 2, ty, esc(l)))
            ty += 17
        for l in notes:
            out.append('<text class="note" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (x + w / 2, ty - 1, esc(l)))
            ty += 15
    if n["evidence"] and any(e.get("verified") for e in n["evidence"]):
        out.append('<text class="badge" x="%.1f" y="%.1f" text-anchor="end">✓ src</text>' % (x + w - 5, y - 4))
    elif n["assumed"]:
        out.append('<text class="badge warn" x="%.1f" y="%.1f" text-anchor="end">assumed</text>' % (x + w - 5, y - 4))
    out.append("</g>")
    return "".join(out)


def place_labels(spec, occupied):
    """Put each edge label on a segment of its own route where it overlaps nothing placed."""
    def hit(r, rs):
        for o in rs:
            if r[0] < o[2] and r[2] > o[0] and r[1] < o[3] and r[3] > o[1]:
                return True
        return False
    segs_all = []
    for e in spec["edges"]:
        pts = e.get("pts", [])
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            segs_all.append((e["id"], (min(x0, x1) - 2, min(y0, y1) - 2, max(x0, x1) + 2, max(y0, y1) + 2)))
    for e in spec["edges"]:
        if not e.get("label") or len(e.get("pts", [])) < 2:
            continue
        others = [r for (eid, r) in segs_all if eid != e["id"]]
        lines = wrap(e["label"], 150, 11, 2)
        w = max(text_w(l, 11) for l in lines) + 10
        h = 14 * len(lines) + 4
        pts = e["pts"]
        segs = sorted(range(len(pts) - 1), key=lambda i: -(abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1])))
        cands = []
        for i in segs:
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            for f in (0.5, 0.3, 0.7, 0.15, 0.85):
                cands.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
        best = None
        for cx, cy in cands:
            r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if not hit(r, occupied) and not hit(r, others):
                best = r
                break
        if best is None:
            for cx, cy in cands:
                r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                if not hit(r, occupied):
                    best = r
                    break
        if best is None:
            cx, cy = cands[0]
            best = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        occupied.append(best)
        e["label_box"] = best
        e["label_lines"] = lines


def edge_svg(e, seq=False):
    cls = ["edge", "s-" + e["style"]]
    if e["assumed"]:
        cls.append("assumed")
    if e.get("status"):
        cls.append("st-" + e["status"])
    if e.get("emphasis"):
        cls.append("emph")
    if seq and e.get("kind") == "return":
        cls.append("s-dashed")
    title = esc(e["label"] or "%s → %s" % (e["from"], e["to"]))
    out = ['<g class="%s" id="e-%s" data-id="%s" data-from="%s" data-to="%s">' % (
        " ".join(cls + (["tree"] if e.get("tree") else [])), esc(e["id"]), esc(e["id"]), esc(e["from"]), esc(e["to"]))]
    out.append("<title>%s</title>" % title)
    d = rounded_path(e["pts"]) if not seq else "M" + " L".join("%.1f,%.1f" % p for p in e["pts"])
    rel = e.get("rel")
    if e.get("tree"):
        markers = ""
    elif rel in ("inherits", "implements"):
        markers = ' marker-end="url(#tri)"'
    elif rel == "composition":
        markers = ' marker-start="url(#dia-solid)"'
    elif rel == "aggregation":
        markers = ' marker-start="url(#dia-open)"'
    elif rel in ("association", "dependency"):
        markers = ' marker-end="url(#open)"'
    else:
        markers = ' marker-end="url(#arrow)"' + (' marker-start="url(#arrow-start)"' if e.get("both") else "")
    out.append('<path class="hit" d="%s"/>' % d)
    out.append('<path class="line" d="%s"%s/>' % (d, markers))
    if seq and e.get("lines"):
        x, y, anchor = e["label_at"]
        for i, l in enumerate(e["lines"]):
            out.append('<text class="elabel" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (x, y + 14 * i, anchor, esc(l)))
    elif e.get("label_box"):
        x0, y0, x1, y1 = e["label_box"]
        out.append('<rect class="lbg" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3"/>' % (x0, y0, x1 - x0, y1 - y0))
        for i, l in enumerate(e["label_lines"]):
            out.append('<text class="elabel" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % ((x0 + x1) / 2, y0 + 13 + 14 * i, esc(l)))
    for key, at in (("from_card", 0), ("to_card", -1)):
        if e.get(key) and len(e["pts"]) >= 2:
            p, q = e["pts"][at], e["pts"][1 if at == 0 else -2]
            dx = 1 if q[0] > p[0] else -1
            out.append('<text class="card" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (
                p[0] + (6 if at == 0 else 14) * dx, p[1] - 6, "start" if dx > 0 else "end", esc(e[key])))
    out.append("</g>")
    return "".join(out)


def render_svg(spec, geo):
    W, H = geo["w"], geo["h"]
    seq = spec["type"] == "sequence"
    out = ['<svg id="map" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="group" aria-label="%s">' % (
        W, H, W, H, esc(spec["title"]))]
    out.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto-start-reverse">'
               '<path d="M0,0 L10,5 L0,10 z" class="arrowhead"/></marker>'
               '<marker id="arrow-start" viewBox="0 0 10 10" refX="1" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto-start-reverse">'
               '<path d="M0,0 L10,5 L0,10 z" class="arrowhead"/></marker>'
               '<marker id="tri" viewBox="0 0 12 12" refX="11" refY="6" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" orient="auto-start-reverse">'
               '<path d="M1,1 L11,6 L1,11 z" class="mk-open"/></marker>'
               '<marker id="open" viewBox="0 0 12 12" refX="11" refY="6" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto-start-reverse">'
               '<path d="M1,1 L11,6 L1,11" class="mk-line"/></marker>'
               '<marker id="dia-solid" viewBox="0 0 16 10" refX="15" refY="5" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="11" orient="auto-start-reverse">'
               '<path d="M1,5 L8,1 L15,5 L8,9 z" class="arrowhead"/></marker>'
               '<marker id="dia-open" viewBox="0 0 16 10" refX="15" refY="5" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="11" orient="auto-start-reverse">'
               '<path d="M1,5 L8,1 L15,5 L8,9 z" class="mk-open"/></marker></defs>')
    out.append('<rect class="canvas" x="0" y="0" width="%d" height="%d"/>' % (W, H))
    labels = {g["id"]: g for g in spec["groups"]}
    for g in sorted(geo["groups"], key=lambda g: g["depth"]):
        meta = labels.get(g["id"], {})
        cls = "group d%d" % min(g["depth"], 3) + (" st-" + meta["status"] if meta.get("status") else "")
        out.append('<g class="%s" data-group="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="10"/>'
                   '<text class="glabel" x="%.1f" y="%.1f">%s</text></g>' % (
                       cls, esc(g["id"]), g["x"], g["y"], g["w"], g["h"], g["x"] + 12, g["y"] + 18,
                       esc(meta.get("label", g["id"]) + (" (continued)" if g.get("cont") else ""))))
    if seq:
        y0, y1 = geo["lifeline"]
        for f in spec["frames"]:
            if "y0" in f and "y1" in f:
                lab = "%s %s" % (f.get("kind", "group"), f.get("label", ""))
                out.append('<g class="frame"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>'
                           '<rect class="ftab" x="%.1f" y="%.1f" width="%.1f" height="18"/><text x="%.1f" y="%.1f">%s</text></g>' % (
                               f["x0"], f["y0"], f["x1"] - f["x0"], f["y1"] - f["y0"], f["x0"], f["y0"], text_w(lab, 11) + 14,
                               f["x0"] + 7, f["y0"] + 13, esc(lab.strip())))
        for p in spec["nodes"]:
            out.append('<line class="lifeline" data-for="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
                esc(p["id"]), p["cx"], p["y"] + p["h"], p["cx"], y1))
        for i, m in enumerate(spec["edges"]):
            if m.get("pts"):
                out.append('<text class="seqno" x="%.1f" y="%.1f">%d</text>' % (14, m["pts"][0][1] + 4, i + 1))
    if spec["type"] == "timeline":
        out.append(timeline_svg(spec))
    elif spec["type"] == "waterfall":
        out.append(waterfall_svg(spec))
    else:
        for e in spec["edges"]:
            if e.get("pts"):
                out.append(edge_svg(e, seq))
        for n in spec["nodes"]:
            out.append(node_svg(n))
    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------------- Mermaid

def mm_text(s):
    return str(s).replace('"', "#quot;").replace("\n", " ")


def mm_id(s):
    return re.sub(r"[^A-Za-z0-9_]", "_", s) or "n"


def to_mermaid(spec):
    t = spec["type"]
    nodes = [n for n in spec["nodes"] if n.get("status") != "removed"]
    edges = [e for e in spec["edges"] if e.get("status") != "removed"]
    if t == "tree":
        out = ["flowchart LR"] + ['    %s["%s"]' % (mm_id(n["id"]), mm_text(n["label"])) for n in nodes]
        out += ["    %s --- %s" % (mm_id(n["parent"]), mm_id(n["id"])) for n in nodes if n.get("parent")]
        return "\n".join(out) + "\n"
    if t == "timeline":
        groups = {g["id"]: g["label"] for g in spec["groups"]}
        out = ["timeline", "    title %s" % mm_text(spec["title"]).replace(":", " -")]
        lanes = []
        for n in nodes:
            ln = n.get("lane") or n.get("group") or ""
            if ln not in lanes:
                lanes.append(ln)
        for ln in lanes:
            if ln:
                out.append("    section %s" % mm_text(groups.get(ln, ln)).replace(":", " -"))
            for n in sorted([n for n in nodes if (n.get("lane") or n.get("group") or "") == ln], key=lambda n: n["_t"][0]):
                out.append("        %s : %s" % (mm_text(n["when"]).replace(":", "."), mm_text(n["label"]).replace(":", " -")))
        return "\n".join(out) + "\n"
    if t == "waterfall":
        t0 = min(n["_start"] for n in nodes)
        out = ["gantt", "    title %s" % mm_text(spec["title"]).replace(":", " -"), "    dateFormat x", "    axisFormat %S.%L"]
        svcs = []
        for n in sorted(nodes, key=lambda n: n.get("row", 0)):
            svc = n.get("service") or "spans"
            if svc not in svcs:
                svcs.append(svc)
        for svc in svcs:
            out.append("    section %s" % mm_text(svc).replace(":", " -"))
            for n in sorted([n for n in nodes if (n.get("service") or "spans") == svc], key=lambda n: n.get("row", 0)):
                tag = "crit, " if n.get("crit") else ""
                out.append("    %s :%s%s, %d, %d" % (mm_text(n["label"]).replace(":", " -"), tag, mm_id(n["id"]),
                                                    round(n["_start"] - t0), max(round(n["_end"] - t0), round(n["_start"] - t0) + 1)))
        return "\n".join(out) + "\n"
    if t == "class":
        out = ["classDiagram"]
        if spec["direction"] == "LR":
            out.append("    direction LR")
        for n in nodes:
            out.append("    class %s {" % mm_id(n["label"]))
            if n["kind"] != "class":
                out.append("        <<%s>>" % n["kind"])
            for f in n["fields"]:
                out.append("        %s" % mm_text(member_text(f)).replace("{", "(").replace("}", ")"))
            out.append("    }")
        name = {n["id"]: mm_id(n["label"]) for n in nodes}
        arrow = {"inherits": "--|>", "implements": "..|>", "composition": "*--", "aggregation": "o--",
                 "association": "-->", "dependency": "..>"}
        for e in edges:
            lab = (" : " + mm_text(e["label"])) if e["label"] else ""
            out.append("    %s %s %s%s" % (name[e["from"]], arrow[e["rel"]], name[e["to"]], lab))
        return "\n".join(out) + "\n"
    if t == "sequence":
        out = ["sequenceDiagram"]
        for p in nodes:
            out.append('    %s %s as %s' % ("actor" if p["kind"] in ("person", "actor") else "participant", mm_id(p["id"]), mm_text(p["label"]).replace(";", ",")))
        opens = {}
        closes = {}
        for f in spec["frames"]:
            opens.setdefault(f.get("from"), []).append(f)
            closes.setdefault(f.get("to"), []).append(f)
        for m in edges:
            for f in opens.get(m["id"], []):
                out.append("    %s %s" % (f.get("kind", "rect") if f.get("kind") in ("loop", "alt", "opt", "par", "critical", "break") else "opt",
                                          mm_text(f.get("label", ""))))
            arrow = "-->>" if m.get("kind") == "return" else ("-)" if m.get("kind") == "async" else "->>")
            out.append("    %s%s%s: %s" % (mm_id(m["from"]), arrow, mm_id(m["to"]), mm_text(m["label"]).replace(";", ",") or " "))
            for f in closes.get(m["id"], []):
                out.append("    end")
        return "\n".join(out) + "\n"
    if t == "lifecycle":
        out = ["stateDiagram-v2"]
        if spec["direction"] == "LR":
            out.append("    direction LR")
        for n in nodes:
            if n["shape"] not in ("initial", "final"):
                out.append('    state "%s" as %s' % (mm_text(n["label"]), mm_id(n["id"])))
        kinds = {n["id"]: n["shape"] for n in nodes}
        for e in edges:
            a = "[*]" if kinds.get(e["from"]) == "initial" else mm_id(e["from"])
            b = "[*]" if kinds.get(e["to"]) == "final" else mm_id(e["to"])
            out.append("    %s --> %s%s" % (a, b, (": " + mm_text(e["label"])) if e["label"] else ""))
        return "\n".join(out) + "\n"
    if t == "erd":
        out = ["erDiagram"]
        left = {"0..1": "|o", "1": "||", "1..1": "||", "1..*": "}|", "*": "}o", "0..*": "}o", "n": "}o", "many": "}o", "m": "}o"}
        right = {"0..1": "o|", "1": "||", "1..1": "||", "1..*": "|{", "*": "o{", "0..*": "o{", "n": "o{", "many": "o{", "m": "o{"}
        name = {n["id"]: mm_id(n["label"]) for n in nodes}
        for e in edges:
            l = left.get(str(e.get("from_card", "*")).lower(), "}o")
            r = right.get(str(e.get("to_card", "1")).lower(), "||")
            out.append('    %s %s--%s %s : "%s"' % (name[e["from"]], l, r, name[e["to"]], mm_text(e["label"] or "has")))
        for n in nodes:
            out.append("    %s {" % name[n["id"]])
            for f in n["fields"]:
                keys = f.get("key")
                keys = keys if isinstance(keys, list) else ([keys] if keys else [])
                ks = ",".join(k.upper() for k in keys if k.lower() in ("pk", "fk", "uk"))
                out.append("        %s %s%s" % (mm_id(str(f.get("type") or "string")), mm_id(f.get("name", "field")), (" " + ks) if ks else ""))
            out.append("    }")
        return "\n".join(out) + "\n"
    out = ["flowchart " + spec["direction"]]
    shapes = {"cylinder": ('[("', '")]'), "diamond": ('{"', '"}'), "terminal": ('(["', '"])'), "round": ('("', '")'),
              "pipe": ('[["', '"]]'), "document": ('[/"', '"/]'), "person": ('(["', '"])'), "initial": ('(("', '"))'),
              "final": ('((("', '")))'), "table": ('["', '"]')}

    def decl(n, indent):
        a, b = shapes.get(n["shape"], ('["', '"]'))
        return "%s%s%s%s%s" % (indent, mm_id(n["id"]), a, mm_text(n["label"]), b)
    groups, kids, top = group_tree(spec)
    members = {}
    for n in nodes:
        members.setdefault(n.get("group"), []).append(n)

    def emit(gid, depth):
        ind = "    " * depth
        out.append('%ssubgraph %s["%s"]' % (ind, mm_id(gid), mm_text(groups[gid]["label"])))
        for n in members.get(gid, []):
            out.append(decl(n, ind + "    "))
        for k in kids[gid]:
            emit(k, depth + 1)
        out.append(ind + "end")
    for n in members.get(None, []):
        out.append(decl(n, "    "))
    for g in top:
        emit(g, 1)
    for e in edges:
        arrow = "-.->" if e["style"] != "solid" or e["assumed"] else ("==>" if e.get("emphasis") else "-->")
        if e.get("both"):
            arrow = "<" + arrow
        lab = '|"%s"|' % mm_text(e["label"]) if e["label"] else ""
        out.append("    %s %s%s %s" % (mm_id(e["from"]), arrow, lab, mm_id(e["to"])))
    assumed = [mm_id(n["id"]) for n in nodes if n["assumed"]]
    if assumed:
        out.append("    classDef assumed stroke-dasharray: 5 4")
        out.append("    class %s assumed" % ",".join(assumed))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- text outline

def outline_special(spec, evs, assumed):
    t = spec["type"]
    if t == "tree":
        kids = {}
        for n in spec["nodes"]:
            kids.setdefault(n.get("parent"), []).append(n)

        def ul(parent):
            items = kids.get(parent, [])
            if not items:
                return ""
            return "<ul>" + "".join("<li><b>%s</b>%s%s%s%s</li>" % (
                esc(n["label"]), (" \u2014 " + esc(n["note"])) if n.get("note") else "", assumed(n), evs(n), ul(n["id"])) for n in items) + "</ul>"
        return "<h2>What contains what</h2>" + ul(None)
    if t == "timeline":
        groups = {g["id"]: g["label"] for g in spec["groups"]}
        rows = sorted(spec["nodes"], key=lambda n: n["_t"][0])
        tl = spec.get("_timeline") or {}
        head = "<p>%s to %s (%s).</p>" % (esc(tl.get("start", "")), esc(tl.get("end", "")), esc(tl.get("span", ""))) if tl else ""
        return "<h2>Events, in time order</h2>" + head + "<ol>" + "".join("<li><b>%s</b> %s%s%s%s</li>" % (
            esc(n["when"]), esc(n["label"]), (" <span class=\"muted\">(%s)</span>" % esc(groups.get(n.get("lane") or n.get("group"), n.get("lane") or n.get("group"))))
            if (n.get("lane") or n.get("group")) else "", assumed(n), evs(n)) for n in rows) + "</ol>"
    if t == "waterfall":
        wf = spec.get("_waterfall") or {}
        rows = sorted(spec["nodes"], key=lambda n: n.get("row", 0))
        return ("<h2>Spans, in call order</h2><p>Total %s. What it waited on, in order: %s.</p><ul>" % (
            esc(wf.get("total", "")), esc(" \u2192 ".join(next(n["label"] for n in rows if n["id"] == i) for i in wf.get("crit", [])))) +
            "".join("<li>%s<b>%s</b>: starts at %s, takes %s (%s)%s%s</li>" % (
                "\u2003" * n.get("depth", 0), esc(n["label"]), esc(n["facts"][0][1]), esc(n["facts"][1][1]), esc(n["facts"][2][1]),
                assumed(n), evs(n)) for n in rows) + "</ul>")
    return None


def outline_html(spec):
    """The map as text: what a screen reader, a search engine, a judge or a reader without
    JavaScript gets, and what can be pasted into a doc."""
    t = spec["type"]
    by_id = {n["id"]: n for n in spec["nodes"]}
    lab = lambda i: by_id[i]["label"] if i in by_id else i
    out = []
    groups = {g["id"]: g for g in spec["groups"]}

    def status(x):
        s = x.get("status")
        return ' <span class="tag st-%s">%s</span>' % (s, s) if s else ""

    def assumed(x):
        return ' <span class="tag warn">assumption</span>' if x.get("assumed") else ""

    def evs(x):
        if not x["evidence"]:
            return ""
        parts = []
        for e in x["evidence"]:
            mark = " ✓" if e.get("verified") else ""
            parts.append("<code>%s</code>%s" % (esc(ev_text(e)), mark))
        return ' <span class="ev">(%s)</span>' % ", ".join(parts)
    found = ""  # the findings sit at the top of the page
    special = outline_special(spec, evs, assumed)
    if special is not None:
        return found + special
    if special is not None:
        return special
    noun = {"sequence": "Participants", "erd": "Tables", "lifecycle": "States", "class": "Types"}.get(t, "Parts")
    out.append("<h2>%s</h2><ul>" % noun)
    for n in spec["nodes"]:
        g = groups.get(n.get("group"))
        extra = " — %s" % esc(n["note"]) if n.get("note") else ""
        ing = " <span class=\"muted\">in %s</span>" % esc(g["label"]) if g else ""
        fields = ""
        if n["fields"]:
            fields = "<ul>" + "".join("<li><code>%s</code> %s%s</li>" % (
                esc(f.get("name", "")), esc(f.get("type", "")),
                (" <b>%s</b>" % esc("/".join(f["key"]) if isinstance(f.get("key"), list) else f["key"]).upper()) if f.get("key") else "")
                for f in n["fields"]) + "</ul>"
        out.append("<li><b>%s</b>%s%s%s%s%s%s</li>" % (esc(n["label"]), extra, ing, assumed(n), status(n), evs(n), fields))
    out.append("</ul>")
    noun = "Messages, in order" if t == "sequence" else ("Relationships" if t == "erd" else "Connections")
    out.append("<h2>%s</h2><ol>" % noun if t == "sequence" else "<h2>%s</h2><ul>" % noun)
    for e in spec["edges"]:
        card = ""
        if e.get("from_card") or e.get("to_card"):
            card = " <span class=\"muted\">(%s to %s)</span>" % (esc(e.get("from_card", "?")), esc(e.get("to_card", "?")))
        out.append("<li>%s → %s%s%s%s%s%s</li>" % (esc(lab(e["from"])), esc(lab(e["to"])),
                                                    (": " + esc(e["label"])) if e["label"] else "", card, assumed(e), status(e), evs(e)))
    out.append("</ol>" if t == "sequence" else "</ul>")
    if spec["story"]:
        out.append("<h2>Walkthrough</h2><ol>" + "".join("<li>%s</li>" % esc(s.get("text", "")) for s in spec["story"]) + "</ol>")
    return "".join(out)


# --------------------------------------------------------------------------- HTML

CSS = r"""
:root{--bg:#f7f8fa;--panel:#ffffff;--ink:#16181d;--muted:#5b6170;--line:#d5d9e0;--edge:#6b7385;--accent:#2563eb;
--warn:#b45309;--ok:#15803d;--bad:#b91c1c;--hl:#f59e0b;--canvas:#fbfcfd;--group:#eef1f6;--group2:#e6eaf2;--shadow:0 1px 2px rgba(0,0,0,.06)}
:root[data-theme=dark]{--bg:#0f1115;--panel:#171a21;--ink:#e7e9ee;--muted:#9aa1b2;--line:#2b303b;--edge:#8b93a7;--accent:#60a5fa;
--warn:#f59e0b;--ok:#4ade80;--bad:#f87171;--hl:#fbbf24;--canvas:#12151b;--group:#1a1e27;--group2:#20252f;--shadow:none}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
body{display:flex;flex-direction:column}body>*{flex:none}section.text{order:10}
header.top{padding:18px 24px 10px;max-width:1400px}header.top h1{margin:0 0 4px;font-size:21px}
.q{color:var(--muted);margin:0 0 6px}.sum{margin:0;max-width:900px}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:8px 24px;position:sticky;top:0;background:var(--bg);z-index:5;border-bottom:1px solid var(--line)}
.bar button,.bar input{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:6px;padding:4px 9px;cursor:pointer}
.bar input{cursor:text;width:180px}.bar button:hover{border-color:var(--accent)}.bar .sep{width:1px;height:20px;background:var(--line);margin:0 4px}
.bar .hint{color:var(--muted);font-size:12px;margin-left:auto}
.wrap{display:flex;gap:0;height:calc(100vh - 150px);min-height:420px;padding:10px 24px 0}
#stage{flex:1;position:relative;overflow:hidden;border:1px solid var(--line);border-radius:10px;background:var(--canvas);touch-action:none;cursor:grab}
#stage.drag{cursor:grabbing}#stage svg{position:absolute;left:0;top:0;width:100%;height:100%}
aside#panel{width:340px;margin-left:12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);overflow:auto;padding:14px 16px;display:none}
aside#panel.open{display:block}aside h3{margin:0 0 2px;font-size:16px}aside .kind{color:var(--muted);font-size:12px;margin-bottom:8px}
aside .close{float:right;border:0;background:none;color:var(--muted);font-size:18px;cursor:pointer}
aside pre{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;overflow:auto;font-size:12px;max-height:260px}
aside ul{padding-left:18px;margin:4px 0}aside a.jump{color:var(--accent);cursor:pointer;text-decoration:none}
aside .acts button{font:inherit;font-size:12px;margin:2px 4px 2px 0;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:5px;padding:3px 7px;cursor:pointer}
.caption{display:none;margin:8px 24px 0;padding:8px 12px;border-left:3px solid var(--hl);background:var(--panel);border-radius:4px}
.caption.on{display:block}
section.text{max-width:1100px;padding:10px 24px 40px}section.text h2{font-size:15px;margin:18px 0 4px}
.tag{font-size:11px;padding:0 5px;border-radius:4px;border:1px solid var(--line);margin-left:4px}.tag.warn{color:var(--warn);border-color:var(--warn)}
.tag.st-added{color:var(--ok);border-color:var(--ok)}.tag.st-removed{color:var(--bad);border-color:var(--bad)}.tag.st-changed{color:var(--accent);border-color:var(--accent)}
.muted{color:var(--muted)}.ev{color:var(--muted);font-size:12px}code{font-size:12px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted);padding:6px 24px 0}
.legend i{display:inline-block;width:22px;height:0;border-top:2px solid var(--edge);vertical-align:middle;margin-right:5px}
.legend i.d{border-top-style:dashed}.legend i.a{border-top:2px dashed var(--warn)}
.findings{margin:10px 0 0;padding:8px 14px;border-left:3px solid var(--accent);background:var(--panel);border-radius:4px;max-width:1000px}
.findings ul{margin:4px 0 0;padding-left:18px}.findings li{margin:2px 0}
table.answers{border-collapse:collapse;margin:10px 0 0;max-width:1100px;font-size:13px}
table.answers th,table.answers td{border:1px solid var(--line);padding:5px 9px;text-align:left;vertical-align:top}
table.answers th{background:var(--group2);font-weight:600}table.answers td.ev{font-size:12px;color:var(--muted)}
.issues{margin:8px 24px 0;padding:8px 12px;border:1px solid var(--warn);border-radius:6px;color:var(--warn);font-size:13px}
/* diagram */
.canvas{fill:var(--canvas)}
.group rect{fill:var(--group);stroke:var(--line);stroke-width:1}.group.d2 rect{fill:var(--group2)}.group.d3 rect{fill:var(--group)}
.glabel{font-size:12px;font-weight:600;fill:var(--muted);letter-spacing:.02em}
.group.st-removed rect{stroke:var(--bad);stroke-dasharray:6 4;fill:none}
.node{cursor:pointer;outline:none}.node .shape{stroke-width:1.5;fill:var(--panel)}.node .shape.solid{fill:var(--ink);stroke:var(--ink)}
.node .shape-line{fill:none;stroke-width:1.2}.node .glyph{fill:var(--muted)}
.node .label{font-size:13px;font-weight:600;fill:var(--ink)}.node .note{font-size:11px;fill:var(--muted)}
.node .badge{font-size:10px;fill:var(--ok)}.node .badge.warn{fill:var(--warn)}
.table-head{fill:var(--group2)}.fname{font-size:12px;fill:var(--ink)}.ftype{font-size:11px;fill:var(--muted)}.fkey{font-size:9px;font-weight:700;fill:var(--warn)}
.c-blue .shape,.c-blue .shape-line{stroke:#3b82f6}.c-violet .shape{stroke:#8b5cf6}.c-green .shape,.c-green .shape-line{stroke:#16a34a}
.c-teal .shape,.c-teal .shape-line{stroke:#0d9488}.c-amber .shape,.c-amber .shape-line{stroke:#d97706}.c-slate .shape{stroke:#64748b}
.c-rose .shape{stroke:#e11d48}.c-indigo .shape{stroke:#4f46e5}.k-external .shape{stroke-dasharray:5 3}
.node.assumed .shape{stroke:var(--warn)!important;stroke-dasharray:6 4}
.node.st-added .shape{stroke:var(--ok)!important;stroke-width:2.5}.node.st-changed .shape{stroke:var(--accent)!important;stroke-width:2.5}
.node.st-removed{opacity:.55}.node.st-removed .shape{stroke:var(--bad)!important;stroke-dasharray:6 4}.node.st-removed .label{text-decoration:line-through}
.edge .line{fill:none;stroke:var(--edge);stroke-width:1.5}.edge .hit{fill:none;stroke:transparent;stroke-width:12;cursor:pointer}
.edge.s-dashed .line{stroke-dasharray:7 5}.edge.s-dotted .line{stroke-dasharray:2 4}.edge.emph .line{stroke-width:2.6}
.edge.assumed .line{stroke:var(--warn);stroke-dasharray:6 4}.edge.st-added .line{stroke:var(--ok);stroke-width:2.2}
.edge.st-removed .line{stroke:var(--bad);stroke-dasharray:6 4;opacity:.7}
.arrowhead{fill:var(--edge)}.lbg{fill:var(--canvas);opacity:.92}.elabel{font-size:11px;fill:var(--muted)}.card{font-size:11px;font-weight:700;fill:var(--muted)}
.lifeline{stroke:var(--line);stroke-width:1.2;stroke-dasharray:4 4}.seqno{font-size:10px;fill:var(--muted)}
.frame rect{fill:none;stroke:var(--muted);stroke-width:1}.frame .ftab{fill:var(--group2);stroke:var(--muted)}.frame text{font-size:11px;fill:var(--ink);font-weight:600}
svg.focus .node,svg.focus .edge,svg.focus .group{opacity:.18;transition:opacity .15s}
svg.focus .on,svg.focus .group.on{opacity:1}svg .node.on .shape{stroke-width:2.6}svg .edge.on .line{stroke:var(--hl);stroke-width:2.6}
svg .node.sel .shape{stroke:var(--hl)!important;stroke-width:3}svg .node:focus-visible .shape{stroke:var(--accent)!important;stroke-width:3}
@media (prefers-reduced-motion:no-preference){svg .edge.on.flow .line{stroke-dasharray:8 6;animation:flow 1s linear infinite}}
@keyframes flow{to{stroke-dashoffset:-28}}
.lane rect{fill:var(--group);stroke:var(--line)}.lane-line{stroke:var(--line);stroke-width:2}
.axis line{stroke:var(--muted);stroke-width:1}.axis text{font-size:11px;fill:var(--muted)}.axis .grid{stroke:var(--line);stroke-dasharray:2 4}
.brk{stroke:var(--muted);stroke-width:1.5;fill:none}.brk-label{font-size:10px;fill:var(--muted)}
.node.event .shape{stroke-width:2;fill:var(--panel)}.node.event .bar{fill:var(--group2);stroke-width:1.5}
.node.event .leader{stroke:var(--line);stroke-width:1}.node.event.approx .shape{stroke-dasharray:3 2}.node .label.tl{font-size:12px}.node .note.tl{font-size:10px}
.node.span .rowbg{fill:transparent}.node.span:hover .rowbg,.node.span.on .rowbg{fill:var(--group)}
.node.span .bar{stroke:none;opacity:.88}.node.span.crit .bar{stroke:var(--hl);stroke-width:2.5;opacity:1}
.node.span.err .bar{stroke:var(--bad);stroke-width:2.5}.node .label.wf{font-size:12px;font-weight:500}.node .note.wf{font-size:11px}
.node .label.italic{font-style:italic}.mk-open{fill:var(--canvas);stroke:var(--edge);stroke-width:1.2}.mk-line{fill:none;stroke:var(--edge);stroke-width:1.4}
.edge.tree .line{stroke:var(--line);stroke-width:1.5}
aside table.facts{border-collapse:collapse;font-size:13px;margin:6px 0}aside table.facts th{text-align:left;color:var(--muted);font-weight:400;padding:2px 10px 2px 0}
@media print{.bar,aside,.caption{display:none!important}.wrap{height:auto}#stage{border:0}#stage svg{position:static;height:auto}}
"""

JS = r"""
(function(){
var DATA=JSON.parse(document.getElementById('diagram-data').textContent);var WD=DATA.words;
var svg=document.getElementById('map'),stage=document.getElementById('stage'),panel=document.getElementById('panel');
var root=document.documentElement;
var pref=null;try{pref=localStorage.getItem('idg-theme')}catch(e){}pref=pref||root.getAttribute('data-theme-default');
if(pref==='auto'||!pref){pref=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}
root.setAttribute('data-theme',pref);
var W=+svg.getAttribute('width'),H=+svg.getAttribute('height');svg.removeAttribute('width');svg.removeAttribute('height');
var vb={x:0,y:0,w:W,h:H};
function apply(){svg.setAttribute('viewBox',vb.x+' '+vb.y+' '+vb.w+' '+vb.h)}
function fit(){var r=stage.getBoundingClientRect();var s=Math.max(W/r.width,H/r.height,0.6);vb.w=r.width*s;vb.h=r.height*s;vb.x=(W-vb.w)/2;vb.y=(H-vb.h)/2;apply()}
function zoom(f,cx,cy){var r=stage.getBoundingClientRect();if(cx==null){cx=r.width/2;cy=r.height/2}
 var px=vb.x+cx/r.width*vb.w,py=vb.y+cy/r.height*vb.h;var nw=Math.min(Math.max(vb.w*f,120),W*6);var k=nw/vb.w;
 vb.x=px-(px-vb.x)*k;vb.y=py-(py-vb.y)*k;vb.w=nw;vb.h=vb.h*k;apply()}
stage.addEventListener('wheel',function(e){e.preventDefault();var r=stage.getBoundingClientRect();zoom(e.deltaY>0?1.12:1/1.12,e.clientX-r.left,e.clientY-r.top)},{passive:false});
var drag=null;
stage.addEventListener('pointerdown',function(e){if(e.target.closest('.node')||e.target.closest('.edge'))return;drag={x:e.clientX,y:e.clientY,vx:vb.x,vy:vb.y};stage.classList.add('drag');stage.setPointerCapture(e.pointerId)});
stage.addEventListener('pointermove',function(e){if(!drag)return;var r=stage.getBoundingClientRect();vb.x=drag.vx-(e.clientX-drag.x)*vb.w/r.width;vb.y=drag.vy-(e.clientY-drag.y)*vb.h/r.height;apply()});
stage.addEventListener('pointerup',function(){drag=null;stage.classList.remove('drag')});
// Lookups are Maps, never plain objects: ids come from the spec and the URL, and a key such as
// __proto__ must stay a key.
var nodes=new Map(),edges=new Map(),outE=new Map(),inE=new Map();
DATA.nodes.forEach(function(n){nodes.set(n.id,n);outE.set(n.id,[]);inE.set(n.id,[])});
DATA.edges.forEach(function(e){edges.set(e.id,e);if(outE.has(e.from))outE.get(e.from).push(e.id);if(inE.has(e.to))inE.get(e.to).push(e.id)});
function el(kind,id){return document.getElementById(kind+'-'+id)}
function clear(){svg.classList.remove('focus');svg.querySelectorAll('.on,.sel,.flow').forEach(function(x){x.classList.remove('on','sel','flow')})}
function light(ns,es,flow){clear();svg.classList.add('focus');ns.forEach(function(i){var x=el('n',i);x&&x.classList.add('on')});
 es.forEach(function(i){var x=el('e',i);if(x){x.classList.add('on');flow&&x.classList.add('flow')}})}
function reach(id,dir){if(!nodes.has(id))return {n:[],e:[]};var seen=new Set([id]),es=[],q=[id];while(q.length){var u=q.shift();(dir>0?outE.get(u):inE.get(u)).forEach(function(eid){var e=edges.get(eid);es.push(eid);var v=dir>0?e.to:e.from;if(!seen.has(v)){seen.add(v);q.push(v)}})}
 return {n:Array.from(seen),e:es}}
function path(a,b,directed){if(!nodes.has(a)||!nodes.has(b))return null;var prev=new Map([[a,null]]),q=[a];while(q.length){var u=q.shift();if(u===b)break;
 var nb=outE.get(u).map(function(i){return [edges.get(i).to,i]});if(!directed)nb=nb.concat(inE.get(u).map(function(i){return [edges.get(i).from,i]}));
 nb.forEach(function(p){if(!prev.has(p[0])){prev.set(p[0],[u,p[1]]);q.push(p[0])}})}
 if(!prev.has(b))return null;var ns=[b],es=[],c=b;while(prev.get(c)){es.push(prev.get(c)[1]);c=prev.get(c)[0];ns.push(c)}return {n:ns.reverse(),e:es.reverse()}}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function evHtml(list){if(!list||!list.length)return '<p class="muted">No evidence cited.</p>';
 return '<ul>'+list.map(function(e){var t=e.said!=null?(esc(e.source||'user')+': “'+esc(e.said)+'”'):esc(e.file+(e.start?':'+e.start+(e.end!==e.start?'-'+e.end:''):''));
  if(e.file&&DATA.source_url){t='<a href="'+esc(DATA.source_url.replace(/\/?$/,'/')+e.file+(e.start?'#L'+e.start+(e.end!==e.start?'-L'+e.end:''):''))+'" target="_blank" rel="noopener">'+t+'</a>'}
  var v=e.verified===true?' <span class="tag" style="color:var(--ok)">checked</span>':(e.verified===null&&e.file?' <span class="tag">not checked</span>':'');
  return '<li>'+t+v+(e.snippet?'<pre>'+esc(e.snippet)+'</pre>':'')+'</li>'}).join('')+'</ul>'}
var selected=null;
function show(kind,id){var x=kind==='n'?nodes.get(id):edges.get(id);if(!x)return;var h='<button class="close" aria-label="Close">×</button>';
 if(kind==='n'){h+='<h3>'+esc(x.label)+'</h3><div class="kind">'+esc(x.kind)+(x.group_label?' · '+esc(x.group_label):'')+(x.assumed?' · <span style="color:var(--warn)">assumption</span>':'')+(x.status?' · '+esc(x.status):'')+'</div>';
  if(x.note)h+='<p>'+esc(x.note)+'</p>';if(x.detail)h+='<p>'+esc(x.detail)+'</p>';
  if(x.fields&&x.fields.length)h+='<ul>'+x.fields.map(function(f){return '<li><code>'+esc(f.name)+'</code> '+esc(f.type||'')+(f.key?' <b>'+esc([].concat(f.key).join('/').toUpperCase())+'</b>':'')+(f.references?' → '+esc(f.references):'')+(f.note?' — '+esc(f.note):'')+'</li>'}).join('')+'</ul>';
  if(x.facts&&x.facts.length)h+='<table class="facts">'+x.facts.map(function(f){return '<tr><th>'+esc(f[0])+'</th><td>'+esc(f[1])+'</td></tr>'}).join('')+'</table>';
  h+='<div class="acts"><button data-act="out">'+esc(WD.reach_out)+'</button><button data-act="in">'+esc(WD.reach_in)+'</button><button data-act="near">Neighbours</button></div>';
  h+='<p class="muted" style="font-size:12px">Shift-click another part to see the path between them.</p>';
  var o=outE.get(id).map(function(i){var e=edges.get(i);return '<li><a class="jump" data-n="'+esc(e.to)+'">'+esc(nodes.get(e.to).label)+'</a>'+(e.label?' — '+esc(e.label):'')+'</li>'}).join('');
  var n=inE.get(id).map(function(i){var e=edges.get(i);return '<li><a class="jump" data-n="'+esc(e.from)+'">'+esc(nodes.get(e.from).label)+'</a>'+(e.label?' — '+esc(e.label):'')+'</li>'}).join('');
  if(o)h+='<b>'+esc(WD.out)+'</b><ul>'+o+'</ul>';if(n)h+='<b>'+esc(WD.in)+'</b><ul>'+n+'</ul>';
  h+='<b>Evidence</b>'+evHtml(x.evidence);
  var nb=new Set([id]);outE.get(id).concat(inE.get(id)).forEach(function(i){nb.add(edges.get(i).from);nb.add(edges.get(i).to)});light(Array.from(nb),outE.get(id).concat(inE.get(id)));el('n',id).classList.add('sel');
 }else{h+='<h3>'+esc(nodes.get(x.from).label)+' → '+esc(nodes.get(x.to).label)+'</h3><div class="kind">'+(x.label?esc(x.label):'connection')+(x.assumed?' · <span style="color:var(--warn)">assumption</span>':'')+(x.status?' · '+esc(x.status):'')+'</div>';
  if(x.detail)h+='<p>'+esc(x.detail)+'</p>';h+='<b>Evidence</b>'+evHtml(x.evidence);light([x.from,x.to],[id],true)}
 panel.innerHTML=h;panel.classList.add('open');selected=kind==='n'?id:null;
 panel.querySelector('.close').onclick=function(){panel.classList.remove('open');clear();selected=null};
 panel.querySelectorAll('.jump').forEach(function(a){a.onclick=function(){show('n',a.getAttribute('data-n'))}});
 panel.querySelectorAll('[data-act]').forEach(function(b){b.onclick=function(){var a=b.getAttribute('data-act');
  if(a==='near'){show('n',id);return}var r=reach(id,a==='out'?1:-1);light(r.n,r.e,true);el('n',id).classList.add('sel')}})}
svg.addEventListener('click',function(e){var g=e.target.closest('.node');if(g){var id=g.getAttribute('data-id');
  if(e.shiftKey&&selected&&selected!==id){var p=path(selected,id,true)||path(selected,id,false);if(p){light(p.n,p.e,true)}return}show('n',id);return}
 var ed=e.target.closest('.edge');if(ed){show('e',ed.getAttribute('data-id'));return}});
svg.addEventListener('keydown',function(e){var g=e.target.closest&&e.target.closest('.node');if(g&&(e.key==='Enter'||e.key===' ')){e.preventDefault();show('n',g.getAttribute('data-id'))}});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){panel.classList.remove('open');clear();selected=null}
 if(e.target.tagName==='INPUT')return;if(e.key==='ArrowRight'&&tour)step(1);if(e.key==='ArrowLeft'&&tour)step(-1)});
var q=document.getElementById('find');q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();if(!v){clear();return}
 var ns=DATA.nodes.filter(function(n){return (n.label+' '+(n.note||'')+' '+(n.fields||[]).map(function(f){return f.name}).join(' ')).toLowerCase().indexOf(v)>=0}).map(function(n){return n.id});light(ns,[])});
document.getElementById('zin').onclick=function(){zoom(1/1.25)};document.getElementById('zout').onclick=function(){zoom(1.25)};document.getElementById('zfit').onclick=fit;
document.getElementById('theme').onclick=function(){var t=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',t);try{localStorage.setItem('idg-theme',t)}catch(e){}};
function download(name,type,data){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type:type}));a.download=name;document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},500)}
function standalone(){var c=svg.cloneNode(true);c.setAttribute('viewBox','0 0 '+W+' '+H);c.setAttribute('width',W);c.setAttribute('height',H);c.classList.remove('focus');
 c.querySelectorAll('.on,.sel,.flow').forEach(function(x){x.classList.remove('on','sel','flow')});
 var cs=getComputedStyle(root),vars=['--bg','--panel','--ink','--muted','--line','--edge','--accent','--warn','--ok','--bad','--hl','--canvas','--group','--group2'].map(function(v){return v+':'+cs.getPropertyValue(v)}).join(';');
 var st=document.createElementNS('http://www.w3.org/2000/svg','style');st.textContent='svg{'+vars+';font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}'+document.getElementById('diagram-css').textContent.split('/* diagram */')[1];
 c.insertBefore(st,c.firstChild);return new XMLSerializer().serializeToString(c)}
var base=(DATA.slug||'diagram');window.interactiveDiagram={svg:standalone,mermaid:function(){return DATA.mermaid}};
document.getElementById('xsvg').onclick=function(){download(base+'.svg','image/svg+xml',standalone())};
document.getElementById('xpng').onclick=function(){var img=new Image();img.onload=function(){var k=2,cv=document.createElement('canvas');cv.width=W*k;cv.height=H*k;var ctx=cv.getContext('2d');ctx.scale(k,k);ctx.drawImage(img,0,0);cv.toBlob(function(b){download(base+'.png','image/png',b)})};
 img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(standalone())};
document.getElementById('xmmd').onclick=function(){var t=DATA.mermaid;if(navigator.clipboard)navigator.clipboard.writeText(t).catch(function(){});download(base+'.mmd','text/plain',t)};
var tour=null,cap=document.getElementById('caption');
var steps=DATA.story&&DATA.story.length?DATA.story:(DATA.auto_steps&&DATA.auto_steps.length)?DATA.auto_steps:(DATA.type==='sequence'?DATA.edges.map(function(m,i){return {text:(i+1)+'. '+nodes.get(m.from).label+' → '+nodes.get(m.to).label+(m.label?': '+m.label:''),edges:[m.id],nodes:[m.from,m.to]}}):[]);
var tb=document.getElementById('tour');if(!steps.length){tb.style.display='none'}
function step(d){tour.i=Math.max(0,Math.min(steps.length-1,tour.i+d));var s=steps[tour.i];
 light((s.nodes||[]).concat((s.edges||[]).map(function(i){return edges.get(i)?edges.get(i).from:null}).filter(Boolean)).concat((s.edges||[]).map(function(i){return edges.get(i)?edges.get(i).to:null}).filter(Boolean)),s.edges||[],true);
 cap.innerHTML='<b>Step '+(tour.i+1)+' of '+steps.length+'</b> — '+esc(s.text||'')+' <span class="muted">(← → to move, Esc to stop)</span>';cap.classList.add('on')}
tb.onclick=function(){if(tour){tour=null;cap.classList.remove('on');clear();tb.textContent='Walk through';return}tour={i:-1};tb.textContent='Stop';step(1)};
document.getElementById('prev').onclick=function(){if(tour)step(-1)};document.getElementById('next').onclick=function(){if(!tour){tb.onclick()}else step(1)};
if(!steps.length){document.getElementById('prev').style.display='none';document.getElementById('next').style.display='none'}
function size(){var wr=document.querySelector('.wrap');var avail=Math.max(window.innerHeight-150,360);var r=stage.getBoundingClientRect();
 var s=Math.max(W/Math.max(r.width,1),0.6);wr.style.height=Math.min(avail,Math.max(H/s+24,300))+'px'}
size();fit();window.addEventListener('resize',function(){size();fit()});
function hash(){var h=decodeURIComponent(location.hash.slice(1));if(!h)return;var kv=new Map();h.split('&').forEach(function(p){var i=p.indexOf('=');if(i>0)kv.set(p.slice(0,i),p.slice(i+1))});
 if(kv.get('theme'))root.setAttribute('data-theme',kv.get('theme'));
 if(kv.get('n')&&nodes.get(kv.get('n')))show('n',kv.get('n'));if(kv.get('e')&&edges.get(kv.get('e')))show('e',kv.get('e'));
 if(kv.get('path')){var ab=kv.get('path').split(',');var p=path(ab[0],ab[1],true)||path(ab[0],ab[1],false);if(p)light(p.n,p.e,true)}
 if(kv.get('reach')){var ar=kv.get('reach').split(',');var r=reach(ar[0],ar[1]==='up'?-1:1);light(r.n,r.e,true)}
 if(kv.get('step')&&steps.length){tour={i:-1};tb.textContent='Stop';step(+kv.get('step'))}}
hash();window.addEventListener('hashchange',hash);
})();
"""


def auto_steps(spec):
    """A walkthrough when the spec has none: a timeline in time order, a waterfall along its
    critical path."""
    t = spec["type"]
    if spec["story"]:
        return []
    if t == "timeline":
        return [{"text": "%s \u2014 %s" % (n["when"], n["label"]), "nodes": [n["id"]]}
                for n in sorted(spec["nodes"], key=lambda n: n["_t"][0])]
    if t == "waterfall":
        by_id = {n["id"]: n for n in spec["nodes"]}
        return [{"text": "%s: %s, %s of the whole, %s of its own" % (by_id[i]["label"], by_id[i]["facts"][1][1], by_id[i]["facts"][2][1],
                                                                 by_id[i]["facts"][3][1]), "nodes": [i]}
                for i in spec["_waterfall"]["crit"]]
    return []


def type_facts(spec):
    """Facts a part's detail panel lists, beyond its note and evidence."""
    t = spec["type"]
    if t == "timeline":
        groups = {g["id"]: g["label"] for g in spec["groups"]}
        for n in spec["nodes"]:
            ln = n.get("lane") or n.get("group")
            n["facts"] = [["when", n["when"]]] + ([["source", groups.get(ln, ln)]] if ln else [])
    if t == "tree":
        kids = {}
        for n in spec["nodes"]:
            kids.setdefault(n.get("parent"), []).append(n["id"])

        def count(u):
            return sum(1 + count(v) for v in kids.get(u, []))
        for n in spec["nodes"]:
            c = count(n["id"])
            if c:
                n["facts"] = [["inside it", "%d item%s" % (c, "" if c == 1 else "s")]]


def build_html(spec, svg, mermaid, issues, theme):
    t = spec["type"]
    by_group = {g["id"]: g["label"] for g in spec["groups"]}
    data = {"type": t, "slug": re.sub(r"[^a-z0-9]+", "-", spec["title"].lower()).strip("-")[:60] or "diagram",
            "source_url": spec.get("source_url") if re.match(r"^https?://[^\s\"'<>]+$", str(spec.get("source_url") or "")) else None,
            "story": spec["story"], "nodes": [], "edges": [], "mermaid": mermaid,
            "words": WORDS.get(t, WORDS["default"]), "auto_steps": auto_steps(spec)}
    for n in spec["nodes"]:
        d = {k: n.get(k) for k in ("id", "label", "kind", "note", "detail", "fields", "evidence", "assumed", "status", "facts")}
        d["group_label"] = by_group.get(n.get("group"))
        data["nodes"].append(d)
    for e in spec["edges"]:
        data["edges"].append({k: e.get(k) for k in ("id", "from", "to", "label", "detail", "evidence", "assumed", "status")})
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    assumed_n = sum(1 for x in spec["nodes"] + spec["edges"] if x["assumed"] and not x.get("tree"))
    file_ev = [e for x in spec["nodes"] + spec["edges"] for e in x["evidence"] if "file" in e]
    checked = sum(1 for e in file_ev if e.get("verified"))
    facts = []
    if file_ev:
        facts.append("%d of %d file citations checked against the repository" % (checked, len(file_ev)) if checked
                     else "%d file citations, not checked against a repository" % len(file_ev))
    if assumed_n:
        facts.append("%d item%s drawn dashed as assumptions" % (assumed_n, "" if assumed_n == 1 else "s"))
    if spec.get("compared"):
        cnt = {}
        for x in spec["nodes"] + spec["edges"]:
            if x.get("status"):
                cnt[x["status"]] = cnt.get(x["status"], 0) + 1
        facts.append(", ".join("%d %s" % (v, k) for k, v in sorted(cnt.items())) or "no changes")
    legend = {
        "tree": ['<span><i></i>contains</span>'],
        "timeline": ['<span>\u25cf event</span>', '<span>\u25c6 milestone</span>', '<span>\u25ac lasted from \u2026 to</span>',
                     '<span>// a quiet stretch, shortened</span>'],
        "waterfall": ['<span>\u25ac a span, to scale</span>', '<span style="color:var(--hl)">\u25ad what the whole waited on (the critical path)</span>',
                      '<span style="color:var(--bad)">\u25ad failed</span>'] + (
            ['<span>total %s</span>' % esc(spec["_waterfall"]["total"])] if spec.get("_waterfall") else []),
        "class": ['<span>\u25b7 inherits (solid) or implements (dashed)</span>', '<span>\u25c6 composition</span>',
                  '<span>\u25c7 aggregation</span>', '<span>\u2192 association</span>', '<span>\u21e2 dependency</span>'],
    }.get(spec["type"], ['<span><i></i>connection</span>', '<span><i class="d"></i>async / optional</span>'])
    if assumed_n:
        legend.append('<span><i class="a"></i>assumption (not shown by the evidence)</span>')
    if spec.get("compared"):
        legend.append('<span style="color:var(--ok)">■ added</span><span style="color:var(--bad)">■ removed</span>'
                      '<span style="color:var(--accent)">■ changed</span>')
    notes = "".join("<li>%s</li>" % esc(x) for x in spec["notes"])
    warn_html = ""  # warnings are for whoever builds the page; they are printed, not published
    up_front = ""
    if spec.get("_findings"):
        up_front += '<div class="findings"><b>What it shows</b><ul>' + "".join("<li>%s</li>" % esc(f) for f in spec["_findings"]) + "</ul></div>"
    if spec["answers"]:
        def ev_short(a):
            if a.get("assumed") and not a["evidence"]:
                return '<span class="tag warn">assumption</span>'
            return ", ".join("<code>%s</code>%s" % (esc(ev_text(e)), " \u2713" if e.get("verified") else "") for e in a["evidence"])
        up_front += ('<table class="answers"><thead><tr><th>Question</th><th>What the material says</th><th>From</th></tr></thead><tbody>' +
                     "".join("<tr><td>%s</td><td>%s</td><td class=\"ev\">%s</td></tr>" % (esc(a["question"]), esc(a["answer"]), ev_short(a))
                             for a in spec["answers"]) + "</tbody></table>")
    return """<!doctype html>
<html lang="en" data-theme-default="%(theme)s"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src '%(js_hash)s'; style-src 'unsafe-inline'; img-src data: blob:; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- One self-contained file: no external scripts, styles, fonts or requests. The policy above makes the browser refuse any. -->
<title>%(title)s</title><meta name="generator" content="interactive-diagram (skilldrop)"></head>
<body>
<header class="top"><h1>%(title)s</h1>%(question)s%(summary)s%(up_front)s<p class="muted" style="font-size:12px;margin:6px 0 0">%(facts)s</p></header>
<section class="text" id="outline" aria-label="The diagram as text">
<details%(open)s><summary>The diagram as text</summary>%(outline)s%(notes)s</details></section>
<nav class="bar" aria-label="Diagram controls">
<input id="find" type="search" placeholder="Find a part…" aria-label="Find a part">
<button id="zin" title="Zoom in">+</button><button id="zout" title="Zoom out">−</button><button id="zfit" title="Fit to screen">Fit</button>
<span class="sep"></span><button id="tour">Walk through</button><button id="prev" title="Previous step">←</button><button id="next" title="Next step">→</button>
<span class="sep"></span><button id="xsvg">SVG</button><button id="xpng">PNG</button><button id="xmmd" title="Copy and download Mermaid">Mermaid</button>
<button id="theme" title="Light or dark">◐</button>
<span class="hint">Click a part for detail and evidence · shift-click a second part for the path · drag to pan · scroll to zoom</span></nav>
<div class="legend">%(legend)s</div>%(warn)s
<div class="caption" id="caption" aria-live="polite"></div>
<div class="wrap"><div id="stage">%(svg)s</div><aside id="panel" aria-live="polite"></aside></div>
<style id="diagram-css">%(css)s</style>
<script type="application/json" id="diagram-data">%(data)s</script>
<script>%(js)s</script>
</body></html>
""" % {"theme": esc(theme), "title": esc(spec["title"]),
       "question": '<p class="q">%s</p>' % esc(spec["question"]) if spec["question"] else "",
       "summary": '<p class="sum">%s</p>' % esc(spec["summary"]) if spec["summary"] else "",
       "facts": esc(" · ".join(facts)), "open": "" if len(spec["nodes"]) > 12 else " open",
       "outline": outline_html(spec), "notes": "<h2>Notes</h2><ul>%s</ul>" % notes if notes else "",
       "legend": "".join(legend), "warn": warn_html, "up_front": up_front, "svg": svg, "css": CSS,
       "data": payload, "js": JS,
       "js_hash": "sha256-" + base64.b64encode(hashlib.sha256(JS.encode("utf-8")).digest()).decode()}


# --------------------------------------------------------------------------- main

def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="diagram spec (JSON)")
    ap.add_argument("-o", "--out", help="HTML file to write")
    ap.add_argument("--repo-root", help="check every file:line citation against this directory and show the cited lines")
    ap.add_argument("--compare", metavar="BASE", help="a base spec: mark what this one added, removed or changed")
    ap.add_argument("--mermaid", metavar="FILE", help="also write the diagram as Mermaid")
    ap.add_argument("--theme", choices=("auto", "light", "dark"), default="auto")
    ap.add_argument("--check", action="store_true", help="validate (and verify evidence); write nothing")
    ap.add_argument("--json", action="store_true", help="print the receipt as JSON")
    a = ap.parse_args(argv)
    if not a.check and not a.out:
        ap.error("give -o OUT.html, or --check to validate only")
    issues = Issues()
    try:
        spec = normalise(load(a.spec), issues)
    except (OSError, ValueError) as err:
        print("cannot read %s: %s" % (a.spec, err), file=sys.stderr)
        return 2
    if a.compare:
        try:
            base_issues = Issues()
            base = normalise(load(a.compare), base_issues)
            merge_compare(spec, base, issues)
        except (OSError, ValueError) as err:
            print("cannot read %s: %s" % (a.compare, err), file=sys.stderr)
            return 2
    verify_evidence(spec, a.repo_root, issues)
    file_ev = [e for x in spec["nodes"] + spec["edges"] for e in x["evidence"] if "file" in e]
    if file_ev and not a.repo_root:
        issues.warn("evidence/unchecked", "evidence", "%d file citations were not checked" % len(file_ev),
                    "Pass --repo-root so each file and line is verified.")
    receipt = {"ok": not issues.errors, "type": spec["type"], "nodes": len(spec["nodes"]), "edges": len(spec["edges"]),
               "assumed": sum(1 for x in spec["nodes"] + spec["edges"] if x["assumed"]),
               "file_citations": len(file_ev), "verified": sum(1 for e in file_ev if e.get("verified")),
               "errors": issues.errors, "warnings": issues.warnings}
    if not issues.errors and not a.check:
        t = spec["type"]
        if t == "sequence":
            geo = layout_sequence(spec)
        elif t == "tree":
            geo = layout_tree(spec)
        elif t == "timeline":
            geo = layout_timeline(spec)
        elif t == "waterfall":
            geo = layout_waterfall(spec)
        else:
            flipped = [e for e in spec["edges"] if e.get("rel") in ("inherits", "implements")]
            for e in flipped:  # the parent goes first, so it sits above its children
                e["from"], e["to"] = e["to"], e["from"]
            geo = layout_graph_full(spec)
            for e in flipped:
                e["from"], e["to"] = e["to"], e["from"]
                e["pts"] = list(reversed(e.get("pts", [])))
            occupied = [(n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]) for n in spec["nodes"]]
            labels = {g["id"]: g["label"] for g in spec["groups"]}
            occupied += [(g["x"] + 6, g["y"] + 4, g["x"] + 18 + text_w(labels.get(g["id"], ""), 12), g["y"] + 24) for g in geo["groups"]]
            place_labels(spec, occupied)
        if t == "tree":
            for e in spec["edges"]:
                e.pop("label_box", None)
        type_facts(spec)
        svg = render_svg(spec, geo)
        mermaid = to_mermaid(spec)
        out = build_html(spec, svg, mermaid, issues, a.theme)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        receipt["output"] = os.path.abspath(a.out)
        receipt["bytes"] = len(out.encode("utf-8"))
        receipt["edges"] = len([e for e in spec["edges"] if not e.get("tree")]) or len(spec["edges"])
        shown_path = os.path.relpath(os.path.abspath(a.out)) if not os.path.relpath(os.path.abspath(a.out)).startswith("..") else os.path.abspath(a.out)
        receipt["reply_first_line"] = "[%s](%s)" % (spec["title"].replace("]", ")"), shown_path)
        receipt["findings"] = spec.get("_findings", [])
        if a.mermaid:
            with open(a.mermaid, "w", encoding="utf-8") as fh:
                fh.write(mermaid)
            receipt["mermaid"] = os.path.abspath(a.mermaid)
    if a.json:
        print(json.dumps(receipt, indent=1))
    else:
        for i in issues.items:
            print("%s %s [%s] %s%s" % ("ERROR" if i["level"] == "error" else "warning", i["where"], i["code"], i["message"],
                                       (" — " + i["fix"]) if i["fix"] else ""))
        if issues.errors:
            print("%d error(s); nothing written. Fix the spec and run again." % len(issues.errors))
        elif a.check:
            print("OK: %d %s, %d %s, %d assumed, %d of %d file citations verified" % (
                receipt["nodes"], "participants" if spec["type"] == "sequence" else "nodes", receipt["edges"],
                "messages" if spec["type"] == "sequence" else "edges", receipt["assumed"], receipt["verified"], receipt["file_citations"]))
        else:
            item, link = {"sequence": ("participants", "messages"), "tree": ("items", "links"), "timeline": ("events", "links"),
                          "waterfall": ("spans", "parent links"), "class": ("types", "relations")}.get(spec["type"], ("nodes", "edges"))
            print("Your reply starts with this line, before anything else:\n" + receipt["reply_first_line"] + "\n")
            print("For the end of the reply: %d of %d file citations checked; %d drawn as assumptions. (%s, %d KB: %d %s, %d %s.)" % (
                receipt["verified"], receipt["file_citations"], receipt["assumed"], a.out, receipt["bytes"] // 1024,
                receipt["nodes"], item, receipt["edges"], link))
            if receipt["findings"]:
                print("Computed from the spec, and shown at the top of the page (use these numbers as they are; don't re-add durations):\n"
                      + "\n".join("- " + f for f in receipt["findings"]))
    return 1 if issues.errors else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Compare recorded outputs of an old and a new system, case by case (golden master).

Each side is either
  - a directory: one file per case, the case id is the file name without its
    extension; *.json files are parsed as JSON, any other file is compared as
    text; or
  - a JSONL file: one JSON object per line, the case id is the value of --key
    (default "case_id").

A rules file normalises known noise before comparing. Each rule names one
field path, one rule and a reason:

    {"rules": [
      {"path": "body.quoted_at", "rule": "ignore", "reason": "wall-clock time"},
      {"path": "body.quote_id", "rule": "regex", "pattern": "^Q-[0-9a-f]{8}$",
       "replace": "Q-<id>", "reason": "random per call"},
      {"path": "body.lines", "rule": "sort", "by": "sku", "reason": "set order"},
      {"path": "body.fx_rate", "rule": "tolerance", "abs": "0.000001",
       "reason": "float printed by a different library"},
      {"path": "body.score", "rule": "round", "digits": 3, "reason": "..."}
    ]}

A plain object {"<path>": "ignore" | {"rule": ...}} is accepted too.

Paths: dotted keys; `[]` is every element of a list, `[2]` one element, `*` any
key at that level, `$` the whole record (for text files). There is no
any-depth wildcard on purpose: every rule names where it applies.

Rules:
  ignore     the value becomes "<ignored>"; a field present on one side only
             still counts as a difference
  regex      re.sub(pattern, replace) on string values (replace defaults to "<norm>")
  sort       sorts the list, by the element key "by" or by the whole element
  tolerance  numbers within "abs" and/or "rel" compare equal (applied while comparing)
  round      rounds numbers to "digits" places, "mode" half_even (default) or half_up
Order: ignore, regex and round in file order, then sort, then compare.

--accepted FILE lists intended changes, each with an approver:
    {"accepted": [{"path": "body.message", "reason": "...", "approver": "...",
                   "cases": ["c07"]}]}
A difference at that path (in those cases, or every case when "cases" is
absent) is reported as accepted instead of failing the comparison.

Usage:
    python3 golden_diff.py OLD NEW [--rules rules.json] [--accepted accepted.json]
                           [--key case_id] [--max-diffs 20] [--json] [-o report]

Exit codes: 0 equivalent after rules (accepted changes allowed),
            1 not equivalent (a difference, or a case missing on one side),
            2 bad input.
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

RULES = ("ignore", "regex", "sort", "tolerance", "round")
MONEY_WORDS = ("price", "amount", "total", "cost", "fee", "tax", "vat", "minor",
               "cents", "pence", "balance", "charge", "subtotal", "money")
IGNORED = "<ignored>"
ABSENT = object()


class BadInput(Exception):
    pass


# ---------------------------------------------------------------- paths

TOKEN = re.compile(r"\[(\d*)\]|([^.\[\]]+)")


def parse_path(text):
    text = text.strip()
    if text in ("$", ""):
        return []
    if text.startswith("$."):
        text = text[2:]
    out, pos = [], 0
    while pos < len(text):
        if text[pos] == ".":
            pos += 1
            continue
        m = TOKEN.match(text, pos)
        if not m:
            raise BadInput("cannot read path: " + text)
        if m.group(0).startswith("["):
            out.append(("idx", int(m.group(1))) if m.group(1) else ("any_idx", None))
        elif m.group(2) == "*":
            out.append(("any_key", None))
        else:
            out.append(("key", m.group(2)))
        pos = m.end()
    return out


def matches(pattern, concrete):
    if len(pattern) != len(concrete):
        return False
    for (kind, val), step in zip(pattern, concrete):
        if kind == "key" and not (isinstance(step, str) and step == val):
            return False
        if kind == "any_key" and not isinstance(step, str):
            return False
        if kind == "idx" and not (isinstance(step, int) and step == val):
            return False
        if kind == "any_idx" and not isinstance(step, int):
            return False
    return True


def show(concrete):
    out = ""
    for step in concrete:
        out += "[{}]".format(step) if isinstance(step, int) else ("." if out else "") + step
    return out or "$"


def generalise(concrete):
    return show([0 if isinstance(s, int) else s for s in concrete]).replace("[0]", "[]")


# ---------------------------------------------------------------- loading

def num(value, what):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BadInput("{} must be a number, got {!r}".format(what, value))


def load_rules(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BadInput("cannot read rules file {}: {}".format(path, exc))
    if isinstance(raw, dict) and "rules" in raw:
        items = raw["rules"]
    elif isinstance(raw, dict):
        items = []
        for i, (p, spec) in enumerate(raw.items(), 1):
            if not isinstance(spec, (str, dict)):
                raise BadInput("rule {} ({}): spec must be a rule name or an object, got {!r}".format(i, p, spec))
            spec = {"rule": spec} if isinstance(spec, str) else dict(spec)
            spec["path"] = p
            items.append(spec)
    else:
        items = raw
    if not isinstance(items, list):
        raise BadInput("rules file must hold a list of rules")
    rules = []
    for i, r in enumerate(items, 1):
        if not isinstance(r, dict) or "path" not in r or "rule" not in r:
            raise BadInput("rule {} needs a path and a rule".format(i))
        if r["rule"] not in RULES:
            raise BadInput("rule {}: unknown rule {!r} (use one of {})".format(i, r["rule"], ", ".join(RULES)))
        rule = {"n": i, "path": r["path"], "pat": parse_path(r["path"]), "rule": r["rule"],
                "reason": str(r.get("reason", "")).strip(), "hits": 0, "subtree": False}
        if r["rule"] == "regex":
            try:
                rule["re"] = re.compile(r["pattern"])
            except (KeyError, re.error) as exc:
                raise BadInput("rule {}: bad or missing pattern: {}".format(i, exc))
            rule["replace"] = r.get("replace", "<norm>")
        elif r["rule"] == "tolerance":
            if "abs" not in r and "rel" not in r:
                raise BadInput("rule {}: tolerance needs abs or rel".format(i))
            rule["abs"] = num(r.get("abs", 0), "rule {} abs".format(i))
            rule["rel"] = num(r.get("rel", 0), "rule {} rel".format(i))
        elif r["rule"] == "round":
            if not isinstance(r.get("digits"), int):
                raise BadInput("rule {}: round needs integer digits".format(i))
            rule["digits"] = r["digits"]
            mode = r.get("mode", "half_even")
            if mode not in ("half_even", "half_up"):
                raise BadInput("rule {}: mode must be half_even or half_up".format(i))
            rule["mode"] = ROUND_HALF_EVEN if mode == "half_even" else ROUND_HALF_UP
        elif r["rule"] == "sort":
            rule["by"] = r.get("by")
        rules.append(rule)
    return rules


def load_accepted(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BadInput("cannot read accepted-changes file {}: {}".format(path, exc))
    items = raw.get("accepted") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise BadInput("accepted-changes file must hold a list under \"accepted\"")
    out = []
    for i, a in enumerate(items, 1):
        if not isinstance(a, dict) or not a.get("path"):
            raise BadInput("accepted change {} needs a path".format(i))
        if not str(a.get("approver", "")).strip():
            raise BadInput("accepted change {} ({}) has no approver".format(i, a["path"]))
        cases = a.get("cases")
        out.append({"path": a["path"], "pat": parse_path(a["path"]), "approver": a["approver"],
                    "reason": a.get("reason", ""), "cases": set(cases) if cases else None, "hits": 0})
    return out


def parse_json(text, where):
    try:
        return json.loads(text, parse_float=Decimal)
    except ValueError as exc:
        raise BadInput("{}: not valid JSON: {}".format(where, exc))


def load_side(path, key):
    p = Path(path)
    cases = OrderedDict()
    if p.is_dir():
        for f in sorted(p.iterdir()):
            if f.name.startswith(".") or not f.is_file():
                continue
            if f.stem in cases:
                raise BadInput("{}: two files for case {}".format(path, f.stem))
            text = f.read_text(encoding="utf-8")
            cases[f.stem] = parse_json(text, str(f)) if f.suffix == ".json" else text
    elif p.is_file():
        with p.open(encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                rec = parse_json(line, "{} line {}".format(path, n))
                if not isinstance(rec, dict) or key not in rec:
                    raise BadInput("{} line {}: no {!r} field".format(path, n, key))
                cid = str(rec[key])
                if cid in cases:
                    raise BadInput("{} line {}: duplicate case id {}".format(path, n, cid))
                cases[cid] = rec
    else:
        raise BadInput("not found: " + str(path))
    if not cases:
        raise BadInput("no cases in " + str(path))
    return cases


# ---------------------------------------------------------------- normalising

def canon(value):
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


def is_num(v):
    return isinstance(v, (int, Decimal)) and not isinstance(v, bool)


def apply_rule(rule, value):
    kind = rule["rule"]
    if kind == "ignore":
        if isinstance(value, (dict, list)):
            rule["subtree"] = True
        rule["hits"] += 1
        return IGNORED
    if kind == "regex" and isinstance(value, str):
        rule["hits"] += 1
        return rule["re"].sub(rule["replace"], value)
    if kind == "round" and is_num(value):
        rule["hits"] += 1
        q = Decimal(1).scaleb(-rule["digits"])
        return Decimal(value).quantize(q, rounding=rule["mode"])
    if kind == "sort" and isinstance(value, list):
        rule["hits"] += 1
        by = rule.get("by")
        if by:
            return sorted(value, key=lambda e: canon(e.get(by) if isinstance(e, dict) else e))
        return sorted(value, key=canon)
    return value


def normalise(value, rules, here=()):
    if isinstance(value, dict):
        value = OrderedDict((k, normalise(v, rules, here + (k,))) for k, v in value.items())
    elif isinstance(value, list):
        value = [normalise(v, rules, here + (i,)) for i, v in enumerate(value)]
    for rule in rules:
        if matches(rule["pat"], list(here)):
            value = apply_rule(rule, value)
    return value


# ---------------------------------------------------------------- comparing

def within(a, b, rule):
    a, b = Decimal(a), Decimal(b)
    gap = abs(a - b)
    return gap <= rule["abs"] or gap <= rule["rel"] * max(abs(a), abs(b))


def compare(old, new, tolerances, here, diffs):
    tol = next((t for t in tolerances if matches(t["pat"], list(here))), None)
    if is_num(old) and is_num(new):
        if Decimal(old) == Decimal(new):
            return
        if tol and within(old, new, tol):
            tol["hits"] += 1
            return
        diffs.append((here, "changed", old, new))
        return
    if isinstance(old, dict) and isinstance(new, dict):
        for k in old:
            if k not in new:
                diffs.append((here + (k,), "missing in new", old[k], ABSENT))
            else:
                compare(old[k], new[k], tolerances, here + (k,), diffs)
        for k in new:
            if k not in old:
                diffs.append((here + (k,), "added in new", ABSENT, new[k]))
        return
    if isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            diffs.append((here, "list length {} -> {}".format(len(old), len(new)), len(old), len(new)))
        for i in range(min(len(old), len(new))):
            compare(old[i], new[i], tolerances, here + (i,), diffs)
        return
    if type(old) is not type(new) and not (is_num(old) and is_num(new)):
        diffs.append((here, "type {} -> {}".format(tname(old), tname(new)), old, new))
        return
    if isinstance(old, str) and ("\n" in old or "\n" in new):
        a, b = old.split("\n"), new.split("\n")
        for n in range(max(len(a), len(b))):
            la = a[n] if n < len(a) else ABSENT
            lb = b[n] if n < len(b) else ABSENT
            if la != lb:
                diffs.append((here, "line {} changed".format(n + 1), la, lb))
        return
    if old != new:
        diffs.append((here, "changed", old, new))


def tname(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if is_num(v):
        return "number"
    return {str: "string", dict: "object", list: "list"}.get(type(v), type(v).__name__)


def plain(v):
    if v is ABSENT:
        return "(absent)"
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() and "." not in str(v) else float(v)
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [plain(x) for x in v]
    return v


def short(v, width=80):
    if v is ABSENT:
        return "(absent)"
    text = v.replace("\n", "\\n") if isinstance(v, str) else json.dumps(plain(v), ensure_ascii=False, default=str)
    return text if len(text) <= width else text[: width - 3] + "..."


def run(args):
    rules = load_rules(args.rules) if args.rules else []
    accepted = load_accepted(args.accepted) if args.accepted else []
    old = load_side(args.old, args.key)
    new = load_side(args.new, args.key)
    transforms = [r for r in rules if r["rule"] in ("ignore", "regex", "round")]
    sorts = [r for r in rules if r["rule"] == "sort"]
    tolerances = [r for r in rules if r["rule"] == "tolerance"]

    matched, mismatched, accepted_only = [], [], []
    all_diffs, accepted_diffs = [], []
    for cid in old:
        if cid not in new:
            continue
        a = normalise(normalise(old[cid], transforms), sorts)
        b = normalise(normalise(new[cid], transforms), sorts)
        diffs = []
        compare(a, b, tolerances, (), diffs)
        open_diffs = []
        for d in diffs:
            hit = next((x for x in accepted if matches(x["pat"], list(d[0]))
                        and (x["cases"] is None or cid in x["cases"])), None)
            if hit:
                hit["hits"] += 1
                accepted_diffs.append((cid,) + d + (hit,))
            else:
                open_diffs.append(d)
        if open_diffs:
            mismatched.append(cid)
            all_diffs.extend((cid,) + d for d in open_diffs)
        elif diffs:
            accepted_only.append(cid)
        else:
            matched.append(cid)

    missing = [c for c in old if c not in new]
    extra = [c for c in new if c not in old]
    fields = OrderedDict()
    for cid, path, kind, _, _ in all_diffs:
        f = fields.setdefault(generalise(path), {"diffs": 0, "cases": [], "kinds": []})
        f["diffs"] += 1
        if cid not in f["cases"]:
            f["cases"].append(cid)
        if kind not in f["kinds"]:
            f["kinds"].append(kind)

    if mismatched or missing or extra:
        verdict = "NOT EQUIVALENT"
    elif accepted_only:
        verdict = "EQUIVALENT EXCEPT ACCEPTED CHANGES"
    else:
        verdict = "EQUIVALENT"

    warnings = []
    for r in rules:
        label = "rule {} ({} {})".format(r["n"], r["rule"], r["path"])
        if not r["reason"]:
            warnings.append(label + " has no reason")
        if r["hits"] == 0 and r["rule"] != "tolerance":
            warnings.append(label + " matched nothing: check the path")
        if r["subtree"]:
            warnings.append(label + " ignores a whole object or list: name the leaf fields instead")
        last = next((v for k, v in reversed(r["pat"]) if k == "key"), "")
        if r["rule"] in ("tolerance", "round") and any(w in last.lower() for w in MONEY_WORDS):
            warnings.append(label + " loosens a money-like field: compare money exactly in minor units")
        if r["rule"] == "tolerance" and r["hits"]:
            warnings.append("{} absorbed {} difference(s)".format(label, r["hits"]))
    for a in accepted:
        if a["hits"] == 0:
            warnings.append("accepted change at {} matched no difference".format(a["path"]))

    return {
        "verdict": verdict,
        "cases": {"old": len(old), "new": len(new), "compared": len(old) - len(missing),
                  "matched": len(matched), "mismatched": len(mismatched),
                  "accepted_only": len(accepted_only),
                  "missing_in_new": missing, "extra_in_new": extra},
        "mismatched_cases": mismatched,
        "fields": [{"path": p, "diffs": f["diffs"], "cases": len(f["cases"]),
                    "case_ids": f["cases"], "kinds": f["kinds"]} for p, f in fields.items()],
        "diffs": [{"case": c, "path": show(p), "kind": k, "old": plain(o), "new": plain(n)}
                  for c, p, k, o, n in all_diffs[: args.max_diffs]],
        "diffs_total": len(all_diffs),
        "accepted": [{"case": c, "path": show(p), "old": plain(o), "new": plain(n),
                      "approver": h["approver"]} for c, p, _, o, n, h in accepted_diffs],
        "rules": [{"n": r["n"], "path": r["path"], "rule": r["rule"], "reason": r["reason"],
                   "hits": r["hits"]} for r in rules],
        "warnings": warnings,
    }


def render(rep, max_diffs):
    c = rep["cases"]
    head = "Verdict after rules: " + rep["verdict"]
    if rep["warnings"]:
        head += "  ({} warning{} at the end: read them before trusting this)".format(
            len(rep["warnings"]), "" if len(rep["warnings"]) == 1 else "s")
    out = [head, ""]
    out.append("Cases: {} old, {} new, {} compared: {} matched, {} mismatched, {} accepted-only".format(
        c["old"], c["new"], c["compared"], c["matched"], c["mismatched"], c["accepted_only"]))
    if c["missing_in_new"]:
        out.append("Missing in new: " + ", ".join(c["missing_in_new"]))
    if c["extra_in_new"]:
        out.append("Only in new: " + ", ".join(c["extra_in_new"]))
    if rep["fields"]:
        out += ["", "Differences by field:", "  {:<40} {:>6} {:>6}  {}".format("path", "diffs", "cases", "case ids")]
        for f in rep["fields"]:
            ids = ", ".join(f["case_ids"][:8]) + (" ..." if len(f["case_ids"]) > 8 else "")
            out.append("  {:<40} {:>6} {:>6}  {}".format(f["path"], f["diffs"], f["cases"], ids))
    if rep["diffs"]:
        out += ["", "First {} of {} differences:".format(len(rep["diffs"]), rep["diffs_total"])]
        for d in rep["diffs"]:
            out.append("  {}  {}  [{}]  old={}  new={}".format(
                d["case"], d["path"], d["kind"], short(d["old"]), short(d["new"])))
    if rep["accepted"]:
        out += ["", "Accepted changes ({}):".format(len(rep["accepted"]))]
        for a in rep["accepted"][:max_diffs]:
            out.append("  {}  {}  old={}  new={}  approved by {}".format(
                a["case"], a["path"], short(a["old"]), short(a["new"]), a["approver"]))
    if rep["rules"]:
        out += ["", "Rules applied:"]
        for r in rep["rules"]:
            out.append("  {}. {} {}  ({} hit{})  {}".format(
                r["n"], r["rule"], r["path"], r["hits"], "" if r["hits"] == 1 else "s",
                r["reason"] or "NO REASON GIVEN"))
    if rep["warnings"]:
        out += ["", "Warnings:"] + ["  - " + w for w in rep["warnings"]]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Golden-master diff of old vs new recorded outputs.")
    ap.add_argument("old", help="directory or JSONL file of the old system's outputs")
    ap.add_argument("new", help="directory or JSONL file of the new system's outputs")
    ap.add_argument("--rules", help="normalisation rules (JSON)")
    ap.add_argument("--accepted", help="approved intended changes (JSON)")
    ap.add_argument("--key", default="case_id", help="case id field in JSONL records (default case_id)")
    ap.add_argument("--max-diffs", type=int, default=20, help="differences to list (default 20)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("-o", "--output", help="write the report to this path instead of stdout")
    args = ap.parse_args(argv)
    try:
        rep = run(args)
    except BadInput as exc:
        sys.stderr.write("error: {}\n".format(exc))
        return 2
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("error: {}\n".format(exc))
        return 2
    text = json.dumps(rep, indent=2, ensure_ascii=False, default=str) + "\n" if args.json else render(rep, args.max_diffs)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if rep["verdict"] != "NOT EQUIVALENT" else 1


if __name__ == "__main__":
    sys.exit(main())

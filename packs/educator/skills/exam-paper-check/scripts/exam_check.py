#!/usr/bin/env python3
"""Check an exam paper and its mark scheme for the faults students and moderators find. Stdlib only.

Reads the paper (Markdown, plain text or .docx) and, optionally, its mark scheme and a spec
(duration, objectives and their target weightings, which question parts assess which objective).
Reports, each with the question it is in:
  - part marks that don't add up to a question's stated total, and questions that don't add up
    to the paper's stated total (an "answer either 5 or 6" choice counts once)
  - question numbers that skip or repeat, and parts that skip ((a), (c)) or repeat
  - a part with no marks shown
  - a part the mark scheme doesn't cover, a scheme entry for a part that isn't in the paper,
    and a scheme whose marks differ from the paper's
  - the time per mark, and an objective that is never assessed or is far off its weighting
It checks the paper's arithmetic and structure, not whether its questions are good.

Usage:
  python3 exam_check.py paper.md [--scheme scheme.md] [--spec spec.json] [--json]
Exit codes: 0 no failures, 1 a failure, 2 a file can't be read.
"""
import argparse
import json
import re
import sys
import zipfile
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]

QUESTION = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?\s*(?:question|q)\s*\.?\s*(\d{1,3})\b[.):]?(?:\*\*)?\s*(.*)$", re.I)
BARE_Q = re.compile(r"^\s*(?:\*\*(\d{1,3})[.)]?\*\*|(\d{1,3})[.)])\s+(.*)$")
PLAIN_Q = re.compile(r"^\s*(\d{1,3})\s+([A-Za-z].*)$")
COMBINED = re.compile(r"^\s*(?:\*\*)?(\d{1,3})\s*\(?([a-z])\)?(?:\s*\(?((?:x|ix|iv|v?i{0,3}))\))?(?:\*\*)?[\s.:)]+(.*)$", re.I)
PART = re.compile(r"^\s*(?:\*\*)?\(?([a-z])\)(?:\*\*)?\s*(.*)$")
SUBPART = re.compile(r"^\s*(?:\*\*)?\(((?:x|ix|iv|v?i{1,3}|v))\)(?:\*\*)?\s*(.*)$", re.I)
MARK = re.compile(r"[\[(]\s*(\d{1,3})\s*(?:marks?|m)?\s*[\])]\s*\**\s*$", re.I)
Q_TOTAL = re.compile(r"(?:total\s+for\s+question\s+(\d{1,3})\s*(?:is|=|:)?\s*(\d{1,3})\s*marks?"
                     r"|question\s+(\d{1,3})\s+total\s*(?:is|=|:)?\s*(\d{1,3})"
                     r"|\[\s*total\s*(?:for\s+question\s+(\d{1,3}))?\s*[:=]?\s*(\d{1,3})\s*(?:marks?)?\s*\])", re.I)
PAPER_TOTAL = re.compile(r"(?:total\s+(?:for\s+(?:this\s+)?paper|marks?\s+(?:for\s+(?:this\s+)?paper|available)|marks?)"
                         r"\s*(?:is|=|:)?\s*(\d{1,4})|(?:this\s+paper\s+is\s+worth|maximum\s+mark\s*(?:is|:)?)\s*(\d{1,4})"
                         r"|(\d{1,4})\s+marks?\s+in\s+total|total\s+of\s+(\d{1,4})\s+marks?)", re.I)
DURATION = re.compile(r"(?:time(?:\s+allowed)?|duration)\s*[:=]?\s*(?:(\d{1,2})\s*h(?:ours?|rs?)?\s*)?(?:(\d{1,3})\s*min(?:utes?|s)?)?", re.I)
EITHER = re.compile(r"answer\s+either\s+question\s+(\d{1,3})\s+or\s+(?:question\s+)?(\d{1,3})", re.I)


def read_text(path):
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        return ["".join(t.text or "" for t in p.iter(W + "t")) for p in root.iter(W + "p")]
    with open(path, encoding="utf-8-sig") as f:
        return f.read().splitlines()


def parse(lines):
    """Questions with their parts and marks, in document order, plus the stated totals."""
    qs = []
    q = part = None
    stated, stated_line, duration, choices = None, None, None, []

    def new_question(n, line):
        nonlocal q, part
        q = {"n": n, "line": line, "parts": [], "stated": None, "marks": None}
        qs.append(q)
        part = None

    def new_part(label, line):
        nonlocal part
        part = {"label": label, "line": line, "marks": None}
        q["parts"].append(part)

    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        totals = list(Q_TOTAL.finditer(line))
        if totals:
            for m in totals:
                qn = m.group(1) or m.group(3) or m.group(5)
                val = int(m.group(2) or m.group(4) or m.group(6))
                target = next((x for x in reversed(qs) if str(x["n"]) == qn), None) if qn else q
                if target is not None:
                    target["stated"] = val
            continue
        pm = PAPER_TOTAL.search(line)
        if pm and stated is None and not re.search(r"question\s+\d", line, re.I):
            stated, stated_line = int(next(g for g in pm.groups() if g)), i
            continue
        dm = DURATION.search(line)
        if dm and duration is None and (dm.group(1) or dm.group(2)):
            duration = int(dm.group(1) or 0) * 60 + int(dm.group(2) or 0)
        choices += [(int(e.group(1)), int(e.group(2))) for e in EITHER.finditer(line)]

        rest, labelled = line, False
        m, c, b = QUESTION.match(line), COMBINED.match(line), BARE_Q.match(line)
        if not b:
            pl = PLAIN_Q.match(line)    # "4 Level-marked…" in a scheme: only as the next question number
            if pl and (q is None and pl.group(1) == "1" or q is not None and int(pl.group(1)) == q["n"] + 1):
                b = re.match(r"^\s*()(\d{1,3})\s+(.*)$", line)
        sub, pt = SUBPART.match(line), PART.match(line)
        if m:
            new_question(int(m.group(1)), i)
            rest, labelled = m.group(2), True
        elif c and c.group(2).lower() <= "j":
            n = int(c.group(1))
            if q is None or q["n"] != n:
                new_question(n, i)
            new_part(c.group(2).lower() + (f"({c.group(3).lower()})" if c.group(3) else ""), i)
            rest, labelled = c.group(4), True
        elif b and (q is None or b.group(1) or int(b.group(2)) == q["n"] + 1):   # a bold number is always a question
            new_question(int(b.group(1) or b.group(2)), i)
            rest, labelled = b.group(3), True
        elif q is not None and sub and part is not None and not (
                sub.group(1).lower() == "i" and part["label"] == "h"):   # (i) after (h) is the next part
            new_part(f"{part['label'].split('(')[0]}({sub.group(1).lower()})", i)
            rest, labelled = sub.group(2), True
        elif q is not None and pt:
            new_part(pt.group(1).lower(), i)
            rest, labelled = pt.group(2), True
            inner = SUBPART.match(rest)        # "(a) (i) Describe…" opens the part and its first subpart
            if inner:
                new_part(f"{part['label']}({inner.group(1).lower()})", i)
                rest = inner.group(2)
        mk = MARK.search(rest)
        if mk and q is not None:
            if part is not None:
                if part["marks"] is None:
                    part["marks"] = int(mk.group(1))
            elif q["marks"] is None:
                q["marks"] = int(mk.group(1))
    return {"questions": qs, "stated_total": stated, "stated_line": stated_line,
            "duration": duration, "choices": choices}


def q_marks(q):
    leaves = leaf_parts(q)
    if leaves:
        return sum(p["marks"] or 0 for p in leaves)
    return q["marks"] or 0


def leaf_parts(q):
    """Parts that carry marks themselves: (a)(i) and (a)(ii), not (a) when it has subparts."""
    labels = [p["label"] for p in q["parts"]]
    return [p for p in q["parts"] if not any(o.startswith(p["label"] + "(") for o in labels)]


def check(paper, scheme=None, spec=None):
    fails, warns = [], []
    qs = paper["questions"]
    if not qs:
        return {"fails": ["no numbered questions found"], "warns": [], "rows": [], "total": 0, "stated_total": None,
                "duration": None, "pace": None, "coverage": {}}
    seen = {}
    for q in qs:
        if q["n"] in seen:
            fails.append(f"Question {q['n']} is numbered twice (lines {seen[q['n']]} and {q['line']})")
        seen.setdefault(q["n"], q["line"])
    nums = sorted(seen)
    for a, b in zip(nums, nums[1:]):
        if b != a + 1:
            warns.append(f"question numbers jump from {a} to {b}")
    if nums[0] != 1:
        warns.append(f"the first question is numbered {nums[0]}")
    rows = []
    for q in qs:
        letters, last_roman = [], {}
        for p in q["parts"]:
            base, _, sub = p["label"].partition("(")
            if sub:
                r = sub.rstrip(")")
                prev = last_roman.get(base)
                want = ROMAN[ROMAN.index(prev) + 1] if prev in ROMAN and ROMAN.index(prev) + 1 < len(ROMAN) else "i"
                if r != want:
                    warns.append(f"Question {q['n']}({base}): part ({r}) follows ({prev or '—'}); expected ({want})")
                last_roman[base] = r
            else:
                if base in letters:
                    fails.append(f"Question {q['n']}: part ({base}) appears twice")
                elif letters and ord(base) != ord(letters[-1]) + 1:
                    warns.append(f"Question {q['n']}: part ({base}) follows ({letters[-1]}); "
                                 f"({chr(ord(letters[-1]) + 1)}) is missing")
                elif not letters and base != "a":
                    warns.append(f"Question {q['n']}: the first part is ({base})")
                letters.append(base)
        for p in leaf_parts(q):
            if p["marks"] is None:
                warns.append(f"Question {q['n']}({p['label']}) shows no marks")
        if not q["parts"] and q["marks"] is None and q["stated"] is None:
            warns.append(f"Question {q['n']} shows no marks")
        total = q_marks(q) if (q["parts"] or q["marks"] is not None) else (q["stated"] or 0)
        if q["stated"] is not None and (q["parts"] or q["marks"] is not None) and total != q["stated"]:
            fails.append(f"Question {q['n']}: the parts add up to {total} but the question total says {q['stated']}")
        rows.append({"question": q["n"], "marks": total, "stated": q["stated"],
                     "parts": {p["label"]: p["marks"] for p in leaf_parts(q)}})
    by_n = {r["question"]: r["marks"] for r in rows}
    total = sum(by_n.values())
    for a, b in paper["choices"]:
        if a in by_n and b in by_n:
            total -= min(by_n[a], by_n[b])
            if by_n[a] != by_n[b]:
                fails.append(f"Questions {a} and {b} are a choice but are worth {by_n[a]} and {by_n[b]} marks")
    stated = paper["stated_total"] if paper["stated_total"] is not None else (spec or {}).get("total")
    if stated is not None and total != stated:
        fails.append(f"the questions add up to {total} marks but the paper says {stated}")
    duration = paper["duration"] or (spec or {}).get("duration_minutes")
    pace = duration / total if duration and total else None
    if scheme is not None:
        smap = {}
        for q in scheme["questions"]:
            leaves = leaf_parts(q)
            if leaves:
                for p in leaves:
                    smap[f"{q['n']}{p['label']}"] = p["marks"]
            else:
                smap[str(q["n"])] = q["marks"]
        pmap = {}
        for q in qs:
            leaves = leaf_parts(q)
            if leaves:
                for p in leaves:
                    pmap[f"{q['n']}{p['label']}"] = p["marks"]
            else:
                pmap[str(q["n"])] = q["marks"] if q["marks"] is not None else q["stated"]
        for k, v in pmap.items():
            if k not in smap:
                fails.append(f"the mark scheme has nothing for {pretty(k)}")
            elif smap[k] is not None and v is not None and smap[k] != v:
                fails.append(f"{pretty(k)} is worth {v} on the paper but {smap[k]} in the mark scheme")
        for k in smap:
            if k not in pmap:
                fails.append(f"the mark scheme covers {pretty(k)}, which isn't on the paper")
        if scheme.get("stated_total") is not None:
            s_by_q = {}
            for k, v in smap.items():
                n = int(re.match(r"\d+", k).group(0))
                s_by_q[n] = s_by_q.get(n, 0) + (v or 0)
            s_total = sum(s_by_q.values())
            for a, b in paper["choices"]:
                if a in s_by_q and b in s_by_q:
                    s_total -= min(s_by_q[a], s_by_q[b])
            if s_total != scheme["stated_total"]:
                fails.append(f"the mark scheme says it is out of {scheme['stated_total']} but its own marks add up to {s_total}")
    coverage = {}
    if spec and spec.get("assesses"):
        targets = spec.get("objectives", {})
        pmarks = {}
        for q in qs:
            leaves = leaf_parts(q)
            for p in leaves or [{"label": "", "marks": q_marks(q)}]:
                pmarks[f"{q['n']}{p['label']}"] = p["marks"] or 0
        dropped = {str(b) for _, b in paper["choices"]}   # a choice counts once
        for key, objs in spec["assesses"].items():
            k = key.replace(" ", "").lower()
            if re.match(r"\d+", k).group(0) in dropped:
                continue
            share = pmarks.get(k)
            if share is None:
                matches = {pk: v for pk, v in pmarks.items() if pk.startswith(k)}
                share = sum(matches.values()) if matches else None
            if share is None:
                warns.append(f"the spec maps {key} to objectives but there is no {key} on the paper")
                continue
            objs = [objs] if isinstance(objs, str) else objs
            for o in objs:
                coverage[o] = coverage.get(o, 0) + share / len(objs)
        for o, target in targets.items():
            got = coverage.get(o, 0)
            if got == 0:
                fails.append(f"objective {o} is never assessed")
            elif target and total and abs(got / total * 100 - target) > max(5, target * 0.25):
                warns.append(f"objective {o} has {got / total * 100:.0f} % of the marks against a target of {target:g} %")
    return {"fails": fails, "warns": warns, "rows": rows, "total": total, "stated_total": stated,
            "duration": duration, "pace": pace, "coverage": coverage}


def pretty(key):
    m = re.match(r"(\d+)([a-z]?)(\(.*\))?", key)
    n, a, r = m.groups()
    return f"Question {n}" + (f"({a})" if a else "") + (r or "")


def report(r):
    L = ["# Exam paper check", "", "| Question | Marks | Stated total | Parts |", "|---|---:|---:|---|"]
    for row in r["rows"]:
        parts = ", ".join(f"({k.replace('(', ')(').rstrip(')')}) {v if v is not None else '?'}" for k, v in row["parts"].items())
        L.append(f"| {row['question']} | {row['marks']} | {row['stated'] if row['stated'] is not None else ''} | {parts} |")
    L.append(f"| **Paper** | **{r['total']}** | {r['stated_total'] if r['stated_total'] is not None else ''} | |")
    if r["pace"]:
        L += ["", f"Time: {r['duration']} minutes for {r['total']} marks, {r['pace']:.2f} minutes a mark."]
    if r["coverage"]:
        L += ["", "| Objective | Marks | Share |", "|---|---:|---:|"]
        for o, v in sorted(r["coverage"].items()):
            L.append(f"| {o} | {v:g} | {v / r['total'] * 100:.0f} % |")
    L.append("")
    if not r["fails"]:
        L.append("PASS every total adds up, numbering runs in order, and the scheme matches the paper.")
    L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an exam paper and its mark scheme.")
    ap.add_argument("paper")
    ap.add_argument("--scheme", help="the mark scheme (.md, .txt or .docx)")
    ap.add_argument("--spec", help="spec.json: duration_minutes, total, objectives {name: target %%}, assesses {part: [objectives]}")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        paper = parse(read_text(args.paper))
        scheme = parse(read_text(args.scheme)) if args.scheme else None
        spec = None
        if args.spec:
            with open(args.spec, encoding="utf-8-sig") as f:
                spec = json.load(f)
            if not isinstance(spec, dict):
                raise ValueError("spec.json must be an object")
    except (OSError, ValueError, UnicodeDecodeError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as e:
        print(f"FAIL cannot read input: {e}")
        return 2
    r = check(paper, scheme, spec)
    print(json.dumps(r, indent=2) if args.json else report(r), end="" if not args.json else "\n")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

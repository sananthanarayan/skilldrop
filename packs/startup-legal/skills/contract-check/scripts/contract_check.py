#!/usr/bin/env python3
"""Check an agreement for the mechanical faults that slip past a read-through. Stdlib only.

Reads a contract as Markdown, plain text or Word (.docx) and reports, each with where it is:
  - blanks left in: [●], [•], [___], ____, [DATE], [insert …], TBD
  - cross-references to a clause, section, schedule, exhibit, annex or appendix that doesn't exist
  - clause numbering that skips or repeats
  - a defined term defined twice, defined and never used, or used in lower case once defined
  - a role or object used as if defined (Customer, Services, Confidential Information …) but never defined
  - an amount or period in words that disagrees with its figure: "thirty (60) days", "ten thousand ($1,000)"
  - a date that doesn't exist (31 June, 29 February in a non-leap year)
and lists every notice period, so deadlines can be worked out.

It checks the document's consistency, not whether its terms are fair or lawful.

Usage:
  python3 contract_check.py agreement.docx [--json]
Exit codes: 0 no failures, 1 a failure, 2 the file can't be read.
"""
import argparse
import json
import re
import sys
import zipfile
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_text(path):
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        lines = []
        for p in root.iter(W + "p"):
            text = "".join(t.text or "" for t in p.iter(W + "t"))
            lines.append(text)
        return lines
    with open(path, encoding="utf-8-sig") as f:
        return f.read().splitlines()


# ---------- numbering and cross-references ----------

MULTI = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?\s*(?:(?:clause|section|article)\s+)?(\d+(?:\.\d+){1,3})\.?(?=\s|\*\*|$)", re.I)
SINGLE = re.compile(r"^\s*(#+\s*)?(\*\*)?\s*((?:clause|section|article)\s+)?(\d{1,3})\.?(?=\s|\*\*|$)(.*)$", re.I)
APPENDIX_HEAD = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?\s*(schedule|exhibit|annex|appendix|annexure)\s+([A-Z0-9]{1,3})\b", re.I)
REF = re.compile(r"\b(clauses?|sections?|articles?)\s+(\d+(?:\.\d+){0,3})((?:\s*(?:,|and|or|to|-|–)\s*\d+(?:\.\d+){0,3})*)", re.I)
APPENDIX_REF = re.compile(r"\b(schedule|exhibit|annex|appendix|annexure)\s+([A-Z0-9]{1,3})\b", re.I)


def clause_number(line):
    """The clause number a line starts, or None. "7.2 …" anywhere counts; a bare "7." counts only
    as a heading (Markdown #, bold, "Clause 7", or a short title line), so a numbered list inside
    a clause isn't read as clauses."""
    m = MULTI.match(line)
    if m:
        return m.group(1)
    m = SINGLE.match(line)
    if not m:
        return None
    hashes, bold, word, n, rest = m.groups()
    rest = rest.strip().strip("*").strip()
    if hashes or bold or word:
        return n
    if rest and len(rest) <= 60 and not rest.endswith((".", ";", ",")) and rest[:1].isupper():
        return n
    return None


def appendix_at(line):
    a = APPENDIX_HEAD.match(line)
    if a and len(line.strip()) < 120:
        return (a.group(1).lower().replace("annexure", "annex"), a.group(2).upper())
    return None


def scan(lines):
    """Clause numbers in the main body, appendices present, and each numbered line with its scope."""
    nums, apps, numbered = {}, {}, []
    scope = "body"
    for i, line in enumerate(lines, 1):
        key = appendix_at(line)
        if key:
            apps.setdefault(key, i)
            scope = key
            continue
        n = clause_number(line)
        if n:
            numbered.append((scope, n, i))
            if scope == "body":
                nums.setdefault(n, i)
    return nums, apps, numbered


def numbering_faults(numbered):
    out = []
    seen = {}
    last = {}
    for scope, n, i in numbered:
        if (scope, n) in seen:
            out.append(("FAIL", i, f"clause {n} is numbered twice (also line {seen[(scope, n)]})"))
            continue
        seen[(scope, n)] = i
        parts = [int(x) for x in n.split(".")]
        parent = (scope,) + tuple(parts[:-1])
        prev = last.get(parent)
        if prev is not None and parts[-1] > prev + 1:
            want = ".".join(map(str, parts[:-1] + [prev + 1]))
            out.append(("WARN", i, f"clause numbering jumps to {n}; {want} is missing"))
        last[parent] = parts[-1]
        for k in [k for k in last if len(k) > len(parent) and k[:len(parent)] == parent and k[len(parent)] != parts[-1]]:
            del last[k]
    return out


def ref_faults(lines, nums, apps):
    out = []
    tops = {n.split(".")[0] for n in nums}
    if not nums:
        return [("WARN", 0, "no numbered clauses found, so cross-references were not checked")]
    for i, line in enumerate(lines, 1):
        body = MULTI.sub("", line, count=1) if MULTI.match(line) else line
        for m in REF.finditer(body):
            targets = [m.group(2)] + re.findall(r"\d+(?:\.\d+){0,3}", m.group(3) or "")
            for t in targets:
                if t in nums or (("." not in t) and t in tops):
                    continue
                out.append(("FAIL", i, f"refers to {m.group(1).rstrip('s').lower()} {t}, which doesn't exist"))
        for m in APPENDIX_REF.finditer(line):
            key = (m.group(1).lower().replace("annexure", "annex"), m.group(2).upper())
            if appendix_at(line) and m.start() < 12:
                continue
            if key not in apps and not re.match(r"^(this|the|each|any|a)$", m.group(2), re.I):
                out.append(("FAIL", i, f"refers to {key[0].title()} {key[1]}, which isn't in the document"))
    return dedupe(out)


# ---------- blanks ----------

BLANKS = [
    (re.compile(r"\[\s*[●•]+\s*\]|[●•]{1,}"), "a [●] placeholder"),
    (re.compile(r"\[\s*_+\s*\]|_{4,}"), "a blank line to fill in"),
    (re.compile(r"\[(?:insert|enter|add|date|name|address|amount|company|party|tbc|tbd|xx+)[^\]]{0,40}\]", re.I), "a bracketed placeholder"),
    (re.compile(r"\bTB[CD]\b"), "TBD/TBC"),
    (re.compile(r"\bX{2,}\b"), "an XX placeholder"),
]


def blank_faults(lines):
    out = []
    for i, line in enumerate(lines, 1):
        for rx, what in BLANKS:
            m = rx.search(line)
            if m:
                out.append(("FAIL", i, f"{what} is still in: “{snippet(line, m.start())}”"))
                break
    return out


# ---------- defined terms ----------

DEF_PATTERNS = [
    re.compile(r"\(\s*(?:the\s+|each\s+a\s+|together\s+the\s+|hereinafter\s+(?:the\s+)?)?[\"“]([A-Z][A-Za-z0-9&'\- ]{1,60}?)[\"”]\s*\)"),
    re.compile(r"[\"“]([A-Z][A-Za-z0-9&'\- ]{1,60}?)[\"”]\s+(?:means|shall mean|has the meaning|includes|refers to)\b"),
    re.compile(r"\*\*[\"“]?([A-Z][A-Za-z0-9&'\- ]{1,60}?)[\"”]?\*\*\s+(?:means|shall mean|has the meaning)\b"),
]

COMMON = ["Agreement", "Customer", "Client", "Company", "Supplier", "Vendor", "Provider", "Service Provider",
          "Licensee", "Licensor", "Contractor", "Consultant", "Services", "Deliverables", "Software", "Fees",
          "Effective Date", "Term", "Territory", "Confidential Information", "Intellectual Property",
          "Intellectual Property Rights", "Affiliate", "Personal Data", "Products", "Order Form",
          "Statement of Work", "Disclosing Party", "Receiving Party", "Purpose", "Business Day",
          "Commencement Date", "Investor", "Founder", "Employee", "Platform", "Subscription Term",
          "Documentation", "Customer Data", "Work Product", "Background IP", "Licensed Materials"]


def definitions(lines):
    defs = {}
    for i, line in enumerate(lines, 1):
        for rx in DEF_PATTERNS:
            for m in rx.finditer(line):
                term = m.group(1).strip()
                if len(term) < 2 or term.lower() in ("the", "a", "an"):
                    continue
                defs.setdefault(term, []).append(i)
    return defs


def term_faults(lines, defs):
    out = []
    text = "\n".join(lines)
    for term, where in defs.items():
        places = sorted(set(where))
        if len(places) > 1:
            out.append(("FAIL", places[1], f"“{term}” is defined more than once (lines {', '.join(map(str, places))})"))
        uses = len(re.findall(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", text))
        if uses <= len(where):
            out.append(("WARN", places[0], f"“{term}” is defined but never used"))
        lower = [n for n, l in enumerate(lines, 1) if n not in places and
                 re.search(r"(?<![A-Za-z])" + re.escape(term.lower()) + r"(?![A-Za-z])", l) and len(term.split()) > 1]
        if lower:
            out.append(("WARN", lower[0], f"“{term.lower()}” appears in lower case although “{term}” is a "
                                           f"defined term (lines {', '.join(map(str, lower[:5]))})"))
    defined_lower = {t.lower() for t in defs}
    for term in COMMON:
        if term.lower() in defined_lower:
            continue
        rx = re.compile(r"(?<=[a-z,;] )(?:the )?" + re.escape(term) + r"(?![A-Za-z])")
        hits = [(n, len(rx.findall(l))) for n, l in enumerate(lines, 1) if rx.search(l)]
        count = sum(c for _, c in hits)
        if count >= 2:
            out.append(("WARN", hits[0][0], f"“{term}” is used as a defined term (capitalised, {count} times) but "
                                            "never defined"))
    return out


# ---------- amounts in words and figures ----------

UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                     "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
SCALES = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lakhs": 100000, "million": 10 ** 6,
          "crore": 10 ** 7, "crores": 10 ** 7, "billion": 10 ** 9}
WORD = r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|" \
       r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|lakhs?|" \
       r"million|crores?|billion|and|point)"
WORDS_FIG = re.compile(r"\b((?:" + WORD + r")(?:[\s-]+" + WORD + r")*)\b(?:\s+[A-Za-z]+){0,3}?\s*\(\s*([$€£₹]?\s?[\d,]+(?:\.\d+)?)\s*\)", re.I)


def words_to_number(words):
    total, current = 0, 0
    toks = [t for t in re.split(r"[\s-]+", words.lower()) if t and t != "and"]
    if not toks or "point" in toks:
        return None
    for t in toks:
        if t in UNITS:
            current += UNITS[t]
        elif t in TENS:
            current += TENS[t]
        elif t == "hundred":
            current = (current or 1) * 100
        elif t in SCALES:
            total += (current or 1) * SCALES[t]
            current = 0
        else:
            return None
    return total + current


def amount_faults(lines):
    out = []
    for i, line in enumerate(lines, 1):
        for m in WORDS_FIG.finditer(line):
            words = m.group(1)
            if words.strip().lower() in ("and", "point", "one"):
                if words.strip().lower() != "one":
                    continue
            val = words_to_number(words)
            fig = float(re.sub(r"[^\d.]", "", m.group(2)) or "nan")
            if val is None or fig != fig:
                continue
            if abs(val - fig) > 1e-9:
                out.append(("FAIL", i, f"“{m.group(0).strip()}”: the words say {val:,} and the figure says {fig:,.0f}"))
    return out


# ---------- dates and notice periods ----------

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
DATE1 = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(" + "|".join(MONTHS) + r"),?\s+(\d{4})\b", re.I)
DATE2 = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I)
NOTICE = re.compile(r"\(?(\d{1,3})\)?\s+(business\s+days?|calendar\s+days?|days?|weeks?|months?)[’']?\s*"
                    r"(?:(?:prior\s+)?(?:written\s+)?notice|(?:prior\s+to|before)\s+(?:the\s+)?(?:end|expiry|expiration|renewal))",
                    re.I)


def date_faults(lines):
    import calendar
    out = []
    for i, line in enumerate(lines, 1):
        for m in list(DATE1.finditer(line)) + list(DATE2.finditer(line)):
            if m.re is DATE1:
                d, mon, y = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
            else:
                mon, d, y = MONTHS[m.group(1).lower()], int(m.group(2)), int(m.group(3))
            if not 1 <= d <= calendar.monthrange(y, mon)[1]:
                out.append(("FAIL", i, f"“{m.group(0)}” is not a real date"))
    return out


def notices(lines, term_end=None):
    found = []
    for i, line in enumerate(lines, 1):
        for m in NOTICE.finditer(line):
            n = {"line": i, "period": f"{m.group(1)} {m.group(2).lower()}", "text": snippet(line, m.start(), 90)}
            before_end = re.search(r"before|prior to|renew|expir|end of", line[m.start():], re.I)
            if term_end and before_end:
                n["notice_by"] = notice_by(term_end, int(m.group(1)), m.group(2).lower()).isoformat()
            found.append(n)
    return found


def notice_by(end, n, unit):
    """The last day notice can be given so that n units still remain before `end`."""
    import calendar
    import datetime as dt
    if unit.startswith("business"):
        d, left = end, n
        while left:
            d -= dt.timedelta(days=1)
            if d.weekday() < 5:
                left -= 1
        return d
    if unit.startswith("week"):
        return end - dt.timedelta(weeks=n)
    if unit.startswith("month"):
        y, mth = divmod(end.year * 12 + end.month - 1 - n, 12)
        return end.replace(year=y, month=mth + 1, day=min(end.day, calendar.monthrange(y, mth + 1)[1]))
    return end - dt.timedelta(days=n)


# ---------- output ----------

def snippet(line, at, width=60):
    start = max(0, at - 20)
    s = line[start:start + width].strip()
    return ("…" if start else "") + s + ("…" if start + width < len(line) else "")


def dedupe(items):
    seen, out = set(), []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def check(lines, term_end=None):
    nums, apps, numbered = scan(lines)
    defs = definitions(lines)
    findings = (blank_faults(lines) + ref_faults(lines, nums, apps) + numbering_faults(numbered) +
                term_faults(lines, defs) + amount_faults(lines) + date_faults(lines))
    findings = dedupe(findings)
    findings.sort(key=lambda f: (f[0] != "FAIL", f[1]))
    return {"findings": findings, "clauses": len(nums), "appendices": sorted(f"{k[0].title()} {k[1]}" for k in apps),
            "defined_terms": sorted(defs), "notices": notices(lines, term_end)}


def clause_at(lines, n):
    """The nearest numbered clause at or above line n, for a reader who has the document open."""
    for i in range(min(n, len(lines)), 0, -1):
        if appendix_at(lines[i - 1]):
            return None
        c = clause_number(lines[i - 1])
        if c:
            return c
    return None


def report(path, lines, r):
    L = [f"# Contract check: {path}", "",
         f"{r['clauses']} numbered clauses, {len(r['defined_terms'])} defined terms, "
         f"{len(r['appendices'])} schedules or exhibits ({', '.join(r['appendices']) or 'none'}).", ""]
    if not any(f[0] == "FAIL" for f in r["findings"]):
        L.append("PASS no blanks, broken cross-references, repeated clause numbers, doubly defined terms, "
                 "mismatched amounts or impossible dates.")
    for level, line, msg in r["findings"]:
        where = f"line {line}" if line else "document"
        c = clause_at(lines, line) if line else None
        if c:
            where += f", clause {c}"
        L.append(f"{level} [{where}] {msg}")
    if r["notices"]:
        L += ["", "Notice periods:"]
        for n in r["notices"]:
            c = clause_at(lines, n["line"])
            by = f" — give notice by {n['notice_by']}" if n.get("notice_by") else ""
            L.append(f"- {n['period']} (line {n['line']}{', clause ' + c if c else ''}){by}: {n['text']}")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an agreement's mechanics.")
    ap.add_argument("document")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--term-end", help="YYYY-MM-DD the current term ends, to date each notice deadline")
    args = ap.parse_args(argv)
    term_end = None
    if args.term_end:
        import datetime as dt
        try:
            term_end = dt.date.fromisoformat(args.term_end)
        except ValueError:
            print("FAIL --term-end must be a date as YYYY-MM-DD")
            return 2
    try:
        lines = read_text(args.document)
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as e:
        print(f"FAIL cannot read {args.document}: {e}")
        return 2
    r = check(lines, term_end)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(report(args.document, lines, r), end="")
    return 1 if any(f[0] == "FAIL" for f in r["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())

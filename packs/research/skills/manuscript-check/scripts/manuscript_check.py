#!/usr/bin/env python3
"""Check a manuscript's citations and cross-references before it goes to a journal, a
supervisor or a publisher. Stdlib only.

Reads a paper, thesis chapter or report (Markdown, plain text or .docx) and reports, each with
its line:
  - numbered citations ([3], [2-5], [1, 4]): a number with no reference, a reference never
    cited, references not numbered in order of first citation, a number used twice in the list
  - author-year citations ((Smith, 2020), Smith et al. (2019), (Lee & Park 2021a; Okafor 2018)):
    a citation with no matching reference, a near miss (the right author with another year, or
    the right year with a misspelt name), a reference never cited
  - the same work listed twice (same DOI, or same title)
  - Figure, Table and Section references with no such figure, table or section; a caption never
    referred to; figures or tables numbered out of order or with gaps
  - Markdown footnotes used but not defined, or defined but not used; malformed DOIs
  - the abstract's word count against a limit
It checks the manuscript's internal consistency, not whether the citations support the claims.

Usage:
  python3 manuscript_check.py paper.md [--abstract-limit 250] [--json]
Exit codes: 0 no failures, 1 a failure, 2 the file can't be read.
"""
import argparse
import json
import re
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REF_HEAD = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(?:\d+\.?\s*)?(references|bibliography|works\s+cited|literature\s+cited|reference\s+list|sources)\s*(?:\*\*)?\s*:?\s*$", re.I)
NUM_CITE = re.compile(r"\[(\d{1,3}(?:\s*[-–,]\s*\d{1,3})*)\]")
NUM_ENTRY = re.compile(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})\.)\s+(.+)")
SURNAME = r"(?:[A-Z][A-Za-z'’\-]+|(?:van|von|de|da|del|der|di|le|la)\s+[A-Z][A-Za-z'’\-]+)"
AUTH = SURNAME + r"(?:\s+(?:et\s+al\.?|and|&)\s*(?:" + SURNAME + r")?)?"
YEAR = r"(?:1[89]\d\d|20\d\d)[a-z]?|n\.d\.|in press|forthcoming"
PAREN = re.compile(r"\(([^()]*?(?:" + YEAR + r")[^()]*)\)")
NARRATIVE = re.compile(r"\b(" + AUTH + r")\s*\((" + YEAR + r")(?:[,;][^)]*)?\)")
IN_PAREN = re.compile(r"(?:see\s+|e\.g\.,?\s+|cf\.\s+)?(" + AUTH + r"),?\s+(" + YEAR + r")")
FIG_REF = re.compile(r"\b(Fig(?:ure|\.)?s?|Tables?|Sections?|§)\s*(\d{1,3}(?:\.\d{1,3})*)(?:\s*(?:and|&|–|-|to)\s*(\d{1,3}(?:\.\d{1,3})*))?", re.I)
CAPTION = re.compile(r"^\s*(?:!\[[^\]]*\]\([^)]*\)\s*)?(?:\*\*|_|\*)?\s*(Fig(?:ure|\.)?|Table)\s+(\d{1,3})\s*[.:|—–-]", re.I)
SECTION_HEAD = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+[A-Z]")
FOOT_USE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
FOOT_DEF = re.compile(r"^\s*\[\^([^\]\s]+)\]:")
DOI = re.compile(r"\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\S+)", re.I)
GOOD_DOI = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9<>\[\]]+$")
ABSTRACT = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*abstract\s*(?:\*\*)?\s*:?\s*(.*)$", re.I)


def read_lines(path):
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        return ["".join(t.text or "" for t in p.iter(W + "t")) for p in root.iter(W + "p")]
    with open(path, encoding="utf-8-sig") as f:
        return f.read().splitlines()


def fold(s):
    """Lower case without accents, so Müller matches Muller."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def expand(spec):
    out = []
    for part in re.split(r"\s*,\s*", spec):
        m = re.match(r"(\d+)\s*[-–]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out += list(range(a, b + 1)) if 0 < b - a < 200 else [a, b]
        elif part.strip().isdigit():
            out.append(int(part))
    return out


def split(lines):
    """(body lines with numbers, reference entries) — the list runs from its heading to the next heading."""
    start = next((i for i, l in enumerate(lines) if REF_HEAD.match(l)), None)
    if start is None:
        return list(enumerate(lines, 1)), []
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^\s*#{1,6}\s+\S", lines[i]) and not REF_HEAD.match(lines[i])
                and not re.match(r"^\s*#{1,6}\s+(appendix|supplement)", lines[i], re.I) or
                re.match(r"^\s*#{1,6}\s+(appendix|supplement)", lines[i], re.I)), len(lines))
    body = list(enumerate(lines[:start], 1)) + list(enumerate(lines[end:], end + 1))
    entries, cur = [], None
    for n, l in enumerate(lines[start + 1:end], start + 2):
        if not l.strip():
            cur = None
            continue
        m = NUM_ENTRY.match(l)
        bullet = re.match(r"^\s*[-*•]\s+(.+)", l)
        if m or bullet or cur is None:
            text = m.group(3) if m else bullet.group(1) if bullet else l.strip()
            cur = {"line": n, "num": int(m.group(1) or m.group(2)) if m else None, "text": text.strip()}
            entries.append(cur)
        else:
            cur["text"] += " " + l.strip()
    return body, entries


def entry_key(e):
    """(first author's surname, year with suffix) from an author-year reference entry."""
    t = re.sub(r"^[\s*_]+", "", e["text"])
    m = re.match(r"((?:van|von|de|da|del|der|di|le|la)\s+)?([A-Z][^\s,.(]*)", t)
    y = re.search(r"\((" + YEAR + r")\)|[,.]\s*(" + YEAR + r")[.,)]", t)
    sur = ((m.group(1) or "") + m.group(2)).strip() if m else None
    year = (y.group(1) or y.group(2)) if y else None
    return (fold(sur) if sur else None, year.lower() if year else None)


def surname_of(auth):
    a = re.split(r"\s+(?:et\s+al\.?|and|&)\s*", auth.strip())[0]
    return fold(a.strip())


def author_year_cites(body):
    cites = []
    for n, line in body:
        clean = re.sub(r"\[[^\]]*\]\([^)]*\)", "", line)
        for m in NARRATIVE.finditer(clean):
            cites.append((n, surname_of(m.group(1)), m.group(2).lower(), m.group(0)))
        for p in PAREN.finditer(clean):
            inner = p.group(1)
            for chunk in re.split(r";", inner):
                mm = IN_PAREN.search(chunk)
                if mm:
                    years = re.findall(YEAR, chunk[mm.start(2):])
                    for y in years or [mm.group(2)]:
                        cites.append((n, surname_of(mm.group(1)), y.lower(), chunk.strip()))
    seen, out = set(), []
    for c in cites:
        if (c[0], c[1], c[2]) not in seen:
            seen.add((c[0], c[1], c[2]))
            out.append(c)
    return out


def close(a, b):
    """Two surnames one edit apart (a typo), or one a prefix of the other."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def check(lines, abstract_limit=None):
    fails, warns = [], []
    body, entries = split(lines)
    numbered = [e for e in entries if e["num"] is not None]
    style = "numbered" if numbered and len(numbered) >= len(entries) / 2 else "author-year" if entries else None
    body_text = [(n, l) for n, l in body]
    stats = {"references": len(entries), "style": style}
    if style == "numbered":
        nums = {}
        for e in numbered:
            if e["num"] in nums:
                fails.append(f"reference [{e['num']}] is numbered twice in the list (lines {nums[e['num']]} and {e['line']})")
            nums.setdefault(e["num"], e["line"])
        order, cited = [], {}
        for n, l in body_text:
            for m in NUM_CITE.finditer(l):
                if re.search(r"\]\(", l[m.end():m.end() + 2]):
                    continue                   # a Markdown link, not a citation
                for k in expand(m.group(1)):
                    cited.setdefault(k, n)
                    if k not in order:
                        order.append(k)
        for k, n in sorted(cited.items(), key=lambda x: x[1]):
            if k not in nums:
                fails.append(f"line {n}: cites [{k}], but there is no reference [{k}]")
        for k, n in sorted(nums.items()):
            if k not in cited:
                warns.append(f"reference [{k}] (line {n}) is never cited")
        listed = sorted(nums)
        for a, b in zip(listed, listed[1:]):
            if b != a + 1:
                warns.append(f"the reference list jumps from [{a}] to [{b}]")
        in_list = [k for k in order if k in nums]
        if in_list and in_list != sorted(in_list):
            # the numbering a citation-order style expects: cited references by first citation,
            # then any never cited, in their current order
            new_order = in_list + [k for k in sorted(nums) if k not in in_list]
            stats["renumber"] = {old: new for new, old in enumerate(new_order, 1) if old != new}
            first = next(k for i, k in enumerate(in_list) if k != sorted(in_list)[i])
            warns.append(f"references aren't numbered in order of first citation (from [{first}], line {cited[first]}); "
                         "numbered styles such as Vancouver and IEEE expect that")
        stats["cited"] = len([k for k in cited if k in nums])
    elif style == "author-year":
        keys = [(entry_key(e), e) for e in entries]
        cites = author_year_cites(body_text)
        used = set()
        for n, sur, year, text in cites:
            exact = [e for (s, y), e in keys if s == sur and y == year]
            if exact:
                used.update(id(e) for e in exact)
                continue
            if year.rstrip("abcdefgh") == year and any(s == sur and y and y.rstrip("abcdefgh") == year for (s, y), _ in keys):
                warns.append(f"line {n}: “{text}” needs its year's letter: the list has more than one {sur.title()} {year}")
                used.update(id(e) for (s, y), e in keys if s == sur and y and y.startswith(year))
                continue
            same_author = [y for (s, y), _ in keys if s == sur and y]
            typo = [s for (s, y), _ in keys if s and y == year and close(s, sur)]
            if same_author:
                fails.append(f"line {n}: cites “{text}”, but the reference list has {sur.title()} {', '.join(sorted(set(same_author)))}")
                used.update(id(e) for (s, y), e in keys if s == sur)
            elif typo:
                fails.append(f"line {n}: cites “{text}”, but the reference list spells it {typo[0].title()} ({year})")
                used.update(id(e) for (s, y), e in keys if s == typo[0] and y == year)
            else:
                fails.append(f"line {n}: cites “{text}”, but there is no {sur.title()} {year} in the reference list")
        for (s, y), e in keys:
            if id(e) not in used and s:
                warns.append(f"reference on line {e['line']} ({s.title()} {y or 'no year'}) is never cited")
        stats["cited"] = len(used)
    elif any(NUM_CITE.search(l) for _, l in body_text):
        fails.append("the text cites references, but there is no reference list (a heading such as References or Bibliography)")
    # the same work twice
    seen_doi, seen_title, dup_pairs = {}, {}, set()
    for e in entries:
        for m in DOI.finditer(e["text"]):
            d = m.group(1).rstrip(".,;)").lower()
            if not GOOD_DOI.match(d):
                warns.append(f"reference on line {e['line']}: “{m.group(0)[:60]}” isn't a well-formed DOI")
            elif d in seen_doi:
                fails.append(f"references on lines {seen_doi[d]} and {e['line']} are the same work (DOI {d})")
                dup_pairs.add((seen_doi[d], e["line"]))
            seen_doi.setdefault(d, e["line"])
        t = re.search(r"(?:\)\.?|\d{4}[a-z]?\.)\s*[\"“]?([^.\"”]{20,})[\"”]?[.?]", e["text"])
        if not t and e["num"] is not None:
            # Vancouver and IEEE put the title after the authors: "Smith J, Lee K. Title of the work. Journal."
            t = re.search(r"^[^.]*?(?:et al|[A-Z]{1,3})\.\s+[\"“]?([^.\"”]{20,})[\"”]?[.?]", e["text"])
        if t:
            key = re.sub(r"[^a-z0-9]+", " ", fold(t.group(1))).strip()
            if key in seen_title and (seen_title[key], e["line"]) not in dup_pairs:
                fails.append(f"references on lines {seen_title[key]} and {e['line']} have the same title")
            seen_title.setdefault(key, e["line"])
    # figures, tables, sections
    captions = {"figure": {}, "table": {}}
    sections = set()
    for n, l in body_text:
        c = CAPTION.match(l)
        if c:
            kind = "table" if c.group(1).lower().startswith("tab") else "figure"
            k = int(c.group(2))
            if k in captions[kind]:
                fails.append(f"line {n}: {kind.title()} {k} has a second caption (also line {captions[kind][k]})")
            captions[kind].setdefault(k, n)
        h = SECTION_HEAD.match(l)
        if h:
            sections.add(h.group(1))
    refs = {"figure": {}, "table": {}}
    for n, l in body_text:
        if CAPTION.match(l):
            l = CAPTION.sub("", l, count=1)
        for m in FIG_REF.finditer(l):
            word = m.group(1).lower()
            kind = "table" if word.startswith("tab") else "section" if word.startswith(("sec", "§")) else "figure"
            nums = [m.group(2)] + ([m.group(3)] if m.group(3) else [])
            if kind != "section" and m.group(3) and re.search(r"–|-|to", m.group(0)):
                try:
                    nums = [str(x) for x in range(int(m.group(2)), int(m.group(3)) + 1)]
                except ValueError:
                    pass
            for k in nums:
                if kind == "section":
                    if sections and k not in sections and not any(s.startswith(k + ".") for s in sections):
                        fails.append(f"line {n}: refers to Section {k}, but there is no section {k}")
                    continue
                if "." in k:
                    continue
                refs[kind].setdefault(int(k), n)
                if captions[kind] and int(k) not in captions[kind]:
                    fails.append(f"line {n}: refers to {kind.title()} {k}, but there is no {kind.title()} {k}")
    for kind in ("figure", "table"):
        nums = sorted(captions[kind])
        for k in nums:
            if k not in refs[kind]:
                warns.append(f"{kind.title()} {k} (line {captions[kind][k]}) is never referred to in the text")
        for a, b in zip(nums, nums[1:]):
            if b != a + 1:
                warns.append(f"{kind}s jump from {a} to {b}")
        if nums and nums[0] != 1:
            warns.append(f"the first {kind} is numbered {nums[0]}")
        first_mention = [k for k, _ in sorted(refs[kind].items(), key=lambda x: x[1]) if k in captions[kind]]
        if first_mention != sorted(first_mention):
            warns.append(f"{kind}s are first mentioned out of order ({', '.join(map(str, first_mention))})")
        stats[kind + "s"] = len(nums)
    # footnotes
    uses, defs = {}, {}
    for n, l in enumerate(lines, 1):
        d = FOOT_DEF.match(l)
        if d:
            defs.setdefault(d.group(1), n)
        for u in FOOT_USE.finditer(l):
            uses.setdefault(u.group(1), n)
    for k, n in uses.items():
        if k not in defs:
            fails.append(f"line {n}: footnote [^{k}] is used but never defined")
    for k, n in defs.items():
        if k not in uses:
            warns.append(f"footnote [^{k}] (line {n}) is defined but never used")
    # abstract
    abstract_words = None
    for i, l in enumerate(lines):
        m = ABSTRACT.match(l)
        if m:
            words, j = len(re.findall(r"\b[\w'’-]+\b", m.group(1))), i + 1
            while j < len(lines) and not re.match(r"^\s*(#{1,6}\s|\*\*[^*]+\*\*\s*$|(keywords|key words)\s*:)", lines[j], re.I):
                words += len(re.findall(r"\b[\w'’-]+\b", lines[j]))
                j += 1
            abstract_words = words
            break
    if abstract_limit and abstract_words is not None and abstract_words > abstract_limit:
        fails.append(f"the abstract is {abstract_words} words, over the limit of {abstract_limit}")
    stats["abstract_words"] = abstract_words
    return {"fails": fails, "warns": warns, "stats": stats}


def report(r):
    s = r["stats"]
    L = ["# Manuscript check", "",
         f"Citation style: {s['style'] or 'none found'}; {s['references']} references"
         + (f", {s.get('cited', 0)} cited" if s["style"] else "") + f"; {s.get('figures', 0)} figures; {s.get('tables', 0)} tables"
         + (f"; abstract {s['abstract_words']} words" if s.get("abstract_words") is not None else "") + ".", ""]
    if s.get("renumber"):
        L += ["Renumbering for citation order (old → new): " + ", ".join(f"[{o}] → [{n}]" for o, n in sorted(s["renumber"].items())), ""]
    if not r["fails"]:
        L.append("PASS every citation has a reference, and every figure, table and section referred to exists.")
    L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a manuscript's citations and cross-references.")
    ap.add_argument("manuscript")
    ap.add_argument("--abstract-limit", type=int)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        lines = read_lines(args.manuscript)
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as e:
        print(f"FAIL cannot read {args.manuscript}: {e}")
        return 2
    r = check(lines, args.abstract_limit)
    print(json.dumps(r, indent=2) if args.json else report(r), end="" if not args.json else "\n")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

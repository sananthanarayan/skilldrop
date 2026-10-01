#!/usr/bin/env python3
"""Check the citations in a source synthesis draft.

Every claim in a synthesis should cite a supplied source and a location in it,
written as [S1:p4], [S2:§3.2], [S3:00:12:30], or several at once as
[S1:p4; S2:p7]. Facts from outside the supplied sources are tagged [outside].

This script reads the draft and a sources list and reports:
  - citations whose source id is not in the sources list   (error)
  - malformed citations, such as [S1, S2]                  (error)
  - paragraphs, list items and table rows with no citation (error)
  - citations with no location, such as a bare [S1]        (warning)
  - sources that are never cited                           (warning)
  - [outside] tags, which a reader should check            (info)

Not checked as claims: headings, the Sources and Question sections, a line that
is all italics (such as a "Prepared ..." line), units shorter than --min-words,
units that start with a bold label such as **Strength:** or **Agreement:**
(change with --label), and any unit containing <!-- no-cite -->.
  - how many times each source is cited                    (info)

The sources list is either a separate file (--sources) or a "## Sources"
section inside the draft. Each source is one line that starts with its id:
    S1: Northwind pilot report, Q2 2026 (internal, 18 pp.)
    - [S2] Interview transcript, Acme support lead, 12 Mar 2026

Usage:
    python3 citations.py draft.md
    python3 citations.py draft.md --sources sources.md -o report.md
    python3 citations.py draft.md --strict --json

Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors found,
2 bad input (missing file, no sources found, duplicate source ids).
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

SOURCE_LINE = re.compile(r"^\s*(?:[-*+]\s+)?\[?(S\d+)\]?\s*[:.)\]\-—–]\s*(\S.*)$")
BRACKET = re.compile(r"\[([^\[\]]+)\](?!\()")
CITE_PART = re.compile(r"^\s*(S\d+)\s*(?::\s*(.*?))?\s*$")
LOOKS_LIKE_CITE = re.compile(r"^\s*S\d+\b")
OUTSIDE = re.compile(r"\[outside\]", re.IGNORECASE)
NO_CITE = "<!-- no-cite -->"
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")

DEFAULT_SKIP = ["sources", "references", "bibliography", "source list"]
CLAIM_FREE_SECTIONS = ["question", "questions", "research question"]
DEFAULT_LABELS = ["agreement", "strength", "confidence"]
ITALIC_LINE = re.compile(r"^\s*(_[^_].*_|\*[^*].*\*)\s*$")
LABEL = re.compile(r"^\s*(?:[-*+]\s+)?\*\*([^*:]+):?\*\*")


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


def read_text(path):
    p = Path(path)
    if not p.is_file():
        fail("file not found: " + str(path))
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("not a UTF-8 text file: " + str(path))
    return ""


def parse_sources(lines):
    """Return an ordered dict id -> description, and a list of duplicate ids."""
    sources = OrderedDict()
    dupes = []
    for line in lines:
        m = SOURCE_LINE.match(line)
        if not m:
            continue
        sid, desc = m.group(1), m.group(2).strip()
        if sid in sources:
            dupes.append(sid)
        else:
            sources[sid] = desc
    return sources, dupes


def split_sections(text):
    """Yield (heading_title_lower, [lines]) blocks; the first block has title ''."""
    title = ""
    block = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            block.append(line)
            continue
        m = None if in_code else HEADING.match(line)
        if m:
            yield title, block
            title = m.group(2).strip().lower()
            block = []
        else:
            block.append(line)
    yield title, block


def units(lines, start_line):
    """Split body lines into checkable units: paragraphs, list items, table rows.

    Returns a list of (line_number, text).
    """
    out = []
    current = []
    current_start = None
    in_code = False

    def flush():
        if current:
            out.append((current_start, " ".join(s.strip() for s in current)))

    for offset, line in enumerate(lines):
        n = start_line + offset
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            current, current_start = [], None
            in_code = not in_code
            continue
        if in_code:
            continue
        if not stripped or RULE.match(line) or (stripped.startswith(">") and not stripped.strip("> ")):
            flush()
            current, current_start = [], None
            continue
        if stripped.startswith("|"):
            flush()
            current, current_start = [], None
            if TABLE_SEP.match(line):
                # The row above a separator is the table's header, not a claim.
                if out and out[-1][1].startswith("|"):
                    out.pop()
            else:
                out.append((n, stripped))
            continue
        if LIST_ITEM.match(line):
            flush()
            current, current_start = [line], n
            continue
        if not current:
            current_start = n
        current.append(line)
    flush()
    return out


def main():
    ap = argparse.ArgumentParser(description="Check [S1:p4]-style citations in a synthesis draft.")
    ap.add_argument("draft", help="the draft, as markdown or plain text")
    ap.add_argument("--sources", help="a file listing sources, one per line as 'S1: ...'. "
                                      "Default: the draft's own '## Sources' section")
    ap.add_argument("--skip-section", action="append", default=[],
                    help="a heading whose body needs no citations (repeatable). "
                         "Sources/References are always skipped")
    ap.add_argument("--label", action="append", default=None,
                    help="a bold label, such as Strength, whose unit is a judgment, not a "
                         "claim (repeatable). Default: Agreement, Strength, Confidence")
    ap.add_argument("--min-words", type=int, default=6,
                    help="units shorter than this are treated as labels, not claims (default 6)")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", help="write the report as JSON")
    ap.add_argument("-o", "--output", help="write the report here instead of stdout")
    args = ap.parse_args()

    if args.min_words < 0:
        fail("--min-words must be zero or more")

    text = read_text(args.draft)
    skip = set(DEFAULT_SKIP) | set(CLAIM_FREE_SECTIONS) | set(x.strip().lower() for x in args.skip_section)
    labels = set(x.strip().lower() for x in (args.label if args.label is not None else DEFAULT_LABELS))

    # Sources
    if args.sources:
        sources, dupes = parse_sources(read_text(args.sources).splitlines())
        where = args.sources
    else:
        src_lines = []
        for title, block in split_sections(text):
            if title in DEFAULT_SKIP:
                src_lines.extend(block)
        sources, dupes = parse_sources(src_lines)
        where = "the draft's Sources section"
    if not sources:
        fail("no sources found in " + where + ". List each one on its own line as 'S1: description'.")
    if dupes:
        fail("duplicate source ids in " + where + ": " + ", ".join(sorted(set(dupes))))

    # Walk the body
    unresolved, malformed, uncited, no_location, outside = [], [], [], [], []
    counts = OrderedDict((sid, 0) for sid in sources)
    checked = 0
    line_no = 1
    for title, block in split_sections(text):
        start = line_no + (0 if title == "" else 1)
        line_no = start + len(block)
        if title in skip:
            continue
        for n, unit in units(block, start):
            cited = False
            for m in BRACKET.finditer(unit):
                inner = m.group(1)
                if not LOOKS_LIKE_CITE.match(inner):
                    continue
                for part in inner.split(";"):
                    pm = CITE_PART.match(part)
                    if not pm:
                        malformed.append((n, "[" + inner + "]"))
                        continue
                    sid, loc = pm.group(1), (pm.group(2) or "").strip()
                    if sid not in sources:
                        unresolved.append((n, "[" + inner + "]", sid))
                        continue
                    cited = True
                    counts[sid] += 1
                    if not loc:
                        no_location.append((n, "[" + inner + "]"))
            if OUTSIDE.search(unit):
                outside.append((n, unit))
                cited = True
            if NO_CITE in unit or ITALIC_LINE.match(unit):
                continue
            lm = LABEL.match(unit)
            if lm and lm.group(1).strip().lower() in labels:
                continue
            words = len(re.findall(r"[A-Za-z0-9']+", BRACKET.sub(" ", unit)))
            if words < args.min_words:
                continue
            checked += 1
            if not cited:
                uncited.append((n, unit))

    unused = [sid for sid, c in counts.items() if c == 0]
    errors = len(unresolved) + len(malformed) + len(uncited)
    warnings = len(no_location) + len(unused)
    failed = errors > 0 or (args.strict and warnings > 0)

    if args.json:
        report = json.dumps({
            "draft": args.draft,
            "sources": len(sources),
            "units_checked": checked,
            "errors": errors,
            "warnings": warnings,
            "passed": not failed,
            "unresolved": [{"line": n, "citation": c, "source": s} for n, c, s in unresolved],
            "malformed": [{"line": n, "citation": c} for n, c in malformed],
            "uncited": [{"line": n, "text": t} for n, t in uncited],
            "no_location": [{"line": n, "citation": c} for n, c in no_location],
            "unused_sources": unused,
            "outside": [{"line": n, "text": t} for n, t in outside],
            "citations_per_source": counts,
        }, indent=2) + "\n"
    else:
        def short(t, k=90):
            return t if len(t) <= k else t[:k - 3] + "..."
        out = ["# Citation check: " + Path(args.draft).name, ""]
        out.append("Sources: {}  ·  Claims checked: {}  ·  Errors: {}  ·  Warnings: {}  ·  Result: {}".format(
            len(sources), checked, errors, warnings, "FAIL" if failed else "PASS"))
        out.append("")
        def section(title, rows):
            out.append("## " + title + " (" + str(len(rows)) + ")")
            out.append("")
            if rows:
                out.extend(rows)
            else:
                out.append("None.")
            out.append("")
        section("Errors: citations that do not resolve",
                ["- line {}: {} — no source {} in the list".format(n, c, s) for n, c, s in unresolved])
        section("Errors: malformed citations",
                ["- line {}: {} — write one id per part, separated by ';', e.g. [S1:p4; S2:p7]".format(n, c)
                 for n, c in malformed])
        section("Errors: uncited claims",
                ["- line {}: \"{}\"".format(n, short(t)) for n, t in uncited])
        section("Warnings: citations with no location",
                ["- line {}: {} — add a page, section or timestamp".format(n, c) for n, c in no_location])
        section("Warnings: sources never cited",
                ["- {}: {}".format(s, short(sources[s], 70)) for s in unused])
        section("Info: [outside] claims to check by hand",
                ["- line {}: \"{}\"".format(n, short(t)) for n, t in outside])
        out.append("## Citations per source")
        out.append("")
        out.append("| Source | Citations |")
        out.append("|---|---|")
        for sid, c in counts.items():
            out.append("| {} | {} |".format(sid, c))
        report = "\n".join(out) + "\n"

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        sys.stdout.write("wrote {} — {}, {} error(s), {} warning(s)\n".format(
            args.output, "FAIL" if failed else "PASS", errors, warnings))
    else:
        sys.stdout.write(report)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

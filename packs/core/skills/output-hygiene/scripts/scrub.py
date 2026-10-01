#!/usr/bin/env python3
"""Deterministic surface-hygiene pass over agent-written text. Stdlib only, no network.

    python3 scrub.py DRAFT.md                  # report findings, exit 1 if any
    python3 scrub.py DRAFT.md --fix            # rewrite the file, report what changed
    python3 scrub.py - < draft.md              # read stdin, report
    python3 scrub.py - --fix < draft.md        # read stdin, write cleaned text to stdout
    python3 scrub.py DRAFT.md --json           # machine-readable findings (for a hook)
    python3 scrub.py MSG.txt --medium commit   # a medium where curly quotes ARE a defect
    python3 scrub.py DRAFT.md --ascii --fix    # flatten curly quotes and dashes regardless

Two tiers, and the split is the point:

  AUTO   invisible characters, non-ASCII spacing, provenance trailers, chat closers.
         Removing these cannot change what the text asserts, so --fix applies them.
  REVIEW homoglyphs and typographic punctuation. A blind rewrite here corrupts meaning
         (a Cyrillic 'а' may be intentional; an em dash in Markdown prose is correct),
         so these are reported and left alone unless the caller opts in with --ascii.

Typography is medium-dependent and the default medium is markdown, where curly quotes and
em dashes are correct typesetting rather than defects — reporting them there would bury the
findings that matter under one row per apostrophe. Pass --medium for a target that will
re-encode the text (commit, code, csv, plaintext) and they become review findings.

What this script cannot do is the other half of the job: prose tells — the cadence, the
bolded lead-in on every bullet, the hedge vocabulary — need a model pass. See SKILL.md.

Exit codes: 0 nothing left to fix · 1 findings remain · 2 usage or I/O error.
"""
import argparse
import json
import re
import sys
import unicodedata

# --- AUTO tier ------------------------------------------------------------------------

# Zero-width, directional, and formatting characters. They survive copy-paste, render as
# nothing, and break grep, diff, and anything that compares strings.
INVISIBLE = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "⁠": "WORD JOINER",
    "﻿": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "­": "SOFT HYPHEN",
    " ": "LINE SEPARATOR",
    " ": "PARAGRAPH SEPARATOR",
    "‪": "LEFT-TO-RIGHT EMBEDDING",
    "‫": "RIGHT-TO-LEFT EMBEDDING",
    "‬": "POP DIRECTIONAL FORMATTING",
    "‭": "LEFT-TO-RIGHT OVERRIDE",
    "‮": "RIGHT-TO-LEFT OVERRIDE",
    "⁦": "LEFT-TO-RIGHT ISOLATE",
    "⁧": "RIGHT-TO-LEFT ISOLATE",
    "⁨": "FIRST STRONG ISOLATE",
    "⁩": "POP DIRECTIONAL ISOLATE",
}

# Spaces that are not U+0020. They look identical and silently break word-splitting,
# Markdown table alignment, and YAML.
SPACING = {
    " ": "NO-BREAK SPACE",
    " ": "NARROW NO-BREAK SPACE",
    " ": "FIGURE SPACE",
    " ": "THIN SPACE",
    " ": "HAIR SPACE",
    " ": "EN SPACE",
    " ": "EM SPACE",
    "　": "IDEOGRAPHIC SPACE",
}

# Whole-line provenance trailers added by an agent harness, not by the author.
PROVENANCE = [
    ("co-authored-by trailer", re.compile(r"^\s*co-authored-by:\s*claude\b.*$", re.I)),
    ("generated-with footer", re.compile(r"^\s*(?:\S\s*)?generated with \[?claude code\]?.*$", re.I)),
    ("generated-with footer", re.compile(r"^\s*(?:\S\s*)?generated (?:with|by) \[[^\]]+\]\(https://claude\.com[^)]*\).*$", re.I)),
    # A signature is a dash, a name, and nothing else. A plain "-" opener is excluded and the
    # tail is capped: "- Claude Code project settings: …" is a bullet, not a sign-off, and a
    # cleaner that eats real list items loses the author's trust for the findings that were real.
    ("assistant signature", re.compile(r"^\s*(?:—|–|--)\s*claude\b[\w.()\s-]{0,24}$", re.I)),
]

# A trailing paragraph that addresses the reader as a chat partner. Matched only as the
# final block of the text, and only when it opens with one of these — a conservative list,
# because a false positive here deletes real content.
CLOSER_OPENERS = re.compile(
    r"^(?:let me know (?:if|whether)|(?:i )?hope (?:this|that) helps|"
    r"would you like me to|want me to|happy to (?:help|expand|adjust)|"
    r"feel free to (?:ask|reach out|let me know)|"
    r"if you(?:'| a)?d like(?:,| )?\s*i can)\b",
    re.I,
)

# --- REVIEW tier ----------------------------------------------------------------------

# Non-ASCII letters sitting inside an otherwise-ASCII word: the classic paste artifact
# (and, occasionally, a deliberate spoof). Never auto-fixed — the correct ASCII letter is
# a guess, and the word may be genuinely foreign.
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

TYPOGRAPHY = {
    "‘": ("'", "LEFT SINGLE QUOTATION MARK"),
    "’": ("'", "RIGHT SINGLE QUOTATION MARK"),
    "“": ('"', "LEFT DOUBLE QUOTATION MARK"),
    "”": ('"', "RIGHT DOUBLE QUOTATION MARK"),
    "–": ("-", "EN DASH"),
    "—": ("--", "EM DASH"),
    "…": ("...", "HORIZONTAL ELLIPSIS"),
    "′": ("'", "PRIME"),
    "″": ('"', "DOUBLE PRIME"),
}


def _positions(text):
    """Offset -> (line, col), both 1-based. Computed once; the scan is O(n)."""
    line, col, out = 1, 1, []
    for ch in text:
        out.append((line, col))
        if ch == "\n":
            line, col = line + 1, 1
        else:
            col += 1
    return out


def _finding(cls, tier, line, col, detail, excerpt):
    return {"class": cls, "tier": tier, "line": line, "col": col,
            "detail": detail, "excerpt": excerpt}


def _excerpt(text, offset, width=36):
    lo = text.rfind("\n", 0, offset) + 1
    hi = text.find("\n", offset)
    hi = len(text) if hi == -1 else hi
    frag = text[lo:hi]
    rel = offset - lo
    start = max(0, rel - width // 2)
    snippet = frag[start:start + width].replace("\t", " ")
    return ("…" if start > 0 else "") + snippet.strip() + ("…" if start + width < len(frag) else "")


# Media where typographic punctuation survives and is correct. Everywhere else it is a
# defect waiting for a re-encode.
TYPOGRAPHY_OK = {"markdown", "html"}


def scan(text, ascii_mode=False, medium="markdown"):
    """Return (findings, cleaned_text). cleaned_text applies the AUTO tier, plus the
    REVIEW typography tier when ascii_mode is on. Findings describe the ORIGINAL text."""
    findings = []
    report_typography = ascii_mode or medium not in TYPOGRAPHY_OK
    pos = _positions(text)

    # --- character-level classes
    for i, ch in enumerate(text):
        line, col = pos[i]
        if ch in INVISIBLE:
            findings.append(_finding("invisible", "auto", line, col,
                                     f"U+{ord(ch):04X} {INVISIBLE[ch]} — renders as nothing",
                                     _excerpt(text, i)))
        elif ch in SPACING:
            findings.append(_finding("spacing", "auto", line, col,
                                     f"U+{ord(ch):04X} {SPACING[ch]} — not a plain space",
                                     _excerpt(text, i)))
        elif ch in TYPOGRAPHY and report_typography:
            repl, name = TYPOGRAPHY[ch]
            findings.append(_finding("typography", "auto" if ascii_mode else "review", line, col,
                                     f"U+{ord(ch):04X} {name} — flatten to {repl!r} for plain-text targets",
                                     _excerpt(text, i)))

    # --- homoglyphs: a non-ASCII letter inside a word that is otherwise ASCII
    for m in WORD.finditer(text):
        word = m.group(0)
        # A homoglyph is a LETTER that impersonates another letter. Superscripts and symbols
        # inside a word — the ² in "O(n²)" — are typography, and flagging them is the noise
        # that teaches an author to ignore the findings that were real.
        odd = [(k, c) for k, c in enumerate(word)
               if ord(c) > 127 and unicodedata.category(c).startswith("L")]
        if not odd or len(odd) == len(word):
            continue
        for k, c in odd:
            off = m.start() + k
            line, col = pos[off]
            try:
                name = unicodedata.name(c)
            except ValueError:
                name = "UNNAMED"
            findings.append(_finding("homoglyph", "review", line, col,
                                     f"U+{ord(c):04X} {name} inside ASCII word {word!r} — verify before replacing",
                                     _excerpt(text, off)))

    # --- line-level provenance
    drop_lines = set()
    for n, raw in enumerate(text.split("\n"), start=1):
        for label, pattern in PROVENANCE:
            if pattern.match(raw):
                findings.append(_finding("provenance", "auto", n, 1,
                                         f"{label} — harness-added, not authored", raw.strip()))
                drop_lines.add(n)
                break

    cleaned = "\n".join(l for n, l in enumerate(text.split("\n"), start=1) if n not in drop_lines)
    if drop_lines:
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"\n+\Z", "\n" if text.endswith("\n") else "", cleaned)

    # --- trailing chat closer, measured against the text as it stands after line drops
    trimmed = cleaned.rstrip()
    blocks = re.split(r"\n\s*\n", trimmed)
    if len(blocks) > 1 and CLOSER_OPENERS.match(blocks[-1].strip()):
        tail = blocks[-1]
        idx = trimmed.rfind(tail)
        findings.append(_finding("closer", "auto", trimmed.count("\n", 0, max(idx, 0)) + 1, 1,
                                 "trailing chat closer — addresses a chat partner, not a reader",
                                 " ".join(tail.split())[:80]))
        cleaned = "\n\n".join(blocks[:-1]).rstrip() + ("\n" if text.endswith("\n") else "")

    # --- character substitutions
    for ch in INVISIBLE:
        cleaned = cleaned.replace(ch, "\n" if ch in (" ", " ") else "")
    for ch in SPACING:
        cleaned = cleaned.replace(ch, " ")
    if ascii_mode:
        for ch, (repl, _) in TYPOGRAPHY.items():
            cleaned = cleaned.replace(ch, repl)

    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings, cleaned


TIER_ORDER = {"auto": 0, "review": 1}


def report(path, findings, fixed, ascii_mode, medium):
    auto = [f for f in findings if f["tier"] == "auto"]
    review = [f for f in findings if f["tier"] == "review"]
    head = (f"{path} [{medium}]: {len(findings)} finding(s) — "
            f"{len(auto)} auto, {len(review)} review")
    lines = [head, "=" * len(head)]
    for tier, group, note in (
        ("auto", auto, "applied" if fixed else "safe to apply with --fix"),
        ("review", review, "left alone — judgment required" + ("" if ascii_mode else "; --ascii flattens typography")),
    ):
        if not group:
            continue
        lines.append(f"\n[{tier}] {len(group)} — {note}")
        for f in group:
            lines.append(f"  {str(f['line']) + ':' + str(f['col']):<9} {f['class']:<11} {f['detail']}")
            lines.append(f"  {'':<9} {'':<11} {f['excerpt']}")
    if not findings:
        lines = [f"{path} [{medium}]: clean"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="Report and optionally remove machine artifacts from agent-written text.")
    ap.add_argument("paths", nargs="+", help="files to scan, or - for stdin")
    ap.add_argument("--fix", action="store_true",
                    help="apply the auto tier (rewrites files in place; stdin goes to stdout)")
    ap.add_argument("--medium", default="markdown",
                    choices=["markdown", "html", "plaintext", "commit", "code", "csv"],
                    help="where the text is going; decides whether typographic punctuation "
                         "is a defect (default: markdown, where it is not)")
    ap.add_argument("--ascii", action="store_true",
                    help="report AND flatten curly quotes, dashes, and ellipses whatever the medium")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--quiet", action="store_true", help="exit code only, no report")
    args = ap.parse_args()

    if args.json and args.quiet:
        ap.error("--json and --quiet are mutually exclusive")

    results, remaining = [], 0
    for path in args.paths:
        try:
            text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"scrub.py: cannot read {path}: {e}", file=sys.stderr)
            return 2
        except UnicodeDecodeError:
            print(f"scrub.py: {path} is not UTF-8 text", file=sys.stderr)
            return 2

        findings, cleaned = scan(text, ascii_mode=args.ascii, medium=args.medium)
        if args.fix and cleaned != text:
            if path == "-":
                sys.stdout.write(cleaned)
            else:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(cleaned)
                except OSError as e:
                    print(f"scrub.py: cannot write {path}: {e}", file=sys.stderr)
                    return 2
        elif args.fix and path == "-":
            sys.stdout.write(cleaned)

        left = [f for f in findings if f["tier"] == "review" or not args.fix]
        remaining += len(left)
        results.append({"path": path, "findings": findings,
                        "fixed": args.fix and cleaned != text})

    if args.json:
        print(json.dumps({"results": results, "remaining": remaining}, indent=2))
    elif not args.quiet:
        out = sys.stderr if (args.fix and "-" in args.paths) else sys.stdout
        for r in results:
            print(report(r["path"], r["findings"], r["fixed"], args.ascii, args.medium), file=out)
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())

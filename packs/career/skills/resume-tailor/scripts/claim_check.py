#!/usr/bin/env python3
"""List what a tailored resume or cover letter says that the candidate's own material doesn't.

  python3 claim_check.py DRAFT --source RESUME [--source NOTES ...] [--posting POSTING] [--json]

DRAFT is the text you are about to send. Each --source is something the candidate wrote or
told you: the original resume, notes from the conversation. --posting is the job posting.

It reports four kinds of finding, each with the line it is on:

  number       a figure in the draft that no source contains ("35%", "$2M", "team of 8")
  name         a named thing in the draft that no source contains: a tool, an employer, a
               certification, a degree ("Kubernetes", "Epic", "Green Belt")
  combination  capitalised words that each appear in a source but never together
               ("Senior Manager" when the source has "Senior Analyst" and "Office Manager")
  borrowed     wording the draft shares with the posting and no source uses. Fine when the
               source shows the same thing in other words; a false claim when it doesn't.

A name or number that the posting contains is marked "in posting": right when the draft is
talking about the employer, wrong when it is claimed as the candidate's own.

It reads text, so it cannot tell a true claim from a false one. It tells you where to look.
Exit status: 0 nothing found, 1 findings, 2 a file could not be read. Standard library only.
"""
import argparse
import json
import re
import sys

MULT = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mm": 1e6, "million": 1e6,
        "bn": 1e9, "b": 1e9, "billion": 1e9}
NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?:(k|mm|m|bn|b)\b|\s?(thousand|million|billion)\b)?"
                    r"(\s?%|\s?percent\b|\s?per cent\b)?(?!(?:em|mm|pt|cm|px|fr)\b)", re.I)
WORD = re.compile(r"(?<![A-Za-z0-9])\.?[A-Za-z][A-Za-z0-9+#']*(?:\.[A-Za-z0-9]+)*")
LIST_MARK = re.compile(r"^\s*(?:[-*•–>]+|\d+[.)]|#+|\|)\s*")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SUFFIXES = ("ations", "ation", "ments", "ment", "ings", "ing", "ers", "ies", "ed", "er", "es", "s", "ly")

# Words that start a line or a sentence with a capital letter and name nothing.
PLAIN = set("""
a an and are as at be been both but by for from had has have he her his i if in into is it its
me my no not of on or our she so that the their them then there these they this to up us was
we were what when where which who why with you your dear sincerely regards kind best yours
faithfully hiring manager team committee recruiter sir madam re subject date enclosed
summary profile objective experience employment work history education skills tools
certifications certification qualifications training projects awards languages interests
references available request professional career key core technical additional other
volunteering volunteer contact details achievements highlights about present current
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec monday tuesday wednesday thursday friday
saturday sunday full part time application applying while although though because since
during after before however also please thank thanks between over across within having most each every one two three
""".split())
DATE_LINE = re.compile(r"^\s*(?:\d{1,2}(?:st|nd|rd|th)?\s+)?[A-Z][a-z]{2,8}\.?\s+(?:\d{1,2}(?:st|nd|rd|th)?,?\s+)?\d{4}\s*$")
# The joining words allowed inside a capitalised phrase: "Head of Geography".
JOINERS = {"of", "and", "for", "the", "in", "at", "&", "de"}
STOP = PLAIN | set("""
able across after also been before being between can could did does doing each every experience
experienced including into just like more most much need needs over role roles some such than
them through under using very well will within without work worked working would years year
have with that this from your their about must should strong good great team teams including
ability skills skill knowledge new help helps support supports ensure make makes
""".split())


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        print("claim_check: cannot read %s: %s" % (path, e.strerror), file=sys.stderr)
        sys.exit(2)


def clean(line):
    """A line with its markup removed, so `**Go**` and `Go` read the same. Resumes kept as
    Typst or LaTeX source escape `$`, `&`, `%` and `#`; the escapes are dropped too."""
    line = LINK.sub(r"\1", line)
    line = re.sub(r"\\([$&%#_])", r"\1", line)
    line = line.replace("’", "'").replace("‘", "'").replace("–", " - ").replace("—", " - ")
    return re.sub(r"[*_`~]", "", line)


def numbers(text):
    """{(value, is_percent)} for every figure in the text. "$2M" and "2 million" are one value."""
    found = set()
    for m in NUMBER.finditer(text):
        try:
            value = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        unit = (m.group(2) or m.group(3) or "").lower()
        found.add((value * MULT.get(unit, 1), bool(m.group(4))))
    return found


def stem(word):
    w = word.lower().strip("'.")
    if w.endswith("'s"):
        w = w[:-2]
    for s in SUFFIXES:
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[: -len(s)]
    return w


def key(word):
    """How a name is compared: case, dots, a plural, a possessive or a contraction don't matter."""
    w = word.lower().strip("'")
    w = re.sub(r"'(?:s|m|d|ve|ll|re|t)$", "", w)
    w = w.replace(".", "") or w
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w


def vocabulary(text):
    names, stems = set(), set()
    for line in text.splitlines():
        for w in WORD.findall(clean(line)):
            names.add(key(w))
            stems.add(stem(w))
    flat = " ".join(key(w) for line in text.splitlines() for w in WORD.findall(clean(line)))
    return names, stems, " " + flat + " "


def looks_named(word):
    """True for a word that is a name whatever its position: AWS, JavaScript, C++, k8s, .NET."""
    body = word.lstrip(".")
    return bool(re.search(r"[A-Z]", body[1:]) or re.search(r"[0-9+#]", body) or word.startswith("."))


def phrases(line):
    """Runs of capitalised or name-shaped words in one line, as lists of words.

    The first word of a line or sentence is capitalised by grammar, not because it is a name,
    so it only counts when it is name-shaped itself or opens a longer capitalised run."""
    text = LIST_MARK.sub("", clean(line))
    out, run, start_of_sentence = [], [], True
    tokens = re.findall(r"(?<![A-Za-z0-9])\.?[A-Za-z][A-Za-z0-9+#']*(?:\.[A-Za-z0-9]+)*|&|[.!?;:]\s|[,|·/()]|\s-\s", text + " ")
    for i, tok in enumerate(tokens):
        if not (tok[0].isalpha() or tok[0] in ".&") or tok.strip() in (".", "!", "?", ";", ":"):
            if run:
                out.append(run)
            run = []
            start_of_sentence = tok.strip() in (".", "!", "?")
            continue
        if "'" in tok and key(tok) in PLAIN:  # I'm, I've, we'd
            tok = key(tok)
        capital = tok[0].isupper() or looks_named(tok)
        if capital and not (start_of_sentence and not looks_named(tok) and tok.lower() in PLAIN):
            run.append((tok, start_of_sentence))
        elif run and tok.lower() in JOINERS and i + 1 < len(tokens) and tokens[i + 1][:1].isupper():
            run.append((tok, False))
        else:
            if run:
                out.append(run)
            run = []
        start_of_sentence = False
    if run:
        out.append(run)
    cleaned = []
    for r in out:
        # A lone sentence-opening word ("Led", "Built") is grammar, not a name.
        if len(r) == 1 and r[0][1] and not looks_named(r[0][0]):
            continue
        # A sentence-opening verb in front of a name ("Led AWS migration") is dropped from the run.
        if len(r) > 1 and r[0][1] and not looks_named(r[0][0]) and r[0][0].lower() not in PLAIN:
            r = r[1:] if r[0][0].lower().endswith(("ed", "ing")) else r
        words = [w for w, _ in r]
        while words and words[-1].lower() in JOINERS:
            words.pop()
        if words:
            cleaned.append(words)
    return cleaned


def check(draft, sources, posting):
    src_names, src_stems, src_flat = vocabulary("\n".join(sources))
    src_numbers = numbers("\n".join(clean(s) for s in sources))
    post_names, post_stems, _ = vocabulary(posting or "")
    post_numbers = numbers(clean(posting or ""))
    findings, seen = [], set()

    def add(kind, what, n, line, in_posting=False):
        if (kind, what.lower()) in seen:
            return
        seen.add((kind, what.lower()))
        findings.append({"kind": kind, "text": what, "line": n, "context": line.strip()[:160],
                         "in_posting": in_posting})

    for n, raw in enumerate(draft.splitlines(), 1):
        line = clean(raw)
        if not line.strip() or DATE_LINE.match(LIST_MARK.sub("", line)):
            continue  # a letter's own date line claims nothing
        body = LIST_MARK.sub("", line)
        for m in NUMBER.finditer(body):
            got = next(iter(numbers(m.group(0))), None)
            if got and got not in src_numbers:
                add("number", m.group(0).strip(), n, raw, got in post_numbers)
        for words in phrases(raw):
            content = [w for w in words if w.lower() not in JOINERS]
            missing = [w for w in content if key(w) not in src_names and w.lower() not in PLAIN]
            if missing:
                add("name", " ".join(words), n, raw, all(key(w) in post_names for w in missing))
            elif len(content) > 1 and all(w.lower() not in PLAIN for w in content):
                flat = " ".join(key(w) for w in words if w != "&")
                if " " + flat + " " not in src_flat:
                    add("combination", " ".join(words), n, raw)
        if posting:
            for w in WORD.findall(body):
                s = stem(w)
                if (len(s) >= 4 and w.lower() not in STOP and s in post_stems and s not in src_stems
                        and key(w) not in src_names and not w[0].isupper() and not looks_named(w)):
                    add("borrowed", w.lower(), n, raw, True)
    return findings


def main():
    ap = argparse.ArgumentParser(description="List what a draft says that the candidate's own material doesn't.")
    ap.add_argument("draft")
    ap.add_argument("--source", action="append", required=True, metavar="FILE",
                    help="the candidate's own resume or notes; repeat for more than one")
    ap.add_argument("--posting", metavar="FILE", help="the job posting")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    findings = check(read(a.draft), [read(p) for p in a.source], read(a.posting) if a.posting else None)
    if a.json:
        print(json.dumps({"draft": a.draft, "findings": findings}, indent=1))
        return 1 if findings else 0
    if not findings:
        print("PASS  %s: every figure and name is in the source material." % a.draft)
        return 0
    labels = {"number": "Figures not in the source", "name": "Names not in the source",
              "combination": "Words the source has, but not together",
              "borrowed": "Wording taken from the posting"}
    print("REVIEW  %s: %d item(s) to check against the source material." % (a.draft, len(findings)))
    for kind in ("number", "name", "combination", "borrowed"):
        rows = [f for f in findings if f["kind"] == kind]
        if not rows:
            continue
        print("\n%s (%d)" % (labels[kind], len(rows)))
        for f in rows:
            note = "  [in posting]" if f["in_posting"] and kind != "borrowed" else ""
            print("  line %d: %s%s\n      %s" % (f["line"], f["text"], note, f["context"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())

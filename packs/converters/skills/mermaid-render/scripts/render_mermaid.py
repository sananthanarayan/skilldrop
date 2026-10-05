#!/usr/bin/env python3
"""Lint Mermaid diagrams for the errors that stop them rendering, then render them.

Stdlib only, Python 3.9+.

Lint catches, with line numbers: an unknown diagram type on the first line, unbalanced
brackets or quotes in node labels, unquoted parentheses or brackets inside a label, the
reserved word `end` used as a flowchart node id, a missing or single-dash arrow, and a
subgraph (or sequence `alt`/`loop`/... block) with no `end`.

Render uses `mmdc` (mermaid-cli) for .svg/.png/.pdf when it is on PATH. Without it, the
script writes a standalone .html that draws the diagrams with a pinned Mermaid from
jsDelivr, which needs network when the file is opened.

Usage:
    python3 render_mermaid.py diagram.mmd                  # lint only
    python3 render_mermaid.py diagram.mmd -o diagram.svg   # lint, then render
    python3 render_mermaid.py design.md -o figs/arch.svg   # every ```mermaid fence -> arch-1.svg, arch-2.svg ...
    python3 render_mermaid.py design.md -o design.html     # one HTML page with every diagram
"""

import argparse
import base64
import difflib
import hashlib
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MERMAID_VERSION = "11.4.1"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@%s/dist/mermaid.esm.min.mjs" % MERMAID_VERSION
MERMAID_INIT = ('import mermaid from "%s";'
                'mermaid.initialize({startOnLoad:true,securityLevel:"strict"});' % MERMAID_URL)
MERMAID_INIT_HASH = base64.b64encode(hashlib.sha256(MERMAID_INIT.encode("utf-8")).digest()).decode("ascii")

# Diagram keywords Mermaid 11.4 recognises on the first line.
DIAGRAM_TYPES = [
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "classDiagram-v2", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "journey", "gantt", "pie", "quadrantChart", "requirementDiagram",
    "gitGraph", "C4Context", "C4Container", "C4Component", "C4Dynamic", "C4Deployment", "mindmap",
    "timeline", "zenuml", "sankey-beta", "xychart-beta", "block-beta", "packet-beta",
    "architecture-beta", "kanban",
]
DIRECTIONS = {"TB", "TD", "BT", "RL", "LR"}
FLOW_KEYWORDS = ("classDef", "class", "style", "linkStyle", "click", "direction", "accTitle",
                 "accDescr", "title")
SEQ_OPEN = ("loop", "alt", "opt", "par", "critical", "break", "rect", "box")
SEQ_MIDDLE = {"else": ("alt",), "and": ("par",), "option": ("critical",)}

# Node shapes, longest opener first. Each maps to the closers that may end it.
SHAPES = [("(((", (")))",)), ("((", ("))",)), ("([", ("])",)), ("[[", ("]]",)), ("[(", (")]",)),
          ("[/", ("/]", "\\]")), ("[\\", ("\\]", "/]")), ("{{", ("}}",)), ("[", ("]",)),
          ("(", (")",)), ("{", ("}",)), (">", ("]",))]
ID_RE = re.compile(r"[^\W](?:[\w.]|-(?=\w))*", re.U)
LINK_RE = re.compile(r"\s*(?:<|(?<=\s)[ox](?=[-=]))?(?:-{2,}|={2,}|-\.+-|~{3,})(?:[->ox](?!\w))?>?\s*")


class Issue:
    def __init__(self, line, level, msg):
        self.line, self.level, self.msg = line, level, msg


def strip_edge_labels(s):
    s = re.sub(r"\|[^|]*\|", " ", s)                                              # -->|label|
    s = re.sub(r"-\.(?=[^.\->\s]|\s+[^.\->])\s*([^\n]*?)\s*\.-+>?", " -.-> ", s)  # -. label .->
    s = re.sub(r"(?<![-<.=])--(?!-|>|[ox]\s)\s*([^-|>\n][^|>\n]*?)\s*(?:-{2,}>|-{3,})", " --> ", s)
    s = re.sub(r"(?<![=<])==(?!=|>)\s*([^=|>\n][^|>\n]*?)\s*(?:={2,}>|={3,})", " ==> ", s)
    return s


def split_statements(line):
    """Split on ; outside quotes."""
    out, cur, q = [], "", False
    for ch in line:
        if ch == '"':
            q = not q
        if ch == ";" and not q:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [s for s in out if s.strip()]


def scan_nodes(part, ln, issues):
    """Walk one link-free chunk: node ids, their shapes, & separators. Returns node ids."""
    i, n = 0, len(part)
    ids, need_sep = [], False
    while i < n:
        c = part[i]
        if c.isspace():
            i += 1
            continue
        if c == "&":
            need_sep = False
            i += 1
            continue
        m = ID_RE.match(part, i)
        if not m:
            if c in ")]}":
                issues.append(Issue(ln, "error", "closing `%s` with no matching opening bracket" % c))
            elif c in "([{":
                issues.append(Issue(ln, "error", "a shape `%s` with no node id before it" % c))
            elif c == '"':
                issues.append(Issue(ln, "error", "a quoted label must sit inside a shape, as id[\"label\"]"))
            elif part.startswith("->", i) or part.startswith("=>", i):
                issues.append(Issue(ln, "error", "`%s` is not a flowchart arrow; use `-->` (or `==>`)"
                                    % part[i:i + 2]))
                i += 2
                need_sep = False
                continue
            else:
                issues.append(Issue(ln, "error", "unexpected `%s`" % c))
            return ids
        nid = m.group(0)
        if need_sep:
            issues.append(Issue(ln, "error", "no arrow between `%s` and `%s`; join them with `-->`"
                                % (ids[-1], nid)))
        ids.append(nid)
        if nid == "end":
            issues.append(Issue(ln, "error", "`end` is reserved in flowcharts and breaks the diagram; "
                                "use `End`, `END` or `done` as the node id"))
        i = m.end()
        if part.startswith("@{", i):
            j = part.find("}", i)
            if j < 0:
                issues.append(Issue(ln, "error", "`@{` shape block is never closed with `}`"))
                return ids
            i = j + 1
        else:
            for opener, closers in SHAPES:
                if not part.startswith(opener, i):
                    continue
                i += len(opener)
                if part[i:i + 1] == '"':
                    j = part.find('"', i + 1)
                    if j < 0:
                        issues.append(Issue(ln, "error", "unbalanced quote in the label of `%s`" % nid))
                        return ids
                    i = j + 1
                    while i < n and part[i] == " ":
                        i += 1
                    hit = [cl for cl in closers if part.startswith(cl, i)]
                    if not hit:
                        issues.append(Issue(ln, "error", "label of `%s` opens with `%s` but does not close "
                                            "with `%s` after the quotes" % (nid, opener, closers[0])))
                        return ids
                    i += len(hit[0])
                else:
                    found = [(part.find(cl, i), cl) for cl in closers if part.find(cl, i) >= 0]
                    if not found:
                        issues.append(Issue(ln, "error", "unbalanced brackets: `%s%s` is never closed with `%s`"
                                            % (nid, opener, closers[0])))
                        return ids
                    pos, cl = min(found)
                    label = part[i:pos]
                    bad = sorted({ch for ch in label if ch in '()[]{}"'})
                    if bad:
                        issues.append(Issue(ln, "error", "label of `%s` has unquoted %s; wrap the label in "
                                            "quotes: %s%s\"%s\"%s" % (nid, " ".join("`%s`" % b for b in bad),
                                                                    nid, opener, label.replace('"', "'"), cl)))
                    i = pos + len(cl)
                break
        m2 = re.match(r":::[\w-]+", part[i:])
        if m2:
            i += m2.end()
        need_sep = True
    return ids


def lint_flowchart(lines, issues):
    stack = []
    for ln, raw in lines:
        s = raw.strip()
        if not s or s.startswith("%%"):
            continue
        word = s.split()[0]
        if word == "subgraph":
            stack.append(ln)
            rest = s[len("subgraph"):].strip()
            if rest.count('"') % 2:
                issues.append(Issue(ln, "error", "unbalanced quote in the subgraph title"))
            elif re.match(r'^"[^"]*"$', rest):
                pass
            elif re.match(r"^[^\W][\w.-]*\s*[\[({>]", rest, re.U):
                scan_nodes(rest, ln, issues)              # subgraph id[label]
            elif re.search(r"[\[\](){}]", rest):
                issues.append(Issue(ln, "error", "subgraph title has unquoted brackets; write "
                                    "subgraph id[\"%s\"]" % rest.replace('"', "'")))
            continue
        if s == "end":
            if stack:
                stack.pop()
            else:
                issues.append(Issue(ln, "error", "`end` with no open subgraph"))
            continue
        if word in FLOW_KEYWORDS or word.startswith(("accTitle:", "accDescr")):
            continue
        for stmt in split_statements(s):
            if stmt.count('"') % 2:
                issues.append(Issue(ln, "error", "unbalanced double quote"))
                continue
            if re.search(r"(?:-{2,}|={2,})[ox][A-Za-z0-9_]", stmt):
                issues.append(Issue(ln, "warning", "`--o`/`--x` followed by a letter is read as a circle or "
                                    "cross arrowhead; add a space if the node id starts with o or x"))
            for lab in re.findall(r"\|([^|]*)\|", stmt):
                inner = lab.strip()
                bad = sorted({ch for ch in inner if ch in "()[]{}"})
                if bad and not (inner.startswith('"') and inner.endswith('"')):
                    issues.append(Issue(ln, "error", "arrow label |%s| has unquoted %s; quote it: |\"%s\"|"
                                        % (inner, " ".join("`%s`" % b for b in bad), inner)))
            body = strip_edge_labels(stmt)
            parts = LINK_RE.split(body)
            if len(parts) > 1 and (not parts[0].strip() or not parts[-1].strip()):
                issues.append(Issue(ln, "error", "an arrow with no node on one side"))
            for part in parts:
                if part.strip():
                    scan_nodes(part, ln, issues)
    for ln in stack:
        issues.append(Issue(ln, "error", "subgraph opened here has no matching `end`"))


def lint_sequence(lines, issues):
    stack = []
    for ln, raw in lines:
        s = raw.strip()
        if not s or s.startswith("%%"):
            continue
        word = s.split()[0]
        if word in SEQ_OPEN:
            stack.append((word, ln))
        elif word in SEQ_MIDDLE:
            if not stack or stack[-1][0] not in SEQ_MIDDLE[word]:
                issues.append(Issue(ln, "error", "`%s` outside a `%s` block" % (word, SEQ_MIDDLE[word][0])))
        elif s == "end":
            if stack:
                stack.pop()
            else:
                issues.append(Issue(ln, "error", "`end` with no open loop/alt/opt/par/critical/break/rect/box"))
        elif re.search(r"(?:-{1,2}>>?|-{1,2}[x)])", s) and ":" not in s and not s.startswith(("participant", "actor", "Note", "note", "autonumber", "activate", "deactivate", "create", "destroy", "title", "link", "links")):
            issues.append(Issue(ln, "error", "message without `: text`; write `A->>B: what is sent`"))
    for word, ln in stack:
        issues.append(Issue(ln, "error", "`%s` block opened here has no matching `end`" % word))


def lint_braces(lines, issues):
    depth, opened = 0, []
    for ln, raw in lines:
        s = re.sub(r'"[^"]*"', "", raw)
        # erDiagram cardinality markers such as ||--o{ and }|..|{ are not braces
        s = re.sub(r"(?:\|o|\|\||\}o|\}\|)(?:--|\.\.)(?:o\||\|\||o\{|\|\{)", " ", s)
        if s.strip().startswith("%%"):
            continue
        for ch in s:
            if ch == "{":
                depth += 1
                opened.append(ln)
            elif ch == "}":
                if depth == 0:
                    issues.append(Issue(ln, "error", "`}` with no matching `{`"))
                else:
                    depth -= 1
                    opened.pop()
    for ln in opened:
        issues.append(Issue(ln, "error", "`{` opened here is never closed"))


def lint(text, first_line=1):
    """Lint one diagram. first_line is the file line number of the diagram's first line."""
    issues = []
    lines = [(first_line + k, l) for k, l in enumerate(text.split("\n"))]
    k = 0
    # skip front matter (--- ... ---), %%{init}%% directives and comments
    while k < len(lines) and not lines[k][1].strip():
        k += 1
    if k < len(lines) and lines[k][1].strip() == "---":
        k += 1
        while k < len(lines) and lines[k][1].strip() != "---":
            k += 1
        k += 1
    while k < len(lines) and (not lines[k][1].strip() or lines[k][1].strip().startswith("%%")):
        k += 1
    if k >= len(lines):
        return [Issue(first_line, "error", "the diagram is empty")], None
    ln, head = lines[k]
    words = head.strip().split()
    kind = words[0].rstrip(";:")
    if kind not in DIAGRAM_TYPES:
        guess = difflib.get_close_matches(kind, DIAGRAM_TYPES, n=1, cutoff=0.6)
        hint = " Did you mean `%s`?" % guess[0] if guess else " Start with one of: flowchart, sequenceDiagram, classDiagram, stateDiagram-v2, erDiagram, gantt."
        issues.append(Issue(ln, "error", "unknown diagram type `%s` on the first line.%s" % (kind, hint)))
        return issues, None
    body = lines[k + 1:]
    if kind in ("flowchart", "graph"):
        if len(words) > 1 and words[1].rstrip(";") not in DIRECTIONS:
            issues.append(Issue(ln, "error", "unknown direction `%s`; use TD, TB, BT, LR or RL" % words[1]))
        lint_flowchart(body, issues)
    elif kind == "sequenceDiagram":
        lint_sequence(body, issues)
    elif kind in ("classDiagram", "classDiagram-v2", "stateDiagram", "stateDiagram-v2", "erDiagram"):
        lint_braces(body, issues)
    if not any(l.strip() and not l.strip().startswith("%%") for _, l in body) and kind not in ("pie",):
        issues.append(Issue(ln, "warning", "the diagram has a type but no content"))
    return issues, kind


# ---------------------------------------------------------------- input

def extract_fences(text):
    """Return [(first_line_number, diagram_text)] for every ```mermaid / ~~~mermaid fence."""
    out = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^\s{0,3}(`{3,}|~{3,})\s*mermaid\b", lines[i])
        if m:
            fence = m.group(1)
            start = i + 2  # 1-based line number of the first diagram line
            body = []
            i += 1
            while i < len(lines) and not re.match(r"^\s{0,3}%s%s*\s*$" % (re.escape(fence), re.escape(fence[0])), lines[i]):
                body.append(lines[i])
                i += 1
            if i >= len(lines):
                out.append((start, "\n".join(body), "unclosed"))
            else:
                out.append((start, "\n".join(body), None))
        i += 1
    return out


# ---------------------------------------------------------------- render

def html_page(diagrams, title):
    csp = ("default-src 'none'; script-src 'sha256-%s' https://cdn.jsdelivr.net; "
           "style-src 'unsafe-inline'; img-src data: https:; font-src data: https:; "
           "connect-src https://cdn.jsdelivr.net" % MERMAID_INIT_HASH)
    figs = []
    for k, (label, text) in enumerate(diagrams, 1):
        figs.append('<figure><pre class="mermaid">%s</pre><figcaption>%s</figcaption></figure>'
                    % (html.escape(text), html.escape(label)))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="%s">
<title>%s</title>
<style>
body{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;margin:2rem auto;max-width:72rem;padding:0 1rem;color:#222}
figure{margin:0 0 2.5rem;border:1px solid #e3e3e3;border-radius:6px;padding:1rem}
figcaption{font-size:.85rem;color:#666;margin-top:.5rem}
pre.mermaid{text-align:center;background:#fff;margin:0}
.note{font-size:.85rem;color:#666}
@media print{figure{break-inside:avoid;border:0}.note{display:none}}
</style>
</head>
<body>
<p class="note">Drawn by Mermaid %s loaded from cdn.jsdelivr.net; this page needs network when opened.</p>
%s
<script type="module">%s</script>
</body>
</html>
""" % (csp, html.escape(title), MERMAID_VERSION, "\n".join(figs), MERMAID_INIT)


def run_mmdc(exe, text, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "diagram.mmd"
        src.write_text(text, encoding="utf-8")
        cmd = [exe, "-i", str(src), "-o", str(out_path)]
        if out_path.suffix.lower() == ".png":
            cmd += ["-b", "white", "-s", "2"]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
        except subprocess.TimeoutExpired:
            return "mmdc timed out after 180 s"
        if proc.returncode != 0:
            return mmdc_error((proc.stderr or proc.stdout).decode("utf-8", "replace"))
    return None


def mmdc_error(raw):
    """Mermaid's own message (from "Error:" up to the stack trace), not the stack trace:
    mmdc prints a browser-library trace after the parse error, and the parse error is the
    part a person can act on."""
    lines = raw.strip().splitlines()
    start = next((k for k, l in enumerate(lines) if l.lstrip().startswith("Error")), 0)
    keep = []
    for l in lines[start:]:
        if re.match(r"^\s+at\s", l) or re.search(r"\((https?|file)://[^)]*\)\s*$", l):
            break
        keep.append(l.rstrip())
    msg = "\n".join(keep[:8]).strip()
    return msg or raw.strip()[-800:]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint Mermaid diagrams, then render to svg/png/pdf (mmdc) or html.")
    ap.add_argument("input", help=".mmd/.mermaid file with one diagram, or .md with ```mermaid fences")
    ap.add_argument("-o", "--output", help="out.svg | out.png | out.pdf | out.html. Leave out to lint only.")
    ap.add_argument("--force", action="store_true", help="render even when lint finds errors")
    a = ap.parse_args(argv)

    src = Path(a.input)
    if not src.is_file():
        sys.exit("error: input not found: %s" % a.input)
    try:
        text = src.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    except UnicodeDecodeError:
        sys.exit("error: %s is not UTF-8 text" % a.input)

    if src.suffix.lower() in (".md", ".markdown"):
        fences = extract_fences(text)
        if not fences:
            sys.exit("error: no ```mermaid fences found in %s" % a.input)
        diagrams = fences
    else:
        diagrams = [(1, text, None)]

    errors = warnings = 0
    for k, (start, body, flag) in enumerate(diagrams, 1):
        issues, kind = lint(body, start)
        if flag == "unclosed":
            issues.insert(0, Issue(start - 1, "error", "the ```mermaid fence is never closed"))
        label = "diagram %d (%s)" % (k, kind or "unknown type") if len(diagrams) > 1 else (kind or "diagram")
        if not issues:
            print("%s: %s: ok" % (src.name, label))
        for it in sorted(issues, key=lambda x: x.line):
            print("%s:%d: %s: %s" % (src.name, it.line, it.level, it.msg))
            if it.level == "error":
                errors += 1
            else:
                warnings += 1
    print("lint: %d diagram(s), %d error(s), %d warning(s)" % (len(diagrams), errors, warnings))

    if not a.output:
        return 1 if errors else 0
    if errors and not a.force:
        sys.stdout.flush()
        print("not rendering: fix the errors above, or rerun with --force", file=sys.stderr)
        return 1

    out = Path(a.output)
    if not out.parent.exists():
        sys.exit("error: output folder does not exist: %s" % out.parent)
    ext = out.suffix.lower()
    if ext not in (".svg", ".png", ".pdf", ".html", ".htm"):
        sys.exit("error: output must end in .svg, .png, .pdf or .html")
    many = len(diagrams) > 1
    labels = ["%s, diagram %d (line %d)" % (src.name, k, d[0]) if many else src.name
              for k, d in enumerate(diagrams, 1)]

    exe = shutil.which("mmdc") if ext in (".svg", ".png", ".pdf") else None
    if exe:
        failed = 0
        for k, (start, body, _) in enumerate(diagrams, 1):
            target = out.with_name("%s-%d%s" % (out.stem, k, out.suffix)) if many else out
            err = run_mmdc(exe, body, target)
            if err:
                failed += 1
                print("mmdc failed on %s:\n%s" % (labels[k - 1], err), file=sys.stderr)
            else:
                print("wrote %s" % target)
        return 1 if failed else 0

    target = out if ext in (".html", ".htm") else out.with_suffix(".html")
    target.write_text(html_page([(labels[k], d[1]) for k, d in enumerate(diagrams)], src.name), encoding="utf-8")
    if ext not in (".html", ".htm"):
        print("mmdc (mermaid-cli) is not on PATH, so no %s was written. Wrote %s instead: it draws "
              "the diagram(s) with Mermaid %s from cdn.jsdelivr.net and needs network when opened. "
              "For %s output: npm install -g @mermaid-js/mermaid-cli, then rerun."
              % (ext, target, MERMAID_VERSION, ext))
    else:
        print("wrote %s (%d diagram(s); draws with Mermaid %s from cdn.jsdelivr.net, needs network when opened)"
              % (target, len(diagrams), MERMAID_VERSION))
    return 0


if __name__ == "__main__":
    sys.exit(main())

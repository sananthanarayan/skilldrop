#!/usr/bin/env python3
"""Docs portal generator for skilldrop. No deps, no network. Run from the repo root:

    python3 build_docs.py              # writes build/docs/index.html + per-guide pages
    python3 build_docs.py --out <dir>  # write somewhere else
    python3 build_docs.py --check      # exit 1 if build/docs/ differs from a fresh render

Walks guides/ recursively, reads frontmatter (title/summary/kind), renders markdown
to HTML, and emits a portal landing page plus one page per guide with sidebar nav.
Stdlib only — no setup-python step needed in CI.
"""
import argparse
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
GUIDES_DIR = os.path.join(ROOT, "guides")

from build_loops import LIFECYCLE, COLOUR  # stage order, headings and colours (RFC-0044)
REPO_URL = "https://github.com/sananthanarayan/skilldrop"
SITE_URL = "https://sananthanarayan.github.io/skilldrop/"

# Diátaxis kinds in display order.
KINDS = ["tutorial", "how-to", "reference", "explanation"]
KIND_LABELS = {
    "tutorial":    "Tutorial",
    "how-to":      "How-to",
    "reference":   "Reference",
    "explanation": "Explanation",
}
# The sidebar opens with these pages, in this order, then the five stages, then everything
# else by kind (RFC-0044). Each entry is (kind, slug); a missing one fails the build.
START = [("explanation", "operating-model"), ("how-to", "install"), ("how-to", "install-per-ide"),
         ("tutorial", "follow-a-change-through-the-loops")]

# Files outside guides/ that the portal also publishes: (repo path, kind, title, summary).
OUTSIDE_GUIDES = [
    ("CONTRIBUTING.md", "explanation", "Contributing",
     "How to add or change a skill, a pack, a loop or a subagent, what an RFC is needed for, and the checks a pull request must pass."),
]

KIND_TAGLINES = {
    "tutorial":    "Learn by doing something real.",
    "how-to":      "I have a goal — what are the steps?",
    "reference":   "What exactly does this field or command do?",
    "explanation": "Why is it built this way?",
}

# ── CSS shared across every docs page ────────────────────────────────────────

SHARED_CSS = """
:root {
  --dark-950:#0d0d0f; --dark-900:#141417;
  --n-50:#fafaf9; --n-100:#f3f3f1; --n-200:#e4e4e0; --n-600:#6a6a66; --n-900:#17171a;
  --accent:#7c5cff; --accent-300:#a48cff; --accent-700:#4c31d6; --accent-10:rgba(124,92,255,.10);
  --w-06:rgba(255,255,255,.06); --w-10:rgba(255,255,255,.10); --w-20:rgba(255,255,255,.20);
  --w-60:rgba(255,255,255,.60); --w-80:rgba(255,255,255,.80);
  --surface:var(--n-50); --surface-alt:var(--n-100); --fg:var(--n-900);
  --fg-muted:var(--n-600); --border:var(--n-200); --card:#fff;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --r-sm:5px; --r:10px;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;background:var(--surface);color:var(--fg);
  font:400 1rem/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,sans-serif;
  -webkit-font-smoothing:antialiased;}
a{color:var(--accent-700);}
/* doc header */
.doc-header{background:var(--surface-alt);border-bottom:1px solid var(--border);
  padding:.75rem 1.5rem;font-size:.85rem;display:flex;align-items:center;gap:.5rem;}
.doc-header a{color:var(--accent-700);text-decoration:none;}
.doc-header .sep{color:var(--fg-muted);}
/* layout */
.layout{display:grid;grid-template-columns:220px 1fr;gap:2.5rem;
  max-width:1100px;margin:2rem auto;padding:0 1.5rem;}
@media(max-width:700px){.layout{grid-template-columns:1fr;}.sidebar{display:none;}}
.layout--toc{max-width:1320px;}
@media(min-width:1180px){.layout--toc{grid-template-columns:220px minmax(0,1fr) 210px;}}
.toc{display:none;}
@media(min-width:1180px){.toc{display:block;position:sticky;top:1.5rem;align-self:start;font-size:.8rem;
  border-left:1px solid var(--border);padding-left:1rem;max-height:calc(100vh - 3rem);overflow:auto;}}
.toc__h{font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--fg-muted);margin:0 0 .6rem;}
.toc ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.35rem;}
.toc a{color:var(--fg-muted);text-decoration:none;}
.toc a:hover{color:var(--accent-700);}
.toc__3{padding-left:.8rem;}
.edit{margin:2.5rem 0 1rem;font-size:.85rem;color:var(--fg-muted);}
.edit a{color:var(--fg-muted);}
.pager{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0 2rem;}
.pager a{display:block;border:1px solid var(--border);border-radius:8px;padding:.8rem 1rem;text-decoration:none;color:var(--fg);font-weight:600;font-size:.92rem;}
.pager a:hover{border-color:var(--accent-700);}
.pager span{display:block;font-size:.72rem;font-weight:500;text-transform:uppercase;letter-spacing:.06em;color:var(--fg-muted);margin-bottom:.2rem;}
.pager__next{text-align:right;}
/* sidebar */
.sidebar{font-size:.85rem;position:sticky;top:1.5rem;align-self:start;}
.sidebar details{margin-bottom:1rem;}
.sidebar summary{font-weight:700;font-size:.72rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--accent-700);cursor:pointer;
  list-style:none;margin-bottom:.5rem;}
.sidebar ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.35rem;}
.sidebar a{color:var(--fg-muted);text-decoration:none;font-size:.83rem;
  display:block;padding:.15rem 0;}
.sidebar a:hover{color:var(--accent-700);}
.sidebar a[aria-current="page"]{color:var(--accent-700);font-weight:600;}
/* content */
.content{min-width:0;}
.content h1{font-size:1.9rem;line-height:1.15;letter-spacing:-.02em;margin:0 0 .5rem;}
.content .summary{font-size:1.05rem;color:var(--fg-muted);margin:0 0 2rem;
  padding-bottom:1.5rem;border-bottom:1px solid var(--border);}
.content h2{font-size:1.3rem;margin:2rem 0 .5rem;
  border-bottom:1px solid var(--border);padding-bottom:.35rem;}
.content h3{font-size:1.05rem;margin:1.5rem 0 .4rem;}
.content h4,h5,h6{font-size:.95rem;margin:1.2rem 0 .3rem;}
.content p{margin:.6rem 0 1rem;line-height:1.7;}
.content ul,.content ol{padding-left:1.4rem;margin:.5rem 0 1rem;line-height:1.7;}
.content pre{background:var(--surface-alt);border:1px solid var(--border);
  border-radius:var(--r);padding:1rem;overflow-x:auto;margin:1rem 0;}
.content code{font:.83em var(--mono);background:var(--accent-10);
  padding:1px 4px;border-radius:3px;}
.content pre code{background:none;padding:0;font-size:.82em;}
/* portal landing */
.portal-inner{max-width:1100px;margin:0 auto;padding:2rem 1.5rem;}
.portal-hero{margin-bottom:2.5rem;}
.portal-hero h1{font-size:2.2rem;letter-spacing:-.03em;margin:0 0 .4rem;}
.portal-hero p{font-size:1.06rem;color:var(--fg-muted);margin:0;}
.kind-section{margin-bottom:2.5rem;}
.kind-section h2{font-size:.75rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--accent-700);margin:0 0 .2rem;}
.kind-section .kind-tagline{font-size:.84rem;color:var(--fg-muted);
  margin:0 0 .9rem;font-style:italic;}
.doc-cards{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));}
.doc-card{background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:1.2rem;}
.doc-card h3{margin:0 0 .4rem;font-size:1rem;letter-spacing:-.01em;}
.doc-card p{margin:0 0 .8rem;font-size:.85rem;color:var(--fg-muted);line-height:1.5;}
.doc-card--packs{grid-column:1/-1;}
.doc-card--packs p{font-size:.9rem;line-height:1.9;}
.doc-card--packs a{color:var(--accent-700);white-space:nowrap;}
.doc-card a.read{font-size:.85rem;font-weight:600;color:var(--accent-700);text-decoration:none;}
.doc-card a.read:hover{text-decoration:underline;}
.sidebar-search{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;
  padding:.4rem .6rem;font-size:.8rem;color:var(--fg-muted);text-decoration:none;
  border:1px solid var(--border);border-radius:4px;background:var(--card);}
.sidebar-search:hover{border-color:var(--accent-700);color:var(--fg);}
.sidebar-search kbd{font:600 .68rem ui-monospace,Menlo,monospace;border:1px solid var(--border);border-radius:4px;padding:0 .3rem;}
/* tables */
.table-wrap{overflow-x:auto;margin:1rem 0 1.4rem;}
.content table{border-collapse:collapse;width:100%;font-size:.9rem;}
.content th,.content td{border-bottom:1px solid var(--border);padding:.5rem .7rem;text-align:left;vertical-align:top;}
.content td:first-child{white-space:nowrap;}
.content th{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--fg-muted);}
.content blockquote{margin:1rem 0;padding:.2rem 1rem;border-left:3px solid var(--accent-700);color:var(--fg-muted);}
/* stages (RFC-0044): each stage keeps its colour from the operating-model picture */
.sidebar .side-h{font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--fg-muted);margin:0 0 .6rem;}
.sidebar details.stage{border-left:3px solid var(--stage);padding-left:.7rem;margin-bottom:.8rem;}
.sidebar details.stage summary{color:var(--stage);}
.sidebar .stage-n{display:inline-block;min-width:1.1rem;}
.stage-chip{display:inline-block;margin:0 0 .6rem;padding:.15rem .6rem;border-radius:999px;font-size:.72rem;
  font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--stage);
  border:1px solid var(--stage);}
.content figure{margin:1.5rem 0;}
.content figure img{display:block;width:100%;height:auto;}
.stage-cards{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));}
.stage-card{background:var(--card);border:1px solid var(--border);border-top:4px solid var(--stage);
  border-radius:var(--r);padding:1rem 1.1rem;}
.stage-card h3{margin:0;font-size:.95rem;color:var(--stage);}
.stage-card p{margin:.2rem 0 .7rem;font-size:.82rem;color:var(--fg-muted);line-height:1.45;}
.stage-card ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:.35rem;font-size:.84rem;}
.stage-card a{color:var(--accent-700);text-decoration:none;}
.stage-card a:hover{text-decoration:underline;}
/* search */
.search-wrap{margin:1.5rem 0;}
#docs-search{width:100%;max-width:520px;padding:.7rem 1rem;font-size:1rem;
  color:var(--fg);background:var(--card);border:1px solid var(--border);
  border-radius:6px;outline:none;}
#docs-search:focus{border-color:var(--accent-700);box-shadow:0 0 0 3px var(--accent-10);}
/* reading aids: tutorial length, section lists, code copy */
.doc-card p.doc-time{margin:-.1rem 0 .5rem;font-size:.75rem;font-weight:600;color:var(--accent-700);}
.kind-section h2 a{color:inherit;text-decoration:none;}
.kind-section h2 a:hover{text-decoration:underline;}
.doc-list{padding-left:1.1rem;font-size:.9rem;}
.doc-list li{margin:.35rem 0;}
.code-wrap{position:relative;}
.code-copy{position:absolute;top:.4rem;right:.4rem;cursor:pointer;font:600 .72rem/1 inherit;
  color:var(--accent-700);background:var(--card);border:1px solid var(--border);border-radius:4px;padding:.35rem .55rem;}
.code-copy:hover{border-color:var(--accent-700);}
.code-copy:focus-visible{outline:2px solid var(--accent);outline-offset:1px;}
""".strip()

# ── Frontmatter parser ────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Return (meta_dict, body_text). Minimal YAML scalar parser."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body

# ── Markdown renderer ─────────────────────────────────────────────────────────

def _esc(s):
    return html.escape(str(s), quote=True)

def _slug(text):
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<![*\w])\*(?![*\s])(.+?)(?<![*\s])\*(?![*\w])")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# `_emphasis_` opens and closes only outside a word, so snake_case names stay as they are.
_UNDER = re.compile(r"(?<![\w\\])_(?![_\s])(.+?)(?<![_\s])_(?!\w)")
_STRIKE = re.compile(r"~~(?!\s)(.+?)(?<!\s)~~")
_AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")

def _href(target, src, docs_base=None):
    """Point a guide's markdown link at something that exists on the published site. A link
    to another guide becomes that guide's .html page; a link to any other repo file (AGENTS.md,
    an RFC, a skill's SKILL.md) goes to GitHub, because the site does not carry those files.
    `src` is the guide's repo-relative path; without it, links pass through unchanged."""
    if not src or re.match(r"^([a-z]+:|#|/)", target):
        return target
    path, _, anchor = target.partition("#")
    repo_path = os.path.normpath(os.path.join(os.path.dirname(src), path)).replace(os.sep, "/")
    if repo_path.startswith(".."):
        return target
    frag = f"#{anchor}" if anchor else ""
    # Guides publish flat, as docs/<kind>/<slug>.html, even from a subfolder such as
    # guides/how-to/packs/ (the generated pack guides), so match on kind + file name only.
    m = re.match(r"^guides/([^/]+)/(?:[^/]+/)*([^/]+)\.md$", repo_path)
    if m and not src.startswith("guides/"):
        # A page outside the docs portal (the changelog) links into it through docs_base.
        return f"{docs_base or ''}{m.group(1)}/{m.group(2)}.html" + frag
    here = src[len("guides/"):].split("/")[0] if src.count("/") > 1 else "."
    if m:
        return os.path.relpath(f"{m.group(1)}/{m.group(2)}.html", here).replace(os.sep, "/") + frag
    if repo_path == "guides/README.md":
        return os.path.relpath("index.html", here).replace(os.sep, "/") + frag
    full = os.path.join(ROOT, repo_path)
    if os.path.exists(full):
        kind = "tree" if os.path.isdir(full) else "blob"
        return f"{REPO_URL}/{kind}/main/{repo_path}{frag}"
    return target


def _inline(text, src=None, docs_base=None):
    # Order matters: escape HTML first on raw parts, then apply inline markup.
    # Process link/code/bold as replacements on the original text.
    parts = []
    pos = 0
    tokens = sorted(
        [m for pat in (_INLINE_CODE, _AUTOLINK, _BOLD, _LINK, _ITAL, _UNDER, _STRIKE) for m in pat.finditer(text)],
        key=lambda m: m.start()
    )
    for m in tokens:
        if m.start() < pos:
            continue  # overlapping — skip
        parts.append(_esc(text[pos:m.start()]))
        if m.re is _INLINE_CODE:
            parts.append(f"<code>{_esc(m.group(1))}</code>")
        elif m.re is _BOLD:
            parts.append(f"<strong>{_inline(m.group(1), src, docs_base)}</strong>")
        elif m.re in (_ITAL, _UNDER):
            parts.append(f"<em>{_inline(m.group(1), src, docs_base)}</em>")
        elif m.re is _STRIKE:
            parts.append(f"<del>{_inline(m.group(1), src, docs_base)}</del>")
        elif m.re is _AUTOLINK:
            parts.append(f'<a href="{_esc(m.group(1))}">{_esc(m.group(1))}</a>')
        else:  # link — its text may carry `code` or **bold**, so render it inline too
            parts.append(f'<a href="{_esc(_href(m.group(2), src, docs_base))}">{_inline(m.group(1), src, docs_base)}</a>')
        pos = m.end()
    parts.append(_esc(text[pos:]))
    return "".join(parts)

# A diagram on a line of its own: ![alt](src), optionally wrapped in a link to the full size.
_FIGURE = re.compile(r"^\[?!\[([^\]]*)\]\(([^)\s]+)\)(?:\]\(([^)\s]+)\))?$")
# SVGs a guide shows, keyed by their path under docs/: render_all publishes each beside the pages.
ASSETS = {}


def _asset(target, src):
    """A repo SVG a guide shows is published at docs/img/<name>; anything else passes through."""
    if not src or re.match(r"^([a-z]+:|#|/)", target) or not target.endswith(".svg"):
        return target
    repo_path = os.path.normpath(os.path.join(os.path.dirname(src), target))
    full = os.path.join(ROOT, repo_path)
    if not os.path.isfile(full):
        return target
    ASSETS["img/" + os.path.basename(full)] = full
    return "../img/" + os.path.basename(full)


def _figure(m, src):
    """One image line. A `#gh-light-mode-only` or `#gh-dark-mode-only` fragment, which GitHub
    uses to pick the image for its own theme, does the same job here through a class."""
    target, link = m.group(2), m.group(3)
    theme = ""
    for frag, cls in (("#gh-light-mode-only", "only-light"), ("#gh-dark-mode-only", "only-dark")):
        if target.endswith(frag):
            target, theme = target[: -len(frag)], cls
        if link and link.endswith(frag):
            link = link[: -len(frag)]
    img = f'<img src="{_esc(_asset(target, src))}" alt="{_esc(m.group(1))}" loading="lazy">'
    if link:
        img = f'<a href="{_esc(_asset(link, src))}">{img}</a>'
    return f'<figure{f" class={chr(34)}{theme}{chr(34)}" if theme else ""}>{img}</figure>'


_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


_LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")


def _list_html(lines, il):
    """A list block, nested by indentation: an item indented past its parent's marker starts a
    sublist, and an indented line that is not an item continues the item above it. `[ ]` and
    `[x]` at the start of an item render as checkboxes."""
    root = {"children": [], "indent": -1}
    stack = [root]  # each entry: a list item dict (root is a sentinel)
    for ln in lines:
        if not ln.strip():
            continue
        m = _LIST_ITEM.match(ln)
        if m:
            indent = len(m.group(1).expandtabs(4))
            while len(stack) > 1 and indent <= stack[-1]["indent"]:
                stack.pop()
            item = {"indent": indent, "ordered": m.group(2)[0].isdigit(), "num": m.group(2)[:-1],
                    "text": m.group(3), "children": []}
            stack[-1]["children"].append(item)
            stack.append(item)
        elif len(stack) > 1:
            stack[-1]["text"] += " " + ln.strip()

    def render(items):
        ordered = items[0]["ordered"]
        tag = "ol" if ordered else "ul"
        start = items[0]["num"] if ordered else "1"
        attr = f' start="{int(start)}"' if ordered and start.isdigit() and int(start) != 1 else ""
        out = [f"<{tag}{attr}>"]
        for it in items:
            task = _TASK.match(it["text"])
            if task:
                box = '<input type="checkbox" disabled' + (" checked" if task.group(1) in "xX" else "") + "> "
                body, cls = box + il(task.group(2)), ' class="task"'
            else:
                body, cls = il(it["text"]), ""
            out.append(f"<li{cls}>{body}{render(it['children']) if it['children'] else ''}</li>")
        out.append(f"</{tag}>")
        return "".join(out)
    return render(root["children"]) if root["children"] else ""


def render_md(text, src=None, docs_base=None):
    """The markdown the guides, skills and changelog use: ATX headings, fenced code, nested and
    ordered lists with task checkboxes, pipe tables, blockquotes holding any of these, images on
    a line of their own, and paragraphs that span several lines."""
    lines = text.splitlines()
    out, para = [], []
    il = lambda t: _inline(t, src, docs_base)

    def flush_para():
        if para:
            out.append(f"<p>{il(' '.join(para))}</p>")
            para.clear()

    i = 0
    while i < len(lines):
        raw = lines[i]
        if raw.lstrip().startswith("```"):
            # Fences may be indented (a code block inside a list item); strip that indent.
            flush_para()
            pad = len(raw) - len(raw.lstrip())
            lang = raw.strip()[3:].strip()
            cls = f' class="language-{_esc(lang)}"' if lang else ""
            buf, i = [], i + 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                ln = lines[i]
                buf.append(ln[pad:] if ln[:pad].strip() == "" else ln.lstrip()); i += 1
            out.append(f"<pre><code{cls}>{_esc(chr(10).join(buf))}</code></pre>")
            i += 1
            continue
        if not raw.strip():
            flush_para(); i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", raw):
            flush_para(); out.append("<hr>"); i += 1
            continue
        if raw.lstrip().startswith("<!--"):
            # HTML comments (e.g. the generated-block markers) never reach the page, including
            # ones that span several lines: skip through the line that closes the comment.
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = _FIGURE.match(raw.strip())
        if m:
            flush_para()
            out.append(_figure(m, src))
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            flush_para()
            level, text_content = len(m.group(1)), m.group(2).strip().rstrip("#").strip()
            slug = _slug(re.sub(r"[*`\[\]]", "", text_content))
            out.append(f'<h{level} id="{slug}">{il(text_content)}</h{level}>')
            i += 1
            continue
        if raw.lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1].strip()):
            flush_para()
            head = "".join(f"<th>{il(c)}</th>" for c in _cells(raw))
            rows, i = [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append("<tr>" + "".join(f"<td>{il(c)}</td>" for c in _cells(lines[i])) + "</tr>")
                i += 1
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
            continue
        if raw.startswith(">"):
            # A quote holds markdown of its own (an example document, a heading, a list), so its
            # lines render recursively. Its headings carry no id: they are not this page's sections.
            flush_para()
            inner = []
            while i < len(lines) and lines[i].startswith(">"):
                ln = lines[i][1:]
                inner.append(ln[1:] if ln.startswith(" ") else ln)
                i += 1
            body = re.sub(r'(<h[1-6]) id="[^"]*"', r"\1", render_md("\n".join(inner), src, docs_base))
            out.append(f"<blockquote>{body}</blockquote>")
            continue
        if _LIST_ITEM.match(raw) and (not para or not raw[0].isspace()):
            flush_para()
            # Gather the whole list: items at any depth and their indented continuation lines,
            # through single blank lines, until a line at the margin that is not an item.
            block = []
            while i < len(lines):
                ln = lines[i]
                if ln.lstrip().startswith(("```", "|", ">")) and not _LIST_ITEM.match(ln):
                    break
                if not ln.strip():
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if not (_LIST_ITEM.match(nxt) or nxt.startswith(("  ", "\t"))):
                        break
                elif not _LIST_ITEM.match(ln) and not ln.startswith(("  ", "\t")):
                    break
                block.append(ln); i += 1
            out.append(_list_html(block, il))
            continue
        para.append(raw.strip()); i += 1
    flush_para()
    return "\n".join(out)

# ── Guide discovery ───────────────────────────────────────────────────────────

def collect_guides():
    """Returns {kind: [{title, summary, kind, slug, rel_path, abs_path}]} in KINDS order."""
    by_kind = {k: [] for k in KINDS}
    for dirpath, _, filenames in os.walk(GUIDES_DIR):
        for fname in sorted(filenames):
            if not fname.endswith(".md") or fname == "README.md":
                continue
            abs_path = os.path.join(dirpath, fname)
            text = open(abs_path, encoding="utf-8").read()
            meta, _ = parse_frontmatter(text)
            kind = meta.get("kind", "").strip()
            if kind not in KINDS:
                print(f"build_docs.py: skipping {abs_path} — unknown kind '{kind}'",
                      file=sys.stderr)
                continue
            slug = os.path.splitext(fname)[0]
            rel_path = os.path.relpath(abs_path, ROOT)
            by_kind[kind].append({
                "title":    meta.get("title", slug),
                "summary":  meta.get("summary", ""),
                "kind":     kind,
                "stage":    meta.get("stage", ""),
                "slug":     slug,
                "rel_path": rel_path,
                "abs_path": abs_path,
                # Generated per-pack guides (build_pack_guides.py) live in a packs/ subfolder and
                # are grouped, so 2 × N pack pages don't bury the hand-written guides.
                "group":    os.path.basename(dirpath) if os.path.basename(dirpath) in ("packs", "skills") else "",
            })
    # Repo files published into the portal as they are, so the site's copy can't drift.
    for rel, kind, title, summary in OUTSIDE_GUIDES:
        by_kind[kind].append({"title": title, "summary": summary, "kind": kind, "stage": "",
                              "slug": os.path.splitext(os.path.basename(rel))[0].lower(), "rel_path": rel,
                              "abs_path": os.path.join(ROOT, rel), "group": ""})
    return by_kind

# ── HTML page builders ────────────────────────────────────────────────────────

def _page(title, header_html, body_html, depth=2, desc="", url="", extra_head=""):
    # The shared site nav (RFC-0035), so a reader deep in a guide can still reach packs and skills.
    from build_site import site_nav, head_meta, NAV_CSS
    nav = site_nav("../" * depth, "docs/")
    # Mermaid blocks (the loop diagrams in guides/reference/loops.md) render as diagrams, not code.
    mermaid = ""
    if 'class="language-mermaid"' in body_html:
        body_html = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                           r'<pre class="mermaid">\1</pre>', body_html, flags=re.S)
        mermaid = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
                   'mermaid.initialize({ startOnLoad: true, securityLevel: "strict" });</script>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
{head_meta(title, desc, url) if url else ""}
{extra_head}
<link rel="icon" href="{"../" * depth}favicon.svg" type="image/svg+xml">
<style>
{SHARED_CSS}
{NAV_CSS}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism-tomorrow.min.css">
<style>
/* Code keeps the Tomorrow theme's own dark background: its token colours are made for it,
   and on the page's light surface they were close to unreadable. */
.content pre[class*="language-"]{{border-radius:6px;font-size:.84rem;}}
.content pre[class*="language-"] code{{background:none;border:0;padding:0;}}
</style>
</head>
<body>
{nav}
{header_html}
{body_html}
<script defer src="https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/autoloader/prism-autoloader.min.js"></script>
{mermaid}
{COPY_CODE_JS if "<pre><code" in body_html else ""}
</body>
</html>"""

# A copy button on every code block. The button is added by script, so with scripting off
# there is no button that does nothing; the code stays selectable either way.
COPY_CODE_JS = """<script>
document.querySelectorAll('.content pre > code').forEach(function (code) {
  var pre = code.parentNode, wrap = document.createElement('div'), b = document.createElement('button');
  wrap.className = 'code-wrap'; pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
  b.type = 'button'; b.className = 'code-copy'; b.textContent = 'Copy'; b.setAttribute('aria-label', 'Copy this code');
  b.addEventListener('click', function () {
    var t = code.innerText, say = function (m) { b.textContent = m; setTimeout(function () { b.textContent = 'Copy'; }, 1500); };
    var legacy = function () {
      var a = document.createElement('textarea'); a.value = t; a.setAttribute('readonly', '');
      a.style.position = 'absolute'; a.style.left = '-9999px'; document.body.appendChild(a); a.select();
      var ok = false; try { ok = document.execCommand('copy'); } catch (e) {} document.body.removeChild(a);
      say(ok ? 'Copied' : 'Select & copy');
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(function () { say('Copied'); }, legacy);
    else legacy();
  });
  wrap.appendChild(b);
});
</script>"""


def _groups(by_kind):
    """The sidebar's order (RFC-0044): Start here, then one group per lifecycle stage (its loop's
    page, then the pages filed under that stage), then every remaining page by Diátaxis kind.
    Each guide appears once. Returns [(key, label, [guide | ("loop", name)])]."""
    every = {(g["kind"], g["slug"]): g for k in KINDS for g in by_kind.get(k, [])}
    missing = [f"{k}/{s}" for k, s in START if (k, s) not in every]
    if missing:
        raise SystemExit(f"build_docs.py: START names guides that do not exist: {', '.join(missing)}")
    placed = set(START)
    groups = [("start", "Start here", [every[ks] for ks in START])]
    for name in LIFECYCLE:
        staged = [g for ks, g in every.items() if g["stage"] == name and ks not in placed]
        staged.sort(key=lambda g: (bool(g.get("group")), KINDS.index(g["kind"])))
        placed |= {(g["kind"], g["slug"]) for g in staged}
        groups.append((f"stage:{name}", name, [("loop", name)] + staged))
    for kind in KINDS:
        rest = [g for g in by_kind.get(kind, []) if (g["kind"], g["slug"]) not in placed]
        if rest:
            groups.append((kind, KIND_LABELS[kind], rest))
    return groups


def _order(by_kind):
    """Every guide in sidebar order, for previous/next."""
    return [g for _, _, items in _groups(by_kind) for g in items if isinstance(g, dict)]


def _sidebar_html(by_kind, current_kind, current_slug, depth):
    """depth=1 for docs/index.html, depth=2 for docs/kind/slug.html"""
    prefix = "../" * (depth - 1)
    parts = ['<nav class="sidebar" aria-label="Guides">']
    if depth == 2:
        # Opens the site-wide search dialog; without JavaScript it is a link to the docs index.
        parts.append(
            '<a class="js-search sidebar-search" href="../index.html">Search the site'
            '<kbd>/</kbd></a>'
        )

    def link(g):
        href = f"{prefix}{g['kind']}/{g['slug']}.html"
        aria = ' aria-current="page"' if g["kind"] == current_kind and g["slug"] == current_slug else ""
        return f'<li><a href="{href}"{aria}>{_esc(g["title"])}</a></li>'

    for n, (key, label, items) in enumerate(_groups(by_kind)):
        if key.startswith("stage:"):
            if key == f"stage:{next(iter(LIFECYCLE))}":
                parts.append('<p class="side-h">Through the stages</p>')
            name = key.split(":", 1)[1]
            stage_no = list(LIFECYCLE).index(name) + 1
            parts.append(f'<details open class="stage" style="--stage:{COLOUR[name]}">'
                         f'<summary><span class="stage-n">{stage_no}</span>{_esc(name.capitalize())}</summary><ul>')
            for it in items:
                if isinstance(it, tuple):
                    parts.append(f'<li><a href="{"../" * depth}loops/{it[1]}/">The {it[1]} loop</a></li>')
                else:
                    parts.append(link(it))
            parts.append("</ul></details>")
            continue
        parts.append(f'<details open><summary>{_esc(label)}</summary><ul>')
        for g in [g for g in items if not g.get("group")]:
            parts.append(link(g))
        for gname, glabel in (("packs", "Per pack"), ("skills", "Per skill")):
            grouped = [g for g in items if g.get("group") == gname]
            if not grouped:
                continue
            inside = any(g["kind"] == current_kind and g["slug"] == current_slug for g in grouped)
            parts.append(f'<li><details{" open" if inside else ""}><summary>{glabel} ({len(grouped)})</summary><ul>')
            parts += [link(g) for g in grouped]
            parts.append("</ul></details></li>")
        parts.append("</ul></details>")
    parts.append("</nav>")
    return "\n".join(parts)

def _stage_chip(guide):
    name = guide.get("stage")
    if name not in LIFECYCLE:
        return ""
    return (f'<p class="stage-chip" style="--stage:{COLOUR[name]}">'
            f'Stage {list(LIFECYCLE).index(name) + 1} · {_esc(name)}</p>')


def build_guide_page(guide, by_kind, out_dir):
    text = open(guide["abs_path"], encoding="utf-8").read()
    _, body_md = parse_frontmatter(text)
    # The page header already shows the frontmatter title; drop the body's own "# Title".
    body_md = re.sub(r"\A\s*# [^\n]*\n", "", body_md)
    src = os.path.relpath(guide["abs_path"], ROOT).replace(os.sep, "/")
    body_html = render_md(body_md, src=src, docs_base=None if src.startswith("guides/") else "../")
    sidebar = _sidebar_html(by_kind, guide["kind"], guide["slug"], depth=2)
    header = (
        '<header class="doc-header">'
        '<a href="../../index.html">skilldrop</a>'
        '<span class="sep">·</span>'
        '<a href="../index.html">docs</a>'
        f'<span class="sep">·</span><a href="index.html">{_esc(KIND_LABELS[guide["kind"]])}</a>'
        "</header>"
    )
    # Reading aids: an "On this page" rail from the h2/h3 headings, previous/next in sidebar
    # order, and an edit link to the source on GitHub.
    heads = [(lvl, hid, re.sub(r"<[^>]+>", "", txt)) for lvl, hid, txt in
             re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', body_html)]
    toc = ""
    if len(heads) >= 2:
        toc = ('<aside class="toc" aria-label="On this page"><p class="toc__h">On this page</p><ul>'
               + "".join(f'<li class="toc__{lvl}"><a href="#{_esc(hid)}">{txt}</a></li>' for lvl, hid, txt in heads)
               + "</ul></aside>")
    order = _order(by_kind)
    at = next(n for n, g in enumerate(order) if g["slug"] == guide["slug"] and g["kind"] == guide["kind"])
    prev_g = order[at - 1] if at > 0 else None
    next_g = order[at + 1] if at + 1 < len(order) else None
    pager = ('<nav class="pager" aria-label="Previous and next guide" data-pagefind-ignore>'
             + (f'<a class="pager__prev" href="../{prev_g["kind"]}/{prev_g["slug"]}.html"><span>Previous</span>{_esc(prev_g["title"])}</a>' if prev_g else '<span></span>')
             + (f'<a class="pager__next" href="../{next_g["kind"]}/{next_g["slug"]}.html"><span>Next</span>{_esc(next_g["title"])}</a>' if next_g else '<span></span>')
             + "</nav>")
    rel = os.path.relpath(guide["abs_path"], ROOT).replace(os.sep, "/")
    edit = (f'<p class="edit" data-pagefind-ignore><a href="{REPO_URL}/edit/main/{_esc(rel)}">Edit this page on GitHub</a>'
            f' · <a href="{REPO_URL}/blob/main/{_esc(rel)}">View source</a></p>')
    content = (
        f'<main class="content" id="main" data-pagefind-body data-pagefind-meta="kind:{guide["kind"]}">'
        f'{_stage_chip(guide)}'
        f'<h1>{_esc(guide["title"])}</h1>'
        f'<p class="summary">{_esc(guide["summary"])}</p>'
        f'{body_html}'
        f'{edit}{pager}'
        f'</main>'
    )
    page_body = f'<div class="layout{" layout--toc" if toc else ""}">{sidebar}{content}{toc}</div>'
    from build_site import SITE_URL, breadcrumbs_ld, ld
    url = f"{SITE_URL}docs/{guide['kind']}/{guide['slug']}.html"
    meta = (breadcrumbs_ld([("skilldrop", SITE_URL), ("Docs", f"{SITE_URL}docs/"),
                            (KIND_LABELS[guide["kind"]], f"{SITE_URL}docs/{guide['kind']}/"), (guide["title"], url)])
            + ld({"@context": "https://schema.org", "@type": "TechArticle", "headline": guide["title"],
                  "description": guide["summary"], "url": url, "inLanguage": "en"}))
    page_html = _page(f'{guide["title"]} — skilldrop docs', header, page_body,
                      desc=guide["summary"], url=url, extra_head=meta)
    out_path = os.path.join(out_dir, guide["kind"], f'{guide["slug"]}.html')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    return out_path, page_html

_DURATION = re.compile(r"^In about ([a-z -]+?) you'll", re.M)


def duration(guide):
    """How long a tutorial says it takes, from its own first line ("In about twenty minutes
    you'll…"). None when the guide doesn't say, rather than a guess."""
    if guide["kind"] != "tutorial":
        return None
    m = _DURATION.search(open(guide["abs_path"], encoding="utf-8").read())
    return f"About {m.group(1)}" if m else None


def _card(g, href):
    d = duration(g)
    return (f'<div class="doc-card" data-slug="{_esc(g["slug"])}" data-kind="{_esc(g["kind"])}">'
            f'<h3>{_esc(g["title"])}</h3>'
            + (f'<p class="doc-time">{_esc(d)}</p>' if d else "")
            + f'<p>{_esc(g["summary"])}</p>'
            f'<a class="read" href="{href}">Read &rarr;</a></div>')


def build_section_index(kind, by_kind):
    """docs/<kind>/index.html: every guide of one kind, so the URL a reader trims to (and the
    kind in each guide's header) lands on a page instead of a 404."""
    guides = by_kind.get(kind, [])
    header = ('<header class="doc-header"><a href="../../index.html">skilldrop</a><span class="sep">·</span>'
              f'<a href="../index.html">docs</a><span class="sep">·</span><span>{_esc(KIND_LABELS[kind])}</span></header>')
    cards = "".join(_card(g, f'{g["slug"]}.html') for g in guides if not g.get("group"))
    grouped = ""
    for gname, glabel in (("packs", "Per pack"), ("skills", "Per skill")):
        gs = [g for g in guides if g.get("group") == gname]
        if gs:
            grouped += (f'<h2>{glabel} ({len(gs)})</h2><ul class="doc-list">'
                        + "".join(f'<li><a href="{g["slug"]}.html">{_esc(g["title"])}</a> — {_esc(g["summary"])}</li>' for g in gs)
                        + "</ul>")
    content = (f'<main class="content" id="main"><h1>{_esc(KIND_LABELS[kind])}</h1>'
               f'<p class="summary">{_esc(KIND_TAGLINES[kind])}</p>'
               f'<div class="doc-cards">{cards}</div>{grouped}</main>')
    from build_site import SITE_URL
    page = _page(f"{KIND_LABELS[kind]} — skilldrop docs", header,
                 f'<div class="layout">{_sidebar_html(by_kind, None, None, depth=2)}{content}</div>',
                 desc=f"Every skilldrop {KIND_LABELS[kind].lower()} guide. {KIND_TAGLINES[kind]}", url=f"{SITE_URL}docs/{kind}/")
    return f"{kind}/index.html", page


def build_portal_index(by_kind, out_dir):
    header = (
        '<header class="doc-header">'
        '<a href="../index.html">skilldrop</a>'
        '<span class="sep">·</span><span>docs</span>'
        "</header>"
    )
    groups = _groups(by_kind)
    start = groups[0][2]
    cards_html = [
        '<section class="kind-section"><h2>Start here</h2>'
        '<p class="kind-tagline">The operating model, then install, then one change followed end to end.</p>'
        '<div class="doc-cards">'
        + "".join(f'<div class="doc-card"><h3>{_esc(g["title"])}</h3><p>{_esc(g["summary"])}</p>'
                  f'<a class="read" href="{g["kind"]}/{g["slug"]}.html">Read &rarr;</a></div>' for g in start)
        + "</div></section>"
    ]
    stage_cards = []
    for key, _, items in groups:
        if not key.startswith("stage:"):
            continue
        name = key.split(":", 1)[1]
        links = "".join(
            f'<li><a href="../loops/{it[1]}/">The {it[1]} loop</a></li>' if isinstance(it, tuple)
            else f'<li><a href="{it["kind"]}/{it["slug"]}.html">{_esc(it["title"])}</a></li>'
            for it in items)
        stage_cards.append(
            f'<div class="stage-card" style="--stage:{COLOUR[name]}">'
            f'<h3>{list(LIFECYCLE).index(name) + 1} · {_esc(name)}</h3>'
            f'<p>{_esc(LIFECYCLE[name][0])}</p><ul>{links}</ul></div>')
    cards_html.append(
        '<section class="kind-section"><h2>Through the stages</h2>'
        '<p class="kind-tagline">Each stage\'s loop, and the guides for the work done there.</p>'
        f'<div class="stage-cards">{"".join(stage_cards)}</div></section>')
    for kind in KINDS:
        guides = by_kind.get(kind, [])
        if not guides:
            continue
        label = KIND_LABELS[kind]
        tagline = KIND_TAGLINES[kind]
        cards = "".join(_card(g, f'{g["kind"]}/{g["slug"]}.html') for g in guides if not g.get("group"))
        grouped = [g for g in guides if g.get("group")]
        if grouped:
            cards += (f'<div class="doc-card doc-card--packs" data-kind="{_esc(kind)}"><h3>Per pack</h3>'
                      f'<p>' + " · ".join(f'<a href="{g["kind"]}/{g["slug"]}.html">{_esc(g["title"].replace("Use the ", "").replace(" pack reference", "").replace(" pack", ""))}</a>'
                                          for g in grouped) + '</p></div>')
        cards_html.append(
            f'<section class="kind-section">'
            f'<h2><a href="{kind}/">{_esc(label)}</a></h2>'
            f'<p class="kind-tagline">{_esc(tagline)}</p>'
            f'<div class="doc-cards">{cards}</div>'
            f'</section>'
        )
    search_js = (
        "<script>(function(){"
        "var input=document.getElementById('docs-search');"
        "if(!input)return;"
        "var index=[];"
        "fetch('search-index.json').then(function(r){return r.json();})"
        ".then(function(data){index=data;"
        "var params=new URLSearchParams(location.search);"
        "var q=params.get('q');"
        "if(q){input.value=q;input.dispatchEvent(new Event('input'));}"
        "});"
        "input.addEventListener('input',function(){"
        "var q=this.value.trim().toLowerCase();"
        "var cards=document.querySelectorAll('.doc-card[data-slug]');"
        "var visible=0;"
        "cards.forEach(function(card){"
        "var slug=card.dataset.slug,kind=card.dataset.kind;"
        "if(!q){card.style.display='';visible++;return;}"
        "var entry=index.find(function(e){return e.slug===slug&&e.kind===kind;});"
        "var text=entry?(entry.title+' '+entry.summary+' '+entry.body).toLowerCase():'';"
        "var show=text.indexOf(q)!==-1;"
        "card.style.display=show?'':'none';"
        "if(show)visible++;"
        "});"
        "var msg=document.getElementById('search-empty');"
        "if(msg)msg.style.display=(visible===0&&q)?'':'none';"
        "});"
        "})();</script>"
    )
    body = (
        '<main class="portal-inner" id="main">'
        '<div class="portal-hero">'
        '<h1>Documentation</h1>'
        '<p>Start with the operating model, then follow your work through the five stages. '
        'Every guide is also listed below by kind: tutorials to learn by doing, how-tos for a goal.</p>'
        '<p>New here? <a href="../start/">Get started in four steps</a>: install, choose your starting work, ask, then check the result.</p>'
        '</div>'
        '<div class="search-wrap">'
        '<input id="docs-search" type="search" placeholder="Search guides…" autocomplete="off" aria-label="Search guides">'
        '</div>'
        '<p id="search-empty" style="display:none;color:var(--fg-muted);font-size:.9rem;">No guides match your search.</p>'
        + "".join(cards_html) +
        f'<p style="margin-top:2rem;font-size:.85rem;color:var(--fg-muted)">'
        f'<a href="{REPO_URL}/blob/main/llms.txt"><code>llms.txt</code></a> '
        f'&mdash; the same index in plain text, for agents to read instead of crawling the tree.</p>'
        '</main>'
        + search_js
    )
    from build_site import SITE_URL
    page_html = _page("Documentation — skilldrop", header, body, depth=1,
                      desc="Install guides, tutorials, the loop reference and the full skill catalogue for skilldrop.",
                      url=f"{SITE_URL}docs/")
    out_path = os.path.join(out_dir, "index.html")
    return out_path, page_html

# ── Main ──────────────────────────────────────────────────────────────────────

def _plain_text(html_str):
    """Strip HTML tags and collapse whitespace for search indexing."""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    return re.sub(r'\s+', ' ', text).strip()[:400]

def render_all(out_dir):
    """Return ({relative_path: html_string}, [search_index_entries])."""
    by_kind = collect_guides()
    pages = {}
    search_index = []
    # Guide pages
    for kind in KINDS:
        for guide in by_kind.get(kind, []):
            path, html_text = build_guide_page(guide, by_kind, out_dir)
            rel = os.path.relpath(path, out_dir)
            pages[rel] = html_text
            raw = open(guide["abs_path"], encoding="utf-8").read()
            _, body_md = parse_frontmatter(raw)
            body_plain = _plain_text(render_md(body_md))
            search_index.append({
                "title":   guide["title"],
                "kind":    guide["kind"],
                "slug":    guide["slug"],
                "summary": guide["summary"],
                "url":     f"{guide['kind']}/{guide['slug']}.html",
                "body":    body_plain,
            })
    for kind in KINDS:
        if by_kind.get(kind):
            rel, page = build_section_index(kind, by_kind)
            pages[rel] = page
    # Portal index
    idx_path, idx_html = build_portal_index(by_kind, out_dir)
    pages["index.html"] = idx_html
    # Diagrams the guides show, published beside the pages that link to them.
    for rel, full in sorted(ASSETS.items()):
        pages[rel] = open(full, encoding="utf-8").read()
    return pages, search_index

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "docs"),
                    help="output directory (default: build/docs/)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any output file is missing or stale")
    args = ap.parse_args()

    pages, search_index = render_all(args.out)
    index_json = json.dumps(search_index, ensure_ascii=False, indent=2)
    index_rel = "search-index.json"
    index_path = os.path.join(args.out, index_rel)

    if args.check:
        stale = []
        for rel, text in pages.items():
            p = os.path.join(args.out, rel)
            if not os.path.exists(p):
                stale.append(f"{rel}: missing")
            elif open(p, encoding="utf-8").read() != text:
                stale.append(f"{rel}: stale")
        if not os.path.exists(index_path):
            stale.append(f"{index_rel}: missing")
        elif open(index_path, encoding="utf-8").read() != index_json:
            stale.append(f"{index_rel}: stale")
        if stale:
            print("build_docs.py --check: docs portal is stale:", file=sys.stderr)
            for s in stale:
                print(f"  {s}", file=sys.stderr)
            print("  run: python3 build_docs.py", file=sys.stderr)
            sys.exit(1)
        print(f"OK: docs portal is current ({len(pages)} pages + search index).")
        return

    os.makedirs(args.out, exist_ok=True)
    for rel, text in pages.items():
        p = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote docs/{rel}")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_json)
    print(f"wrote docs/{index_rel}  ({len(search_index)} entries)")
    total_guides = sum(len(v) for v in collect_guides().values())
    print(f"\n{total_guides} guides rendered into {os.path.relpath(args.out, ROOT)}/")
    print(f"Preview: python3 -m http.server -d {os.path.relpath(os.path.dirname(args.out), ROOT)}")


if __name__ == "__main__":
    main()

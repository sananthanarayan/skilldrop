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
@media (prefers-color-scheme:dark) {
  :root {
    --surface:#111113; --surface-alt:#17171a; --fg:#ecebe8; --fg-muted:#9a9a95;
    --border:#2a2a2d; --card:#1a1a1d; --accent:#a48cff; --accent-700:#c4b5ff;
    --accent-10:rgba(164,140,255,.12);
  }
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
/* search */
.search-wrap{margin:1.5rem 0;}
#docs-search{width:100%;max-width:520px;padding:.7rem 1rem;font-size:1rem;
  color:var(--fg);background:var(--card);border:1px solid var(--border);
  border-radius:6px;outline:none;}
#docs-search:focus{border-color:var(--accent-700);box-shadow:0 0 0 3px var(--accent-10);}
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
    m = re.match(r"^guides/([^/]+)/([^/]+)\.md$", repo_path)
    if m and not src.startswith("guides/"):
        # A page outside the docs portal (the changelog) links into it through docs_base.
        return f"{docs_base or ''}{m.group(1)}/{m.group(2)}.html" + frag
    if m:
        here = os.path.dirname(src)[len("guides/"):] or "."
        return os.path.relpath(f"{m.group(1)}/{m.group(2)}.html", here).replace(os.sep, "/") + frag
    if repo_path == "guides/README.md":
        return os.path.relpath("index.html", os.path.dirname(src)[len("guides/"):] or ".").replace(os.sep, "/") + frag
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
        [m for pat in (_INLINE_CODE, _BOLD, _LINK, _ITAL) for m in pat.finditer(text)],
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
        elif m.re is _ITAL:
            parts.append(f"<em>{_inline(m.group(1), src, docs_base)}</em>")
        else:  # link — its text may carry `code` or **bold**, so render it inline too
            parts.append(f'<a href="{_esc(_href(m.group(2), src, docs_base))}">{_inline(m.group(1), src, docs_base)}</a>')
        pos = m.end()
    parts.append(_esc(text[pos:]))
    return "".join(parts)

_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def render_md(text, src=None, docs_base=None):
    """The markdown subset the guides use: ATX headings, fenced code, lists (with wrapped
    continuation lines), pipe tables, blockquotes, and paragraphs that span several lines."""
    lines = text.splitlines()
    out, para, item, quote = [], [], None, []
    list_type = None  # "ul" | "ol" | None
    il = lambda t: _inline(t, src, docs_base)

    def flush_para():
        if para:
            out.append(f"<p>{il(' '.join(para))}</p>")
            para.clear()

    def flush_item():
        nonlocal item
        if item is not None:
            out.append(f"<li>{il(item)}</li>")
            item = None

    def flush_list():
        nonlocal list_type
        flush_item()
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def flush_quote():
        if quote:
            out.append(f"<blockquote><p>{il(' '.join(quote))}</p></blockquote>")
            quote.clear()

    def flush_all():
        flush_para(); flush_list(); flush_quote()

    i = 0
    while i < len(lines):
        raw = lines[i]
        if raw.startswith("```"):
            flush_all()
            lang = raw[3:].strip()
            cls = f' class="language-{_esc(lang)}"' if lang else ""
            buf, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            out.append(f"<pre><code{cls}>{_esc(chr(10).join(buf))}</code></pre>")
            i += 1
            continue
        if not raw.strip():
            flush_all(); i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", raw):
            flush_all(); out.append("<hr>"); i += 1
            continue
        if raw.lstrip().startswith("<!--"):
            # HTML comments (e.g. the generated-block markers) never reach the page, including
            # ones that span several lines: skip through the line that closes the comment.
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            flush_all()
            level, text_content = len(m.group(1)), m.group(2).strip()
            slug = _slug(re.sub(r"[*`\[\]]", "", text_content))
            out.append(f'<h{level} id="{slug}">{il(text_content)}</h{level}>')
            i += 1
            continue
        if raw.lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1].strip()):
            flush_all()
            head = "".join(f"<th>{il(c)}</th>" for c in _cells(raw))
            rows, i = [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append("<tr>" + "".join(f"<td>{il(c)}</td>" for c in _cells(lines[i])) + "</tr>")
                i += 1
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
            continue
        if raw.startswith(">"):
            flush_para(); flush_list()
            quote.append(raw.lstrip(">").strip()); i += 1
            continue
        m = re.match(r"^(- |\d+\. )(.*)", raw)
        if m:
            flush_para(); flush_quote()
            kind = "ul" if m.group(1) == "- " else "ol"
            if list_type != kind:
                flush_list(); out.append(f"<{kind}>"); list_type = kind
            flush_item(); item = m.group(2)
            i += 1
            continue
        if item is not None and raw.startswith(("  ", "\t")):
            item += " " + raw.strip(); i += 1
            continue
        flush_list(); flush_quote()
        para.append(raw.strip()); i += 1
    flush_all()
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
                "slug":     slug,
                "rel_path": rel_path,
                "abs_path": abs_path,
            })
    return by_kind

# ── HTML page builders ────────────────────────────────────────────────────────

def _page(title, header_html, body_html, depth=2):
    # The shared site nav (RFC-0035), so a reader deep in a guide can still reach packs and skills.
    from build_site import site_nav, NAV_CSS
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
<link rel="icon" href="{"../" * depth}favicon.svg" type="image/svg+xml">
<style>
{SHARED_CSS}
{NAV_CSS}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism-tomorrow.min.css">
<style>
.content pre[class*="language-"]{{background:var(--surface-alt);border:1px solid var(--border);border-radius:6px;}}
.content pre[class*="language-"] code{{background:none;}}
</style>
</head>
<body>
{nav}
{header_html}
{body_html}
<script src="https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/autoloader/prism-autoloader.min.js"></script>
{mermaid}
</body>
</html>"""

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
    for kind in KINDS:
        guides = by_kind.get(kind, [])
        if not guides:
            continue
        label = KIND_LABELS[kind]
        parts.append(f'<details open><summary>{label}</summary><ul>')
        for g in guides:
            href = f"{prefix}{g['kind']}/{g['slug']}.html"
            current = g["kind"] == current_kind and g["slug"] == current_slug
            aria = ' aria-current="page"' if current else ""
            parts.append(f'<li><a href="{href}"{aria}>{_esc(g["title"])}</a></li>')
        parts.append("</ul></details>")
    parts.append("</nav>")
    return "\n".join(parts)

def build_guide_page(guide, by_kind, out_dir):
    text = open(guide["abs_path"], encoding="utf-8").read()
    _, body_md = parse_frontmatter(text)
    # The page header already shows the frontmatter title; drop the body's own "# Title".
    body_md = re.sub(r"\A\s*# [^\n]*\n", "", body_md)
    body_html = render_md(body_md, src=os.path.relpath(guide["abs_path"], ROOT).replace(os.sep, "/"))
    sidebar = _sidebar_html(by_kind, guide["kind"], guide["slug"], depth=2)
    header = (
        '<header class="doc-header">'
        '<a href="../../index.html">skilldrop</a>'
        '<span class="sep">·</span>'
        '<a href="../index.html">docs</a>'
        f'<span class="sep">·</span><span>{_esc(KIND_LABELS[guide["kind"]])}</span>'
        "</header>"
    )
    content = (
        f'<main class="content">'
        f'<h1>{_esc(guide["title"])}</h1>'
        f'<p class="summary">{_esc(guide["summary"])}</p>'
        f'{body_html}'
        f'</main>'
    )
    page_body = f'<div class="layout">{sidebar}{content}</div>'
    page_html = _page(f'{guide["title"]} — skilldrop docs', header, page_body)
    out_path = os.path.join(out_dir, guide["kind"], f'{guide["slug"]}.html')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    return out_path, page_html

def build_portal_index(by_kind, out_dir):
    header = (
        '<header class="doc-header">'
        '<a href="../index.html">skilldrop</a>'
        '<span class="sep">·</span><span>docs</span>'
        "</header>"
    )
    cards_html = []
    for kind in KINDS:
        guides = by_kind.get(kind, [])
        if not guides:
            continue
        label = KIND_LABELS[kind]
        tagline = KIND_TAGLINES[kind]
        cards = "".join(
            f'<div class="doc-card" data-slug="{_esc(g["slug"])}" data-kind="{_esc(g["kind"])}">'
            f'<h3>{_esc(g["title"])}</h3>'
            f'<p>{_esc(g["summary"])}</p>'
            f'<a class="read" href="{g["kind"]}/{g["slug"]}.html">Read &rarr;</a>'
            f'</div>'
            for g in guides
        )
        cards_html.append(
            f'<section class="kind-section">'
            f'<h2>{_esc(label)}</h2>'
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
        '<div class="portal-inner">'
        '<div class="portal-hero">'
        '<h1>Documentation</h1>'
        '<p>Long-form guides split by Diátaxis kind. '
        'Start with a tutorial to learn by doing, or jump straight to a how-to for a specific goal.</p>'
        '</div>'
        '<div class="search-wrap">'
        '<input id="docs-search" type="search" placeholder="Search guides…" autocomplete="off" aria-label="Search guides">'
        '</div>'
        '<p id="search-empty" style="display:none;color:var(--fg-muted);font-size:.9rem;">No guides match your search.</p>'
        + "".join(cards_html) +
        f'<p style="margin-top:2rem;font-size:.85rem;color:var(--fg-muted)">'
        f'<a href="{REPO_URL}/blob/main/llms.txt"><code>llms.txt</code></a> '
        f'&mdash; the same index in plain text, for agents to read instead of crawling the tree.</p>'
        '</div>'
        + search_js
    )
    page_html = _page("Documentation — skilldrop", header, body, depth=1)
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
    # Portal index
    idx_path, idx_html = build_portal_index(by_kind, out_dir)
    pages["index.html"] = idx_html
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

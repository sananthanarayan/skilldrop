#!/usr/bin/env python3
"""Convert a Markdown file into one self-contained, print-friendly HTML file.

Stdlib only, Python 3.9+. Local images are embedded as data URIs so the file
survives being emailed. Raw HTML in the Markdown is escaped by default, because
the output is usually shared with people who did not write the source.

Usage:
    python3 md_to_html.py input.md -o out.html
    python3 md_to_html.py input.md -o out.html --brand brand.json --toc
    python3 md_to_html.py input.md -o out.html --mermaid cdn

Supported: ATX headings (with anchor ids), paragraphs, bold, italic,
strikethrough, inline code, fenced and indented code, blockquotes, nested
ordered/unordered lists, task lists, GFM pipe tables, horizontal rules, links,
autolinks, images. Not supported: setext headings, footnotes, reference-style
links, definition lists. Those come through as plain text.
"""

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import re
import sys
from pathlib import Path

# Pinned so the rendered output never changes under the reader. Bump deliberately.
MERMAID_VERSION = "11.4.1"
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@%s/dist/mermaid.esm.min.mjs" % MERMAID_VERSION
MERMAID_INIT = ('import mermaid from "%s";'
                'mermaid.initialize({startOnLoad:true,securityLevel:"strict"});' % MERMAID_URL)
MERMAID_INIT_HASH = base64.b64encode(hashlib.sha256(MERMAID_INIT.encode("utf-8")).digest()).decode("ascii")
MAX_IMAGE_BYTES = 5 * 1024 * 1024

DEFAULT_BRAND = {
    "primary": "#1F3A5F",
    "secondary": "#4A6A8A",
    "accent": "#C8553D",
    "background": "#FFFFFF",
    "text": "#1E1E1E",
    "heading_font": "Georgia, 'Times New Roman', serif",
    "body_font": "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
}

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*([^\s`]*)[^`]*$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
LIST_RE = re.compile(r"^( *)([-*+]|\d{1,9}[.)])(?:[ \t]+(.*)|[ \t]*$)")
QUOTE_RE = re.compile(r"^ {0,3}> ?(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
HTML_BLOCK_RE = re.compile(r"^ {0,3}<(?:[A-Za-z][A-Za-z0-9-]*|/[A-Za-z]|!--)")
SAFE_URL_RE = re.compile(r"^(?:https?:|mailto:|tel:|#|/|\./|\.\./|[^:/?#]+(?:[/?#]|$))", re.I)


def esc(s):
    return html.escape(s, quote=True)


class Ctx:
    def __init__(self, base_dir, allow_html, mermaid):
        self.base_dir = base_dir
        self.allow_html = allow_html
        self.mermaid = mermaid
        self.slugs = {}
        self.headings = []  # (level, id, text-html)
        self.warnings = []
        self.counts = {"images_embedded": 0, "images_remote": 0, "images_missing": 0,
                       "mermaid": 0, "tables": 0, "code_blocks": 0, "raw_html_escaped": 0}

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)


# ---------------------------------------------------------------- inline

def safe_url(url, ctx):
    u = url.strip()
    if u.lower().startswith("data:image/"):
        return u
    if SAFE_URL_RE.match(u) and not re.match(r"^\s*(javascript|vbscript|data):", u, re.I):
        return u
    ctx.warn("dropped an unsafe link target: %s" % u[:60])
    return None


def embed_image(src, alt, title, ctx):
    t = ' title="%s"' % esc(title) if title else ""
    if re.match(r"^https?://", src, re.I):
        ctx.counts["images_remote"] += 1
        ctx.warn("remote image left as a link (it will not show offline): %s" % src)
        return '<img src="%s" alt="%s"%s>' % (esc(src), esc(alt), t)
    if src.lower().startswith("data:image/"):
        ctx.counts["images_embedded"] += 1
        return '<img src="%s" alt="%s"%s>' % (esc(src), esc(alt), t)
    path = (ctx.base_dir / src.split("#")[0].split("?")[0]).resolve()
    if not path.is_file():
        ctx.counts["images_missing"] += 1
        ctx.warn("image not found, alt text shown instead: %s" % src)
        return '<span class="missing-img">[image not found: %s]</span>' % esc(alt or src)
    data = path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        ctx.warn("large image embedded (%.1f MB), the HTML will be heavy to email: %s"
                 % (len(data) / 1048576.0, src))
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    if not mime.startswith("image/"):
        ctx.counts["images_missing"] += 1
        ctx.warn("not an image file, skipped: %s" % src)
        return '<span class="missing-img">[not an image: %s]</span>' % esc(alt or src)
    ctx.counts["images_embedded"] += 1
    b64 = base64.b64encode(data).decode("ascii")
    return '<img src="data:%s;base64,%s" alt="%s"%s>' % (mime, b64, esc(alt), t)


def emphasis(s):
    s = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w])__(?=\S)(.+?)(?<=\S)__(?![\w])", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(?=\S)(.+?)(?<=\S)\*", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w])_(?=\S)(.+?)(?<=\S)_(?![\w])", r"<em>\1</em>", s)
    s = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", s)
    return s


def inline(text, ctx):
    stash = []

    def put(fragment):
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    # code spans first: nothing inside them is Markdown
    text = re.sub(r"(`+)(.+?)(?<!`)\1(?!`)",
                  lambda m: put("<code>%s</code>" % esc(m.group(2).strip())), text)
    # backslash escapes
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>~])", lambda m: put(esc(m.group(1))), text)
    # autolinks <https://...>
    text = re.sub(r"<((?:https?://|mailto:)[^>\s]+)>",
                  lambda m: put('<a href="%s">%s</a>' % (esc(m.group(1)), esc(m.group(1)))), text)

    def img(m):
        return put(embed_image(m.group(2), m.group(1), m.group(3), ctx))

    text = re.sub(r'!\[([^\]]*)\]\(\s*<?((?:[^()\s>]|\([^()\s]*\))+)>?(?:\s+"([^"]*)")?\s*\)', img, text)

    def lnk(m):
        label = emphasis(esc(m.group(1)))
        url = safe_url(m.group(2), ctx)
        if url is None:
            return put(label)
        t = ' title="%s"' % esc(m.group(3)) if m.group(3) else ""
        return put('<a href="%s"%s>%s</a>' % (esc(url), t, label))

    text = re.sub(r'\[([^\]]+)\]\(\s*<?((?:[^()\s>]|\([^()\s]*\))+)>?(?:\s+"([^"]*)")?\s*\)', lnk, text)
    # bare URLs
    text = re.sub(r"(?<![\w\"'=/])(https?://[^\s<>\x00]+[^\s<>\x00.,;:!?)\]'\"])",
                  lambda m: put('<a href="%s">%s</a>' % (esc(m.group(1)), esc(m.group(1)))), text)
    if "<" in text and re.search(r"<[A-Za-z/!]", text):
        ctx.counts["raw_html_escaped"] += 1
    text = emphasis(esc(text))
    for _ in range(4):  # link labels can hold stashed code spans
        if "\x00" not in text:
            break
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def plain(html_text):
    return html.unescape(re.sub(r"<[^>]+>", "", html_text)).strip()


def slugify(text, ctx):
    base = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U).strip()
    base = re.sub(r"[\s_]+", "-", base).strip("-") or "section"
    n = ctx.slugs.get(base, 0)
    ctx.slugs[base] = n + 1
    return base if n == 0 else "%s-%d" % (base, n)


# ---------------------------------------------------------------- blocks

def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, in_code, i = [], "", False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if c == "`":
            in_code = not in_code
        if c == "|" and not in_code:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    cells.append(cur.strip())
    return cells


def is_block_start(line, next_line):
    return bool(FENCE_RE.match(line) or HEADING_RE.match(line) or HR_RE.match(line)
                or QUOTE_RE.match(line) or LIST_RE.match(line)
                or ("|" in line and next_line is not None and TABLE_SEP_RE.match(next_line)
                    and "-" in next_line))


def render_table(rows, aligns, ctx):
    ctx.counts["tables"] += 1
    out = ['<div class="table-wrap"><table>', "<thead><tr>"]
    width = len(aligns)

    def cell(tag, text, i):
        a = aligns[i] if i < len(aligns) else None
        style = ' style="text-align:%s"' % a if a else ""
        return "<%s%s>%s</%s>" % (tag, style, inline(text, ctx), tag)

    head = (rows[0] + [""] * width)[:width]
    out.append("".join(cell("th", c, i) for i, c in enumerate(head)))
    out.append("</tr></thead><tbody>")
    for r in rows[1:]:
        r = (r + [""] * width)[:width]
        out.append("<tr>%s</tr>" % "".join(cell("td", c, i) for i, c in enumerate(r)))
    out.append("</tbody></table></div>")
    return "".join(out)


def render_blocks(lines, ctx, tight=False):
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < n else None
        if not line.strip():
            i += 1
            continue

        m = FENCE_RE.match(line)
        if m:
            indent, fence, lang = len(m.group(1)), m.group(2), m.group(3).lower()
            body, i = [], i + 1
            closed = False
            while i < n:
                if re.match(r"^ {0,3}%s%s*\s*$" % (re.escape(fence[0]) * len(fence), re.escape(fence[0])),
                            lines[i]):
                    closed = True
                    i += 1
                    break
                body.append(lines[i][indent:] if lines[i][:indent].strip() == "" else lines[i])
                i += 1
            if not closed:
                ctx.warn("a code fence was never closed; it runs to the end of the file")
            code = "\n".join(body)
            if lang == "mermaid":
                ctx.counts["mermaid"] += 1
                out.append('<pre class="mermaid">%s</pre>' % esc(code))
            else:
                ctx.counts["code_blocks"] += 1
                cls = ' class="language-%s"' % esc(lang) if lang else ""
                out.append("<pre><code%s>%s</code></pre>" % (cls, esc(code)))
            continue

        if line.startswith("    ") or line.startswith("\t"):
            body = []
            while i < n and (lines[i].startswith("    ") or lines[i].startswith("\t") or not lines[i].strip()):
                body.append(lines[i][4:] if lines[i].startswith("    ") else lines[i][1:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            ctx.counts["code_blocks"] += 1
            out.append("<pre><code>%s</code></pre>" % esc("\n".join(body)))
            continue

        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            content = inline(m.group(2) or "", ctx)
            hid = slugify(plain(content), ctx)
            ctx.headings.append((level, hid, content))
            out.append('<h%d id="%s">%s<a class="anchor" href="#%s" aria-hidden="true">#</a></h%d>'
                       % (level, hid, content, hid, level))
            i += 1
            continue

        if HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        if "|" in line and nxt is not None and TABLE_SEP_RE.match(nxt) and "-" in nxt:
            aligns = []
            for c in split_row(nxt):
                c = c.strip()
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("center")
                elif c.endswith(":"):
                    aligns.append("right")
                elif c.startswith(":"):
                    aligns.append("left")
                else:
                    aligns.append(None)
            rows = [split_row(line)]
            i += 2
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(split_row(lines[i]))
                i += 1
            out.append(render_table(rows, aligns, ctx))
            continue

        if QUOTE_RE.match(line):
            body = []
            while i < n and lines[i].strip():
                q = QUOTE_RE.match(lines[i])
                body.append(q.group(1) if q else lines[i])
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_blocks(body, ctx))
            continue

        m = LIST_RE.match(line)
        if m:
            html_list, i = render_list(lines, i, ctx)
            out.append(html_list)
            continue

        if HTML_BLOCK_RE.match(line):
            body = []
            while i < n and lines[i].strip():
                body.append(lines[i])
                i += 1
            if ctx.allow_html:
                out.append("\n".join(body))
            else:
                ctx.counts["raw_html_escaped"] += 1
                out.append('<pre class="raw-html">%s</pre>' % esc("\n".join(body)))
            continue

        para = []
        while i < n and lines[i].strip():
            if para and is_block_start(lines[i], lines[i + 1] if i + 1 < n else None):
                break
            para.append(lines[i])
            i += 1
        text = "\n".join(p.lstrip() for p in para).rstrip()
        text = re.sub(r"(?:  +|\\)\n", "\x01", text)
        rendered = inline(text, ctx).replace("\x01", "<br>\n")
        out.append(rendered if tight else "<p>%s</p>" % rendered)
    return "\n".join(out)


def render_list(lines, i, ctx):
    first = LIST_RE.match(lines[i])
    base_indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(first.group(2)[:-1]) if ordered else 1
    items, loose = [], False
    n = len(lines)
    while i < n:
        m = LIST_RE.match(lines[i])
        if not m or len(m.group(1)) != base_indent or m.group(2)[0].isdigit() != ordered:
            break
        content_offset = len(m.group(1)) + len(m.group(2)) + 1
        body = [m.group(3) or ""]
        i += 1
        while i < n:
            ln = lines[i]
            if not ln.strip():
                # blank line: item continues only if the next non-blank line is indented
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and (len(lines[j]) - len(lines[j].lstrip(" "))) >= content_offset:
                    body.extend([""] * (j - i))
                    loose = True
                    i = j
                    continue
                break
            ind = len(ln) - len(ln.lstrip(" "))
            if ind >= content_offset:
                body.append(ln[content_offset:])
            elif ind > base_indent and LIST_RE.match(ln):
                body.append(ln[min(ind, content_offset):])
            elif LIST_RE.match(ln) or is_block_start(ln, lines[i + 1] if i + 1 < n else None):
                break
            else:
                body.append(ln.strip())  # lazy continuation
            i += 1
        items.append(body)
        # blank line between items makes the list loose
        if i < n and not lines[i].strip():
            j = i
            while j < n and not lines[j].strip():
                j += 1
            m2 = LIST_RE.match(lines[j]) if j < n else None
            if m2 and len(m2.group(1)) == base_indent and m2.group(2)[0].isdigit() == ordered:
                loose = True
                i = j
    tag = "ol" if ordered else "ul"
    attr = ' start="%d"' % start if ordered and start != 1 else ""
    parts = []
    for body in items:
        check = ""
        tm = re.match(r"^\[([ xX])\]\s+(.*)$", body[0])
        if tm:
            body = [tm.group(2)] + body[1:]
            check = '<input type="checkbox" disabled%s> ' % (" checked" if tm.group(1) != " " else "")
        parts.append("<li%s>%s%s</li>" % (' class="task"' if check else "", check,
                                           render_blocks(body, ctx, tight=not loose)))
    return "<%s%s>\n%s\n</%s>" % (tag, attr, "\n".join(parts), tag), i


# ---------------------------------------------------------------- brand + page

def css_font(s):
    return re.sub(r"[;{}<>\\]", "", s)


def load_brand(path, ctx):
    b = dict(DEFAULT_BRAND)
    b["logo"] = None
    b["footer"] = ""
    b["name"] = ""
    if not path:
        return b
    p = Path(path)
    if not p.is_file():
        sys.exit("error: brand file not found: %s" % path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit("error: brand file is not valid JSON: %s (%s)" % (path, e))
    colors = data.get("colors") or {}
    for key in ("primary", "secondary", "accent", "background", "text"):
        v = colors.get(key)
        if v:
            if HEX_RE.match(str(v)):
                b[key] = v
            else:
                ctx.warn("brand colour %s=%r is not a hex code; using the default" % (key, v))
    fonts = data.get("fonts") or {}
    for key, out_key in (("heading", "heading_font"), ("body", "body_font")):
        f = fonts.get(key) or {}
        if f.get("family"):
            fam = css_font(str(f["family"]))
            fb = css_font(str(f.get("fallback") or "sans-serif"))
            b[out_key] = "'%s', %s" % (fam.replace("'", ""), fb)
    logo = (data.get("logo") or {}).get("primary")
    if logo:
        lp = (p.parent / logo).resolve()
        if lp.is_file():
            b["logo"] = embed_image(str(lp), data.get("name") or "logo", None, ctx)
        else:
            ctx.warn("brand logo not found, header shown without it: %s" % logo)
    b["footer"] = (data.get("legal") or {}).get("footer") or ""
    b["name"] = data.get("name") or ""
    return b


CSS = """
:root{--primary:%(primary)s;--secondary:%(secondary)s;--accent:%(accent)s;--bg:%(background)s;--text:%(text)s;}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;color:var(--text);background:var(--bg);font-family:%(body_font)s;font-size:16px;line-height:1.6}
main{max-width:46rem;margin:0 auto;padding:2.5rem 1.25rem 4rem}
header.brand{display:flex;align-items:center;gap:.75rem;border-bottom:3px solid var(--primary);padding-bottom:.75rem;margin-bottom:1.5rem}
header.brand img{max-height:40px;width:auto}
h1,h2,h3,h4,h5,h6{font-family:%(heading_font)s;color:var(--primary);line-height:1.25;margin:1.8em 0 .6em}
h1{font-size:2.1rem;margin-top:0}h2{font-size:1.55rem;border-bottom:1px solid #e3e3e3;padding-bottom:.25em}h3{font-size:1.25rem}
h4,h5,h6{font-size:1.05rem}
a{color:var(--secondary)}
a.anchor{color:#bbb;text-decoration:none;margin-left:.4em;font-size:.8em;visibility:hidden}
h1:hover a.anchor,h2:hover a.anchor,h3:hover a.anchor,h4:hover a.anchor{visibility:visible}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;background:#f3f4f6;padding:.1em .3em;border-radius:3px}
pre{background:#f6f8fa;border:1px solid #e3e6ea;border-radius:6px;padding:.9rem 1rem;overflow-x:auto;line-height:1.45}
pre code{background:none;padding:0;font-size:.88em}
pre.mermaid{background:#fff;text-align:center}
pre.raw-html{border-style:dashed}
blockquote{margin:1.2em 0;padding:.4em 1em;border-left:4px solid var(--accent);color:#444;background:#fafafa}
blockquote p{margin:.4em 0}
.table-wrap{overflow-x:auto;margin:1.2em 0}
table{border-collapse:collapse;width:100%%;font-size:.95em}
th,td{border:1px solid #d9dde3;padding:.45em .7em;vertical-align:top;text-align:left}
thead th{background:var(--primary);color:#fff}
tbody tr:nth-child(even){background:#f7f8fa}
img{max-width:100%%;height:auto}
hr{border:0;border-top:1px solid #ddd;margin:2em 0}
li.task{list-style:none}li.task input{margin:0 .4em 0 -1.3em}
.missing-img{color:#a33;font-style:italic}
nav.toc{border:1px solid #e3e3e3;border-radius:6px;padding:.75rem 1.25rem;margin:1.5rem 0;background:#fbfbfb}
nav.toc p{margin:0 0 .4em;font-weight:600}
nav.toc ul{margin:0;padding-left:1.1em}nav.toc ul ul{padding-left:1.2em}
footer{margin-top:3rem;border-top:1px solid #e3e3e3;padding-top:.75rem;font-size:.85em;color:#666}
@media print{
  @page{margin:18mm 16mm}
  html,body{background:#fff}
  body{font-size:11pt}
  main{max-width:none;padding:0}
  a{color:var(--text);text-decoration:underline}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:.85em;color:#555;word-break:break-all}
  a.anchor{display:none}
  h1,h2,h3,h4{break-after:avoid;page-break-after:avoid}
  pre,blockquote,table,img,figure,nav.toc{break-inside:avoid;page-break-inside:avoid}
  pre{white-space:pre-wrap;word-break:break-word;overflow:visible}
  .table-wrap{overflow:visible}
  thead{display:table-header-group}
  thead th,tbody tr:nth-child(even),pre,code{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""


def build_toc(headings):
    items = [(lvl, hid, txt) for (lvl, hid, txt) in headings if lvl in (2, 3)]
    if not items:
        return ""
    out = ['<nav class="toc" aria-label="Contents"><p>Contents</p><ul>']
    depth = 2
    first = True
    for lvl, hid, txt in items:
        link = '<a href="#%s">%s</a>' % (hid, re.sub(r"<a [^>]*>|</a>", "", txt))
        if lvl > depth:
            out.append("<ul>")
            depth = lvl
        elif lvl < depth:
            out.append("</li></ul></li>")
            depth = lvl
        elif not first:
            out.append("</li>")
        out.append("<li>%s" % link)
        first = False
    out.append("</li>")
    if depth == 3:
        out.append("</ul></li>")
    out.append("</ul></nav>")
    return "".join(out)


def convert(src_text, base_dir, brand_path=None, toc=False, mermaid="none", allow_html=False):
    ctx = Ctx(base_dir, allow_html, mermaid)
    brand = load_brand(brand_path, ctx)
    lines = src_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # drop a leading YAML front-matter block
    if lines and lines[0].strip() == "---":
        for k in range(1, min(len(lines), 60)):
            if lines[k].strip() in ("---", "..."):
                lines = lines[k + 1:]
                break
    body = render_blocks(lines, ctx)
    title = plain(ctx.headings[0][2]) if ctx.headings else (brand["name"] or "Document")

    if toc:
        toc_html = build_toc(ctx.headings)
        if not toc_html:
            ctx.warn("--toc asked for, but the document has no level-2 or level-3 headings")
        elif body.startswith("<h1"):
            cut = body.index("</h1>") + len("</h1>")
            body = body[:cut] + "\n" + toc_html + body[cut:]
        else:
            body = toc_html + "\n" + body

    draw = mermaid == "cdn" and ctx.counts["mermaid"]
    # The page may run exactly one script, the pinned Mermaid loader, identified by its hash.
    csp_script = ("script-src 'sha256-%s' https://cdn.jsdelivr.net; " % MERMAID_INIT_HASH) if draw else ""
    csp = ("default-src 'none'; img-src data: https:; style-src 'unsafe-inline'; font-src data: https:; "
           "%sconnect-src https://cdn.jsdelivr.net" % csp_script)
    head = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="%s">' % csp,
        '<meta name="generator" content="skilldrop md-to-html">',
        "<title>%s</title>" % esc(title),
        "<style>%s</style>" % (CSS % brand),
        "</head>",
        "<body>",
        "<main>",
    ]
    if brand["logo"]:
        head.append('<header class="brand">%s</header>' % brand["logo"])
    tail = []
    if brand["footer"]:
        tail.append("<footer>%s</footer>" % esc(brand["footer"]))
    tail.append("</main>")
    if draw:
        tail.append('<script type="module">%s</script>' % MERMAID_INIT)
    elif ctx.counts["mermaid"]:
        ctx.warn("%d Mermaid diagram(s) kept as text; use --mermaid cdn to draw them "
                 "(needs network when opened), or render them to SVG with mermaid-render"
                 % ctx.counts["mermaid"])
    tail += ["</body>", "</html>", ""]
    return "\n".join(head + [body] + tail), ctx


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown to one self-contained, print-friendly HTML file.")
    ap.add_argument("input", help="Markdown file, or - for stdin")
    ap.add_argument("-o", "--output", required=True, help="HTML file to write")
    ap.add_argument("--brand", help="brand.json (brand-kit shape): colours, fonts, logo, footer")
    ap.add_argument("--toc", action="store_true", help="add a table of contents from level-2 and level-3 headings")
    ap.add_argument("--mermaid", choices=("none", "cdn"), default="none",
                    help="none (default): keep diagrams as text. cdn: draw them with mermaid %s "
                         "from jsDelivr, which needs network when the file is opened" % MERMAID_VERSION)
    ap.add_argument("--allow-html", action="store_true",
                    help="pass raw HTML blocks through instead of escaping them (only for your own trusted source)")
    a = ap.parse_args(argv)

    if a.input == "-":
        text, base = sys.stdin.read(), Path.cwd()
    else:
        p = Path(a.input)
        if not p.is_file():
            sys.exit("error: input not found: %s" % a.input)
        try:
            text = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            sys.exit("error: %s is not UTF-8 text; is it really Markdown?" % a.input)
        base = p.resolve().parent
    if not text.strip():
        sys.exit("error: input is empty")

    out_html, ctx = convert(text, base, a.brand, a.toc, a.mermaid, a.allow_html)
    out = Path(a.output)
    if out.parent and not out.parent.exists():
        sys.exit("error: output folder does not exist: %s" % out.parent)
    out.write_text(out_html, encoding="utf-8")

    c = ctx.counts
    print("wrote %s (%d KB): %d headings, %d tables, %d code blocks, %d Mermaid, "
          "%d images embedded, %d remote, %d missing"
          % (out, len(out_html.encode("utf-8")) // 1024, len(ctx.headings), c["tables"], c["code_blocks"],
             c["mermaid"], c["images_embedded"], c["images_remote"], c["images_missing"]))
    if c["raw_html_escaped"] and not a.allow_html:
        ctx.warn("raw HTML found and shown as text (%d place(s)); this is deliberate, see --allow-html"
                 % c["raw_html_escaped"])
    for w in ctx.warnings:
        print("warning: %s" % w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Convert Markdown to Confluence storage format (XHTML), and optionally publish it.

Stdlib only, Python 3.9+.

Convert (no network):
    python3 md_to_confluence.py runbook.md -o runbook.xhtml [--toc] [--keep-h1] [--title "..."]

Check the target page before writing (read-only GET):
    ... --inspect --base-url https://<site>.atlassian.net/wiki --space SRE [--page-id N | --title "..."]

Publish (create, or update with --page-id):
    ... --publish --base-url https://<site>.atlassian.net/wiki --space SRE --title "..."
        [--parent-id N] [--page-id N --expected-version V] [--dry-run]

Credentials come from the environment only: CONFLUENCE_EMAIL + CONFLUENCE_API_TOKEN
(Cloud, basic auth) or CONFLUENCE_PAT (Data Center, bearer). Never from arguments or files.

Supported: ATX and setext headings, paragraphs, bold, italic, strikethrough, inline code,
links (inline, reference-style, autolinks, bare URLs), nested ordered/unordered lists, task
lists (ac:task-list), GFM pipe tables with a header row, blockquotes, callouts
(> **Note:** / > **Warning:** / > [!NOTE] ...) as info/tip/note/warning macros, fenced and
indented code as the code macro, images as page attachments, horizontal rules, and an
optional table-of-contents macro. Dropped with a WARN line: raw HTML blocks, inline HTML
tags (text kept), footnotes, in-page #anchor links (text kept), data: images, YAML front
matter (its title: is used).

Exit codes: 0 done; 1 error; 2 refused for safety (nothing was written to Confluence).
"""

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*([^\s`]*)[^`]*$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
LIST_RE = re.compile(r"^( *)([-*+]|\d{1,9}[.)])(?:[ \t]+(.*)|[ \t]*$)")
QUOTE_RE = re.compile(r"^ {0,3}> ?(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
HTML_BLOCK_RE = re.compile(r"^ {0,3}<(?:[A-Za-z][A-Za-z0-9-]*|/[A-Za-z]|!--)")
FOOTNOTE_DEF_RE = re.compile(r"^ {0,3}\[\^[^\]]+\]:")
REF_DEF_RE = re.compile(r"""^ {0,3}\[([^\]^][^\]]*)\]:\s*<?(\S+?)>?(?:\s+["'(](.*)["')])?\s*$""")
INLINE_TAG_RE = re.compile(r"<!--.*?-->|</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>", re.S)
CALLOUT_RE = re.compile(
    r"^\s*(?:\*\*(note|info|tip|important|warning|caution)\s*:\s*\*\*|"
    r"\*\*(note|info|tip|important|warning|caution)\*\*\s*:|"
    r"\[!(note|tip|important|warning|caution)\])\s*", re.I)
# Markdown label -> Confluence macro. Confluence's own "note" macro is the yellow one.
CALLOUT_MACRO = {"note": "info", "info": "info", "tip": "tip", "important": "note",
                 "warning": "warning", "caution": "warning"}
# Languages the code macro highlights on both Cloud and Data Center, plus common aliases.
CODE_LANGS = {"actionscript3", "applescript", "bash", "c#", "cpp", "css", "coldfusion", "delphi",
              "diff", "erl", "groovy", "xml", "java", "javafx", "js", "php", "perl", "text",
              "powershell", "py", "ruby", "sql", "sass", "scala", "vb", "yml", "go", "json",
              "kotlin", "typescript"}
CODE_ALIASES = {"python": "py", "python3": "py", "javascript": "js", "node": "js", "sh": "bash",
                "shell": "bash", "zsh": "bash", "console": "bash", "yaml": "yml", "html": "xml",
                "xhtml": "xml", "csharp": "c#", "cs": "c#", "c++": "cpp", "c": "cpp", "ts": "typescript",
                "ps1": "powershell", "pwsh": "powershell", "rb": "ruby", "erlang": "erl", "golang": "go",
                "kt": "kotlin", "patch": "diff", "plaintext": "text", "txt": "text", "jsonc": "json"}
XML_BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff\ue000\ue001]")
STASH_OPEN, STASH_CLOSE = "\ue000", "\ue001"
ENTITY_RE = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")


class L(str):
    """A source line that remembers its line number through slicing in nested blocks."""

    def __new__(cls, s, ln):
        o = str.__new__(cls, s)
        o.ln = ln
        return o


def sub(line, text):
    return L(text, getattr(line, "ln", 0))


def esc(s):
    return html.escape(s, quote=True)


def cdata(text):
    # "]]>" cannot appear inside CDATA: close the section after "]]" and reopen it before ">".
    return "<![CDATA[%s]]>" % text.replace("]]>", "]]]]><![CDATA[>")


class Ctx:
    def __init__(self, base_dir, refs):
        self.base_dir = base_dir
        self.refs = refs
        self.line = 0
        self.headings = []  # (level, plain text)
        self.attachments = {}  # filename -> {"src", "path", "found"}
        self.task_id = 0
        self.warnings = []
        self.counts = {"tables": 0, "code": 0, "callouts": 0, "task_lists": 0, "images_remote": 0}

    def warn(self, msg, line=None):
        where = line if line is not None else self.line
        text = ("line %d: %s" % (where, msg)) if where else msg
        if text not in self.warnings:
            self.warnings.append(text)


# ---------------------------------------------------------------- inline

def emphasis(s):
    s = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w])__(?=\S)(.+?)(?<=\S)__(?![\w])", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(?=\S)(.+?)(?<=\S)\*", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w])_(?=\S)(.+?)(?<=\S)_(?![\w])", r"<em>\1</em>", s)
    s = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r'<span style="text-decoration: line-through;">\1</span>', s)
    return s


def image(src, alt, title, ctx):
    attrs = (' ac:alt="%s"' % esc(alt)) if alt else ""
    if title:
        attrs += ' ac:title="%s"' % esc(title)
    if re.match(r"^https?://", src, re.I):
        ctx.counts["images_remote"] += 1
        ctx.warn("remote image shown from its URL, not attached (it breaks if that site moves or "
                 "needs a login): %s" % src[:80])
        return '<ac:image%s><ri:url ri:value="%s" /></ac:image>' % (attrs, esc(src))
    if re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
        ctx.warn("image with a %s URL dropped, alt text kept" % src.split(":", 1)[0])
        return esc(alt)
    rel = urllib.parse.unquote(src.split("#")[0].split("?")[0])
    path = (ctx.base_dir / rel).resolve()
    name = path.name
    seen = ctx.attachments.get(name)
    if seen and seen["path"] != str(path):
        ctx.warn("two different images are both named %s (%s and %s); attachments are matched by "
                 "file name, so both would show the same picture. Rename one" % (name, seen["src"], src))
    elif not seen:
        ctx.attachments[name] = {"src": src, "path": str(path), "found": path.is_file()}
        if not path.is_file():
            ctx.warn("image not found next to the Markdown: %s" % src)
    return '<ac:image%s><ri:attachment ri:filename="%s" /></ac:image>' % (attrs, esc(name))


def link(label_html, url, title, ctx):
    u = url.strip()
    if u.startswith("#"):
        ctx.warn("in-page link to %s kept as plain text (Confluence heading anchors are named "
                 "differently); the table of contents covers navigation" % u[:40])
        return label_html
    if re.match(r"^\s*(javascript|vbscript|data|file):", u, re.I):
        ctx.warn("unsafe link target dropped, text kept: %s" % u[:60])
        return label_html
    t = (' title="%s"' % esc(title)) if title else ""
    return '<a href="%s"%s>%s</a>' % (esc(u), t, label_html)


def inline(text, ctx):
    stash = []

    def put(fragment):
        stash.append(fragment)
        return "%s%d%s" % (STASH_OPEN, len(stash) - 1, STASH_CLOSE)

    text = re.sub(r"(`+)(.+?)(?<!`)\1(?!`)", lambda m: put("<code>%s</code>" % esc(m.group(2).strip())), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>~])", lambda m: put(esc(m.group(1))), text)

    def footnote(m):
        ctx.warn("footnote reference %s dropped (footnotes are not supported)" % m.group(0))
        return ""

    text = re.sub(r"\[\^[^\]]+\]", footnote, text)
    text = re.sub(r"<((?:https?://|mailto:)[^>\s]+)>",
                  lambda m: put('<a href="%s">%s</a>' % (esc(m.group(1)), esc(m.group(1)))), text)
    text = re.sub(r'!\[([^\]]*)\]\(\s*<?((?:[^()\s>]|\([^()\s]*\))+)>?(?:\s+"([^"]*)")?\s*\)',
                  lambda m: put(image(m.group(2), m.group(1), m.group(3), ctx)), text)
    text = re.sub(r'\[([^\]]+)\]\(\s*<?((?:[^()\s>]|\([^()\s]*\))+)>?(?:\s+"([^"]*)")?\s*\)',
                  lambda m: put(link(emphasis(esc(m.group(1))), m.group(2), m.group(3), ctx)), text)

    def ref_link(m):
        key = (m.group(2) or m.group(1)).strip().lower()
        if key not in ctx.refs:
            return m.group(0)
        url, title = ctx.refs[key]
        return put(link(emphasis(esc(m.group(1))), url, title, ctx))

    text = re.sub(r"\[([^\]]+)\]\[([^\]]*)\]", ref_link, text)
    text = re.sub(r"(?<![\w\"'=/])(https?://[^\s<>%s]+[^\s<>%s.,;:!?)\]'\"])" % (STASH_OPEN, STASH_OPEN),
                  lambda m: put('<a href="%s">%s</a>' % (esc(m.group(1)), esc(m.group(1)))), text)

    def tag(m):
        t = m.group(0)
        if re.match(r"^<br\s*/?>$", t, re.I):
            return put("<br />")
        ctx.warn("inline HTML %s removed, text kept" % t[:30])
        return ""

    text = INLINE_TAG_RE.sub(tag, text)
    # Decode character references (&amp; &mdash; &#8212;) outside the stashed pieces, then escape
    # everything once. Only semicolon-terminated ones, so "?a=1&para=2" stays as typed.
    parts = re.split("(%s\\d+%s)" % (STASH_OPEN, STASH_CLOSE), text)
    text = "".join(pt if k % 2 else XML_BAD.sub("", ENTITY_RE.sub(lambda m: html.unescape(m.group(0)), pt))
                   for k, pt in enumerate(parts))
    text = emphasis(esc(text))
    pat = re.compile("%s(\\d+)%s" % (STASH_OPEN, STASH_CLOSE))
    for _ in range(4):  # link labels can hold stashed code spans
        if STASH_OPEN not in text:
            break
        text = pat.sub(lambda m: stash[int(m.group(1))], text)
    return text


def plain(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


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


def is_table_start(line, nxt):
    return "|" in line and nxt is not None and bool(TABLE_SEP_RE.match(nxt)) and "-" in nxt


def is_block_start(line, nxt):
    return bool(FENCE_RE.match(line) or HEADING_RE.match(line) or HR_RE.match(line)
                or QUOTE_RE.match(line) or LIST_RE.match(line) or is_table_start(line, nxt))


def code_macro(code, lang, ctx):
    ctx.counts["code"] += 1
    lang = (lang or "").lower()
    params = ""
    if lang == "mermaid":
        ctx.warn("Mermaid diagram kept as a code block; Confluence draws it only with a diagram "
                 "app, or embed a rendered image instead")
    elif lang:
        mapped = CODE_ALIASES.get(lang, lang)
        if mapped in CODE_LANGS:
            params = '<ac:parameter ac:name="language">%s</ac:parameter>' % esc(mapped)
        else:
            ctx.warn("code language '%s' has no Confluence highlighter; shown without highlighting" % lang)
    return ('<ac:structured-macro ac:name="code" ac:schema-version="1">%s'
            "<ac:plain-text-body>%s</ac:plain-text-body></ac:structured-macro>" % (params, cdata(code)))


def render_table(rows, aligns, ctx):
    ctx.counts["tables"] += 1
    width = len(aligns)

    def cell(tag, text, i):
        a = aligns[i] if i < len(aligns) else None
        body = inline(text, ctx)
        if a:
            body = '<p style="text-align: %s;">%s</p>' % (a, body)
        return "<%s>%s</%s>" % (tag, body, tag)

    out = ["<table><tbody>"]
    for r_i, r in enumerate(rows):
        if len(r) != width:
            ctx.warn("table row %d has %d cells, the header has %d; padded or cut" % (r_i, len(r), width))
        r = (r + [""] * width)[:width]
        tag = "th" if r_i == 0 else "td"
        out.append("<tr>%s</tr>" % "".join(cell(tag, c, i) for i, c in enumerate(r)))
    out.append("</tbody></table>")
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
        ctx.line = getattr(line, "ln", 0)

        m = FENCE_RE.match(line)
        if m:
            indent, fence, lang = len(m.group(1)), m.group(2), m.group(3)
            body, i, closed = [], i + 1, False
            close_re = re.compile(r"^ {0,3}%s+\s*$" % (re.escape(fence[0]) * len(fence)))
            while i < n:
                if close_re.match(lines[i]):
                    closed, i = True, i + 1
                    break
                body.append(lines[i][indent:] if lines[i][:indent].strip() == "" else lines[i])
                i += 1
            if not closed:
                ctx.warn("a code fence was never closed; it runs to the end of the file")
            out.append(code_macro("\n".join(body), lang, ctx))
            continue

        if line.startswith("    ") or line.startswith("\t"):
            body = []
            while i < n and (lines[i].startswith("    ") or lines[i].startswith("\t") or not lines[i].strip()):
                body.append(lines[i][4:] if lines[i].startswith("    ") else lines[i][1:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            out.append(code_macro("\n".join(body), "", ctx))
            continue

        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            content = inline(m.group(2) or "", ctx)
            ctx.headings.append((level, plain(content)))
            out.append("<h%d>%s</h%d>" % (level, content, level))
            i += 1
            continue

        if HR_RE.match(line):
            out.append("<hr />")
            i += 1
            continue

        if is_table_start(line, nxt):
            aligns = []
            for c in split_row(nxt):
                c = c.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":") else
                              "right" if c.endswith(":") else "left" if c.startswith(":") else None)
            rows = [split_row(line)]
            i += 2
            while i < n and lines[i].strip() and "|" in lines[i]:
                ctx.line = getattr(lines[i], "ln", 0)
                rows.append(split_row(lines[i]))
                i += 1
            out.append(render_table(rows, aligns, ctx))
            continue

        if QUOTE_RE.match(line):
            body = []
            while i < n and lines[i].strip():
                q = QUOTE_RE.match(lines[i])
                body.append(sub(lines[i], q.group(1) if q else lines[i]))
                i += 1
            cm = CALLOUT_RE.match(body[0]) if body else None
            if cm:
                kind = (cm.group(1) or cm.group(2) or cm.group(3)).lower()
                body[0] = sub(body[0], body[0][cm.end():])
                ctx.counts["callouts"] += 1
                out.append('<ac:structured-macro ac:name="%s" ac:schema-version="1"><ac:rich-text-body>%s'
                           "</ac:rich-text-body></ac:structured-macro>"
                           % (CALLOUT_MACRO[kind], render_blocks(body, ctx)))
            else:
                out.append("<blockquote>%s</blockquote>" % render_blocks(body, ctx))
            continue

        if LIST_RE.match(line):
            html_list, i = render_list(lines, i, ctx)
            out.append(html_list)
            continue

        if FOOTNOTE_DEF_RE.match(line):
            start = ctx.line
            i += 1
            while i < n and lines[i].strip() and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                i += 1
            ctx.warn("footnote definition dropped (footnotes are not supported)", start)
            continue

        if HTML_BLOCK_RE.match(line):
            start = ctx.line
            body = []
            while i < n and lines[i].strip():
                body.append(lines[i])
                i += 1
            end = getattr(body[-1], "ln", start)
            if re.match(r"^\s*<!--.*-->\s*$", "\n".join(body), re.S):
                ctx.warn("HTML comment dropped", start)
            else:
                ctx.warn("raw HTML block dropped%s; rewrite it as Markdown to keep it"
                         % ((" (lines %d-%d)" % (start, end)) if end > start else ""), start)
            continue

        para = []
        while i < n and lines[i].strip():
            if para and SETEXT_RE.match(lines[i]):
                break
            if para and (is_block_start(lines[i], lines[i + 1] if i + 1 < n else None)
                         or FOOTNOTE_DEF_RE.match(lines[i]) or HTML_BLOCK_RE.match(lines[i])):
                break
            para.append(lines[i])
            i += 1
        text = "\n".join(p.lstrip() for p in para).rstrip()
        if i < n and para and SETEXT_RE.match(lines[i]):
            level = 1 if lines[i].strip().startswith("=") else 2
            content = inline(text.replace("\n", " "), ctx)
            ctx.headings.append((level, plain(content)))
            out.append("<h%d>%s</h%d>" % (level, content, level))
            i += 1
            continue
        text = re.sub(r"(?:  +|\\)\n", "\x01", text)
        rendered = inline(text, ctx).replace("\x01", "<br />")
        out.append(rendered if tight else "<p>%s</p>" % rendered)
    return "".join(out)


def render_list(lines, i, ctx):
    first = LIST_RE.match(lines[i])
    base_indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(first.group(2)[:-1]) if ordered else 1
    if ordered and start != 1:
        ctx.warn("numbered list starts at %d but Confluence restarts it at 1; indent the code block or "
                 "text that split the list under the previous item so it stays one list" % start)
    items, loose, n = [], False, len(lines)
    while i < n:
        m = LIST_RE.match(lines[i])
        if not m or len(m.group(1)) != base_indent or m.group(2)[0].isdigit() != ordered:
            break
        content_offset = len(m.group(1)) + len(m.group(2)) + 1
        body = [sub(lines[i], m.group(3) or "")]
        i += 1
        while i < n:
            ln = lines[i]
            if not ln.strip():
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and (len(lines[j]) - len(lines[j].lstrip(" "))) >= content_offset:
                    body.extend([sub(ln, "")] * (j - i))
                    loose, i = True, j
                    continue
                break
            ind = len(ln) - len(ln.lstrip(" "))
            if ind >= content_offset:
                body.append(sub(ln, ln[content_offset:]))
            elif ind > base_indent and LIST_RE.match(ln):
                body.append(sub(ln, ln[min(ind, content_offset):]))
            elif LIST_RE.match(ln) or is_block_start(ln, lines[i + 1] if i + 1 < n else None):
                break
            else:
                body.append(sub(ln, ln.strip()))  # lazy continuation
            i += 1
        items.append(body)
        if i < n and not lines[i].strip():
            j = i
            while j < n and not lines[j].strip():
                j += 1
            m2 = LIST_RE.match(lines[j]) if j < n else None
            if m2 and len(m2.group(1)) == base_indent and m2.group(2)[0].isdigit() == ordered:
                loose, i = True, j

    tasks = [re.match(r"^\[([ xX])\]\s+(.*)$", b[0]) for b in items]
    if all(tasks) and not ordered:
        ctx.counts["task_lists"] += 1
        parts = []
        for tm, body in zip(tasks, items):
            ctx.task_id += 1
            content = render_blocks([sub(body[0], tm.group(2))] + body[1:], ctx, tight=True)
            parts.append("<ac:task><ac:task-id>%d</ac:task-id><ac:task-status>%s</ac:task-status>"
                         "<ac:task-body>%s</ac:task-body></ac:task>"
                         % (ctx.task_id, "incomplete" if tm.group(1) == " " else "complete", content))
        return "<ac:task-list>%s</ac:task-list>" % "".join(parts), i
    if any(tasks):
        ctx.warn("list mixes checkboxes with plain items; checkboxes written as text boxes, not "
                 "Confluence tasks. Put the tasks in a list of their own")
    tag = "ol" if ordered else "ul"
    parts = []
    for tm, body in zip(tasks, items):
        if tm:
            body = [sub(body[0], ("\u2611 " if tm.group(1) != " " else "\u2610 ") + tm.group(2))] + body[1:]
        parts.append("<li>%s</li>" % render_blocks(body, ctx, tight=not loose))
    return "<%s>%s</%s>" % (tag, "".join(parts), tag), i


# ---------------------------------------------------------------- document

def check_well_formed(body):
    doc = ('<root xmlns:ac="http://atlassian.com/content" '
           'xmlns:ri="http://atlassian.com/resource/identifier">%s</root>' % body)
    ET.fromstring(doc)


def convert(src, base_dir, toc=False, keep_h1=False, title=None):
    text = XML_BAD.sub("", src.replace("\r\n", "\n").replace("\r", "\n"))
    raw = text.split("\n")
    offset, fm_title = 0, None
    if raw and raw[0].strip() == "---":
        for k in range(1, min(len(raw), 60)):
            if raw[k].strip() in ("---", "..."):
                for fl in raw[1:k]:
                    tm = re.match(r"^title:\s*(.+?)\s*$", fl)
                    if tm:
                        fm_title = tm.group(1).strip("\"'")
                offset = k + 1
                break
    refs, lines = {}, []
    for idx, s in enumerate(raw[offset:], start=offset + 1):
        rm = REF_DEF_RE.match(s)
        if rm and not s.lstrip().startswith("[^"):
            refs[rm.group(1).strip().lower()] = (rm.group(2), rm.group(3))
            continue
        lines.append(L(s, idx))
    ctx = Ctx(base_dir, refs)
    if offset:
        ctx.warn("YAML front matter dropped (lines 1-%d)%s" % (offset, "; its title: is used" if fm_title else ""), 0)
    body = render_blocks(lines, ctx)

    first_h1 = ctx.headings[0][1] if ctx.headings and ctx.headings[0][0] == 1 and body.startswith("<h1>") else None
    page_title = title or fm_title or first_h1
    notes = []
    if first_h1 and not keep_h1:
        if first_h1 == page_title:
            body = body[body.index("</h1>") + len("</h1>"):]
            notes.append("the first heading became the page title and was removed from the body "
                         "(Confluence shows the title above the page); --keep-h1 keeps it")
        else:
            notes.append("the first heading (%s) differs from the page title (%s); kept in the body"
                         % (first_h1, page_title))
    if toc:
        body = '<ac:structured-macro ac:name="toc" ac:schema-version="1" />' + body
        if len([h for h in ctx.headings if h[0] >= 2]) < 2:
            notes.append("--toc added, but the page has fewer than two section headings")
    check_well_formed(body)
    return body, page_title, ctx, notes


# ---------------------------------------------------------------- publish

class Refused(Exception):
    """A safety refusal: nothing was written to Confluence."""


class PublishError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # Following a redirect would resend the Authorization header to wherever it points.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublishError("Confluence answered with a redirect to %s; not following it with your "
                           "credentials. Check --base-url" % newurl)


OPENER = urllib.request.build_opener(NoRedirect)

HINTS = {401: "credentials rejected: check the email and API token, or the PAT",
         403: "these credentials may not view or edit this page or space",
         404: "no such page or space, or these credentials cannot see it",
         409: "version conflict: someone saved the page meanwhile; inspect it again"}


def normalize_base(url):
    p = urllib.parse.urlsplit((url or "").strip())
    if p.scheme.lower() != "https":
        raise Refused("refusing a non-https base URL (%s): the credentials would travel in clear text"
                      % (url or "none given"))
    if p.username or p.password:
        raise Refused("the base URL must not contain a user name or password; credentials come "
                      "from the environment")
    if not p.hostname or p.query or p.fragment:
        raise Refused("base URL should look like https://<site>.atlassian.net/wiki")
    path = p.path.rstrip("/")
    host = p.hostname.lower()
    if host.endswith(".atlassian.net") and not path.startswith("/wiki"):
        path = "/wiki" + path
    return urllib.parse.urlunsplit(("https", p.netloc, path, "", "")), host


def credentials(host):
    """Return (Authorization header value or None, description safe to print)."""
    email = os.environ.get("CONFLUENCE_EMAIL")
    token = os.environ.get("CONFLUENCE_API_TOKEN")
    pat = os.environ.get("CONFLUENCE_PAT")
    if email and token and (host.endswith(".atlassian.net") or not pat):
        basic = base64.b64encode(("%s:%s" % (email, token)).encode("utf-8")).decode("ascii")
        return "Basic " + basic, "basic auth from CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN"
    if pat:
        return "Bearer " + pat, "bearer token from CONFLUENCE_PAT"
    return None, ("none found: set CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN (Cloud) or "
                  "CONFLUENCE_PAT (Data Center) in the environment")


def call(method, url, auth, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", auth)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with OPENER.open(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode("utf-8", "replace")).get("message", "")
        except (ValueError, AttributeError):
            pass
        raise PublishError("%s %s failed: HTTP %d%s%s" % (method, url, e.code,
                           (" (%s)" % HINTS[e.code]) if e.code in HINTS else "",
                           (": %s" % detail[:300]) if detail else ""))
    except urllib.error.URLError as e:
        raise PublishError("could not reach %s: %s" % (url, e.reason))
    except ValueError:
        raise PublishError("%s %s answered with something that is not JSON; is --base-url the "
                           "Confluence address?" % (method, url))


def page_line(p, base):
    v = p.get("version") or {}
    by = (v.get("by") or {}).get("displayName")
    web = ((p.get("_links") or {}).get("webui")) or ""
    return ('id %s, "%s" in space %s, version %s%s%s%s'
            % (p.get("id"), p.get("title"), (p.get("space") or {}).get("key", "?"), v.get("number", "?"),
               (", last edited by %s" % by) if by else "", (" on %s" % v["when"]) if v.get("when") else "",
               (", %s%s" % (base, web)) if web else ""))


def find_by_title(api, auth, space, title):
    q = urllib.parse.urlencode({"spaceKey": space, "title": title, "type": "page", "expand": "version,space"})
    return (call("GET", "%s?%s" % (api, q), auth).get("results") or [])


def publish(a, body, title, base, host):
    api = base + "/rest/api/content"
    auth, auth_desc = credentials(host)
    storage = {"storage": {"value": body, "representation": "storage"}}
    update = a.page_id is not None

    if a.dry_run:
        print("dry run: nothing was sent")
        print("  %s %s" % ("PUT" if update else "POST", "%s/%s" % (api, a.page_id) if update else api))
        shown = (a.title or "(kept from the page)") if update else title
        print('  space %s, title "%s", parent %s' % (a.space, shown,
                                                     a.parent_id or ("unchanged" if update else "the space home page")))
        print("  body: %d bytes of storage format" % len(body.encode("utf-8")))
        if update:
            print("  version: read from the page at publish time and sent as current + 1%s"
                  % ("; refused if the page is not at version %d" % a.expected_version
                     if a.expected_version is not None else "; no --expected-version, so any newer edit is overwritten"))
        else:
            print("  first checks space %s for a page with this title and stops if one exists" % a.space)
        print("  auth: %s" % auth_desc)
        return
    if not auth:
        raise Refused("no Confluence credentials: " + auth_desc.split(": ", 1)[1])

    if a.inspect:
        if update:
            p = call("GET", "%s/%s?expand=version,space" % (api, a.page_id), auth)
            print("would overwrite: " + page_line(p, base))
            print("to publish over exactly this version, add --expected-version %s" % (p.get("version") or {}).get("number"))
        else:
            found = find_by_title(api, auth, a.space, title)
            if found:
                print("a page with this title already exists: " + page_line(found[0], base))
                print("publishing without --page-id will refuse; to replace it, use --page-id %s" % found[0].get("id"))
            else:
                print('no page titled "%s" in space %s: publishing creates a new page' % (title, a.space))
        if a.parent_id:
            par = call("GET", "%s/%s?expand=space" % (api, a.parent_id), auth)
            print("parent: " + page_line(par, base))
        return

    if update:
        cur = call("GET", "%s/%s?expand=version,space" % (api, a.page_id), auth)
        cur_space = (cur.get("space") or {}).get("key")
        n = (cur.get("version") or {}).get("number")
        if cur_space and cur_space != a.space:
            raise Refused("page %s is in space %s, not %s; nothing was changed" % (a.page_id, cur_space, a.space))
        if not isinstance(n, int):
            raise PublishError("could not read the current version of page %s" % a.page_id)
        if a.expected_version is not None and n != a.expected_version:
            raise Refused("page %s is at version %d, but --expected-version is %d%s; nothing was changed. "
                          "Inspect it again and confirm before overwriting"
                          % (a.page_id, n, a.expected_version,
                             " (someone edited it since you checked)" if n > a.expected_version else ""))
        keep = cur.get("title")
        if not a.title and title and keep and title != keep:
            print('note: kept the page\'s current title "%s"; the Markdown says "%s". Pass --title to rename it'
                  % (keep, title))
        payload = {"id": str(a.page_id), "type": "page", "title": a.title or keep or title,
                   "space": {"key": cur_space or a.space}, "version": {"number": n + 1}, "body": storage}
        if a.parent_id:
            payload["ancestors"] = [{"id": str(a.parent_id)}]
        res = call("PUT", "%s/%s" % (api, a.page_id), auth, payload)
        print("updated page: version %d -> %s; %s" % (n, (res.get("version") or {}).get("number", n + 1), page_line(res, base)))
    else:
        found = find_by_title(api, auth, a.space, title)
        if found:
            raise Refused("a page titled \"%s\" already exists in %s (%s). Nothing was created. To replace "
                          "it, inspect it and rerun with --page-id %s" % (title, a.space, page_line(found[0], base),
                                                                          found[0].get("id")))
        payload = {"type": "page", "title": title, "space": {"key": a.space}, "body": storage}
        if a.parent_id:
            payload["ancestors"] = [{"id": str(a.parent_id)}]
        res = call("POST", api, auth, payload)
        print("created page: " + page_line(res, base))


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown to Confluence storage format, with an optional publish.")
    ap.add_argument("input", help="Markdown file, or - for stdin")
    ap.add_argument("-o", "--output", required=True, help="storage-format file to write (.xhtml)")
    ap.add_argument("--toc", action="store_true", help="put a table-of-contents macro at the top")
    ap.add_argument("--keep-h1", action="store_true", help="keep the first # heading in the body even when it is the page title")
    ap.add_argument("--title", help="page title (default: front matter title:, else the first # heading)")
    g = ap.add_argument_group("Confluence (credentials from the environment only)")
    g.add_argument("--publish", action="store_true", help="create the page, or update it with --page-id")
    g.add_argument("--inspect", action="store_true", help="read-only: show the page that publishing would create or overwrite")
    g.add_argument("--dry-run", action="store_true", help="with --publish: print the request and send nothing")
    g.add_argument("--base-url", help="https://<site>.atlassian.net/wiki, or the Data Center address")
    g.add_argument("--space", help="space key, e.g. SRE")
    g.add_argument("--parent-id", type=int, help="create the page under this page")
    g.add_argument("--page-id", type=int, help="update this page instead of creating one")
    g.add_argument("--expected-version", type=int, help="with --page-id: refuse unless the page is at exactly this version")
    a = ap.parse_args(argv)

    if a.input == "-":
        src, base_dir = sys.stdin.read(), Path.cwd()
    else:
        p = Path(a.input)
        if not p.is_file():
            sys.exit("error: input not found: %s" % a.input)
        try:
            with open(p, encoding="utf-8-sig") as f:
                src = f.read()
        except UnicodeDecodeError:
            sys.exit("error: %s is not UTF-8 text; is it really Markdown?" % a.input)
        base_dir = p.resolve().parent
    if not src.strip():
        sys.exit("error: input is empty")
    online = a.publish or a.inspect
    if a.dry_run and not a.publish:
        sys.exit("error: --dry-run goes with --publish")
    if a.publish and a.inspect:
        sys.exit("error: choose --inspect (read-only) or --publish, not both")
    if online and not (a.base_url and a.space):
        sys.exit("error: --publish and --inspect need --base-url and --space")
    if a.expected_version is not None and a.page_id is None:
        sys.exit("error: --expected-version goes with --page-id")

    try:
        body, title, ctx, notes = convert(src, base_dir, a.toc, a.keep_h1, a.title)
    except ET.ParseError as e:
        sys.exit("error: internal: the storage format came out malformed (%s); please report it" % e)
    if online and not title and a.page_id is None:
        sys.exit("error: no page title: pass --title, or start the Markdown with a # heading")

    out = Path(a.output)
    if not out.resolve().parent.is_dir():
        sys.exit("error: output folder does not exist: %s" % out.parent)
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)

    c = ctx.counts
    print('wrote %s (%d KB storage format): title "%s"; %d headings, %d tables, %d code blocks, '
          "%d callouts, %d task lists, %d images to attach, %d remote images"
          % (out, (len(body.encode("utf-8")) + 1023) // 1024, title or "(none)", len(ctx.headings), c["tables"],
             c["code"], c["callouts"], c["task_lists"], len(ctx.attachments), c["images_remote"]))
    for note in notes:
        print("note: " + note)
    if ctx.attachments:
        print("upload these files to the page as attachments, with exactly these names, or the images show as broken:")
        for name, info in ctx.attachments.items():
            print("  %s  (from %s)%s" % (name, info["src"], "" if info["found"] else "  NOT FOUND"))
    for w in ctx.warnings:
        print("WARN %s" % w, file=sys.stderr)
    if ctx.warnings:
        print("%d warning(s): the items above were dropped or changed; tell the reader before publishing"
              % len(ctx.warnings), file=sys.stderr)

    if not online:
        return 0
    try:
        base, host = normalize_base(a.base_url)
        publish(a, body, title, base, host)
    except Refused as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2
    except PublishError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

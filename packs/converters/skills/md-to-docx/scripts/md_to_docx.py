#!/usr/bin/env python3
"""Convert a Markdown file to a Word document (.docx). Stdlib only: zip + XML by hand.

Supported: ATX and setext headings (h1-h4 map to Word's built-in Heading 1-4 styles, so the
navigation pane and a table of contents work; h5/h6 become Heading 4 with a warning),
paragraphs, **bold**, *italic*, ~~strike~~, `code`, links (real hyperlinks; #anchors jump to
headings), bullet and numbered lists with one nesting level, task-list boxes, pipe tables with a
header row and column alignment, fenced and indented code blocks, blockquotes, horizontal rules,
hard line breaks, and local PNG/JPEG images embedded at their real size (shrunk to fit the page).

Dropped, with a warning on stderr naming the line: raw HTML (tags removed, text kept), footnotes,
images that are remote, missing or not PNG/JPEG, list nesting deeper than one level (flattened),
YAML front matter (its title: is used for the document title).

Usage:
  python3 md_to_docx.py input.md -o out.docx [--brand brand.json] [--title "..."]
                        [--page letter|a4] [--hr rule|page-break]

--brand reads a brand-kit brand.json: fonts.heading.family, fonts.body.family, colors.primary
(heading colour) and colors.text (body colour). Every other field is ignored.
"""
import argparse
import datetime
import json
import os
import re
import struct
import sys
import zipfile
from xml.sax.saxutils import escape as _esc

WARNINGS = []


def warn(line, msg):
    where = "line %d: " % line if line else ""
    WARNINGS.append(where + msg)
    print("WARN %s%s" % (where, msg), file=sys.stderr)


def die(msg):
    print("ERROR %s" % msg, file=sys.stderr)
    sys.exit(1)


# Control characters XML 1.0 forbids: every code point below 0x20 except tab, LF and CR.
_BAD_XML = dict.fromkeys(c for c in range(0x20) if c not in (0x09, 0x0A, 0x0D))


def x(s):
    """Escape text for XML element content and attributes."""
    return _esc(s.translate(_BAD_XML), {'"': "&quot;"})


# --------------------------------------------------------------------------- block parsing

RE_ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
RE_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
RE_HR = re.compile(r"^ {0,3}((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$")
RE_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*([^`]*)$")
RE_ITEM = re.compile(r"^([ \t]*)([-*+]|\d{1,9}[.)])(?:[ \t]+(.*)|$)")
RE_TABLE_SEP = re.compile(r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
RE_HTML_BLOCK = re.compile(r"^ {0,3}<(!--|/?[A-Za-z][A-Za-z0-9-]*(\s[^>]*)?/?>|/?[A-Za-z][A-Za-z0-9-]*\s*$)")
RE_FOOTDEF = re.compile(r"^ {0,3}\[\^[^\]]+\]:")
RE_REFDEF = re.compile(r"^ {0,3}\[([^\]^][^\]]*)\]:[ \t]*<?(\S+?)>?(?:[ \t]+[\"'(].*[\"')])?[ \t]*$")


def expand_tabs(line):
    return line.expandtabs(4)


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], "", 0
    in_code = False
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


def parse_blocks(lines, base_line, refs):
    """lines: list of str (no newline). Returns list of block dicts, each with 'line'."""
    blocks = []
    i = 0
    n = len(lines)
    para = []  # (line_no, text)

    def flush_para():
        if para:
            blocks.append({"type": "para", "lines": list(para), "line": para[0][0]})
            del para[:]

    while i < n:
        raw = lines[i]
        line = expand_tabs(raw)
        ln = base_line + i
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        m = RE_FENCE.match(line)
        if m:
            flush_para()
            fence, info = m.group(2), m.group(3).strip()
            ind = len(m.group(1))
            body = []
            i += 1
            closed = False
            while i < n:
                l2 = expand_tabs(lines[i])
                if l2.strip().startswith(fence[0] * len(fence)) and set(l2.strip()) <= {fence[0]}:
                    closed = True
                    i += 1
                    break
                body.append(l2[ind:] if indent_of(l2) >= ind else l2.lstrip(" "))
                i += 1
            if not closed:
                warn(ln, "code fence never closed; ran to end of file")
            lang = info.split()[0] if info else ""
            if lang.lower() == "mermaid":
                warn(ln, "mermaid block kept as code text, not rendered as a diagram")
            blocks.append({"type": "code", "text": "\n".join(body), "line": ln})
            continue

        if not para and indent_of(line) >= 4:
            body = []
            while i < n and (not lines[i].strip() or indent_of(expand_tabs(lines[i])) >= 4):
                body.append(expand_tabs(lines[i])[4:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            blocks.append({"type": "code", "text": "\n".join(body), "line": ln})
            continue

        m = RE_ATX.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            text = (m.group(2) or "").strip()
            if level > 4:
                warn(ln, "h%d has no Word equivalent here; written as Heading 4" % level)
            blocks.append({"type": "heading", "level": min(level, 4), "text": text, "line": ln})
            i += 1
            continue

        if para and RE_SETEXT.match(line) and len(para) == 1:
            level = 1 if stripped.startswith("=") else 2
            blocks.append({"type": "heading", "level": level, "text": para[0][1].strip(), "line": para[0][0]})
            del para[:]
            i += 1
            continue

        if RE_HR.match(line):
            flush_para()
            blocks.append({"type": "hr", "line": ln})
            i += 1
            continue

        if RE_FOOTDEF.match(line):
            flush_para()
            warn(ln, "footnote definition dropped (footnotes are not supported)")
            i += 1
            while i < n and lines[i].strip() and indent_of(expand_tabs(lines[i])) >= 2:
                i += 1
            continue

        m = RE_REFDEF.match(line)
        if m and not para:
            refs[m.group(1).strip().lower()] = m.group(2)
            i += 1
            continue

        if not para and RE_HTML_BLOCK.match(line):
            start = ln
            while i < n and lines[i].strip():
                i += 1
            end = base_line + i - 1
            warn(start, "raw HTML block dropped" + (" (lines %d-%d)" % (start, end) if end > start else ""))
            continue

        if stripped.startswith(">"):
            flush_para()
            inner = []
            start = ln
            while i < n:
                l2 = expand_tabs(lines[i])
                s2 = l2.lstrip(" ")
                if s2.startswith(">"):
                    s2 = s2[1:]
                    if s2.startswith(" "):
                        s2 = s2[1:]
                    inner.append(s2)
                elif l2.strip() and inner and inner[-1].strip():
                    inner.append(l2.strip())  # lazy continuation
                else:
                    break
                i += 1
            blocks.append({"type": "quote", "blocks": parse_blocks(inner, start, refs), "line": start})
            continue

        if "|" in line and i + 1 < n and RE_TABLE_SEP.match(lines[i + 1]) and "-" in lines[i + 1]:
            flush_para()
            header = split_row(line)
            aligns = []
            for c in split_row(lines[i + 1]):
                c = c.strip()
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("center")
                elif c.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append("left")
            rows = []
            i += 2
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(split_row(lines[i]))
                i += 1
            width = len(header)
            for r_i, r in enumerate(rows):
                if len(r) != width:
                    warn(ln, "table row %d has %d cells, header has %d; padded or cut" % (r_i + 1, len(r), width))
            rows = [(r + [""] * width)[:width] for r in rows]
            aligns = (aligns + ["left"] * width)[:width]
            blocks.append({"type": "table", "header": header, "rows": rows, "aligns": aligns, "line": ln})
            continue

        m = RE_ITEM.match(line)
        if m and (not para or m.group(3)):
            # an ordered item interrupts a paragraph only if it starts at 1 (CommonMark)
            marker = m.group(2)
            if not para or not marker[0].isdigit() or int(marker[:-1]) == 1:
                flush_para()
                lst, i = parse_list(lines, i, base_line)
                blocks.append(lst)
                continue

        para.append((ln, line))
        i += 1

    flush_para()
    return blocks


def parse_list(lines, i, base_line):
    n = len(lines)
    items = []  # dicts: level, ordered, start, lines[(ln,text)], task
    base = None
    child_indent = None
    deep_warned = False
    start_ln = base_line + i
    while i < n:
        line = expand_tabs(lines[i])
        ln = base_line + i
        if not line.strip():
            # blank: continue the list only if the next non-blank line is an item or indented
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                nxt = expand_tabs(lines[j])
                if RE_ITEM.match(nxt) and indent_of(nxt) >= (base or 0) or (items and indent_of(nxt) >= (base or 0) + 2):
                    i = j
                    continue
            break
        m = RE_ITEM.match(line)
        ind = indent_of(line)
        if m and not RE_HR.match(line):
            if base is None:
                base = ind
            if ind < base:
                break
            if ind < base + 2:
                level = 0
                child_indent = None
            else:
                if child_indent is None:
                    child_indent = ind
                level = 1
                if ind >= child_indent + 2 and not deep_warned:
                    warn(ln, "list nested deeper than one level; flattened to the second level")
                    deep_warned = True
            marker = m.group(2)
            ordered = marker[0].isdigit()
            text = m.group(3) or ""
            task = None
            tm = re.match(r"^\[([ xX])\][ \t]+(.*)$", text)
            if tm:
                task = tm.group(1).lower() == "x"
                text = tm.group(2)
            items.append({"level": level, "ordered": ordered, "start": int(marker[:-1]) if ordered else 1,
                          "lines": [(ln, text)], "task": task})
            i += 1
            continue
        if items and (ind >= (base or 0) + 2 or not RE_ATX.match(line) and not line.lstrip().startswith(">")
                      and not RE_FENCE.match(line) and not RE_HR.match(line)):
            s = line.strip()
            if RE_FENCE.match(s) or s.startswith("|"):
                warn(ln, "code block or table inside a list item; written as plain text in the item")
            items[-1]["lines"].append((ln, line.strip()))
            i += 1
            continue
        break
    return {"type": "list", "items": items, "line": start_ln}, i


# --------------------------------------------------------------------------- inline parsing

RE_IMG = re.compile(r"!\[((?:[^\]\\]|\\.)*)\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
RE_LINK = re.compile(r"\[((?:[^\[\]\\]|\\.|\[[^\]]*\])*)\]\(\s*<?([^)\s>]*)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
RE_REFLINK = re.compile(r"\[((?:[^\[\]\\]|\\.)+)\]\[([^\]]*)\]")
RE_SHORTREF = re.compile(r"\[((?:[^\[\]\\]|\\.)+)\](?![\[(:])")
RE_AUTOLINK = re.compile(r"<((?:https?|mailto|ftp):[^>\s]+)>")
RE_BAREURL = re.compile(r"https?://[^\s<>()]*[^\s<>().,;:!?'\"*_~]")
RE_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(\s[^<>]*)?/?>|<!--.*?-->")
RE_FOOTREF = re.compile(r"\[\^[^\]]+\]")
PUNCT = "\\`*_{}[]()#+-.!|~<>\"'$&"


class Inline(object):
    def __init__(self, refs, line):
        self.refs = refs
        self.line = line
        self.html_warned = False

    def parse(self, text, style=None):
        """Return a list of segments: ('text', str, style) | ('br',) | ('img', alt, src)."""
        style = dict(style or {})
        out = []
        buf = []

        def flush():
            if buf:
                out.append(("text", "".join(buf), dict(style)))
                del buf[:]

        i, n = 0, len(text)
        while i < n:
            c = text[i]
            rest = text[i:]
            if c == "\\" and i + 1 < n and text[i + 1] in PUNCT:
                buf.append(text[i + 1])
                i += 2
                continue
            if c == "`":
                run = len(rest) - len(rest.lstrip("`"))
                close = text.find("`" * run, i + run)
                while close != -1 and close + run < n and text[close + run] == "`":
                    close = text.find("`" * run, close + run + 1)
                if close != -1:
                    flush()
                    code = text[i + run:close]
                    if code.startswith(" ") and code.endswith(" ") and code.strip():
                        code = code[1:-1]
                    st = dict(style)
                    st["code"] = True
                    out.append(("text", code, st))
                    i = close + run
                    continue
                buf.append("`" * run)
                i += run
                continue
            if c == "!" and rest.startswith("!["):
                m = RE_IMG.match(rest)
                if m:
                    flush()
                    out.append(("img", m.group(1), m.group(2)))
                    i += m.end()
                    continue
            if c == "[":
                m = RE_FOOTREF.match(rest)
                if m:
                    warn(self.line, "footnote reference %s dropped" % m.group(0))
                    i += m.end()
                    continue
                m = RE_LINK.match(rest)
                url = None
                if m:
                    label, url = m.group(1), m.group(2)
                else:
                    m = RE_REFLINK.match(rest)
                    if m:
                        label = m.group(1)
                        key = (m.group(2) or m.group(1)).strip().lower()
                        url = self.refs.get(key)
                        if url is None:
                            m = None
                    if m is None:
                        m = RE_SHORTREF.match(rest)
                        if m and m.group(1).strip().lower() in self.refs:
                            label = m.group(1)
                            url = self.refs[label.strip().lower()]
                        else:
                            m = None
                if m:
                    flush()
                    st = dict(style)
                    st["link"] = url
                    out.extend(self.parse(label, st))
                    i += m.end()
                    continue
            if c == "<":
                m = RE_AUTOLINK.match(rest)
                if m:
                    flush()
                    st = dict(style)
                    st["link"] = m.group(1)
                    out.append(("text", m.group(1).replace("mailto:", ""), st))
                    i += m.end()
                    continue
                m = RE_TAG.match(rest)
                if m:
                    tag = m.group(0).lower()
                    if re.match(r"<br\s*/?>", tag):
                        flush()
                        out.append(("br",))
                    elif not self.html_warned:
                        warn(self.line, "inline HTML tag %s removed (text kept)" % m.group(0)[:30])
                        self.html_warned = True
                    i += m.end()
                    continue
            if c == "h" and not style.get("link") and (i == 0 or not text[i - 1].isalnum()):
                m = RE_BAREURL.match(rest)
                if m:
                    flush()
                    st = dict(style)
                    st["link"] = m.group(0)
                    out.append(("text", m.group(0), st))
                    i += m.end()
                    continue
            if c in "*_~":
                run_char = c
                run = len(rest) - len(rest.lstrip(c))
                if c == "~" and run >= 2:
                    close = text.find("~~", i + 2)
                    if close > i + 2:
                        flush()
                        st = dict(style)
                        st["strike"] = True
                        out.extend(self.parse(text[i + 2:close], st))
                        i = close + 2
                        continue
                elif c in "*_":
                    left_ok = i + run < n and not text[i + run].isspace()
                    if c == "_" and i > 0 and text[i - 1].isalnum():
                        left_ok = False
                    if left_ok:
                        for size in ((3, 2, 1) if run >= 3 else (2, 1) if run == 2 else (1,)):
                            delim = run_char * size
                            close = self._find_close(text, i + size, delim)
                            if close != -1:
                                flush()
                                st = dict(style)
                                if size >= 2:
                                    st["bold"] = True
                                if size in (1, 3):
                                    st["italic"] = True
                                out.extend(self.parse(text[i + size:close], st))
                                i = close + size
                                break
                        else:
                            buf.append(c * run)
                            i += run
                        continue
                buf.append(c * run)
                i += run
                continue
            if c == "\n":
                # hard break: two trailing spaces or a backslash before the newline
                if buf and ("".join(buf).endswith("  ") or "".join(buf).endswith("\\")):
                    s = "".join(buf).rstrip(" ").rstrip("\\")
                    del buf[:]
                    buf.append(s)
                    flush()
                    out.append(("br",))
                else:
                    s = "".join(buf).rstrip(" ")
                    del buf[:]
                    buf.append(s + " ")
                i += 1
                while i < n and text[i] == " ":
                    i += 1
                continue
            buf.append(c)
            i += 1
        flush()
        return out

    @staticmethod
    def _find_close(text, start, delim):
        """Index of the delimiter run that closes emphasis opened before `start`, or -1."""
        ch, size, n = delim[0], len(delim), len(text)
        pos = start
        while True:
            close = text.find(delim, pos)
            if close == -1:
                return -1
            run_end = close
            while run_end < n and text[run_end] == ch:
                run_end += 1
            run = run_end - close
            if close == start or text[close - 1].isspace():
                pos = run_end
                continue
            if ch == "_" and run_end < n and text[run_end].isalnum():
                pos = run_end
                continue
            if run == size:
                return close
            if run == 3 and size < 3:
                return run_end - size
            pos = run_end


# --------------------------------------------------------------------------- images

def image_size(path):
    """Return (width_px, height_px, dpi_x, dpi_y, kind) or None."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", data[16:24])
        dx = dy = 96.0
        pos = 8
        while pos + 8 <= len(data):
            length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
            if ctype == b"pHYs" and length == 9:
                px, py, unit = struct.unpack(">IIB", data[pos + 8:pos + 17])
                if unit == 1 and px and py:
                    dx, dy = px * 0.0254, py * 0.0254
                break
            if ctype == b"IDAT":
                break
            pos += 12 + length
        return w, h, dx, dy, "png"
    if data[:2] == b"\xff\xd8":
        dx = dy = 96.0
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                pos += 2
                continue
            length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            seg = data[pos + 4:pos + 2 + length]
            if marker == 0xE0 and seg[:5] == b"JFIF\x00" and len(seg) >= 12:
                units = seg[7]
                xd, yd = struct.unpack(">HH", seg[8:12])
                if units == 1 and xd and yd:
                    dx, dy = float(xd), float(yd)
                elif units == 2 and xd and yd:
                    dx, dy = xd * 2.54, yd * 2.54
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", seg[1:5])
                return w, h, dx, dy, "jpeg"
            pos += 2 + length
    return None


# --------------------------------------------------------------------------- docx writer

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
PAGES = {"letter": (12240, 15840), "a4": (11906, 16838)}  # twips
MARGIN = 1440
EMU_PER_TWIP = 635


def slugify(text):
    s = re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-")
    return s


class Doc(object):
    def __init__(self, src_dir, page, hr_mode, brand):
        self.src_dir = src_dir
        self.page = page
        self.hr_mode = hr_mode
        self.brand = brand
        self.rels = []  # (id, type, target, external)
        self.media = []  # (zip name, bytes)
        self.nums = []  # (numId, abstractId, start)
        self.body = []
        self.counts = {"headings": 0, "paragraphs": 0, "lists": 0, "tables": 0, "code blocks": 0,
                       "images": 0, "links": 0, "quotes": 0}
        self.next_pic = 1
        self.anchors = {}
        self.bookmark_id = 0
        self.content_width_twips = PAGES[page][0] - 2 * MARGIN
        self.add_rel("styles", "styles.xml")
        self.add_rel("numbering", "numbering.xml")
        self.add_rel("settings", "settings.xml")
        self.add_num(1, 1)  # numId 1 = bullets

    def add_rel(self, kind, target, external=False):
        rid = "rId%d" % (len(self.rels) + 1)
        self.rels.append((rid, REL_BASE + kind, target, external))
        return rid

    def add_num(self, abstract, start):
        num_id = len(self.nums) + 1
        self.nums.append((num_id, abstract, start))
        return num_id

    # ---- runs
    def runs(self, segments, base_rpr="", line=0):
        out = []
        for seg in segments:
            if seg[0] == "br":
                out.append("<w:r><w:br/></w:r>")
                continue
            if seg[0] == "img":
                out.append(self.image_run(seg[1], seg[2], line))
                continue
            _, text, st = seg
            if not text:
                continue
            rpr = base_rpr
            if st.get("bold"):
                rpr += "<w:b/>"
            if st.get("italic"):
                rpr += "<w:i/>"
            if st.get("strike"):
                rpr += "<w:strike/>"
            if st.get("code"):
                rpr += ('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
                        '<w:sz w:val="20"/><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>')
            link = st.get("link")
            if link is not None:
                rpr = '<w:rStyle w:val="Hyperlink"/>' + rpr
            run = "<w:r>%s<w:t xml:space=\"preserve\">%s</w:t></w:r>" % (
                "<w:rPr>%s</w:rPr>" % rpr if rpr else "", x(text))
            if link is not None:
                run = self.wrap_link(link, run, line)
            out.append(run)
        return "".join(out)

    def wrap_link(self, url, run, line):
        if not url:
            return run
        if url.startswith("#"):
            name = self.anchors.get(url[1:].lower())
            if not name:
                warn(line, "link to #%s has no matching heading; kept as plain text" % url[1:])
                return run.replace('<w:rStyle w:val="Hyperlink"/>', "")
            self.counts["links"] += 1
            return '<w:hyperlink w:anchor="%s" w:history="1">%s</w:hyperlink>' % (name, run)
        self.counts["links"] += 1
        rid = self.add_rel("hyperlink", url, external=True)
        return '<w:hyperlink r:id="%s" w:history="1">%s</w:hyperlink>' % (rid, run)

    def image_run(self, alt, src, line):
        alt_plain = re.sub(r"\\(.)", r"\1", alt)
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", src) or src.startswith("data:"):
            warn(line, "remote or inline image %s not embedded; alt text written instead" % src[:60])
            return "<w:r><w:t xml:space=\"preserve\">[%s]</w:t></w:r>" % x(alt_plain or "image")
        path = os.path.join(self.src_dir, src.replace("%20", " "))
        if not os.path.isfile(path):
            warn(line, "image %s not found; alt text written instead" % src)
            return "<w:r><w:t xml:space=\"preserve\">[%s]</w:t></w:r>" % x(alt_plain or "image")
        info = image_size(path)
        if not info:
            warn(line, "image %s is not PNG or JPEG; alt text written instead" % src)
            return "<w:r><w:t xml:space=\"preserve\">[%s]</w:t></w:r>" % x(alt_plain or "image")
        w, h, dx, dy, kind = info
        cx = int(w / dx * 914400)
        cy = int(h / dy * 914400)
        max_cx = self.content_width_twips * EMU_PER_TWIP
        max_cy = int((PAGES[self.page][1] - 2 * MARGIN) * EMU_PER_TWIP * 0.9)
        scale = min(1.0, float(max_cx) / cx if cx else 1, float(max_cy) / cy if cy else 1)
        cx, cy = int(cx * scale), int(cy * scale)
        pid = self.next_pic
        self.next_pic += 1
        name = "image%d.%s" % (pid, "png" if kind == "png" else "jpeg")
        with open(path, "rb") as f:
            self.media.append(("word/media/" + name, f.read()))
        rid = self.add_rel("image", "media/" + name)
        self.counts["images"] += 1
        return (
            '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            '<wp:docPr id="%d" name="Picture %d" descr="%s"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="%d" name="%s" descr="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
        ) % (cx, cy, pid, pid, x(alt_plain), pid, x(name), x(alt_plain), rid, cx, cy)

    def inline(self, text, line, style=None):
        return Inline(self.refs, line).parse(text, style)

    def para(self, segs_xml, ppr=""):
        return "<w:p>%s%s</w:p>" % ("<w:pPr>%s</w:pPr>" % ppr if ppr else "", segs_xml)

    # ---- blocks
    def collect_anchors(self, blocks):
        seen = {}
        for b in blocks:
            if b["type"] == "heading":
                slug = slugify(re.sub(r"[*_`\[\]]|\(.*?\)", "", b["text"]))
                if slug in seen:
                    seen[slug] += 1
                    slug = "%s-%d" % (slug, seen[slug])
                else:
                    seen[slug] = 0
                name = "h_" + re.sub(r"[^A-Za-z0-9_]", "_", slug)[:38]
                k = 2
                base = name
                while name in self.anchors.values():
                    name = "%s%d" % (base[:38 - len(str(k))], k)
                    k += 1
                self.anchors[slug] = name
                b["anchor"] = name
            elif b["type"] == "quote":
                self.collect_anchors(b["blocks"])

    def render(self, blocks, quote=False):
        for b in blocks:
            t = b["type"]
            ln = b["line"]
            if t == "heading":
                self.counts["headings"] += 1
                bid = self.bookmark_id
                self.bookmark_id += 1
                inner = '<w:bookmarkStart w:id="%d" w:name="%s"/>%s<w:bookmarkEnd w:id="%d"/>' % (
                    bid, b.get("anchor", "h_%d" % bid), self.runs(self.inline(b["text"], ln), "", ln), bid)
                self.body.append(self.para(inner, '<w:pStyle w:val="Heading%d"/>' % b["level"]))
            elif t == "para":
                self.counts["paragraphs"] += 1
                text = "\n".join(l for _, l in b["lines"]).strip()
                segs = self.inline(text, ln)
                ppr = '<w:pStyle w:val="Quote"/>' if quote else ""
                if len(segs) == 1 and segs[0][0] == "img" and not quote:
                    ppr = '<w:jc w:val="center"/>'
                self.body.append(self.para(self.runs(segs, "", ln), ppr))
            elif t == "code":
                self.counts["code blocks"] += 1
                parts = []
                for k, cl in enumerate(b["text"].split("\n")):
                    if k:
                        parts.append("<w:br/>")
                    pieces = cl.split("\t")
                    for j, piece in enumerate(pieces):
                        if j:
                            parts.append("<w:tab/>")
                        if piece:
                            parts.append('<w:t xml:space="preserve">%s</w:t>' % x(piece))
                self.body.append(self.para("<w:r>%s</w:r>" % "".join(parts), '<w:pStyle w:val="SourceCode"/>'))
            elif t == "quote":
                self.counts["quotes"] += 1
                self.render(b["blocks"], quote=True)
            elif t == "hr":
                if self.hr_mode == "page-break":
                    self.body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
                else:
                    self.body.append(self.para("", '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" '
                                                    'w:color="BFBFBF"/></w:pBdr>'))
            elif t == "list":
                self.render_list(b)
            elif t == "table":
                self.render_table(b)

    def render_list(self, b):
        self.counts["lists"] += 1
        current = [None, None]  # numId of the running ordered sequence per level
        for it in b["items"]:
            lvl = it["level"]
            if lvl == 0:
                current[1] = None
            if it["ordered"]:
                if current[lvl] is None:
                    current[lvl] = self.add_num(2, it["start"])
                num_id = current[lvl]
            else:
                current[lvl] = None
                num_id = 1
            text = "\n".join(t for _, t in it["lines"])
            segs = self.inline(text, it["lines"][0][0])
            if it["task"] is not None:
                segs.insert(0, ("text", u"\u2612 " if it["task"] else u"\u2610 ", {}))
            ppr = '<w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%d"/></w:numPr>' % (
                lvl, num_id)
            self.body.append(self.para(self.runs(segs, "", it["lines"][0][0]), ppr))

    def render_table(self, b):
        self.counts["tables"] += 1
        ncols = len(b["header"])
        colw = self.content_width_twips // max(ncols, 1)
        out = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="pct"/>'
               '<w:tblBorders>' + "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' % e
                                   for e in ("top", "left", "bottom", "right", "insideH", "insideV")) +
               '</w:tblBorders><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
               'w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>']
        out.append("".join('<w:gridCol w:w="%d"/>' % colw for _ in range(ncols)))
        out.append("</w:tblGrid>")
        for r_i, row in enumerate([b["header"]] + b["rows"]):
            is_head = r_i == 0
            out.append("<w:tr>%s" % ('<w:trPr><w:tblHeader/></w:trPr>' if is_head else ""))
            for c_i, cell in enumerate(row):
                tcpr = '<w:tcW w:w="%d" w:type="dxa"/>' % colw
                if is_head:
                    tcpr += '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % self.brand["header_fill"]
                segs = self.inline(cell, b["line"], {"bold": True} if is_head else None)
                ppr = '<w:spacing w:before="40" w:after="40"/><w:jc w:val="%s"/>' % b["aligns"][c_i]
                out.append("<w:tc><w:tcPr>%s</w:tcPr>%s</w:tc>" % (tcpr, self.para(self.runs(segs, "", b["line"]), ppr)))
            out.append("</w:tr>")
        out.append("</w:tbl>")
        self.body.append("".join(out))
        self.body.append("<w:p/>")  # Word needs a paragraph between adjacent tables

    # ---- parts
    def document_xml(self):
        pw, ph = PAGES[self.page]
        sect = ('<w:sectPr><w:pgSz w:w="%d" w:h="%d"/><w:pgMar w:top="%d" w:right="%d" w:bottom="%d" '
                'w:left="%d" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>') % (
                    pw, ph, MARGIN, MARGIN, MARGIN, MARGIN)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<w:document xmlns:w="%s" xmlns:r="%s" '
                'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                '<w:body>%s%s</w:body></w:document>') % (NS_W, NS_R, "".join(self.body), sect)

    def styles_xml(self):
        br = self.brand
        hf, bf = x(br["heading_font"]), x(br["body_font"])
        hc, bc = br["heading_color"], br["text_color"]
        sizes = {1: 32, 2: 26, 3: 24, 4: 22}
        heads = []
        for lvl in range(1, 5):
            heads.append(
                '<w:style w:type="paragraph" w:styleId="Heading%d"><w:name w:val="heading %d"/>'
                '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/>'
                '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="%d" w:after="80"/><w:outlineLvl w:val="%d"/></w:pPr>'
                '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s"/><w:b/>%s<w:color w:val="%s"/>'
                '<w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr></w:style>' % (
                    lvl, lvl, 360 if lvl == 1 else 240, lvl - 1, hf, hf, hf,
                    "<w:i/>" if lvl == 4 else "", hc, sizes[lvl], sizes[lvl]))
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:styles xmlns:w="%s">'
            '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:eastAsia="%s" w:cs="%s"/>'
            '<w:color w:val="%s"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
            '</w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
            '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s"/></w:rPr></w:style>'
            '%s'
            '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>'
            '<w:next w:val="Normal"/><w:uiPriority w:val="10"/><w:qFormat/><w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s"/>'
            '<w:color w:val="%s"/><w:sz w:val="48"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/>'
            '<w:uiPriority w:val="29"/><w:qFormat/><w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" '
            'w:color="BFBFBF"/></w:pBdr><w:ind w:left="360" w:right="360"/></w:pPr><w:rPr><w:i/>'
            '<w:color w:val="595959"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
            '<w:basedOn w:val="Normal"/><w:uiPriority w:val="34"/><w:qFormat/><w:pPr><w:spacing w:after="60"/>'
            '<w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:customStyle="1" w:styleId="SourceCode"><w:name w:val="Source Code"/>'
            '<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
            '<w:spacing w:before="60" w:after="160" w:line="240" w:lineRule="auto"/><w:ind w:left="144" w:right="144"/></w:pPr>'
            '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:color w:val="1F1F1F"/>'
            '<w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:uiPriority w:val="99"/>'
            '<w:unhideWhenUsed/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
            '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/>'
            '<w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
            '</w:tblCellMar></w:tblPr></w:style>'
            '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:basedOn w:val="TableNormal"/>'
            '<w:uiPriority w:val="39"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
            '<w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            '<w:left w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            '<w:right w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/></w:tblBorders></w:tblPr></w:style>'
            '</w:styles>'
        ) % (NS_W, bf, bf, bf, bf, bc, bf, bf, bf, "".join(heads), hf, hf, hc)

    def numbering_xml(self):
        def lvl(i, fmt, text, ind, start=1):
            font = ""
            if fmt == "bullet":
                face = "Symbol" if text == u"\uf0b7" else "Courier New"
                font = '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:hint="default"/></w:rPr>' % (face, face)
            return ('<w:lvl w:ilvl="%d"><w:start w:val="%d"/><w:numFmt w:val="%s"/><w:lvlText w:val="%s"/>'
                    '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="%d" w:hanging="360"/></w:pPr>%s</w:lvl>') % (
                        i, start, fmt, x(text), ind, font)
        abstracts, nums = [], []
        for num_id, kind, start in self.nums:
            # one abstract definition per list run: readers that ignore startOverride, or that
            # continue numbering across lists sharing a definition, still number correctly
            if kind == 1:
                levels = lvl(0, "bullet", u"\uf0b7", 720) + lvl(1, "bullet", "o", 1440)
            else:
                levels = lvl(0, "decimal", "%1.", 720, start) + lvl(1, "lowerLetter", "%2.", 1440, start)
            abstracts.append('<w:abstractNum w:abstractNumId="%d"><w:multiLevelType w:val="hybridMultilevel"/>'
                             '%s</w:abstractNum>' % (num_id, levels))
            nums.append('<w:num w:numId="%d"><w:abstractNumId w:val="%d"/></w:num>' % (num_id, num_id))
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<w:numbering xmlns:w="%s">%s%s</w:numbering>') % (NS_W, "".join(abstracts), "".join(nums))

    def rels_xml(self):
        rows = []
        for rid, kind, target, ext in self.rels:
            rows.append('<Relationship Id="%s" Type="%s" Target="%s"%s/>' % (
                rid, kind, x(target), ' TargetMode="External"' if ext else ""))
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">%s'
                '</Relationships>') % "".join(rows)


def static_parts(title):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Default Extension="png" ContentType="image/png"/>'
          '<Default Extension="jpeg" ContentType="image/jpeg"/>'
          '<Override PartName="/word/document.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/word/numbering.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
          '<Override PartName="/word/settings.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
          '<Override PartName="/docProps/app.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
          '</Types>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="%sofficeDocument" Target="word/document.xml"/>'
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/'
                 'metadata/core-properties" Target="docProps/core.xml"/>'
                 '<Relationship Id="rId3" Type="%sextended-properties" Target="docProps/app.xml"/>'
                 '</Relationships>') % (REL_BASE, REL_BASE)
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>%s</dc:title><dc:creator></dc:creator>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified>'
            '</cp:coreProperties>') % (x(title), now, now)
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>md_to_docx.py</Application></Properties>')
    settings = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<w:settings xmlns:w="%s"><w:defaultTabStop w:val="720"/>'
                '<w:characterSpacingControl w:val="doNotCompress"/><w:compat>'
                '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
                '</w:compat></w:settings>') % NS_W
    return ct, root_rels, core, app, settings


# --------------------------------------------------------------------------- brand

def load_brand(path):
    brand = {"heading_font": "Calibri", "body_font": "Calibri", "heading_color": "1F3864",
             "text_color": "222222", "header_fill": "F2F2F2"}
    if not path:
        return brand, False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        die("cannot read brand file %s: %s" % (path, e))
    if not isinstance(data, dict):
        die("brand file %s is not a JSON object" % path)
    fonts = data.get("fonts") or {}
    colors = data.get("colors") or {}
    for key, field in (("heading_font", "heading"), ("body_font", "body")):
        fam = (fonts.get(field) or {}).get("family") if isinstance(fonts.get(field), dict) else None
        if fam:
            brand[key] = str(fam)
    for key, field in (("heading_color", "primary"), ("text_color", "text")):
        val = colors.get(field)
        if val:
            if re.match(r"^#?[0-9A-Fa-f]{6}$", str(val)):
                brand[key] = str(val).lstrip("#").upper()
            else:
                warn(0, "brand colors.%s %r is not a 6-digit hex code; default kept" % (field, val))
    return brand, True


# --------------------------------------------------------------------------- main

def convert(src, out, brand_path, title, page, hr_mode):
    try:
        with open(src, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        die("cannot read %s: %s" % (src, e))
    except UnicodeDecodeError:
        die("%s is not UTF-8 text; save it as UTF-8 and rerun" % src)
    if "\x00" in text:
        die("%s looks like a binary file, not Markdown" % src)
    out_dir = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(out_dir):
        die("output folder %s does not exist" % out_dir)

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    base = 1
    fm_title = None
    if lines and lines[0].strip() == "---":
        for k in range(1, min(len(lines), 200)):
            if lines[k].strip() in ("---", "..."):
                for fl in lines[1:k]:
                    m = re.match(r"^title:\s*[\"']?(.*?)[\"']?\s*$", fl)
                    if m:
                        fm_title = m.group(1)
                warn(1, "YAML front matter dropped (lines 1-%d)%s" % (
                    k + 1, "; its title is used as the document title" if fm_title else ""))
                lines = lines[k + 1:]
                base = k + 2
                break

    brand, branded = load_brand(brand_path)
    refs = {}
    blocks = parse_blocks(lines, base, refs)
    if not title:
        title = fm_title
    if not title:
        for b in blocks:
            if b["type"] == "heading" and b["level"] == 1:
                title = re.sub(r"[*_`]", "", b["text"])
                break
    if not title:
        title = os.path.splitext(os.path.basename(src))[0]

    doc = Doc(os.path.dirname(os.path.abspath(src)), page, hr_mode, brand)
    doc.refs = refs
    doc.collect_anchors(blocks)
    doc.render(blocks)
    if not doc.body:
        die("%s has no content to convert" % src)

    ct, root_rels, core, app, settings = static_parts(title)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("word/document.xml", doc.document_xml())
        z.writestr("word/styles.xml", doc.styles_xml())
        z.writestr("word/numbering.xml", doc.numbering_xml())
        z.writestr("word/settings.xml", settings)
        z.writestr("word/_rels/document.xml.rels", doc.rels_xml())
        for name, data in doc.media:
            z.writestr(name, data)

    c = doc.counts
    summary = ", ".join("%d %s" % (v, k[:-1] if v == 1 else k) for k, v in c.items() if v)
    print("wrote %s (%s, page %s; brand: %s)" % (out, summary or "empty", page,
                                                 "%s / %s" % (brand["heading_font"], brand["body_font"]) if branded else "no"))
    print("  title: %s" % title)
    if WARNINGS:
        print("%d warning(s): the items above were dropped or changed; tell the user before sharing" % len(WARNINGS))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Markdown file")
    ap.add_argument("-o", "--output", required=True, help="output .docx path")
    ap.add_argument("--brand", help="brand.json from brand-kit (fonts and heading colour)")
    ap.add_argument("--title", help="document title for File > Properties (default: front matter, first h1, file name)")
    ap.add_argument("--page", choices=sorted(PAGES), default="letter", help="page size (default letter)")
    ap.add_argument("--hr", choices=("rule", "page-break"), default="rule",
                    help="what a --- horizontal rule becomes (default rule)")
    a = ap.parse_args(argv)
    if not a.output.lower().endswith(".docx"):
        die("output must end in .docx: %s" % a.output)
    convert(a.input, a.output, a.brand, a.title, a.page, a.hr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

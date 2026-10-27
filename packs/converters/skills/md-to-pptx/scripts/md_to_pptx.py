#!/usr/bin/env python3
"""Convert a Markdown document to a PowerPoint deck (.pptx). Stdlib only: zip + XML by hand.

Mapping (one rule each, so the deck is predictable):
  title slide   --title, else the first # heading, else front matter title:; subtitle from front
                matter subtitle/author/presenter/date, or one short paragraph right under the #
  ## heading    starts a slide; its text is the slide title. A later # heading starts a section
                slide (or a content slide, when text follows it before the next ##)
  ### to ###### a bold subheading line on the current slide
  lists         bulleted / numbered paragraphs, nesting kept to three levels (deeper is flattened)
  paragraphs    body text; > quotes in italic
  pipe tables   real PowerPoint tables (a:tbl) with a shaded header row; long tables split by
                rows onto continued slides, the header row repeated
  images        local PNG / JPEG embedded, scaled down to fit (never up)
  code blocks   a shaded monospace text box
  ---           forces a new slide, titled "<title> (continued)"
  <!-- notes: ... -->   speaker notes for the slide it sits on (the only notes convention)

Overflow: text height is estimated per slide; a slide that would overflow is split into
"<title> (continued)" slides instead of shrinking text. Every split is reported.

Dropped or changed, each with a WARN line naming the source line: raw HTML blocks and other
HTML comments, inline HTML tags (text kept), footnotes, remote / missing / non-PNG-JPEG images,
nesting past three levels, code or tables inside list items, front matter (title fields used),
links to local files, a "Notes:" paragraph (kept on the slide, not made into notes).

After writing, the file is re-opened and checked: every XML part parses, every internal
relationship target exists, and every part has a content type.

Usage:
  python3 md_to_pptx.py input.md -o deck.pptx [--brand brand.json] [--title "..."]
                        [--aspect 16:9|4:3]
  (input "-" reads Markdown from stdin; image paths are then relative to the current folder)
"""
import argparse
import datetime
import json
import os
import posixpath
import re
import struct
import sys
import zipfile
from urllib.parse import quote
from xml.dom import minidom
from xml.sax.saxutils import escape as _esc

WARNINGS = []
QUIET = [False]  # set while measuring, so a cell parsed twice warns once


def warn(line, msg):
    if QUIET[0]:
        return
    where = "line %d: " % line if line else ""
    if where + msg in WARNINGS:
        return
    WARNINGS.append(where + msg)
    print("WARN %s%s" % (where, msg), file=sys.stderr)


def die(msg, code=1):
    print("ERROR %s" % msg, file=sys.stderr)
    sys.exit(code)


_BAD_XML = dict.fromkeys(c for c in range(0x20) if c not in (0x09, 0x0A, 0x0D))


def x(s):
    """Escape text for XML element content and attributes."""
    return _esc(s.translate(_BAD_XML), {'"': "&quot;"})


# =========================================================================== block parsing

RE_ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
RE_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
RE_HR = re.compile(r"^ {0,3}((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$")
RE_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*([^`]*)$")
RE_ITEM = re.compile(r"^([ \t]*)([-*+]|\d{1,9}[.)])(?:[ \t]+(.*)|$)")
RE_TABLE_SEP = re.compile(r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
RE_HTML_BLOCK = re.compile(r"^ {0,3}<(/?[A-Za-z][A-Za-z0-9-]*(\s[^>]*)?/?>|/?[A-Za-z][A-Za-z0-9-]*\s*$)")
RE_FOOTDEF = re.compile(r"^ {0,3}\[\^[^\]]+\]:")
RE_REFDEF = re.compile(r"^ {0,3}\[([^\]^][^\]]*)\]:[ \t]*<?(\S+?)>?(?:[ \t]+[\"'(].*[\"')])?[ \t]*$")
RE_NOTES = re.compile(r"^\s*(?:speaker[ _-]?)?notes?\s*:\s*(.*)$", re.I | re.S)
RE_NOTES_PARA = re.compile(r"^\s*(?:\*\*|__)?\s*(?:speaker\s+)?notes\s*(?:\*\*|__)?\s*:", re.I)


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
    """lines: list of str (no newline). Returns a list of block dicts, each with 'line'."""
    blocks = []
    i = 0
    n = len(lines)
    para = []

    def flush_para():
        if para:
            blocks.append({"type": "para", "lines": list(para), "line": para[0][0]})
            del para[:]

    while i < n:
        line = expand_tabs(lines[i])
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

        if stripped.startswith("<!--"):
            flush_para()
            buf = [stripped]
            while "-->" not in buf[-1] and i + 1 < n:
                i += 1
                buf.append(lines[i])
            i += 1
            body = "\n".join(buf)
            if "-->" not in body:
                warn(ln, "HTML comment never closed; ran to end of file")
            tail = body.split("-->", 1)[1].strip() if "-->" in body else ""
            inner = body[4:].split("-->", 1)[0]
            nm = RE_NOTES.match(inner)
            if nm:
                text = "\n".join(l.strip() for l in nm.group(1).strip().split("\n"))
                blocks.append({"type": "notes", "text": text, "line": ln})
            else:
                warn(ln, "HTML comment dropped (only <!-- notes: ... --> becomes speaker notes)")
            if tail:
                warn(ln, "text after the closing --> on the same line dropped")
            continue

        m = RE_ATX.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            text = (m.group(2) or "").strip()
            blocks.append({"type": "heading", "level": level, "text": text, "line": ln})
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
                s2 = l2.lstrip()  # the same whitespace the test above strips, or a line led by \v never advances
                if s2.startswith(">"):
                    s2 = s2[1:]
                    if s2.startswith(" "):
                        s2 = s2[1:]
                    inner.append(s2)
                elif l2.strip() and inner and inner[-1].strip():
                    inner.append(l2.strip())
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
                    aligns.append("ctr")
                elif c.endswith(":"):
                    aligns.append("r")
                else:
                    aligns.append("l")
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
            aligns = (aligns + ["l"] * width)[:width]
            blocks.append({"type": "table", "header": header, "rows": rows, "aligns": aligns, "line": ln})
            continue

        m = RE_ITEM.match(line)
        if m and (not para or m.group(3)):
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
    """A list block with items at levels 0-2. Deeper items are flattened to level 2."""
    n = len(lines)
    items = []
    stack = []  # indent of each open level
    deep_warned = False
    start_ln = base_line + i
    while i < n:
        line = expand_tabs(lines[i])
        ln = base_line + i
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                nxt = expand_tabs(lines[j])
                base = stack[0] if stack else 0
                if RE_ITEM.match(nxt) and indent_of(nxt) >= base or (items and indent_of(nxt) >= base + 2):
                    i = j
                    continue
            break
        m = RE_ITEM.match(line)
        ind = indent_of(line)
        if m and not RE_HR.match(line):
            if not stack:
                stack = [ind]
            if ind < stack[0]:
                break
            while len(stack) > 1 and ind < stack[-1]:
                stack.pop()
            if ind >= stack[-1] + 2:
                stack.append(ind)
            level = len(stack) - 1
            if level > 2:
                if not deep_warned:
                    warn(ln, "list nested deeper than three levels; flattened to the third level")
                    deep_warned = True
                level = 2
            marker = m.group(2)
            ordered = marker[0].isdigit()
            text = m.group(3) or ""
            task = None
            tm = re.match(r"^\[([ xX])\][ \t]+(.*)$", text)
            if tm:
                task = tm.group(1).lower() == "x"
                text = tm.group(2)
            items.append({"level": level, "ordered": ordered, "start": int(marker[:-1]) if ordered else 1,
                          "paren": marker.endswith(")"), "lines": [(ln, text)], "task": task})
            i += 1
            continue
        base = stack[0] if stack else 0
        if items and (ind >= base + 2 or not RE_ATX.match(line) and not line.lstrip().startswith(">")
                      and not RE_FENCE.match(line) and not RE_HR.match(line)
                      and not line.lstrip().startswith("<!--")):
            s = line.strip()
            if RE_FENCE.match(s) or s.startswith("|"):
                warn(ln, "code block or table inside a list item; written as plain text in the item")
            items[-1]["lines"].append((ln, s))
            i += 1
            continue
        break
    # number ordered items the way PowerPoint will: a run continues past deeper items
    runs = [None, None, None]
    run_id = 0
    jump_warned = False
    for it in items:
        lvl = it["level"]
        for k in range(lvl + 1, 3):
            runs[k] = None
        if it["ordered"]:
            if runs[lvl] is None:
                run_id += 1
                runs[lvl] = [run_id, it["start"]]
            elif it["start"] != runs[lvl][1] and not jump_warned:
                warn(it["lines"][0][0], "numbered list goes from %d to %d in the source; the slides number items "
                     "in sequence, so \"%d.\" shows as %d. Check for a missing item, and for text that refers to "
                     "items by number" % (runs[lvl][1] - 1, it["start"], it["start"], runs[lvl][1]))
                jump_warned = True
            it["num"] = runs[lvl][1]
            it["run"] = (start_ln, runs[lvl][0])
            runs[lvl][1] += 1
        else:
            runs[lvl] = None
    return {"type": "list", "items": items, "line": start_ln}, i


# =========================================================================== inline parsing

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
        """Return segments: ('text', str, style) | ('br',) | ('img', alt, src)."""
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


def plain(segs):
    out = []
    for s in segs:
        if s[0] == "text":
            out.append(s[1])
        elif s[0] == "br":
            out.append("\n")
        elif s[0] == "img":
            out.append("[%s]" % s[1])
    return "".join(out)


def slugify(text):
    text = re.sub(r"[*_`\[\]]|\(.*?\)", "", text)
    return re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-")


# =========================================================================== images

def image_size(path):
    """Return (width_px, height_px, dpi_x, dpi_y, kind) or None."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
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
        return (w, h, dx, dy, "png") if w and h else None
    if data[:2] == b"\xff\xd8":
        dx = dy = 96.0
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xD8, 0x01, 0xFF) or 0xD0 <= marker <= 0xD7:
                pos += 1 if marker == 0xFF else 2
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
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC) and len(seg) >= 5:
                h, w = struct.unpack(">HH", seg[1:5])
                return (w, h, dx, dy, "jpeg") if w and h else None
            pos += 2 + length
    return None


# =========================================================================== geometry

EMU_IN = 914400
EMU_PT = 12700
SLIDE_H = 6858000
SLIDE_W = {"16:9": 12192000, "4:3": 9144000}
MARGIN_X = int(0.6 * EMU_IN)
TITLE_Y = int(0.35 * EMU_IN)
TITLE_H = int(1.0 * EMU_IN)
BODY_Y = int(1.45 * EMU_IN)
BODY_BOTTOM = int(7.05 * EMU_IN)
GAP = int(0.12 * EMU_IN)
INSET = 45720  # 0.05 in top and bottom inset of text frames
SIDE_INSET = 91440  # 0.1 in left and right
USABLE = 0.96  # keep a little headroom: the height model is an estimate

TITLE_PT = 32
SIZES = {  # role -> (font pt, left margin in, hanging indent in, space before pt)
    "p": (20, 0.0, 0.0, 8),
    "quote": (20, 0.4, 0.0, 8),
    "sub": (22, 0.0, 0.0, 12),
    0: (20, 0.375, 0.375, 8),
    1: (18, 0.75, 0.3, 4),
    2: (16, 1.1, 0.25, 2),
}
CODE_PT = 14
TABLE_PT = 14
CELL_MAR_X = 91440
CELL_MAR_Y = 45720
BULLETS = {0: u"\u2022", 1: u"\u2013", 2: u"\u25e6"}
NUM_SCHEMES = {0: "arabic", 1: "alphaLc", 2: "romanLc"}


def char_factor(font):
    f = (font or "").lower()
    if any(k in f for k in ("verdana", "tahoma", "trebuchet")):
        return 0.60
    if any(k in f for k in ("calibri", "aptos", "segoe", "candara", "corbel")):
        return 0.50
    return 0.55


def wrapped_lines(text, cpl):
    total = 0
    for hard in text.split("\n"):
        words = hard.split()
        if not words:
            total += 1
            continue
        lines, cur = 1, 0
        for w in words:
            wl = len(w)
            if wl > cpl:  # a very long token (URL) starts a fresh line and breaks mid-word
                if cur:
                    lines += 1
                full, rest = divmod(wl, cpl)
                lines += full - 1 + (1 if rest else 0)
                cur = rest if rest else cpl
                continue
            need = wl + (1 if cur else 0)
            if cur + need > cpl:
                lines += 1
                cur = wl
            else:
                cur += need
        total += lines
    return total


def text_lines(text, size_pt, width_emu, factor):
    width_pt = width_emu / float(EMU_PT)
    cpl = max(6, int(width_pt / (size_pt * factor)))
    return wrapped_lines(text, cpl)


# =========================================================================== deck model

class Deck(object):
    def __init__(self, src_dir, aspect, brand, refs):
        self.src_dir = src_dir
        self.aspect = aspect
        self.brand = brand
        self.refs = refs
        self.width = SLIDE_W[aspect]
        self.body_w = self.width - 2 * MARGIN_X
        self.body_h = int((BODY_BOTTOM - BODY_Y) * USABLE)
        self.body_factor = char_factor(brand["body_font"])
        self.head_factor = char_factor(brand["heading_font"])
        self.media = []
        self.media_by_path = {}
        self.counts = {"tables": 0, "images": 0, "links": 0, "code blocks": 0}

    # ---- unit builders ------------------------------------------------------------
    def inline(self, text, line, style=None):
        return Inline(self.refs, line).parse(text, style)

    def para_unit(self, role, segs, line, level=None, extra=None):
        key = level if role in ("bullet", "num") else role
        size, marl, _, spc = SIZES[key]
        width = self.body_w - 2 * SIDE_INSET - int(marl * EMU_IN)
        factor = self.head_factor * 1.06 if role == "sub" else self.body_factor
        if any(s[0] == "text" and s[2].get("bold") for s in segs):
            factor *= 1.03
        lines = text_lines(plain(segs), size, width, factor)
        h = int((lines * size * 1.2 + spc) * EMU_PT)
        u = {"kind": "para", "role": role, "level": level or 0, "segs": segs, "line": line, "h": h}
        if extra:
            u.update(extra)
        return u

    def image_unit(self, alt, src, line):
        alt_plain = re.sub(r"\\(.)", r"\1", alt)
        fallback = [("text", "[%s]" % (alt_plain or "image"), {"italic": True})]
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", src) or src.startswith("data:"):
            warn(line, "remote or inline image %s not fetched; alt text written instead" % src[:60])
            return self.para_unit("p", fallback, line)
        path = os.path.join(self.src_dir, src.replace("%20", " "))
        if not os.path.isfile(path):
            warn(line, "image %s not found; alt text written instead" % src)
            return self.para_unit("p", fallback, line)
        info = image_size(path)
        if not info:
            warn(line, "image %s is not PNG or JPEG; alt text written instead" % src)
            return self.para_unit("p", fallback, line)
        w, h, dx, dy, kind = info
        if min(w, h) < 64:
            warn(line, "image %s is only %dx%d pixels, so it shows as a speck on the slide; it looks like a "
                       "placeholder or a thumbnail. Replace it with the full-size image" % (src, w, h))
        cx, cy = w / dx * EMU_IN, h / dy * EMU_IN
        scale = min(1.0, self.body_w / cx, self.body_h / cy)
        return {"kind": "image", "path": os.path.abspath(path), "alt": alt_plain, "fmt": kind,
                "cx": int(cx * scale), "cy": int(cy * scale), "line": line}

    def table_rows(self, header, rows, aligns):
        QUIET[0] = True
        try:
            return self._table_rows(header, rows)
        finally:
            QUIET[0] = False

    def _table_rows(self, header, rows):
        ncols = len(header)
        natural = []
        for c in range(ncols):
            longest = max([len(plain(self.inline(r[c], 0))) for r in [header] + rows] + [3])
            natural.append((min(longest, 40) + 1) * TABLE_PT * 0.6 * EMU_PT + 2 * CELL_MAR_X)
        total = sum(natural)
        width = int(min(self.body_w, max(total, self.body_w * 0.5)))
        cols = [max(int(width * nw / total), int(0.75 * EMU_IN)) for nw in natural]
        width = sum(cols)
        if width > self.body_w:
            cols = [int(c * self.body_w / float(width)) for c in cols]
            width = sum(cols)
        heights = []
        for r in [header] + rows:
            lines = 1
            for c in range(ncols):
                f = self.body_factor * (1.05 if r is header else 1.0)
                lines = max(lines, text_lines(plain(self.inline(r[c], 0)), TABLE_PT,
                                              cols[c] - 2 * CELL_MAR_X, f))
            heights.append(int(lines * TABLE_PT * 1.2 * EMU_PT + 2 * CELL_MAR_Y + 2 * EMU_PT))
        return cols, heights

    def code_lines_h(self, lines):
        width = self.body_w - 2 * SIDE_INSET
        n = sum(text_lines(l or " ", CODE_PT, width, 0.6) for l in lines)
        return int(n * CODE_PT * 1.2 * EMU_PT) + 2 * int(0.08 * EMU_IN)

    def units_from_blocks(self, blocks, quote=False):
        units = []
        for b in blocks:
            t, ln = b["type"], b["line"]
            if t == "heading":
                segs = self.inline(b["text"], ln, {"bold": True})
                units.append(self.para_unit("sub", segs, ln, extra={"slug": slugify(b["text"])}))
            elif t == "para":
                text = "\n".join(l for _, l in b["lines"]).strip()
                if RE_NOTES_PARA.match(text):
                    warn(ln, "paragraph starting \"Notes:\" stays on the slide as text; wrap it in "
                             "<!-- notes: ... --> to make it speaker notes")
                segs = self.inline(text, ln)
                imgs = [s for s in segs if s[0] == "img"]
                rest = [s for s in segs if s[0] != "img"]
                if plain(rest).strip():
                    if imgs:
                        warn(ln, "image inside a text paragraph placed below the paragraph")
                    units.append(self.para_unit("quote" if quote else "p", rest, ln))
                for s in imgs:
                    units.append(self.image_unit(s[1], s[2], ln))
            elif t == "list":
                for it in b["items"]:
                    iln = it["lines"][0][0]
                    segs = self.inline("\n".join(tx for _, tx in it["lines"]), iln)
                    if any(s[0] == "img" for s in segs):
                        warn(iln, "image inside a list item not embedded; alt text written instead")
                    if it["task"] is not None:
                        segs.insert(0, ("text", u"\u2612 " if it["task"] else u"\u2610 ", {}))
                    role = "num" if it["ordered"] else "bullet"
                    extra = {"num": it.get("num"), "run": it.get("run"), "paren": it["paren"]}
                    units.append(self.para_unit(role, segs, iln, it["level"], extra))
            elif t == "code":
                self.counts["code blocks"] += 1
                units.append({"kind": "code", "lines": b["text"].split("\n"), "line": ln})
            elif t == "quote":
                units.extend(self.units_from_blocks(b["blocks"], quote=True))
            elif t == "table":
                self.counts["tables"] += 1
                if len(b["header"]) > 8:
                    warn(ln, "table has %d columns; at 14 pt the cells wrap heavily. Split it into two "
                             "tables or move it to an appendix" % len(b["header"]))
                cols, heights = self.table_rows(b["header"], b["rows"], b["aligns"])
                units.append({"kind": "table", "header": b["header"], "rows": b["rows"], "aligns": b["aligns"],
                              "cols": cols, "heights": heights, "line": ln})
            elif t == "notes":
                units.append({"kind": "notes", "text": b["text"], "line": ln})
            elif t == "hr":
                units.append({"kind": "break", "line": ln})
        return units

    # ---- pagination ---------------------------------------------------------------
    def paginate(self, units, title, line):
        """Pack units into pages of body height. Returns (pages, split_reason or None).

        A section that splits is then balanced: it is packed again into less height while it still
        takes the same number of slides, so the last one isn't left holding two stray lines."""
        pages, reasons = self._paginate([dict(u) for u in units], self.body_h)
        breaks = any(u["kind"] == "break" for u in units)
        if len(pages) > 1 and not breaks:
            best, H = (pages, reasons), self.body_h
            for k in range(1, 9):
                trial = self._paginate([dict(u) for u in units], int(H * (1 - 0.05 * k)))
                if len(trial[0]) != len(pages):
                    break
                best = trial
            pages, reasons = best
        return pages, reasons

    def _paginate(self, units, H):
        pages = [[]]
        used = [0]
        last = [None]
        reasons = []

        def new_page():
            if pages[-1] and any(u["kind"] != "notes" for u in pages[-1]):
                pages.append([])
                used[0] = 0
                last[0] = None

        def cost(u, h):
            if u["kind"] == "para" and last[0] == "para":
                return h
            return (GAP if used[0] else 0) + (2 * INSET if u["kind"] == "para" else 0) + h

        def place(u, h):
            used[0] += cost(u, h)
            last[0] = u["kind"]
            pages[-1].append(u)

        for u in units:
            k = u["kind"]
            if k == "notes":
                pages[-1].append(u)
                continue
            if k == "break":
                new_page()
                continue
            if k == "para":
                if used[0] + cost(u, u["h"]) > H and used[0]:
                    carry = []
                    # A nested list line belongs with the item above it: move the whole item, from
                    # its top-level line, to the next slide, unless that would empty this one or
                    # the item is taller than a slide anyway.
                    if u["role"] in ("bullet", "num") and u["level"] > 0:
                        cur = pages[-1]
                        i = len(cur)
                        while i > 0 and cur[i - 1]["kind"] == "para" and cur[i - 1]["role"] in ("bullet", "num") \
                                and cur[i - 1]["level"] > 0:
                            i -= 1
                        if i > 0 and cur[i - 1]["kind"] == "para" and cur[i - 1]["role"] in ("bullet", "num"):
                            i -= 1
                            item_h = sum(x["h"] for x in cur[i:]) + u["h"]
                            if [x for x in cur[:i] if x["kind"] != "notes"] and item_h < 0.8 * H:
                                carry = cur[i:]
                                del cur[i:]
                    # keep a subheading, or a lead-in line ending in ":", with what follows it
                    while pages[-1] and pages[-1][-1]["kind"] == "para" and (
                            pages[-1][-1]["role"] == "sub" or plain(pages[-1][-1]["segs"]).rstrip().endswith(":")) \
                            and len([p for p in pages[-1] if p["kind"] != "notes"]) > 1:
                        carry.insert(0, pages[-1].pop())
                    reasons.append("text")
                    pages.append([])
                    used[0] = 0
                    last[0] = None
                    for c in carry:
                        place(c, c["h"])
                if not used[0] and cost(u, u["h"]) > H:
                    warn(u["line"], "one paragraph is taller than a slide and will overflow it; "
                                    "break it into bullets or shorten it")
                place(u, u["h"])
            elif k == "image":
                full = u["cy"]
                room = H - used[0] - (GAP if used[0] else 0)
                if room >= full:
                    place(u, full)
                elif used[0] and room >= max(0.6 * full, 1.5 * EMU_IN):
                    s = room / float(full)
                    u["cx"], u["cy"] = int(u["cx"] * s), int(u["cy"] * s)
                    place(u, u["cy"])
                else:
                    reasons.append("image")
                    new_page()
                    place(u, full)
            elif k == "code":
                lines = u["lines"]
                while lines:
                    room = H - used[0] - (GAP if used[0] else 0)
                    take = len(lines)
                    while take > 0 and self.code_lines_h(lines[:take]) > room:
                        take -= 1
                    if take == len(lines) or (take >= 3 and used[0]) or not used[0]:
                        if take == 0:
                            take = 1
                        left = len(lines) - take
                        if 0 < left < 3 and take > 6:  # don't strand one or two lines on a slide
                            take -= 3 - left
                        chunk = dict(u, lines=lines[:take])
                        place(chunk, self.code_lines_h(chunk["lines"]))
                        lines = lines[take:]
                        if lines:
                            reasons.append("code")
                            new_page()
                    else:
                        reasons.append("code")
                        new_page()
            elif k == "table":
                rows = list(range(len(u["rows"])))
                hh = u["heights"][0]
                first = True
                while first or rows:
                    first = False
                    room = H - used[0] - (GAP if used[0] else 0)
                    take, h = 0, hh
                    while take < len(rows) and h + u["heights"][rows[take] + 1] <= room:
                        h += u["heights"][rows[take] + 1]
                        take += 1
                    if take == len(rows) or (take >= 2 and used[0]) or not used[0]:
                        if take == 0 and rows:
                            take = 1
                        left = len(rows) - take
                        if left == 1 and take > 4:  # don't strand one row under a repeated header
                            take -= 1
                        h = hh + sum(u["heights"][r + 1] for r in rows[:take])
                        chunk = dict(u, rows=[u["rows"][r] for r in rows[:take]],
                                     heights=[hh] + [u["heights"][r + 1] for r in rows[:take]])
                        if h > H:
                            warn(u["line"], "a table row is taller than a slide and will overflow it")
                        place(chunk, h)
                        rows = rows[take:]
                        if rows:
                            reasons.append("table")
                            new_page()
                    else:
                        reasons.append("table")
                        new_page()
        if not pages[-1] and len(pages) > 1:
            pages.pop()
        return pages, reasons


# =========================================================================== XML writers

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CT = "application/vnd.openxmlformats-officedocument.presentationml."
GRP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
       '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
       '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def xfrm(xo, yo, cx, cy):
    return '<a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm>' % (xo, yo, cx, cy)


def rels_xml(rels):
    rows = []
    for rid, kind, target, ext in rels:
        rows.append('<Relationship Id="%s" Type="%s%s" Target="%s"%s/>' % (
            rid, REL, kind, x(target), ' TargetMode="External"' if ext else ""))
    return (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '%s</Relationships>') % "".join(rows)


class SlideOut(object):
    def __init__(self, deck, layout, anchors, number):
        self.deck = deck
        self.rels = [("rId1", "slideLayout", "../slideLayouts/slideLayout%d.xml" % layout, False)]
        self.shapes = []
        self.next_id = 2
        self.anchors = anchors
        self.number = number
        self.notes = []
        self.layout = layout

    def add_rel(self, kind, target, ext=False):
        for rid, k, t, e in self.rels:
            if k == kind and t == target and e == ext:
                return rid
        rid = "rId%d" % (len(self.rels) + 1)
        self.rels.append((rid, kind, target, ext))
        return rid

    def sid(self):
        i = self.next_id
        self.next_id += 1
        return i

    # ---- runs
    def runs(self, segs, size, line, color=None, font=None):
        out = []
        sz = ' sz="%d"' % int(size * 100) if size else ""
        for seg in segs:
            if seg[0] == "br":
                out.append('<a:br><a:rPr lang="en-US"%s/></a:br>' % sz)
                continue
            if seg[0] == "img":
                warn(line, "image inside a list item or table cell not embedded; alt text written instead")
                seg = ("text", "[%s]" % (seg[1] or "image"), {"italic": True})
            _, text, st = seg
            if not text:
                continue
            attrs = ' lang="en-US"' + sz
            if st.get("bold"):
                attrs += ' b="1"'
            if st.get("italic"):
                attrs += ' i="1"'
            if st.get("strike"):
                attrs += ' strike="sngStrike"'
            kids = ""
            if color:
                kids += '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % color
            if st.get("code"):
                kids += '<a:latin typeface="Consolas" pitchFamily="49" charset="0"/>' \
                        '<a:cs typeface="Consolas" pitchFamily="49" charset="0"/>'
            elif font:
                kids += '<a:latin typeface="%s"/>' % x(font)
            link = st.get("link")
            if link is not None:
                kids += self.link_xml(link, line)
            out.append('<a:r><a:rPr%s>%s</a:rPr><a:t>%s</a:t></a:r>' % (attrs, kids, x(text)))
        return "".join(out)

    def link_xml(self, url, line):
        if not url:
            return ""
        if url.startswith("#"):
            target = self.anchors.get(url[1:].lower())
            if not target:
                warn(line, "link to #%s has no matching heading; kept as plain text" % url[1:])
                return ""
            self.deck.counts["links"] += 1
            rid = self.add_rel("slide", "slide%d.xml" % target)
            return '<a:hlinkClick r:id="%s" action="ppaction://hlinksldjump"/>' % rid
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
            warn(line, "link to local file %s kept as a link, but the file is not inside the deck; "
                       "it opens only where that path exists" % url[:60])
        self.deck.counts["links"] += 1
        rid = self.add_rel("hyperlink", quote(url, safe=":/?#[]@!$&'()*+,;=%~-._"), ext=True)
        return '<a:hlinkClick r:id="%s"/>' % rid

    # ---- shapes
    def title(self, segs, line, ctr=False, sub_lines=None):
        ph = '<p:ph type="ctrTitle"/>' if ctr else '<p:ph type="title"/>'
        body = self.runs(segs, None, line)
        self.shapes.append(
            '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Title %d"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr>%s</p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p>%s'
            '<a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>' % (self.sid(), self.next_id - 2, ph, body))
        if sub_lines:
            paras = "".join('<a:p>%s</a:p>' % self.runs(s, None, line) for s in sub_lines)
            self.shapes.append(
                '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Subtitle %d"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
                '</p:cNvSpPr><p:nvPr><p:ph type="subTitle" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
                '<p:txBody><a:bodyPr/><a:lstStyle/>%s</p:txBody></p:sp>' % (self.sid(), self.next_id - 2, paras))

    def para_xml(self, u, startat):
        role, lvl = u["role"], u["level"]
        key = lvl if role in ("bullet", "num") else role
        size, marl, hang, spc = SIZES[key]
        color = None
        attrs = ' marL="%d" indent="%d"' % (int(marl * EMU_IN), -int(hang * EMU_IN))
        if role in ("bullet", "num"):
            attrs += ' lvl="%d"' % lvl
        inner = '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc><a:spcBef><a:spcPts val="%d"/></a:spcBef>' % (spc * 100)
        if role == "bullet":
            inner += ('<a:buClr><a:schemeClr val="accent1"/></a:buClr><a:buFont typeface="Arial"/>'
                      '<a:buChar char="%s"/>' % BULLETS[lvl])
        elif role == "num":
            scheme = NUM_SCHEMES[lvl] + ("ParenR" if u.get("paren") else "Period")
            inner += '<a:buClr><a:schemeClr val="accent1"/></a:buClr><a:buFont typeface="+mj-lt"/>' \
                     '<a:buAutoNum type="%s"%s/>' % (scheme, ' startAt="%d"' % startat if startat != 1 else "")
        else:
            inner += '<a:buNone/>'
        segs = u["segs"]
        if role == "quote":
            segs = [(s[0], s[1], dict(s[2], italic=True)) if s[0] == "text" else s for s in segs]
            color = "595959"
        if role == "sub":
            color = self.deck.brand.get("primary_for_text", self.deck.brand["primary"])
        font = self.deck.brand["heading_font"] if role == "sub" else None
        return '<a:p><a:pPr%s>%s</a:pPr>%s<a:endParaRPr lang="en-US" sz="%d"/></a:p>' % (
            attrs, inner, self.runs(segs, size, u["line"], color, font), size * 100)

    def text_frame(self, paras, y, h, placeholder):
        starts = {}
        out = []
        for u in paras:
            startat = 1
            if u["role"] == "num":
                run = u.get("run")
                if run not in starts:
                    starts[run] = u.get("num") or 1
                startat = starts[run]
            out.append(self.para_xml(u, startat))
        sid = self.sid()
        body = ('<p:txBody><a:bodyPr wrap="square" lIns="%d" tIns="%d" rIns="%d" bIns="%d" anchor="t">'
                '<a:normAutofit/></a:bodyPr><a:lstStyle/>%s</p:txBody>') % (
                    SIDE_INSET, INSET, SIDE_INSET, INSET, "".join(out))
        geo = xfrm(MARGIN_X, y, self.deck.body_w, h)
        if placeholder:
            self.shapes.append(
                '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Content %d"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
                '</p:cNvSpPr><p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr><p:spPr>%s</p:spPr>%s</p:sp>'
                % (sid, sid - 1, geo, body))
        else:
            self.shapes.append(
                '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Text %d"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                '<p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>%s</p:sp>'
                % (sid, sid - 1, geo, body))

    def code_box(self, u, y, h):
        sid = self.sid()
        paras = []
        for l in u["lines"]:
            l = l.replace("\t", "    ")
            run = ('<a:r><a:rPr lang="en-US" sz="%d"><a:solidFill><a:srgbClr val="1F1F1F"/></a:solidFill>'
                   '<a:latin typeface="Consolas" pitchFamily="49" charset="0"/>'
                   '<a:cs typeface="Consolas" pitchFamily="49" charset="0"/></a:rPr><a:t>%s</a:t></a:r>'
                   % (CODE_PT * 100, x(l))) if l else ""
            paras.append('<a:p><a:pPr marL="0" indent="0"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
                         '<a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/></a:pPr>%s'
                         '<a:endParaRPr lang="en-US" sz="%d"/></a:p>' % (run, CODE_PT * 100))
        ins = int(0.08 * EMU_IN)
        self.shapes.append(
            '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Code %d"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            '<p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="F2F2F2"/>'
            '</a:solidFill><a:ln w="6350"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill></a:ln></p:spPr>'
            '<p:txBody><a:bodyPr wrap="square" lIns="%d" tIns="%d" rIns="%d" bIns="%d" anchor="t"><a:noAutofit/>'
            '</a:bodyPr><a:lstStyle/>%s</p:txBody></p:sp>'
            % (sid, sid - 1, xfrm(MARGIN_X, y, self.deck.body_w, h), SIDE_INSET, ins, SIDE_INSET, ins, "".join(paras)))

    def table(self, u, y):
        sid = self.sid()
        cols, heights = u["cols"], u["heights"]
        width = sum(cols)
        xo = MARGIN_X + (self.deck.body_w - width) // 2
        brand = self.deck.brand
        head_text = brand["on_primary"]
        border = ('<a:%s w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:srgbClr val="BFBFBF"/>'
                  '</a:solidFill><a:prstDash val="solid"/></a:%s>')
        lines = "".join(border % (e, e) for e in ("lnL", "lnR", "lnT", "lnB"))
        rows_xml = []
        for r_i, row in enumerate([u["header"]] + u["rows"]):
            head = r_i == 0
            fill = brand["primary"] if head else ("FFFFFF" if r_i % 2 else "F2F2F2")
            cells = []
            for c_i, cell in enumerate(row):
                segs = Inline(self.deck.refs, u["line"]).parse(cell, {"bold": True} if head else None)
                cells.append(
                    '<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="%s" marL="0" indent="0"><a:buNone/>'
                    '</a:pPr>%s<a:endParaRPr lang="en-US" sz="%d"/></a:p></a:txBody>'
                    '<a:tcPr marL="%d" marR="%d" marT="%d" marB="%d" anchor="ctr">%s<a:solidFill>'
                    '<a:srgbClr val="%s"/></a:solidFill></a:tcPr></a:tc>' % (
                        u["aligns"][c_i], self.runs(segs, TABLE_PT, u["line"], head_text if head else None),
                        TABLE_PT * 100, CELL_MAR_X, CELL_MAR_X, CELL_MAR_Y, CELL_MAR_Y, lines, fill))
            rows_xml.append('<a:tr h="%d">%s</a:tr>' % (heights[r_i], "".join(cells)))
        grid = "".join('<a:gridCol w="%d"/>' % c for c in cols)
        self.shapes.append(
            '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="%d" name="Table %d"/><p:cNvGraphicFramePr>'
            '<a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
            '<p:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></p:xfrm><a:graphic>'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl>'
            '<a:tblPr firstRow="1" bandRow="1"><a:tableStyleId>{2D5ABB26-0587-4C30-8999-92F81FD0307C}'
            '</a:tableStyleId></a:tblPr><a:tblGrid>%s</a:tblGrid>%s</a:tbl></a:graphicData></a:graphic>'
            '</p:graphicFrame>' % (sid, sid - 1, xo, y, width, sum(heights), grid, "".join(rows_xml)))

    def picture(self, u, y):
        deck = self.deck
        name = deck.media_by_path.get(u["path"])
        if not name:
            name = "image%d.%s" % (len(deck.media) + 1, u["fmt"])
            with open(u["path"], "rb") as f:
                deck.media.append(("ppt/media/" + name, f.read()))
            deck.media_by_path[u["path"]] = name
        deck.counts["images"] += 1
        rid = self.add_rel("image", "../media/" + name)
        sid = self.sid()
        xo = MARGIN_X + (deck.body_w - u["cx"]) // 2
        self.shapes.append(
            '<p:pic><p:nvPicPr><p:cNvPr id="%d" name="Picture %d" descr="%s"/><p:cNvPicPr>'
            '<a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill>'
            '<a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>%s'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
            % (sid, sid - 1, x(u["alt"]), rid, xfrm(xo, y, u["cx"], u["cy"])))

    def layout_body(self, units):
        y = BODY_Y
        placeholder_used = False
        i = 0
        while i < len(units):
            u = units[i]
            k = u["kind"]
            if k == "notes":
                self.notes.append(u["text"])
                i += 1
                continue
            if y > BODY_Y:
                y += GAP
            if k == "para":
                group = []
                while i < len(units) and units[i]["kind"] in ("para", "notes"):
                    if units[i]["kind"] == "notes":
                        self.notes.append(units[i]["text"])
                    else:
                        group.append(units[i])
                    i += 1
                h = sum(p["h"] for p in group) + 2 * INSET
                self.text_frame(group, y, h, not placeholder_used)
                placeholder_used = True
                y += h
                continue
            if k == "code":
                h = self.deck.code_lines_h(u["lines"])
                self.code_box(u, y, h)
                y += h
            elif k == "table":
                self.table(u, y)
                y += sum(u["heights"])
            elif k == "image":
                self.picture(u, y)
                y += u["cy"]
            i += 1

    def xml(self):
        return (XML_HEAD + '<p:sld %s><p:cSld><p:spTree>%s%s</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>') % (NS, GRP, "".join(self.shapes))


def notes_xml(texts, width):
    paras = []
    for t in texts:
        for line in t.split("\n"):
            paras.append('<a:p><a:r><a:rPr lang="en-US"/><a:t>%s</a:t></a:r></a:p>' % x(line) if line.strip()
                         else '<a:p><a:endParaRPr lang="en-US"/></a:p>')
    img_h = int(5486400 * SLIDE_H / float(width))
    return (XML_HEAD + '<p:notes %s><p:cSld><p:spTree>%s'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" '
            'noRot="1" noChangeAspect="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr>'
            '<p:spPr>%s</p:spPr></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
            '</p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr>%s</p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>%s</p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>') % (
                NS, GRP, xfrm(685800, 1143000, 5486400, img_h), xfrm(685800, 4400550, 5486400, 3600450),
                "".join(paras))


# ---- fixed parts --------------------------------------------------------------------

def theme_xml(brand, name):
    accents = [brand["primary"], brand["accent"], "A5A5A5", "FFC000", "5B9BD5", "70AD47"]
    clr = ('<a:dk1><a:srgbClr val="%s"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
           '<a:dk2><a:srgbClr val="%s"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>' % (brand["text"], brand["primary"]))
    clr += "".join('<a:accent%d><a:srgbClr val="%s"/></a:accent%d>' % (i + 1, c, i + 1) for i, c in enumerate(accents))
    clr += '<a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink>'
    ln = ('<a:ln w="%d" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>')
    solid = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    return (XML_HEAD + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="%s">'
            '<a:themeElements><a:clrScheme name="%s">%s</a:clrScheme>'
            '<a:fontScheme name="%s"><a:majorFont><a:latin typeface="%s"/><a:ea typeface=""/><a:cs typeface=""/>'
            '</a:majorFont><a:minorFont><a:latin typeface="%s"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
            '</a:fontScheme><a:fmtScheme name="%s"><a:fillStyleLst>%s</a:fillStyleLst><a:lnStyleLst>%s</a:lnStyleLst>'
            '<a:effectStyleLst>%s</a:effectStyleLst><a:bgFillStyleLst>%s</a:bgFillStyleLst></a:fmtScheme>'
            '</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>') % (
                x(name), x(name), clr, x(name), x(brand["heading_font"]), x(brand["body_font"]), x(name),
                solid * 3, ln % 6350 + ln % 12700 + ln % 19050,
                '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3, solid * 3)


def text_styles():
    def lvl(n, marl, ind, sz, char, spc):
        return ('<a:lvl%dpPr marL="%d" indent="%d" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" '
                'hangingPunct="1"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc><a:spcBef><a:spcPts val="%d"/>'
                '</a:spcBef><a:buFont typeface="Arial"/><a:buChar char="%s"/><a:defRPr sz="%d" kern="1200">'
                '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/>'
                '<a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl%dpPr>') % (
                    n, marl, ind, spc, char, sz, n)
    body = "".join(lvl(i + 1, int(SIZES[i][1] * EMU_IN), -int(SIZES[i][2] * EMU_IN), SIZES[i][0] * 100,
                       BULLETS[i], SIZES[i][3] * 100) for i in range(3))
    title = ('<p:titleStyle><a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" '
             'hangingPunct="1"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/></a:spcBef>'
             '<a:buNone/><a:defRPr sz="%d" b="1" kern="1200"><a:solidFill><a:schemeClr val="tx2"/></a:solidFill>'
             '<a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:defRPr>'
             '</a:lvl1pPr></p:titleStyle>') % (TITLE_PT * 100)
    other = ('<p:otherStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr><a:lvl1pPr marL="0" algn="l" '
             'defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1"><a:defRPr sz="1800" kern="1200">'
             '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>'
             '<a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr></p:otherStyle>')
    return '<p:txStyles>%s<p:bodyStyle>%s</p:bodyStyle>%s</p:txStyles>' % (title, body, other)


def ph_sp(sid, name, ph, geo, body_pr, lst, text):
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr>%s</p:nvPr></p:nvSpPr><p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            '<p:txBody>%s<a:lstStyle>%s</a:lstStyle><a:p><a:r><a:rPr lang="en-US"/><a:t>%s</a:t></a:r></a:p>'
            '</p:txBody></p:sp>') % (sid, name, ph, geo, body_pr, lst, text)


CLRMAP = ('bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
          'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"')


def master_xml(width):
    bw = width - 2 * MARGIN_X
    title = ph_sp(2, "Title Placeholder 1", '<p:ph type="title"/>', xfrm(MARGIN_X, TITLE_Y, bw, TITLE_H),
                  '<a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0" anchor="b">'
                  '<a:normAutofit/></a:bodyPr>', "", "Click to edit Master title style")
    body = ph_sp(3, "Text Placeholder 2", '<p:ph type="body" idx="1"/>',
                 xfrm(MARGIN_X, BODY_Y, bw, BODY_BOTTOM - BODY_Y),
                 '<a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0">'
                 '<a:normAutofit/></a:bodyPr>', "", "Click to edit Master text styles")
    rule = ('<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="4" name="Title Rule"/><p:cNvCxnSpPr/><p:nvPr userDrawn="1"/>'
            '</p:nvCxnSpPr><p:spPr>%s<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="19050">'
            '<a:solidFill><a:schemeClr val="accent2"/></a:solidFill></a:ln></p:spPr></p:cxnSp>') % xfrm(
                MARGIN_X + SIDE_INSET, TITLE_Y + TITLE_H + 45720, int(1.2 * EMU_IN), 0)
    return (XML_HEAD + '<p:sldMaster %s><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef>'
            '</p:bg><p:spTree>%s%s%s%s</p:spTree></p:cSld><p:clrMap %s/><p:sldLayoutIdLst>'
            '<p:sldLayoutId id="2147483649" r:id="rId1"/><p:sldLayoutId id="2147483650" r:id="rId2"/>'
            '</p:sldLayoutIdLst>%s</p:sldMaster>') % (NS, GRP, title, body, rule, CLRMAP, text_styles())


def layout_xml(kind, width):
    bw = width - 2 * MARGIN_X
    if kind == 1:
        t = ph_sp(2, "Title 1", '<p:ph type="ctrTitle"/>', xfrm(MARGIN_X, int(1.9 * EMU_IN), bw, int(1.9 * EMU_IN)),
                  '<a:bodyPr anchor="b"><a:normAutofit/></a:bodyPr>',
                  '<a:lvl1pPr algn="ctr"><a:defRPr sz="4000"/></a:lvl1pPr>', "Click to edit Master title style")
        s = ph_sp(3, "Subtitle 2", '<p:ph type="subTitle" idx="1"/>',
                  xfrm(MARGIN_X, int(4.0 * EMU_IN), bw, int(1.6 * EMU_IN)),
                  '<a:bodyPr><a:normAutofit/></a:bodyPr>',
                  '<a:lvl1pPr marL="0" indent="0" algn="ctr"><a:spcBef><a:spcPts val="600"/></a:spcBef><a:buNone/>'
                  '<a:defRPr sz="2000"><a:solidFill><a:srgbClr val="595959"/></a:solidFill></a:defRPr></a:lvl1pPr>',
                  "Click to edit Master subtitle style")
        return (XML_HEAD + '<p:sldLayout %s type="title" preserve="1" showMasterSp="0"><p:cSld name="Title Slide"><p:spTree>%s%s%s'
                '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>') % (NS, GRP, t, s)
    t = ph_sp(2, "Title 1", '<p:ph type="title"/>', xfrm(MARGIN_X, TITLE_Y, bw, TITLE_H),
              '<a:bodyPr/>', "", "Click to edit Master title style")
    b = ph_sp(3, "Content Placeholder 2", '<p:ph idx="1"/>', xfrm(MARGIN_X, BODY_Y, bw, BODY_BOTTOM - BODY_Y),
              '<a:bodyPr/>', "", "Click to edit Master text styles")
    return (XML_HEAD + '<p:sldLayout %s type="obj" preserve="1"><p:cSld name="Title and Content"><p:spTree>%s%s%s'
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>') % (NS, GRP, t, b)


def notes_master_xml(width):
    img_h = int(5486400 * SLIDE_H / float(width))
    return (XML_HEAD + '<p:notesMaster %s><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef>'
            '</p:bg><p:spTree>%s'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" '
            'noRot="1" noChangeAspect="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr>'
            '<p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="12700"><a:solidFill>'
            '<a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
            '</p:cNvSpPr><p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr><p:spPr>%s'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr><p:txBody><a:bodyPr vert="horz" lIns="91440" '
            'tIns="45720" rIns="91440" bIns="45720" rtlCol="0"/><a:lstStyle/><a:p><a:pPr lvl="0"/><a:r>'
            '<a:rPr lang="en-US"/><a:t>Click to edit Master text styles</a:t></a:r></a:p></p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMap %s/><p:notesStyle><a:lvl1pPr marL="0" algn="l" defTabSz="914400" '
            'rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1"><a:defRPr sz="1200" kern="1200"><a:solidFill>'
            '<a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>'
            '<a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr></p:notesStyle></p:notesMaster>') % (
                NS, GRP, xfrm(685800, 1143000, 5486400, img_h), xfrm(685800, 4400550, 5486400, 3600450), CLRMAP)


# =========================================================================== brand

def hex6(val):
    s = str(val).strip()
    if re.match(r"^#?[0-9A-Fa-f]{6}$", s):
        return s.lstrip("#").upper()
    return None


def luminance(h):
    def ch(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def load_brand(path):
    brand = {"heading_font": "Calibri", "body_font": "Calibri", "primary": "1F3864", "accent": "2E75B6",
             "text": "222222"}
    branded = False
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            die("cannot read brand file %s: %s" % (path, e))
        if not isinstance(data, dict):
            die("brand file %s is not a JSON object" % path)
        branded = True
        fonts = data.get("fonts") if isinstance(data.get("fonts"), dict) else {}
        colors = data.get("colors") if isinstance(data.get("colors"), dict) else {}
        for key, field in (("heading_font", "heading"), ("body_font", "body")):
            val = fonts.get(field)
            fam = val.get("family") if isinstance(val, dict) else val if isinstance(val, str) else None
            if fam and str(fam).strip():
                brand[key] = str(fam).strip()
        for key in ("primary", "accent", "text"):
            val = colors.get(key)
            if val:
                h = hex6(val)
                if h:
                    brand[key] = h
                else:
                    warn(0, "brand colors.%s %r is not a 6-digit hex code; default #%s kept" % (key, val, brand[key]))
    if contrast(brand["primary"], "FFFFFF") < 3.0:
        warn(0, "brand primary #%s is too light for slide titles on white (contrast %.1f:1); "
                "titles use the text colour instead" % (brand["primary"], contrast(brand["primary"], "FFFFFF")))
        brand["primary_for_text"] = brand["text"]
    brand["on_primary"] = "FFFFFF" if contrast(brand["primary"], "FFFFFF") >= contrast(brand["primary"], "1F1F1F") \
        else "1F1F1F"
    return brand, branded


# =========================================================================== verification

def verify(path):
    """Re-open the package: XML parses, internal targets exist, every part has a content type."""
    problems = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        xml_parts = [n for n in names if n.endswith(".xml") or n.endswith(".rels")]
        for n in xml_parts:
            try:
                minidom.parseString(z.read(n))
            except Exception as e:  # noqa: BLE001 - report any parser failure
                problems.append("%s does not parse: %s" % (n, e))
        ct = minidom.parseString(z.read("[Content_Types].xml"))
        defaults = {e.getAttribute("Extension").lower() for e in ct.getElementsByTagName("Default")}
        overrides = {e.getAttribute("PartName") for e in ct.getElementsByTagName("Override")}
        for o in overrides:
            if o.lstrip("/") not in names:
                problems.append("content type declared for missing part %s" % o)
        for n in names:
            if n == "[Content_Types].xml" or n.endswith("/"):
                continue
            if "/" + n not in overrides and n.rsplit(".", 1)[-1].lower() not in defaults:
                problems.append("no content type for %s" % n)
        n_rels = 0
        for n in names:
            if not n.endswith(".rels"):
                continue
            folder = posixpath.dirname(posixpath.dirname(n))
            ids = set()
            for r in minidom.parseString(z.read(n)).getElementsByTagName("Relationship"):
                n_rels += 1
                rid = r.getAttribute("Id")
                if rid in ids:
                    problems.append("%s repeats relationship id %s" % (n, rid))
                ids.add(rid)
                if r.getAttribute("TargetMode") == "External":
                    continue
                t = r.getAttribute("Target")
                full = posixpath.normpath(t.lstrip("/") if t.startswith("/") else posixpath.join(folder, t))
                if full not in names:
                    problems.append("%s: %s points to missing %s" % (n, rid, full))
            src = n.replace("_rels/", "").rsplit(".rels", 1)[0]
            if src in names and src.endswith(".xml"):
                used = set(re.findall(r'r:(?:id|embed)="([^"]+)"', z.read(src).decode("utf-8")))
                for rid in used - ids:
                    problems.append("%s uses %s, which %s does not define" % (src, rid, n))
    if problems:
        for p in problems:
            print("ERROR verify: %s" % p, file=sys.stderr)
        die("the written file failed its own check; please report this with the input", code=2)
    return len(xml_parts), n_rels


# =========================================================================== main

def front_matter(lines):
    fm, base = {}, 1
    if lines and lines[0].strip() == "---":
        for k in range(1, min(len(lines), 200)):
            if lines[k].strip() in ("---", "..."):
                for fl in lines[1:k]:
                    m = re.match(r"^(title|subtitle|author|date|presenter)\s*:\s*[\"']?(.*?)[\"']?\s*$", fl, re.I)
                    if m and m.group(2):
                        fm[m.group(1).lower()] = m.group(2)
                used = ", ".join(k2 for k2 in ("title", "subtitle", "author", "presenter", "date") if k2 in fm)
                warn(1, "YAML front matter dropped (lines 1-%d)%s" % (
                    k + 1, "; used on the title slide: %s" % used if used else ""))
                return fm, lines[k + 1:], k + 2
    return fm, lines, base


def convert(src, out, brand_path, title_arg, aspect):
    if src == "-":
        text = sys.stdin.read()
        src_dir = os.getcwd()
        stem = "slides"
    else:
        try:
            with open(src, encoding="utf-8-sig") as f:
                text = f.read()
        except OSError as e:
            die("cannot read %s: %s" % (src, e))
        except UnicodeDecodeError:
            die("%s is not UTF-8 text; save it as UTF-8 and rerun" % src)
        src_dir = os.path.dirname(os.path.abspath(src))
        stem = os.path.splitext(os.path.basename(src))[0]
    if "\x00" in text:
        die("%s looks like a binary file, not Markdown" % src)
    if not text.strip():
        die("%s is empty" % src)
    out_dir = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(out_dir):
        die("output folder %s does not exist" % out_dir)

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    fm, lines, base = front_matter(lines)
    brand, branded = load_brand(brand_path)
    refs = {}
    blocks = parse_blocks(lines, base, refs)
    deck = Deck(src_dir, aspect, brand, refs)

    # ---- title, subtitle, and the sections that become slides
    # the title slide shows what a reader of the Markdown sees: --title, else the first # heading
    # (when it is the first heading), else the front matter title
    title, title_line = title_arg, 0
    first_heading = next((b for b in blocks if b["type"] == "heading"), None)
    if first_heading is not None and first_heading["level"] == 1:
        if title:
            warn(first_heading["line"], "first # heading \"%s\" replaced on the title slide by --title"
                 % first_heading["text"][:50])
        else:
            title, title_line = first_heading["text"], first_heading["line"]
        blocks.remove(first_heading)
    if not title:
        title = fm.get("title")
    pre, sections, cur = [], [], None
    for b in blocks:
        if b["type"] == "heading" and b["level"] <= 2:
            cur = {"title": b["text"], "line": b["line"], "level": b["level"], "blocks": []}
            sections.append(cur)
        elif cur is None:
            pre.append(b)
        else:
            cur["blocks"].append(b)

    sub_lines = []
    for key in ("subtitle", "author", "presenter", "date"):
        if fm.get(key):
            sub_lines.append(fm[key])
    title_notes = [b["text"] for b in pre if b["type"] == "notes"]
    content_pre = [b for b in pre if b["type"] != "notes"]
    if (title and not sub_lines and len(content_pre) == 1 and content_pre[0]["type"] == "para"
            and len(" ".join(l for _, l in content_pre[0]["lines"])) <= 200):
        sub_lines.append("\n".join(l for _, l in content_pre[0]["lines"]).strip())
        content_pre = []
    if title:
        if content_pre:
            sections.insert(0, {"title": title, "line": title_line, "level": 2,
                                "blocks": content_pre})
    else:
        if content_pre:
            sections.insert(0, {"title": stem, "line": 0, "level": 2, "blocks": content_pre})
            warn(0, "text before the first ## heading has no heading; its slide is titled with the file name "
                    "\"%s\"" % stem)
        warn(0, "no # title, front matter title or --title; the deck has no title slide")
        title_notes = []
    if not sections and not title:
        die("%s has nothing to put on slides" % src)

    # ---- paginate every section
    plan = []  # dicts: kind, title_segs, units, layout, section, page, pages
    if title:
        plan.append({"kind": "title", "title": title, "line": title_line, "units": [], "sub": sub_lines,
                     "notes": title_notes})
    anchors = {}
    splits = []
    for s in sections:
        units = deck.units_from_blocks(s["blocks"])
        if s["level"] == 1 and not [u for u in units if u["kind"] not in ("notes", "break")]:
            anchors.setdefault(slugify(s["title"]), len(plan) + 1)
            plan.append({"kind": "section", "title": s["title"], "line": s["line"], "units": [], "sub": [],
                         "notes": [u["text"] for u in units if u["kind"] == "notes"]})
            continue
        title_lines = text_lines(s["title"], TITLE_PT, deck.body_w - 2 * SIDE_INSET, deck.head_factor * 1.05)
        if title_lines > 2:
            warn(s["line"], "slide title \"%s\" wraps to %d lines; shorten it to fit two" % (
                s["title"][:50], title_lines))
        pages, reasons = deck.paginate(units, s["title"], s["line"])
        first = len(plan) + 1
        anchors.setdefault(slugify(s["title"]), first)
        for p_i, page in enumerate(pages):
            for u in page:
                if u.get("slug"):
                    anchors.setdefault(u["slug"], len(plan) + 1)
            plan.append({"kind": "content", "title": s["title"] + (" (continued)" if p_i else ""),
                         "line": s["line"], "units": page, "sub": [], "notes": []})
        if reasons:
            splits.append((s, first, first + len(pages) - 1, sorted(set(reasons))))

    for s, a, b, why in splits:
        warn(s["line"], "\"%s\" did not fit on one slide; split into %d slides (%d-%d) at a %s boundary, "
                        "text kept at full size" % (s["title"][:60], b - a + 1, a, b, " / ".join(why)))

    # ---- render
    width = deck.width
    slides = []
    for n, item in enumerate(plan, 1):
        layout = 2 if item["kind"] == "content" else 1
        so = SlideOut(deck, layout, anchors, n)
        segs = deck.inline(item["title"], item["line"])
        segs = [s for s in segs if s[0] != "img"]
        if item["kind"] == "content":
            so.title(segs, item["line"])
            so.layout_body(item["units"])
        else:
            so.title(segs, item["line"], ctr=True,
                     sub_lines=[deck.inline(t, item["line"]) for t in item["sub"]])
        so.notes = item["notes"] + so.notes
        slides.append(so)

    # ---- package
    n_notes = sum(1 for s in slides if s.notes)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pres_rels = [("rId1", "slideMaster", "slideMasters/slideMaster1.xml", False)]
    sld_ids = []
    for i in range(len(slides)):
        rid = "rId%d" % (len(pres_rels) + 1)
        pres_rels.append((rid, "slide", "slides/slide%d.xml" % (i + 1), False))
        sld_ids.append('<p:sldId id="%d" r:id="%s"/>' % (256 + i, rid))
    notes_master_id = ""
    if n_notes:
        rid = "rId%d" % (len(pres_rels) + 1)
        pres_rels.append((rid, "notesMaster", "notesMasters/notesMaster1.xml", False))
        notes_master_id = '<p:notesMasterIdLst><p:notesMasterId r:id="%s"/></p:notesMasterIdLst>' % rid
    for kind, target in (("theme", "theme/theme1.xml"), ("presProps", "presProps.xml"),
                         ("viewProps", "viewProps.xml"), ("tableStyles", "tableStyles.xml")):
        pres_rels.append(("rId%d" % (len(pres_rels) + 1), kind, target, False))
    presentation = (XML_HEAD + '<p:presentation %s saveSubsetFonts="1"><p:sldMasterIdLst>'
                    '<p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>%s<p:sldIdLst>%s</p:sldIdLst>'
                    '<p:sldSz cx="%d" cy="%d"%s/><p:notesSz cx="6858000" cy="9144000"/>'
                    '<p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle>'
                    '</p:presentation>') % (NS, notes_master_id, "".join(sld_ids), width, SLIDE_H,
                                             ' type="screen4x3"' if aspect == "4:3" else "")
    overrides = [("/ppt/presentation.xml", CT + "presentation.main+xml"),
                 ("/ppt/slideMasters/slideMaster1.xml", CT + "slideMaster+xml"),
                 ("/ppt/slideLayouts/slideLayout1.xml", CT + "slideLayout+xml"),
                 ("/ppt/slideLayouts/slideLayout2.xml", CT + "slideLayout+xml"),
                 ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
                 ("/ppt/presProps.xml", CT + "presProps+xml"),
                 ("/ppt/viewProps.xml", CT + "viewProps+xml"),
                 ("/ppt/tableStyles.xml", CT + "tableStyles+xml"),
                 ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
                 ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml")]
    if n_notes:
        overrides.append(("/ppt/notesMasters/notesMaster1.xml", CT + "notesMaster+xml"))
        overrides.append(("/ppt/theme/theme2.xml", "application/vnd.openxmlformats-officedocument.theme+xml"))
    for i, s in enumerate(slides, 1):
        overrides.append(("/ppt/slides/slide%d.xml" % i, CT + "slide+xml"))
        if s.notes:
            overrides.append(("/ppt/notesSlides/notesSlide%d.xml" % i, CT + "notesSlide+xml"))
    content_types = (XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Default Extension="png" ContentType="image/png"/>'
                     '<Default Extension="jpeg" ContentType="image/jpeg"/>%s</Types>') % "".join(
                         '<Override PartName="%s" ContentType="%s"/>' % o for o in overrides)
    root_rels = rels_xml([("rId1", "officeDocument", "ppt/presentation.xml", False),
                          ("rId2", "metadata/core-properties", "docProps/core.xml", False),
                          ("rId3", "extended-properties", "docProps/app.xml", False)])
    root_rels = root_rels.replace(REL + "metadata/core-properties",
                                  "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties")
    doc_title = fm.get("title") or title or stem
    core = (XML_HEAD + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/'
            'core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>%s</dc:title><dc:creator></dc:creator>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified></cp:coreProperties>') % (
                x(re.sub(r"[*_`]", "", doc_title)), now, now)
    app = (XML_HEAD + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>md_to_pptx.py</Application><Slides>%d</Slides><Notes>%d</Notes></Properties>') % (
               len(slides), n_notes)
    pres_props = XML_HEAD + '<p:presentationPr %s/>' % NS
    view_props = (XML_HEAD + '<p:viewPr %s><p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/>'
                  '</p:normalViewPr><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>') % NS
    table_styles = (XML_HEAD + '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                    'def="{2D5ABB26-0587-4C30-8999-92F81FD0307C}"/>')
    title_brand = dict(brand, primary=brand.get("primary_for_text", brand["primary"]))

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("ppt/presentation.xml", presentation)
        z.writestr("ppt/_rels/presentation.xml.rels", rels_xml(pres_rels))
        z.writestr("ppt/presProps.xml", pres_props)
        z.writestr("ppt/viewProps.xml", view_props)
        z.writestr("ppt/tableStyles.xml", table_styles)
        z.writestr("ppt/theme/theme1.xml", theme_xml(title_brand, "Deck"))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master_xml(width))
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels_xml([
            ("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml", False),
            ("rId2", "slideLayout", "../slideLayouts/slideLayout2.xml", False),
            ("rId3", "theme", "../theme/theme1.xml", False)]))
        for k in (1, 2):
            z.writestr("ppt/slideLayouts/slideLayout%d.xml" % k, layout_xml(k, width))
            z.writestr("ppt/slideLayouts/_rels/slideLayout%d.xml.rels" % k, rels_xml([
                ("rId1", "slideMaster", "../slideMasters/slideMaster1.xml", False)]))
        if n_notes:
            z.writestr("ppt/theme/theme2.xml", theme_xml(title_brand, "Deck notes"))
            z.writestr("ppt/notesMasters/notesMaster1.xml", notes_master_xml(width))
            z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels_xml([
                ("rId1", "theme", "../theme/theme2.xml", False)]))
        for i, s in enumerate(slides, 1):
            if s.notes:
                s.add_rel("notesSlide", "../notesSlides/notesSlide%d.xml" % i)
                z.writestr("ppt/notesSlides/notesSlide%d.xml" % i, notes_xml(s.notes, width))
                z.writestr("ppt/notesSlides/_rels/notesSlide%d.xml.rels" % i, rels_xml([
                    ("rId1", "notesMaster", "../notesMasters/notesMaster1.xml", False),
                    ("rId2", "slide", "../slides/slide%d.xml" % i, False)]))
            z.writestr("ppt/slides/slide%d.xml" % i, s.xml())
            z.writestr("ppt/slides/_rels/slide%d.xml.rels" % i, rels_xml(s.rels))
        for name, data in deck.media:
            z.writestr(name, data)

    n_parts, n_rels = verify(out)

    # ---- report
    c = deck.counts
    n_cont = sum(1 for p in plan if p["title"].endswith(" (continued)") and p["kind"] == "content")
    parts = ["%d slide%s" % (len(slides), "" if len(slides) == 1 else "s")]
    if n_cont:
        parts.append("%d of them continued" % n_cont)
    for k in ("tables", "images", "code blocks", "links"):
        if c[k]:
            parts.append("%d %s" % (c[k], k[:-1] if c[k] == 1 else k))
    parts.append("speaker notes on %d" % n_notes)
    print("wrote %s (%s; %s; brand: %s)" % (out, ", ".join(parts), aspect,
                                           "%s / %s" % (brand["heading_font"], brand["body_font"]) if branded else "no"))
    print("  checked: %d XML parts parse, %d relationships resolve, every part has a content type" % (
        n_parts, n_rels))
    for n, item in enumerate(plan, 1):
        bits = []
        for k in ("table", "image", "code"):
            m = sum(1 for u in item["units"] if u["kind"] == k)
            if m:
                bits.append("%s%s" % (k, " x%d" % m if m > 1 else ""))
        if slides[n - 1].notes:
            bits.append("notes")
        label = {"title": "title", "section": "section"}.get(item["kind"], "")
        print("  %2d. %s%s%s" % (n, re.sub(r"[*_`]", "", item["title"]),
                                 " [%s]" % label if label else "", " [%s]" % ", ".join(bits) if bits else ""))
    if WARNINGS:
        print("%d warning(s): the items above were dropped, split or changed; tell the user before sharing"
              % len(WARNINGS))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Markdown file, or - for stdin")
    ap.add_argument("-o", "--output", required=True, help="output .pptx path")
    ap.add_argument("--brand", help="brand.json (fonts.heading/body, colors.primary/accent/text)")
    ap.add_argument("--title", help="title slide text (default: front matter title, then the first # heading)")
    ap.add_argument("--aspect", choices=sorted(SLIDE_W), default="16:9", help="slide shape (default 16:9)")
    a = ap.parse_args(argv)
    if not a.output.lower().endswith(".pptx"):
        die("output must end in .pptx: %s" % a.output)
    convert(a.input, a.output, a.brand, a.title, a.aspect)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

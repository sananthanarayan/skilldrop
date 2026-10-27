#!/usr/bin/env python3
"""Convert a document into clean Markdown that another skill can read.

Stdlib only, Python 3.9+. Handles .docx, .pptx, .xlsx, .html/.htm, .csv/.tsv,
.json, .txt/.md, .eml and Outlook .msg email, and .pdf (through `pdftotext` when it is installed). A PDF page with no
text layer (a scan) is read by OCR when `tesseract` and `pdftoppm` are installed.
Embedded .docx and .pptx images are saved beside the output and linked, and tracked
changes come through as pending ({++added++}, {--removed--}). Everything else the
conversion could not carry (charts, comments, formulas) is counted and reported on
stderr, so nobody mistakes the Markdown for the whole document.

Usage:
    python3 to_markdown.py report.docx -o report.md
    python3 to_markdown.py deck.pptx -o deck.md
    python3 to_markdown.py model.xlsx -o model.md --max-rows 200
    python3 to_markdown.py page.html -o -          # write to stdout
    python3 to_markdown.py scan.pdf -o scan.md --ocr-lang deu   # OCR a German scan
"""

import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import zlib
from collections import OrderedDict
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


class Report:
    def __init__(self):
        self.kept = OrderedDict()
        self.dropped = OrderedDict()
        self.notes = []

    def keep(self, what, n=1):
        self.kept[what] = self.kept.get(what, 0) + n

    def drop(self, what, n=1):
        if n:
            self.dropped[what] = self.dropped.get(what, 0) + n


# ---------------------------------------------------------------- helpers

def md_escape(text):
    text = text.replace("\\", "\\\\")
    text = re.sub(r"([*_`\[\]])", r"\\\1", text)
    text = re.sub(r"<(?=[A-Za-z/!])", r"\\<", text)  # literal <tag> text must not read as raw HTML
    return text


def escape_line_start(text):
    """Stop plain text from turning into a heading, list or quote."""
    if re.match(r"^\s*(#{1,6}\s|[-+>]\s|\d+[.)]\s)", text):
        return re.sub(r"^(\s*)([#\-+>]|\d+)", r"\1\\\2", text, count=1)
    return text


def cell_text(text):
    return text.replace("|", "\\|").replace("\n", "<br>").strip()


def md_table(rows):
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(cell_text(c) for c in rows[0]) + " |",
           "|" + "|".join(["---"] * width) + "|"]
    for r in rows[1:]:
        out.append("| " + " | ".join(cell_text(c) for c in r) + " |")
    return "\n".join(out)


def wrap(text, bold, italic):
    if not text.strip():
        return text
    lead = text[:len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    core = text.strip()
    if bold and italic:
        core = "***%s***" % core
    elif bold:
        core = "**%s**" % core
    elif italic:
        core = "*%s*" % core
    return lead + core + trail


class Raw(str):
    """Markdown written as is: an image link, or a tracked-change marker. Never escaped, never
    merged with the text around it."""


# Where embedded images are saved: a folder beside the output file, set by main(). None when
# the Markdown goes to stdout, and then images are counted as dropped, as before.
MEDIA = {"dir": None, "link": None, "names": {}}


def save_media(z, member, alt, rep):
    """Copy one image out of an Office package beside the Markdown, and return the Markdown that
    links it, or None when there is nowhere to save it or the part is missing."""
    if not MEDIA["dir"] or member not in z.namelist():
        rep.drop("images")
        return None
    name = MEDIA["names"].get(member)
    if name is None:
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", member.rsplit("/", 1)[-1]) or "image"
        name, k = base, 1
        while name in MEDIA["names"].values():
            stem, dot, ext = base.rpartition(".")
            name = "%s-%d.%s" % (stem, k, ext) if dot else "%s-%d" % (base, k)
            k += 1
        os.makedirs(MEDIA["dir"], exist_ok=True)
        with open(os.path.join(MEDIA["dir"], name), "wb") as fh:
            fh.write(z.read(member))
        MEDIA["names"][member] = name
    rep.keep("images saved")
    alt = re.sub(r"[\[\]\n]+", " ", alt or "").strip() or "image"
    return Raw("![%s](%s/%s)" % (alt, MEDIA["link"], name))


def render_segments(segs):
    """segs: list of (text, bold, italic, href). Merge neighbours with equal formatting."""
    merged = []
    for t, b, i, h in segs:
        if merged and merged[-1][1:] == (b, i, h) and not isinstance(t, Raw) and not isinstance(merged[-1][0], Raw):
            merged[-1] = (merged[-1][0] + t, b, i, h)
        else:
            merged.append((t, b, i, h))
    out = []
    for t, b, i, h in merged:
        if isinstance(t, Raw):
            out.append(str(t))
            continue
        piece = wrap(md_escape(t), b, i)
        if h:
            piece = "[%s](%s)" % (piece.strip(), h.replace(" ", "%20").replace(")", "%29"))
        out.append(piece)
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def read_rels(z, path):
    rels = {}
    if path in z.namelist():
        for rel in ET.fromstring(z.read(path)).iter(PKG_REL + "Relationship"):
            rels[rel.get("Id")] = (rel.get("Target"), rel.get("Type", ""), rel.get("TargetMode", ""))
    return rels


def resolve(base_dir, target):
    if target.startswith("/"):
        return target.lstrip("/")
    parts = (base_dir.rstrip("/") + "/" + target).split("/")
    stack = []
    for p in parts:
        if p == "..":
            if stack:
                stack.pop()
        elif p and p != ".":
            stack.append(p)
    return "/".join(stack)


def truthy(el, attr=W + "val"):
    if el is None:
        return False
    v = el.get(attr)
    return v is None or v not in ("0", "false", "off", "none")


def span_of(value, cap):
    """A cell's column span, from 1 to the format's own limit (Word: 63 columns; HTML: colspan
    1000), so a damaged or hostile value can't make a row of a billion cells."""
    v = (value or "1").strip()
    return min(int(v), cap) if v.isascii() and v.isdigit() and int(v) > 0 else 1


# Every package opened during a conversion, closed by main() when it ends: a nested function
# that keeps the ZipFile alive would otherwise hold the file open on Windows until garbage
# collection, so it couldn't be deleted or overwritten.
OPEN_ZIPS = []


def close_zips():
    while OPEN_ZIPS:
        OPEN_ZIPS.pop().close()


def open_zip(path, kind):
    try:
        z = zipfile.ZipFile(str(path))
        OPEN_ZIPS.append(z)
    except zipfile.BadZipFile:
        with open(str(path), "rb") as fh:
            if fh.read(8) == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
                # Office saves a password-protected .docx/.pptx/.xlsx as a compound file holding
                # the encrypted package, not as a zip
                sys.exit("error: %s is password-protected (or an old binary Office file). Open it, remove "
                         "the password or save it as %s, and rerun." % (path, kind))
        sys.exit("error: %s is not a valid %s file (not a zip package). If it is an old binary "
                 "Office file, save it as %s first." % (path, kind, kind))
    if any(info.flag_bits & 0x1 for info in z.infolist()):
        sys.exit("error: %s has encrypted parts, which Office never writes; it is damaged, or was "
                 "zipped with a password by another tool" % path)
    return z


# ---------------------------------------------------------------- docx

def docx_to_md(path, rep):
    z = open_zip(path, ".docx")
    names = set(z.namelist())
    if "word/document.xml" not in names:
        sys.exit("error: %s has no word/document.xml; it is not a Word document" % path)
    styles = {}
    style_num = {}
    if "word/styles.xml" in names:
        for st in ET.fromstring(z.read("word/styles.xml")).iter(W + "style"):
            sid = st.get(W + "styleId")
            name_el = st.find(W + "name")
            name = (name_el.get(W + "val") if name_el is not None else sid or "").lower()
            ppr = st.find(W + "pPr")
            outline = None
            if ppr is not None:
                ol = ppr.find(W + "outlineLvl")
                if ol is not None:
                    outline = int(ol.get(W + "val", "9"))
                num = ppr.find(W + "numPr")
                if num is not None and num.find(W + "numId") is not None:
                    style_num[sid] = num.find(W + "numId").get(W + "val")
            styles[sid] = (name, outline)
    num_fmt = {}
    if "word/numbering.xml" in names:
        root = ET.fromstring(z.read("word/numbering.xml"))
        abstract = {}
        for an in root.iter(W + "abstractNum"):
            lv = {}
            for lvl in an.iter(W + "lvl"):
                f = lvl.find(W + "numFmt")
                lv[lvl.get(W + "ilvl")] = f.get(W + "val") if f is not None else "bullet"
            abstract[an.get(W + "abstractNumId")] = lv
        for num in root.iter(W + "num"):
            ref = num.find(W + "abstractNumId")
            if ref is not None:
                num_fmt[num.get(W + "numId")] = abstract.get(ref.get(W + "val"), {})
    rels = read_rels(z, "word/_rels/document.xml.rels")

    if "word/comments.xml" in names:
        rep.drop("comments", len(list(ET.fromstring(z.read("word/comments.xml")).iter(W + "comment"))))
    if "word/footnotes.xml" in names:
        fns = [f for f in ET.fromstring(z.read("word/footnotes.xml")).iter(W + "footnote")
               if int(f.get(W + "id", "0")) > 0]
        rep.drop("footnotes", len(fns))
    rep.drop("charts", len([n for n in names if re.match(r"word/charts/chart\d+\.xml$", n)]))
    for n in names:
        if re.match(r"word/(header|footer)\d*\.xml$", n):
            if "".join(t.text or "" for t in ET.fromstring(z.read(n)).iter(W + "t")).strip():
                rep.drop("headers/footers")
                break

    body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    if body is None:
        sys.exit("error: %s has no document body (word/document.xml has no w:body in the WordprocessingML "
                 "namespace); it is not a Word document, or it is damaged" % path)

    def para_segments(p, in_table=False):
        segs = []
        field = {"instr": "", "href": None, "state": None}

        def run(r, href):
            rpr = r.find(W + "rPr")
            b = rpr is not None and truthy(rpr.find(W + "b"))
            i = rpr is not None and truthy(rpr.find(W + "i"))
            for ch in r:
                tag = ch.tag
                if tag == W + "fldChar":
                    kind = ch.get(W + "fldCharType")
                    if kind == "begin":
                        field.update(instr="", href=None, state="instr")
                    elif kind == "separate":
                        m = re.search(r'HYPERLINK\s+"([^"]+)"', field["instr"])
                        field["href"] = m.group(1) if m else None
                        field["state"] = "result"
                    elif kind == "end":
                        field.update(state=None, href=None)
                elif tag == W + "instrText":
                    field["instr"] += ch.text or ""
                elif field["state"] == "instr":
                    continue
                elif tag in (W + "t", W + "delText"):
                    segs.append((ch.text or "", b, i, href or field["href"]))
                elif tag == W + "tab":
                    segs.append((" ", False, False, None))
                elif tag in (W + "br", W + "cr"):
                    segs.append(("\n", False, False, None))
                elif tag in (W + "pict", W + "object"):
                    rep.drop("images")
                elif tag == W + "drawing":
                    uris = [g.get("uri") or "" for g in ch.iter(A + "graphicData")]
                    blips = list(ch.iter(A + "blip"))
                    if blips:
                        rid = blips[0].get(R + "embed")
                        target = rels.get(rid, (None, "", ""))
                        alt = next((d.get("descr") or d.get("name") for d in ch.iter() if d.tag.endswith("}docPr")), "")
                        link = save_media(z, resolve("word", target[0]), alt, rep) if target[0] and target[2] != "External" else None
                        if link is None and not target[0]:
                            rep.drop("images")
                        elif link:
                            segs.append((link, False, False, None))
                    elif not any("chart" in u for u in uris):  # charts are counted from word/charts
                        rep.drop("shapes/text boxes")

        def walk(node, href):
            for ch in node:
                if ch.tag == W + "r":
                    run(ch, href)
                elif ch.tag == W + "hyperlink":
                    rid = ch.get(R + "id")
                    target = rels.get(rid, (None,))[0] if rid else None
                    walk(ch, target)
                elif ch.tag == W + "ins":
                    # Pending, not accepted: shown in CriticMarkup so a reader sees it is a
                    # proposal, and nothing is silently settled.
                    rep.keep("tracked insertions shown as {++ ++}")
                    segs.append((Raw("{++"), False, False, None))
                    walk(ch, href)
                    segs.append((Raw("++}"), False, False, None))
                elif ch.tag == W + "del":
                    rep.keep("tracked deletions shown as {-- --}")
                    segs.append((Raw("{--"), False, False, None))
                    walk(ch, href)
                    segs.append((Raw("--}"), False, False, None))
                elif ch.tag in (W + "smartTag", W + "sdt", W + "sdtContent", W + "fldSimple"):
                    walk(ch, href)
        walk(p, None)
        text = render_segments(segs)
        return text.replace("\n", "<br>" if in_table else "  \n")

    def heading_level(p):
        ppr = p.find(W + "pPr")
        if ppr is None:
            return None
        ol = ppr.find(W + "outlineLvl")
        if ol is not None and int(ol.get(W + "val", "9")) < 6:
            return int(ol.get(W + "val")) + 1
        ps = ppr.find(W + "pStyle")
        if ps is None:
            return None
        name, outline = styles.get(ps.get(W + "val"), (ps.get(W + "val", "").lower(), None))
        if name == "title":
            return 1
        m = re.match(r"heading\s*(\d)", name)
        if m:
            return min(int(m.group(1)), 6)
        if outline is not None and outline < 6:
            return outline + 1
        return None

    def list_info(p):
        ppr = p.find(W + "pPr")
        if ppr is None:
            return None
        num = ppr.find(W + "numPr")
        num_id, ilvl = None, "0"
        if num is not None:
            nid = num.find(W + "numId")
            lvl = num.find(W + "ilvl")
            num_id = nid.get(W + "val") if nid is not None else None
            ilvl = lvl.get(W + "val") if lvl is not None else "0"
        ps = ppr.find(W + "pStyle")
        sid = ps.get(W + "val") if ps is not None else None
        if num_id is None and sid in style_num:
            num_id = style_num[sid]
        if num_id is None or num_id == "0":
            name = styles.get(sid, ("", None))[0] if sid else ""
            if "list bullet" in name:
                return ("bullet", 0)
            if "list number" in name:
                return ("decimal", 0)
            return None
        fmt = num_fmt.get(num_id, {}).get(ilvl, "bullet")
        return (fmt, min(max(int(ilvl), 0), 8))  # Word's list levels are 0 to 8

    def table_md(tbl):
        rows = []
        for tr in tbl.findall(W + "tr"):
            row = []
            for tc in tr.findall(W + "tc"):
                tcpr = tc.find(W + "tcPr")
                parts = []
                for p in tc.iter(W + "p"):
                    t = para_segments(p, in_table=True)
                    if t:
                        parts.append(t)
                text = "<br>".join(parts)
                if tcpr is not None:
                    vm = tcpr.find(W + "vMerge")
                    if vm is not None and vm.get(W + "val") in (None, "continue"):
                        text = ""
                row.append(text)
                if tcpr is not None and tcpr.find(W + "gridSpan") is not None:
                    row.extend([""] * (span_of(tcpr.find(W + "gridSpan").get(W + "val"), 63) - 1))
            rows.append(row)
        if len(list(tbl.iter(W + "tbl"))) > 1:
            rep.notes.append("a nested table was flattened into its parent cell")
        rep.keep("tables")
        return md_table(rows)

    def raw_text(p):
        return "".join((n.text or "") if n.tag == W + "t" else "\t" for n in p.iter()
                       if n.tag in (W + "t", W + "tab"))

    def style_name(p):
        ppr = p.find(W + "pPr")
        ps = ppr.find(W + "pStyle") if ppr is not None else None
        if ps is None:
            return ""
        sid = ps.get(W + "val", "")
        return styles.get(sid, (sid.lower(), None))[0]

    def code_text(p):
        """Text of a code paragraph: line breaks and tabs kept, no inline formatting or escaping."""
        return "".join((n.text or "") if n.tag == W + "t" else "\t" if n.tag == W + "tab" else "\n"
                       for n in p.iter() if n.tag in (W + "t", W + "tab", W + "br", W + "cr"))

    def run_size(p):
        """(largest font size in half-points, every text run bold?) for unstyled documents."""
        sizes, bold = [0], True
        for r in p.iter(W + "r"):
            if not "".join(t.text or "" for t in r.iter(W + "t")).strip():
                continue
            rpr = r.find(W + "rPr")
            sz = rpr.find(W + "sz") if rpr is not None else None
            sizes.append(int(sz.get(W + "val", "0")) if sz is not None else 0)
            bold = bold and rpr is not None and truthy(rpr.find(W + "b"))
        return max(sizes), bold

    # Documents saved without heading styles (pasted text, textutil, some exporters) mark
    # headings with size and bold only. Infer levels from that, and say so.
    inferred = {}
    top = [el for el in body if el.tag == W + "p"]
    if not any(heading_level(p) for p in top):
        weight = {}
        info = {}
        for p in top:
            t = raw_text(p).strip()
            if not t:
                continue
            sz, b = run_size(p)
            info[id(p)] = (sz, b, t)
            weight[sz] = weight.get(sz, 0) + len(t)
        if weight:
            body_sz = max(weight, key=weight.get)
            bigger = sorted({sz for sz, b, t in info.values() if sz > body_sz and len(t) <= 120}, reverse=True)
            for p in top:
                if id(p) not in info:
                    continue
                sz, b, t = info[id(p)]
                if len(t) > 120 or t.endswith((".", ":", ";")) and sz <= body_sz:
                    continue
                if sz in bigger:  # bold alone is not enough: bold table cells and labels look the same
                    inferred[id(p)] = min(bigger.index(sz) + 1, 6)
            if inferred:
                rep.notes.append("no heading styles in the document; %d heading(s) inferred from font "
                                 "size and bold, so check the levels" % len(inferred))

    blocks = []
    counters = {}
    prev_list = False
    for el in body:
        if el.tag == W + "p":
            text = para_segments(el)
            lvl = heading_level(el) or inferred.get(id(el))
            li = list_info(el)
            if not li and not lvl:
                raw = raw_text(el)
                m = re.match(r"^\s*([\u2022\u25e6\u25aa\u2023\u00b7\u25cf\u25cb\u25a0\u2013])\s*", raw)
                m2 = re.match(r"^\s*(\d{1,3})[.)]?\t", raw)
                if m or m2:
                    li = ("bullet", 0) if m else ("decimal", 0)
                    text = re.sub(r"^\s*(\S{1,4})\s+", "", text, count=1)
                    rep.notes.append("list items written as typed bullets or numbers were turned into a Markdown list") \
                        if not any("typed bullets" in n for n in rep.notes) else None
            if lvl and id(el) in inferred:
                text = re.sub(r"^\*{1,3}(.*?)\*{1,3}$", r"\1", text)
            if not text:
                prev_list = False if not li else prev_list
                continue
            sname = "" if lvl or li else style_name(el)
            if re.match(r"(source ?code|code|html preformatted|preformatted text|macro text)$", sname):
                # one code block may be one paragraph with line breaks or a run of one-line paragraphs
                if blocks and blocks[-1][0] == "code":
                    blocks[-1] = ("code", blocks[-1][1] + "\n" + code_text(el))
                else:
                    blocks.append(("code", code_text(el)))
                    rep.keep("code blocks")
                prev_list = False
            elif "quote" in sname or sname == "block text":
                blocks.append(("block", "> " + text.replace("\n", "\n> ")))
                prev_list = False
            elif lvl:
                rep.keep("headings")
                blocks.append(("block", "#" * lvl + " " + text.replace("  \n", " ")))
                prev_list = False
                counters = {}
            elif li:
                fmt, depth = li
                if not prev_list:
                    counters = {}
                for d in list(counters):
                    if d > depth:
                        del counters[d]
                kind = "ul" if fmt in ("bullet", "none") else "ol"
                prev_kind, count = counters.get(depth, (kind, 0))
                count = count + 1 if prev_kind == kind else 1
                counters[depth] = (kind, count)
                marker = "-" if kind == "ul" else "%d." % count
                blocks.append(("list", "   " * depth + marker + " " + text))
                rep.keep("list items")
                prev_list = True
            else:
                blocks.append(("block", escape_line_start(text)))
                prev_list = False
        elif el.tag == W + "tbl":
            blocks.append(("block", table_md(el)))
            prev_list = False
        elif el.tag == W + "sdt":
            content = el.find(W + "sdtContent")
            if content is not None:
                for p in content.iter(W + "p"):
                    t = para_segments(p)
                    if t:
                        blocks.append(("block", t))
    out = []
    for k, (kind, text) in enumerate(blocks):
        if k and not (kind == "list" and blocks[k - 1][0] == "list"):
            out.append("")
        if kind == "code":
            fence = "```"
            while fence in text:
                fence += "`"
            text = fence + "\n" + text + "\n" + fence
        out.append(text)
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- pptx

def pptx_to_md(path, rep):
    z = open_zip(path, ".pptx")
    names = set(z.namelist())
    if "ppt/presentation.xml" not in names:
        sys.exit("error: %s has no ppt/presentation.xml; it is not a PowerPoint file" % path)
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    prels = read_rels(z, "ppt/_rels/presentation.xml.rels")
    slide_paths = []
    lst = pres.find(P + "sldIdLst")
    for sid in (lst if lst is not None else []):
        target = prels.get(sid.get(R + "id"), (None,))[0]
        if target:
            slide_paths.append(resolve("ppt", target))
    rep.drop("comments", len([n for n in names if re.match(r"ppt/comments/.*\.xml$", n)]))

    def para_text(p, rels):
        segs = []
        for ch in p:
            if ch.tag in (A + "r", A + "fld"):
                rpr = ch.find(A + "rPr")
                b = rpr is not None and rpr.get("b") in ("1", "true")
                i = rpr is not None and rpr.get("i") in ("1", "true")
                href = None
                if rpr is not None and rpr.find(A + "hlinkClick") is not None:
                    rid = rpr.find(A + "hlinkClick").get(R + "id")
                    tgt = rels.get(rid)
                    if tgt and tgt[2] == "External":
                        href = tgt[0]
                t = ch.find(A + "t")
                segs.append((t.text or "" if t is not None else "", b, i, href))
            elif ch.tag == A + "br":
                segs.append((" ", False, False, None))
        return render_segments(segs)

    def shape_lines(sp, rels, is_body):
        lines = []
        tx = sp.find(P + "txBody")
        if tx is None:
            return lines
        for p in tx.findall(A + "p"):
            text = para_text(p, rels)
            if not text:
                continue
            ppr = p.find(A + "pPr")
            lvl = min(max(int(ppr.get("lvl", "0")), 0), 8) if ppr is not None else 0  # PowerPoint's are 0 to 8
            bullet = is_body
            if ppr is not None:
                if ppr.find(A + "buNone") is not None:
                    bullet = False
                elif ppr.find(A + "buChar") is not None or ppr.find(A + "buAutoNum") is not None:
                    bullet = True
            lines.append(("  " * lvl + "- " + text) if bullet else escape_line_start(text))
        return lines

    def walk_tree(tree, rels, title_box, lines):
        for sp in tree:
            tag = sp.tag
            if tag == P + "sp":
                ph = sp.find(P + "nvSpPr/" + P + "nvPr/" + P + "ph")
                ph_type = ph.get("type", "body") if ph is not None else None
                if ph_type in ("title", "ctrTitle"):
                    title_box.append(" ".join(para_text(p, rels) for p in sp.iter(A + "p")).strip())
                    continue
                if ph_type in ("sldNum", "dt", "ftr"):
                    continue
                got = shape_lines(sp, rels, ph_type in ("body", "obj"))
                if got:
                    if lines:
                        lines.append("")
                    lines.extend(got)
            elif tag == P + "pic":
                blip = next(iter(sp.iter(A + "blip")), None)
                target = rels.get(blip.get(R + "embed"), (None, "", "")) if blip is not None else (None, "", "")
                cnv = next((d for d in sp.iter() if d.tag.endswith("}cNvPr")), None)
                alt = (cnv.get("descr") or cnv.get("name")) if cnv is not None else ""
                link = save_media(z, resolve(base, target[0]), alt, rep) if target[0] and target[2] != "External" else None
                if link:
                    if lines:
                        lines.append("")
                    lines.append(str(link))
                elif not target[0]:
                    rep.drop("images")
            elif tag == P + "graphicFrame":
                tbl = sp.find(".//" + A + "tbl")
                if tbl is not None:
                    rows = []
                    for tr in tbl.findall(A + "tr"):
                        rows.append([" ".join(para_text(p, rels) for p in tc.iter(A + "p")).strip()
                                     for tc in tr.findall(A + "tc")])
                    lines.extend(["", md_table(rows)])
                    rep.keep("tables")
                else:
                    gd = sp.find(".//" + A + "graphicData")
                    uri = gd.get("uri", "") if gd is not None else ""
                    rep.drop("charts" if "chart" in uri else "diagrams/objects")
            elif tag == P + "grpSp":
                walk_tree(sp, rels, title_box, lines)
            elif tag == P + "cxnSp":
                continue

    out = []
    for n, sp_path in enumerate(slide_paths, 1):
        if sp_path not in names:
            rep.notes.append("slide %d is listed but missing from the file" % n)
            continue
        root = ET.fromstring(z.read(sp_path))
        base = sp_path.rsplit("/", 1)[0]
        rels_path = base + "/_rels/" + sp_path.rsplit("/", 1)[1] + ".rels"
        rels = read_rels(z, rels_path)
        tree = root.find(P + "cSld/" + P + "spTree")
        title_box, lines = [], []
        if tree is not None:
            walk_tree(tree, rels, title_box, lines)
        title = title_box[0] if title_box and title_box[0] else "(untitled)"
        hidden = " (hidden)" if root.get("show") == "0" else ""
        out.append("## Slide %d: %s%s" % (n, title, hidden))
        rep.keep("slides")
        if lines:
            out.append("")
            out.extend(lines)
        for tgt, typ, _ in rels.values():
            if typ.endswith("/notesSlide"):
                npath = resolve(base, tgt)
                if npath in names:
                    nroot = ET.fromstring(z.read(npath))
                    notes = []
                    for sp in nroot.iter(P + "sp"):
                        ph = sp.find(P + "nvSpPr/" + P + "nvPr/" + P + "ph")
                        if ph is not None and ph.get("type") == "body":
                            notes += [para_text(p, rels) for p in sp.iter(A + "p")]
                    notes = [t for t in notes if t]
                    if notes:
                        rep.keep("slides with speaker notes")
                        out.append("")
                        out.append("> **Speaker notes:** " + notes[0])
                        for t in notes[1:]:
                            out.append(">")
                            out.append("> " + t)
        out.append("")
    if not slide_paths:
        rep.notes.append("the presentation has no slides")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- xlsx

BUILTIN_DATE_FMTS = set(range(14, 23)) | {45, 46, 47}


def cell_ref(ref):
    """(row, column) from a cell reference such as B7 or $B$7, counting from 0; None for anything
    else, so a damaged reference skips that cell rather than the sheet."""
    m = re.fullmatch(r"\$?([A-Za-z]{1,3})\$?(\d{1,7})", ref.strip())
    if not m or int(m.group(2)) < 1:
        return None
    n = 0
    for ch in m.group(1).upper():
        n = n * 26 + (ord(ch) - 64)
    return int(m.group(2)) - 1, n - 1


def xlsx_to_md(path, rep, max_rows=0):
    z = open_zip(path, ".xlsx")
    names = set(z.namelist())
    if "xl/workbook.xml" not in names:
        sys.exit("error: %s has no xl/workbook.xml; it is not an Excel workbook" % path)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    pr = wb.find(S + "workbookPr")
    epoch = datetime(1904, 1, 1) if (pr is not None and pr.get("date1904") in ("1", "true")) \
        else datetime(1899, 12, 30)
    shared = []
    if "xl/sharedStrings.xml" in names:
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(S + "si"):
            # plain <t>, or rich-text runs <r><t>; phonetic hints <rPh> are skipped
            parts = [si.find(S + "t")] + [r.find(S + "t") for r in si.findall(S + "r")]
            shared.append("".join(t.text or "" for t in parts if t is not None))
    date_styles = set()
    if "xl/styles.xml" in names:
        st = ET.fromstring(z.read("xl/styles.xml"))
        custom = {}
        nf = st.find(S + "numFmts")
        for f in (nf if nf is not None else []):
            code = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", f.get("formatCode", "")).lower()
            custom[int(f.get("numFmtId"))] = bool(re.search(r"[dmyh]", code))
        xfs = st.find(S + "cellXfs")
        for k, xf in enumerate(xfs if xfs is not None else []):
            fid = int(xf.get("numFmtId", "0"))
            if fid in BUILTIN_DATE_FMTS or custom.get(fid):
                date_styles.add(k)
    rels = read_rels(z, "xl/_rels/workbook.xml.rels")
    rep.drop("charts", len([n for n in names if re.match(r"xl/charts/chart\d+\.xml$", n)]))
    rep.drop("images", len([n for n in names if n.startswith("xl/media/")]))
    for n in names:
        if re.match(r"xl/comments\d*\.xml$", n):
            rep.drop("comments", len(list(ET.fromstring(z.read(n)).iter(S + "comment"))))

    out = []
    sheets = wb.find(S + "sheets")
    for sh in (sheets if sheets is not None else []):
        name = sh.get("name")
        target = rels.get(sh.get(R + "id"), (None,))[0]
        if not target:
            continue
        spath = resolve("xl", target)
        if spath not in names:
            continue
        root = ET.fromstring(z.read(spath))
        grid = {}
        formulas = 0
        for c in root.iter(S + "c"):
            ref = c.get("r")
            if not ref:
                continue
            rc = cell_ref(ref)
            if rc is None:
                continue
            row, col = rc
            t = c.get("t", "n")
            v = c.find(S + "v")
            if c.find(S + "f") is not None:
                formulas += 1
            if t == "s" and v is not None:
                val = shared[int(v.text)] if int(v.text) < len(shared) else ""
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(S + "t"))
            elif t == "b" and v is not None:
                val = "TRUE" if v.text == "1" else "FALSE"
            elif v is not None and v.text is not None:
                val = v.text
                if t == "n" and int(c.get("s", "0")) in date_styles:
                    try:
                        d = epoch + timedelta(days=float(val))
                        val = d.strftime("%Y-%m-%d") if float(val) == int(float(val)) \
                            else d.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, OverflowError):
                        pass
            else:
                continue
            if val != "":
                grid[(row, col)] = val
        state = sh.get("state")
        label = "## %s%s" % (name, " (%s)" % state if state in ("hidden", "veryHidden") else "")
        out.append(label)
        out.append("")
        merges = root.find(S + "mergeCells")
        if merges is not None and len(merges):
            rep.notes.append("sheet '%s' has %d merged range(s); the value sits in the first cell only"
                             % (name, len(merges)))
        if formulas:
            rep.drop("formulas (cached values kept)", formulas)
        if not grid:
            out.append("*(empty sheet)*")
            out.append("")
            continue
        # Only the rows and columns that hold a value: one stray cell at ZZZ999999 must not
        # build a grid of a million empty rows.
        rows_used = sorted({r for r, _ in grid})
        cols_used = sorted({c for _, c in grid})
        gaps = cols_used[-1] - cols_used[0] + 1 - len(cols_used)
        if gaps:
            rep.notes.append("sheet '%s': %d empty column(s) left out" % (name, gaps))
        table = [[grid.get((r, c), "") for c in cols_used] for r in rows_used]
        if max_rows and len(table) > max_rows + 1:
            rep.notes.append("sheet '%s' cut to %d of %d data rows (--max-rows)"
                             % (name, max_rows, len(table) - 1))
            table = table[:max_rows + 1]
        out.append(md_table(table))
        out.append("")
        rep.keep("sheets")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- html

class HTMLToMD(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg", "head", "iframe", "object", "canvas", "nav"}
    BLOCK = {"p", "div", "section", "article", "header", "footer", "main", "aside", "nav",
             "figure", "figcaption", "address", "form", "fieldset", "dl", "dt", "dd", "hr"}

    INLINE = {"strong": "**", "b": "**", "em": "*", "i": "*", "code": "`"}

    def __init__(self, rep):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.inline_stack = []
        self.in_code = 0
        self.rep = rep
        self.lines = []
        self.buf = []
        self.skip = 0
        self.lists = []  # stack of ["ul"|"ol", counter]
        self.quote = 0
        self.pre = False
        self.pre_buf = []
        self.pre_lang = ""
        self.links = []
        self.table = None  # list of rows
        self.cell = None
        self.heading = 0
        self.li_prefix = None

    # output helpers
    def text_target(self):
        return self.cell if self.cell is not None else self.buf

    def flush(self):
        text = re.sub(r"[ \t\r\n]+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not text and self.li_prefix is None:
            return
        if self.heading:
            line = "#" * self.heading + " " + text
        elif self.li_prefix is not None:
            line = self.li_prefix + text
            self.li_prefix = None
        else:
            line = escape_line_start(text)
        if self.quote:
            line = "> " * self.quote + line
        item = re.compile(r"^(> )*\s*(-|\d+\.) ")
        both_items = self.lines and item.match(self.lines[-1]) and item.match(line)
        if self.lines and self.lines[-1] != "" and not both_items:
            self.lines.append("")
        self.lines.append(line)

    def blank(self):
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if self.pre:
            if tag == "code":
                m = re.search(r"language-([\w+-]+)", a.get("class") or "")
                if m:
                    self.pre_lang = m.group(1)
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.cell is None:
            self.flush()
            self.heading = int(tag[1])
            self.rep.keep("headings")
        elif tag in self.BLOCK and self.cell is None:
            self.flush()
            if tag == "hr":
                self.blank()
                self.lines.append("---")
        elif tag == "br":
            self.text_target().append("<br>" if self.cell is not None else "  \n")
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.append([tag, 0])
        elif tag == "li":
            self.flush()
            if self.lists:
                self.lists[-1][1] += 1
                kind, count = self.lists[-1]
                indent = "   " * (len(self.lists) - 1)
                self.li_prefix = indent + ("%d. " % count if kind == "ol" else "- ")
                self.rep.keep("list items")
        elif tag == "blockquote":
            self.flush()
            self.quote += 1
        elif tag == "pre":
            self.flush()
            self.pre, self.pre_buf, self.pre_lang = True, [], ""
        elif tag in self.INLINE:
            self.open_inline(tag)
        elif tag == "a":
            href = a.get("href") or ""
            if href and not href.lower().startswith(("javascript:", "data:")):
                self.text_target().append("[")
                self.links.append(href)
            else:
                self.links.append(None)
        elif tag == "img":
            src = a.get("src") or ""
            alt = a.get("alt") or ""
            if src.startswith("data:") or not src:
                self.rep.drop("images (embedded data)")
            else:
                self.text_target().append("![%s](%s)" % (md_escape(alt), src))
                self.rep.keep("image links")
        elif tag == "table":
            self.flush()
            if self.table is not None:
                self.rep.notes.append("a nested table was flattened into its parent cell")
            else:
                self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            if not self.table:
                self.table.append([])
            self.cell = []
            self._span = span_of(a.get("colspan"), 1000)

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if self.pre:
            if tag == "pre":
                code = "".join(self.pre_buf).strip("\n")
                self.blank()
                self.lines.append("```" + self.pre_lang)
                self.lines.extend(code.split("\n"))
                self.lines.append("```")
                self.pre = False
                self.rep.keep("code blocks")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.cell is None:
            self.flush()
            self.heading = 0
        elif tag in self.BLOCK and self.cell is None:
            self.flush()
        elif tag in ("ul", "ol"):
            self.flush()
            if self.lists:
                self.lists.pop()
        elif tag == "li":
            self.flush()
        elif tag == "blockquote":
            self.flush()
            self.quote = max(0, self.quote - 1)
        elif tag in self.INLINE:
            self.close_inline(tag)
        elif tag == "a" and self.links:
            href = self.links.pop()
            if href:
                self.text_target().append("](%s)" % href.replace(" ", "%20"))
        elif tag in ("td", "th") and self.cell is not None and self.table is not None:
            text = re.sub(r"\s+", " ", "".join(self.cell)).strip()
            self.table[-1].append(text)
            self.table[-1].extend([""] * (getattr(self, "_span", 1) - 1))
            self.cell = None
        elif tag == "table" and self.table is not None:
            md = md_table(self.table)
            self.table = None
            if md:
                self.blank()
                self.lines.extend(md.split("\n"))
                self.rep.keep("tables")

    def handle_data(self, data):
        if self.skip:
            return
        if self.pre:
            self.pre_buf.append(data)
            return
        self.text_target().append(data if self.in_code else md_escape(data))

    def open_inline(self, tag):
        target = self.text_target()
        self.inline_stack.append((tag, target, len(target)))
        target.append(self.INLINE[tag])
        if tag == "code":
            self.in_code += 1

    def close_inline(self, tag):
        if tag == "code":
            self.in_code = max(0, self.in_code - 1)
        for k in range(len(self.inline_stack) - 1, -1, -1):
            if self.inline_stack[k][0] == tag:
                _, target, idx = self.inline_stack.pop(k)
                break
        else:
            return
        if idx >= len(target) or target is not self.text_target():
            return
        mark = self.INLINE[tag]
        content = "".join(target[idx + 1:])
        core = content.strip()
        lead = content[:len(content) - len(content.lstrip())]
        trail = content[len(content.rstrip()):]
        target[idx:] = [lead + mark + core + mark + trail] if core else [content]

    def result(self):
        self.flush()
        text = "\n".join(self.lines)
        text = re.sub(r"\[\s*\]\([^)]*\)", "", text)                  # links with no text
        return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def html_to_md(path, rep):
    raw = path.read_bytes()
    m = re.search(br'charset=["\']?([\w-]+)', raw[:2048], re.I)
    enc = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    try:
        text = raw.decode(enc, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    skipped = len(re.findall(r"<(script|style)\b", text, re.I))
    if skipped:
        rep.drop("scripts/styles", skipped)
    navs = len(re.findall(r"<nav\b", text, re.I))
    if navs:
        rep.drop("navigation menus", navs)
    parser = HTMLToMD(rep)
    parser.feed(text)
    parser.close()
    return parser.result()


def _html_text_to_md(text, rep):
    """HTML already decoded to text (an email body) -> Markdown, through the same parser."""
    skipped = len(re.findall(r"<(script|style)\b", text, re.I))
    if skipped:
        rep.drop("scripts/styles", skipped)
    parser = HTMLToMD(rep)
    parser.feed(text)
    parser.close()
    return parser.result()


# ---------------------------------------------------------------- email (.eml, .msg)

def _email_md(subject, rows, body_md, attachments, rep, note=None):
    """One email as Markdown: subject as the title, the headers as a table, the body, and the
    attachments listed by name and size, since their content is not converted."""
    out = ["# " + md_escape(subject or "(no subject)"), "", "| | |", "|---|---|"]
    for k, v in rows:
        if v:
            out.append("| %s | %s |" % (k, cell_text(md_escape(v))))
    out += ["", body_md.strip() or "_(no text body)_", ""]
    if attachments:
        out += ["## Attachments", ""]
        for name, size in attachments:
            out.append("- %s (%s)" % (md_escape(name or "unnamed"), _human_size(size)))
        out.append("")
        rep.drop("attachments (listed, not converted)", len(attachments))
    if note:
        rep.notes.append(note)
    rep.keep("emails", 1)
    return "\n".join(out).rstrip() + "\n"


def _email_text(text):
    """A plain-text email body as Markdown. Bullets and `> ` quoted replies already read as
    Markdown lists and quotes, so only a leading `#` (which would become a heading) and a
    line of `=` or `-` under text (which would turn that text into one) are escaped."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("#"):
            line = line.replace("#", "\\#", 1)
        elif re.fullmatch(r"\s*(=+|-{2,})\s*", line) and out and out[-1].strip():
            line = "\\" + line.strip()
        out.append(line)
    return "\n".join(out)


def _human_size(n):
    if n is None:
        return "size unknown"
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "bytes" else ("%.1f %s" % (n, unit))
        n /= 1024.0


def _part_text(part):
    """A text part's content. A charset Python doesn't know (a typo, or a vendor's own label) is
    read as UTF-8 with replacement characters, as html_to_md does, rather than lost."""
    try:
        return part.get_content()
    except LookupError:
        return (part.get_payload(decode=True) or b"").decode("utf-8", "replace")


def _unescape(text):
    """The email package keeps undecodable header bytes as surrogates, which can't be written as
    UTF-8. Read them as UTF-8, with a replacement character for any that aren't."""
    return text.encode("utf-8", "surrogateescape").decode("utf-8", "replace")


def _header(msg, name):
    """A header's decoded value, or its raw text when it won't parse: Python 3.9's email package
    raises on a malformed date or address that later versions keep."""
    try:
        return _unescape(str(msg.get(name, "")))
    except (TypeError, ValueError, IndexError, AttributeError, OverflowError):
        return _unescape(next((" ".join(str(v).split()) for k, v in msg.raw_items() if k.lower() == name.lower()), ""))


def eml_to_md(path, rep):
    """An RFC 5322 message (.eml): the plain-text part when there is one, else the HTML part."""
    import email
    from email import policy
    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    rows = [(h, _header(msg, h)) for h in ("From", "To", "Cc", "Date")]
    try:
        plain = msg.get_body(preferencelist=("plain",))
        html = msg.get_body(preferencelist=("html",))
        parts = list(msg.iter_attachments())
    except (AttributeError, TypeError, KeyError):
        # Python 3.9 fails inside get_body on a multipart message whose boundary never appears.
        # Read it as one text body, which is what the raw message holds.
        raw = msg.get_payload()
        rep.notes.append("the message's MIME parts could not be separated, so its body is the raw text")
        return _email_md(_header(msg, "Subject"), rows, _email_text(_unescape(raw) if isinstance(raw, str) else ""), [], rep)
    if plain is not None:
        body = _email_text(_part_text(plain))
        if html is not None:
            rep.drop("HTML alternative (the plain-text part was used)", 1)
    elif html is not None:
        body = _html_text_to_md(_part_text(html), rep)
    else:
        body = ""
    attachments = []
    for part in parts:
        payload = part.get_payload(decode=True)
        name = part.get_filename() or ("forwarded message" if part.get_content_type() == "message/rfc822" else None)
        attachments.append((name, len(payload) if payload is not None else None))
    return _email_md(_header(msg, "Subject"), rows, body, attachments, rep)


class _CFB:
    """A minimal, read-only reader for the Compound File Binary format Outlook saves .msg in.
    Bounded on every loop and offset, so a malformed file stops with an error, never a hang."""
    MAGIC = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"

    def __init__(self, data):
        import struct
        self.struct = struct
        if data[:8] != self.MAGIC or len(data) < 512:
            raise ValueError("not an Outlook .msg file (no compound-file header)")
        self.d = data
        self.ss = 1 << struct.unpack_from("<H", data, 30)[0]
        self.mss = 1 << struct.unpack_from("<H", data, 32)[0]
        if self.ss not in (512, 4096) or self.mss != 64:
            raise ValueError("unsupported compound-file sector size")
        nfat, dir_start = struct.unpack_from("<I", data, 44)[0], struct.unpack_from("<I", data, 48)[0]
        self.cutoff = struct.unpack_from("<I", data, 56)[0]
        minifat_start, nminifat, difat_start, ndifat = struct.unpack_from("<IIII", data, 60)
        difat = list(struct.unpack_from("<109I", data, 76))
        per = self.ss // 4
        # A FAT never needs more sectors than it takes to map the file, and lists each one once:
        # a repeated or looping list would otherwise build a table far larger than the file.
        nsect = len(data) // self.ss - 1
        need = -(-nsect // per)
        s, seen = difat_start, set()
        while ndifat and s < 0xFFFFFFFA and s not in seen and len(seen) < need:
            seen.add(s)
            vals = struct.unpack("<%dI" % per, self._sector(s))
            difat += vals[:-1]
            s, ndifat = vals[-1], ndifat - 1
        self.fat, used = [], set()
        for fs in difat[:min(nfat, need)]:
            if fs < 0xFFFFFFFA and fs not in used:
                used.add(fs)
                self.fat += struct.unpack("<%dI" % per, self._sector(fs))
        raw = self._chain(dir_start)
        self.entries = []
        for i in range(0, len(raw) - 127, 128):
            e = raw[i:i + 128]
            nlen = struct.unpack_from("<H", e, 64)[0]
            name = e[:max(0, min(nlen, 64) - 2)].decode("utf-16-le", "replace")
            kind = e[66]
            left, right, child = struct.unpack_from("<III", e, 68)
            start = struct.unpack_from("<I", e, 116)[0]
            size = struct.unpack_from("<I", e, 120)[0]  # the high half is zero for version 3 files
            self.entries.append({"name": name, "kind": kind, "left": left, "right": right, "child": child,
                                 "start": start, "size": size})
        if not self.entries or self.entries[0]["kind"] != 5:
            raise ValueError("compound file has no root entry")
        root = self.entries[0]
        self.ministream = self._chain(root["start"])[:root["size"]] if root["start"] < 0xFFFFFFFA else b""
        mf = self._chain(minifat_start) if nminifat else b""
        self.minifat = list(struct.unpack("<%dI" % (len(mf) // 4), mf[:len(mf) // 4 * 4]))

    def _sector(self, n):
        off = (n + 1) * self.ss
        if off + self.ss > len(self.d):
            raise ValueError("compound file is truncated or corrupt")
        return self.d[off:off + self.ss]

    def _chain(self, start, mini=False):
        fat, out, n, seen = (self.minifat if mini else self.fat), [], start, set()
        while n < 0xFFFFFFFA:
            if n >= len(fat) or n in seen:  # off the table, or a loop: each sector is read once
                raise ValueError("compound file has a broken sector chain")
            seen.add(n)
            if mini:
                off = n * self.mss
                out.append(self.ministream[off:off + self.mss])
            else:
                out.append(self._sector(n))
            n = fat[n]
        return b"".join(out)

    def children(self, idx):
        """The entries directly inside storage `idx`, by name."""
        out, stack, seen = {}, [self.entries[idx]["child"]], set()
        while stack:
            i = stack.pop()
            if i >= len(self.entries) or i in seen:
                continue
            seen.add(i)
            e = self.entries[i]
            out[e["name"]] = i
            stack += [e["left"], e["right"]]
        return out

    def read(self, i):
        e = self.entries[i]
        if e["size"] < self.cutoff:
            return self._chain(e["start"], mini=True)[:e["size"]]
        return self._chain(e["start"])[:e["size"]]


def _msg_props(cfb, idx):
    """The string and binary properties of one .msg storage, by four-hex-digit property id."""
    out = {}
    for name, i in cfb.children(idx).items():
        m = re.match(r"__substg1\.0_([0-9A-Fa-f]{4})([0-9A-Fa-f]{4})$", name)
        if not m or cfb.entries[i]["kind"] != 2:
            continue
        pid, ptype = m.group(1).upper(), m.group(2).upper()
        data = cfb.read(i)
        if ptype == "001F":
            out[pid] = data.decode("utf-16-le", "replace").rstrip("\x00")
        elif ptype == "001E":
            out[pid] = data.decode("cp1252", "replace").rstrip("\x00")
        elif ptype == "0102":
            out.setdefault(pid + ":bin", data)
    return out


def _msg_fixed(cfb, idx, header):
    """Fixed-size properties (times, integers) from a storage's __properties_version1.0."""
    import struct
    from datetime import datetime as _dt
    stream = cfb.children(idx).get("__properties_version1.0")
    if stream is None:
        return {}
    data, out = cfb.read(stream), {}
    for off in range(header, len(data) - 15, 16):
        tag, = struct.unpack_from("<I", data, off)
        ptype, pid = tag & 0xFFFF, "%04X" % (tag >> 16)
        if ptype == 0x0040:
            ft, = struct.unpack_from("<Q", data, off + 8)
            try:
                if ft:
                    out[pid] = _dt(1601, 1, 1) + timedelta(microseconds=ft // 10)
            except OverflowError:
                pass  # a time past the year 9999 is a placeholder or damage; the message has no date
        elif ptype == 0x0003:
            out[pid] = struct.unpack_from("<i", data, off + 8)[0]
    return out


def msg_to_md(path, rep):
    """An Outlook message (.msg): subject, sender, recipients, sent time, the text body (or the
    HTML body when there is no text one), and attachments listed by name and size."""
    try:
        cfb = _CFB(path.read_bytes())
    except ValueError as e:
        sys.exit("error: %s: %s" % (path, e))
    props = _msg_props(cfb, 0)
    fixed = _msg_fixed(cfb, 0, 32)
    to, cc = [], []
    for name, i in sorted(cfb.children(0).items()):
        if name.startswith("__recip_version1.0_"):
            rp, rf = _msg_props(cfb, i), _msg_fixed(cfb, i, 8)
            who = rp.get("3001", "")
            addr = rp.get("39FE") or rp.get("3003", "")
            label = ("%s <%s>" % (who, addr)) if who and addr and addr not in who else (who or addr)
            (cc if rf.get("0C15") == 2 else to).append(label)
    sender = props.get("0C1A", "")
    saddr = props.get("5D01") or props.get("0C1F") or props.get("0065", "")
    sent = fixed.get("0039") or fixed.get("0E06")
    rows = [("From", ("%s <%s>" % (sender, saddr)) if sender and saddr else (sender or saddr)),
            ("To", "; ".join(to) or props.get("0E04", "")), ("Cc", "; ".join(cc) or props.get("0E03", "")),
            ("Date", sent.strftime("%Y-%m-%d %H:%M UTC") if sent else "")]
    note = None
    if props.get("1000"):
        body = _email_text(props["1000"])
    elif props.get("1013") or props.get("1013:bin"):
        html = props.get("1013") or props["1013:bin"].decode("utf-8", "replace")
        body = _html_text_to_md(html, rep)
    else:
        body = ""
        if props.get("1009:bin"):
            note = "the message body is stored only as compressed RTF, which is not converted"
            rep.drop("RTF body", 1)
    attachments = []
    for name, i in sorted(cfb.children(0).items()):
        if name.startswith("__attach_version1.0_"):
            ap, kids = _msg_props(cfb, i), cfb.children(i)
            data = ap.get("3701:bin")
            fname = ap.get("3707") or ap.get("3704") or ("embedded message" if "__substg1.0_3701000D" in kids else None)
            attachments.append((fname, len(data) if data is not None else None))
    return _email_md(props.get("0037", ""), rows, body, attachments, rep, note)


# ---------------------------------------------------------------- csv / json / txt / pdf

def read_text(path, rep):
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        rep.notes.append("file is not UTF-8; read it as Latin-1, so check accented characters")
        return raw.decode("latin-1")


def csv_to_md(path, rep):
    text = read_text(path, rep)
    if path.suffix.lower() == ".tsv":
        dialect = csv.excel_tab
    else:
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        sys.exit("error: %s has no rows" % path)
    rep.keep("rows", len(rows) - 1)
    return md_table([[md_escape(c) for c in r] for r in rows]) + "\n"


def scalar(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def objects_table(items):
    keys = []
    for it in items:
        for k in it:
            if k not in keys:
                keys.append(k)
    rows = [keys] + [[md_escape(scalar(it.get(k))) for k in keys] for it in items]
    return md_table(rows)


def json_to_md(path, rep):
    try:
        data = json.loads(read_text(path, rep))
    except ValueError as e:
        sys.exit("error: %s is not valid JSON: %s" % (path, e))
    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
        rep.keep("rows", len(data))
        return objects_table(data) + "\n"
    if isinstance(data, list):
        return "\n".join("- " + md_escape(scalar(x)) for x in data) + "\n"
    if isinstance(data, dict):
        out, simple = [], []
        for k, v in data.items():
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                out += ["## %s" % k, "", objects_table(v), ""]
                rep.keep("tables")
            else:
                simple.append([md_escape(str(k)), md_escape(scalar(v))])
        if simple:
            out = [md_table([["Key", "Value"]] + simple), ""] + out
        return "\n".join(out).rstrip() + "\n"
    return md_escape(scalar(data)) + "\n"


_GAP = re.compile(r"\s{3,}")
_BULLET = re.compile(r"^[\u2022\u25e6\u25aa\u2023\u2043\u2013*-]\s+")
_CODEISH_RE = re.compile(r"[{};]|^\s*(def|function|class|SELECT|FROM)\b")


def _codeish(line):
    """Looks like code: diagram arrows, braces or semicolons, or a definition keyword.
    Arrows are a plain substring test (a regex for them reads like an HTML-comment filter)."""
    return "-->" in line or "==>" in line or bool(_CODEISH_RE.search(line))
_CODE_START = re.compile(r"^\s*(def |class |function |import |from \S+ import |SELECT |WITH |#include|package |func |public |const |let |var )")


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _cells(line):
    return [c for c in _GAP.split(line.strip()) if c]


def _col_starts(line):
    """Character positions where each of the line's text segments begins."""
    return set(m.start() for m in re.finditer(r"(?:(?<=^)|(?<= {3}))\S", line))


def _near(cols):
    """Column positions, widened by two characters either side."""
    return set(c + d for c in cols for d in (-2, -1, 0, 1, 2))


def _multi_column(page):
    """True when prose sits in side-by-side columns. Layout mode interleaves such columns line
    by line, so these pages are read in pdftotext's reading order instead. The signal: a text
    segment (after 3+ spaces, or a deep indent) starting at the same horizontal position on
    many lines, and carrying prose (3+ words on average). Table columns line up too, but
    their cells are short, so they don't qualify."""
    lines = [l for l in page.splitlines() if l.strip()]
    if len(lines) < 8:
        return False
    starts = {}
    for l in lines:
        for m in re.finditer(r"(?:^ {20,}|\S {3,})(\S.*?)(?= {3,}|$)", l):
            col = m.start(1) // 3  # bucket nearby positions together
            if col >= 7:  # at least ~20 characters in from the left margin
                starts.setdefault(col, []).append(len(m.group(1).split()))
    for words in starts.values():
        if len(words) >= max(6, 0.25 * len(lines)) and sum(words) / len(words) >= 3:
            return True
    return False


def _pdf_page_plain(page):
    """Reading-order text: paragraphs joined, nothing inferred."""
    paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", page)]
    out = []
    for p in paras:
        if p:
            out += [escape_line_start(md_escape(p)), ""]
    return out


_BBOX_PAGE = re.compile(r"<page\b.*?</page>", re.S)
_BBOX_WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', re.S)


def _word_rows(bbox_html):
    """Each physical line of every page as [(xMin, xMax, height, text)], keyed by its words.
    `pdftotext -bbox-layout` puts each table cell in a block of its own, so words are
    regrouped by their vertical position into the rows the layout reading shows."""
    import html as _html
    rows = {}
    for page in _BBOX_PAGE.findall(bbox_html):
        words = [(float(a), float(b), float(c), float(d), _html.unescape(t)) for a, b, c, d, t in _BBOX_WORD.findall(page)]
        words.sort(key=lambda w: (round(w[3]), w[0]))
        line, base = [], None
        for x0, y0, x1, y1, t in words + [(0, 0, 0, -99, "")]:
            if base is not None and abs(y1 - base) > 2:
                line.sort()
                key = " ".join(w[3] for w in line)
                if key and key not in rows:
                    rows[key] = line
                line = []
            base = y1
            if t:
                line.append((x0, x1, y1 - y0, t))
    return rows


def _finer_cells(region, boxes):
    """The region's rows split again from where each word sits on the page, or None.

    `pdftotext -layout` turns positions into characters, so two columns whose text sits closer
    than about two characters (a right-aligned amount beside a left-aligned date) come out one
    space apart and merge into one cell. A gap between words is a column when it is at least
    0.6 of the line's height (a word space is about a quarter of it) and, when the table has
    word spaces to compare with, at least twice the smallest of them, which keeps a monospace
    font's wide spaces from reading as columns. The new split is used only when every row then
    has the same number of cells, so a table that already came out right is never changed."""
    if not boxes:
        return None
    found = [boxes.get(" ".join(r.split())) for r in region]
    if not any(found):
        return None
    gaps = []
    for ws in found:
        if ws:
            h = sorted(w[2] for w in ws)[len(ws) // 2]
            gaps += [(b[0] - a[1], h) for a, b in zip(ws, ws[1:])]
    small = [g for g, h in gaps if g < 0.6 * h]
    floor = 2 * min(small) if small else 0
    rows = []
    for r, ws in zip(region, found):
        if not ws:
            rows.append(_cells(r))
            continue
        h = sorted(w[2] for w in ws)[len(ws) // 2]
        cells, cur = [], [ws[0][3]]
        for a, b in zip(ws, ws[1:]):
            g = b[0] - a[1]
            if g >= 0.6 * h and g >= floor:
                cells.append(" ".join(cur)); cur = []
            cur.append(b[3])
        cells.append(" ".join(cur))
        rows.append(cells)
    if len(set(len(c) for c in rows)) != 1 or rows == [_cells(r) for r in region]:
        return None
    return rows


def _pdf_page_md(page, rep, fine=None):
    """One page of `pdftotext -layout` text -> Markdown. Layout mode keeps line breaks,
    indentation and column alignment, which is what tables and lists are recovered from.
    `fine` maps a line's words to where each word sits on the page (see _finer_cells)."""
    lines = page.splitlines()
    out, i, n = [], 0, len(lines)
    while i < n:
        if not lines[i].strip():
            i += 1
            continue
        # A table: two or more lines that each split into 2+ cells on wide gaps, with single
        # blank lines allowed between rows (PDF row spacing often reads as one). A line whose
        # text starts under one of the table's columns is a wrapped cell, so it belongs too.
        if len(_cells(lines[i])) >= 2:
            cols = _col_starts(lines[i])
            region, rows, j = [], 0, i
            while j < n:
                line = lines[j]
                if line.strip() and len(_cells(line)) >= 2:
                    region.append(line); rows += 1; cols |= _col_starts(line); j += 1
                elif line.strip() and _col_starts(line) and _col_starts(line) <= _near(cols):
                    region.append(line); j += 1
                elif not line.strip() and j + 1 < n and len(_cells(lines[j + 1])) >= 2:
                    # After a blank line only a full row continues the table. A one-cell line
                    # there ("End of report.") is the next paragraph, not a wrapped cell.
                    j += 1
                else:
                    break
            if rows >= 2:
                widths = set(len(_cells(r)) for r in region)
                finer = _finer_cells(region, fine) if rows == len(region) else None
                if finer and (len(widths) != 1 or len(finer[0]) > len(_cells(region[0]))):
                    rep.keep("pdf table columns separated by position", 1)
                    cells = [[cell_text(md_escape(c)) for c in r] for r in finer]
                    width = len(cells[0])
                    out.append("| " + " | ".join(cells[0]) + " |")
                    out.append("|" + "---|" * width)
                    out += ["| " + " | ".join(r) + " |" for r in cells[1:]]
                    rep.keep("pdf tables", 1)
                elif len(widths) == 1 and rows == len(region):
                    cells = [[cell_text(md_escape(c)) for c in _cells(r)] for r in region]
                    width = len(cells[0])
                    out.append("| " + " | ".join(cells[0]) + " |")
                    out.append("|" + "---|" * width)
                    out += ["| " + " | ".join(r) + " |" for r in cells[1:]]
                    rep.keep("pdf tables", 1)
                else:
                    out += ["```text"] + [r.rstrip() for r in region] + ["```"]
                    rep.keep("pdf tables kept as aligned text", 1)
                out.append("")
                i = j
                continue
        # Otherwise a block of consecutive non-blank lines.
        block = []
        while i < n and lines[i].strip() and not (block and len(_cells(lines[i])) >= 2 and len(_cells(lines[i - 1])) >= 2):
            block.append(lines[i]); i += 1
        if not block:  # a single table-like line on its own
            block = [lines[i]]; i += 1
        base = min(_indent(l) for l in block)
        if (base >= 8 and any(_codeish(l) for l in block)) or _CODE_START.match(block[0]):
            out += ["```"] + [l[base:].rstrip() for l in block] + ["```", ""]
            rep.keep("pdf code blocks", 1)
            continue
        first, rest = block[0], block[1:]
        indented = [l for l in rest if _indent(l) > _indent(first)]
        bulleted = [l for l in block if _BULLET.match(l.strip())]
        if bulleted or (rest and len(indented) == len(rest) and len(first.split()) <= 8):
            items = block
            if not bulleted:  # a short lead line over an indented run: heading, then the list
                lead = first.strip()
                if lead and lead[-1] not in ".:;,!?":
                    out.append("### " + md_escape(lead)); rep.keep("pdf headings guessed", 1)
                else:
                    out.append(escape_line_start(md_escape(lead)))
                out.append("")
                items = rest
            # Indents within 2 spaces are one level: renderers offset numbered and bulleted
            # items by a space or so, which is not nesting.
            levels = []
            for ind in sorted(set(_indent(l) for l in items)):
                if not levels or ind - levels[-1] > 2:
                    levels.append(ind)
            for l in items:
                depth = min(max(k for k, lv in enumerate(levels) if lv <= _indent(l) + 2), 3)
                text = _BULLET.sub("", l.strip())
                out.append("  " * depth + "- " + md_escape(text))
            out.append("")
            continue
        lead = block[0].strip()
        if len(block) > 1 and len(lead.split()) <= 10 and lead[-1:] not in ".:;,!?" and lead[:1].isupper() \
                and len(lead) < 0.7 * max(len(l.strip()) for l in block[1:]):
            out += ["### " + md_escape(lead), ""]  # a title line over its first paragraph
            rep.keep("pdf headings guessed", 1)
            block = block[1:]
        para = " ".join(l.strip() for l in block)
        if len(block) == 1 and len(para.split()) <= 8 and para[-1:] not in ".:;,!?" and para[:1].isupper():
            out += ["### " + md_escape(para), ""]
            rep.keep("pdf headings guessed", 1)
        else:
            out += [escape_line_start(md_escape(para)), ""]
    return out


_FURNITURE = re.compile(r"^\s*(page\s+)?\d{1,4}(\s*(of|/)\s*\d{1,4})?\s*$|^\s*[-–—]\s*\d{1,4}\s*[-–—]\s*$", re.I)


def _join_split_tables(pages, rep):
    """A table that runs off the foot of one page continues at the top of the next, where it
    would otherwise start a second table whose first data row reads as its header. When a page
    ends in a table and the next page's first rows (after page numbers and any running header)
    have the same number of cells, those rows are moved up to finish the table. A header row
    the PDF repeats on the new page is dropped. Returns the pages, rewritten."""
    pages = [p.split("\n") for p in pages]
    first_lines = [next((l.strip() for l in p if l.strip()), "") for p in pages]
    running = {t for t in first_lines if t and first_lines.count(t) > 1}  # a header on several pages
    holder = None
    for k in range(len(pages) - 1):
        a_idx = k if holder is None else holder
        a, b = pages[a_idx], pages[k + 1]
        # the last table row on the holder page, before trailing page furniture
        end = len(a) - 1
        while end >= 0 and (not a[end].strip() or _FURNITURE.match(a[end])):
            end -= 1
        holder = None
        if end < 0 or len(_cells(a[end])) < 2:
            continue
        width = len(_cells(a[end]))
        start = end
        while start - 1 >= 0 and (len(_cells(a[start - 1])) == width or
                                  (not a[start - 1].strip() and start - 2 >= 0 and len(_cells(a[start - 2])) == width)):
            start -= 1
        header = " ".join(a[start].split())
        # the first content on the next page, past page numbers and a running header (a line
        # that repeats the table's own header is the table's, not the page's)
        i = 0
        while i < len(b) and (not b[i].strip() or _FURNITURE.match(b[i]) or
                              (b[i].strip() in running and " ".join(b[i].split()) != header)):
            i += 1
        if i >= len(b) or len(_cells(b[i])) != width:
            continue
        j = i
        rows = []
        while j < len(b) and (len(_cells(b[j])) == width or
                              (not b[j].strip() and j + 1 < len(b) and len(_cells(b[j + 1])) == width)):
            if b[j].strip():
                rows.append(b[j])
            j += 1
        dropped = bool(rows) and " ".join(rows[0].split()) == header
        if dropped:
            rows = rows[1:]
        if not rows:
            continue
        a[end + 1:end + 1] = rows
        del b[i:j]
        rep.notes.append("a table continued from page %d onto page %d was joined into one%s" % (
            a_idx + 1, k + 2, ", and the header row repeated on page %d was dropped" % (k + 2) if dropped else ""))
        rep.keep("pdf tables joined across pages", 1)
        if not any(l.strip() and not _FURNITURE.match(l) and l.strip() not in running for l in b):
            holder = a_idx  # the whole page was table: the next page may continue it too
    return ["\n".join(p) for p in pages]


def _ocr_page(path, n, ppm, tess, lang):
    """Page n of the PDF as text, by rendering it at 300 dpi and reading it with tesseract.
    Page segmentation mode 6 reads a uniform block and keeps the spacing between words, which
    is what the table and list inference reads columns from."""
    with tempfile.TemporaryDirectory(prefix="to-md-ocr-") as tmp:
        stem = str(Path(tmp) / "page")
        r = subprocess.run([ppm, "-r", "300", "-png", "-f", str(n), "-l", str(n), str(path), stem],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        pngs = sorted(Path(tmp).glob("page*.png"))
        if r.returncode != 0 or not pngs:
            sys.exit("error: pdftoppm could not render page %d: %s" % (n, r.stderr.decode("utf-8", "replace").strip()))
        r = subprocess.run([tess, str(pngs[0]), "stdout", "-l", lang, "--psm", "6",
                            "-c", "preserve_interword_spaces=1"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if r.returncode != 0:
            sys.exit("error: tesseract failed on page %d: %s" % (n, r.stderr.decode("utf-8", "replace").strip()))
        return r.stdout.decode("utf-8", "replace").replace("\f", "")


def pdf_to_md(path, rep, ocr=True, ocr_lang="eng"):
    exe = shutil.which("pdftotext")
    if not exe:
        sys.exit("error: reading PDF needs `pdftotext` (part of Poppler), which is not on PATH.\n"
                 "  macOS:          brew install poppler\n"
                 "  Debian/Ubuntu:  sudo apt install poppler-utils\n"
                 "  Windows:        install Poppler for Windows and add its bin folder to PATH\n"
                 "Then rerun. Or export the PDF to .docx or .txt and convert that.")
    def run(mode):
        proc = subprocess.run([exe] + mode + ["-enc", "UTF-8", str(path), "-"], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0:
            sys.exit("error: pdftotext failed: %s" % proc.stderr.decode("utf-8", "replace").strip())
        text = proc.stdout.decode("utf-8", "replace")
        pages = text.split("\f")
        return pages[:-1] if pages and not pages[-1].strip() else pages

    layout, reading = run(["-layout"]), run([])
    blank = [n for n, p in enumerate(layout, 1) if not p.strip()]
    if blank and ocr is not False:
        tess, ppm = shutil.which("tesseract"), shutil.which("pdftoppm")
        if not (tess and ppm):
            if len(blank) == len(layout):
                sys.exit("error: %s has no text layer (probably scanned), so it needs OCR, which uses "
                         "`tesseract`%s.\n"
                         "  macOS:          brew install tesseract   (pdftoppm comes with poppler)\n"
                         "  Debian/Ubuntu:  sudo apt install tesseract-ocr poppler-utils\n"
                         "  Windows:        install Tesseract (UB Mannheim build) and add it to PATH\n"
                         "Then rerun. Add --ocr-lang deu (or another installed language) for a non-English scan."
                         % (path, "" if ppm else " and `pdftoppm`"))
            rep.notes.append("page(s) %s have no text layer and were left empty: install tesseract to read them by OCR"
                             % ", ".join(map(str, blank)))
        else:
            for n in blank:
                text = _ocr_page(path, n, ppm, tess, ocr_lang)
                layout[n - 1] = text
                if n <= len(reading):
                    reading[n - 1] = text
            rep.keep("pages read by OCR", len(blank))
            rep.notes.append("page(s) %s are scanned, so their text was read by OCR (tesseract, language %s, 300 dpi). "
                             "OCR misreads characters: check every number, name and date against the PDF"
                             % (", ".join(map(str, blank)), ocr_lang))
    elif blank and len(blank) == len(layout):
        sys.exit("error: %s has no text layer (probably scanned), and --no-ocr was given." % path)
    layout = _join_split_tables(layout, rep)
    # Where each word sits, to tell table columns apart that sit closer than two characters
    # in the layout reading (see _finer_cells).
    proc = subprocess.run([exe, "-bbox-layout", "-enc", "UTF-8", str(path), "-"], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    fine = _word_rows(proc.stdout.decode("utf-8", "replace")) if proc.returncode == 0 else {}
    out, plain_pages = [], []
    for n, page in enumerate(layout, 1):
        out += ["<!-- page %d -->" % n, ""]
        if _multi_column(page) and n <= len(reading):
            out += _pdf_page_plain(reading[n - 1])
            plain_pages.append(n)
        else:
            out += _pdf_page_md(page, rep, fine)
    pages = layout
    if plain_pages:
        rep.notes.append("page(s) %s have side-by-side columns, so they were read in column order with "
                         "no tables, lists or headings inferred" % ", ".join(str(p) for p in plain_pages))
    rep.keep("pages", len(pages))
    rep.notes.append("PDF gives no structure, so it is inferred from the layout: tables from aligned columns, "
                     "lists from indentation, and short standalone lines as ### headings. Check them against the PDF; "
                     "images and charts are not recovered")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- main

HANDLERS = {
    ".docx": docx_to_md, ".pptx": pptx_to_md, ".xlsx": xlsx_to_md, ".xlsm": xlsx_to_md,
    ".html": html_to_md, ".htm": html_to_md, ".csv": csv_to_md, ".tsv": csv_to_md,
    ".json": json_to_md, ".pdf": pdf_to_md, ".eml": eml_to_md, ".msg": msg_to_md,
}
# What a damaged or truncated file raises from the zip, XML, compound-file and email layers.
DAMAGED = (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError, ET.ParseError, ValueError, LookupError,
           KeyError, IndexError, NotImplementedError, OSError)
LEGACY = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx", ".rtf": ".docx", ".odt": ".docx",
          ".pages": ".docx", ".key": ".pptx", ".numbers": ".xlsx"}


def main(argv=None):
    try:
        return _main(argv)
    finally:
        close_zips()  # on success, on an error exit, and on a damaged file alike


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Convert a document to Markdown for another skill to read.")
    ap.add_argument("input", help=".docx .pptx .xlsx .html .csv .tsv .json .txt .md .eml .msg .pdf")
    ap.add_argument("-o", "--output", required=True, help="Markdown file to write, or - for stdout")
    ap.add_argument("--max-rows", type=int, default=0,
                    help="xlsx only: keep at most this many data rows per sheet (0 = all)")
    ap.add_argument("--ocr-lang", default="eng",
                    help="pdf only: tesseract language for scanned pages, e.g. eng, deu, fra, eng+fra (default eng)")
    ap.add_argument("--no-ocr", action="store_true", help="pdf only: never run OCR on scanned pages")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z_]{3,}(\+[A-Za-z_]{3,})*", a.ocr_lang):
        sys.exit("error: --ocr-lang takes tesseract language codes such as eng or eng+fra")

    path = Path(a.input)
    if not path.is_file():
        sys.exit("error: input not found: %s" % a.input)
    ext = path.suffix.lower()
    rep = Report()
    # Embedded images go beside the Markdown, in <name>-images/; to stdout there is nowhere to
    # put them, so they are counted as dropped.
    if a.output != "-":
        stem = Path(a.output).stem
        MEDIA.update(dir=str(Path(a.output).parent / (stem + "-images")), link=quote(stem + "-images"), names={})
    else:
        MEDIA.update(dir=None, link=None, names={})
    if ext in LEGACY:
        sys.exit("error: %s files are not supported. Save or export it as %s and rerun%s."
                 % (ext, LEGACY[ext], " (on macOS: textutil -convert docx <file>)"
                    if ext in (".doc", ".rtf", ".odt") else ""))
    if ext in (".txt", ".md", ".markdown", ".text", ""):
        md = read_text(path, rep)
        if not md.endswith("\n"):
            md += "\n"
    elif ext in HANDLERS:
        fn = HANDLERS[ext]
        try:
            md = (fn(path, rep, a.max_rows) if fn is xlsx_to_md else
                  fn(path, rep, ocr=not a.no_ocr, ocr_lang=a.ocr_lang) if fn is pdf_to_md else fn(path, rep))
        except DAMAGED as e:
            if ext not in (".docx", ".pptx", ".xlsx", ".xlsm", ".msg", ".eml"):
                raise
            # A file that opens in its own app is a bug here; one that doesn't is damaged.
            sys.exit("error: %s looks damaged or truncated, so it could not be read as %s (%s: %s). If it "
                     "opens normally in its own app, please report it." % (path, ext, type(e).__name__, e))
    else:
        sys.exit("error: unsupported file type %r. Supported: %s, .txt, .md"
                 % (ext, ", ".join(sorted(HANDLERS))))

    if not md.strip():
        rep.notes.append("the conversion produced no text")
    if any(k.startswith("tracked") for k in rep.kept):
        rep.notes.append("tracked changes are pending, not accepted: {++added++} and {--removed--} mark them. "
                         "Accept or reject them in Word to settle the text")
    if a.output == "-":
        sys.stdout.write(md)
    else:
        out = Path(a.output)
        if out.parent and not out.parent.exists():
            sys.exit("error: output folder does not exist: %s" % out.parent)
        out.write_text(md, encoding="utf-8")

    kept = ", ".join("%d %s" % (v, k) for k, v in rep.kept.items()) or "text only"
    dest = "stdout" if a.output == "-" else a.output
    print("converted %s -> %s: %s" % (path.name, dest, kept), file=sys.stderr)
    if rep.dropped:
        print("dropped (not in the Markdown): " +
              ", ".join("%d %s" % (v, k) for k, v in rep.dropped.items()), file=sys.stderr)
    else:
        print("dropped: nothing detected", file=sys.stderr)
    for n in rep.notes:
        print("note: %s" % n, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

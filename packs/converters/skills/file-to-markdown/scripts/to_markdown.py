#!/usr/bin/env python3
"""Convert a document into clean Markdown that another skill can read.

Stdlib only, Python 3.9+. Handles .docx, .pptx, .xlsx, .html/.htm, .csv/.tsv,
.json, .txt/.md, and .pdf (through `pdftotext` when it is installed).
Everything the conversion could not carry (images, charts, comments, formulas,
tracked changes) is counted and reported on stderr, so nobody mistakes the
Markdown for the whole document.

Usage:
    python3 to_markdown.py report.docx -o report.md
    python3 to_markdown.py deck.pptx -o deck.md
    python3 to_markdown.py model.xlsx -o model.md --max-rows 200
    python3 to_markdown.py page.html -o -          # write to stdout
"""

import argparse
import csv
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from collections import OrderedDict
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
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


def render_segments(segs):
    """segs: list of (text, bold, italic, href). Merge neighbours with equal formatting."""
    merged = []
    for t, b, i, h in segs:
        if merged and merged[-1][1:] == (b, i, h):
            merged[-1] = (merged[-1][0] + t, b, i, h)
        else:
            merged.append((t, b, i, h))
    out = []
    for t, b, i, h in merged:
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


def open_zip(path, kind):
    try:
        return zipfile.ZipFile(str(path))
    except zipfile.BadZipFile:
        sys.exit("error: %s is not a valid %s file (not a zip package). If it is an old binary "
                 "Office file, save it as %s first." % (path, kind, kind))


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
                elif tag == W + "t":
                    segs.append((ch.text or "", b, i, href or field["href"]))
                elif tag == W + "tab":
                    segs.append((" ", False, False, None))
                elif tag in (W + "br", W + "cr"):
                    segs.append(("\n", False, False, None))
                elif tag in (W + "pict", W + "object"):
                    rep.drop("images")
                elif tag == W + "drawing":
                    uris = [g.get("uri") or "" for g in ch.iter(A + "graphicData")]
                    if any(True for _ in ch.iter(A + "blip")):
                        rep.drop("images")
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
                    rep.drop("tracked insertions (kept as text)")
                    walk(ch, href)
                elif ch.tag == W + "del":
                    rep.drop("tracked deletions (left out)")
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
        return (fmt, int(ilvl))

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
                    row.extend([""] * (int(tcpr.find(W + "gridSpan").get(W + "val", "1")) - 1))
            rows.append(row)
        if any(tbl.iter(W + "tbl")) and len(list(tbl.iter(W + "tbl"))) > 1:
            rep.notes.append("a nested table was flattened into its parent cell")
        rep.keep("tables")
        return md_table(rows)

    def raw_text(p):
        return "".join((n.text or "") if n.tag == W + "t" else "\t" for n in p.iter()
                       if n.tag in (W + "t", W + "tab"))

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
            if lvl:
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
            lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
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


def col_index(ref):
    letters = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


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
            row = int(re.search(r"(\d+)$", ref).group(1)) - 1
            col = col_index(ref)
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
        rows_used = sorted({r for r, _ in grid})
        cols_used = sorted({c for _, c in grid})
        c0, c1 = cols_used[0], cols_used[-1]
        table = []
        for r in range(rows_used[0], rows_used[-1] + 1):
            table.append([grid.get((r, c), "") for c in range(c0, c1 + 1)])
        table = [r for r in table if any(r)]
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
            span = int(a.get("colspan") or "1") if (a.get("colspan") or "1").isdigit() else 1
            self._span = span

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
_CODEISH = re.compile(r"-->|==>|[{};]|^\s*(def|function|class|SELECT|FROM)\b")
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


def _pdf_page_md(page, rep):
    """One page of `pdftotext -layout` text -> Markdown. Layout mode keeps line breaks,
    indentation and column alignment, which is what tables and lists are recovered from."""
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
                elif not line.strip() and j + 1 < n and lines[j + 1].strip() and (
                        len(_cells(lines[j + 1])) >= 2 or _col_starts(lines[j + 1]) <= _near(cols)):
                    j += 1
                else:
                    break
            if rows >= 2:
                widths = set(len(_cells(r)) for r in region)
                if len(widths) == 1 and rows == len(region):
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
        if (base >= 8 and any(_CODEISH.search(l) for l in block)) or _CODE_START.match(block[0]):
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


def pdf_to_md(path, rep):
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
    if not "".join(layout).strip():
        sys.exit("error: %s has no text layer (probably scanned). It needs OCR first; "
                 "this script does not do OCR." % path)
    out, plain_pages = [], []
    for n, page in enumerate(layout, 1):
        out += ["<!-- page %d -->" % n, ""]
        if _multi_column(page) and n <= len(reading):
            out += _pdf_page_plain(reading[n - 1])
            plain_pages.append(n)
        else:
            out += _pdf_page_md(page, rep)
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
    ".json": json_to_md, ".pdf": pdf_to_md,
}
LEGACY = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx", ".rtf": ".docx", ".odt": ".docx",
          ".pages": ".docx", ".key": ".pptx", ".numbers": ".xlsx"}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert a document to Markdown for another skill to read.")
    ap.add_argument("input", help=".docx .pptx .xlsx .html .csv .tsv .json .txt .md .pdf")
    ap.add_argument("-o", "--output", required=True, help="Markdown file to write, or - for stdout")
    ap.add_argument("--max-rows", type=int, default=0,
                    help="xlsx only: keep at most this many data rows per sheet (0 = all)")
    a = ap.parse_args(argv)

    path = Path(a.input)
    if not path.is_file():
        sys.exit("error: input not found: %s" % a.input)
    ext = path.suffix.lower()
    rep = Report()
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
        md = fn(path, rep, a.max_rows) if fn is xlsx_to_md else fn(path, rep)
    else:
        sys.exit("error: unsupported file type %r. Supported: %s, .txt, .md"
                 % (ext, ", ".join(sorted(HANDLERS))))

    if not md.strip():
        rep.notes.append("the conversion produced no text")
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

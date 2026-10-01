#!/usr/bin/env python3
"""Convert Markdown tables, a CSV file or a JSON array to an Excel workbook (.xlsx). Stdlib only.

Input by extension:
  .md / .markdown  every pipe table becomes one sheet, named from the nearest heading above it
  .csv / .tsv      one sheet (delimiter detected: comma, semicolon, tab or pipe)
  .json            an array of objects becomes one sheet; an object whose values are arrays of
                   objects becomes one sheet per key

Cells are typed: numbers (thousands separators, $/£/€ prefixes and percentages kept as number
formats), ISO 8601 dates and date-times, TRUE/FALSE, text otherwise. Codes with leading zeros
(007, 02134) and numbers longer than 15 digits stay text, because Excel would change them.
Text starting with "=" is written as text unless --formulas is given (formula injection).

Every sheet gets a bold, shaded, frozen header row, an autofilter and column widths sized to
the content. Strings are stored once in a shared-strings table.

Usage:
  python3 md_to_xlsx.py input.md|input.csv|input.json -o out.xlsx [--formulas] [--title "..."]
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import zipfile
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape as _esc

WARNINGS = []
MAX_ROWS = 1048576
MAX_COLS = 16384
MAX_CELL = 32767


def warn(msg):
    WARNINGS.append(msg)
    print("WARN %s" % msg, file=sys.stderr)


def die(msg):
    print("ERROR %s" % msg, file=sys.stderr)
    sys.exit(1)


# Control characters XML 1.0 forbids: every code point below 0x20 except tab, LF and CR.
_BAD_XML = dict.fromkeys(c for c in range(0x20) if c not in (0x09, 0x0A, 0x0D))


def x(s):
    return _esc(s.translate(_BAD_XML), {'"': "&quot;"})


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


# --------------------------------------------------------------------------- typing

RE_NUM = re.compile(r"^([-+]?)([$£€]?)((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?|\.(\d+))(%?)$")
RE_SCI = re.compile(r"^[-+]?\d+(?:\.\d+)?[eE][-+]?\d+$")
RE_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
RE_DATETIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?(Z|[+-]\d{2}:?\d{2})?$")
EPOCH = datetime.datetime(1899, 12, 30)


class Cell(object):
    __slots__ = ("kind", "value", "fmt", "width")

    def __init__(self, kind, value, fmt=None, width=0):
        self.kind = kind  # 's' string, 'n' number, 'b' bool, 'f' formula, 'd' date (number)
        self.value = value
        self.fmt = fmt
        self.width = width


def num_text(v):
    if isinstance(v, int):
        return str(v)
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return repr(v)


def type_date(s, tz_flag):
    m = RE_DATE.match(s)
    if m:
        try:
            d = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
        if d.year < 1900:
            return None
        return Cell("d", num_text((d - EPOCH).days), "yyyy-mm-dd", 10)
    m = RE_DATETIME.match(s)
    if m:
        try:
            frac = float("0." + m.group(7)) if m.group(7) else 0.0
            d = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                  int(m.group(4)), int(m.group(5)), int(m.group(6) or 0))
        except ValueError:
            return None
        if d.year < 1900:
            return None
        if m.group(8):
            tz_flag[0] = True
        delta = d - EPOCH
        serial = delta.days + (delta.seconds + frac) / 86400.0
        fmt = "yyyy-mm-dd hh:mm:ss" if m.group(6) else "yyyy-mm-dd hh:mm"
        return Cell("d", repr(round(serial, 10)), fmt, len(fmt))
    return None


def type_text(s, formulas, stats, tz_flag, infer_numbers=True):
    """Type one cell given as text. Returns Cell or None for empty."""
    if s is None:
        return None
    raw = s
    s = s.strip()
    if not s:
        return None
    width = max(len(line) for line in s.split("\n"))
    if s.startswith("=") and len(s) > 1:
        if formulas:
            stats["formulas"] += 1
            return Cell("f", s[1:], None, width)
        stats["formula_text"] += 1
        return Cell("s", s, None, width)
    if s.lower() in ("true", "false"):
        stats["booleans"] += 1
        return Cell("b", "1" if s.lower() == "true" else "0", None, 5)
    d = type_date(s, tz_flag)
    if d:
        stats["dates"] += 1
        return d
    if infer_numbers:
        m = RE_NUM.match(s)
        if m:
            sign, cur, body, dec, dec_only, pct = m.groups()
            intpart = body.split(".")[0].replace(",", "")
            digits = len(intpart.lstrip("0")) + len(dec or dec_only or "")
            leading_zero = len(intpart) > 1 and intpart.startswith("0") and "," not in body
            if not leading_zero and digits <= 15 and not (cur and pct):
                decimals = len(dec or dec_only or "")
                try:
                    val = Decimal(sign + body.replace(",", ""))
                except InvalidOperation:
                    val = None
                if val is not None:
                    if pct:
                        val = val / 100
                        fmt = "0%" if not decimals else "0." + "0" * decimals + "%"
                    elif cur:
                        fmt = ('"%s"#,##0' % cur) + ("." + "0" * decimals if decimals else "")
                    elif "," in body:
                        fmt = "#,##0" + ("." + "0" * decimals if decimals else "")
                    else:
                        fmt = None
                    stats["numbers"] += 1
                    text = format(val.normalize(), "f") if val != 0 else "0"
                    if text in ("-0", "+0"):
                        text = "0"
                    return Cell("n", text, fmt, width)
        if RE_SCI.match(s):
            stats["numbers"] += 1
            return Cell("n", repr(float(s)), None, width)
    if len(raw) > MAX_CELL:
        stats["truncated"] += 1
        s = s[:MAX_CELL]
    stats["text"] += 1
    return Cell("s", s, None, width)


def type_json(v, formulas, stats, tz_flag):
    if v is None:
        return None
    if isinstance(v, bool):
        stats["booleans"] += 1
        return Cell("b", "1" if v else "0", None, 5)
    if isinstance(v, (int, float)):
        if v != v or v in (float("inf"), float("-inf")):
            stats["text"] += 1
            return Cell("s", str(v), None, len(str(v)))
        stats["numbers"] += 1
        return Cell("n", num_text(v), None, len(num_text(v)))
    if isinstance(v, (dict, list)):
        stats["nested"] += 1
        v = json.dumps(v, ensure_ascii=False)
    # JSON strings stay strings (the producer chose a string), except ISO dates and formulas
    return type_text(str(v), formulas, stats, tz_flag, infer_numbers=False)


# --------------------------------------------------------------------------- readers

RE_TABLE_SEP = re.compile(r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
RE_HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
RE_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


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


def strip_md(s):
    """Plain text from a Markdown table cell."""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"(\*\*|__)(.+?)\1", r"\2", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", s)
    s = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", s)
    s = re.sub(r"~~(.+?)~~", r"\1", s)
    s = re.sub(r"</?[A-Za-z][^>]*>", "", s)
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|~])", r"\1", s)
    return s


def read_markdown(text):
    """Return list of (name_hint, header, rows, line_no)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    tables = []
    heading = None
    fence = None
    i = 0
    while i < len(lines):
        line = lines[i]
        fm = RE_FENCE.match(line)
        if fence:
            if fm and fm.group(1)[0] == fence[0] and len(fm.group(1)) >= len(fence):
                fence = None
            i += 1
            continue
        if fm:
            fence = fm.group(1)
            i += 1
            continue
        hm = RE_HEADING.match(line)
        if hm:
            heading = strip_md(hm.group(1)).strip()
            i += 1
            continue
        if "|" in line and i + 1 < len(lines) and RE_TABLE_SEP.match(lines[i + 1]) and "-" in lines[i + 1]:
            header = [strip_md(c) for c in split_row(line)]
            start = i + 1
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                rows.append([strip_md(c) for c in split_row(lines[i])])
                i += 1
            tables.append((heading, header, rows, start))
            continue
        i += 1
    return tables


def read_csv(text, path):
    sample = text[:20000]
    delim = "\t" if path.lower().endswith(".tsv") else None
    if delim is None:
        try:
            delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            delim = ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    if not rows:
        die("%s has no rows" % path)
    return rows[0], rows[1:], delim


def read_json(text, path):
    try:
        data = json.loads(text)
    except ValueError as e:
        die("%s is not valid JSON: %s" % (path, e))

    def as_sheet(arr, label):
        if not isinstance(arr, list) or not arr:
            die("%s: %s must be a non-empty array" % (path, label))
        if all(isinstance(r, dict) for r in arr):
            keys = []
            for r in arr:
                for k in r:
                    if k not in keys:
                        keys.append(k)
            return [str(k) for k in keys], [[r.get(k) for k in keys] for r in arr]
        if all(isinstance(r, list) for r in arr):
            return [str(c) for c in arr[0]], arr[1:]
        die("%s: %s must hold objects (or arrays), one per row" % (path, label))

    if isinstance(data, list):
        h, rows = as_sheet(data, "the top-level array")
        return [(None, h, rows)]
    if isinstance(data, dict) and data and all(isinstance(v, list) for v in data.values()):
        out = []
        for k, v in data.items():
            h, rows = as_sheet(v, "key %r" % k)
            out.append((str(k), h, rows))
        return out
    die("%s must be an array of objects, or an object whose values are arrays of objects" % path)


# --------------------------------------------------------------------------- sheet names

FORBIDDEN = re.compile(r"[\[\]:*?/\\]")


def sheet_name(hint, fallback, used):
    name = FORBIDDEN.sub(" ", hint or "")
    name = re.sub(r"\s+", " ", name).strip().strip("'").strip()
    if not name:
        name = fallback
    if len(name) > 31:
        cut = name[:31]
        space = cut.rfind(" ")
        name = (cut[:space] if space >= 16 else cut).rstrip(" (-,;&")
        if name.count("(") > name.count(")"):  # don't leave half a parenthetical
            name = name[:name.rfind("(")].rstrip() or name
    if name.lower() == "history":  # Excel reserves this name
        name = "History data"
    base, k = name, 2
    while name.lower() in used:
        suffix = " (%d)" % k
        name = base[:31 - len(suffix)].rstrip() + suffix
        k += 1
    used.add(name.lower())
    if hint and name != hint.strip():
        return name, True
    return name, False


# --------------------------------------------------------------------------- writer

class Styles(object):
    BUILTIN = {"0%": 9, "0.00%": 10, "#,##0": 3, "#,##0.00": 4}

    def __init__(self):
        self.fmts = {}  # code -> id
        self.xfs = [(0, False, False)]  # (numFmtId, header, wrap)

    def xf(self, fmt, header=False, wrap=False):
        fid = 0
        if fmt:
            fid = self.BUILTIN.get(fmt) or self.fmts.setdefault(fmt, 164 + len(self.fmts))
        key = (fid, header, wrap)
        if key not in self.xfs:
            self.xfs.append(key)
        return self.xfs.index(key)

    def xml(self):
        fmts = "".join('<numFmt numFmtId="%d" formatCode="%s"/>' % (i, x(c)) for c, i in self.fmts.items())
        xfs = []
        for fid, header, wrap in self.xfs:
            attrs = 'numFmtId="%d" fontId="%d" fillId="%d" borderId="%d" xfId="0"' % (
                fid, 1 if header else 0, 2 if header else 0, 1 if header else 0)
            if fid:
                attrs += ' applyNumberFormat="1"'
            if header:
                attrs += ' applyFont="1" applyFill="1" applyBorder="1"'
            if wrap:
                xfs.append('<xf %s applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>' % attrs)
            else:
                xfs.append("<xf %s/>" % attrs)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '%s'
                '<fonts count="2"><font><sz val="11"/><name val="Calibri"/><family val="2"/></font>'
                '<font><b/><sz val="11"/><name val="Calibri"/><family val="2"/></font></fonts>'
                '<fills count="3"><fill><patternFill patternType="none"/></fill>'
                '<fill><patternFill patternType="gray125"/></fill>'
                '<fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill>'
                '</fills>'
                '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
                '<border><left/><right/><top/><bottom style="thin"><color rgb="FF808080"/></bottom><diagonal/></border>'
                '</borders>'
                '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                '<cellXfs count="%d">%s</cellXfs>'
                '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                '</styleSheet>') % (
                    '<numFmts count="%d">%s</numFmts>' % (len(self.fmts), fmts) if self.fmts else "",
                    len(xfs), "".join(xfs))


class SharedStrings(object):
    def __init__(self):
        self.index = {}
        self.items = []
        self.count = 0

    def add(self, s):
        self.count += 1
        if s not in self.index:
            self.index[s] = len(self.items)
            self.items.append(s)
        return self.index[s]

    def xml(self):
        sis = "".join('<si><t xml:space="preserve">%s</t></si>' % x(s) for s in self.items)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="%d" uniqueCount="%d">'
                '%s</sst>') % (self.count, len(self.items), sis)


def build_sheet(name, header, rows, typer, styles, sst, first):
    """header: list of str; rows: list of lists of raw values; typer(raw)->Cell|None."""
    ncols = max([len(header)] + [len(r) for r in rows]) if rows else len(header)
    if ncols > MAX_COLS:
        die("sheet %r has %d columns; Excel's limit is %d" % (name, ncols, MAX_COLS))
    if len(rows) + 1 > MAX_ROWS:
        die("sheet %r has %d rows; Excel's limit is %d" % (name, len(rows) + 1, MAX_ROWS))
    ragged = sum(1 for r in rows if len(r) != len(header))
    if ragged:
        warn("sheet %r: %d row(s) have a different cell count from the header; padded with empty cells"
             % (name, ragged))
    header = list(header) + [""] * (ncols - len(header))
    blank = [i for i, h in enumerate(header) if not str(h).strip()]
    for i in blank:
        header[i] = "Column %d" % (i + 1)
    if blank:
        warn("sheet %r: empty header cell(s) named %s" % (name, ", ".join(header[i] for i in blank)))
    widths = [len(str(h)) + 3 for h in header]
    hstyle = styles.xf(None, header=True)
    out = ['<row r="1">']
    for c, h in enumerate(header):
        out.append('<c r="%s1" t="s" s="%d"><v>%d</v></c>' % (col_letter(c), hstyle, sst.add(str(h).strip())))
    out.append("</row>")
    for r_i, row in enumerate(rows):
        rn = r_i + 2
        cells = []
        for c in range(ncols):
            cell = typer(row[c] if c < len(row) else None)
            if cell is None:
                continue
            ref = "%s%d" % (col_letter(c), rn)
            widths[c] = max(widths[c], cell.width)
            if cell.kind == "s":
                wrap = "\n" in cell.value
                s = styles.xf(None, wrap=wrap)
                cells.append('<c r="%s" t="s"%s><v>%d</v></c>' % (ref, ' s="%d"' % s if s else "", sst.add(cell.value)))
            elif cell.kind == "b":
                cells.append('<c r="%s" t="b"><v>%s</v></c>' % (ref, cell.value))
            elif cell.kind == "f":
                cells.append('<c r="%s"><f>%s</f></c>' % (ref, x(cell.value)))
            else:
                s = styles.xf(cell.fmt)
                cells.append('<c r="%s"%s><v>%s</v></c>' % (ref, ' s="%d"' % s if s else "", cell.value))
        out.append('<row r="%d">%s</row>' % (rn, "".join(cells)))
    last = "%s%d" % (col_letter(ncols - 1), len(rows) + 1)
    cols = "".join('<col min="%d" max="%d" width="%.1f" customWidth="1"/>' % (
        i + 1, i + 1, min(max(w * 1.1 + 1, 8), 60)) for i, w in enumerate(widths))
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
           '<dimension ref="A1:%s"/>'
           '<sheetViews><sheetView %sworkbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
           'state="frozen"/><selection pane="bottomLeft" activeCell="A2" sqref="A2"/></sheetView></sheetViews>'
           '<sheetFormatPr defaultRowHeight="15"/><cols>%s</cols><sheetData>%s</sheetData>'
           '<autoFilter ref="A1:%s"/>'
           '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
           '</worksheet>') % (last, 'tabSelected="1" ' if first else "", cols, "".join(out), last)
    return xml, "A1:" + last, len(rows), ncols


def write_xlsx(out, sheets, title, formulas):
    """sheets: list of (name, sheet_xml, ref)."""
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/styles.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          '<Override PartName="/xl/sharedStrings.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
          '<Override PartName="/docProps/app.xml" '
          'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    sheet_tags, names = [], []
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    for i, (name, _, ref) in enumerate(sheets):
        n = i + 1
        ct.append('<Override PartName="/xl/worksheets/sheet%d.xml" '
                  'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % n)
        rels.append('<Relationship Id="rId%d" Type="%sworksheet" Target="worksheets/sheet%d.xml"/>' % (n, R, n))
        sheet_tags.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (x(name), n, n))
        a, b = ref.split(":")
        absref = "$%s$%s:$%s$%s" % (re.match(r"[A-Z]+", a).group(0), a.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                                    re.match(r"[A-Z]+", b).group(0), b.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        names.append('<definedName name="_xlnm._FilterDatabase" localSheetId="%d" hidden="1">%s</definedName>' % (
            i, x("'%s'!%s" % (name.replace("'", "''"), absref))))
    k = len(sheets)
    rels.append('<Relationship Id="rId%d" Type="%sstyles" Target="styles.xml"/>' % (k + 1, R))
    rels.append('<Relationship Id="rId%d" Type="%ssharedStrings" Target="sharedStrings.xml"/>' % (k + 2, R))
    rels.append("</Relationships>")
    ct.append("</Types>")
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<bookViews><workbookView activeTab="0"/></bookViews><sheets>%s</sheets>'
                '<definedNames>%s</definedNames>%s</workbook>') % (
                    "".join(sheet_tags), "".join(names), '<calcPr fullCalcOnLoad="1"/>' if formulas else "")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>%s</dc:title>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified></cp:coreProperties>') % (
                x(title), now, now)
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>md_to_xlsx.py</Application></Properties>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="%sofficeDocument" Target="xl/workbook.xml"/>'
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/'
                 'metadata/core-properties" Target="docProps/core.xml"/>'
                 '<Relationship Id="rId3" Type="%sextended-properties" Target="docProps/app.xml"/>'
                 '</Relationships>') % (R, R)
    return ct, rels, workbook, core, app, root_rels


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help=".md, .csv, .tsv or .json file")
    ap.add_argument("-o", "--output", required=True, help="output .xlsx path")
    ap.add_argument("--formulas", action="store_true",
                    help="write cells starting with = as live formulas (default: text, to block formula injection)")
    ap.add_argument("--title", help="workbook title for File > Properties (default: input file name)")
    a = ap.parse_args(argv)

    if not a.output.lower().endswith(".xlsx"):
        die("output must end in .xlsx: %s" % a.output)
    out_dir = os.path.dirname(os.path.abspath(a.output))
    if not os.path.isdir(out_dir):
        die("output folder %s does not exist" % out_dir)
    ext = os.path.splitext(a.input)[1].lower()
    if ext not in (".md", ".markdown", ".csv", ".tsv", ".json"):
        die("unsupported input type %r; give a .md, .csv, .tsv or .json file" % ext)
    try:
        with open(a.input, encoding="utf-8-sig", newline="") as f:
            text = f.read()
    except OSError as e:
        die("cannot read %s: %s" % (a.input, e))
    except UnicodeDecodeError:
        die("%s is not UTF-8 text; save it as UTF-8 (in Excel: CSV UTF-8) and rerun" % a.input)

    stem = os.path.splitext(os.path.basename(a.input))[0]
    raw_sheets = []  # (hint, header, rows, source label, json?)
    if ext in (".md", ".markdown"):
        tables = read_markdown(text)
        if not tables:
            die("%s has no pipe tables (a header row, then a |---| separator row)" % a.input)
        for k, (hint, header, rows, ln) in enumerate(tables):
            raw_sheets.append((hint, header, rows, "table at line %d" % ln, False, "Table %d" % (k + 1)))
    elif ext in (".csv", ".tsv"):
        header, rows, delim = read_csv(text, a.input)
        raw_sheets.append((stem, header, rows, "delimiter %r" % delim, False, "Sheet1"))
    else:
        for hint, header, rows in read_json(text, a.input):
            raw_sheets.append((hint or stem, header, rows, "JSON", True, "Sheet1"))

    styles, sst = Styles(), SharedStrings()
    used = set()
    built = []
    report = []
    total_formula_text = 0
    for k, (hint, header, rows, label, is_json, fallback) in enumerate(raw_sheets):
        name, renamed = sheet_name(hint, fallback, used)
        stats = {"numbers": 0, "dates": 0, "booleans": 0, "text": 0, "formulas": 0, "formula_text": 0,
                 "nested": 0, "truncated": 0}
        tz = [False]
        if is_json:
            typer = lambda v, s=stats, t=tz: type_json(v, a.formulas, s, t)
        else:
            typer = lambda v, s=stats, t=tz: type_text(v, a.formulas, s, t)
        xml, ref, nrows, ncols = build_sheet(name, header, rows, typer, styles, sst, k == 0)
        built.append((name, xml, ref))
        if renamed and hint:
            warn("sheet name %r changed to %r (Excel allows 31 characters, no []:*?/\\, unique names)" % (hint, name))
        if tz[0]:
            warn("sheet %r: time-zone offsets dropped; Excel has no time zones, times kept as written" % name)
        if stats["nested"]:
            warn("sheet %r: %d nested JSON value(s) written as JSON text" % (name, stats["nested"]))
        if stats["truncated"]:
            warn("sheet %r: %d cell(s) cut to Excel's 32,767-character limit" % (name, stats["truncated"]))
        total_formula_text += stats["formula_text"]
        parts = ["%d %s" % (stats[key], key) for key in ("numbers", "dates", "booleans", "text", "formulas")
                 if stats[key]]
        report.append('  sheet "%s" (%s): %d row%s x %d col%s; %s' % (
            name, label, nrows, "" if nrows == 1 else "s", ncols, "" if ncols == 1 else "s",
            ", ".join(parts) or "no data cells"))
    if total_formula_text:
        warn("%d cell(s) start with '=' and were written as text, not formulas; rerun with --formulas only "
             "if you trust the source" % total_formula_text)

    ct, rels, workbook, core, app, root_rels = write_xlsx(a.output, built, a.title or stem, a.formulas)
    with zipfile.ZipFile(a.output, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", root_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", "".join(rels))
        z.writestr("xl/styles.xml", styles.xml())
        z.writestr("xl/sharedStrings.xml", sst.xml())
        for i, (_, xml, _) in enumerate(built):
            z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), xml)
    print("wrote %s (%d sheet%s, %d unique strings)" % (a.output, len(built), "" if len(built) == 1 else "s",
                                                        len(sst.items)))
    for line in report:
        print(line)
    if WARNINGS:
        print("%d warning(s): check them before sharing the workbook" % len(WARNINGS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Check translated string files against the source strings before they ship. Stdlib only.

Reads the source file and one or more target files in any of these formats, detected by
extension or content:
  JSON (flat or nested; i18next plurals as key_one / key_other ...), ARB, gettext .po/.pot,
  Android strings.xml (string, plurals, string-array), iOS .strings (UTF-8 or UTF-16) and
  iOS .stringsdict.
The locale of each file comes from its path (de.json, fr-CA.json, values-fr/strings.xml,
fr.lproj/Localizable.strings, fr.po, app_fr.arb, locales/fr/common.json), from an ARB
@@locale or a .po Language header, or from --locale.

It FAILS a target where
  - a source key is missing, or its translation is empty
  - a placeholder differs from the source: {name}, {{name}}, %s, %d, %1$s, %@, %(name)s, and
    ICU arguments; a positional printf argument whose type changes, or plain %s / %d
    arguments in a different order (they would swap at runtime)
  - an ICU message that parses in the source doesn't parse in the target, or a select
    keyword (male / female / other) was translated or dropped
  - a plural form the target language needs is missing (CLDR cardinal categories: ar needs
    zero, one, two, few, many and other; pl one, few, many and other; ja only other); for
    gettext, the number of msgstr[n] forms differs from the language's nplurals
  - markup tags (<b>, <a href>, <0>...</0>, <xliff:g>) differ from the source or don't balance
  - a string is over its character budget (--budget)
  - a target file doesn't parse at all
and WARNS where
  - a key in the target is not in the source
  - a translation is identical to the source (possibly untranslated), for text over 3 letters
  - leading or trailing whitespace changed, or the source's ending punctuation was dropped
  - a word mixes Latin, Cyrillic or Greek letters (a look-alike typed by mistake)
  - a plural form the language uses only for large numbers (fr, es, it, pt "many") is absent
  - a gettext entry is marked fuzzy (msgfmt leaves it out, so the source text shows)

--budget FILE is JSON: {"keys": {"checkout.pay": 18}, "ratio": 1.4, "ratio_min_source": 10}
or a CSV with columns key,max. A per-key limit applies to every locale; the ratio applies to
keys without one, when the source string is at least ratio_min_source characters long.
Lengths count visible characters: markup tags and placeholders are not counted.
Without --budget no length is checked, and the report says so.

Usage:
  python3 locale_check.py en.json de.json fr.json [--budget budget.json] [--json] [-o OUT]
  python3 locale_check.py values/strings.xml values-pl/strings.xml values-ar/strings.xml
  python3 locale_check.py messages.pot fr.po --locale fr

Exit codes: 0 no failures, 1 a failure, 2 bad input (a file missing, an unknown format, a
source that doesn't parse, or bad arguments).
"""
import argparse
import csv
import io
import json
import math
import os
import plistlib
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

# --------------------------------------------------------------------------- languages

# CLDR cardinal plural categories (CLDR 44) for the languages most products ship.
CLDR = {}
for _langs, _cats in (
    ("ja zh ko vi th id ms km lo my yo ig jv su", ("other",)),
    ("en de nl sv da nb nn no fi et el hu tr bg af sw ur hi bn fa ta te ml mr gu kn is fil az ka "
     "kk ky mn sq eu gl ne pa si zu xh am ps", ("one", "other")),
    ("fr es it pt ca", ("one", "many", "other")),
    ("ru uk be", ("one", "few", "many", "other")),
    ("pl", ("one", "few", "many", "other")),
    ("cs sk", ("one", "few", "many", "other")),
    ("lt", ("one", "few", "many", "other")),
    ("hr sr bs", ("one", "few", "other")),
    ("ro mo", ("one", "few", "other")),
    ("lv", ("zero", "one", "other")),
    ("sl", ("one", "two", "few", "other")),
    ("he iw", ("one", "two", "other")),
    ("ar", ("zero", "one", "two", "few", "many", "other")),
    ("cy", ("zero", "one", "two", "few", "many", "other")),
    ("ga", ("one", "two", "few", "many", "other")),
    ("mt", ("one", "two", "few", "many", "other")),
):
    for _l in _langs.split():
        CLDR[_l] = _cats
# Categories a language has that only very large numbers reach: missing is a warning.
SOFT = {"fr": {"many"}, "es": {"many"}, "it": {"many"}, "pt": {"many"}, "ca": {"many"}}
# gettext nplurals as the usual Plural-Forms headers set them.
NPLURALS = {}
for _langs, _n in (("ja zh ko vi th id ms km lo my", 1),
                   ("en de nl sv da nb nn no fi et el hu tr bg af sw ur hi bn fa ta te ml mr gu kn "
                    "is fil fr es it pt ca az ka kk ky mn sq eu gl ne pa si zu he iw", 2),
                   ("ru uk be pl cs sk lt hr sr bs ro mo lv", 3), ("sl cy", 4), ("ga", 5), ("ar", 6)):
    for _l in _langs.split():
        NPLURALS[_l] = _n
CATEGORIES = ("zero", "one", "two", "few", "many", "other")
LANG_RE = re.compile(r"^([a-z]{2,3})(?:[-_](?:[A-Z][a-z]{3}|[A-Za-z]{2}|\d{3}|r[A-Z]{2}))*$")


def lang_of(code):
    """'pt-BR' -> 'pt', 'zh_Hant' -> 'zh', 'values-pt-rBR' handled by the caller."""
    return re.split(r"[-_]", code.strip())[0].lower() if code else ""


def detect_locale(path):
    """The locale a file's path names, or ''."""
    parts = re.split(r"[\\/]", os.path.abspath(path))
    name = parts[-1]
    stem = name.split(".")[0]
    m = re.match(r"^values-([a-z]{2,3})(?:-r([A-Z]{2}))?", parts[-2] if len(parts) > 1 else "")
    if m:
        return m.group(1) + ("-" + m.group(2) if m.group(2) else "")
    for p in reversed(parts[:-1]):
        m = re.match(r"^([A-Za-z]{2,3}(?:[-_][A-Za-z]{2,4})?)\.lproj$", p)
        if m:
            return m.group(1)
    if LANG_RE.match(stem) and lang_of(stem) in CLDR:
        return stem
    for tok in reversed(re.split(r"[_.]", name)[:-1]):
        if LANG_RE.match(tok) and lang_of(tok) in CLDR:
            return tok
    for p in reversed(parts[-3:-1]):
        if LANG_RE.match(p) and lang_of(p) in CLDR:
            return p
    if len(parts) > 1 and parts[-2] in ("values", "Base.lproj", "en.lproj"):
        return "en"
    return ""


# --------------------------------------------------------------------------- entries

class Entry(object):
    """One string, or one plural string as {category: text}."""

    __slots__ = ("key", "value", "line", "plural", "fuzzy", "gettext_n", "icu_ok")

    def __init__(self, key, value, line=None, plural=False, fuzzy=False, gettext_n=None):
        self.key, self.value, self.line, self.plural = key, value, line, plural
        self.fuzzy, self.gettext_n, self.icu_ok = fuzzy, gettext_n, None

    def texts(self):
        return list(self.value.values()) if self.plural else [self.value]


class BadInput(Exception):
    pass


class ParseError(Exception):
    pass


def read_text(path):
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        raise BadInput("can't read %s: %s" % (path, e.strerror or e))
    for bom, enc in ((b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16")):
        if raw.startswith(bom):
            return raw.decode(enc, errors="replace")
    if len(raw) > 1 and raw[1:2] == b"\x00" and raw[0:1] != b"\x00":
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def detect_format(path, text):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".json", ".arb", ".po", ".pot", ".strings", ".stringsdict", ".xml"):
        return {"json": "json", "arb": "arb", "po": "po", "pot": "po", "strings": "strings",
                "stringsdict": "stringsdict", "xml": "android"}[ext[1:]]
    head = text.lstrip()[:400]
    if head.startswith("{"):
        return "arb" if '"@@locale"' in text else "json"
    if "<resources" in head:
        return "android"
    if "<plist" in head or "<!DOCTYPE plist" in head:
        return "stringsdict"
    if re.search(r'^\s*msgid\s+"', text, re.M):
        return "po"
    if re.search(r'^\s*"(?:[^"\\]|\\.)*"\s*=\s*"', text, re.M):
        return "strings"
    raise BadInput("%s: unknown format (use .json, .arb, .po, .xml, .strings or .stringsdict)" % path)


def json_key_lines(text):
    """{dotted key path: line} for every object key in a JSON text, without a full parser."""
    lines, stack, i, n, line = {}, [], 0, len(text), 1
    pending, last_str = None, None
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 1
                if j < n and text[j] == "\n":
                    line += 1
                j += 1
            last_str = (text[i + 1:j], line)
            i = j
        elif c == ":" and last_str is not None:
            pending = last_str
            key = ".".join([k for k in stack if k is not None] + [pending[0]])
            lines.setdefault(key, pending[1])
            last_str = None
        elif c in "{[":
            stack.append(pending[0] if pending else None)
            pending, last_str = None, None
        elif c in "}]":
            if stack:
                stack.pop()
            pending, last_str = None, None
        elif c == ",":
            pending, last_str = None, None
        i += 1
    return lines


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from flatten(v, prefix + ("." if prefix else "") + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flatten(v, prefix + "." + str(i))
    elif isinstance(obj, str):
        yield prefix, obj
    elif obj is None or isinstance(obj, (int, float, bool)):
        yield prefix, "" if obj is None else str(obj)


PLURAL_SUFFIX = re.compile(r"^(.*)_(zero|one|two|few|many|other)$")


def parse_json(text, arb=False):
    try:
        doc = json.loads(text)
    except ValueError as e:
        raise ParseError("not valid JSON: %s" % e)
    except RecursionError:
        raise ParseError("nested too deeply to read")
    if not isinstance(doc, dict):
        raise ParseError("the top level is not an object of strings")
    locale = doc.get("@@locale") if arb and isinstance(doc.get("@@locale"), str) else ""
    lines = json_key_lines(text)
    try:
        flat = [(k, v) for k, v in flatten(doc) if not (arb and k.split(".")[0].startswith("@"))]
    except RecursionError:
        raise ParseError("nested too deeply to read")
    keys = {k for k, _ in flat}
    entries, grouped = {}, {}
    for k, v in flat:
        m = PLURAL_SUFFIX.match(k)
        if m and (m.group(1) + "_other") in keys:
            grouped.setdefault(m.group(1), {})[m.group(2)] = (v, lines.get(k))
            continue
        entries[k] = Entry(k, v, lines.get(k))
    for base, forms in grouped.items():
        line = min((ln for _, ln in forms.values() if ln), default=None)
        if base in entries:  # a bare key beside its plural forms is the fallback form
            forms.setdefault("other", (entries.pop(base).value, line))
        entries[base] = Entry(base, {c: t for c, (t, _) in forms.items()}, line, plural=True)
    return entries, locale


def po_unquote(chunks):
    out = []
    for c in chunks:
        try:
            out.append(json.loads(c))
        except ValueError:
            out.append(c.strip('"'))
    return "".join(out)


def parse_po(text, source=False):
    entries, header_lang, nplurals = {}, "", None
    items, cur, field, fuzzy = [], None, None, False

    def close():
        if cur and "msgid" in cur["f"]:
            items.append(cur)

    for no, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        s = raw.strip()
        if not s:
            close()
            cur, field = None, None
            continue
        if s.startswith("#"):
            if s.startswith("#,") and "fuzzy" in s:
                fuzzy = True
            continue
        m = re.match(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(".*")\s*$', s)
        if m:
            kw = m.group(1)
            if cur is None or (kw in ("msgctxt", "msgid") and any(k.startswith("msgstr") for k in cur["f"])):
                close()
                cur = {"f": {}, "line": no, "fuzzy": fuzzy}
                fuzzy = False
            if kw == "msgid":
                cur["line"] = no
            field = kw
            cur["f"].setdefault(kw, []).append(m.group(2))
        elif s.startswith('"') and cur is not None and field:
            cur["f"][field].append(s)
        else:
            raise ParseError("line %d: can't read %r" % (no, s[:40]))
    close()
    for it in items:
        fields = it["f"]
        msgid = po_unquote(fields["msgid"])
        if msgid == "" and "msgctxt" not in fields:
            hdr = po_unquote(fields.get("msgstr", []))
            m = re.search(r"^Language:\s*(\S+)", hdr, re.M)
            header_lang = m.group(1) if m else ""
            m = re.search(r"nplurals\s*=\s*(\d+)", hdr)
            nplurals = int(m.group(1)) if m else None
            continue
        key = (po_unquote(fields["msgctxt"]) + "\x04" if "msgctxt" in fields else "") + msgid
        if "msgid_plural" in fields:
            forms = {}
            for f, v in fields.items():
                m = re.match(r"msgstr\[(\d+)\]", f)
                if m:
                    forms[int(m.group(1))] = po_unquote(v)
            plural_src = po_unquote(fields["msgid_plural"])
            if source:
                value = {"one": forms.get(0) or msgid, "other": forms.get(1) or plural_src}
            else:
                value = {"[%d]" % i: forms[i] for i in sorted(forms)}
            e = Entry(key, value, it["line"], plural=True, fuzzy=it["fuzzy"], gettext_n=len(forms))
        else:
            msgstr = po_unquote(fields.get("msgstr", []))
            e = Entry(key, (msgstr or msgid) if source else msgstr, it["line"], fuzzy=it["fuzzy"])
        entries[key] = e
    if not entries and not header_lang:
        raise ParseError("no msgid entries")
    return entries, header_lang, nplurals


def inner_xml(el):
    """An element's content with its markup, as Android keeps it."""
    parts = [el.text or ""]
    for child in el:
        s = ET.tostring(child, encoding="unicode")
        parts.append(re.sub(r'\sxmlns:\w+="[^"]*"', "", s))
    return "".join(parts)


def android_raw_problem(raw):
    """aapt rejects an apostrophe without a backslash outside a double-quoted string."""
    body = raw.strip()
    if len(body) >= 2 and body[0] == '"' and body[-1] == '"':
        return None
    text = re.sub(r"<[^>]*>", "", body)
    if re.search(r"(?<!\\)'", text):
        return "an apostrophe without a backslash: the Android build fails (write \\' )"
    return None


def android_unescape(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return re.sub(r"\\([nt'\"@?\\])", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def parse_android(text):
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as e:
        raise ParseError("not valid XML: %s" % e)
    if root.tag != "resources":
        raise ParseError("the root element is <%s>, not <resources>" % root.tag)

    def line_of(name, tag):
        m = re.search(r'<%s\b[^>]*\bname="%s"' % (tag, re.escape(name)), text)
        return text.count("\n", 0, m.start()) + 1 if m else None

    entries = {}
    for el in root:
        name = el.get("name")
        if not name or el.get("translatable") == "false":
            continue
        if el.tag == "string":
            raw = inner_xml(el)
            entries[name] = Entry(name, android_unescape(raw), line_of(name, "string"))
            entries[name].icu_ok = android_raw_problem(raw)
        elif el.tag == "plurals":
            raws = {it.get("quantity"): inner_xml(it) for it in el if it.get("quantity")}
            forms = {q: android_unescape(r) for q, r in raws.items()}
            entries[name] = Entry(name, forms, line_of(name, "plurals"), plural=True)
            entries[name].icu_ok = next((android_raw_problem(r) for r in raws.values() if android_raw_problem(r)), None)
        elif el.tag == "string-array":
            ln = line_of(name, "string-array")
            for i, it in enumerate(el):
                k = "%s[%d]" % (name, i)
                entries[k] = Entry(k, android_unescape(inner_xml(it)), ln)
    return entries


STRINGS_RE = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;|([A-Za-z_][\w.]*)\s*=\s*"((?:[^"\\]|\\.)*)"\s*;')


def strings_unescape(s):
    def rep(m):
        c = m.group(1)
        if c.startswith("U") or c.startswith("u"):
            try:
                return chr(int(c[1:], 16))
            except ValueError:
                return c
        return {"n": "\n", "t": "\t", "r": "\r", "0": "\0"}.get(c, c)
    return re.sub(r"\\([Uu][0-9A-Fa-f]{4}|.)", rep, s)


def parse_strings(text):
    body = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    body = re.sub(r"(?m)^\s*//.*$", "", body)
    entries = {}
    for m in STRINGS_RE.finditer(body):
        key = strings_unescape(m.group(1) if m.group(1) is not None else m.group(3))
        val = strings_unescape(m.group(2) if m.group(2) is not None else m.group(4))
        entries[key] = Entry(key, val, body.count("\n", 0, m.start()) + 1)
    rest = STRINGS_RE.sub("", body)
    stray = re.search(r'"[^"\n]*"\s*=|=\s*"', rest)
    if stray:
        raise ParseError("line %d: an entry that isn't \"key\" = \"value\";" % (body.count("\n", 0, stray.start()) + 1))
    if not entries and rest.strip():
        raise ParseError('no "key" = "value"; entries')
    return entries


def parse_stringsdict(text):
    try:
        doc = plistlib.loads(text.encode("utf-8"))
    except Exception as e:  # plistlib raises several types for bad input
        raise ParseError("not a valid plist: %s" % e)
    if not isinstance(doc, dict):
        raise ParseError("the plist's top level is not a dictionary")
    entries = {}
    for key, spec in doc.items():
        if not isinstance(spec, dict):
            continue
        m = re.search(r"^\s*<key>%s</key>" % re.escape(key), text, re.M)
        line = text.count("\n", 0, m.start()) + 1 if m else None
        fmt = spec.get("NSStringLocalizedFormatKey")
        if isinstance(fmt, str):
            entries[key] = Entry(key, fmt, line)
        for var, rule in spec.items():
            if isinstance(rule, dict) and rule.get("NSStringFormatSpecTypeKey") == "NSStringPluralRuleType":
                forms = {c: rule[c] for c in CATEGORIES if isinstance(rule.get(c), str)}
                k = "%s#%s" % (key, var)
                entries[k] = Entry(k, forms, line, plural=True)
    return entries


def load(path, source, locale_override=""):
    text = read_text(path)
    fmt = detect_format(path, text)
    locale, nplurals = "", None
    if fmt in ("json", "arb"):
        entries, locale = parse_json(text, arb=fmt == "arb")
    elif fmt == "po":
        entries, locale, nplurals = parse_po(text, source=source)
    elif fmt == "android":
        entries = parse_android(text)
    elif fmt == "strings":
        entries = parse_strings(text)
    else:
        entries = parse_stringsdict(text)
    locale = locale_override or locale or detect_locale(path)
    return {"path": path, "format": fmt, "locale": locale, "entries": entries, "nplurals": nplurals}


# --------------------------------------------------------------------------- placeholders

PRINTF = re.compile(r"%(?:%|(?:(\d+)\$|\((\w+)\))?[-+ 0#']*(?:\d+|\*)?(?:\.(?:\d+|\*))?"
                    r"(?:hh|h|ll|l|L|q|j|z|t)?([diouxXeEfFgGaAcCsSpn@]))")
DOUBLE = re.compile(r"\{\{\s*([^{}\s,]+)[^{}]*\}\}")
SINGLE = re.compile(r"(?<!\{)\{\s*([A-Za-z_][\w.]*|\d+)\s*\}(?!\})")
TAG = re.compile(r"<(/?)([A-Za-z][\w:.-]*|\d+)(\s[^<>]*?)?(/?)>")
TYPE = {"i": "d", "u": "d", "o": "d", "x": "d", "X": "d", "F": "f", "e": "f", "E": "f",
        "g": "f", "G": "f", "a": "f", "A": "f", "S": "s", "C": "c"}


def printf_args(s):
    """{position or name: type}, plus the error when plain and positional are mixed."""
    out, plain, i = {}, 0, 0
    for m in PRINTF.finditer(s):
        if m.group(0) == "%%":
            continue
        t = TYPE.get(m.group(3), m.group(3))
        if m.group(1):
            out[int(m.group(1))] = t
        elif m.group(2):
            out[m.group(2)] = t
        else:
            plain += 1
            out[plain] = t
    return out


def printf_tokens(s):
    """{position or name: the specifier as written}, numbered as printf_args numbers them."""
    out, plain = {}, 0
    for m in PRINTF.finditer(s):
        if m.group(0) == "%%":
            continue
        if m.group(1):
            out[int(m.group(1))] = m.group(0)
        elif m.group(2):
            out[m.group(2)] = m.group(0)
        else:
            plain += 1
            out[plain] = m.group(0)
    return out


def brace_args(s):
    names = [m.group(1) for m in DOUBLE.finditer(s)]
    names += ["{%s}" % m.group(1) for m in SINGLE.finditer(DOUBLE.sub("", s))]
    return names


# --------------------------------------------------------------------------- ICU

class IcuError(Exception):
    pass


def icu_parse(s):
    """Parse an ICU MessageFormat string. Returns [(name, type, {keyword: ...})] for every
    argument, nested ones included. Raises IcuError when the message doesn't parse."""
    args, pos = [], [0]
    n = len(s)

    def message(depth, in_plural):
        if depth > 50:
            raise IcuError("nested more than 50 levels deep")
        while pos[0] < n:
            c = s[pos[0]]
            if c == "'":
                if pos[0] + 1 < n and s[pos[0] + 1] == "'":
                    pos[0] += 2
                elif pos[0] + 1 < n and s[pos[0] + 1] in "{}#|":
                    end = s.find("'", pos[0] + 1)
                    pos[0] = n if end < 0 else end + 1
                else:
                    pos[0] += 1
            elif c == "{":
                pos[0] += 1
                argument(depth)
            elif c == "}":
                if depth == 0:
                    raise IcuError("an unmatched '}' at %d" % pos[0])
                return
            else:
                pos[0] += 1
        if depth:
            raise IcuError("a '{' that is never closed")

    def ws():
        while pos[0] < n and s[pos[0]].isspace():
            pos[0] += 1

    def ident():
        ws()
        m = re.compile(r"[^\s{},'#]+").match(s, pos[0])
        if not m:
            raise IcuError("expected a name at %d" % pos[0])
        pos[0] = m.end()
        return m.group(0)

    def argument(depth):
        name = ident()
        ws()
        if pos[0] < n and s[pos[0]] == "}":
            pos[0] += 1
            args.append((name, "", {}))
            return
        if pos[0] >= n or s[pos[0]] != ",":
            raise IcuError("expected ',' or '}' after %r" % name)
        pos[0] += 1
        kind = ident().lower()
        ws()
        if kind in ("plural", "selectordinal", "select"):
            if pos[0] >= n or s[pos[0]] != ",":
                raise IcuError("expected ',' after %s" % kind)
            pos[0] += 1
            branches = {}
            while True:
                ws()
                if pos[0] < n and s[pos[0]] == "}":
                    pos[0] += 1
                    break
                if pos[0] >= n:
                    raise IcuError("a %s that is never closed" % kind)
                key = ident()
                if key.startswith("offset:"):
                    continue
                ws()
                if pos[0] >= n or s[pos[0]] != "{":
                    raise IcuError("expected '{' after %r in %s" % (key, name))
                pos[0] += 1
                message(depth + 1, kind != "select")
                if pos[0] >= n or s[pos[0]] != "}":
                    raise IcuError("a branch of %s that is never closed" % name)
                pos[0] += 1
                branches[key] = True
            if "other" not in branches:
                raise IcuError("%s %r has no 'other' branch" % (kind, name))
            args.append((name, kind, branches))
        else:
            if pos[0] < n and s[pos[0]] == ",":
                end = s.find("}", pos[0])
                if end < 0:
                    raise IcuError("an argument that is never closed")
                pos[0] = end
            ws()
            if pos[0] >= n or s[pos[0]] != "}":
                raise IcuError("expected '}' to close %r" % name)
            pos[0] += 1
            args.append((name, kind, {}))

    message(0, False)
    return args


ICU_COMPLEX = re.compile(r"\{\s*[\w.]+\s*,\s*(?:plural|select|selectordinal|number|date|time|spellout|ordinal)\b")


def looks_icu(s):
    """An ICU message with a formatted argument. A string with only {name} placeholders is
    checked as plain text, so a dropped placeholder gets its own finding and fix."""
    return "{{" not in s and bool(ICU_COMPLEX.search(s))


# --------------------------------------------------------------------------- checks

def visible(s):
    """Characters a reader sees: markup and placeholders out, combining marks not counted."""
    s = TAG.sub("", s)
    s = PRINTF.sub(lambda m: "%" if m.group(0) == "%%" else "", s)
    s = DOUBLE.sub("", s)
    s = SINGLE.sub("", s)
    return sum(1 for ch in unicodedata.normalize("NFC", s) if not unicodedata.combining(ch))


def tags_of(s):
    return [(m.group(1) == "/", m.group(2).lower(), m.group(4) == "/") for m in TAG.finditer(s)]


def tag_problem(src, tgt):
    a, b = tags_of(src), tags_of(tgt)
    if sorted(a) != sorted(b):
        names = lambda ts: ", ".join("<%s%s%s>" % ("/" if c else "", t, "/" if sc else "") for c, t, sc in ts) or "none"
        return "markup differs from the source: source has %s, target has %s" % (names(a), names(b))
    stack = []
    for close, name, self_close in b:
        if self_close:
            continue
        if not close:
            stack.append(name)
        elif not stack or stack.pop() != name:
            return "markup tags don't nest: </%s> closes the wrong tag" % name
    if stack:
        return "markup tag <%s> is never closed" % stack[-1]
    return None


SCRIPT_OF = (("LATIN", "Latin"), ("CYRILLIC", "Cyrillic"), ("GREEK", "Greek"))


def mixed_script(s):
    for word in re.findall(r"\w+", s):
        seen = set()
        for ch in word:
            if ch.isalpha():
                name = unicodedata.name(ch, "")
                for k, v in SCRIPT_OF:
                    if name.startswith(k):
                        seen.add(v)
        if len(seen) > 1:
            return word, sorted(seen)
    return None


END_PUNCT = set(".!?:…。！？：؟;·।")


def letters(s):
    return sum(1 for ch in TAG.sub("", PRINTF.sub("", SINGLE.sub("", DOUBLE.sub("", s)))) if ch.isalpha())


class Report(object):
    def __init__(self):
        self.failures, self.warnings = [], []

    def add(self, level, locale, key, where, problem, source="", target="", fix=""):
        row = {"locale": locale, "key": key.replace("\x04", " | "), "where": where, "problem": problem,
               "source": source, "target": target}
        if fix:
            row["fix"] = fix
        (self.failures if level == "fail" else self.warnings).append(row)


def where(t, e):
    return "%s:%s" % (os.path.basename(t["path"]), e.line) if e and e.line else os.path.basename(t["path"])


def short(v):
    if isinstance(v, dict):
        return "; ".join("%s: %s" % (k, x) for k, x in v.items())
    return v


def compare_placeholders(src_texts, tgt_text):
    """A problem with one target string's placeholders against the source's, or None."""
    src_join = " ".join(src_texts)
    sp, tp = {}, printf_args(tgt_text)
    shown = {}
    for s in src_texts:
        for k, v in printf_args(s).items():
            sp.setdefault(k, v)
        for k, v in printf_tokens(s).items():
            shown.setdefault(("s", k), v)
    for k, v in printf_tokens(tgt_text).items():
        shown.setdefault(("t", k), v)

    def fmt_printf(k, t, side="s"):
        return shown.get((side, k)) or ("%%%s$%s" % (k, t) if isinstance(k, int) else "%%(%s)%s" % (k, t))
    if len(src_texts) == 1:
        if sp != tp:
            missing = [k for k in sp if k not in tp]
            extra = [k for k in tp if k not in sp]
            changed = [k for k in sp if k in tp and sp[k] != tp[k]]
            bits = []
            if missing:
                bits.append("missing %s" % ", ".join(fmt_printf(k, sp[k]) for k in missing))
            if extra:
                bits.append("extra %s" % ", ".join(fmt_printf(k, tp[k], "t") for k in extra))
            if changed:
                named = all(not isinstance(k, int) for k in changed)
                bits.append("the arguments are %s in the source but %s here, %s" % (
                    " ".join(fmt_printf(k, sp[k]) for k in sorted(sp, key=str)),
                    " ".join(fmt_printf(k, tp[k], "t") for k in sorted(tp, key=str)),
                    "a changed type that msgfmt --check and translation builds reject" if named else
                    "so the values swap at runtime or the app crashes formatting them"))
            if not bits:
                bits.append("arguments reordered")
            return "printf placeholders differ: " + "; ".join(bits)
    else:
        extra = [k for k in tp if k not in sp or sp[k] != tp[k]]
        if extra:
            return "printf placeholder not in the source: %s" % ", ".join(fmt_printf(k, tp[k], "t") for k in extra)
    sb, tb = brace_args(src_join) if len(src_texts) > 1 else brace_args(src_texts[0]), brace_args(tgt_text)
    if len(src_texts) == 1:
        if sorted(sb) != sorted(tb):
            missing = [x for x in set(sb) if sb.count(x) > tb.count(x)]
            extra = [x for x in set(tb) if tb.count(x) > sb.count(x)]
            bits = (["missing " + ", ".join(sorted(fmt_brace(x) for x in missing))] if missing else []) + \
                   (["extra " + ", ".join(sorted(fmt_brace(x) for x in extra))] if extra else [])
            return "placeholders differ: " + "; ".join(bits)
    else:
        extra = sorted(set(tb) - set(sb))
        if extra:
            return "placeholder not in the source: " + ", ".join(fmt_brace(x) for x in extra)
    return None


def fmt_printf(k, t):
    return "%%%s$%s" % (k, t) if isinstance(k, int) else "%%(%s)%s" % (k, t)


def fmt_brace(x):
    return x if x.startswith("{") else "{{%s}}" % x


def required_plurals(lang):
    cats = CLDR.get(lang)
    return set(cats) if cats else None


def check_target(src, tgt, budget, rep):
    loc = tgt["locale"] or "?"
    lang = lang_of(tgt["locale"])
    S, T = src["entries"], tgt["entries"]
    gettext_n = NPLURALS.get(lang)
    if tgt["format"] == "po" and tgt["nplurals"] and gettext_n and tgt["nplurals"] != gettext_n:
        rep.add("fail", loc, "(Plural-Forms header)", os.path.basename(tgt["path"]),
                "the header sets nplurals=%d; %s needs %d" % (tgt["nplurals"], lang, gettext_n))
    for key, se in S.items():
        te = T.get(key)
        w = where(tgt, te)
        if te is None:
            rep.add("fail", loc, key, os.path.basename(tgt["path"]), "missing", short(se.value), "")
            continue
        if tgt["format"] == "android" and te.icu_ok:
            rep.add("fail", loc, key, w, te.icu_ok, short(se.value), short(te.value))
        if te.fuzzy:
            rep.add("warn", loc, key, w, "marked fuzzy: msgfmt leaves it out, so the source text shows",
                    short(se.value), short(te.value))
        if se.plural and not te.plural:
            te = Entry(te.key, {"other": te.value}, te.line, plural=True)
        if not se.plural and te.plural:
            rep.add("fail", loc, key, w, "a plural set where the source has one string", se.value, short(te.value))
            continue
        if se.plural:
            check_plural(se, te, tgt, lang, loc, w, rep)
            src_texts = [x for x in se.value.values() if x]
        else:
            src_texts = [se.value]
            if te.value.strip() == "" and se.value.strip():
                rep.add("fail", loc, key, w, "empty translation", se.value, te.value)
                continue
        for label, tv in (te.value.items() if te.plural else [("", te.value)]):
            if te.plural and tv == "":
                continue
            tag = ("[%s] " % label) if label else ""
            sv = src_texts[0] if len(src_texts) == 1 else (se.value.get(label) or se.value.get("other") or src_texts[0])
            icu_src = [x for x in src_texts if looks_icu(x)]
            icu_handled = False
            if icu_src:
                try:
                    sargs = [a for x in icu_src for a in icu_parse(x)]
                    src_ok = True
                except IcuError:
                    src_ok = False
                if src_ok:
                    icu_handled = True
                    try:
                        targs = icu_parse(tv)
                    except IcuError as e:
                        rep.add("fail", loc, key, w, tag + "ICU message doesn't parse: %s" % e, sv, tv)
                        continue
                    check_icu(sargs, targs, lang, loc, key, w, tag, sv, tv, rep)
            if not icu_handled:
                last = label == "other" or (tgt["format"] == "po" and label == "[%d]" % (len(te.value) - 1))
                strict = (not se.plural) or (last and len(te.value) > 1)
                p = compare_placeholders([se.value.get("other", sv)] if se.plural and strict else
                                         (src_texts if se.plural else [sv]), tv)
                if p:
                    rep.add("fail", loc, key, w, tag + p, sv, tv, fix_for(sv, tv))
            elif PRINTF.search(sv.replace("%%", "")) or PRINTF.search(tv.replace("%%", "")):
                p = compare_placeholders([sv], tv)
                if p and "printf" in p:
                    rep.add("fail", loc, key, w, tag + p, sv, tv)
            t = tag_problem(sv, tv)
            if t:
                rep.add("fail", loc, key, w, tag + t, sv, tv)
            limit = budget_limit(budget, key, sv)
            if limit is not None and visible(tv) > limit:
                rep.add("fail", loc, key, w, tag + "%d characters, over the budget of %d" % (visible(tv), limit), sv, tv)
            style_warnings(sv, tv, loc, key, w, tag, rep, tgt)
    for key, te in T.items():
        if key not in S and tgt["format"] == "android" and te.icu_ok:
            rep.add("fail", loc, key, where(tgt, te), te.icu_ok, "", short(te.value))
        if key not in S:
            rep.add("warn", loc, key, where(tgt, te), "not in the source (stale or misspelled key)", "", short(te.value))


def check_plural(se, te, tgt, lang, loc, w, rep):
    if tgt["format"] == "po":
        need = NPLURALS.get(lang)
        have = te.gettext_n if te.gettext_n is not None else len(te.value)
        if need and have != need:
            rep.add("fail", loc, se.key, w, "has %d plural form%s; %s needs %d (msgstr[0] to msgstr[%d])" % (
                have, "" if have == 1 else "s", lang, need, need - 1),
                    short(se.value), short(te.value))
        for k, v in te.value.items():
            if not v.strip():
                rep.add("fail", loc, se.key, w, "plural form %s is empty" % k, short(se.value), short(te.value))
        return
    need = required_plurals(lang)
    have = {k for k, v in te.value.items() if v != ""}
    if need is None:
        if "other" not in have:
            rep.add("fail", loc, se.key, w, "no 'other' plural form", short(se.value), short(te.value))
        return
    missing = need - have
    soft = missing & SOFT.get(lang, set())
    hard = missing - soft
    if hard:
        rep.add("fail", loc, se.key, w, "plural forms %s missing; %s needs %s" % (
            ", ".join(c for c in CATEGORIES if c in hard), lang, ", ".join(c for c in CATEGORIES if c in need)),
            short(se.value), short(te.value))
    if soft:
        rep.add("warn", loc, se.key, w, "plural form 'many' missing; %s uses it for large numbers such as 1 000 000" % lang,
                short(se.value), short(te.value))
    extra = {k for k in have if k in CATEGORIES} - need
    if extra:
        rep.add("warn", loc, se.key, w, "plural forms %s are never used in %s" % (
            ", ".join(c for c in CATEGORIES if c in extra), lang), short(se.value), short(te.value))


def check_icu(sargs, targs, lang, loc, key, w, tag, sv, tv, rep):
    sn = {(a, k if k in ("plural", "select", "selectordinal") else "") for a, k, _ in sargs}
    tn = {(a, k if k in ("plural", "select", "selectordinal") else "") for a, k, _ in targs}
    if sn != tn:
        missing = sorted("{%s}" % a for a, _ in sn - tn)
        extra = sorted("{%s}" % a for a, _ in tn - sn)
        bits = (["missing " + ", ".join(missing)] if missing else []) + (["extra " + ", ".join(extra)] if extra else [])
        rep.add("fail", loc, key, w, tag + "ICU arguments differ: " + "; ".join(bits or ["an argument changed type"]), sv, tv)
    sel_src = {a: set(b) for a, k, b in sargs if k == "select"}
    for a, k, b in targs:
        if k == "select" and a in sel_src:
            lost = sel_src[a] - set(b)
            if lost:
                rep.add("fail", loc, key, w, tag + "select %r lost keyword %s (keywords are code, not text)" % (
                    a, ", ".join(sorted(lost))), sv, tv)
        if k == "plural":
            need = required_plurals(lang)
            if need:
                have = {x for x in b if x in CATEGORIES}
                missing = need - have - SOFT.get(lang, set())
                if missing:
                    rep.add("fail", loc, key, w, tag + "ICU plural %r is missing %s; %s needs %s" % (
                        a, ", ".join(c for c in CATEGORIES if c in missing), lang,
                        ", ".join(c for c in CATEGORIES if c in need)), sv, tv)
            bad = [x for x in b if x not in CATEGORIES and not re.match(r"^=\d+$", x)]
            if bad:
                rep.add("fail", loc, key, w, tag + "ICU plural %r has keyword %s, which isn't a plural category" % (
                    a, ", ".join(sorted(bad))), sv, tv)


def fix_for(sv, tv):
    """A mechanical fix when exactly one placeholder was dropped and the source has it once:
    say what to restore, never where in the sentence, which takes the language."""
    sb, tb = brace_args(sv), brace_args(tv)
    sp, tp = printf_args(sv), printf_args(tv)
    gone = [x for x in set(sb) if sb.count(x) > tb.count(x)]
    if len(gone) == 1 and sp == tp and not [x for x in tb if x not in sb]:
        return "restore %s" % fmt_brace(gone[0])
    if sb == tb and len(sp) > 1 and sorted(sp.values()) == sorted(tp.values()) and set(sp) == set(tp) and sp != tp:
        # Number each of the target's plain specifiers with the source argument of its type, in order.
        free = {t: [k for k in sorted(k for k in sp if isinstance(k, int)) if sp[k] == t] for t in set(sp.values())}
        out, ok = [], True

        def num(m):
            nonlocal ok
            if m.group(0) == "%%" or m.group(1) or m.group(2):
                return m.group(0)
            t = TYPE.get(m.group(3), m.group(3))
            if not free.get(t):
                ok = False
                return m.group(0)
            k = free[t].pop(0)
            return m.group(0).replace("%", "%%%d$" % k, 1)
        fixed = PRINTF.sub(num, tv)
        return ("use %s" % fixed) if ok and len({v for v in sp.values()}) == len(sp) else \
            "number the arguments in source order (%s) so a translation can move them" % " ".join(
                "%%%d$%s" % (k, v) for k, v in sorted(sp.items()))
    return ""


def style_warnings(sv, tv, loc, key, w, tag, rep, tgt):
    if sv == tv and letters(sv) > 3 and not re.match(r"^[\w.+-]+@|^https?://", sv) and lang_of(tgt["locale"]) != "en":
        rep.add("warn", loc, key, w, tag + "identical to the source: untranslated?", sv, tv)
    if (sv[:1].isspace()) != (tv[:1].isspace()) or (sv[-1:].isspace()) != (tv[-1:].isspace()):
        rep.add("warn", loc, key, w, tag + "leading or trailing space changed", repr(sv), repr(tv))
    s_end = sv.rstrip()[-1:] if sv.rstrip() else ""
    t_end = tv.rstrip()[-1:] if tv.rstrip() else ""
    if s_end in END_PUNCT and t_end not in END_PUNCT and tv.strip():
        rep.add("warn", loc, key, w, tag + "ending punctuation %r dropped" % s_end, sv, tv)
    mix = mixed_script(tv)
    if mix:
        rep.add("warn", loc, key, w, tag + "%r mixes %s letters (a look-alike typed by mistake?)" % (
            mix[0], " and ".join(mix[1])), sv, tv)


# --------------------------------------------------------------------------- budget

def load_budget(path):
    text = read_text(path)
    if path.lower().endswith(".csv"):
        keys = {}
        rows = csv.DictReader(io.StringIO(text))
        cols = {c.lower().strip(): c for c in (rows.fieldnames or [])}
        if "key" not in cols or not ({"max", "max_chars", "limit"} & set(cols)):
            raise BadInput("%s: a budget CSV needs columns key and max" % path)
        mc = cols.get("max") or cols.get("max_chars") or cols.get("limit")
        for r in rows:
            try:
                keys[r[cols["key"]].strip()] = int(r[mc])
            except (TypeError, ValueError):
                raise BadInput("%s: %r is not a number of characters" % (path, r.get(mc)))
        return {"keys": keys, "ratio": None, "ratio_min_source": 10}
    try:
        doc = json.loads(text)
    except ValueError as e:
        raise BadInput("%s: not valid JSON: %s" % (path, e))
    if not isinstance(doc, dict):
        raise BadInput("%s: the budget must be an object" % path)
    keys = doc.get("keys", {})
    if not isinstance(keys, dict) or not all(isinstance(v, int) and not isinstance(v, bool) for v in keys.values()):
        raise BadInput("%s: \"keys\" must map each key to a whole number of characters" % path)
    ratio = doc.get("ratio")
    if ratio is not None and (not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or ratio <= 0):
        raise BadInput("%s: \"ratio\" must be a positive number" % path)
    rmin = doc.get("ratio_min_source", 10)
    if not isinstance(rmin, int) or isinstance(rmin, bool):
        raise BadInput("%s: \"ratio_min_source\" must be a whole number" % path)
    return {"keys": keys, "ratio": ratio, "ratio_min_source": rmin}


def budget_limit(budget, key, sv):
    if not budget:
        return None
    k = key.replace("\x04", " | ")
    if k in budget["keys"]:
        return budget["keys"][k]
    if budget["ratio"] and visible(sv) >= budget["ratio_min_source"]:
        return int(math.ceil(visible(sv) * budget["ratio"]))
    return None


# --------------------------------------------------------------------------- output

def esc(s, width=90):
    s = "" if s is None else str(s)
    s = s.replace("\n", "\\n").replace("|", "\\|")
    return s if len(s) <= width else s[:width - 3] + "..."


def render(src, targets, rep, budget):
    out = ["# Translation check", ""]
    out.append("Source: `%s` (%s), %d strings." % (os.path.basename(src["path"]), src["locale"] or "locale unknown",
                                                    len(src["entries"])))
    for t in targets:
        out.append("Target: `%s` (%s), %d strings." % (os.path.basename(t["path"]), t["locale"] or "locale unknown",
                                                       len(t["entries"])))
    out.append("")
    nf, nw = len(rep.failures), len(rep.warnings)
    out.append("**%s.** %d warning(s)." % ("No failures" if not nf else "%d failure(s)" % nf, nw))
    if not budget:
        out.append("No character budget given, so string lengths were not checked.")
    out.append("")
    for title, rows in (("Failures", rep.failures), ("Warnings", rep.warnings)):
        if not rows:
            continue
        out += ["## " + title, "", "| Locale | Key | Problem | Where | Source | Target | Fix |", "|---|---|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: (r["locale"], r["key"])):
            out.append("| %s | `%s` | %s | %s | %s | %s | %s |" % (
                esc(r["locale"]), esc(r["key"]), esc(r["problem"], 240), esc(r["where"]), esc(r["source"]),
                esc(r["target"]), esc(r.get("fix", ""), 160)))
        out.append("")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source")
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--locale", action="append", default=[],
                    help="the locale of each target, in order (overrides the path)")
    ap.add_argument("--source-locale", default="")
    ap.add_argument("--budget", help="JSON or CSV of character limits")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    try:
        try:
            src = load(a.source, True, a.source_locale)
        except ParseError as e:
            raise BadInput("%s: %s" % (a.source, e))
        budget = load_budget(a.budget) if a.budget else None
        rep, targets = Report(), []
        for i, path in enumerate(a.targets):
            override = a.locale[i] if i < len(a.locale) else ""
            try:
                t = load(path, False, override)
            except ParseError as e:
                loc = override or detect_locale(path) or "?"
                rep.add("fail", loc, "(file)", os.path.basename(path), "the file doesn't parse: %s" % e)
                continue
            targets.append(t)
            check_target(src, t, budget, rep)
    except BadInput as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if a.json:
        text = json.dumps({"source": {"file": src["path"], "locale": src["locale"], "strings": len(src["entries"])},
                           "targets": [{"file": t["path"], "locale": t["locale"], "format": t["format"],
                                        "strings": len(t["entries"])} for t in targets],
                           "lengths_checked": bool(budget), "failures": rep.failures, "warnings": rep.warnings},
                          ensure_ascii=False, indent=2) + "\n"
    else:
        text = render(src, targets, rep, budget)
    if a.out:
        try:
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as e:
            print("error: can't write %s: %s" % (a.out, e.strerror or e), file=sys.stderr)
            return 2
    else:
        sys.stdout.write(text)
    return 1 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())

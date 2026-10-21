import os
import re
import struct
import unittest
import zipfile
import zlib
from xml.etree import ElementTree as ET

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "md-to-docx", "md_to_docx.py"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def png(path, w, h, ppm=None):
    """A valid w x h greyscale PNG; `ppm` adds a pHYs chunk in pixels per metre."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    if ppm:
        data += chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
    data += chunk(b"IDAT", zlib.compress(b"".join(b"\x00" + b"\xff" * w for _ in range(h))))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return path


def convert(d, md, *flags, name="doc.md"):
    """Write `md`, convert it, return (exit code, stdout, stderr, {part name: text})."""
    src = write(os.path.join(d, name), md)
    out = os.path.join(d, "out.docx")
    code, so, se = run(SKILL, SCRIPT, src, "-o", out, *flags)
    parts = {}
    if os.path.exists(out):
        with zipfile.ZipFile(out) as z:
            parts = {n: z.read(n) for n in z.namelist()}
            parts = {n: (v.decode("utf-8") if n.endswith((".xml", ".rels")) else v) for n, v in parts.items()}
    return code, so, se, parts


def paragraphs(document_xml):
    """[(style or '', text)] for each body paragraph."""
    body = ET.fromstring(document_xml).find(W + "body")
    out = []
    for p in body.iter(W + "p"):
        ps = p.find(W + "pPr/" + W + "pStyle")
        out.append((ps.get(W + "val") if ps is not None else "", "".join(t.text or "" for t in p.iter(W + "t"))))
    return out


class MdToDocxTest(unittest.TestCase):
    def test_package_has_every_part_and_each_xml_part_parses(self):
        with workdir() as d:
            code, so, se, parts = convert(d, "# Title\n\nBody text.\n")
        self.assertEqual(code, 0, se)
        for name in ("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml",
                     "word/numbering.xml", "word/settings.xml", "word/_rels/document.xml.rels",
                     "docProps/core.xml", "docProps/app.xml"):
            self.assertIn(name, parts)
            ET.fromstring(parts[name])
        self.assertIn("1 heading, 1 paragraph", so)
        self.assertEqual(se, "")

    def test_headings_use_builtin_styles_and_h5_becomes_heading4_with_warning(self):
        md = "# One\n\n## Two\n\n### Three\n\n#### Four\n\n##### Five\n"
        with workdir() as d:
            code, so, se, parts = convert(d, md)
        self.assertEqual(code, 0)
        self.assertEqual(paragraphs(parts["word/document.xml"]),
                         [("Heading1", "One"), ("Heading2", "Two"), ("Heading3", "Three"),
                          ("Heading4", "Four"), ("Heading4", "Five")])
        self.assertIn("WARN line 9: h5 has no Word equivalent here; written as Heading 4", se)
        self.assertIn("1 warning(s)", so)

    def test_setext_headings_are_recognised(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "Report\n======\n\nPart\n----\n")
        self.assertEqual(paragraphs(parts["word/document.xml"]), [("Heading1", "Report"), ("Heading2", "Part")])

    def test_inline_bold_italic_strike_and_code_runs(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "A **b** *i* ~~s~~ `c` ***bi***\n")
        doc = parts["word/document.xml"]
        self.assertIn('<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">b</w:t></w:r>', doc)
        self.assertIn('<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">i</w:t></w:r>', doc)
        self.assertIn('<w:r><w:rPr><w:strike/></w:rPr><w:t xml:space="preserve">s</w:t></w:r>', doc)
        self.assertRegex(doc, r'<w:rFonts w:ascii="Consolas"[^>]*/><w:sz w:val="20"/>.*?<w:t xml:space="preserve">c</w:t>')
        self.assertIn('<w:rPr><w:b/><w:i/></w:rPr><w:t xml:space="preserve">bi</w:t>', doc)

    def test_snake_case_words_are_not_italicised(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "Set max_retry_count here.\n")
        self.assertNotIn("<w:i/>", parts["word/document.xml"])
        self.assertIn("Set max_retry_count here.", parts["word/document.xml"])

    def test_external_links_are_hyperlinks_with_external_relationships(self):
        md = "See [the guide](https://example.test/g), <https://example.test/a> and https://example.test/b.\n"
        with workdir() as d:
            _, so, _, parts = convert(d, md)
        doc, rels = parts["word/document.xml"], parts["word/_rels/document.xml.rels"]
        rids = re.findall(r'<w:hyperlink r:id="(rId\d+)"', doc)
        self.assertEqual(len(rids), 3)
        for rid, url in zip(rids, ("https://example.test/g", "https://example.test/a", "https://example.test/b")):
            self.assertIn('Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                          'hyperlink" Target="%s" TargetMode="External"' % (rid, url), rels)
        self.assertIn("3 links", so)
        # the bare URL stops before the sentence's full stop
        self.assertNotIn('Target="https://example.test/b."', rels)

    def test_reference_style_link_resolves(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "Read [the spec][s].\n\n[s]: https://example.test/spec\n")
        self.assertIn('Target="https://example.test/spec"', parts["word/_rels/document.xml.rels"])

    def test_anchor_link_jumps_to_heading_bookmark(self):
        md = "# Intro\n\nGo to [rollout](#rollout-plan).\n\n## Rollout plan\n"
        with workdir() as d:
            _, _, se, parts = convert(d, md)
        doc = parts["word/document.xml"]
        self.assertIn('<w:bookmarkStart w:id="1" w:name="h_rollout_plan"/>', doc)
        self.assertIn('<w:hyperlink w:anchor="h_rollout_plan"', doc)
        self.assertEqual(se, "")

    def test_anchor_link_to_missing_heading_warns_and_stays_text(self):
        with workdir() as d:
            _, _, se, parts = convert(d, "# A\n\nSee [x](#nowhere).\n")
        self.assertIn("WARN line 3: link to #nowhere has no matching heading; kept as plain text", se)
        self.assertNotIn("w:hyperlink", parts["word/document.xml"])

    def test_bullets_numbering_start_and_nesting(self):
        md = "- one\n- two\n  - nested\n\nText.\n\n3. third\n4. fourth\n"
        with workdir() as d:
            _, _, se, parts = convert(d, md)
        doc, num = parts["word/document.xml"], parts["word/numbering.xml"]
        items = re.findall(r'<w:ilvl w:val="(\d)"/><w:numId w:val="(\d+)"/>', doc)
        self.assertEqual(items, [("0", "1"), ("0", "1"), ("1", "1"), ("0", "2"), ("0", "2")])
        # numId 2 is a decimal list starting at 3
        abstract2 = re.search(r'<w:abstractNum w:abstractNumId="2">.*?</w:abstractNum>', num).group(0)
        self.assertIn('<w:start w:val="3"/><w:numFmt w:val="decimal"/>', abstract2)
        self.assertEqual(se, "")

    def test_list_nested_past_two_levels_is_flattened_with_warning(self):
        with workdir() as d:
            _, _, se, parts = convert(d, "- a\n  - b\n    - c\n")
        self.assertIn("WARN line 3: list nested deeper than one level", se)
        levels = re.findall(r'<w:ilvl w:val="(\d)"/>', parts["word/document.xml"])
        self.assertEqual(levels, ["0", "1", "1"])

    def test_task_list_items_get_boxes(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "- [ ] open\n- [x] done\n")
        texts = [t for _, t in paragraphs(parts["word/document.xml"])]
        self.assertEqual(texts, ["☐ open", "☒ done"])

    def test_table_header_repeats_is_shaded_bold_and_keeps_alignment(self):
        md = "| Region | Tickets |\n|:---|---:|\n| North | 120 |\n| South |\n"
        with workdir() as d:
            _, so, se, parts = convert(d, md)
        doc = parts["word/document.xml"]
        self.assertEqual(doc.count("<w:tr>"), 3)
        self.assertEqual(doc.count("<w:tblHeader/>"), 1)
        self.assertIn('w:fill="F2F2F2"/></w:tcPr>', doc)
        self.assertIn('<w:rPr><w:b/></w:rPr><w:t xml:space="preserve">Region</w:t>', doc)
        self.assertEqual(re.findall(r'<w:jc w:val="(\w+)"/>', doc), ["left", "right"] * 3)
        self.assertIn("WARN line 1: table row 2 has 1 cells, header has 2; padded or cut", se)
        self.assertIn("1 table", so)

    def test_fenced_code_is_one_source_code_paragraph_with_breaks_and_tabs(self):
        with workdir() as d:
            _, _, _, parts = convert(d, "```python\ndef f():\n\treturn 1 < 2\n```\n")
        doc = parts["word/document.xml"]
        self.assertIn('<w:pStyle w:val="SourceCode"/></w:pPr><w:r><w:t xml:space="preserve">def f():</w:t>'
                      '<w:br/><w:t xml:space="preserve">    return 1 &lt; 2</w:t></w:r>', doc)

    def test_mermaid_and_unclosed_fence_warn(self):
        with workdir() as d:
            _, _, se, _ = convert(d, "```mermaid\ngraph TD\n```\n\n```\nopen\n")
        self.assertIn("WARN line 1: mermaid block kept as code text", se)
        self.assertIn("WARN line 5: code fence never closed", se)

    def test_blockquote_uses_quote_style(self):
        with workdir() as d:
            _, so, _, parts = convert(d, "> Keep it short.\n")
        self.assertEqual(paragraphs(parts["word/document.xml"]), [("Quote", "Keep it short.")])
        self.assertIn("1 quote", so)

    def test_hr_is_a_rule_by_default_and_a_page_break_with_flag(self):
        with workdir() as d:
            _, _, _, rule = convert(d, "A\n\n---\n\nB\n")
            _, _, _, brk = convert(d, "A\n\n---\n\nB\n", "--hr", "page-break")
        self.assertIn("<w:pBdr><w:bottom", rule["word/document.xml"])
        self.assertNotIn('w:type="page"', rule["word/document.xml"])
        self.assertIn('<w:br w:type="page"/>', brk["word/document.xml"])

    def test_page_size_letter_by_default_and_a4_with_flag(self):
        with workdir() as d:
            _, so, _, letter = convert(d, "Text\n")
            _, so4, _, a4 = convert(d, "Text\n", "--page", "a4")
        self.assertIn('<w:pgSz w:w="12240" w:h="15840"/>', letter["word/document.xml"])
        self.assertIn('<w:pgSz w:w="11906" w:h="16838"/>', a4["word/document.xml"])
        self.assertIn("page a4", so4)

    def test_png_embedded_at_real_size_from_its_dpi(self):
        with workdir() as d:
            png(os.path.join(d, "a.png"), 96, 48)              # 96 dpi default: 1in x 0.5in
            png(os.path.join(d, "b.png"), 300, 150, ppm=11811)  # 300 dpi: 1in x 0.5in
            code, so, se, parts = convert(d, "![Chart A](a.png)\n\n![Chart B](b.png)\n")
        self.assertEqual(code, 0, se)
        doc, rels = parts["word/document.xml"], parts["word/_rels/document.xml.rels"]
        extents = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"/>', doc)
        self.assertEqual(extents[0], ("914400", "457200"))
        cx, cy = map(int, extents[1])
        self.assertAlmostEqual(cx, 914400, delta=200)
        self.assertAlmostEqual(cy, 457200, delta=200)
        self.assertIn('descr="Chart A"', doc)
        self.assertIn("word/media/image1.png", parts)
        self.assertIn('Target="media/image2.png"', rels)
        self.assertIn('<w:jc w:val="center"/>', doc)
        self.assertIn("2 images", so)

    def test_wide_image_is_shrunk_to_page_width(self):
        with workdir() as d:
            png(os.path.join(d, "w.png"), 1920, 96)   # 20in wide at 96 dpi
            _, _, _, parts = convert(d, "![w](w.png)\n")
        cx, cy = map(int, re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"/>', parts["word/document.xml"]).groups())
        self.assertEqual(cx, (12240 - 2 * 1440) * 635)   # letter content width in EMU
        self.assertAlmostEqual(cy, 914400 * 6.5 / 20, delta=5)

    def test_missing_remote_and_non_png_images_write_alt_text_and_warn(self):
        md = "![Gone](gone.png)\n\n![Web](https://example.test/x.png)\n\n![Gif](g.gif)\n"
        with workdir() as d:
            write(os.path.join(d, "g.gif"), "GIF89a")
            _, _, se, parts = convert(d, md)
        texts = [t for _, t in paragraphs(parts["word/document.xml"])]
        self.assertEqual(texts, ["[Gone]", "[Web]", "[Gif]"])
        self.assertIn("WARN line 1: image gone.png not found", se)
        self.assertIn("WARN line 3: remote or inline image https://example.test/x.png not embedded", se)
        self.assertIn("WARN line 5: image g.gif is not PNG or JPEG", se)
        self.assertFalse(any(n.startswith("word/media/") for n in parts))

    def test_footnotes_raw_html_and_inline_tags_are_dropped_with_warnings(self):
        md = "Claim[^1] with <span>tag</span>.<br>Next.\n\n<div>\nblock\n</div>\n\n[^1]: The source.\n"
        with workdir() as d:
            _, _, se, parts = convert(d, md)
        doc = parts["word/document.xml"]
        self.assertIn("WARN line 1: footnote reference [^1] dropped", se)
        self.assertIn("WARN line 1: inline HTML tag <span> removed (text kept)", se)
        self.assertIn("WARN line 3: raw HTML block dropped (lines 3-5)", se)
        self.assertIn("WARN line 7: footnote definition dropped", se)
        self.assertEqual(paragraphs(doc), [("", "Claim with tag.Next.")])
        self.assertIn("<w:br/>", doc)
        self.assertNotIn("block", doc)
        self.assertNotIn("The source", doc)

    def test_title_from_front_matter_then_flag_then_first_h1(self):
        fm = "---\ntitle: \"Vendor onboarding\"\nauthor: x\n---\n# Heading\n"
        with workdir() as d:
            _, so, se, parts = convert(d, fm)
            self.assertIn("<dc:title>Vendor onboarding</dc:title>", parts["docProps/core.xml"])
            self.assertIn("WARN line 1: YAML front matter dropped (lines 1-4); its title is used", se)
            self.assertEqual(paragraphs(parts["word/document.xml"]), [("Heading1", "Heading")])
            _, _, _, parts = convert(d, fm, "--title", "Given & named")
            self.assertIn("<dc:title>Given &amp; named</dc:title>", parts["docProps/core.xml"])
            _, _, _, parts = convert(d, "# First *one*\n\n# Second\n")
            self.assertIn("<dc:title>First one</dc:title>", parts["docProps/core.xml"])
            _, _, _, parts = convert(d, "No heading.\n", name="field-notes.md")
            self.assertIn("<dc:title>field-notes</dc:title>", parts["docProps/core.xml"])

    def test_brand_sets_fonts_and_colours_and_bad_hex_warns(self):
        brand = ('{"fonts": {"heading": {"family": "Georgia"}, "body": {"family": "Verdana"}},'
                 ' "colors": {"primary": "#0a7f3c", "text": "teal"}}')
        with workdir() as d:
            bp = write(os.path.join(d, "brand.json"), brand)
            _, so, se, parts = convert(d, "# H\n\nBody\n", "--brand", bp)
        styles = parts["word/styles.xml"]
        self.assertIn('<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia" w:cs="Georgia"/><w:b/><w:color w:val="0A7F3C"/>',
                      styles)
        self.assertIn('<w:rFonts w:ascii="Verdana" w:hAnsi="Verdana" w:eastAsia="Verdana"', styles)
        self.assertIn('<w:color w:val="222222"/>', styles)  # bad text colour keeps the default
        self.assertIn("brand colors.text 'teal' is not a 6-digit hex code; default kept", se)
        self.assertIn("brand: Georgia / Verdana", so)

    def test_unreadable_or_non_object_brand_fails_clearly(self):
        with workdir() as d:
            bad = write(os.path.join(d, "bad.json"), "{nope")
            arr = write(os.path.join(d, "arr.json"), "[]")
            c1, _, e1, _ = convert(d, "x\n", "--brand", bad)
            c2, _, e2, _ = convert(d, "x\n", "--brand", arr)
            c3, _, e3, _ = convert(d, "x\n", "--brand", os.path.join(d, "none.json"))
        self.assertEqual((c1, c2, c3), (1, 1, 1))
        self.assertIn("ERROR cannot read brand file", e1)
        self.assertIn("is not a JSON object", e2)
        self.assertIn("ERROR cannot read brand file", e3)

    def test_control_characters_are_stripped_so_the_xml_stays_valid(self):
        with workdir() as d:
            code, _, _, parts = convert(d, "Bell\x07 and form\x0cfeed & <ok>\n")
        self.assertEqual(code, 0)
        ET.fromstring(parts["word/document.xml"])
        self.assertIn("Bell and formfeed &amp; ", parts["word/document.xml"])

    def test_bad_inputs_exit_1_with_a_message(self):
        with workdir() as d:
            empty = write(os.path.join(d, "empty.md"), "\n\n")
            with open(os.path.join(d, "latin.md"), "wb") as f:
                f.write("café".encode("latin-1"))
            cases = [
                ((os.path.join(d, "missing.md"), "-o", os.path.join(d, "o.docx")), "ERROR cannot read"),
                ((empty, "-o", os.path.join(d, "o.docx")), "has no content to convert"),
                ((os.path.join(d, "latin.md"), "-o", os.path.join(d, "o.docx")), "is not UTF-8 text"),
                ((empty, "-o", os.path.join(d, "o.pdf")), "output must end in .docx"),
                ((empty, "-o", os.path.join(d, "nodir", "o.docx")), "does not exist"),
            ]
            for args, msg in cases:
                code, _, err = run(SKILL, SCRIPT, *args)
                self.assertEqual(code, 1, args)
                self.assertIn(msg, err)
                self.assertNotIn("Traceback", err)
            self.assertFalse(os.path.exists(os.path.join(d, "o.docx")))


class MdToDocxFunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def test_split_row_keeps_escaped_pipes_and_pipes_in_code(self):
        self.assertEqual(self.m.split_row("| a \\| b | `x|y` | c |"), ["a | b", "`x|y`", "c"])

    def test_image_size_reads_png_dpi_and_jpeg_dimensions(self):
        with workdir() as d:
            p = png(os.path.join(d, "a.png"), 10, 20, ppm=3780)  # ~96 dpi
            w, h, dx, dy, kind = self.m.image_size(p)
            self.assertEqual((w, h, kind), (10, 20, "png"))
            self.assertAlmostEqual(dx, 96.0, places=0)
            jpg = os.path.join(d, "a.jpg")
            app0 = b"JFIF\x00\x01\x01\x01" + struct.pack(">HH", 72, 72) + b"\x00\x00"
            sof = b"\x08" + struct.pack(">HH", 30, 40) + b"\x01\x01\x11\x00"
            with open(jpg, "wb") as f:
                f.write(b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", len(app0) + 2) + app0 +
                        b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xd9")
            self.assertEqual(self.m.image_size(jpg), (40, 30, 72.0, 72.0, "jpeg"))
            self.assertIsNone(self.m.image_size(write(os.path.join(d, "t.png"), "text")))


if __name__ == "__main__":
    unittest.main()

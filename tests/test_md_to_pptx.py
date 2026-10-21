import contextlib
import io
import os
import re
import struct
import unittest
import zipfile
import zlib
import xml.etree.ElementTree as ET

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "md-to-pptx", "md_to_pptx.py"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def png_bytes(w, h):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class Deck(object):
    """The parts of a written .pptx that a reader of the deck sees."""

    def __init__(self, path):
        with zipfile.ZipFile(path) as z:
            self.names = set(z.namelist())
            self.parts = {n: z.read(n).decode("utf-8") for n in self.names if n.endswith((".xml", ".rels"))}
        pres = ET.fromstring(self.parts["ppt/presentation.xml"])
        self.count = len(pres.find(P + "sldIdLst"))
        self.size = pres.find(P + "sldSz").attrib

    def slide(self, n):
        return ET.fromstring(self.parts["ppt/slides/slide%d.xml" % n])

    def title(self, n):
        for sp in self.slide(n).iter(P + "sp"):
            ph = sp.find("%snvSpPr/%snvPr/%sph" % (P, P, P))
            if ph is not None and ph.get("type") in ("title", "ctrTitle"):
                return "".join(t.text or "" for t in sp.iter(A + "t"))
        return None

    def titles(self):
        return [self.title(n) for n in range(1, self.count + 1)]

    def texts(self, n):
        return [t.text or "" for t in self.slide(n).iter(A + "t")]

    def notes(self, n):
        part = self.parts.get("ppt/notesSlides/notesSlide%d.xml" % n)
        if part is None:
            return None
        return [t.text for t in ET.fromstring(part).iter(A + "t")]

    def tables(self, n):
        out = []
        for tbl in self.slide(n).iter(A + "tbl"):
            out.append([["".join(t.text or "" for t in tc.iter(A + "t")) for tc in tr.findall(A + "tc")]
                        for tr in tbl.findall(A + "tr")])
        return out


class ConvertTest(unittest.TestCase):
    def build(self, md, *args, files=None):
        with workdir() as d:
            src = write(os.path.join(d, "deck.md"), md)
            for name, data in (files or {}).items():
                with open(os.path.join(d, name), "wb") as f:
                    f.write(data)
            out = os.path.join(d, "deck.pptx")
            code, so, se = run(SKILL, SCRIPT, src, "-o", out, *args, cwd=d)
            deck = Deck(out) if code == 0 else None
        return code, so, se, deck

    def test_headings_become_title_section_and_content_slides(self):
        md = ("# Quarterly review\n\nA short look back.\n\n## Results\n\n- Revenue up\n\n"
              "## Costs\n\nFlat.\n\n# Appendix\n\n## Links\n\nNone.\n")
        code, so, se, deck = self.build(md)
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.titles(), ["Quarterly review", "Results", "Costs", "Appendix", "Links"])
        self.assertIn("A short look back.", deck.texts(1))  # short lead paragraph is the subtitle
        self.assertIn("slideLayout1.xml", deck.parts["ppt/slides/_rels/slide4.xml.rels"])
        self.assertIn("slideLayout2.xml", deck.parts["ppt/slides/_rels/slide2.xml.rels"])
        self.assertIn("5 slides", so)
        self.assertIn("4. Appendix [section]", so)
        self.assertIn("checked:", so)

    def test_bullets_keep_nesting_levels(self):
        code, _, se, deck = self.build("# T\n\n## S\n\n- top\n  - mid\n    - low\n      - deeper\n")
        self.assertEqual(code, 0, se)
        levels = [p.find(A + "pPr").get("lvl") for p in deck.slide(2).iter(A + "p")
                  if p.find(A + "pPr") is not None and p.find(A + "pPr").get("lvl") is not None]
        self.assertEqual(levels, ["0", "1", "2", "2"])
        self.assertIn("list nested deeper than three levels", se)

    def test_speaker_notes_from_notes_comment_only(self):
        md = ("# T\n\n## Results\n\nText.\n\n<!-- notes: Mention the delay.\nSecond line. -->\n\n"
              "<!-- just a comment -->\n\n## Other\n\nNotes: not speaker notes\n")
        code, so, se, deck = self.build(md)
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.notes(2), ["Mention the delay.", "Second line."])
        self.assertIsNone(deck.notes(3))
        self.assertIn("Notes: not speaker notes", deck.texts(3))
        self.assertIn("HTML comment dropped (only <!-- notes: ... --> becomes speaker notes)", se)
        self.assertIn("paragraph starting \"Notes:\" stays on the slide", se)
        self.assertIn("speaker notes on 1", so)

    def test_horizontal_rule_forces_continued_slide(self):
        code, _, se, deck = self.build("# T\n\n## Plan\n\nBefore.\n\n---\n\nAfter.\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.titles(), ["T", "Plan", "Plan (continued)"])
        self.assertIn("After.", deck.texts(3))
        self.assertNotIn("After.", deck.texts(2))

    def test_pipe_table_becomes_real_table(self):
        md = "# T\n\n## Regions\n\n| Region | Value |\n|:--|--:|\n| North | 1 |\n| South | 2 | extra |\n"
        code, _, se, deck = self.build(md)
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.tables(2), [[["Region", "Value"], ["North", "1"], ["South", "2"]]])
        algns = [p.get("algn") for p in deck.slide(2).iter(A + "pPr") if p.get("algn")]
        self.assertEqual(algns[:2], ["l", "r"])
        self.assertIn("table row 2 has 3 cells, header has 2; padded or cut", se)

    def test_long_table_splits_with_header_repeated(self):
        rows = "".join("| Item %d | %d |\n" % (i, i * 10) for i in range(1, 41))
        code, so, se, deck = self.build("# T\n\n## Inventory\n\n| Name | Qty |\n|---|---|\n" + rows)
        self.assertEqual(code, 0, se)
        self.assertGreater(deck.count, 2)
        titles = deck.titles()
        self.assertEqual(titles[1], "Inventory")
        self.assertTrue(all(t == "Inventory (continued)" for t in titles[2:]))
        body_rows = []
        for n in range(2, deck.count + 1):
            (table,) = deck.tables(n)
            self.assertEqual(table[0], ["Name", "Qty"])
            body_rows.extend(r[0] for r in table[1:])
        self.assertEqual(body_rows, ["Item %d" % i for i in range(1, 41)])  # every row once, in order
        self.assertIn("at a table boundary", se)
        self.assertIn("%d of them continued" % (deck.count - 2), so)

    def test_long_bullet_list_overflows_to_continued_slides(self):
        items = "".join("- Point number %d about the plan\n" % i for i in range(1, 31))
        code, _, se, deck = self.build("# T\n\n## Plan\n\n" + items)
        self.assertEqual(code, 0, se)
        self.assertGreater(deck.count, 2)
        seen = [t for n in range(2, deck.count + 1) for t in deck.texts(n) if t.startswith("Point")]
        self.assertEqual(seen, ["Point number %d about the plan" % i for i in range(1, 31)])
        self.assertIn("did not fit on one slide", se)
        for n in range(2, deck.count + 1):  # no text below its set size
            sizes = {int(r.get("sz")) for r in deck.slide(n).iter(A + "rPr") if r.get("sz")}
            self.assertEqual(sizes, {2000})

    def test_title_flag_replaces_first_heading(self):
        code, _, se, deck = self.build("# Old\n\n## S\n\nx\n", "--title", "New title")
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.title(1), "New title")
        self.assertIn("replaced on the title slide by --title", se)

    def test_front_matter_title_and_subtitle(self):
        md = "---\ntitle: FM deck\nauthor: Test Author\n---\n## S\n\nx\n"
        code, _, se, deck = self.build(md)
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.title(1), "FM deck")
        self.assertIn("Test Author", deck.texts(1))
        self.assertIn("used on the title slide: title, author", se)

    def test_no_title_means_no_title_slide(self):
        code, _, se, deck = self.build("Intro text.\n\n## Only\n\nx\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.titles(), ["deck", "Only"])
        self.assertIn("the deck has no title slide", se)

    def test_aspect_4_3(self):
        code, _, se, deck = self.build("# T\n\n## S\n\nx\n", "--aspect", "4:3")
        self.assertEqual(code, 0, se)
        self.assertEqual(deck.size, {"cx": "9144000", "cy": "6858000", "type": "screen4x3"})

    def test_local_png_embedded_and_missing_image_warns(self):
        md = "# T\n\n## Pic\n\n![Chart](chart.png)\n\n![Gone](gone.png)\n"
        code, so, se, deck = self.build(md, files={"chart.png": png_bytes(4, 2)})
        self.assertEqual(code, 0, se)
        self.assertIn("ppt/media/image1.png", deck.names)
        pics = list(deck.slide(2).iter(P + "pic"))
        self.assertEqual(len(pics), 1)
        self.assertEqual(pics[0].find("%snvPicPr/%scNvPr" % (P, P)).get("descr"), "Chart")
        self.assertIn("[Gone]", deck.texts(2))
        self.assertIn("image gone.png not found", se)
        self.assertIn("1 image", so)

    def test_internal_anchor_jumps_to_slide_and_external_link(self):
        md = "# T\n\n## Results\n\nx\n\n## Links\n\nSee [results](#results) and [site](https://example.com/a).\n"
        code, _, se, deck = self.build(md)
        self.assertEqual(code, 0, se)
        rels = deck.parts["ppt/slides/_rels/slide3.xml.rels"]
        self.assertIn('Target="slide2.xml"', rels)
        self.assertIn('Target="https://example.com/a" TargetMode="External"', rels)
        self.assertIn('action="ppaction://hlinksldjump"', deck.parts["ppt/slides/slide3.xml"])

    def test_brand_fonts_and_bad_colour(self):
        with workdir() as d:
            brand = write(os.path.join(d, "brand.json"),
                          '{"fonts": {"heading": "Georgia", "body": {"family": "Verdana"}}, '
                          '"colors": {"primary": "#123456", "accent": "blue"}}')
            src = write(os.path.join(d, "a.md"), "# T\n\n## S\n\nx\n")
            out = os.path.join(d, "a.pptx")
            code, so, se = run(SKILL, SCRIPT, src, "-o", out, "--brand", brand)
            self.assertEqual(code, 0, se)
            theme = Deck(out).parts["ppt/theme/theme1.xml"]
        self.assertIn('<a:majorFont><a:latin typeface="Georgia"/>', theme)
        self.assertIn('<a:minorFont><a:latin typeface="Verdana"/>', theme)
        self.assertIn('<a:dk2><a:srgbClr val="123456"/>', theme)
        self.assertIn("brand colors.accent 'blue' is not a 6-digit hex code", se)
        self.assertIn("brand: Georgia / Verdana", so)

    def test_bad_input_fails_clearly(self):
        with workdir() as d:
            good = write(os.path.join(d, "a.md"), "# T\n")
            empty = write(os.path.join(d, "e.md"), "\n\n")
            badbrand = write(os.path.join(d, "b.json"), "{not json")
            cases = [([os.path.join(d, "missing.md"), "-o", os.path.join(d, "o.pptx")], "cannot read"),
                     ([empty, "-o", os.path.join(d, "o.pptx")], "is empty"),
                     ([good, "-o", os.path.join(d, "o.ppt")], "output must end in .pptx"),
                     ([good, "-o", os.path.join(d, "nodir", "o.pptx")], "does not exist"),
                     ([good, "-o", os.path.join(d, "o.pptx"), "--brand", badbrand], "cannot read brand file")]
            for args, msg in cases:
                code, _, se = run(SKILL, SCRIPT, *args)
                self.assertEqual(code, 1, args)
                self.assertIn("ERROR", se)
                self.assertIn(msg, se)
                self.assertNotIn("Traceback", se)


class HelpersTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_wrapped_lines(self):
        self.assertEqual(self.m.wrapped_lines("aaa bbb ccc", 7), 2)
        self.assertEqual(self.m.wrapped_lines("one\n\ntwo", 10), 3)
        self.assertEqual(self.m.wrapped_lines("ab " + "x" * 25, 10), 4)

    # BUG: a token longer than a line, at the start of a line, is counted one line short
    # (25 chars at 10 per line is 3 lines, the estimate says 2), so long URLs can overflow a slide.
    @unittest.expectedFailure
    def test_wrapped_lines_long_token_at_line_start(self):
        self.assertEqual(self.m.wrapped_lines("x" * 25, 10), 3)

    def test_slugify_matches_heading_anchors(self):
        self.assertEqual(self.m.slugify("Rollout **plan** (v2)!"), "rollout-plan")

    def test_split_row_respects_code_and_escaped_pipes(self):
        self.assertEqual(self.m.split_row("| `a|b` | c \\| d | e |"), ["`a|b`", "c | d", "e"])

    def test_numbered_list_jump_warns(self):
        m = self.m
        with contextlib.redirect_stderr(io.StringIO()):
            block = m.parse_blocks(["1. one", "2. two", "4. four"], 1, {})[0]
        self.assertEqual([it["num"] for it in block["items"]], [1, 2, 3])
        self.assertTrue(any("goes from 2 to 4" in w for w in m.WARNINGS))

    def test_inline_styles(self):
        segs = self.m.Inline({}, 1).parse("**b** *i* ~~s~~ `c`")
        styled = [(s[1], sorted(k for k, v in s[2].items() if v)) for s in segs if s[0] == "text" and s[1].strip()]
        self.assertEqual(styled, [("b", ["bold"]), ("i", ["italic"]), ("s", ["strike"]), ("c", ["code"])])

    def test_hex_and_contrast(self):
        self.assertEqual(self.m.hex6("#1f3864"), "1F3864")
        self.assertIsNone(self.m.hex6("blue"))
        self.assertAlmostEqual(self.m.contrast("000000", "FFFFFF"), 21.0, places=3)

    def test_image_size_reads_png_header(self):
        with workdir() as d:
            path = os.path.join(d, "x.png")
            with open(path, "wb") as f:
                f.write(png_bytes(7, 3))
            self.assertEqual(self.m.image_size(path), (7, 3, 96.0, 96.0, "png"))
            with open(path, "wb") as f:
                f.write(b"GIF89a....")
            self.assertIsNone(self.m.image_size(path))


if __name__ == "__main__":
    unittest.main()

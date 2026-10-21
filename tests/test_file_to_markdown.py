import os
import shutil
import unittest
import zipfile
from email.message import EmailMessage

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "file-to-markdown", "to_markdown.py"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
S_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def make_zip(path, parts):
    with zipfile.ZipFile(path, "w") as z:
        for name, text in parts.items():
            z.writestr(name, text)
    return path


def rels(*items):
    body = "".join('<Relationship Id="%s" Type="%s" Target="%s"%s/>'
                   % (rid, typ, tgt, ' TargetMode="External"' if ext else "")
                   for rid, typ, tgt, ext in items)
    return '<Relationships xmlns="%s">%s</Relationships>' % (PKG_NS, body)


def docx(path, body, extra=None, doc_rels=None):
    parts = {"word/document.xml": '<w:document xmlns:w="%s" xmlns:r="%s"><w:body>%s</w:body></w:document>'
                                  % (W_NS, R_NS, body)}
    if doc_rels:
        parts["word/_rels/document.xml.rels"] = rels(*doc_rels)
    parts.update(extra or {})
    return make_zip(path, parts)


def para(text, style=None, rpr=""):
    ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style if style else ""
    return '<w:p>%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (
        ppr, "<w:rPr>%s</w:rPr>" % rpr if rpr else "", text)


def to_md(d, name, *flags):
    out = os.path.join(d, "out.md")
    code, _, err = run(SKILL, SCRIPT, os.path.join(d, name), "-o", out, *flags)
    return code, (read(out) if os.path.exists(out) else ""), err


def tiny_pdf(path, lines):
    """A one-page PDF whose text layer holds `lines`, top to bottom, in Helvetica."""
    ops = ["BT /F1 12 Tf 72 720 Td"]
    for k, line in enumerate(lines):
        if k:
            ops.append("0 -18 Td")
        ops.append("(%s) Tj" % line)
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path, "wb") as f:
        f.write(bytes(out))


class ToMarkdownTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    # ---------------------------------------------------------------- helpers

    def test_md_escape_stops_markdown_and_raw_html(self):
        self.assertEqual(self.m.md_escape("a*b_c [x] `y`"), "a\\*b\\_c \\[x\\] \\`y\\`")
        self.assertEqual(self.m.md_escape("<script> and 3 < 4"), "\\<script> and 3 < 4")

    def test_escape_line_start_keeps_plain_text_from_becoming_structure(self):
        f = self.m.escape_line_start
        self.assertEqual(f("# not a heading"), "\\# not a heading")
        self.assertEqual(f("- not a bullet"), "\\- not a bullet")
        self.assertEqual(f("1. not a list"), "\\1. not a list")
        self.assertEqual(f("Plain sentence."), "Plain sentence.")

    def test_md_table_pads_ragged_rows_and_escapes_pipes(self):
        self.assertEqual(self.m.md_table([["A", "B"], ["x|y"], ["", ""]]),
                         "| A | B |\n|---|---|\n| x\\|y |  |")

    # ---------------------------------------------------------------- docx

    def test_docx_headings_lists_table_bold_and_link(self):
        numbering = ('<w:numbering xmlns:w="%s">'
                     '<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:numFmt w:val="bullet"/></w:lvl></w:abstractNum>'
                     '<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/></w:lvl></w:abstractNum>'
                     '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
                     '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num></w:numbering>' % W_NS)

        def item(text, num):
            return ('<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr></w:pPr>'
                    '<w:r><w:t>%s</w:t></w:r></w:p>' % (num, text))

        body = (para("Pilot plan", "Title") + para("Goals", "Heading2") +
                '<w:p><w:r><w:t xml:space="preserve">Move </w:t></w:r>'
                '<w:r><w:rPr><w:b/></w:rPr><w:t>three</w:t></w:r>'
                '<w:r><w:t xml:space="preserve"> services. See </w:t></w:r>'
                '<w:hyperlink r:id="rId9"><w:r><w:t>the page</w:t></w:r></w:hyperlink></w:p>' +
                item("Cut cost", 1) + item("Retire cluster", 1) +
                para("Steps", "Heading2") + item("Inventory", 2) + item("Pilot", 2) +
                '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Risk</w:t></w:r></w:p></w:tc>'
                '<w:tc><w:p><w:r><w:t>Owner</w:t></w:r></w:p></w:tc></w:tr>'
                '<w:tr><w:tc><w:p><w:r><w:t>Downtime</w:t></w:r></w:p></w:tc>'
                '<w:tc><w:p><w:r><w:t>Ops</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
        with workdir() as d:
            docx(os.path.join(d, "brief.docx"), body, {"word/numbering.xml": numbering},
                 [("rId9", R_NS + "/hyperlink", "https://example.test/plan", True)])
            code, md, err = to_md(d, "brief.docx")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "# Pilot plan\n\n## Goals\n\n"
                             "Move **three** services. See [the page](https://example.test/plan)\n\n"
                             "- Cut cost\n- Retire cluster\n\n## Steps\n\n1. Inventory\n2. Pilot\n\n"
                             "| Risk | Owner |\n|---|---|\n| Downtime | Ops |\n")
        self.assertIn("3 headings, 4 list items, 1 tables", err)
        self.assertIn("dropped: nothing detected", err)

    def test_docx_reports_comments_and_tracked_changes(self):
        comments = ('<w:comments xmlns:w="%s"><w:comment w:id="0"/><w:comment w:id="1"/></w:comments>' % W_NS)
        body = ('<w:p><w:r><w:t xml:space="preserve">Kept </w:t></w:r>'
                '<w:ins><w:r><w:t>added</w:t></w:r></w:ins>'
                '<w:del><w:r><w:delText>removed</w:delText></w:r></w:del></w:p>')
        with workdir() as d:
            docx(os.path.join(d, "c.docx"), body, {"word/comments.xml": comments})
            code, md, err = to_md(d, "c.docx")
        self.assertEqual(code, 0, err)
        self.assertEqual(md.strip(), "Kept added")
        self.assertIn("2 comments", err)
        self.assertIn("1 tracked insertions (kept as text)", err)
        self.assertIn("1 tracked deletions (left out)", err)

    def test_docx_without_heading_styles_infers_headings_and_says_so(self):
        big = '<w:b/><w:sz w:val="36"/>'
        body = (para("Quarterly update", rpr=big) +
                para("This is the body text of the update and it runs long enough to be the body size.") +
                para("More body text that sets the common size for the whole document here."))
        with workdir() as d:
            docx(os.path.join(d, "u.docx"), body)
            code, md, err = to_md(d, "u.docx")
        self.assertEqual(code, 0, err)
        self.assertTrue(md.startswith("# Quarterly update\n"), md)
        self.assertIn("1 heading(s) inferred", err)

    def test_docx_without_document_xml_fails_clearly(self):
        with workdir() as d:
            make_zip(os.path.join(d, "x.docx"), {"other.xml": "<a/>"})
            code, _, err = to_md(d, "x.docx")
        self.assertNotEqual(code, 0)
        self.assertIn("not a Word document", err)
        self.assertNotIn("Traceback", err)

    def test_docx_that_is_not_a_zip_fails_clearly(self):
        with workdir() as d:
            write(os.path.join(d, "x.docx"), "plain text, not a package")
            code, _, err = to_md(d, "x.docx")
        self.assertNotEqual(code, 0)
        self.assertIn("not a valid .docx file", err)
        self.assertNotIn("Traceback", err)

    # ---------------------------------------------------------------- pptx

    def test_pptx_slide_titles_bullets_notes_hidden_and_image(self):
        def sp(ph_type, paras):
            ph = '<p:ph type="%s"/>' % ph_type if ph_type else "<p:ph/>"
            ps = "".join('<a:p><a:r><a:t>%s</a:t></a:r></a:p>' % t for t in paras)
            return ('<p:sp><p:nvSpPr><p:cNvPr id="1" name="s"/><p:cNvSpPr/><p:nvPr>%s</p:nvPr></p:nvSpPr>'
                    '<p:txBody>%s</p:txBody></p:sp>' % (ph, ps))

        def slide(shapes, show=None):
            return ('<p:sld xmlns:p="%s" xmlns:a="%s" xmlns:r="%s"%s><p:cSld><p:spTree>%s</p:spTree></p:cSld></p:sld>'
                    % (P_NS, A_NS, R_NS, ' show="0"' if show == "0" else "", shapes))

        notes = ('<p:notes xmlns:p="%s" xmlns:a="%s"><p:cSld><p:spTree>%s</p:spTree></p:cSld></p:notes>'
                 % (P_NS, A_NS, sp("body", ["Stress the deadline."])))
        parts = {
            "ppt/presentation.xml": '<p:presentation xmlns:p="%s" xmlns:r="%s"><p:sldIdLst>'
                                    '<p:sldId id="256" r:id="rId1"/><p:sldId id="257" r:id="rId2"/>'
                                    '</p:sldIdLst></p:presentation>' % (P_NS, R_NS),
            "ppt/_rels/presentation.xml.rels": rels(("rId1", R_NS + "/slide", "slides/slide1.xml", False),
                                                    ("rId2", R_NS + "/slide", "slides/slide2.xml", False)),
            "ppt/slides/slide1.xml": slide(sp("title", ["Roadmap"]) + sp(None, ["Ship beta", "Hire two"]) +
                                           "<p:pic/>"),
            "ppt/slides/_rels/slide1.xml.rels": rels(("rId1", R_NS + "/notesSlide",
                                                      "../notesSlides/notesSlide1.xml", False)),
            "ppt/notesSlides/notesSlide1.xml": notes,
            "ppt/slides/slide2.xml": slide(sp("title", ["Backup"]), show="0"),
        }
        with workdir() as d:
            make_zip(os.path.join(d, "deck.pptx"), parts)
            code, md, err = to_md(d, "deck.pptx")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "## Slide 1: Roadmap\n\n- Ship beta\n- Hire two\n\n"
                             "> **Speaker notes:** Stress the deadline.\n\n"
                             "## Slide 2: Backup (hidden)\n")
        self.assertIn("2 slides", err)
        self.assertIn("1 slides with speaker notes", err)
        self.assertIn("1 images", err)

    # ---------------------------------------------------------------- xlsx

    def _workbook(self, path, sheet_rows, hidden=False):
        cells = "".join('<row r="%d">%s</row>' % (r, c) for r, c in sheet_rows)
        parts = {
            "xl/workbook.xml": '<workbook xmlns="%s" xmlns:r="%s"><sheets>'
                               '<sheet name="Budget" sheetId="1" r:id="rId1"%s/></sheets></workbook>'
                               % (S_NS, R_NS, ' state="hidden"' if hidden else ""),
            "xl/_rels/workbook.xml.rels": rels(("rId1", R_NS + "/worksheet", "worksheets/sheet1.xml", False)),
            "xl/worksheets/sheet1.xml": '<worksheet xmlns="%s"><sheetData>%s</sheetData></worksheet>' % (S_NS, cells),
            "xl/sharedStrings.xml": '<sst xmlns="%s"><si><t>Item</t></si><si><t>Cost</t></si>'
                                    '<si><t>Due</t></si><si><r><t>Ser</t></r><r><t>vers</t></r></si></sst>' % S_NS,
            "xl/styles.xml": '<styleSheet xmlns="%s"><cellXfs><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs>'
                             '</styleSheet>' % S_NS,
        }
        make_zip(path, parts)

    def test_xlsx_shared_strings_numbers_dates_and_formulas(self):
        rows = [(1, '<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c>'),
                (2, '<c r="A2" t="s"><v>3</v></c><c r="B2"><f>SUM(1,2)</f><v>1200.50</v></c>'
                    '<c r="C2" s="1"><v>45658</v></c>')]
        with workdir() as d:
            self._workbook(os.path.join(d, "b.xlsx"), rows)
            code, md, err = to_md(d, "b.xlsx")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "## Budget\n\n| Item | Cost | Due |\n|---|---|---|\n| Servers | 1200.50 | 2025-01-01 |\n")
        self.assertIn("1 formulas (cached values kept)", err)

    def test_xlsx_max_rows_cuts_each_sheet_and_notes_it(self):
        rows = [(1, '<c r="A1" t="s"><v>0</v></c>')] + [
            (r, '<c r="A%d"><v>%d</v></c>' % (r, r)) for r in range(2, 7)]
        with workdir() as d:
            self._workbook(os.path.join(d, "b.xlsx"), rows, hidden=True)
            code, md, err = to_md(d, "b.xlsx", "--max-rows", "2")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "## Budget (hidden)\n\n| Item |\n|---|\n| 2 |\n| 3 |\n")
        self.assertIn("cut to 2 of 5 data rows", err)

    # ---------------------------------------------------------------- html

    def test_html_structure_kept_and_scripts_and_nav_dropped(self):
        page = ("<html><head><title>t</title><style>p{}</style></head><body>"
                "<nav><a href='/'>Home</a></nav><script>alert(1)</script>"
                "<h1>Status</h1><p>All <strong>green</strong>, see <a href='https://example.test/s'>details</a>.</p>"
                "<ul><li>API up</li><li>DB up</li></ul>"
                "<table><tr><th>Svc</th><th>Uptime</th></tr><tr><td>API</td><td>99.9</td></tr></table>"
                "<pre><code class='language-sh'>make deploy</code></pre></body></html>")
        with workdir() as d:
            write(os.path.join(d, "s.html"), page)
            code, md, err = to_md(d, "s.html")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "# Status\n\nAll **green**, see [details](https://example.test/s).\n\n"
                             "- API up\n- DB up\n\n| Svc | Uptime |\n|---|---|\n| API | 99.9 |\n\n"
                             "```sh\nmake deploy\n```\n")
        self.assertNotIn("alert", md)
        self.assertNotIn("Home", md)
        self.assertIn("2 scripts/styles", err)
        self.assertIn("1 navigation menus", err)

    def test_html_javascript_link_keeps_text_only(self):
        with workdir() as d:
            write(os.path.join(d, "s.html"), "<p><a href='javascript:void(0)'>Click</a></p>")
            code, md, _ = to_md(d, "s.html")
        self.assertEqual(code, 0)
        self.assertEqual(md, "Click\n")

    # ---------------------------------------------------------------- csv / tsv / json / txt

    def test_csv_semicolon_delimiter_is_detected(self):
        with workdir() as d:
            write(os.path.join(d, "s.csv"), "seed;packets\ntomato;12\nbean;30\n")
            code, md, err = to_md(d, "s.csv")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, "| seed | packets |\n|---|---|\n| tomato | 12 |\n| bean | 30 |\n")
        self.assertIn("2 rows", err)

    def test_tsv_is_split_on_tabs(self):
        with workdir() as d:
            write(os.path.join(d, "s.tsv"), "a\tb\n1,5\t2\n")
            code, md, _ = to_md(d, "s.tsv")
        self.assertEqual(code, 0)
        self.assertEqual(md, "| a | b |\n|---|---|\n| 1,5 | 2 |\n")

    def test_empty_csv_fails_clearly(self):
        with workdir() as d:
            write(os.path.join(d, "e.csv"), "")
            code, _, err = to_md(d, "e.csv")
        self.assertNotEqual(code, 0)
        self.assertIn("has no rows", err)

    def test_json_array_of_objects_becomes_one_table_with_union_of_keys(self):
        with workdir() as d:
            write(os.path.join(d, "a.json"), '[{"id": 1, "ok": true}, {"id": 2, "note": null, "tags": ["x"]}]')
            code, md, err = to_md(d, "a.json")
        self.assertEqual(code, 0, err)
        self.assertEqual(md, '| id | ok | note | tags |\n|---|---|---|---|\n'
                             '| 1 | true |  |  |\n| 2 |  |  | \\["x"\\] |\n')

    def test_json_object_gives_key_value_table_and_a_table_per_array(self):
        with workdir() as d:
            write(os.path.join(d, "o.json"), '{"team": "Ops", "members": [{"name": "Ana"}, {"name": "Bo"}]}')
            code, md, _ = to_md(d, "o.json")
        self.assertEqual(code, 0)
        self.assertEqual(md, "| Key | Value |\n|---|---|\n| team | Ops |\n\n"
                             "## members\n\n| name |\n|---|\n| Ana |\n| Bo |\n")

    def test_invalid_json_fails_clearly(self):
        with workdir() as d:
            write(os.path.join(d, "b.json"), '{"a": ')
            code, _, err = to_md(d, "b.json")
        self.assertNotEqual(code, 0)
        self.assertIn("is not valid JSON", err)
        self.assertNotIn("Traceback", err)

    def test_txt_passes_through_and_stdout_mode(self):
        with workdir() as d:
            write(os.path.join(d, "n.txt"), "# Notes\nkeep *as is*")
            code, out, err = run(SKILL, SCRIPT, os.path.join(d, "n.txt"), "-o", "-")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "# Notes\nkeep *as is*\n")
        self.assertIn("-> stdout", err)

    def test_latin1_text_is_read_and_flagged(self):
        with workdir() as d:
            with open(os.path.join(d, "l.txt"), "wb") as f:
                f.write("café".encode("latin-1"))
            code, md, err = to_md(d, "l.txt")
        self.assertEqual(code, 0)
        self.assertEqual(md, "café\n")
        self.assertIn("not UTF-8", err)

    # ---------------------------------------------------------------- email

    def test_eml_subject_headers_plain_body_and_attachment(self):
        msg = EmailMessage()
        msg["Subject"] = "Shift swap"
        msg["From"] = "Rota Bot <rota@example.test>"
        msg["To"] = "crew@example.test"
        msg["Date"] = "Tue, 01 Sep 2026 09:00:00 +0000"
        msg.set_content("Hi all,\n# not a heading\nSee the rota.\n")
        msg.add_alternative("<p>Hi all</p>", subtype="html")
        msg.add_attachment(b"x" * 2048, maintype="application", subtype="pdf", filename="rota.pdf")
        with workdir() as d:
            with open(os.path.join(d, "m.eml"), "wb") as f:
                f.write(bytes(msg))
            code, md, err = to_md(d, "m.eml")
        self.assertEqual(code, 0, err)
        self.assertTrue(md.startswith("# Shift swap\n"), md)
        self.assertIn("| From | Rota Bot \\<rota@example.test> |", md)
        self.assertIn("| To | crew@example.test |", md)
        self.assertNotIn("| Cc |", md)
        self.assertIn("Hi all,\n\\# not a heading\nSee the rota.", md)
        self.assertIn("## Attachments\n\n- rota.pdf (2.0 KB)", md)
        self.assertIn("1 attachments (listed, not converted)", err)
        self.assertIn("1 HTML alternative", err)

    def test_eml_with_html_body_only_converts_the_html(self):
        msg = EmailMessage()
        msg["Subject"] = "Notice"
        msg.set_content("<h2>Closed</h2><p>Back <b>Monday</b>.</p>", subtype="html")
        with workdir() as d:
            with open(os.path.join(d, "m.eml"), "wb") as f:
                f.write(bytes(msg))
            code, md, _ = to_md(d, "m.eml")
        self.assertEqual(code, 0)
        self.assertIn("## Closed\n\nBack **Monday**.", md)

    def test_msg_that_is_not_a_compound_file_fails_clearly(self):
        with workdir() as d:
            write(os.path.join(d, "m.msg"), "not outlook")
            code, _, err = to_md(d, "m.msg")
        self.assertNotEqual(code, 0)
        self.assertIn("not an Outlook .msg file", err)
        self.assertNotIn("Traceback", err)

    # ---------------------------------------------------------------- pdf

    def test_pdf_page_layout_table_heading_and_bullets(self):
        rep = self.m.Report()
        page = ("Project status\n"
                "The pilot finished on time and the team is ready for the next phase of work.\n"
                "\n"
                "Region      Tickets      Hours\n"
                "North       120          3.4\n"
                "South       80           2.1\n"
                "\n"
                "• Hire two agents\n"
                "• Close the backlog\n")
        md = "\n".join(self.m._pdf_page_md(page, rep))
        self.assertIn("### Project status\n\nThe pilot finished", md)
        self.assertIn("| Region | Tickets | Hours |\n|---|---|---|\n| North | 120 | 3.4 |\n| South | 80 | 2.1 |", md)
        self.assertIn("- Hire two agents\n- Close the backlog", md)
        self.assertEqual(rep.kept.get("pdf tables"), 1)

    def test_pdf_table_split_across_pages_is_joined_without_repeated_header(self):
        rep = self.m.Report()
        p1 = "Ticket report\n\nRegion      Tickets\nNorth       120\nSouth       80\n\n1\n"
        p2 = "Region      Tickets\nEast        40\n\n2\n"
        a, b = self.m._join_split_tables([p1, p2], rep)
        self.assertIn("South       80\nEast        40", a)
        self.assertNotIn("East", b)
        self.assertNotIn("Region", b)
        self.assertIn("header row repeated on page 2 was dropped", rep.notes[0])

    def test_pdf_header_repeated_on_every_continuation_page_is_dropped(self):
        p1 = "Ticket report\n\nRegion      Tickets\nNorth       120\n"
        p2 = "Region      Tickets\nEast        40\n"
        p3 = "Region      Tickets\nWest        10\n"
        a, b, c = self.m._join_split_tables([p1, p2, p3], self.m.Report())
        self.assertIn("North       120\nEast        40\nWest        10", a)
        self.assertNotIn("Region", b)
        self.assertNotIn("Region", c)

    def test_pdf_without_pdftotext_gives_install_steps(self):
        with workdir() as d:
            tiny_pdf(os.path.join(d, "r.pdf"), ["Hello"])
            out = os.path.join(d, "out.md")
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "r.pdf"), "-o", out, env={"PATH": d})
        self.assertNotEqual(code, 0)
        self.assertIn("needs `pdftotext`", err)
        self.assertIn("brew install poppler", err)

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not on PATH")
    def test_pdf_text_layer_is_read_with_page_marker(self):
        with workdir() as d:
            tiny_pdf(os.path.join(d, "r.pdf"), ["Seed swap rules",
                                                 "Bring seeds in labelled packets and sign the sheet at the door."])
            code, md, err = to_md(d, "r.pdf")
        self.assertEqual(code, 0, err)
        self.assertTrue(md.startswith("<!-- page 1 -->"), md)
        self.assertIn("Bring seeds in labelled packets", md)
        self.assertIn("1 pages", err)

    # ---------------------------------------------------------------- CLI errors

    def test_legacy_binary_format_is_refused_with_format_to_save_as(self):
        with workdir() as d:
            write(os.path.join(d, "old.doc"), "x")
            code, _, err = to_md(d, "old.doc")
        self.assertNotEqual(code, 0)
        self.assertIn(".doc files are not supported. Save or export it as .docx", err)

    def test_unsupported_extension_lists_supported_types(self):
        with workdir() as d:
            write(os.path.join(d, "a.xyz"), "x")
            code, _, err = to_md(d, "a.xyz")
        self.assertNotEqual(code, 0)
        self.assertIn("unsupported file type '.xyz'", err)

    def test_missing_input_fails_clearly(self):
        with workdir() as d:
            code, _, err = to_md(d, "nope.docx")
        self.assertNotEqual(code, 0)
        self.assertIn("input not found", err)

    def test_missing_output_folder_fails_clearly(self):
        with workdir() as d:
            write(os.path.join(d, "n.txt"), "hi")
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "n.txt"), "-o", os.path.join(d, "no", "o.md"))
        self.assertNotEqual(code, 0)
        self.assertIn("output folder does not exist", err)

    def test_bad_ocr_lang_is_rejected(self):
        with workdir() as d:
            write(os.path.join(d, "n.txt"), "hi")
            code, _, err = to_md(d, "n.txt", "--ocr-lang", "en;rm")
        self.assertNotEqual(code, 0)
        self.assertIn("--ocr-lang takes tesseract language codes", err)


if __name__ == "__main__":
    unittest.main()

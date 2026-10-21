import os
import unittest
import zipfile
import xml.etree.ElementTree as ET

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "md-to-xlsx", "md_to_xlsx.py"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BUILTIN_FMTS = {9: "0%", 10: "0.00%", 3: "#,##0", 4: "#,##0.00"}


class Book(object):
    """Sheets of a written .xlsx as {sheet name: {cell ref: value}} plus each cell's number format."""

    def __init__(self, path):
        with zipfile.ZipFile(path) as z:
            self.parts = {n: z.read(n).decode("utf-8") for n in z.namelist()}
        wb = ET.fromstring(self.parts["xl/workbook.xml"])
        self.names = [s.get("name") for s in wb.find(S + "sheets")]
        sst = ET.fromstring(self.parts["xl/sharedStrings.xml"])
        self.sst_unique = int(sst.get("uniqueCount"))
        strings = ["".join(t.text or "" for t in si.iter(S + "t")) for si in sst]
        styles = ET.fromstring(self.parts["xl/styles.xml"])
        custom = {int(f.get("numFmtId")): f.get("formatCode") for f in styles.iter(S + "numFmt")}
        xf_fmt = []
        for xf in styles.find(S + "cellXfs"):
            fid = int(xf.get("numFmtId"))
            xf_fmt.append(custom.get(fid) or BUILTIN_FMTS.get(fid))
        self.cells, self.fmts, self.xml = {}, {}, {}
        for i, name in enumerate(self.names, 1):
            xml = self.parts["xl/worksheets/sheet%d.xml" % i]
            self.xml[name] = xml
            cells, fmts = {}, {}
            for c in ET.fromstring(xml).iter(S + "c"):
                ref, t, v, f = c.get("r"), c.get("t"), c.find(S + "v"), c.find(S + "f")
                if f is not None:
                    cells[ref] = ("formula", f.text)
                elif t == "s":
                    cells[ref] = strings[int(v.text)]
                elif t == "b":
                    cells[ref] = v.text == "1"
                else:
                    cells[ref] = float(v.text)
                fmts[ref] = xf_fmt[int(c.get("s", "0"))]
            self.cells[name], self.fmts[name] = cells, fmts


def convert(name, text, *args):
    with workdir() as d:
        src = write(os.path.join(d, name), text)
        out = os.path.join(d, "out.xlsx")
        code, so, se = run(SKILL, SCRIPT, src, "-o", out, *args)
        book = Book(out) if code == 0 else None
    return code, so, se, book


class MarkdownTest(unittest.TestCase):
    def test_each_table_is_a_sheet_named_from_its_heading(self):
        md = ("# Report\n\n## Vendors\n\n| ID | Name |\n|---|---|\n| 007 | Acme Test |\n\n"
              "```\n| not | a table |\n|---|---|\n```\n\n### Q1: Sales/Returns\n\n| a |\n|---|\n| 1 |\n")
        code, so, se, book = convert("r.md", md)
        self.assertEqual(code, 0, se)
        self.assertEqual(book.names, ["Vendors", "Q1 Sales Returns"])
        self.assertEqual(book.cells["Vendors"], {"A1": "ID", "B1": "Name", "A2": "007", "B2": "Acme Test"})
        self.assertIn("sheet name 'Q1: Sales/Returns' changed to 'Q1 Sales Returns'", se)
        self.assertIn("wrote", so)
        self.assertIn("(2 sheets", so)

    def test_cell_typing(self):
        md = ("## T\n\n| v |\n|---|\n| 42 |\n| 1,234.5 |\n| $1,200.00 |\n| 12.5% |\n| 02134 |\n"
              "| 1234567890123456 |\n| TRUE |\n| 2024-01-01 |\n| 2024-01-01T12:00 |\n| 2024-02-30 |\n| 1e3 |\n")
        code, _, se, book = convert("t.md", md)
        self.assertEqual(code, 0, se)
        c, f = book.cells["T"], book.fmts["T"]
        self.assertEqual([c["A%d" % r] for r in range(2, 13)],
                         [42.0, 1234.5, 1200.0, 0.125, "02134", "1234567890123456", True,
                          45292.0, 45292.5, "2024-02-30", 1000.0])
        self.assertEqual([f["A%d" % r] for r in range(2, 11)],
                         [None, "#,##0.0", '"$"#,##0.00', "0.0%", None, None, None, "yyyy-mm-dd", "yyyy-mm-dd hh:mm"])

    def test_markdown_formatting_stripped_from_cells(self):
        md = "## T\n\n| a | b |\n|---|---|\n| **bold** [link](https://example.com) | `x\\|y`<br>next |\n"
        code, _, se, book = convert("t.md", md)
        self.assertEqual(code, 0, se)
        self.assertEqual(book.cells["T"]["A2"], "bold link")
        self.assertEqual(book.cells["T"]["B2"], "x|y\nnext")
        self.assertIn("wrapText", book.parts["xl/styles.xml"])

    def test_html_tags_removed_with_warning(self):
        code, _, se, book = convert("t.md", "## T\n\n| a |\n|---|\n| <span>kept</span> |\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(book.cells["T"]["A2"], "kept")
        self.assertIn("2 HTML tag(s) removed", se)

    def test_formula_text_by_default(self):
        md = "## T\n\n| n | f |\n|---|---|\n| 1 | =SUM(A2:A2) |\n"
        code, _, se, book = convert("t.md", md)
        self.assertEqual(code, 0, se)
        self.assertEqual(book.cells["T"]["B2"], "=SUM(A2:A2)")
        self.assertIn("1 cell(s) start with '=' and were written as text", se)
        self.assertNotIn("calcPr", book.parts["xl/workbook.xml"])

    def test_formulas_flag_writes_live_formulas(self):
        md = "## T\n\n| n | f |\n|---|---|\n| 1 | =SUM(A2:A2) |\n"
        code, _, se, book = convert("t.md", md, "--formulas")
        self.assertEqual(code, 0, se)
        self.assertEqual(book.cells["T"]["B2"], ("formula", "SUM(A2:A2)"))
        self.assertIn('<calcPr fullCalcOnLoad="1"/>', book.parts["xl/workbook.xml"])

    def test_header_bold_frozen_filtered(self):
        code, _, se, book = convert("t.md", "## T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n")
        self.assertEqual(code, 0, se)
        xml = book.xml["T"]
        self.assertIn('<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>', xml)
        self.assertIn('<autoFilter ref="A1:B3"/>', xml)
        self.assertIn("'T'!$A$1:$B$3", book.parts["xl/workbook.xml"])
        header = ET.fromstring(xml).find(S + "sheetData")[0][0]
        xfs = list(ET.fromstring(book.parts["xl/styles.xml"]).find(S + "cellXfs"))
        self.assertEqual(xfs[int(header.get("s"))].get("fontId"), "1")  # the bold font

    def test_ragged_rows_and_blank_headers(self):
        md = "## T\n\n| a | |\n|---|---|\n| 1 | 2 | 3 |\n| 4 |\n"
        code, _, se, book = convert("t.md", md)
        self.assertEqual(code, 0, se)
        c = book.cells["T"]
        self.assertEqual((c["B1"], c["C1"], c["C2"]), ("Column 2", "Column 3", 3.0))
        self.assertNotIn("B3", c)
        self.assertIn("2 row(s) have a different cell count", se)
        self.assertIn("empty header cell(s) named Column 2, Column 3", se)

    def test_shared_strings_stored_once(self):
        code, _, se, book = convert("t.md", "## T\n\n| a |\n|---|\n| x |\n| x |\n| y |\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(book.sst_unique, 3)  # a, x, y

    def test_no_tables_fails(self):
        code, _, se, _ = convert("t.md", "# Just prose\n\nNo tables.\n")
        self.assertEqual(code, 1)
        self.assertIn("has no pipe tables", se)


class CsvJsonTest(unittest.TestCase):
    def test_semicolon_csv_detected(self):
        code, so, se, book = convert("sales.csv", "region;amount;note\nNorth;1200;\"a;b\"\nSouth;3,5;x\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(book.names, ["sales"])
        c = book.cells["sales"]
        self.assertEqual((c["A2"], c["B2"], c["C2"]), ("North", 1200.0, "a;b"))
        self.assertEqual(c["B3"], "3,5")
        self.assertIn("delimiter ';'", so)

    def test_tsv_and_trailing_blank_rows(self):
        code, so, se, book = convert("data.tsv", "a\tb\n1\t2\n\n\n")
        self.assertEqual(code, 0, se)
        self.assertEqual(book.cells["data"], {"A1": "a", "B1": "b", "A2": 1.0, "B2": 2.0})
        self.assertIn("1 row x 2 cols", so)

    def test_json_array_keeps_strings_as_strings(self):
        data = ('[{"id": "042", "qty": 5, "big": 12345678901234567, "ok": true, "when": "2024-01-01"},'
                ' {"id": "043", "extra": {"k": 1}}]')
        code, _, se, book = convert("rows.json", data)
        self.assertEqual(code, 0, se)
        c = book.cells["rows"]
        self.assertEqual([c[k] for k in ("A1", "B1", "C1", "D1", "E1", "F1")],
                         ["id", "qty", "big", "ok", "when", "extra"])
        self.assertEqual([c[k] for k in ("A2", "B2", "C2", "D2", "E2")],
                         ["042", 5.0, "12345678901234567", True, 45292.0])
        self.assertEqual(c["F3"], '{"k": 1}')
        self.assertNotIn("B3", c)
        self.assertIn("1 nested JSON value(s) written as JSON text", se)

    def test_json_object_of_arrays_gives_one_sheet_per_key(self):
        code, _, se, book = convert("b.json", '{"Orders": [{"n": 1}], "History": [{"n": 2}]}')
        self.assertEqual(code, 0, se)
        self.assertEqual(book.names, ["Orders", "History data"])

    def test_bad_json_fails_clearly(self):
        for text, msg in (("{oops", "is not valid JSON"), ("[]", "must be a non-empty array"),
                          ('{"a": 1}', "must be an array of objects"), ("[1, 2]", "must hold objects")):
            code, _, se, _ = convert("x.json", text)
            self.assertEqual(code, 1, text)
            self.assertIn(msg, se)
            self.assertNotIn("Traceback", se)


class CliTest(unittest.TestCase):
    def test_bad_arguments_fail_clearly(self):
        with workdir() as d:
            md = write(os.path.join(d, "a.md"), "| a |\n|---|\n| 1 |\n")
            txt = write(os.path.join(d, "a.txt"), "x")
            empty = write(os.path.join(d, "e.csv"), "\n\n")
            cases = [([md, "-o", os.path.join(d, "o.xls")], "output must end in .xlsx"),
                     ([md, "-o", os.path.join(d, "nodir", "o.xlsx")], "does not exist"),
                     ([txt, "-o", os.path.join(d, "o.xlsx")], "unsupported input type"),
                     ([os.path.join(d, "missing.csv"), "-o", os.path.join(d, "o.xlsx")], "cannot read"),
                     ([empty, "-o", os.path.join(d, "o.xlsx")], "has no rows")]
            for args, msg in cases:
                code, _, se = run(SKILL, SCRIPT, *args)
                self.assertEqual(code, 1, args)
                self.assertIn(msg, se)
                self.assertNotIn("Traceback", se)

    def test_title_goes_to_document_properties(self):
        code, _, se, book = convert("t.md", "| a |\n|---|\n| 1 |\n", "--title", "Q3 & more")
        self.assertEqual(code, 0, se)
        self.assertIn("<dc:title>Q3 &amp; more</dc:title>", book.parts["docProps/core.xml"])
        self.assertEqual(book.names, ["Table 1"])


class HelpersTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_col_letter(self):
        self.assertEqual([self.m.col_letter(i) for i in (0, 25, 26, 701, 702)], ["A", "Z", "AA", "ZZ", "AAA"])

    def test_sheet_name_rules(self):
        used = set()
        sn = self.m.sheet_name
        self.assertEqual(sn("A very long heading that goes beyond thirty one characters", "T", used),
                         ("A very long heading that goes", True))
        self.assertEqual(sn("Dup", "T", used), ("Dup", False))
        self.assertEqual(sn("dup", "T", used), ("dup (2)", True))
        self.assertEqual(sn(None, "Table 4", used), ("Table 4", False))
        self.assertEqual(sn("history", "T", used), ("History data", True))
        self.assertTrue(all(len(n) <= 31 for n in used))

    def test_leading_zeros_and_long_numbers_stay_text(self):
        stats = dict.fromkeys(("numbers", "dates", "booleans", "text", "formulas", "formula_text",
                               "nested", "truncated"), 0)
        kinds = [self.m.type_text(v, False, stats, [False]).kind
                 for v in ("007", "00", "1234567890123456", "123456789012345", "1e999", "$5%")]
        self.assertEqual(kinds, ["s", "s", "s", "n", "s", "s"])


if __name__ == "__main__":
    unittest.main()

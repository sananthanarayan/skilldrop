import os
import unittest
import zipfile

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "manuscript-check", "manuscript_check.py"

AY = """# Paper

## Abstract

One two three four five six.

## 1. Introduction

Prior work (Smith, 2020; Lee & Park, 2019a) and Jones et al. (2018) disagree. See Section 2 and Figure 1.

## 2. Results

Table 1 shows it.

**Figure 1.** A figure.

**Table 1.** A table.

## References

Jones, A., Brown, B., & Cole, C. (2018). A long enough title about something. *Journal*, 1, 1-2.

Lee, D., & Park, E. (2019a). Another long enough title about things. *Journal*, 2, 3-4. https://doi.org/10.1000/xyz123

Smith, F. (2020). A third long enough title for this test. *Journal*, 3, 5-6.
"""

NUM = """# Report

Earlier work [1] and later studies [2, 3] agree [4-5].

## References

[1] A. One. First paper. 2019.
[2] B. Two. Second paper. 2020.
[3] C. Three. Third paper. 2021.
[4] D. Four. Fourth paper. 2022.
[5] E. Five. Fifth paper. 2023.
"""


def checked(m, text, limit=None):
    return m.check(text.splitlines(), limit)


class ManuscriptCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_clean_author_year_and_numbered(self):
        for text, style in ((AY, "author-year"), (NUM, "numbered")):
            r = checked(self.m, text)
            self.assertEqual(r["fails"], [], style)
            self.assertEqual(r["warns"], [], style)
            self.assertEqual(r["stats"]["style"], style)

    def test_author_year_wrong_year_typo_missing_and_uncited(self):
        text = AY.replace("(Smith, 2020;", "(Smith, 2021;").replace("Jones et al. (2018)", "Jnes et al. (2018)")
        text = text.replace("See Section 2", "Brown (2015) argued otherwise. See Section 2")
        r = checked(self.m, text)
        f = " | ".join(r["fails"])
        self.assertIn("but the reference list has Smith 2020", f)
        self.assertIn("spells it Jones (2018)", f)
        self.assertIn("no Brown 2015", f)
        self.assertFalse(any("Jones" in w for w in r["warns"]))
        self.assertFalse(any("Smith 2020) is never cited" in w for w in r["warns"]))   # the wrong-year citation is its citation

    def test_year_letter_needed(self):
        text = AY.replace("Lee & Park, 2019a", "Lee & Park, 2019").replace(
            "Smith, F. (2020).", "Lee, D., & Park, E. (2019b). A different long enough title here. *J*, 9.\n\nSmith, F. (2020).")
        self.assertTrue(any("needs its year's letter" in w for w in checked(self.m, text)["warns"]))

    def test_numbered_missing_uncited_order_and_duplicate_number(self):
        text = NUM.replace("[4-5]", "[4-6]").replace("Earlier work [1] and later studies [2, 3]", "Earlier work [3] and later studies [1, 2]")
        text = text.replace("[5] E. Five", "[5] E. Five").replace("[3] C. Three. Third paper. 2021.", "[3] C. Three. Third paper. 2021.\n[3] X. Dup. Dup paper. 2024.")
        r = checked(self.m, text)
        f, w = " | ".join(r["fails"]), " | ".join(r["warns"])
        self.assertIn("cites [6], but there is no reference [6]", f)
        self.assertIn("reference [3] is numbered twice", f)
        self.assertIn("order of first citation", w)
        self.assertEqual(r["stats"]["renumber"], {3: 1, 1: 2, 2: 3})

    def test_markdown_links_are_not_citations(self):
        r = checked(self.m, NUM + "\nSee [1](http://example.com) for the data.\n")
        self.assertEqual(r["fails"], [])

    def test_duplicate_doi_once(self):
        dup = AY + "\nLee, D., & Park, E. (2019). Another long enough title about things. *J*, 2. doi:10.1000/xyz123\n"
        fails = checked(self.m, dup)["fails"]
        self.assertEqual(sum("same work" in f or "same title" in f for f in fails), 1)

    def test_figures_tables_sections(self):
        text = AY.replace("Table 1 shows it.", "Table 2 and Figure 3 show it. Section 5 has more.")
        r = checked(self.m, text)
        f, w = " | ".join(r["fails"]), " | ".join(r["warns"])
        for want in ("no Table 2", "no Figure 3", "no section 5"):
            self.assertIn(want, f)
        self.assertIn("Table 1 (line", w)

    def test_figure_range_and_out_of_order(self):
        text = AY.replace("See Section 2 and Figure 1.", "See Section 2.").replace(
            "Table 1 shows it.", "Table 1 shows it. Figures 2–3 come first, then Figure 1.\n\n**Figure 2.** b\n\n**Figure 3.** c")
        r = checked(self.m, text)
        self.assertTrue(any("first mentioned out of order" in w for w in r["warns"]))

    def test_footnotes_doi_and_abstract(self):
        text = AY + "\nA claim.[^a]\n\n[^b]: unused note.\n\nBad, B. (2021). Some long enough title for the test. doi:10.12/x\n"
        r = checked(self.m, text, limit=5)
        f, w = " | ".join(r["fails"]), " | ".join(r["warns"])
        self.assertIn("footnote [^a] is used but never defined", f)
        self.assertIn("footnote [^b]", w)
        self.assertIn("isn't a well-formed DOI", w)
        self.assertIn("abstract is 6 words, over the limit of 5", f)

    def test_citations_without_a_reference_list(self):
        r = checked(self.m, "# P\n\nAs shown [1].\n")
        self.assertTrue(any("no reference list" in f for f in r["fails"]))


class ManuscriptCheckCliTest(unittest.TestCase):
    def test_markdown_and_docx(self):
        with workdir() as d:
            p = write(os.path.join(d, "p.md"), AY)
            code, out, _ = run(SKILL, SCRIPT, p)
            self.assertEqual(code, 0)
            self.assertIn("Citation style: author-year; 3 references, 3 cited", out)
            body = "".join(f"<w:p><w:r><w:t>{l}</w:t></w:r></w:p>" for l in NUM.replace("[4-5]", "[9]").splitlines())
            docx = os.path.join(d, "p.docx")
            with zipfile.ZipFile(docx, "w") as z:
                z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                                                f"<w:body>{body}</w:body></w:document>")
            code, out, _ = run(SKILL, SCRIPT, docx)
            self.assertEqual(code, 1)
            self.assertIn("cites [9]", out)

    def test_unreadable_exits_2(self):
        with workdir() as d:
            self.assertEqual(run(SKILL, SCRIPT, write(os.path.join(d, "p.docx"), "not a zip"))[0], 2)


if __name__ == "__main__":
    unittest.main()

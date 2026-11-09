import json
import os
import unittest
import zipfile

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "exam-paper-check", "exam_check.py"

PAPER = """# Test
Time allowed: 30 minutes
Total marks: 20

**1** A question.
(a) Name it. [1]
(b) Explain it. [3]
(Total for Question 1 = 4 marks)

**2** Another.
(a) (i) Describe. [2]
(ii) Calculate. [3]
(b) Suggest. [1]
(Total for Question 2 = 6 marks)

**3** Essay. [6]

Answer either Question 4 or Question 5.

**4** Compare. [4]

**5** Evaluate. [4]
"""
SCHEME = """1 (a) friction [1]
1 (b) three points [3]
2 (a)(i) energy [2]
2 (a)(ii) 9 J [3]
2 (b) repeat [1]
3 Level-marked [6]
4 Level-marked [4]
5 Level-marked [4]
"""


def checked(m, paper=PAPER, scheme=None, spec=None):
    return m.check(m.parse(paper.splitlines()), m.parse(scheme.splitlines()) if scheme else None, spec)


class ExamCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_consistent_paper_and_scheme_pass(self):
        r = checked(self.m, scheme=SCHEME)
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["warns"], [])
        self.assertEqual(r["total"], 20)
        self.assertAlmostEqual(r["pace"], 1.5)

    def test_either_or_counts_once_and_must_match(self):
        r = checked(self.m, paper=PAPER.replace("Evaluate. [4]", "Evaluate. [6]"))
        self.assertTrue(any("are a choice but are worth 4 and 6" in f for f in r["fails"]))

    def test_paper_total_mismatch(self):
        r = checked(self.m, paper=PAPER.replace("Total marks: 20", "Total marks: 25"))
        self.assertTrue(any("add up to 20 marks but the paper says 25" in f for f in r["fails"]))

    def test_question_total_mismatch(self):
        r = checked(self.m, paper=PAPER.replace("Question 2 = 6", "Question 2 = 7"))
        self.assertTrue(any("Question 2: the parts add up to 6" in f for f in r["fails"]))

    def test_part_and_subpart_on_one_line_keep_their_marks(self):
        r = checked(self.m)
        row = next(x for x in r["rows"] if x["question"] == 2)
        self.assertEqual(row["parts"], {"a(i)": 2, "a(ii)": 3, "b": 1})

    def test_skipped_and_repeated_parts_and_questions(self):
        r = checked(self.m, paper=PAPER.replace("(b) Explain", "(c) Explain").replace("**3** Essay", "**2** Essay"))
        self.assertTrue(any("(b) is missing" in w for w in r["warns"]))
        self.assertTrue(any("Question 2 is numbered twice" in f for f in r["fails"]))

    def test_part_with_no_marks_warns(self):
        r = checked(self.m, paper=PAPER.replace("Name it. [1]", "Name it."))
        self.assertTrue(any("1(a) shows no marks" in w for w in r["warns"]))

    def test_scheme_missing_extra_and_different(self):
        scheme = SCHEME.replace("2 (b) repeat [1]\n", "").replace("1 (b) three points [3]", "1 (b) three points [2]") + "6 extra [2]\n"
        fails = checked(self.m, scheme=scheme)["fails"]
        self.assertTrue(any("nothing for Question 2(b)" in f for f in fails))
        self.assertTrue(any("Question 1(b) is worth 3 on the paper but 2 in the mark scheme" in f for f in fails))
        self.assertTrue(any("covers Question 6, which isn't on the paper" in f for f in fails))

    def test_scheme_stated_total_against_its_own_rows(self):
        fails = checked(self.m, scheme="Total marks: 21\n" + SCHEME)["fails"]
        self.assertTrue(any("out of 21 but its own marks add up to 20" in f for f in fails))
        self.assertEqual(checked(self.m, scheme="Total marks: 20\n" + SCHEME)["fails"], [])

    def test_objective_coverage(self):
        spec = {"objectives": {"AO1": 50, "AO2": 30, "AO3": 20},
                "assesses": {"1a": "AO1", "1b": "AO2", "2a(i)": "AO1", "2a(ii)": "AO2", "2b": "AO2", "3": "AO1", "4": "AO1", "5": "AO1"}}
        r = checked(self.m, spec=spec)
        self.assertTrue(any("objective AO3 is never assessed" in f for f in r["fails"]))
        self.assertEqual(r["coverage"]["AO1"], 13)    # 1 + 2 + 6 + 4, counting the choice once

    def test_roman_after_h_is_a_part(self):
        paper = "**1** Q\n" + "".join(f"({c}) x [1]\n" for c in "abcdefghi")
        r = checked(self.m, paper=paper)
        self.assertEqual(list(r["rows"][0]["parts"]), list("abcdefghi"))


class ExamCheckCliTest(unittest.TestCase):
    def test_markdown_and_docx(self):
        with workdir() as d:
            p = write(os.path.join(d, "paper.md"), PAPER)
            s = write(os.path.join(d, "scheme.md"), SCHEME)
            code, out, _ = run(SKILL, SCRIPT, p, "--scheme", s)
            self.assertEqual(code, 0)
            self.assertIn("| 2 | 6 | 6 | (a)(i) 2, (a)(ii) 3, (b) 1 |", out)
            body = "".join(f"<w:p><w:r><w:t>{l}</w:t></w:r></w:p>" for l in PAPER.replace("20", "21").splitlines())
            xml = ('<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                   f"<w:body>{body}</w:body></w:document>")
            docx = os.path.join(d, "paper.docx")
            with zipfile.ZipFile(docx, "w") as z:
                z.writestr("word/document.xml", xml)
            self.assertEqual(run(SKILL, SCRIPT, docx)[0], 1)

    def test_spec_file_and_bad_input(self):
        with workdir() as d:
            p = write(os.path.join(d, "paper.md"), PAPER)
            sp = write(os.path.join(d, "spec.json"), json.dumps({"objectives": {"AO1": 100}, "assesses": {"1": "AO1"}}))
            code, out, _ = run(SKILL, SCRIPT, p, "--spec", sp)
            self.assertIn("| AO1 |", out)
            self.assertEqual(run(SKILL, SCRIPT, os.path.join(d, "nope.md"))[0], 2)
            bad = write(os.path.join(d, "bad.json"), "[1]")
            self.assertEqual(run(SKILL, SCRIPT, p, "--spec", bad)[0], 2)


if __name__ == "__main__":
    unittest.main()

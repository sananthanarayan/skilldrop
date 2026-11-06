import os
import unittest
import zipfile

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "contract-check", "contract_check.py"

CLEAN = """# Services Agreement

This agreement (the "Agreement") is between Example Ltd (the "Supplier") and Sample Inc (the "Customer").

## 1. Definitions

1.1 "Services" means the services in Schedule 1.

## 2. Services

2.1 The Supplier shall provide the Services to the Customer under this Agreement.

2.2 Fees are payable within thirty (30) days, as set out in clause 3.

## 3. Fees

3.1 The Customer shall pay ten thousand dollars ($10,000) a month.

3.2 This Agreement renews each year unless either party gives sixty (60) days' written notice before the end of the term.

# Schedule 1 - Services

1. Support
2. Hosting
"""


def findings(m, text):
    return m.check(text.splitlines())["findings"]


def messages(fs, level=None):
    return [f[2] for f in fs if level is None or f[0] == level]


class ContractCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_clean_agreement_has_no_failures(self):
        self.assertEqual(messages(findings(self.m, CLEAN), "FAIL"), [])

    def test_blank_placeholders_fail(self):
        for blank in ("[●]", "[•]", "____", "[insert date]", "TBD", "[DATE]"):
            fs = findings(self.m, CLEAN.replace("$10,000", blank))
            self.assertTrue(any("still in" in m for m in messages(fs, "FAIL")), blank)

    def test_missing_clause_and_schedule_references_fail(self):
        text = CLEAN.replace("as set out in clause 3", "as set out in clause 4.2 and Schedule 2")
        fail = messages(findings(self.m, text), "FAIL")
        self.assertTrue(any("clause 4.2" in m for m in fail))
        self.assertTrue(any("Schedule 2" in m for m in fail))

    def test_reference_to_existing_top_level_clause_passes(self):
        self.assertFalse(any("clause 3" in m for m in messages(findings(self.m, CLEAN), "FAIL")))

    def test_numbering_gap_and_repeat(self):
        text = CLEAN.replace("## 3. Fees", "## 4. Fees").replace("3.1 The", "4.1 The").replace("3.2 This", "4.1 This")
        fs = findings(self.m, text)
        self.assertTrue(any("jumps to 4" in m for m in messages(fs, "WARN")))
        self.assertTrue(any("4.1 is numbered twice" in m for m in messages(fs, "FAIL")))

    def test_schedule_numbering_is_its_own(self):
        fs = findings(self.m, CLEAN)
        self.assertFalse(any("numbered twice" in m for m in messages(fs)))

    def test_words_and_figures_disagree(self):
        fs = findings(self.m, CLEAN.replace("thirty (30)", "thirty (60)"))
        self.assertTrue(any("the words say 30 and the figure says 60" in m for m in messages(fs, "FAIL")))
        fs = findings(self.m, CLEAN.replace("ten thousand dollars ($10,000)", "ten thousand dollars ($1,000)"))
        self.assertTrue(any("10,000" in m for m in messages(fs, "FAIL")))

    def test_words_to_number(self):
        for words, value in (("thirty", 30), ("one hundred and twenty", 120), ("ninety-nine", 99),
                             ("two lakh fifty thousand", 250000), ("one million two hundred thousand", 1200000)):
            self.assertEqual(self.m.words_to_number(words), value)

    def test_impossible_dates_fail(self):
        for d in ("31 June 2026", "February 29, 2027", "30th February 2028"):
            fs = findings(self.m, CLEAN + f"\nSigned on {d}.\n")
            self.assertTrue(any("not a real date" in m for m in messages(fs, "FAIL")), d)
        self.assertFalse(messages(findings(self.m, CLEAN + "\nSigned on 29 February 2028.\n"), "FAIL"))

    def test_defined_twice_unused_and_lower_case(self):
        text = CLEAN + '\n4.1 "Services" includes upgrades.\n\n4.2 "Customer Data" means data the Customer uploads.\n\n4.3 The services include support.\n'
        fs = findings(self.m, text)
        self.assertTrue(any("“Services” is defined more than once" in m for m in messages(fs, "FAIL")))
        self.assertTrue(any("“Customer Data” is defined but never used" in m for m in messages(fs, "WARN")))

    def test_role_used_but_never_defined(self):
        text = CLEAN + "\n4.1 The Client shall pay on time, and the Client shall not resell.\n"
        self.assertTrue(any("“Client” is used as a defined term" in m for m in messages(findings(self.m, text), "WARN")))

    def test_notice_deadline_from_term_end(self):
        import datetime as dt
        r = self.m.check(CLEAN.splitlines(), dt.date(2027, 7, 1))
        self.assertEqual(r["notices"][0]["notice_by"], "2027-05-02")
        self.assertEqual(self.m.notice_by(dt.date(2027, 3, 31), 1, "months"), dt.date(2027, 2, 28))
        self.assertEqual(self.m.notice_by(dt.date(2026, 11, 9), 5, "business days"), dt.date(2026, 11, 2))

    def test_numbered_list_inside_a_clause_is_not_a_clause(self):
        text = CLEAN.replace("2.2 Fees", "2.2 The Supplier shall:\n\n1. answer within a day;\n2. fix within a week.\n\n2.3 Fees")
        self.assertFalse(any("numbered twice" in m for m in messages(findings(self.m, text))))


class ContractCheckCliTest(unittest.TestCase):
    def test_markdown_pass_and_fail(self):
        with workdir() as d:
            f = write(os.path.join(d, "a.md"), CLEAN)
            code, out, _ = run(SKILL, SCRIPT, f, "--term-end", "2027-07-01")
            self.assertEqual(code, 0)
            self.assertIn("PASS", out)
            self.assertIn("give notice by 2027-05-02", out)
            f = write(os.path.join(d, "b.md"), CLEAN.replace("$10,000", "[●]"))
            self.assertEqual(run(SKILL, SCRIPT, f)[0], 1)

    def test_docx_is_read(self):
        body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{line}</w:t></w:r></w:p>"
                       for line in CLEAN.replace("$10,000", "[●]").replace("&", "&amp;").splitlines())
        xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/'
               f'wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>')
        with workdir() as d:
            path = os.path.join(d, "a.docx")
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("word/document.xml", xml)
            code, out, _ = run(SKILL, SCRIPT, path)
            self.assertEqual(code, 1)
            self.assertIn("[●] placeholder", out)

    def test_unreadable_file_exits_2(self):
        with workdir() as d:
            path = write(os.path.join(d, "a.docx"), "not a zip")
            self.assertEqual(run(SKILL, SCRIPT, path)[0], 2)
            self.assertEqual(run(SKILL, SCRIPT, path, "--term-end", "July")[0], 2)


if __name__ == "__main__":
    unittest.main()

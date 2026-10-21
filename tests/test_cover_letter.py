import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "cover-letter", "claim_check.py"

RESUME = """Sam Placeholder
Charge Nurse, Riverside Clinic, 2018-2025
- Supervised a ward of 24 beds and a team of 9 nurses
- Cut medication errors by 40% with a double-check protocol
- Trained staff on the Meditech record system
"""
POSTING = """Lakeview Hospital is hiring a Ward Manager for its 30-bed surgical unit.
You will lead quality improvement and use Epic every day.
"""
LETTER = """March 3, 2026

Dear Hiring Manager,

I am applying for the Ward Manager role at Lakeview Hospital.
At Riverside Clinic I supervised a ward of 24 beds and a team of 9 nurses.
I cut medication errors by 40% with a double-check protocol.

Sincerely,
Sam Placeholder
"""


class ClaimCheckLetterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def check(self, draft, sources=(RESUME,), posting=POSTING):
        return [(f["kind"], f["text"], f["line"], f["in_posting"]) for f in self.m.check(draft, list(sources), posting)]

    def test_letter_parts_claim_nothing(self):
        """Date line, salutation and sign-off are not findings."""
        self.assertEqual(self.check("March 3, 2026\n\nDear Hiring Manager,\n\nSincerely,\nSam Placeholder\n"), [])
        self.assertEqual(self.check("3rd March 2026\n"), [])

    def test_employer_from_posting_is_marked_in_posting(self):
        self.assertEqual(self.check(LETTER), [("name", "Lakeview Hospital", 5, True)])

    def test_posting_figure_claimed_as_own_is_marked_in_posting(self):
        found = self.check("At Riverside Clinic I ran a 30-bed ward.\n")
        self.assertEqual(found, [("number", "30", 1, True)])

    def test_posting_tool_claimed_as_own_is_marked_in_posting(self):
        self.assertEqual(self.check("I use Epic every day at Riverside Clinic.\n"), [("name", "Epic", 1, True)])

    def test_invented_figure_not_in_posting(self):
        self.assertEqual(self.check("I cut medication errors by 45%.\n"), [("number", "45%", 1, False)])

    def test_invented_certification(self):
        self.assertEqual(self.check("I hold a Lean Six Sigma Green Belt.\n"),
                         [("name", "Lean Six Sigma Green Belt", 1, False)])

    def test_posting_wording_borrowed_without_support(self):
        found = self.check("I would bring quality improvement to the surgical unit.\n")
        self.assertEqual(sorted(t for k, t, _, _ in found if k == "borrowed"), ["improvement", "quality", "surgical", "unit"])

    def test_wording_the_resume_also_uses_is_not_borrowed(self):
        self.assertEqual(self.check("I trained staff and supervised nurses on the ward.\n"), [])

    def test_combination_of_real_words(self):
        """Each word is in the resume, the pair is not."""
        self.assertEqual(self.check("As Charge Clinic lead I supervised nurses.\n", posting=None),
                         [("combination", "Charge Clinic", 1, False)])

    def test_title_from_a_plain_word_the_source_has_is_a_combination(self):
        """"Manager" is a plain word, but the source has it, so "Ward Manager" is built from real words."""
        source = "Charge Nurse, Riverside Clinic, 2018-2025\nRan the Ward rota.\nReported to the Clinic Manager.\n"
        self.assertEqual(self.check("Ward Manager, Riverside Clinic, 2018-2025\n", sources=(source,), posting=None),
                         [("combination", "Ward Manager", 1, False)])
        self.assertEqual(self.check("Dear Hiring Manager,\n", sources=(source,), posting=None), [])

    def test_unsourced_title_joined_to_sourced_employer_is_flagged(self):
        source = "Charge Nurse, Northwind Traders, 2018-2025\n"
        self.assertEqual(self.check("I was VP of Northwind Traders.\n", sources=(source,), posting=None),
                         [("name", "VP of Northwind Traders", 1, False)])

    def test_title_and_employer_the_source_has_are_not_flagged(self):
        letter = "I was VP of Northwind Traders.\n"
        self.assertEqual(self.check(letter, sources=("VP of Northwind Traders, 2018-2025\n",), posting=None), [])
        self.assertEqual(self.check(letter, sources=("Charge Nurse, Northwind Traders\nPromoted to VP in 2024.\n",),
                                    posting=None), [])

    def test_irregular_verb_before_sourced_name_is_not_a_finding(self):
        self.assertEqual(self.check("Taught Meditech to new staff at Riverside Clinic.\n"), [])

    def test_curly_quotes_and_dashes_normalised(self):
        self.assertEqual(self.check("I’ve trained staff on Meditech — and supervised 9 nurses.\n"), [])

    def test_cli_review_exit_1_and_in_posting_note(self):
        with workdir() as d:
            letter = write(os.path.join(d, "letter.md"), LETTER)
            src = write(os.path.join(d, "resume.md"), RESUME)
            post = write(os.path.join(d, "posting.txt"), POSTING)
            code, out, err = run(SKILL, SCRIPT, letter, "--source", src, "--posting", post)
        self.assertEqual(code, 1, err)
        self.assertIn("REVIEW", out)
        self.assertIn("1 item(s)", out)
        self.assertIn("line 5: Lakeview Hospital  [in posting]", out)

    def test_cli_clean_letter_exit_0(self):
        with workdir() as d:
            letter = write(os.path.join(d, "letter.md"), "Dear Hiring Manager,\n\nI supervised a team of 9 nurses.\n")
            src = write(os.path.join(d, "resume.md"), RESUME)
            code, out, err = run(SKILL, SCRIPT, letter, "--source", src, "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["findings"], [])

    def test_cli_missing_posting_exits_2(self):
        with workdir() as d:
            letter = write(os.path.join(d, "letter.md"), LETTER)
            src = write(os.path.join(d, "resume.md"), RESUME)
            code, out, err = run(SKILL, SCRIPT, letter, "--source", src, "--posting", os.path.join(d, "nope.txt"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_cli_empty_letter_passes(self):
        with workdir() as d:
            letter = write(os.path.join(d, "letter.md"), "")
            src = write(os.path.join(d, "resume.md"), RESUME)
            code, out, err = run(SKILL, SCRIPT, letter, "--source", src)
        self.assertEqual(code, 0, err)
        self.assertIn("PASS", out)


if __name__ == "__main__":
    unittest.main()

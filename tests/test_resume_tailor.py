import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "resume-tailor", "claim_check.py"

RESUME = """# Jordan Example

## Experience

**Senior Analyst**, Northwind Traders, 2019-2024
- Cut reporting time by 30% using Python and SQL
- Managed a budget of $2 million across 4 regions
- Worked with the Program Director on vendor contracts
- Built dashboards for the [Finance team](https://example.invalid/finance)
"""
POSTING = """Contoso is hiring a Senior Manager.
You will drive stakeholder alignment across 12 markets using Kubernetes and Tableau.
"""


class ClaimCheckResumeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def check(self, draft, sources=(RESUME,), posting=None):
        return self.m.check(draft, list(sources), posting)

    def found(self, draft, **kw):
        return [(f["kind"], f["text"]) for f in self.check(draft, **kw)]

    # --- figures ------------------------------------------------------------------------

    def test_faithful_rewrite_has_no_findings(self):
        draft = ("**Senior Analyst**, Northwind Traders, 2019-2024\n"
                 "- Used Python and SQL to cut reporting time by 30%\n"
                 "- Managed a $2M budget across 4 regions\n")
        self.assertEqual(self.check(draft), [])

    def test_inflated_percentage_flagged_with_line(self):
        draft = "Senior Analyst, Northwind Traders\n- Cut reporting time by 35% using Python\n"
        self.assertEqual([(f["kind"], f["text"], f["line"]) for f in self.check(draft)],
                         [("number", "35%", 2)])

    def test_number_forms_are_one_value(self):
        self.assertEqual(self.m.numbers("$2M"), self.m.numbers("2 million"))
        self.assertEqual(self.m.numbers("1,200 users"), {(1200.0, False)})
        self.assertEqual(self.m.numbers("3.5k"), {(3500.0, False)})
        self.assertEqual(self.m.numbers("30 percent"), {(30.0, True)})

    def test_percent_and_plain_number_differ(self):
        # 30 regions is not 30%
        self.assertEqual(self.found("- Covered 30 regions\n"), [("number", "30")])

    def test_new_team_size_flagged(self):
        self.assertEqual(self.found("- Led a team of 8 analysts\n"), [("number", "8")])

    def test_latex_escaped_figures_match(self):
        draft = "- Managed a \\$2 million budget, cutting time by 30\\%\n"
        self.assertEqual(self.check(draft), [])

    # --- names --------------------------------------------------------------------------

    def test_tool_not_in_resume_flagged(self):
        self.assertEqual(self.found("- Cut reporting time by 30% using Python and Tableau\n"),
                         [("name", "Python and Tableau")])

    def test_sentence_opening_verb_is_not_a_name(self):
        self.assertEqual(self.found("- Built dashboards in Python\n- Managed vendor contracts\n"), [])

    def test_irregular_verb_before_sourced_names_is_not_a_finding(self):
        self.assertEqual(self.found("- Wrote SQL for Northwind Traders\n"), [])

    def test_verb_before_new_acronym_dropped_from_name(self):
        self.assertEqual(self.found("- Led AWS migration\n"), [("name", "AWS")])

    def test_new_employer_flagged(self):
        self.assertEqual(self.found("Senior Analyst, Fabrikam, 2019-2024\n"), [("name", "Fabrikam")])

    def test_markdown_and_link_markup_ignored(self):
        self.assertEqual(self.found("- Built dashboards for the **Finance** team at *Northwind Traders*\n"), [])

    def test_name_key_ignores_case_plural_possessive_dots(self):
        self.assertEqual(self.m.key("Servers"), "server")
        self.assertEqual(self.m.key("Northwind's"), "northwind")
        self.assertEqual(self.m.key("U.S."), "us")
        self.assertEqual(self.m.key("Business"), "business")

    def test_name_shaped_words(self):
        self.assertTrue(self.m.looks_named("JavaScript"))
        self.assertTrue(self.m.looks_named("C++"))
        self.assertTrue(self.m.looks_named(".NET"))
        self.assertTrue(self.m.looks_named("k8s"))
        self.assertFalse(self.m.looks_named("Python"))

    # --- combinations -------------------------------------------------------------------

    def test_title_built_from_two_real_titles_is_a_combination(self):
        self.assertEqual(self.found("**Senior Director**, Northwind Traders, 2019-2024\n"),
                         [("combination", "Senior Director")])

    def test_senior_manager_from_senior_analyst_and_office_manager(self):
        source = "Senior Analyst, Fabrikam, 2020-2024\nReported to the Office Manager.\n"
        self.assertIn(("combination", "Senior Manager"),
                      self.found("Senior Manager, Fabrikam, 2020-2024\n", sources=(source,)))

    def test_unsourced_title_joined_to_sourced_employer_is_flagged(self):
        self.assertEqual(self.found("VP of Northwind Traders, 2019-2024\n"),
                         [("name", "VP of Northwind Traders")])

    def test_title_and_employer_the_source_has_are_not_flagged(self):
        draft = "VP of Northwind Traders, 2019-2024\n"
        self.assertEqual(self.found(draft, sources=("VP of Northwind Traders, 2019-2024\n",)), [])
        self.assertEqual(self.found(draft, sources=(RESUME, "Promoted to VP in 2024.\n")), [])

    def test_a_second_source_counts(self):
        notes = "Also used Tableau for ad-hoc reports.\n"
        self.assertEqual(self.found("- Shared reports from Tableau\n", sources=(RESUME, notes)), [])
        self.assertEqual(self.found("- Shared reports from Tableau\n"), [("name", "Tableau")])

    # --- the posting --------------------------------------------------------------------

    def test_posting_requirement_claimed_back_is_marked_in_posting(self):
        fs = self.check("- Deployed services on Kubernetes across 12 markets\n", posting=POSTING)
        got = {(f["kind"], f["text"]): f["in_posting"] for f in fs}
        self.assertTrue(got[("name", "Kubernetes")])
        self.assertTrue(got[("number", "12")])

    def test_borrowed_posting_wording_flagged(self):
        fs = self.check("- Drove stakeholder alignment on vendor contracts\n", posting=POSTING)
        self.assertEqual(sorted(f["text"] for f in fs if f["kind"] == "borrowed"), ["alignment", "stakeholder"])

    def test_no_borrowed_findings_without_posting(self):
        fs = self.check("- Drove stakeholder alignment on vendor contracts\n")
        self.assertEqual([f for f in fs if f["kind"] == "borrowed"], [])

    def test_findings_deduplicated(self):
        fs = self.check("- Used Tableau daily\n- Shared reports from Tableau\n")
        self.assertEqual([(f["text"], f["line"]) for f in fs], [("Tableau", 1)])

    # --- CLI ----------------------------------------------------------------------------

    def cli(self, draft, *extra, posting=None, sources=(RESUME,)):
        with workdir() as d:
            args = [write(os.path.join(d, "draft.md"), draft)]
            for i, s in enumerate(sources):
                args += ["--source", write(os.path.join(d, "src%d.md" % i), s)]
            if posting is not None:
                args += ["--posting", write(os.path.join(d, "posting.txt"), posting)]
            return run(SKILL, SCRIPT, *args, *extra)

    def test_cli_pass_exits_0(self):
        code, out, err = self.cli("- Cut reporting time by 30% using Python\n")
        self.assertEqual(code, 0, err)
        self.assertIn("PASS", out)

    def test_cli_findings_exit_1_grouped_by_kind(self):
        code, out, err = self.cli("- Cut reporting time by 35% using Kubernetes\n", posting=POSTING)
        self.assertEqual(code, 1, err)
        self.assertIn("REVIEW", out)
        self.assertIn("2 item(s)", out)
        self.assertIn("Figures not in the source (1)", out)
        self.assertIn("line 1: Kubernetes  [in posting]", out)

    def test_cli_json(self):
        code, out, err = self.cli("- Cut reporting time by 35% using Python\n", "--json")
        self.assertEqual(code, 1, err)
        data = json.loads(out)
        self.assertEqual([(f["kind"], f["text"], f["line"]) for f in data["findings"]], [("number", "35%", 1)])

    def test_cli_json_clean_draft_exits_0(self):
        code, out, err = self.cli("- Cut reporting time by 30% using Python\n", "--json")
        self.assertEqual((code, json.loads(out)["findings"]), (0, []))

    def test_cli_unreadable_file_exits_2(self):
        with workdir() as d:
            draft = write(os.path.join(d, "draft.md"), "x\n")
            code, out, err = run(SKILL, SCRIPT, draft, "--source", os.path.join(d, "missing.md"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_cli_source_is_required(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "draft.md"), "x\n"))
        self.assertEqual(code, 2)
        self.assertIn("--source", err)


if __name__ == "__main__":
    unittest.main()

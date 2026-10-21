import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "source-synthesis", "citations.py"
m = load(SKILL, SCRIPT)

SOURCES = """## Sources

- S1: Fictional pilot report, 18 pp.
- [S2] Fictional staff survey, Mar 2026
"""


def draft(body, sources=SOURCES):
    """A draft whose body starts on line 3, after a title and a blank line."""
    return "# Synthesis\n\n" + body + "\n" + sources


def check(text, *args, files=None):
    with workdir() as d:
        path = write(os.path.join(d, "draft.md"), text)
        for name, content in (files or {}).items():
            write(os.path.join(d, name), content)
        code, out, err = run(SKILL, SCRIPT, path, *args, cwd=d)
    return code, out, err


def check_json(text, *args, files=None):
    code, out, err = check(text, "--json", *args, files=files)
    return code, (json.loads(out) if out.strip() else None), err


class ParseTests(unittest.TestCase):
    def test_parse_sources_accepts_documented_forms_and_reports_dupes(self):
        sources, dupes = m.parse_sources([
            "S1: Pilot report", "- [S2] Interview notes", "* S3. Survey", "S4) Memo",
            "not a source", "S1: again"])
        self.assertEqual(list(sources), ["S1", "S2", "S3", "S4"])
        self.assertEqual(sources["S2"], "Interview notes")
        self.assertEqual(dupes, ["S1"])

    def test_units_split_paragraphs_list_items_and_table_rows(self):
        lines = ["First line of a paragraph", "continues here.", "", "- item one", "- item two",
                 "", "| Col | Col |", "|---|---|", "| a | b |"]
        self.assertEqual(m.units(lines, 10), [
            (10, "First line of a paragraph continues here."),
            (13, "- item one"), (14, "- item two"), (18, "| a | b |")])

    def test_units_skip_fenced_code(self):
        self.assertEqual(m.units(["```", "uncited code line", "```", "Text"], 1), [(4, "Text")])


class CitationsCliTests(unittest.TestCase):
    def test_clean_draft_passes(self):
        body = ("Output held steady across all four pilot teams in the trial [S1:p4].\n\n"
                "Staff reported lower stress in the follow-up survey [S2:§3.2; S1:p7].\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 0)
        self.assertTrue(rep["passed"])
        self.assertEqual((rep["sources"], rep["units_checked"], rep["errors"], rep["warnings"]),
                         (2, 2, 0, 0))
        self.assertEqual(rep["citations_per_source"], {"S1": 2, "S2": 1})

    def test_unknown_source_id_is_an_error_with_its_line(self):
        body = ("Output held steady across all four pilot teams [S1:p4].\n\n"
                "Staff reported lower stress in the follow-up survey [S9:p2] [S2:p1].\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 1)
        self.assertEqual(rep["unresolved"], [{"line": 5, "citation": "[S9:p2]", "source": "S9"}])

    def test_comma_separated_ids_are_malformed(self):
        code, rep, _ = check_json(draft("Both sources agree that output held steady [S1, S2].\n"))
        self.assertEqual(code, 1)
        self.assertEqual(rep["malformed"], [{"line": 3, "citation": "[S1, S2]"}])

    def test_comma_separated_parts_with_locations_are_malformed(self):
        code, rep, _ = check_json(draft("Both sources agree that output held steady [S1:p4, S2:p7].\n"))
        self.assertEqual(code, 1)
        self.assertEqual(len(rep["malformed"]), 1)

    def test_uncited_claim_is_an_error(self):
        body = ("Output held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                "Customers noticed slower replies on Fridays during the pilot.\n")
        code, out, _ = check(draft(body))
        self.assertEqual(code, 1)
        self.assertIn("## Errors: uncited claims (1)", out)
        self.assertIn('line 5: "Customers noticed slower replies', out)
        self.assertIn("Result: FAIL", out)

    def test_multi_line_paragraph_is_one_unit_cited_anywhere(self):
        body = ("Output held steady across all four pilot teams\n"
                "according to the final report [S1:p4; S2:p1].\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 0)
        self.assertEqual(rep["units_checked"], 1)

    def test_bare_id_warns_and_strict_fails(self):
        body = "Output held steady across all four pilot teams [S1; S2:p3].\n"
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 0)
        self.assertEqual(rep["no_location"], [{"line": 3, "citation": "[S1; S2:p3]"}])
        code, rep, _ = check_json(draft(body), "--strict")
        self.assertEqual(code, 1)
        self.assertFalse(rep["passed"])

    def test_unused_source_is_a_warning(self):
        code, rep, _ = check_json(draft("Output held steady across all four pilot teams [S1:p4].\n"))
        self.assertEqual(code, 0)
        self.assertEqual(rep["unused_sources"], ["S2"])
        self.assertEqual(rep["warnings"], 1)

    def test_outside_tag_counts_as_cited_and_is_listed(self):
        body = ("Output held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                "National averages for the sector were higher that year [outside].\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 0)
        self.assertEqual(rep["uncited"], [])
        self.assertEqual([o["line"] for o in rep["outside"]], [5])

    def test_non_claim_units_are_not_checked(self):
        body = ("Output held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                "_Prepared for the steering group on a fictional date_\n\n"
                "**Strength:** moderate, because two independent sources agree on this\n\n"
                "Short label line\n\n"
                "An aside that the author marked as needing no citation <!-- no-cite -->\n\n"
                "[S1 report](https://example.com/report) is linked here for the reader.\n"
                "```\nuncited text in a code block that is long enough\n```\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(rep["uncited"], [{"line": 13, "text": "[S1 report](https://example.com/report) is linked here for the reader."}])
        self.assertEqual(rep["units_checked"], 2)

    def test_question_and_sources_sections_need_no_citations(self):
        text = ("## Question\n\nDid the pilot keep output steady across every team?\n\n"
                "## Findings\n\nOutput held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                + SOURCES)
        code, rep, _ = check_json(text)
        self.assertEqual(code, 0)
        self.assertEqual(rep["units_checked"], 1)

    def test_min_words_zero_checks_short_units(self):
        body = "Output held steady across all four pilot teams [S1:p4; S2:p1].\n\nShort label line\n"
        self.assertEqual(check_json(draft(body))[0], 0)
        code, rep, _ = check_json(draft(body), "--min-words", "0")
        self.assertEqual(code, 1)
        self.assertEqual(rep["uncited"], [{"line": 5, "text": "Short label line"}])

    def test_label_flag_replaces_default_labels(self):
        body = ("Output held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                "**Strength:** moderate, because two independent sources agree on this\n\n"
                "**Caveat:** small sample and one employer in a single fictional sector\n")
        code, rep, _ = check_json(draft(body), "--label", "Caveat")
        self.assertEqual(code, 1)
        self.assertEqual([u["line"] for u in rep["uncited"]], [5])

    def test_skip_section_flag(self):
        text = ("## Method\n\nWe read every source twice and compared the figures by hand.\n\n"
                "## Findings\n\nOutput held steady across all four pilot teams [S1:p4; S2:p1].\n\n"
                + SOURCES)
        self.assertEqual(check_json(text)[0], 1)
        code, rep, _ = check_json(text, "--skip-section", "method")
        self.assertEqual(code, 0)

    def test_list_items_and_table_rows_are_claims_but_table_header_is_not(self):
        body = ("- Output held steady across all four pilot teams [S1:p4].\n"
                "- Staff reported lower stress in the follow-up survey.\n\n"
                "| Measure of the pilot outcome | Finding for the teams |\n"
                "|---|---|\n"
                "| Output in all four pilot teams | steady overall [S2:p1] |\n"
                "| Customer reply times on Fridays | slower than before |\n")
        code, rep, _ = check_json(draft(body))
        self.assertEqual(code, 1)
        self.assertEqual([u["line"] for u in rep["uncited"]], [4, 9])
        self.assertEqual(rep["units_checked"], 4)

    def test_sources_file_flag(self):
        files = {"sources.md": "S1: Fictional pilot report\nS2: Fictional survey\n"}
        text = "Output held steady across all four pilot teams [S1:p4; S2:p2].\n"
        code, rep, _ = check_json(text, "--sources", "sources.md", files=files)
        self.assertEqual(code, 0)
        self.assertEqual(rep["sources"], 2)

    def test_output_flag_writes_report_and_prints_summary(self):
        with workdir() as d:
            path = write(os.path.join(d, "draft.md"),
                         draft("Output held steady across all four pilot teams [S1:p4].\n"))
            dest = os.path.join(d, "report.md")
            code, out, _ = run(SKILL, SCRIPT, path, "-o", dest)
            self.assertEqual(code, 0)
            self.assertIn("PASS, 0 error(s), 1 warning(s)", out)
            report = read(dest)
        self.assertIn("# Citation check: draft.md", report)
        self.assertIn("| S1 | 1 |", report)
        self.assertIn("| S2 | 0 |", report)

    def test_no_sources_is_bad_input(self):
        code, _, err = check("Output held steady across all four pilot teams [S1:p4].\n")
        self.assertEqual(code, 2)
        self.assertIn("no sources found", err)

    def test_duplicate_source_ids_are_bad_input(self):
        code, _, err = check(draft("Text [S1:p1].\n", sources="## Sources\n\nS1: a\nS1: b\n"))
        self.assertEqual(code, 2)
        self.assertIn("duplicate source ids", err)
        self.assertIn("S1", err)

    def test_missing_draft_and_negative_min_words_are_bad_input(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.md"))
        self.assertEqual(code, 2)
        self.assertIn("file not found", err)
        self.assertNotIn("Traceback", err)
        code, _, err = check(draft("Text [S1:p1].\n"), "--min-words", "-1")
        self.assertEqual(code, 2)
        self.assertIn("--min-words must be zero or more", err)


if __name__ == "__main__":
    unittest.main()

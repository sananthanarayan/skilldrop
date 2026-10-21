import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "output-hygiene", "scrub.py"
m = load(SKILL, SCRIPT)

ZWSP, NBSP, BOM, LSEP = "​", " ", "﻿", " "
RLO, CYR_A = "‮", "а"
TRAILER = "Co-Authored-By: Claude Opus <noreply@example.com>"
FOOTER = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)"


def classes(findings):
    return [(f["class"], f["tier"]) for f in findings]


class ScanCharacterTests(unittest.TestCase):
    def test_clean_ascii_text_has_no_findings_and_is_unchanged(self):
        text = "Plain text.\n\nSecond paragraph.\n"
        findings, cleaned = m.scan(text)
        self.assertEqual(findings, [])
        self.assertEqual(cleaned, text)

    def test_zero_width_space_reported_at_line_and_col_and_removed(self):
        findings, cleaned = m.scan("first\nab" + ZWSP + "cd\n")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual((f["class"], f["tier"], f["line"], f["col"]), ("invisible", "auto", 2, 3))
        self.assertIn("U+200B ZERO WIDTH SPACE", f["detail"])
        self.assertEqual(cleaned, "first\nabcd\n")

    def test_bom_and_bidi_override_are_invisible_auto_findings(self):
        findings, cleaned = m.scan(BOM + "pay " + RLO + "txt")
        self.assertEqual(classes(findings), [("invisible", "auto"), ("invisible", "auto")])
        self.assertEqual(cleaned, "pay txt")

    def test_line_separator_becomes_a_newline(self):
        findings, cleaned = m.scan("one" + LSEP + "two")
        self.assertEqual(classes(findings), [("invisible", "auto")])
        self.assertEqual(cleaned, "one\ntwo")

    def test_no_break_space_reported_as_spacing_and_flattened(self):
        findings, cleaned = m.scan("10" + NBSP + "ms")
        self.assertEqual(classes(findings), [("spacing", "auto")])
        self.assertIn("U+00A0 NO-BREAK SPACE", findings[0]["detail"])
        self.assertEqual(cleaned, "10 ms")

    def test_cyrillic_letter_in_ascii_word_is_review_homoglyph_left_alone(self):
        text = "p" + CYR_A + "ssword"
        findings, cleaned = m.scan(text)
        self.assertEqual(classes(findings), [("homoglyph", "review")])
        self.assertEqual((findings[0]["line"], findings[0]["col"]), (1, 2))
        self.assertIn("CYRILLIC SMALL LETTER A", findings[0]["detail"])
        self.assertEqual(cleaned, text)

    def test_all_non_ascii_word_and_superscript_are_not_homoglyphs(self):
        findings, _ = m.scan("привет and O(n²)")
        self.assertEqual(findings, [])

    def test_findings_sorted_by_line_then_col(self):
        findings, _ = m.scan("a" + NBSP + "b" + ZWSP + "\n" + ZWSP + "c")
        self.assertEqual([(f["line"], f["col"]) for f in findings], [(1, 2), (1, 4), (2, 1)])


class ScanTypographyTests(unittest.TestCase):
    TEXT = "It’s three phases — each gated…"

    def test_markdown_default_does_not_report_curly_quotes_or_dashes(self):
        findings, cleaned = m.scan(self.TEXT)
        self.assertEqual(findings, [])
        self.assertEqual(cleaned, self.TEXT)

    def test_commit_medium_reports_typography_as_review_and_keeps_it(self):
        findings, cleaned = m.scan(self.TEXT, medium="commit")
        self.assertEqual(classes(findings), [("typography", "review")] * 3)
        self.assertEqual(cleaned, self.TEXT)

    def test_ascii_mode_makes_typography_auto_and_flattens_it(self):
        findings, cleaned = m.scan(self.TEXT, ascii_mode=True)
        self.assertEqual(classes(findings), [("typography", "auto")] * 3)
        self.assertEqual(cleaned, "It's three phases -- each gated...")


class ScanProvenanceAndCloserTests(unittest.TestCase):
    def test_co_authored_by_claude_trailer_dropped(self):
        text = "Fix the parser\n\n" + TRAILER + "\n"
        findings, cleaned = m.scan(text)
        self.assertEqual(classes(findings), [("provenance", "auto")])
        self.assertEqual(findings[0]["line"], 3)
        self.assertEqual(cleaned, "Fix the parser\n")

    def test_human_co_author_trailer_is_kept(self):
        text = "Fix\n\nCo-authored-by: Pat Example <pat@example.com>\n"
        findings, cleaned = m.scan(text)
        self.assertEqual(findings, [])
        self.assertEqual(cleaned, text)

    def test_generated_with_claude_code_footer_dropped(self):
        findings, cleaned = m.scan("Summary of the change.\n\n" + FOOTER + "\n")
        self.assertEqual(classes(findings), [("provenance", "auto")])
        self.assertEqual(cleaned, "Summary of the change.\n")

    def test_dash_claude_signature_dropped_but_claude_bullet_kept(self):
        findings, cleaned = m.scan("Notes\n— Claude\n")
        self.assertEqual(classes(findings), [("provenance", "auto")])
        self.assertEqual(cleaned, "Notes\n")
        bullet = "- Claude Code project settings: see the docs\n"
        self.assertEqual(m.scan(bullet), ([], bullet))

    def test_trailing_closer_paragraph_removed(self):
        text = "The answer is 42.\n\nLet me know if you want the derivation.\n"
        findings, cleaned = m.scan(text)
        self.assertEqual(classes(findings), [("closer", "auto")])
        self.assertEqual(findings[0]["line"], 3)
        self.assertEqual(cleaned, "The answer is 42.\n")

    def test_closer_phrase_not_in_final_block_is_kept(self):
        text = "Hope this helps frame the trade-off.\n\nThe answer is 42.\n"
        self.assertEqual(m.scan(text), ([], text))

    def test_single_block_closer_is_not_removed(self):
        text = "Let me know if you want more."
        self.assertEqual(m.scan(text), ([], text))

    def test_closer_line_refers_to_original_text_after_dropped_trailer(self):
        text = "Intro\n\n" + TRAILER + "\n\nLet me know if you want more.\n"
        findings, _ = m.scan(text)
        closer = [f for f in findings if f["class"] == "closer"][0]
        self.assertEqual(closer["line"], 5)


class ScrubCliTests(unittest.TestCase):
    def test_report_mode_exits_1_and_leaves_file_untouched(self):
        with workdir() as d:
            p = write(os.path.join(d, "draft.md"), "ab" + ZWSP + "c\n")
            code, out, _ = run(SKILL, SCRIPT, p)
            self.assertEqual(code, 1)
            self.assertIn("1 finding(s)", out)
            self.assertIn("U+200B", out)
            self.assertEqual(read(p), "ab" + ZWSP + "c\n")

    def test_clean_file_exits_0_and_says_clean(self):
        with workdir() as d:
            p = write(os.path.join(d, "draft.md"), "All good.\n")
            code, out, _ = run(SKILL, SCRIPT, p)
            self.assertEqual(code, 0)
            self.assertIn("clean", out)

    def test_fix_rewrites_file_and_exits_0_when_only_auto_findings(self):
        with workdir() as d:
            p = write(os.path.join(d, "draft.md"), "Done" + NBSP + "now.\n\n" + TRAILER + "\n")
            code, out, _ = run(SKILL, SCRIPT, p, "--fix")
            self.assertEqual(code, 0)
            self.assertIn("applied", out)
            self.assertEqual(read(p), "Done now.\n")

    def test_fix_exits_1_while_review_findings_remain(self):
        with workdir() as d:
            p = write(os.path.join(d, "draft.md"), "p" + CYR_A + "y" + ZWSP + "\n")
            code, _, _ = run(SKILL, SCRIPT, p, "--fix")
            self.assertEqual(code, 1)
            self.assertEqual(read(p), "p" + CYR_A + "y\n")

    def test_stdin_fix_writes_cleaned_text_to_stdout_and_report_to_stderr(self):
        code, out, err = run(SKILL, SCRIPT, "-", "--fix", stdin="x" + ZWSP + "y\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "xy\n")
        self.assertIn("1 finding(s)", err)

    def test_json_output_lists_findings_and_remaining(self):
        code, out, _ = run(SKILL, SCRIPT, "-", "--json", stdin="a" + NBSP + "b\n")
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["remaining"], 1)
        f = data["results"][0]["findings"][0]
        self.assertEqual((f["class"], f["line"], f["col"]), ("spacing", 1, 2))

    def test_medium_commit_flag_turns_curly_quote_into_a_finding(self):
        text = "Don’t panic\n"
        self.assertEqual(run(SKILL, SCRIPT, "-", "--quiet", stdin=text)[0], 0)
        code, out, _ = run(SKILL, SCRIPT, "-", "--medium", "commit", stdin=text)
        self.assertEqual(code, 1)
        self.assertIn("RIGHT SINGLE QUOTATION MARK", out)

    def test_ascii_fix_flattens_typography_in_file(self):
        with workdir() as d:
            p = write(os.path.join(d, "msg.txt"), "“ok” – done\n")
            code, _, _ = run(SKILL, SCRIPT, p, "--ascii", "--fix")
            self.assertEqual(code, 0)
            self.assertEqual(read(p), '"ok" - done\n')

    def test_quiet_prints_nothing(self):
        code, out, err = run(SKILL, SCRIPT, "-", "--quiet", stdin="a" + ZWSP + "\n")
        self.assertEqual((code, out, err), (1, "", ""))

    def test_json_and_quiet_together_is_usage_error(self):
        code, _, err = run(SKILL, SCRIPT, "-", "--json", "--quiet", stdin="x")
        self.assertEqual(code, 2)
        self.assertIn("mutually exclusive", err)

    def test_missing_file_exits_2_with_message(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "nope.md"))
            self.assertEqual(code, 2)
            self.assertIn("cannot read", err)
            self.assertNotIn("Traceback", err)

    def test_non_utf8_file_exits_2_with_message(self):
        with workdir() as d:
            p = os.path.join(d, "latin1.txt")
            with open(p, "wb") as f:
                f.write(b"caf\xe9\n")
            code, _, err = run(SKILL, SCRIPT, p)
            self.assertEqual(code, 2)
            self.assertIn("not UTF-8", err)

    def test_unknown_medium_rejected(self):
        code, _, err = run(SKILL, SCRIPT, "-", "--medium", "docx", stdin="x")
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)


if __name__ == "__main__":
    unittest.main()

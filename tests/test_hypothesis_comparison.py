import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "hypothesis-comparison", "ach_matrix.py"

MATRIX = (
    "id,evidence,weight,H1,H2,H3\n"
    "E1,Error logs spike at 10:02,2,C,I,II\n"
    "E2,Support tickets mention slowness,1,C,C,C\n"
    "E3,Deploy finished at 10:00,1,I,C,N\n"
)
# H1 = 1 (E3), H2 = 2 (E1 x2), H3 = 4 (E1 II x2)


class AchScoringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def matrix(self, text):
        with workdir() as d:
            return self.m.load(write(os.path.join(d, "m.csv"), text))

    def test_weighted_inconsistency_scores(self):
        hyps, rows = self.matrix(MATRIX)
        self.assertEqual(hyps, ["H1", "H2", "H3"])
        self.assertEqual(self.m.scores(hyps, rows), {"H1": 1.0, "H2": 2.0, "H3": 4.0})

    def test_consistent_ratings_never_lower_a_score(self):
        hyps, rows = self.matrix("evidence,A,B\nx,CC,I\ny,CC,C\nz,CC,N\n")
        self.assertEqual(self.m.scores(hyps, rows), {"A": 0.0, "B": 1.0})

    def test_ranking_is_lowest_first_and_ties_keep_column_order(self):
        s = {"A": 2.0, "B": 1.0, "C": 1.0}
        self.assertEqual(self.m.ranking(["A", "B", "C"], s), ["B", "C", "A"])
        self.assertEqual(self.m.leaders(["A", "B", "C"], s), ["B", "C"])

    def test_default_id_and_weight_and_lowercase_ratings(self):
        hyps, rows = self.matrix("evidence,A,B\nfirst,c,ii\n")
        self.assertEqual(rows[0]["id"], "E1")
        self.assertEqual(rows[0]["weight"], 1.0)
        self.assertEqual(rows[0]["ratings"], {"A": "C", "B": "II"})

    def test_fmt_trims_trailing_zeros(self):
        self.assertEqual(self.m.fmt(3.0), "3")
        self.assertEqual(self.m.fmt(0.5), "0.5")
        self.assertEqual(self.m.fmt(1.25), "1.25")


class AchReportTest(unittest.TestCase):
    def report(self, text):
        with workdir() as d:
            p = write(os.path.join(d, "matrix.csv"), text)
            return run(SKILL, SCRIPT, p)

    def test_ranking_table_and_leader(self):
        code, out, err = self.report(MATRIX)
        self.assertEqual(code, 0, err)
        self.assertIn("3 hypotheses · 3 pieces of evidence", out)
        self.assertIn("| 1 | H1 | 1 | 1 | 0 | 2 |", out)
        self.assertIn("| 2 | H2 | 2 | 1 | 0 | 2 |", out)
        self.assertIn("| 3 | H3 | 4 | 0 | 1 | 1 |", out)
        self.assertLess(out.index("| H1 |"), out.index("| H2 |"))
        self.assertIn("**Least contradicted:** H1 (score 1), 1 ahead of H2.", out)

    def test_non_diagnostic_rows_are_named(self):
        _, out, _ = self.report(MATRIX)
        self.assertIn("| E2 | Support tickets mention slowness | 1 | C | C | C | no |", out)
        self.assertIn("| E1 | Error logs spike at 10:02 | 2 | C | I | II | yes |", out)
        self.assertIn("**Non-diagnostic:** E2.", out)

    def test_mix_of_consistent_and_neutral_is_non_diagnostic(self):
        _, out, _ = self.report("id,evidence,A,B,C\nX1,mixed,C,CC,N\nX2,splits,I,C,C\n")
        self.assertIn("**Non-diagnostic:** X1.", out)

    def test_linchpin_found_by_dropping_each_row(self):
        _, out, _ = self.report(MATRIX)
        self.assertIn("- **E1** (Error logs spike at 10:02): without it, first place is H2 and H3 (tie)", out)
        self.assertNotIn("- **E3**", out)
        self.assertNotIn("- **E2**", out)

    def test_no_linchpin_message(self):
        _, out, _ = self.report("evidence,A,B\none,C,I\ntwo,C,I\n")
        self.assertIn("No single piece of evidence changes first place when removed.", out)

    def test_tie_shares_rank_and_is_called_a_tie(self):
        _, out, _ = self.report("evidence,A,B,C\none,I,I,II\n")
        self.assertIn("| 1 | A | 1 |", out)
        self.assertIn("| 1 | B | 1 |", out)
        self.assertIn("| 3 | C | 2 |", out)
        self.assertIn("**Tie for first:** A, B.", out)

    def test_output_file_and_summary_line(self):
        with workdir() as d:
            p = write(os.path.join(d, "matrix.csv"), MATRIX)
            target = os.path.join(d, "ach-report.md")
            code, out, err = run(SKILL, SCRIPT, p, "-o", target)
            self.assertEqual(code, 0, err)
            self.assertIn("first: H1", out)
            self.assertIn("## Sensitivity", read(target))

    def test_utf8_bom_header_is_accepted(self):
        code, out, err = self.report("﻿evidence,A,B\none,C,I\n")
        self.assertEqual(code, 0, err)
        self.assertIn("**Least contradicted:** A", out)


class AchBadInputTest(unittest.TestCase):
    def fails(self, text, message):
        with workdir() as d:
            p = write(os.path.join(d, "m.csv"), text)
            code, _, err = run(SKILL, SCRIPT, p)
        self.assertEqual(code, 2, err)
        self.assertIn(message, err)
        self.assertNotIn("Traceback", err)

    def test_missing_file(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "nope.csv"))
        self.assertEqual(code, 2)
        self.assertIn("file not found", err)

    def test_empty_file(self):
        self.fails("", "the CSV is empty")

    def test_header_only(self):
        self.fails("evidence,A,B\n", "no evidence rows")

    def test_needs_evidence_column(self):
        self.fails("id,A,B\nE1,C,I\n", "needs an 'evidence' column")

    def test_needs_two_hypotheses(self):
        self.fails("evidence,A\nx,C\n", "at least two hypothesis columns")

    def test_bad_rating(self):
        self.fails("evidence,A,B\nx,C,maybe\n", "rating 'maybe' is not one of")

    def test_bad_or_zero_weight(self):
        self.fails("evidence,weight,A,B\nx,heavy,C,I\n", "weight 'heavy' is not a number")
        self.fails("evidence,weight,A,B\nx,0,C,I\n", "weight must be greater than 0")

    def test_empty_evidence_cell(self):
        self.fails("id,evidence,A,B\nE1,,C,I\n", "row 2: the evidence cell is empty")

    def test_duplicate_ids(self):
        self.fails("id,evidence,A,B\nE1,x,C,I\nE1,y,I,C\n", "duplicate evidence ids: E1")

    def test_row_with_extra_cells_fails_clearly(self):
        self.fails("evidence,A,B\nslow, then fast,C,I\n", "row 2")


    def test_row_number_is_the_file_line_after_a_blank_line(self):
        self.fails("evidence,H1,H2\n\nE1 drop,C,X\n", "row 3 (E1), column 'H2'")

    def test_non_finite_weight(self):
        for w in ("nan", "inf"):
            with self.subTest(w):
                self.fails("evidence,weight,H1,H2\nE1,%s,C,I\n" % w, "is not a finite number")


if __name__ == "__main__":
    unittest.main()

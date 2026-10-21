import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "risk-register", "check_register.py"
m = load(SKILL, SCRIPT)

COLUMNS = ["id", "title", "cause", "event", "consequence", "owner",
           "inherent_likelihood", "inherent_impact", "residual_likelihood", "residual_impact",
           "treatment", "controls", "due_date", "next_review", "review_trigger", "status"]
HEADER = ",".join(COLUMNS)


def row(**over):
    base = {"id": "R1", "title": "Supplier outage", "cause": "single supplier",
            "event": "supplier fails", "consequence": "orders stop", "owner": "Head of Ops",
            "inherent_likelihood": "4", "inherent_impact": "4",
            "residual_likelihood": "2", "residual_impact": "3",
            "treatment": "reduce", "controls": "second supplier", "due_date": "2026-12-01",
            "next_review": "2026-12-01", "review_trigger": "supplier change", "status": "open"}
    base.update(over)
    return ",".join(base[c] for c in COLUMNS)


def check(rows, *args, header=HEADER):
    with workdir() as d:
        path = write(os.path.join(d, "register.csv"), header + "\n" + "".join(r + "\n" for r in rows))
        return run(SKILL, SCRIPT, path, "--as-of", "2026-10-01", *args, cwd=d)


class BandTests(unittest.TestCase):
    def test_band_for_5x5_matches_documented_bands(self):
        got = [(s, m.band_for(s, 5)) for s in (1, 4, 5, 9, 10, 16, 20, 25)]
        self.assertEqual(got, [(1, "low"), (4, "low"), (5, "medium"), (9, "medium"),
                               (10, "high"), (16, "high"), (20, "critical"), (25, "critical")])

    def test_band_ranges_5x5_and_3x3(self):
        self.assertEqual(m.band_ranges(5), {"low": (1, 4), "medium": (5, 9),
                                            "high": (10, 16), "critical": (20, 25)})
        self.assertEqual(m.band_ranges(3), {"low": (1, 1), "medium": (2, 3),
                                            "high": (4, 4), "critical": (6, 9)})

    def test_heat_map_places_counts_by_likelihood_row_and_impact_column(self):
        rows = [{"l": 3, "i": 1}, {"l": 3, "i": 1}, {"l": 1, "i": 2}]
        lines = m.heat_map(rows, "l", "i", 3)
        self.assertEqual(lines[2], "    3 |   2   .   .")
        self.assertEqual(lines[3], "    2 |   .   .   .")
        self.assertEqual(lines[4], "    1 |   .   1   .")

    def test_band_counts(self):
        rows = [{"l": 1, "i": 2}, {"l": 3, "i": 3}, {"l": 5, "i": 4}, {"l": 5, "i": 5}]
        self.assertEqual(m.band_counts(rows, "l", "i", 5),
                         {"low": 1, "medium": 1, "high": 0, "critical": 2})


class CheckRegisterCliTests(unittest.TestCase):
    def test_valid_register_passes_with_exit_0(self):
        code, out, _ = check([row(), row(id="R2", status="closed")])
        self.assertEqual(code, 0, out)
        self.assertIn("2 read, 2 valid, 1 open", out)
        self.assertIn("Errors (0)", out)
        self.assertIn("Result: PASS", out)

    def test_residual_heat_map_counts_open_rows_only(self):
        code, out, _ = check([row(), row(id="R2", residual_likelihood="2", residual_impact="3"),
                              row(id="R3", status="closed")])
        self.assertEqual(code, 0, out)
        residual = out.split("Residual heat map")[1]
        self.assertIn("    2 |   .   .   2   .   .", residual)
        self.assertIn("low 0, medium 2, high 0, critical 0", residual)

    def test_generic_owners_are_errors(self):
        for owner in ("TBD", "IT", "team"):
            code, out, _ = check([row(owner=owner)])
            self.assertEqual(code, 1, owner)
            self.assertIn("is not a named person or role", out)

    def test_empty_required_value_is_an_error(self):
        code, out, _ = check([row(title="")])
        self.assertEqual(code, 1)
        self.assertIn("line 2 [R1]: title is empty", out)

    def test_optional_columns_may_be_blank_but_review_trigger_warns(self):
        code, out, _ = check([row(treatment="accept", controls="", due_date="", review_trigger="")])
        self.assertEqual(code, 0, out)
        self.assertIn("Warnings (1)", out)
        self.assertIn("no review_trigger", out)

    def test_scores_out_of_range_or_not_integers_are_errors(self):
        code, out, _ = check([row(inherent_impact="6", residual_likelihood="two")])
        self.assertEqual(code, 1)
        self.assertIn("inherent_impact=6 is outside the 1-5 scale", out)
        self.assertIn("residual_likelihood must be a whole number 1-5, got 'two'", out)
        self.assertIn("1 read, 0 valid", out)

    def test_scale_flag_changes_the_valid_range(self):
        code, out, _ = check([row()], "--scale", "3")
        self.assertEqual(code, 1)
        self.assertIn("inherent_likelihood=4 is outside the 1-3 scale", out)
        code, out, _ = check([row(inherent_likelihood="9", inherent_impact="7")], "--scale", "10")
        self.assertEqual(code, 0, out)
        self.assertIn("scale:  1-10", out)

    def test_scale_outside_3_to_10_is_bad_input(self):
        for scale in ("2", "11"):
            code, _, err = check([row()], "--scale", scale)
            self.assertEqual(code, 2)
            self.assertIn("--scale must be between 3 and 10", err)

    def test_residual_above_inherent_is_an_error(self):
        code, out, _ = check([row(inherent_likelihood="2", inherent_impact="2",
                                  residual_likelihood="3", residual_impact="2")])
        self.assertEqual(code, 1)
        self.assertIn("residual score 6 is higher than inherent score 4", out)

    def test_duplicate_id_names_the_first_line(self):
        code, out, _ = check([row(), row(title="Another")])
        self.assertEqual(code, 1)
        self.assertIn("line 3 [R1]: duplicate id, first seen on line 2", out)

    def test_bad_treatment_status_and_date_are_errors(self):
        code, out, _ = check([row(treatment="ignore", status="pending", next_review="01/12/2026")])
        self.assertEqual(code, 1)
        self.assertIn("treatment 'ignore' is not one of", out)
        self.assertIn("status 'pending' is not open or closed", out)
        self.assertIn("next_review must be YYYY-MM-DD, got '01/12/2026'", out)

    def test_treatment_and_status_are_case_insensitive(self):
        code, out, _ = check([row(treatment="Reduce", status="Open")])
        self.assertEqual(code, 0, out)

    def test_treatment_warnings_do_not_fail_the_register(self):
        code, out, _ = check([
            row(id="R1", due_date="", controls=""),
            row(id="R2", residual_likelihood="4", residual_impact="4"),
            row(id="R3", treatment="accept", inherent_likelihood="4", inherent_impact="5",
                residual_likelihood="4", residual_impact="4"),
        ])
        self.assertEqual(code, 0, out)
        self.assertIn("line 2 [R1]: treatment is reduce but there is no due_date", out)
        self.assertIn("line 2 [R1]: treatment is reduce but no controls are listed", out)
        self.assertIn("line 3 [R2]: treatment is reduce but residual equals inherent (16)", out)
        self.assertIn("line 4 [R3]: accepting a high residual risk (16) needs a named sign-off", out)
        self.assertIn("Warnings (4)", out)

    def test_overdue_reviews_and_actions_for_open_risks_only(self):
        code, out, _ = check([row(next_review="2026-09-21", due_date="2026-09-30"),
                              row(id="R2", status="closed", next_review="2026-01-01")])
        self.assertEqual(code, 0, out)
        self.assertIn("Overdue (2)", out)
        self.assertIn("review overdue by 10 day(s) (next_review 2026-09-21), owner Head of Ops", out)
        self.assertIn("treatment action overdue by 1 day(s)", out)
        self.assertNotIn("[R2]: review overdue", out)

    def test_top_risks_ranked_by_residual_then_inherent_then_id(self):
        code, out, _ = check([
            row(id="R1", residual_likelihood="2", residual_impact="2"),
            row(id="R2", residual_likelihood="3", residual_impact="3"),
            row(id="R3", inherent_likelihood="5", inherent_impact="5",
                residual_likelihood="3", residual_impact="3"),
            row(id="R0", residual_likelihood="3", residual_impact="3"),
        ], "--top", "3")
        self.assertEqual(code, 0, out)
        top = out.split("Top 3 open risks by residual score")[1].strip().splitlines()
        self.assertEqual([line.split()[0] for line in top[:3]], ["R3", "R0", "R2"])
        self.assertNotIn("R1  residual", out)
        self.assertIn("R3  residual 9 (medium), inherent 25", out)

    def test_reads_stdin_with_dash(self):
        csv_text = HEADER + "\n" + row() + "\n"
        code, out, _ = run(SKILL, SCRIPT, "-", "--as-of", "2026-10-01", stdin=csv_text)
        self.assertEqual(code, 0, out)
        self.assertIn("1 read, 1 valid, 1 open", out)

    def test_out_writes_the_same_report(self):
        with workdir() as d:
            src = write(os.path.join(d, "r.csv"), HEADER + "\n" + row() + "\n")
            dest = os.path.join(d, "report.txt")
            code, out, _ = run(SKILL, SCRIPT, src, "--as-of", "2026-10-01", "--out", dest)
            self.assertEqual(code, 0)
            self.assertEqual(read(dest), out)

    def test_missing_file_is_bad_input(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, os.path.join(d, "nope.csv"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_empty_file_and_missing_column_are_bad_input(self):
        with workdir() as d:
            empty = write(os.path.join(d, "empty.csv"), "")
            code, _, err = run(SKILL, SCRIPT, empty)
            self.assertEqual(code, 2)
            self.assertIn("has no header row", err)
        code, _, err = check([], header=HEADER.replace(",owner", ""))
        self.assertEqual(code, 2)
        self.assertIn("missing required column(s): owner", err)

    def test_bad_as_of_is_bad_input(self):
        with workdir() as d:
            src = write(os.path.join(d, "r.csv"), HEADER + "\n" + row() + "\n")
            code, _, err = run(SKILL, SCRIPT, src, "--as-of", "1 Oct 2026")
        self.assertEqual(code, 2)
        self.assertIn("--as-of must be YYYY-MM-DD", err)

    def test_utf8_bom_file_is_read(self):
        with workdir() as d:
            src = write(os.path.join(d, "r.csv"), "﻿" + HEADER + "\n" + row() + "\n")
            code, out, _ = run(SKILL, SCRIPT, src, "--as-of", "2026-10-01")
        self.assertEqual(code, 0, out)

    def test_utf8_bom_on_stdin_is_read(self):
        code, out, err = run(SKILL, SCRIPT, "-", "--as-of", "2026-10-01",
                             stdin="﻿" + HEADER + "\n" + row() + "\n")
        self.assertEqual(code, 0, err)

    def test_line_numbers_count_blank_lines(self):
        code, out, _ = check(["", row(title="")])
        self.assertEqual(code, 1)
        self.assertIn("line 3 [R1]: title is empty", out)


if __name__ == "__main__":
    unittest.main()

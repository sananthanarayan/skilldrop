import json
import os
import unittest
from pathlib import Path

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "feedback-synthesis", "theme_counts.py"

SHEET = (
    "item_id,person_id,source,themes,severity,plan,quote\n"
    "T1,A,tickets,login;slow,S2,pro,Cannot sign in and it is slow\n"
    "T2,A,tickets,login,S1,pro,Locked out again\n"
    "T3,A,tickets,login,S3,pro,Login still flaky\n"
    "T4,B,nps,slow,S3,free,Pages drag\n"
    "T5,C,nps,slow:S1;+fast-support,,free,Checkout froze but support was quick\n"
    "T6,,interview,login,S2,,Someone mentioned login trouble\n"
    "T7,D,interview,,,pro,Nothing in particular\n"
)


class ThemeCountsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def counts(self, text, person_col="person_id", segments=()):
        with workdir() as d:
            p = Path(write(os.path.join(d, "coded.csv"), text))
            rows, segs, warnings = self.m.load(p, person_col, self.m.DEFAULT_IGNORE, list(segments))
        summary, themes = self.m.analyse(rows, segs)
        return summary, {t["theme"]: t for t in themes}, [t["theme"] for t in themes], warnings

    def test_quote_column_is_ignored_and_other_columns_are_segments(self):
        with workdir() as d:
            p = Path(write(os.path.join(d, "coded.csv"), SHEET))
            _, segs, _ = self.m.load(p, "person_id", self.m.DEFAULT_IGNORE, [])
        self.assertEqual(segs, ["plan"])

    def test_people_counted_once_however_many_items(self):
        _, t, _, _ = self.counts(SHEET)
        self.assertEqual(t["login"]["mentions"], 4)
        self.assertEqual(t["login"]["people"], 1)
        self.assertEqual(t["login"]["repeat_filers"], {"A": 3})
        self.assertEqual(t["slow"]["people"], 3)
        self.assertEqual(t["slow"]["mentions"], 3)

    def test_rows_without_person_id_are_reported_beside_people_not_added(self):
        summary, t, _, _ = self.counts(SHEET)
        self.assertEqual(t["login"]["no_id_items"], 1)
        self.assertEqual(t["login"]["sources"],
                         {"interview": {"people": 0, "no_id_items": 1},
                          "tickets": {"people": 1, "no_id_items": 0}})
        self.assertEqual(summary["people"], 4)
        self.assertEqual(summary["items_without_person_id"], 1)

    def test_severity_is_worst_per_person_and_ranking_needs_two_people(self):
        _, t, _, _ = self.counts(SHEET)
        # A reported S1/S2/S3 for login (worst S1), the no-ID item S2: two reach S2 or worse.
        self.assertEqual(t["login"]["severity_people"], {"S1": 1, "S2": 1})
        self.assertEqual(t["login"]["worst_severity"], "S1")
        self.assertEqual(t["login"]["ranking_severity"], "S2")

    def test_theme_code_severity_overrides_row_severity(self):
        _, t, _, _ = self.counts(SHEET)
        self.assertEqual(t["slow"]["severity_people"], {"S1": 1, "S2": 1, "S3": 1})

    def test_valued_theme_has_no_severity_and_ranks_last(self):
        _, t, order, _ = self.counts(SHEET)
        self.assertTrue(t["+fast-support"]["valued"])
        self.assertEqual(t["+fast-support"]["ranking_severity"], "")
        self.assertEqual(order, ["slow", "login", "+fast-support"])

    def test_severity_outranks_volume(self):
        sheet = ("item_id,person_id,themes,severity\n"
                 "1,P1,typo,S4\n2,P2,typo,S4\n3,P3,typo,S4\n4,P4,typo,S4\n"
                 "5,P5,payment,S1\n6,P6,payment,S1\n")
        _, _, order, _ = self.counts(sheet)
        self.assertEqual(order, ["payment", "typo"])

    def test_one_person_theme_is_marked_one_report(self):
        sheet = "item_id,person_id,themes,severity\n1,P1,crash,S1\n2,P1,crash,S2\n3,P2,other,\n4,P3,other,S1\n"
        _, t, _, _ = self.counts(sheet)
        self.assertEqual(t["crash"]["ranking_severity"], "S1 (1 report)")
        self.assertEqual(t["other"]["ranking_severity"], "S1 (1 rated)")

    def test_severity_aliases_and_unknown_severity_warns(self):
        sheet = "item_id,person_id,themes,severity\n1,P1,a,blocker\n2,P2,a,urgent\n"
        _, t, _, warnings = self.counts(sheet)
        self.assertEqual(t["a"]["severity_people"], {"S1": 1, "unrated": 1})
        self.assertTrue(any("unknown severity 'urgent'" in w for w in warnings))

    def test_theme_in_one_segment_value_is_flagged(self):
        sheet = ("item_id,person_id,themes,region\n"
                 "1,P1,export,EU\n2,P2,export,EU\n3,P3,other,US\n4,P4,other,US\n")
        _, t, _, _ = self.counts(sheet)
        self.assertEqual(t["export"]["single_segment"], ["region=EU (2 of 4 overall)"])

    def test_one_segment_flag_suppressed_when_value_is_most_of_sample(self):
        sheet = ("item_id,person_id,themes,region\n"
                 "1,P1,export,EU\n2,P2,export,EU\n3,P3,export,EU\n4,P4,other,US\n")
        _, t, _, _ = self.counts(sheet)
        self.assertEqual(t["export"]["single_segment"], [])

    def test_unthemed_items_and_most_items_per_person(self):
        summary, _, _, _ = self.counts(SHEET)
        self.assertEqual(summary["unthemed_items"], ["T7"])
        self.assertEqual(summary["most_items_per_person"], {"A": 3})

    def test_segment_conflict_keeps_first_value(self):
        sheet = "item_id,person_id,themes,plan\n1,P1,a,pro\n2,P1,b,free\n"
        summary, t, _, _ = self.counts(sheet)
        self.assertEqual(summary["segment_conflicts"], {"P1 plan": ["free", "pro"]})
        self.assertEqual(t["b"]["segments"]["plan"], {"pro": 1})

    def test_row_without_item_id_skipped_and_duplicate_id_warned(self):
        sheet = "item_id,person_id,themes\n,P1,a\n1,P2,a\n1,P3,a\n"
        summary, t, _, warnings = self.counts(sheet)
        self.assertEqual(summary["items"], 2)
        self.assertEqual(t["a"]["people"], 2)
        self.assertTrue(any("line 2: no item_id" in w for w in warnings))
        self.assertTrue(any("appears twice" in w for w in warnings))


class ThemeCountsCliTest(unittest.TestCase):
    def test_report_and_json_output(self):
        with workdir() as d:
            p = write(os.path.join(d, "coded.csv"), SHEET)
            out_md, out_json = os.path.join(d, "counts.md"), os.path.join(d, "counts.json")
            code, out, err = run(SKILL, SCRIPT, p, "-o", out_md, "--json", out_json)
            self.assertEqual(code, 0, err)
            report = read(out_md)
            data = json.loads(read(out_json))
        self.assertIn("- Items: 7; distinct people with an ID: 4", report)
        self.assertIn("| slow | 3 | 0 | 3 | S2 | S1 |", report)
        self.assertIn("| login | 1 | 1 | 4 | S2 | S1 |", report)
        self.assertIn("WARNING: A accounts for 75% of this theme's mentions", report)
        self.assertIn("## Items with no theme\nT7", report)
        self.assertEqual([t["theme"] for t in data["themes"]], ["slow", "login", "+fast-support"])

    def test_person_col_and_label(self):
        sheet = "item_id,account_id,themes\n1,ACME,a\n2,ACME,a\n3,GLOBEX,a\n"
        with workdir() as d:
            p = write(os.path.join(d, "coded.csv"), sheet)
            code, out, err = run(SKILL, SCRIPT, p, "--person-col", "account_id")
        self.assertEqual(code, 0, err)
        self.assertIn("distinct accounts with an ID: 2", out)
        self.assertIn("| Theme | Accounts |", out)

    def test_segment_and_ignore_flags(self):
        sheet = "item_id,person_id,themes,plan,region\n1,P1,a,pro,EU\n"
        with workdir() as d:
            p = write(os.path.join(d, "coded.csv"), sheet)
            _, only_plan, _ = run(SKILL, SCRIPT, p, "--segment", "plan")
            _, no_region, _ = run(SKILL, SCRIPT, p, "--ignore", "region")
            code, _, err = run(SKILL, SCRIPT, p, "--segment", "tenure")
        for out in (only_plan, no_region):
            self.assertIn("- plan: pro 1", out)
            self.assertNotIn("- region:", out)
        self.assertEqual(code, 2)
        self.assertIn("segment column 'tenure' is not in", err)

    def test_bad_inputs_exit_2_with_message(self):
        cases = [
            ("", "has no header row"),
            ("item_id,person_id\n1,P1\n", "needs a 'themes' column"),
            ("item_id,person_id,themes\n", "has no feedback rows"),
        ]
        with workdir() as d:
            for text, message in cases:
                p = write(os.path.join(d, "coded.csv"), text)
                code, _, err = run(SKILL, SCRIPT, p)
                self.assertEqual(code, 2, text)
                self.assertIn(message, err)
            code, _, err = run(SKILL, SCRIPT, p, "--person-col", "account_id")
            self.assertEqual(code, 2)
            self.assertIn("--person-col 'account_id' is not a column", err)
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.csv"))
            self.assertEqual(code, 2)
            self.assertIn("cannot read", err)
            self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

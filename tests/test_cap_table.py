import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "cap-table", "cap_table.py"

SIMPLE = {"holders": [{"name": "Founders", "shares": 8000000}],
          "options": {"granted": 0, "pool_unissued": 1000000},
          "safes": [{"holder": "Angel", "amount": 1000000, "type": "post", "cap": 10000000}],
          "round": {"pre_money": 20000000, "investors": [{"name": "Lead", "amount": 5000000}], "pool_target": 0.10}}


def rows(r):
    return {row["name"]: row for row in r["rows"]}


class CapTableMathTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def solve(self, data, **kw):
        return self.m.model(self.m.load(data), **kw)

    def test_post_money_safe_and_pool_shuffle_match_hand_calculation(self):
        r = self.solve(SIMPLE)
        # post-money 25M, lead 20 %, pool 10 % post, SAFE 1M shares at $1.00
        self.assertAlmostEqual(r["price"], 25e6 / (12857142.857), places=3)
        self.assertEqual(rows(r)["Angel"]["shares"], 1000000)
        self.assertAlmostEqual(rows(r)["Lead"]["pct"], 20.0, places=2)
        self.assertAlmostEqual(rows(r)["Option pool, unissued"]["pct"], 10.0, places=2)
        self.assertAlmostEqual(rows(r)["Founders"]["pct"], 62.22, places=2)
        self.assertEqual(r["fails"], [])

    def test_post_money_safe_holds_amount_over_cap_before_new_money(self):
        data = json.loads(json.dumps(SIMPLE))
        data["safes"].append({"holder": "Second", "amount": 500000, "type": "post", "cap": 5000000})
        r = self.solve(data)
        before = 9000000 + sum(c["shares"] for c in r["convs"])
        for c, share in zip(r["convs"], (0.10, 0.10)):
            self.assertAlmostEqual(c["shares"] / before, share, places=4)

    def test_pre_money_safe_divides_cap_by_shares_plus_top_up(self):
        data = json.loads(json.dumps(SIMPLE))
        data["safes"] = [{"holder": "Old", "amount": 500000, "type": "pre", "cap": 5000000}]
        r = self.solve(data)
        c = r["convs"][0]
        self.assertAlmostEqual(c["price"], 5000000 / (9000000 + r["pool_increase"]), places=4)

    def test_discount_wins_when_lower_than_cap_price(self):
        data = json.loads(json.dumps(SIMPLE))
        data["safes"] = [{"holder": "Disc", "amount": 200000, "type": "post", "cap": 100000000, "discount": 20}]
        r = self.solve(data)
        self.assertEqual(r["convs"][0]["by"], "discount")
        self.assertAlmostEqual(r["convs"][0]["price"], r["price"] * 0.8, places=6)

    def test_note_accrues_simple_interest_to_close(self):
        data = json.loads(json.dumps(SIMPLE))
        data["safes"] = []
        data["notes"] = [{"holder": "Note", "principal": 100000, "rate": 0.08, "issued": "2025-12-01", "cap": 4000000}]
        data["round"]["close"] = "2026-12-01"
        r = self.solve(data)
        self.assertAlmostEqual(r["convs"][0]["invested"], 108000, places=2)

    def test_note_without_dates_warns_and_converts_principal(self):
        data = json.loads(json.dumps(SIMPLE))
        data["notes"] = [{"holder": "Note", "principal": 100000, "rate": 0.08, "cap": 4000000}]
        r = self.solve(data)
        self.assertTrue(any("interest not counted" in w for w in r["warns"]))

    def test_pool_after_the_round_dilutes_new_investors_too(self):
        pre = self.solve(SIMPLE)
        data = json.loads(json.dumps(SIMPLE))
        data["round"]["pool_in"] = "post"
        post = self.solve(data)
        self.assertGreater(rows(post)["Founders"]["pct"], rows(pre)["Founders"]["pct"])
        self.assertLess(rows(post)["Lead"]["pct"], 20.0)
        self.assertEqual(post["fails"], [])

    def test_scenario_valuation_overrides_pre_money(self):
        r = self.solve(SIMPLE, pre_money=40000000)
        self.assertAlmostEqual(r["pre_money"], 40000000)
        self.assertGreater(rows(r)["Founders"]["pct"], 62.22)

    def test_stack_reports_amount_over_cap(self):
        self.assertAlmostEqual(self.m.stack(self.m.load(SIMPLE))[0][3], 0.10)

    def test_parse_scenarios(self):
        self.assertEqual(self.m.parse_scenarios("8m, 12.5M;20000000"), [8e6, 12.5e6, 2e7])
        with self.assertRaises(self.m.InputError):
            self.m.parse_scenarios("cheap")

    def test_bad_inputs_are_refused(self):
        for data in ({"holders": []}, {"holders": [{"name": "A", "shares": -1}]},
                     dict(SIMPLE, safes=[{"holder": "X", "amount": 1, "type": "weird"}]),
                     dict(SIMPLE, safes=[{"holder": "X", "amount": 1, "discount": 100}])):
            with self.assertRaises(self.m.InputError):
                self.m.load(data)


class CapTableCliTest(unittest.TestCase):
    def test_report_csv_and_scenarios(self):
        with workdir() as d:
            f = write(os.path.join(d, "cap.json"), json.dumps(SIMPLE))
            out = os.path.join(d, "after.csv")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--csv", out, "--scenarios", "15m,25m")
            self.assertEqual(code, 0)
            self.assertIn("| Founders | common | 8,000,000 | 62.22 |", stdout)
            self.assertIn("## At other pre-money valuations", stdout)
            self.assertIn("Founders,common,8000000,62.2222", read(out))

    def test_no_round_shows_today_and_the_safe_stack(self):
        data = dict(SIMPLE)
        data.pop("round")
        with workdir() as d:
            f = write(os.path.join(d, "cap.json"), json.dumps(data))
            code, stdout, _ = run(SKILL, SCRIPT, f)
            self.assertEqual(code, 0)
            self.assertIn("Angel: $1,000,000 ÷ $10,000,000 = 10.00 %", stdout)
            self.assertIn("No priced round given", stdout)

    def test_template_runs_clean(self):
        import catalog
        path = os.path.join(catalog.skill_dir(SKILL), "templates", "cap.json")
        code, stdout, _ = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 0)
        self.assertNotIn("FAIL", stdout)

    def test_bad_input_exits_2(self):
        with workdir() as d:
            f = write(os.path.join(d, "cap.json"), "{")
            self.assertEqual(run(SKILL, SCRIPT, f)[0], 2)


if __name__ == "__main__":
    unittest.main()

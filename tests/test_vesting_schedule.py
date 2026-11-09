import datetime as dt
import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "vesting-schedule", "vesting.py"


def grant(**kw):
    g = {"holder": "A", "type": "option", "shares": 48000, "grant_date": "2026-01-15", "vesting_start": "2026-01-15",
         "months": 48, "cliff_months": 12, "frequency": "monthly"}
    g.update(kw)
    return g


class VestingTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def result(self, as_of="2027-06-30", coc=None, **kw):
        cap = self.m.load({"grants": [grant(**kw)], "change_of_control": coc})
        return self.m.outcome(cap, cap["grants"][0], dt.date.fromisoformat(as_of))

    def test_cliff_then_monthly_sums_exactly(self):
        r = self.result()
        self.assertEqual(r["rows"][0], (dt.date(2027, 1, 15), 12000, 12000))
        self.assertEqual(len(r["rows"]), 37)
        self.assertEqual(r["rows"][-1][2], 48000)
        self.assertEqual(r["vested"], 17000)           # 17 of 48 months
        self.assertEqual(r["fails"], [])

    def test_rounding_never_overshoots(self):
        r = self.result(shares=1001)
        cums = [c for _, _, c in r["rows"]]
        self.assertEqual(cums, sorted(cums))
        self.assertEqual(sum(n for _, n, _ in r["rows"]), 1001)
        self.assertTrue(all(c <= 1001 * k / 48 + 1e-9 for k, c in zip(range(12, 49), cums)))

    def test_month_end_start_and_leap_year(self):
        r = self.result(vesting_start="2027-01-31", grant_date="2027-01-31", cliff_months=0, months=24)
        dates = [d for d, _, _ in r["rows"]]
        self.assertIn(dt.date(2027, 2, 28), dates)
        self.assertIn(dt.date(2028, 2, 29), dates)
        self.assertIn(dt.date(2027, 3, 31), dates)
        self.assertTrue(any("31st" in n for n in r["notes"]))

    def test_cliff_between_quarterly_dates_vests_on_the_cliff(self):
        r = self.result(frequency="quarterly", cliff_months=4, months=12, shares=1200)
        self.assertEqual(r["rows"][0], (dt.date(2026, 5, 15), 400, 400))
        self.assertEqual(r["rows"][1], (dt.date(2026, 7, 15), 200, 600))

    def test_leaver_uses_leaving_date_and_option_window(self):
        r = self.result(as_of="2027-01-01", leave_date="2027-08-20")
        self.assertIn("19,000 vested, 29,000 forfeited", r["leave"])     # Jan–Jul 2027: 19 months
        self.assertIn("2027-11-18 (90 days)", r["leave"])
        self.assertTrue(any("assumed 90 days" in w for w in r["warns"]))

    def test_stock_leaver_is_repurchasable(self):
        r = self.result(type="founder stock", leave_date="2027-02-01", filed_83b=True)
        self.assertIn("unvested shares the company can buy back", r["leave"])
        self.assertTrue(any("buy-back window isn't given" in w for w in r["warns"]))
        r = self.result(type="founder stock", leave_date="2027-02-01", filed_83b=True, repurchase_window_days=90)
        self.assertIn("must exercise the buy-back by 2027-05-02 (90 days)", r["leave"])

    def test_83b_deadline_moves_past_holiday_and_passed_fails(self):
        r = self.result(type="restricted stock", grant_date="2026-06-04", vesting_start="2026-06-04", as_of="2026-06-10")
        self.assertEqual(r["election"]["deadline"], dt.date(2026, 7, 6))   # 4 July is a Saturday; Mon 6th
        self.assertEqual(r["fails"], [])
        r = self.result(type="restricted stock", as_of="2026-03-01")
        self.assertTrue(any("83(b) deadline was 2026-02-17" in f for f in r["fails"]))  # 14 Feb + Presidents' Day
        self.assertIsNone(self.result()["election"])

    def test_single_and_double_trigger(self):
        r = self.result(acceleration={"single": 0.5}, coc="2027-01-15")
        self.assertEqual(r["vested"], 12000 + 18000 + 5000)   # cliff, half the 36,000 unvested, then 5 more months
        r = self.result(acceleration={"double": 1.0, "window_months": 12}, coc="2027-03-01", leave_date="2027-06-01")
        self.assertEqual(r["vested"], 48000)
        before_leaving = self.result(acceleration={"double": 1.0, "window_months": 12}, coc="2027-03-01",
                                     leave_date="2027-06-01", as_of="2027-04-01")
        self.assertEqual(before_leaving["vested"], 14000)     # 14 months; the second trigger hasn't happened yet
        r = self.result(acceleration={"double": 1.0}, coc="2027-03-01")
        self.assertTrue(any("applies only if they are let go" in n for n in r["notes"]))

    def test_bad_inputs(self):
        for g in (grant(shares=0), grant(cliff_months=60), grant(frequency="weekly"), grant(acceleration={"single": 200})):
            with self.assertRaises(self.m.InputError):
                self.m.load({"grants": [g]})


class VestingCliTest(unittest.TestCase):
    def test_report_and_csv(self):
        with workdir() as d:
            f = write(os.path.join(d, "v.json"), json.dumps({"grants": [grant()]}))
            out = os.path.join(d, "s.csv")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--as-of", "2027-06-30", "--csv", out)
            self.assertEqual(code, 0)
            self.assertIn("| A | option | 48,000 | 2027-01-15: 12,000 | 2030-01-15 | 17,000 (2027-06-30) | 31,000 |", stdout)
            self.assertEqual(len(read(out).splitlines()), 38)

    def test_template_and_bad_input(self):
        import catalog
        path = os.path.join(catalog.skill_dir(SKILL), "templates", "vesting.json")
        code, out, _ = run(SKILL, SCRIPT, path, "--as-of", "2026-02-15")
        self.assertEqual(code, 0)
        with workdir() as d:
            self.assertEqual(run(SKILL, SCRIPT, write(os.path.join(d, "v.json"), "{}"))[0], 2)


if __name__ == "__main__":
    unittest.main()

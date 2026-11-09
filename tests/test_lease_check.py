import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "lease-check", "lease_terms.py"

TERMS = {"currency": "GBP", "start": "2027-01-01", "term_months": 60,
         "rent": {"annual": 36000, "rent_free_months": 3,
                  "reviews": [{"month": 36, "type": "cpi", "assumed": 0.04, "cap": 0.04, "collar": 0.01, "years": 3}]},
         "service_charge": {"annual": 4800}, "deposit": {"months": 6},
         "breaks": [{"month": 36, "notice_months": 6, "party": "tenant", "conditions": ["all rent paid"]}],
         "notice_to_leave_months": 6}


def terms(**kw):
    t = json.loads(json.dumps(TERMS))
    t.update(kw)
    return t


class LeaseTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def analyse(self, t=None, as_of=None):
        import datetime as dt
        return self.m.analyse(self.m.load(t or TERMS), dt.date.fromisoformat(as_of) if as_of else None)

    def test_commitments_and_deadlines(self):
        r = self.analyse()
        brk, end = r["commitments"]
        self.assertAlmostEqual(brk[1], 99000)          # 33 paid months at 3,000
        self.assertAlmostEqual(brk[2], 14400)
        self.assertAlmostEqual(end[1], 99000 + 24 * 36000 * 1.04 ** 3 / 12, places=0)
        dl = {w: str(d) for w, d, _ in r["deadlines"]}
        self.assertEqual(dl["tenant break notice"], "2029-07-01")
        self.assertEqual(dl["notice to leave at the end"], "2031-06-30")
        self.assertEqual(str(r["end"]), "2031-12-31")
        self.assertAlmostEqual(r["deposit"], 18000)

    def test_cap_and_collar_and_upward_only(self):
        t = terms(rent={"annual": 10000, "reviews": [{"month": 12, "type": "cpi", "assumed": 0.10, "cap": 0.05}]})
        self.assertAlmostEqual(self.m.rent_by_month(self.m.load(t))[0][12], 10500)
        t = terms(rent={"annual": 10000, "reviews": [{"month": 12, "type": "cpi", "assumed": -0.02, "collar": 0.01}]})
        self.assertAlmostEqual(self.m.rent_by_month(self.m.load(t))[0][12], 10100)
        t = terms(rent={"annual": 10000, "reviews": [{"month": 12, "type": "fixed", "increase": -0.05}]})
        self.assertAlmostEqual(self.m.rent_by_month(self.m.load(t))[0][12], 10000)

    def test_stepped_rent_and_open_market_unknown(self):
        t = terms(rent={"annual": 12000, "stepped": [{"from_month": 12, "annual": 24000}],
                        "reviews": [{"month": 24, "type": "open market"}]})
        rates, notes = self.m.rent_by_month(self.m.load(t))
        self.assertEqual((rates[11], rates[12], rates[24]), (12000, 24000, None))
        self.assertTrue(notes)
        r = self.analyse(t)
        self.assertTrue(r["commitments"][-1][3])     # unknown flagged

    def test_contradictions_and_passed_deadlines(self):
        t = terms(breaks=[{"month": 72, "notice_months": 6}], rent={"annual": 1, "rent_free_months": 60})
        fails = self.analyse(t)["fails"]
        self.assertTrue(any("after the lease ends" in f for f in fails))
        self.assertTrue(any("rent-free period is as long as the term" in f for f in fails))
        fails = self.analyse(as_of="2029-08-01")["fails"]
        self.assertTrue(any("tenant break notice deadline (2029-07-01) has already passed" in f for f in fails))

    def test_conditional_and_landlord_breaks_warn(self):
        t = terms(breaks=[{"month": 24, "notice_months": 6, "party": "landlord", "conditions": ["vacant possession"]}])
        warns = self.analyse(t)["warns"]
        self.assertTrue(any("landlord can end the lease" in w for w in warns))
        self.assertTrue(any("is conditional" in w for w in warns))

    def test_break_on_the_leases_own_date(self):
        t = terms(start="2027-03-01", breaks=[{"date": "2030-02-28", "notice_months": 6}])
        r = self.analyse(t)
        dl = {w: str(d) for w, d, _ in r["deadlines"]}
        self.assertEqual(dl["tenant break notice"], "2029-08-28")
        self.assertEqual(str(r["end"]), "2032-02-29")

    def test_bad_inputs(self):
        for t in (terms(term_months=0), terms(rent={}), terms(start="soon"), terms(breaks=[{"notice_months": 6}]),
                  terms(rent={"annual": 1, "reviews": [{"month": 12, "type": "guess"}]})):
            with self.assertRaises(self.m.InputError):
                self.m.load(t)


class LeaseCliTest(unittest.TestCase):
    def test_report(self):
        with workdir() as d:
            f = write(os.path.join(d, "t.json"), json.dumps(TERMS))
            code, out, _ = run(SKILL, SCRIPT, f, "--as-of", "2026-11-08")
            self.assertEqual(code, 0)
            self.assertIn("| to the break on 2030-01-01 | £99,000 | £14,400 | £113,400 |", out)
            self.assertIn("| 4 | 2030-01-01 | £40,495 | £40,495 |", out)
            self.assertEqual(run(SKILL, SCRIPT, f, "--as-of", "2030-01-02")[0], 1)
            self.assertEqual(run(SKILL, SCRIPT, write(os.path.join(d, "b.json"), "[]"))[0], 2)


if __name__ == "__main__":
    unittest.main()

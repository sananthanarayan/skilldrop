import contextlib
import io
import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "lean-canvas", "unit_economics.py"


class UnitEconomicsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def compute(self, **inp):
        lines, flags = self.m.compute(inp)
        return "\n".join(lines), "\n".join(flags)

    def assertExits2(self, **inp):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as cm:
                self.m.compute(inp)
        self.assertEqual(cm.exception.code, 2)
        return err.getvalue()

    def test_skill_md_example_payback_outruns_lifetime(self):
        lines, flags = self.compute(price=12, variable_cost=7, cac=90, lifetime=6, fixed=6000)
        self.assertIn("Contribution per customer per month: 5.00 (41.7% gross margin)", lines)
        self.assertIn("Lifetime contribution (LTV): 30.00", lines)
        self.assertIn("CAC payback: 18.0 months", lines)
        self.assertIn("LTV:CAC: 0.33", lines)
        self.assertIn("Most a customer can cost to acquire: 30.00 at break-even, 10.00 at 3:1", lines)
        self.assertIn("Break-even customers (active at once): 1,200", lines)
        self.assertIn("every acquired customer loses 60.00", flags)
        self.assertIn("acquisition destroys money", flags)
        self.assertIn("cannot be reached through paid acquisition", flags)

    def test_lifetime_derived_from_churn_fraction(self):
        lines, flags = self.compute(price=29, variable_cost=6, cac=400, churn=0.11)
        self.assertIn("Customer lifetime: 9.1 months (1 / churn of 11.0%)", lines)
        self.assertIn("Lifetime contribution (LTV): 209.09", lines)
        self.assertIn("CAC payback: 17.4 months", lines)
        self.assertIn("LTV:CAC: 0.52", lines)

    def test_churn_given_as_percent_is_converted(self):
        lines, _ = self.compute(price=29, variable_cost=6, churn=11)
        self.assertIn("1 / churn of 11.0%", lines)

    def test_given_lifetime_wins_over_churn(self):
        lines, _ = self.compute(price=29, variable_cost=6, lifetime=12, churn=0.5)
        self.assertIn("Customer lifetime: 12.0 months (as given)", lines)

    def test_healthy_business_has_no_flags(self):
        lines, flags = self.compute(price=100, variable_cost=20, cac=120, lifetime=10,
                                    fixed=8000, market_customers=1000)
        self.assertIn("CAC payback: 1.5 months", lines)
        self.assertIn("LTV:CAC: 6.67", lines)
        self.assertIn("Break-even customers (active at once): 100", lines)
        self.assertIn("Break-even share of the stated market: 10.0%", lines)
        self.assertEqual(flags, "")

    def test_ltv_cac_between_one_and_three_is_flagged(self):
        _, flags = self.compute(price=100, variable_cost=20, cac=400, lifetime=10)
        self.assertIn("LTV:CAC is 2.00, under the 3:1", flags)

    def test_break_even_rounds_up_to_whole_customers(self):
        lines, _ = self.compute(price=40, variable_cost=10, fixed=1000)
        self.assertIn("Break-even customers (active at once): 34", lines)

    def test_break_even_larger_than_market_is_flagged(self):
        _, flags = self.compute(price=100, variable_cost=20, fixed=8000, market_customers=50)
        self.assertIn("Break-even needs 100 active customers but the stated market holds 50", flags)

    def test_break_even_quarter_of_market_is_flagged(self):
        _, flags = self.compute(price=100, variable_cost=20, fixed=8000, market_customers=300)
        self.assertIn("Break-even needs 33% of the stated market", flags)

    def test_negative_margin_is_flagged(self):
        _, flags = self.compute(price=10, variable_cost=15)
        self.assertIn("costs more to serve than they pay (-5.00 per month)", flags)

    def test_missing_variable_cost_is_an_upper_bound(self):
        lines, flags = self.compute(price=10)
        self.assertIn("not given, treated as 0", lines)
        self.assertIn("upper bound", flags)
        self.assertIn("Not computed (input missing): variable_cost, cac, lifetime/churn, fixed", lines)

    def test_period_label_is_used(self):
        lines, _ = self.compute(price=1200, variable_cost=200, lifetime=3, period="year")
        self.assertIn("Customer lifetime: 3.0 years", lines)

    def test_price_is_required_and_positive(self):
        self.assertIn("price is required", self.assertExits2(variable_cost=1))
        self.assertIn("price must be > 0", self.assertExits2(price=0))

    def test_negative_or_non_numeric_inputs_exit_2(self):
        self.assertIn("cac must be >= 0", self.assertExits2(price=10, cac=-1))
        self.assertIn("fixed must be a number", self.assertExits2(price=10, fixed="lots"))

    def test_churn_out_of_range_exits_2(self):
        self.assertIn("churn must be a fraction", self.assertExits2(price=10, churn=150))
        self.assertIn("churn must be > 0", self.assertExits2(price=10, churn=0))

    def test_zero_market_with_zero_fixed_costs_does_not_crash(self):
        self.compute(price=10, variable_cost=2, fixed=0, market_customers=0)


class UnitEconomicsCliTest(unittest.TestCase):
    def test_flags_produce_report_with_flags_section(self):
        code, out, err = run(SKILL, SCRIPT, "--price", "12", "--variable-cost", "7",
                             "--cac", "90", "--lifetime", "6", "--fixed", "6000")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("Unit economics"))
        self.assertIn("Where the numbers don't close:\n- ", out)

    def test_no_flags_says_none_found(self):
        code, out, _ = run(SKILL, SCRIPT, "--price", "100", "--variable-cost", "20",
                           "--cac", "120", "--lifetime", "10")
        self.assertEqual(code, 0)
        self.assertIn("Where the numbers don't close: none found.", out)

    def test_json_from_stdin_with_flag_override_and_output_file(self):
        inp = json.dumps({"price": 29, "variable_cost": 6, "cac": 400, "lifetime": 9})
        with workdir() as d:
            target = os.path.join(d, "out.md")
            code, out, err = run(SKILL, SCRIPT, "--json", "-", "--lifetime", "20",
                                 "-o", target, stdin=inp)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")
            text = read(target)
        self.assertIn("Customer lifetime: 20.0 months (as given)", text)
        self.assertIn("Lifetime contribution (LTV): 460.00", text)

    def test_json_file_input(self):
        with workdir() as d:
            p = write(os.path.join(d, "in.json"), '{"price": 50, "variable_cost": 10, "fixed": 400}')
            code, out, _ = run(SKILL, SCRIPT, "--json", p)
        self.assertEqual(code, 0)
        self.assertIn("Break-even customers (active at once): 10", out)

    def test_unknown_json_key_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "--json", "-", stdin='{"price": 10, "prise": 11}')
        self.assertEqual(code, 2)
        self.assertIn("unknown JSON keys: prise", err)

    def test_malformed_json_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "--json", "-", stdin="{price: 10")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)
        code, _, err = run(SKILL, SCRIPT, "--json", "-", stdin="[1, 2]")
        self.assertEqual(code, 2)
        self.assertIn("one object", err)

    def test_missing_json_file_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, "--json", os.path.join(d, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_missing_price_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "--cac", "10")
        self.assertEqual(code, 2)
        self.assertIn("price is required", err)


if __name__ == "__main__":
    unittest.main()

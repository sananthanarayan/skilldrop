import contextlib
import io
import json
import unittest

from tests.support import load, run

SKILL, SCRIPT = "rollout-plan", "canary_math.py"
BASE = ("--baseline", "1%", "--detect-abs", "1pp", "--traffic", "1000")


def report(*args):
    code, out, err = run(SKILL, SCRIPT, *args, "--json")
    if code != 0:
        raise AssertionError("exit {}: {}".format(code, err))
    return json.loads(out)


class CanaryMathFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)
        self.za, self.zb = self.m.z_values(0.05, 0.8, False)

    def test_z_values_two_sided_and_one_sided(self):
        self.assertAlmostEqual(self.za, 1.959964, places=5)
        self.assertAlmostEqual(self.zb, 0.841621, places=5)
        self.assertAlmostEqual(self.m.z_values(0.05, 0.8, True)[0], 1.644854, places=5)

    def test_equal_arm_n_for_1_to_2_percent(self):
        # (1.96*sqrt(2*.015*.985) + 0.8416*sqrt(.0099+.0196))^2 / .01^2 = 2318.2 -> 2319
        self.assertEqual(self.m.equal_arm_n(0.01, 0.02, self.za, self.zb), 2319)

    def test_hours_at_50_50_equal_two_equal_arms_over_traffic(self):
        h = self.m.hours_needed(0.01, 0.02, 0.5, 0.5, 1000, self.za, self.zb)
        self.assertAlmostEqual(h, 4.636, places=3)
        self.assertAlmostEqual(h * 1000 * 0.5, 2318.2, places=0)

    def test_hours_shrink_as_exposure_grows_towards_half(self):
        hs = [self.m.hours_needed(0.01, 0.02, e, 1 - e, 1000, self.za, self.zb) for e in (0.01, 0.05, 0.25, 0.5)]
        self.assertEqual(hs, sorted(hs, reverse=True))

    def test_hours_none_without_a_treatment_or_control_arm(self):
        self.assertIsNone(self.m.hours_needed(0.01, 0.02, 1.0, 0.0, 1000, self.za, self.zb))
        self.assertIsNone(self.m.hours_needed(0.01, 0.02, 0.0, 1.0, 1000, self.za, self.zb))

    def test_detectable_in_is_the_regression_that_just_fits_the_window(self):
        mde = self.m.detectable_in(0.01, "up", 0.01, 0.99, 1000, self.za, self.zb, 72)
        self.assertGreater(mde, 0.01)
        h = self.m.hours_needed(0.01, 0.01 + mde, 0.01, 0.99, 1000, self.za, self.zb)
        self.assertAlmostEqual(h, 72, places=3)

    def test_detectable_in_none_when_nothing_is_measurable(self):
        self.assertIsNone(self.m.detectable_in(0.01, "up", 0.001, 0.999, 1, self.za, self.zb, 1))

    def test_smallest_sufficient_exposure_is_the_first_step_inside_the_window(self):
        e, h = self.m.smallest_sufficient_exposure(0.01, 0.02, 1000, self.za, self.zb, 72, None)
        self.assertAlmostEqual(e, 0.014)
        self.assertLessEqual(h, 72)
        before = self.m.hours_needed(0.01, 0.02, 0.013, 0.987, 1000, self.za, self.zb)
        self.assertGreater(before, 72)

    def test_parse_rate_accepts_fraction_percent_and_points(self):
        self.assertAlmostEqual(self.m.parse_rate("0.008", "x"), 0.008)
        self.assertAlmostEqual(self.m.parse_rate("0.8%", "x"), 0.008)
        self.assertAlmostEqual(self.m.parse_rate("0.3 PP", "x", allow_pp=True), 0.003)
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(err):
            self.m.parse_rate("0.3pp", "--baseline")
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("'pp' only applies to --detect-abs", err.getvalue())

    def test_fmt_hours_switches_units(self):
        self.assertEqual(self.m.fmt_hours(None), "n/a")
        self.assertEqual(self.m.fmt_hours(0.5), "30 min")
        self.assertEqual(self.m.fmt_hours(5), "5.0 h")
        self.assertEqual(self.m.fmt_hours(72), "72.0 h (3.0 d)")


class CanaryMathCliTest(unittest.TestCase):
    def test_json_rows_cover_each_step_and_status(self):
        rep = report(*BASE, "--steps", "1,50,100")
        self.assertEqual(rep["equal_arm_units_per_arm"], 2319)
        one, half, full = rep["steps"]
        self.assertEqual(one["status"], "insufficient")
        self.assertAlmostEqual(one["hours"], 99.28, places=1)
        self.assertGreater(one["detectable_in_max_hours_abs"], 0.01)
        self.assertEqual(half["status"], "sufficient")
        self.assertAlmostEqual(half["hours"], 4.636, places=3)
        self.assertEqual((half["treatment_units"], half["control_units"]), (2319, 2319))
        self.assertEqual(full["status"], "no-control")
        self.assertIsNone(full["hours"])
        self.assertEqual(rep["smallest_sufficient_exposure_pct"], 1.4)

    def test_default_ladder_has_five_steps(self):
        rep = report(*BASE)
        self.assertEqual([s["exposure_pct"] for s in rep["steps"]], [1, 5, 25, 50, 100])

    def test_detect_rel_is_relative_to_baseline_and_direction_down(self):
        rep = report("--baseline", "3.1%", "--detect-rel", "10%", "--direction", "down", "--traffic", "9000")
        self.assertAlmostEqual(rep["regression_abs"], 0.0031)
        self.assertAlmostEqual(rep["regressed_rate"], 0.0279)
        self.assertEqual(rep["direction"], "down")

    def test_up_and_down_need_the_same_time_around_50_percent(self):
        up = report("--baseline", "50%", "--detect-abs", "5pp", "--traffic", "100", "--steps", "10")
        down = report("--baseline", "50%", "--detect-abs", "5pp", "--traffic", "100", "--steps", "10",
                      "--direction", "down")
        self.assertAlmostEqual(up["steps"][0]["hours"], down["steps"][0]["hours"], places=3)

    def test_one_sided_test_needs_less_time(self):
        two = report(*BASE, "--steps", "5")
        one = report(*BASE, "--steps", "5", "--one-sided")
        self.assertEqual(one["test"], "one-sided")
        self.assertLess(one["steps"][0]["hours"], two["steps"][0]["hours"])

    def test_max_hours_moves_a_step_between_sufficient_and_insufficient(self):
        rep = report(*BASE, "--steps", "50", "--max-hours", "4")
        self.assertEqual(rep["steps"][0]["status"], "insufficient")
        rep = report(*BASE, "--steps", "50", "--max-hours", "5")
        self.assertEqual(rep["steps"][0]["status"], "sufficient")

    def test_fixed_holdback_is_used_and_overlap_is_invalid(self):
        rep = report(*BASE, "--steps", "10,50", "--control-pct", "60")
        ten, fifty = rep["steps"]
        self.assertEqual(ten["control_pct"], 60)
        self.assertIn(ten["status"], ("sufficient", "insufficient"))
        self.assertEqual(fifty["status"], "invalid")
        self.assertEqual(fifty["note"], "exposure plus control exceeds 100%")

    def test_markdown_table_names_the_unit_and_flags_insufficient_steps(self):
        code, out, _ = run(SKILL, SCRIPT, *BASE, "--steps", "1,50,100", "--unit", "users")
        self.assertEqual(code, 0)
        self.assertIn("| Exposure | Control | Treatment users needed | Control users needed |", out)
        self.assertIn("INSUFFICIENT: over 72 h; in 72 h it can only catch >= ", out)
        self.assertIn("no concurrent control at 100%", out)
        self.assertIn("Smallest exposure that reaches sufficiency within 72 h: 1.4%", out)

    def test_says_when_no_exposure_up_to_50_percent_is_enough(self):
        code, out, _ = run(SKILL, SCRIPT, "--baseline", "1%", "--detect-abs", "0.01pp", "--traffic", "10",
                           "--steps", "50")
        self.assertEqual(code, 0)
        self.assertIn("No exposure up to 50% reaches sufficiency within 72 h", out)

    def test_bad_input_exits_2_with_a_message(self):
        cases = {
            "baseline zero": (["--baseline", "0", "--detect-abs", "1pp", "--traffic", "10"], "--baseline"),
            "baseline text": (["--baseline", "lots", "--detect-abs", "1pp", "--traffic", "10"], "not a number"),
            "pp on rel": (["--baseline", "1%", "--detect-rel", "1pp", "--traffic", "10"], "'pp' only applies"),
            "zero regression": (["--baseline", "1%", "--detect-abs", "0", "--traffic", "10"], "greater than zero"),
            "below 0%": (["--baseline", "1%", "--detect-abs", "2pp", "--direction", "down", "--traffic", "10"],
                         "outside 0-100%"),
            "traffic": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "0"], "--traffic"),
            "alpha": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "10", "--alpha", "1.5"], "--alpha"),
            "max hours": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "10", "--max-hours", "0"],
                          "--max-hours"),
            "control": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "10", "--control-pct", "0"],
                        "--control-pct"),
            "step text": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "10", "--steps", "1,x"],
                          "--steps"),
            "step range": (["--baseline", "1%", "--detect-abs", "1pp", "--traffic", "10", "--steps", "0,150"],
                           "--steps"),
            "no regression flag": (["--baseline", "1%", "--traffic", "10"], "required"),
        }
        for name, (args, fragment) in cases.items():
            with self.subTest(name):
                code, out, err = run(SKILL, SCRIPT, *args)
                self.assertEqual(code, 2)
                self.assertIn(fragment, err)
                self.assertNotIn("Traceback", err)

    # BUG: a non-finite --traffic passes the "> 0" check and crashes in math.ceil with a traceback.
    @unittest.expectedFailure
    def test_non_finite_traffic_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "--baseline", "1%", "--detect-abs", "1pp", "--traffic", "nan")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "slo-spec", "slo_math.py"
m = load(SKILL, SCRIPT)


def compute(target=99.9, window=30, rpd=1000000, alerts="standard", deps=(), min_events=10.0,
            outages=None):
    return m.compute("svc", target, window, rpd, alerts, list(deps), min_events, outages)


class SloMathComputeTests(unittest.TestCase):
    def test_budget_999_over_30_days_is_43_2_minutes_and_30000_requests(self):
        r = compute()
        self.assertAlmostEqual(r["budget_minutes_full_outage"], 43.2)
        self.assertAlmostEqual(r["budget_bad_requests"], 30000)
        self.assertAlmostEqual(r["requests_in_window"], 30000000)
        self.assertAlmostEqual(r["budget_pct"], 0.1)

    def test_target_accepts_percent_sign_and_fraction(self):
        self.assertAlmostEqual(m.parse_target("99.9%"), 0.999)
        self.assertAlmostEqual(m.parse_target(0.999), 0.999)
        self.assertAlmostEqual(m.parse_target("99.95"), 0.9995)

    def test_target_100_percent_rejected(self):
        for bad in ("100", "100%", 1.0):
            with self.assertRaises(m.InputError):
                m.parse_target(bad)

    def test_target_non_numeric_zero_and_nan_rejected(self):
        for bad in ("abc", "0", "nan", "inf"):
            with self.assertRaises(m.InputError):
                m.parse_target(bad)

    def test_standard_alert_rows_trip_rate_budget_at_fire_and_exhaustion(self):
        rows = compute()["alerts"]
        self.assertEqual([(a["burn_rate"], a["long_window"], a["short_window"], a["severity"])
                          for a in rows],
                         [(14.4, "1h", "5m", "page"), (6.0, "6h", "30m", "page"),
                          (1.0, "3d", "6h", "ticket")])
        self.assertEqual([a["error_rate_threshold_pct"] for a in rows], [1.44, 0.6, 0.1])
        self.assertEqual([a["budget_consumed_at_fire_pct"] for a in rows], [2.0, 5.0, 10.0])
        self.assertEqual([a["hours_to_exhaustion"] for a in rows], [50.0, 120.0, 720.0])

    def test_expected_bad_events_per_window_at_1m_per_day(self):
        page = compute()["alerts"][0]
        # 1,000,000/day = 41,666.67/h; 1.44% of that over 1 h and 5 m
        self.assertAlmostEqual(page["expected_bad_long"], 600.0)
        self.assertAlmostEqual(page["expected_bad_short"], 50.0)
        self.assertEqual(page["noisy"], [])

    def test_28_day_window_changes_budget_consumed_not_burn_rate(self):
        r = compute(window=28)
        self.assertAlmostEqual(r["budget_minutes_full_outage"], 40.32)
        page = r["alerts"][0]
        self.assertEqual(page["burn_rate"], 14.4)
        self.assertEqual(page["budget_consumed_at_fire_pct"], 2.1429)  # 14.4 / 672 h

    def test_low_traffic_800_per_day_flags_page_alert_as_noisy(self):
        r = compute(rpd=800)
        page = r["alerts"][0]
        self.assertAlmostEqual(page["expected_bad_long"], 0.48)
        self.assertIn("long", page["noisy"])
        self.assertTrue(any("too noisy to alert on" in f and "14.4x 1h/5m" in f
                            for f in r["flags"]))

    def test_whole_window_budget_under_min_events_is_flagged(self):
        r = compute(rpd=100)  # 0.1% of 3,000 requests = 3
        self.assertAlmostEqual(r["budget_bad_requests"], 3)
        self.assertTrue(any("budget is 3 bad requests" in f for f in r["flags"]))

    def test_short_window_only_noisy_gets_flap_flag(self):
        r = compute(rpd=24000)  # 1,000/h: 14.4 bad in 1 h, 1.2 in 5 m
        page = r["alerts"][0]
        self.assertEqual(page["noisy"], ["short"])
        self.assertTrue(any("short window will flap" in f for f in r["flags"]))

    def test_min_events_threshold_changes_noise_verdict(self):
        self.assertEqual(compute(rpd=24000, min_events=1.0)["alerts"][0]["noisy"], [])

    def test_no_traffic_leaves_budget_in_minutes_only(self):
        r = compute(rpd=None)
        self.assertIsNone(r["budget_bad_requests"])
        self.assertIsNone(r["alerts"][0]["expected_bad_long"])
        self.assertTrue(any("No traffic given" in f for f in r["flags"]))

    def test_alert_threshold_above_100_percent_can_never_fire(self):
        r = compute(target=99, alerts="150:1h:5m:page")
        self.assertFalse(r["alerts"][0]["can_fire"])
        self.assertTrue(any("can never fire" in f for f in r["flags"]))

    def test_long_window_longer_than_slo_window_flagged(self):
        r = compute(window=1)
        self.assertTrue(any("1x 3d/6h" in f and "longer than the 1-day SLO window" in f
                            for f in r["flags"]))

    def test_dependency_at_same_order_spends_half_the_budget(self):
        r = compute(deps=[99.95])
        d = r["dependencies"]
        self.assertAlmostEqual(d["serial_ceiling_pct"], 99.95)
        self.assertEqual(d["budget_used_by_dependencies_pct"], 50.0)
        self.assertTrue(d["achievable_without_redundancy"])
        self.assertTrue(any("leaving 50%" in f for f in r["flags"]))

    def test_four_nines_on_three_nines_dependency_not_achievable(self):
        r = compute(target=99.99, deps=[99.9])
        d = r["dependencies"]
        self.assertFalse(d["achievable_without_redundancy"])
        self.assertEqual(d["budget_used_by_dependencies_pct"], 1000.0)
        self.assertTrue(any("Not achievable without redundancy" in f for f in r["flags"]))

    def test_dependencies_multiply_in_series(self):
        r = compute(target=99.5, deps=[99.9, 99.9])
        self.assertAlmostEqual(r["dependencies"]["serial_ceiling_pct"], 99.8001)
        self.assertTrue(r["dependencies"]["achievable_without_redundancy"])

    def test_outage_priced_against_budget(self):
        r = compute(outages=[40, 50])
        self.assertEqual([o["budget_spent_pct"] for o in r["outages"]], [92.59, 115.74])
        self.assertTrue(any("50-minute full outage spends 116%" in f for f in r["flags"]))
        self.assertFalse(any("40-minute" in f for f in r["flags"]))

    def test_custom_alert_default_severity_is_page(self):
        rows = m.parse_alerts("2x:12h:1h")
        self.assertEqual(rows[0]["burn"], 2.0)
        self.assertEqual(rows[0]["severity"], "page")
        self.assertEqual(rows[0]["long_hours"], 12.0)

    def test_malformed_alert_specs_rejected(self):
        for bad in ("14.4:1h", "x:1h:5m", "0:1h:5m", "14.4:5m:1h", "14.4:1y:5m", ",,"):
            with self.assertRaises(m.InputError, msg=bad):
                m.parse_alerts(bad)

    def test_duration_units(self):
        self.assertAlmostEqual(m.parse_duration_hours("30m"), 0.5)
        self.assertAlmostEqual(m.parse_duration_hours("3d"), 72.0)
        self.assertAlmostEqual(m.parse_duration_hours("1w"), 168.0)

    def test_human_formats(self):
        self.assertEqual(m.fmt_hours(50), "2d 2h")
        self.assertEqual(m.fmt_minutes(43.2), "43m 12s")
        self.assertEqual(m.fmt_count(30000), "30,000")


class SloMathCliTests(unittest.TestCase):
    def test_text_output_shows_minutes_requests_and_alert_table(self):
        code, out, err = run(SKILL, SCRIPT, "--target", "99.9", "--window", "30",
                             "--rpd", "1000000")
        self.assertEqual(code, 0, err)
        self.assertIn("43.2 minutes of full outage per window (43m 12s)", out)
        self.assertIn("30,000 bad requests per window at 1,000,000 requests/day", out)
        self.assertIn("14.4x", out)
        self.assertIn("1.44%", out)

    def test_json_single_slo_is_an_object(self):
        code, out, _ = run(SKILL, SCRIPT, "--target", "99.9", "--window", "30",
                           "--rph", "1000", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["requests_per_day"], 24000.0)
        self.assertEqual(data["alerts"][0]["noisy"], ["short"])

    def test_missing_target_exits_2(self):
        code, out, err = run(SKILL, SCRIPT, "--window", "30")
        self.assertEqual(code, 2)
        self.assertIn("give --target and --window", err)
        self.assertNotIn("Traceback", err)

    def test_100_percent_target_exits_2_with_reason(self):
        code, _, err = run(SKILL, SCRIPT, "--target", "100", "--window", "30")
        self.assertEqual(code, 2)
        self.assertIn("no error budget", err)

    def test_negative_traffic_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "--target", "99.9", "--window", "30", "--rpd", "-5")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_batch_file_json_and_out_file(self):
        with workdir() as d:
            src = write(os.path.join(d, "slos.json"), json.dumps([
                {"name": "checkout", "target": 99.9, "window_days": 30,
                 "requests_per_day": 1000000, "dependencies": [99.95],
                 "outages_minutes": [40]},
                {"name": "backoffice", "target": "99.5%", "window_days": 28,
                 "requests_per_hour": 40},
            ]))
            dest = os.path.join(d, "out.json")
            code, out, err = run(SKILL, SCRIPT, "--batch", src, "--json", "-o", dest)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")
            data = json.loads(read(dest))
        self.assertEqual([r["name"] for r in data], ["checkout", "backoffice"])
        self.assertEqual(data[0]["outages"][0]["budget_spent_pct"], 92.59)
        self.assertEqual(data[1]["requests_per_day"], 960.0)
        self.assertAlmostEqual(data[1]["budget_minutes_full_outage"], 201.6)

    def test_batch_from_stdin_single_object(self):
        code, out, err = run(SKILL, SCRIPT, "--batch", "-", "--json",
                             stdin=json.dumps({"target": 99.9, "window_days": 30}))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)[0]["name"], "SLO 1")

    def test_batch_bad_inputs_exit_2(self):
        cases = {
            "missing_key.json": json.dumps([{"target": 99.9}]),
            "empty.json": "[]",
            "broken.json": "{not json",
            "both_traffic.json": json.dumps([{"target": 99.9, "window_days": 30,
                                              "requests_per_day": 10,
                                              "requests_per_hour": 1}]),
            "deps_not_list.json": json.dumps([{"target": 99.9, "window_days": 30,
                                               "dependencies": 99.9}]),
        }
        with workdir() as d:
            for name, text in cases.items():
                path = write(os.path.join(d, name), text)
                code, _, err = run(SKILL, SCRIPT, "--batch", path)
                self.assertEqual(code, 2, name)
                self.assertTrue(err.startswith("error:"), name)
            code, _, err = run(SKILL, SCRIPT, "--batch", os.path.join(d, "nope.json"))
            self.assertEqual(code, 2)
            self.assertIn("cannot read", err)


if __name__ == "__main__":
    unittest.main()

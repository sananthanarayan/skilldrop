import json
import os
import unittest
from datetime import datetime, timedelta, timezone

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "ai-usage-report", "build_report.py"
WINDOW = ("--from", "2026-05-01", "--to", "2026-05-07")

EVENTS = [
    ("2026-05-04T09:00:00Z", "ana", "claude-code", "s1", "1"),
    ("2026-05-04T09:05:00Z", "ana", "claude-code", "s1", "0"),
    ("2026-05-04T10:00:00Z", "ana", "cursor", "s2", "1"),
    ("2026-05-05T09:00:00Z", "ben", "cursor", "s3", "0"),
    ("2026-05-06T09:00:00Z", "ben", "cursor", "s4", ""),
    ("2026-04-30T09:00:00Z", "ben", "cursor", "s9", "1"),  # before the window
]
CSV = "timestamp,user,tool,session_id,output_consumed\n" + "".join(",".join(e) + "\n" for e in EVENTS)
ANA = "| ana | 3 | 2 | 1.5 | 2 | 67% | 50% |"
BEN = "| ben | 2 | 2 | 1.0 | 1 | 0% | 100% |"


class BuildReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def build(self, name, text, *args):
        """Write the input, run the script, return (code, stdout, stderr, report text or None)."""
        with workdir() as d:
            path = write(os.path.join(d, name), text)
            out = os.path.join(d, "report.md")
            code, so, se = run(SKILL, SCRIPT, path, "-o", out, *args)
            report = read(out) if os.path.exists(out) else None
        return code, so, se, report

    # --- per-user -----------------------------------------------------------------------

    def test_per_user_metrics_from_hand_counted_events(self):
        code, so, se, rep = self.build("events.csv", CSV, *WINDOW)
        self.assertEqual(code, 0, se)
        self.assertIn("(5 events, 2 users, view=per-user)", so)
        self.assertIn(ANA, rep)
        self.assertIn(BEN, rep)
        self.assertLess(rep.index(ANA), rep.index(BEN))
        self.assertIn("**Total invocations:** 5", rep)
        self.assertIn("**Distinct tools / skills observed:** 2", rep)

    def test_top_tools_counted_with_share(self):
        code, so, se, rep = self.build("events.csv", CSV, *WINDOW)
        self.assertIn("| cursor | 3 | 60% |\n| claude-code | 2 | 40% |", rep)

    def test_period_is_on_the_header(self):
        code, so, se, rep = self.build("events.csv", CSV, *WINDOW, "--team-name", "Platform")
        self.assertIn("# AI Usage Report — Platform", rep)
        self.assertIn("**Period:** 2026-05-01 → 2026-05-07", rep)

    def test_date_only_range_counts_every_calendar_day(self):
        code, so, se, rep = self.build("events.csv", CSV, "--from", "2026-05-01", "--to", "2026-05-31")
        self.assertIn("(31 days)", rep)

    def test_effectiveness_view_puts_highest_single_shot_first(self):
        code, so, se, rep = self.build("events.csv", CSV, *WINDOW, "--view", "effectiveness")
        self.assertEqual(code, 0, se)
        self.assertLess(rep.index(BEN), rep.index(ANA))

    def test_missing_signals_shown_as_dash_not_invented(self):
        text = "timestamp,user,tool\n2026-05-04T09:00:00Z,ana,cursor\n2026-05-04T10:00:00Z,ana,cursor\n"
        code, so, se, rep = self.build("events.csv", text, *WINDOW)
        self.assertEqual(code, 0, se)
        self.assertIn("| ana | 2 | — | — | 1 | — | — |", rep)
        self.assertIn("input is missing `session_id`, `output_consumed`, `consumed_at`, `outcome`", rep)
        self.assertIn("`output_consumed` absent → **effectiveness rate** could not be computed.", rep)

    def test_caveat_lists_only_the_absent_fields(self):
        code, so, se, rep = self.build("events.csv", CSV, *WINDOW)
        self.assertIn("input is missing `consumed_at`, `outcome`", rep)
        self.assertNotIn("`session_id` absent", rep)

    def test_jsonl_input_gives_same_numbers(self):
        rows = [dict(zip(("timestamp", "user", "tool", "session_id"), e[:4]),
                     **({"output_consumed": e[4] == "1"} if e[4] else {})) for e in EVENTS]
        text = "\n".join(json.dumps(r) for r in rows) + "\n\n"
        code, so, se, rep = self.build("events.jsonl", text, *WINDOW)
        self.assertEqual(code, 0, se)
        self.assertIn(ANA, rep)
        self.assertIn(BEN, rep)

    def test_rolling_week_excludes_older_events(self):
        now = datetime.now(timezone.utc)
        stamp = lambda days: (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        text = "timestamp,user,tool\n{},ana,cursor\n{},ben,cursor\n".format(stamp(1), stamp(10))
        code, so, se, rep = self.build("events.csv", text, "--period", "week")
        self.assertEqual(code, 0, se)
        self.assertIn("(1 events, 1 users, view=per-user)", so)
        self.assertNotIn("| ben |", rep)

    def test_default_output_next_to_input(self):
        with workdir() as d:
            path = write(os.path.join(d, "events.csv"), CSV)
            code, so, se = run(SKILL, SCRIPT, path, *WINDOW)
            self.assertEqual(code, 0, se)
            self.assertTrue(os.path.isfile(os.path.join(d, "events.report.md")))

    # --- team rollup --------------------------------------------------------------------

    def rollup_csv(self, counts, consumed_user=None):
        lines = ["timestamp,user,tool,output_consumed"]
        for user, n in counts:
            for i in range(n):
                lines.append("2026-05-0{}T09:{:02d}:00Z,{},cursor,{}".format(
                    1 + i % 7, i, user, "1" if user == consumed_user else "0"))
        return "\n".join(lines) + "\n"

    def test_rollup_refuses_fewer_than_five_users(self):
        text = self.rollup_csv([("user-a", 3), ("user-b", 3), ("user-c", 3), ("user-d", 3)])
        code, so, se, rep = self.build("events.csv", text, *WINDOW, "--view", "team-rollup")
        self.assertEqual(code, 1)
        self.assertIn("requires ≥5 users", se)
        self.assertIsNone(rep)

    def test_rollup_tiers_medians_and_effectiveness(self):
        counts = [("user-a", 21), ("user-b", 20), ("user-c", 5), ("user-d", 4), ("user-e", 1)]
        text = self.rollup_csv(counts, consumed_user="user-a")
        code, so, se, rep = self.build("events.csv", text, "--view", "team-rollup",
                                       "--from", "2026-05-01", "--to", "2026-05-08T00:00:00+00:00")
        self.assertEqual(code, 0, se)
        self.assertIn("(7 days)", rep)
        self.assertIn("| Invocations / user / day (median) | 0.7 |", rep)
        self.assertIn("| Distinct tools per user (median) | 1 |", rep)
        self.assertIn("| Effectiveness rate (team avg) | 41% |", rep)
        self.assertIn("| Single-shot session rate (team avg) | — |", rep)
        self.assertIn("| Active users (≥1 invocation in period) | 5 of 5 |", rep)
        self.assertRegex(rep, r"\*\*Heavy\*\*[^|]*\| 1 \|")
        self.assertRegex(rep, r"\*\*Moderate\*\*[^|]*\| 2 \|")
        self.assertRegex(rep, r"\*\*Light\*\*[^|]*\| 2 \|")
        self.assertIn("(21 of 51). The remaining 30 invocations", rep)

    def test_rollup_never_names_a_user(self):
        counts = [("user-a", 2), ("user-b", 2), ("user-c", 2), ("user-d", 2), ("user-e", 2)]
        code, so, se, rep = self.build("events.csv", self.rollup_csv(counts), *WINDOW, "--view", "team-rollup")
        self.assertEqual(code, 0, se)
        for user, _ in counts:
            self.assertNotIn(user, rep)

    # --- helpers ------------------------------------------------------------------------

    def test_parse_ts_forms(self):
        utc = timezone.utc
        self.assertEqual(self.m.parse_ts("2026-05-21T14:32:11Z"), datetime(2026, 5, 21, 14, 32, 11, tzinfo=utc))
        self.assertEqual(self.m.parse_ts("2026-05-21"), datetime(2026, 5, 21, tzinfo=utc))
        self.assertEqual(self.m.parse_ts("2026-05-21T14:32:11"), datetime(2026, 5, 21, 14, 32, 11, tzinfo=utc))
        self.assertIsNone(self.m.parse_ts("yesterday"))
        self.assertIsNone(self.m.parse_ts(""))

    def test_parse_bool_forms(self):
        self.assertEqual([self.m.parse_bool(v) for v in ("1", "yes", "T", True, "0", "no", False, "maybe", "")],
                         [True, True, True, True, False, False, False, None, None])

    def test_date_only_to_reaches_end_of_day(self):
        start, end = self.m.resolve_period("week", "2026-05-01", "2026-05-07")
        self.assertEqual(end, datetime(2026, 5, 7, 23, 59, 59, tzinfo=timezone.utc))

    # --- bad input ----------------------------------------------------------------------

    def test_from_without_to_exits_with_message(self):
        code, so, se, rep = self.build("events.csv", CSV, "--from", "2026-05-01")
        self.assertEqual(code, 1)
        self.assertIn("--from and --to must be used together", se)

    def test_unparseable_dates_exit_with_message(self):
        code, so, se, rep = self.build("events.csv", CSV, "--from", "May 1", "--to", "May 7")
        self.assertEqual(code, 1)
        self.assertIn("could not parse --from / --to", se)

    def test_missing_input_exits_1(self):
        with workdir() as d:
            code, so, se = run(SKILL, SCRIPT, os.path.join(d, "nope.csv"))
        self.assertEqual(code, 1)
        self.assertIn("input file not found", se)

    def test_header_only_file_has_no_events(self):
        code, so, se, rep = self.build("events.csv", "timestamp,user,tool\n", *WINDOW)
        self.assertEqual(code, 1)
        self.assertIn("input file has no events", se)

    def test_no_events_in_window_exits_1(self):
        code, so, se, rep = self.build("events.csv", CSV, "--from", "2025-01-01", "--to", "2025-01-31")
        self.assertEqual(code, 1)
        self.assertIn("no events fell within", se)

    def test_unsupported_file_type_exits_with_message(self):
        code, so, se, rep = self.build("events.txt", CSV, *WINDOW)
        self.assertEqual(code, 1)
        self.assertIn("unsupported file type '.txt'", se)

    def test_malformed_jsonl_line_fails_clearly(self):
        text = '{"timestamp": "2026-05-04T09:00:00Z", "user": "ana", "tool": "cursor"}\n{not json\n'
        code, so, se, rep = self.build("events.jsonl", text, *WINDOW)
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", se)

    def test_missing_required_user_column_is_an_error(self):
        text = "timestamp,tool\n2026-05-04T09:00:00Z,cursor\n"
        code, so, se, rep = self.build("events.csv", text, *WINDOW)
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

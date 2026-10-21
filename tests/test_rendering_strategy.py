import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "rendering-strategy", "render_load.py"
HEADER = "route,mode,views_month,pages,revalidate_s,changes_month,builds_month\n"


def row_for(line):
    """Parse one CSV data line against HEADER into the dict csv.DictReader would give."""
    return dict(zip(HEADER.strip().split(","), line.split(",")))


class RenderLoadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def r(self, line):
        return self.m.renders(row_for(line), 2)

    def test_ssr_renders_once_per_view(self):
        r = self.r("/search,ssr,1000,,,,")
        self.assertEqual(r["origin"], 1000)
        self.assertEqual(self.m.pct(r["saved"]), "no fewer")

    def test_edge_renders_once_per_view(self):
        self.assertEqual(self.r("/geo,edge,500,,,,")["origin"], 500)

    def test_csr_has_no_origin_renders_but_notes_data_calls(self):
        r = self.r("/app,csr,1200,,,,")
        self.assertEqual(r["origin"], 0)
        self.assertEqual(self.m.pct(r["saved"]), "100% fewer")
        self.assertIn("1,200 client data calls", r["note"])

    def test_ssg_counts_builds_times_pages_plus_changes(self):
        r = self.r("/docs/[slug],ssg,100000,10,,5,30")
        self.assertEqual(r["origin"], 305)
        self.assertEqual(self.m.pct(r["saved"]), ">99% fewer")

    def test_ssg_more_renders_than_views_is_reported_as_more(self):
        r = self.r("/rare,ssg,1000,100,,0,30")
        self.assertEqual(r["origin"], 3000)
        self.assertEqual(self.m.pct(r["saved"]), "200% more")

    def test_isr_single_page_caps_at_one_render_per_window(self):
        # 30-day month / 60 s = 43,200 windows
        r = self.r("/home,isr,1000000,1,60,0,")
        self.assertEqual(r["origin"], 43200)
        self.assertEqual(r["note"], "at most one render per window")
        self.assertEqual(self.m.pct(r["saved"]), "96% fewer")

    def test_isr_adds_on_demand_changes_to_time_windows(self):
        r = self.r("/home,isr,1000000,1,3600,100,")
        self.assertEqual(r["origin"], 820)

    def test_isr_many_pages_even_traffic_upper_bound(self):
        r = self.r("/p/[slug],isr,1000000,10,3600,0,")
        self.assertEqual(r["origin"], 7200)
        self.assertIn("upper bound if traffic is even", r["note"])

    def test_isr_long_tail_saves_nothing_and_says_use_on_demand(self):
        r = self.r("/p/[slug],isr,50000,10000,60,0,")
        self.assertEqual(r["origin"], 50000)
        self.assertEqual(self.m.pct(r["saved"]), "no fewer")
        self.assertIn("use on-demand", r["note"])

    def test_isr_on_demand_only_renders_once_per_change(self):
        r = self.r("/blog,isr,10000,50,,200,")
        self.assertEqual(r["origin"], 200)
        self.assertEqual(r["note"], "on-demand revalidation only")

    def test_isr_renders_never_exceed_views(self):
        self.assertEqual(self.r("/quiet,isr,100,1,,500,")["origin"], 100)
        self.assertEqual(self.r("/quiet,isr,100,1,60,500,")["origin"], 100)

    def test_pct_bands(self):
        self.assertEqual(self.m.pct(0.003), "<1% fewer")
        self.assertEqual(self.m.pct(0.5), "50% fewer")
        self.assertEqual(self.m.pct(0.997), ">99% fewer")
        self.assertEqual(self.m.pct(-0.25), "25% more")

    def test_underscore_thousands_separator_is_accepted(self):
        self.assertEqual(self.r("/x,ssr,1_000,,,,")["views"], 1000)

    def test_bad_mode_raises_with_line_number(self):
        with self.assertRaisesRegex(ValueError, "line 2: mode must be one of"):
            self.r("/x,spa,10,,,,")

    def test_negative_and_non_numeric_values_raise(self):
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            self.r("/x,ssr,-5,,,,")
        with self.assertRaisesRegex(ValueError, "must be a number"):
            self.r("/x,ssr,lots,,,,")

    def test_views_month_is_required(self):
        with self.assertRaisesRegex(ValueError, "'views_month' is required"):
            self.r("/x,ssr,,,,,")


class RenderLoadCliTest(unittest.TestCase):
    CSV = HEADER + "/search,ssr,1000,,,,\n\n/app,csr,1000,,,,\n"

    def test_report_table_and_total_row(self):
        with workdir() as d:
            p = write(os.path.join(d, "routes.csv"), self.CSV)
            code, out, err = run(SKILL, SCRIPT, p)
        self.assertEqual(code, 0, err)
        self.assertIn("| /search | ssr | 1,000 | 1,000 | no fewer |", out)
        self.assertIn("| /app | csr | 1,000 | 0 | 100% fewer |", out)
        self.assertIn("| **Total** | | 2,000 | 1,000 | 50% fewer | |", out)

    def test_stdin_and_output_file(self):
        with workdir() as d:
            target = os.path.join(d, "report.md")
            code, out, err = run(SKILL, SCRIPT, "-", "-o", target, stdin=self.CSV)
            self.assertEqual(code, 0, err)
            self.assertIn("wrote", out)
            self.assertIn("| **Total** |", read(target))

    def test_missing_columns_exit_2(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin="route,mode\n/x,ssr\n")
        self.assertEqual(code, 2)
        self.assertIn("missing columns: views_month", err)

    def test_header_only_exit_2(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin=HEADER)
        self.assertEqual(code, 2)
        self.assertIn("no routes", err)

    def test_bad_row_exit_2_without_traceback(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin=HEADER + "/x,spa,10,,,,\n")
        self.assertEqual(code, 2)
        self.assertIn("line 2", err)
        self.assertNotIn("Traceback", err)

    def test_missing_file_exit_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "nope.csv"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)


if __name__ == "__main__":
    unittest.main()

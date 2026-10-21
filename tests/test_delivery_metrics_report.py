import json
import os
import unittest
from types import SimpleNamespace

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "delivery-metrics-report", "delivery_metrics.py"
m = load(SKILL, SCRIPT)

# Window: Monday 2026-07-06 .. Sunday 2026-07-19 (two ISO weeks).
DEPLOYS = """deploy_id,service,deployed_at,status,environment,first_commit_at,recovered_at,unplanned
d1,checkout,2026-07-06T10:00:00Z,success,production,2026-07-05T10:00:00Z,,false
d2,checkout,2026-07-07T10:00:00Z,rolled_back,production,2026-07-07T08:00:00Z,2026-07-07T10:30:00Z,false
d3,checkout,2026-07-08T10:00:00Z,success,staging,2026-07-08T09:00:00Z,,false
d4,checkout,2026-07-14T10:00:00Z,success,prod,2026-07-13T22:00:00Z,,true
d5,checkout,2026-07-15T10:00:00Z,success,production,2026-07-15T06:00:00Z,,false
d6,checkout,,success,production,,,false
d7,search,2026-07-09T10:00:00Z,success,production,,,false
"""

INCIDENTS = """incident_id,service,started_at,resolved_at,caused_by_deploy,severity
INC-1,checkout,2026-07-15T11:00:00Z,2026-07-15T14:00:00Z,d5,sev2
INC-2,checkout,2026-07-16T09:00:00Z,2026-07-16T10:00:00Z,,sev3
INC-3,checkout,2026-07-17T09:00:00Z,,,sev3
INC-4,checkout,2026-07-18T09:00:00Z,2026-07-18T10:00:00Z,d99,sev3
"""

PRS = """pr_id,service,opened_at,merged_at,closed_at,first_commit_at,deploy_id
p1,checkout,2026-07-06T09:00:00Z,2026-07-07T09:00:00Z,,2026-07-06T08:00:00Z,d2
p2,checkout,2026-07-13T09:00:00Z,2026-07-14T09:00:00Z,,2026-07-13T22:00:00Z,d4
p3,checkout,2026-07-08T09:00:00Z,,2026-07-10T09:00:00Z,,
p4,checkout,2026-07-15T09:00:00Z,,,,
"""


def compute(d, deploys=DEPLOYS, incidents=None, prs=None, service="checkout",
            date_from="2026-07-06", date_to="2026-07-19", assume_tz=None):
    args = SimpleNamespace(
        deployments=write(os.path.join(d, "deploys.csv"), deploys),
        incidents=write(os.path.join(d, "incidents.csv"), incidents) if incidents is not None else None,
        prs=write(os.path.join(d, "prs.csv"), prs) if prs is not None else None,
        service=service, date_from=date_from, date_to=date_to, assume_tz=assume_tz)
    return m.compute(args)


class DeliveryMetricsTests(unittest.TestCase):
    def test_deployment_frequency_counts_production_rows_for_the_service(self):
        with workdir() as d:
            r = compute(d)
        f = r["dora"]["deployment_frequency"]
        self.assertEqual(f["deployments"], 4)  # d1, d2, d4, d5
        self.assertEqual(f["days_in_window"], 14)
        self.assertEqual(f["per_week_mean"], 2.0)
        self.assertEqual(f["per_day"], 0.286)
        self.assertEqual(f["median_hours_between_deployments"], 24.0)
        self.assertEqual(f["weekly"], {"2026-07-06": 2, "2026-07-13": 2})

    def test_data_quality_counts_skipped_rows(self):
        with workdir() as d:
            q = compute(d)["data_quality"]
        self.assertEqual(q["deploy_rows_read"], 7)
        self.assertEqual(q["deploy_rows_skipped_missing_deployed_at"], 1)
        self.assertEqual(q["deploy_rows_skipped_non_production"], 1)

    def test_change_fail_rate_counts_rollbacks_and_incident_linked_deploys(self):
        with workdir() as d:
            c = compute(d, incidents=INCIDENTS)["dora"]["change_fail_rate"]
        self.assertEqual((c["failed_deployments"], c["deployments"], c["rate"]), (2, 4, 0.5))
        self.assertEqual(c["weekly"]["2026-07-13"], {"failed": 1, "deployments": 2, "rate": 0.5})

    def test_without_incidents_only_status_marks_failure(self):
        with workdir() as d:
            c = compute(d)["dora"]["change_fail_rate"]
        self.assertEqual((c["failed_deployments"], c["rate"]), (1, 0.25))

    def test_failed_deployment_recovery_time_uses_recovered_at_then_incident(self):
        with workdir() as d:
            fd = compute(d, incidents=INCIDENTS)["dora"]["failed_deployment_recovery_time"]
        # d2: 30 min to recovered_at; d5: 4 h to INC-1 resolved_at
        self.assertEqual(fd["n"], 2)
        self.assertEqual(fd["p50_hours"], 2.25)
        self.assertTrue(fd["low_n"])
        self.assertEqual(fd["failed_deployments_without_recovery_time"], [])

    def test_failed_deploy_with_no_recovery_signal_is_listed(self):
        deploys = ("deploy_id,service,deployed_at,status\n"
                   "a1,checkout,2026-07-06T10:00:00Z,hotfixed\n")
        with workdir() as d:
            fd = compute(d, deploys=deploys)["dora"]["failed_deployment_recovery_time"]
        self.assertEqual(fd["n"], 0)
        self.assertEqual(fd["failed_deployments_without_recovery_time"], ["a1"])

    def test_time_to_restore_all_incidents_and_unresolved_count(self):
        with workdir() as d:
            r = compute(d, incidents=INCIDENTS)
        ttr = r["time_to_restore_service_all_incidents"]
        self.assertEqual((ttr["n"], ttr["p50_hours"]), (3, 1.0))
        self.assertEqual(ttr["incidents_in_window"], 4)
        self.assertEqual(ttr["not_caused_by_a_deployment"], 2)
        self.assertEqual(r["data_quality"]["incidents_unresolved_excluded_from_restore_time"], 1)
        self.assertTrue(any("INC-4 names deployment d99" in n for n in r["notes"]))

    def test_lead_time_from_deployments_first_commit(self):
        with workdir() as d:
            lt = compute(d)["dora"]["lead_time_for_changes"]
        # lead times 24, 2, 12, 4 h
        self.assertEqual(lt["source"], "deployments.first_commit_at -> deployed_at")
        self.assertEqual((lt["n"], lt["p50_hours"], lt["p85_hours"], lt["p95_hours"]),
                         (4, 8.0, 18.6, 22.2))

    def test_lead_time_prefers_prs_with_deploy_id(self):
        with workdir() as d:
            r = compute(d, prs=PRS)
        lt = r["dora"]["lead_time_for_changes"]
        self.assertEqual(lt["source"], "prs.first_commit_at -> deployed_at of prs.deploy_id")
        self.assertEqual((lt["n"], lt["p50_hours"]), (2, 19.0))  # 26 h and 12 h
        self.assertEqual(r["data_quality"]["prs_without_a_deploy_in_window_or_first_commit"], 2)

    def test_no_first_commit_anywhere_means_lead_time_not_computed(self):
        deploys = "deploy_id,service,deployed_at,status\na1,checkout,2026-07-06T10:00:00Z,success\n"
        with workdir() as d:
            r = compute(d, deploys=deploys)
        self.assertIsNone(r["dora"]["lead_time_for_changes"])
        self.assertTrue(any("Lead time for changes not computed" in n for n in r["notes"]))

    def test_rework_rate_only_with_unplanned_column(self):
        with workdir() as d:
            rw = compute(d)["dora"]["deployment_rework_rate"]
            self.assertEqual(rw, {"unplanned_deployments": 1, "deployments": 4, "rate": 0.25})
            plain = "deploy_id,service,deployed_at,status\na1,checkout,2026-07-06T10:00:00Z,ok\n"
            self.assertIsNone(compute(d, deploys=plain)["dora"]["deployment_rework_rate"])

    def test_flow_cycle_time_throughput_wip_and_abandoned(self):
        with workdir() as d:
            flow = compute(d, prs=PRS)["flow"]
        cy = flow["cycle_time"]
        # p1 starts at its first commit (25 h); p2's commit is after opening, so opened_at (24 h)
        self.assertEqual((cy["n"], cy["p50_hours"]), (2, 24.5))
        self.assertEqual(flow["throughput_merged_per_week"], {"2026-07-06": 1, "2026-07-13": 1})
        self.assertEqual(flow["throughput_mean_per_week"], 1.0)
        self.assertEqual(flow["wip_at_week_end"], {"2026-07-06": 0, "2026-07-13": 1})
        self.assertEqual(flow["abandoned_in_window"], 1)

    def test_offsets_convert_to_utc_weeks(self):
        deploys = ("deploy_id,service,deployed_at,status\n"
                   "a1,checkout,2026-07-13T01:00:00+02:00,success\n"  # Sunday 23:00 UTC
                   "a2,checkout,2026-07-13T10:00:00Z,success\n")
        with workdir() as d:
            f = compute(d, deploys=deploys)["dora"]["deployment_frequency"]
        self.assertEqual(f["weekly"], {"2026-07-06": 1, "2026-07-13": 1})

    def test_assume_tz_is_applied_and_counted(self):
        deploys = ("deploy_id,service,deployed_at,status\n"
                   "a1,checkout,2026-07-12 22:00,success\n")  # 03:00 UTC Monday at -05:00
        with workdir() as d:
            r = compute(d, deploys=deploys, assume_tz="-05:00")
        self.assertEqual(r["dora"]["deployment_frequency"]["weekly"]["2026-07-13"], 1)
        self.assertEqual(r["data_quality"]["timestamps_with_assumed_offset"], 1)
        self.assertTrue(any("read as -05:00" in n for n in r["notes"]))

    def test_short_or_partial_window_notes(self):
        with workdir() as d:
            notes = compute(d, date_from="2026-07-07", date_to="2026-07-16")["notes"]
        self.assertTrue(any("The window is 10 days" in n for n in notes))
        self.assertTrue(any("does not start on a Monday" in n for n in notes))

    def test_no_service_aggregates_and_says_so(self):
        with workdir() as d:
            r = compute(d, service=None)
        self.assertEqual(r["dora"]["deployment_frequency"]["deployments"], 5)
        self.assertEqual(r["generated_for"]["services_in_file"], ["checkout", "search"])
        self.assertTrue(any("Aggregated across 2 services" in n for n in r["notes"]))

    def test_percentile_linear_interpolation(self):
        self.assertEqual(m.percentile([4, 1, 3, 2], 50), 2.5)
        self.assertAlmostEqual(m.percentile([1, 2, 3, 4], 85), 3.55)
        self.assertEqual(m.percentile([7], 95), 7)
        self.assertIsNone(m.percentile([], 50))


class DeliveryMetricsCliTests(unittest.TestCase):
    def run_cli(self, d, deploys, *extra):
        return run(SKILL, SCRIPT, "--deployments", write(os.path.join(d, "dep.csv"), deploys), *extra)

    def test_report_and_json_files(self):
        with workdir() as d:
            inc = write(os.path.join(d, "inc.csv"), INCIDENTS)
            out, js = os.path.join(d, "o", "r.md"), os.path.join(d, "o", "m.json")
            code, _, err = self.run_cli(d, DEPLOYS, "--incidents", inc, "--service", "checkout",
                                        "--from", "2026-07-06", "--to", "2026-07-19",
                                        "--out", out, "--json", js)
            self.assertEqual(code, 0, err)
            report, data = read(out), json.loads(read(js))
        self.assertIn("# Delivery metrics: checkout", report)
        self.assertIn("| Change fail rate | 2 of 4 deployments (50.0%) |", report)
        self.assertIn("| Deployment rework rate | 1 of 4 deployments (25.0%) |", report)
        self.assertIn("(low n)", report)
        self.assertEqual(data["dora"]["change_fail_rate"]["rate"], 0.5)

    def test_timestamp_without_offset_exits_2_unless_assume_tz(self):
        deploys = "deploy_id,service,deployed_at,status\na1,svc,2026-07-06 10:00,success\n"
        with workdir() as d:
            code, _, err = self.run_cli(d, deploys)
            self.assertEqual(code, 2)
            self.assertIn("has no UTC offset", err)
            code, out, err = self.run_cli(d, deploys, "--assume-tz=+00:00")
            self.assertEqual(code, 0, err)
            self.assertIn("1 timestamp(s) had no UTC offset", out)

    def test_bad_inputs_exit_2_with_message(self):
        ok_head = "deploy_id,service,deployed_at,status\n"
        cases = [
            ("deploy_id,service,deployed_at\na1,s,2026-07-06T10:00:00Z\n", [],
             "missing required column(s): status"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,exploded\n", [], "unknown status 'exploded'"),
            (ok_head + "a1,s,last tuesday,success\n", [], "deployments line 2: cannot parse timestamp"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,success\n", ["--service", "nope"],
             "no production deployments left after filtering for service 'nope'"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,success\n", ["--from", "2026-08-01", "--to", "2026-08-31"],
             "no deployments fall inside"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,success\n", ["--from", "2026-07-10", "--to", "2026-07-01"],
             "is before --from"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,success\n", ["--from", "06/07/2026"],
             "--from must be YYYY-MM-DD"),
            (ok_head + "a1,s,2026-07-06T10:00:00Z,success\n", ["--assume-tz", "EST"],
             "--assume-tz must look like"),
            ("deploy_id,service,deployed_at,status,unplanned\na1,s,2026-07-06T10:00:00Z,success,maybe\n", [],
             "expected true/false"),
            ("", [], "empty or has no header row"),
        ]
        with workdir() as d:
            for deploys, extra, msg in cases:
                code, _, err = self.run_cli(d, deploys, *extra)
                self.assertEqual(code, 2, msg)
                self.assertIn(msg, err)
                self.assertNotIn("Traceback", err, msg)
            code, _, err = run(SKILL, SCRIPT, "--deployments", os.path.join(d, "missing.csv"))
            self.assertEqual(code, 2)
            self.assertIn("deployments file not found", err)

    def test_incident_resolved_before_start_exits_2(self):
        inc = ("incident_id,service,started_at,resolved_at\n"
               "I1,s,2026-07-06T12:00:00Z,2026-07-06T11:00:00Z\n")
        with workdir() as d:
            code, _, err = self.run_cli(d, "deploy_id,service,deployed_at,status\n"
                                           "a1,s,2026-07-06T10:00:00Z,success\n",
                                        "--incidents", write(os.path.join(d, "i.csv"), inc))
        self.assertEqual(code, 2)
        self.assertIn("incidents line 2: resolved_at is before started_at", err)

    def test_header_only_prs_file_does_not_crash(self):
        with workdir() as d:
            prs = write(os.path.join(d, "p.csv"), "pr_id,opened_at,merged_at\n")
            code, _, err = self.run_cli(d, "deploy_id,service,deployed_at,status\n"
                                           "a1,s,2026-07-06T10:00:00Z,success\n", "--prs", prs)
        self.assertIn(code, (0, 2))
        self.assertNotIn("Traceback", err)

    def test_out_of_range_assume_tz_exits_2(self):
        with workdir() as d:
            code, _, err = self.run_cli(d, "deploy_id,service,deployed_at,status\n"
                                           "a1,s,2026-07-06T10:00:00Z,success\n", "--assume-tz=+25:00")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


    def test_non_utf8_deployments_file_exits_2(self):
        with workdir() as d:
            path = os.path.join(d, "deploys.csv")
            with open(path, "wb") as f:
                f.write("deploy_id,service,deployed_at,status\na1,caf\u00e9,2026-07-06T10:00:00Z,success\n".encode("latin-1"))
            code, _, err = run(SKILL, SCRIPT, "--deployments", path)
        self.assertEqual(code, 2)
        self.assertIn("is not UTF-8 text", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

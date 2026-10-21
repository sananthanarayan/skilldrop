import csv
import io
import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "backlog-triage", "triage_backlog.py"
m = load(SKILL, SCRIPT)

BACKLOG = """Issue key,Summary,Description,Status,Assignee,Priority,Story Points,Updated,Labels,Labels
NW-1,Export invoices as PDF,Acceptance criteria: the file downloads,To Do,Ana Example,High,3,2026-09-25,billing,
NW-2,Export invoice as PDF file,no criteria here,To Do,,Medium,13,2026-06-01,billing,pdf
NW-3,Fix login timeout,Given a user when idle then logout,In Progress,Unassigned,Highest,5,2026-08-01,,
NW-4,Add dark mode,- [ ] toggle in settings,To Do,Bo Example,Low,XL,2026-09-30,,
NW-5,Old closed thing,,Done,Bo Example,Low,1,2025-01-01,,
NW-6,Weird priority,AC: works,To Do,Bo Example,Spicy,2,2026-09-30,,
"""


def triage(d, text=BACKLOG, name="backlog.csv", *extra):
    src = write(os.path.join(d, name), text)
    out, changes = os.path.join(d, "triage.md"), os.path.join(d, "changes.csv")
    code, stdout, err = run(SKILL, SCRIPT, src, "--as-of", "2026-10-01", "-o", out,
                            "--changes", changes, *extra)
    if code != 0:
        return code, err, None, None
    return code, err, read(out), list(csv.DictReader(io.StringIO(read(changes))))


def actions(changes):
    return [(r["key"], r["action"]) for r in changes]


class TriageBacklogTests(unittest.TestCase):
    def test_summary_counts(self):
        with workdir() as d:
            code, err, report, _ = triage(d)
        self.assertEqual(code, 0, err)
        self.assertIn("As of 2026-10-01 · 6 items in export · 5 open · 1 done or closed (skipped)",
                      report)
        for row in ("| Duplicate candidate pairs | 1 |", "| No owner | 2 |",
                    "| No acceptance criteria | 1 |", "| Stale (> 30 days) | 2 |",
                    "| Oversized | 2 |", "| Priority conflicts | 3 |"):
            self.assertIn(row, report)

    def test_duplicate_pair_found_with_score_and_shared_words(self):
        with workdir() as d:
            _, _, report, changes = triage(d)
        self.assertRegex(report, r"\| NW-1 / NW-2 \| 0\.\d\d \| Export invoices as PDF / "
                                 r"Export invoice as PDF file \| export pdf \|")
        dup = [r for r in changes if r["action"] == "confirm-duplicate"]
        self.assertEqual(len(dup), 1)
        self.assertEqual((dup[0]["key"], dup[0]["proposed_value"]), ("NW-2", "Duplicate of NW-1"))

    def test_similarity_threshold_flag(self):
        with workdir() as d:
            _, _, report, changes = triage(d, BACKLOG, "backlog.csv", "--similarity", "0.95")
        self.assertIn("| Duplicate candidate pairs | 0 |", report)
        self.assertIn("None at this threshold.", report)
        self.assertNotIn("confirm-duplicate", [r["action"] for r in changes])

    def test_unassigned_counts_as_no_owner_and_done_items_skipped(self):
        with workdir() as d:
            _, _, _, changes = triage(d)
        self.assertEqual([k for k, a in actions(changes) if a == "assign-owner"], ["NW-2", "NW-3"])
        self.assertNotIn("NW-5", [r["key"] for r in changes])

    def test_acceptance_criteria_patterns(self):
        # NW-1 "Acceptance criteria:", NW-3 Given/when/then, NW-4 checkbox, NW-6 "AC:"
        with workdir() as d:
            _, _, _, changes = triage(d)
        self.assertEqual([k for k, a in actions(changes) if a == "add-acceptance-criteria"], ["NW-2"])

    def test_stale_items_sorted_oldest_first_with_age(self):
        with workdir() as d:
            _, _, _, changes = triage(d)
        stale = [(r["key"], r["reason"]) for r in changes if r["action"] == "confirm-or-close"]
        self.assertEqual(stale, [("NW-2", "no update in 122 days"), ("NW-3", "no update in 61 days")])

    def test_stale_days_flag(self):
        with workdir() as d:
            _, _, report, changes = triage(d, BACKLOG, "backlog.csv", "--stale-days", "90")
        self.assertIn("| Stale (> 90 days) | 1 |", report)
        self.assertEqual([k for k, a in actions(changes) if a == "confirm-or-close"], ["NW-2"])

    def test_oversized_by_points_and_tshirt_size(self):
        with workdir() as d:
            _, _, _, changes = triage(d)
            split = [(r["key"], r["reason"]) for r in changes if r["action"] == "split"]
            self.assertEqual(split, [("NW-2", "estimate 13 > 8"), ("NW-4", "size XL")])
            _, _, _, changes = triage(d, BACKLOG, "backlog.csv", "--max-estimate", "13")
            self.assertEqual([r["key"] for r in changes if r["action"] == "split"], ["NW-4"])

    def test_priority_conflicts_listed(self):
        with workdir() as d:
            _, _, report, _ = triage(d)
        self.assertIn("- NW-3 (Fix login timeout): priority Highest but no owner", report)
        self.assertIn("- NW-3 (Fix login timeout): priority Highest but no update in 61 days", report)
        self.assertIn("- NW-1 (Export invoices as PDF): likely duplicate of NW-2 but priority High vs Medium",
                      report)
        self.assertIn("Priority values not recognised (not ranked): Spicy", report)

    def test_priority_inflation_threshold(self):
        with workdir() as d:
            _, _, report, _ = triage(d)
            self.assertNotIn("Priority inflation", report)  # 1 of 4 = 25%, not above 25%
            _, _, report, _ = triage(d, BACKLOG, "backlog.csv", "--inflation-pct", "20")
        self.assertIn("- Priority inflation: 1 of 4 prioritised open items (25%) are at the top priority.",
                      report)

    def test_priority_rank_covers_jira_linear_and_p_labels(self):
        self.assertEqual(m.priority_rank("Highest"), 0)
        self.assertEqual(m.priority_rank("1"), 0)   # Linear urgent
        self.assertEqual(m.priority_rank("0"), 5)   # Linear no priority
        self.assertEqual(m.priority_rank("P2"), 2)
        self.assertIsNone(m.priority_rank("Spicy"))

    def test_date_formats_jira_and_iso(self):
        self.assertEqual(m.parse_date("12/Mar/26 9:15 AM").isoformat(), "2026-03-12")
        self.assertEqual(m.parse_date("2026-09-25T10:00:00Z").isoformat(), "2026-09-25")
        self.assertIsNone(m.parse_date("soon"))

    def test_jira_rest_timestamp_parses(self):
        self.assertEqual(m.parse_date("2026-09-30T08:00:00.000+0000").isoformat(), "2026-09-30")

    def test_jira_rest_json_with_nested_fields_and_resolved_date(self):
        data = {"issues": [
            {"key": "J-1", "fields": {"summary": "Rotate keys", "assignee": {"displayName": "Cy Example"},
                                      "status": {"name": "To Do"}, "priority": {"name": "High"},
                                      "updated": "2026-09-30T08:00:00.000+0000", "description": "AC: done"}},
            {"key": "J-2", "fields": {"summary": "Shipped thing", "assignee": None,
                                      "status": {"name": "Review"}, "resolutiondate": "2026-09-01"}},
        ]}
        with workdir() as d:
            code, err, report, changes = triage(d, json.dumps(data), "export.json")
        self.assertEqual(code, 0, err)
        self.assertIn("2 items in export · 1 open · 1 done or closed", report)
        self.assertIn("| No owner | 0 |", report)
        self.assertEqual(changes, [])

    def test_jsonl_export(self):
        text = '{"identifier": "L-1", "title": "Add search"}\n{"identifier": "L-2", "title": "Add search box"}\n'
        with workdir() as d:
            code, err, report, _ = triage(d, text, "export.jsonl")
        self.assertEqual(code, 0, err)
        self.assertIn("| L-1 / L-2 |", report)

    def test_map_override_and_missing_columns_reported(self):
        text = "Issue summary,Team Lead\nDo a thing,Dee Example\n"
        with workdir() as d:
            code, err, report, _ = triage(d, text, "b.csv", "--map", "title=Issue summary",
                                          "--map", "owner=Team Lead")
        self.assertEqual(code, 0, err)
        self.assertIn("owner='Team Lead'", report)
        self.assertIn("| No owner | 0 |", report)
        self.assertIn("Not found in export (checks that need them are skipped): key, priority, "
                      "estimate, updated, description", report)
        self.assertIn("| Oversized | n/a |", report)

    def test_no_owner_column_does_not_create_owner_conflicts(self):
        text = "Key,Summary,Priority\nK-1,Urgent fix,Highest\n"
        with workdir() as d:
            _, _, report, _ = triage(d, text, "b.csv")
        self.assertIn("| No owner | n/a |", report)
        self.assertNotIn("but no owner", report)

    def test_skipped_checks_write_no_change_rows(self):
        text = "Key,Summary\nK-1,Do a thing\nK-2,Write docs\n"
        with workdir() as d:
            _, _, _, changes = triage(d, text, "b.csv")
        self.assertEqual(changes, [])


class TriageBacklogErrorTests(unittest.TestCase):
    def test_bad_inputs_exit_2_with_message(self):
        cases = {
            "empty.csv": ("", "is empty"),
            "header.csv": ("Summary,Status\n", "has no issues in it"),
            "notitle.csv": ("Key,Status\nK-1,To Do\n", "no title column found"),
            "broken.json": ("{nope", "is not valid JSON"),
            "shape.json": ('{"total": 3}', "JSON must be a list of issues"),
            "export.xlsx": ("x", "unsupported file type '.xlsx'"),
        }
        with workdir() as d:
            for name, (text, msg) in cases.items():
                code, _, err = run(SKILL, SCRIPT, write(os.path.join(d, name), text),
                                   "--as-of", "2026-10-01")
                self.assertEqual(code, 2, name)
                self.assertIn(msg, err, name)
                self.assertNotIn("Traceback", err, name)
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.csv"))
            self.assertEqual(code, 2)
            self.assertIn("does not exist", err)

    def test_bad_flags_exit_2(self):
        with workdir() as d:
            src = write(os.path.join(d, "b.csv"), BACKLOG)
            for args, msg in ((["--as-of", "someday"], "--as-of must be YYYY-MM-DD"),
                              (["--similarity", "0"], "--similarity must be between 0 and 1"),
                              (["--map", "owner"], "--map takes FIELD=Column"),
                              (["--map", "boss=Assignee"], "unknown field 'boss'"),
                              (["--map", "owner=Team Lead"], "no such column")):
                code, _, err = run(SKILL, SCRIPT, src, *args)
                self.assertEqual(code, 2, args)
                self.assertIn(msg, err, args)

    def test_non_utf8_export_exits_2(self):
        with workdir() as d:
            path = os.path.join(d, "b.csv")
            with open(path, "wb") as f:
                f.write("Key,Summary\nK-1,Café\n".encode("latin-1"))
            code, _, err = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_report_to_stdout_without_output_flag(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, write(os.path.join(d, "b.csv"), BACKLOG),
                               "--as-of", "2026-10-01")
        self.assertEqual(code, 0)
        self.assertIn("# Backlog triage findings: b.csv", out)


if __name__ == "__main__":
    unittest.main()

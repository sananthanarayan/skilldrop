import json
import os
import unittest

from tests.support import run, workdir, write, read

SKILL, SCRIPT = "team-status-report", "status_counts.py"
PERIOD = ("--from", "2026-09-24", "--to", "2026-09-30")

EXPORT = """Issue key,Summary,Status,Assignee,Priority,Resolved,Updated,Due date,Sprint,Blocked reason,Labels
CHK-1,Ship cart,Done,Ana Example,High,2026-09-25,2026-09-25,2026-09-28,CHK Sprint 14,,
CHK-2,Fix tax,Done,Bo Example,Medium,2026-09-20,2026-09-20,2026-09-29,CHK Sprint 14,,
CHK-3,Coupons,In Progress,Cy Example,High,,2026-09-29,2026-09-30,CHK Sprint 14,,
CHK-4,Payments API,Blocked,Ana Example,Medium,,2026-09-27,2026-09-26,CHK Sprint 14,Waiting on vendor sandbox,
CHK-5,Refunds,In Review,,Low,,2026-09-28,2026-09-30,CHK Sprint 14,,blocked
CHK-6,Hotfix banner,Done,Bo Example,Low,2026-09-26,2026-09-26,,,,
CHK-7,Old due,To Do,Dee Example,Highest,,2026-09-01,2026-09-10,CHK Sprint 13,,
CHK-8,Dropped idea,Cancelled,,Low,,,2026-09-27,CHK Sprint 14,,
CHK-9,Done no date,Done,Ana Example,Low,,,2026-10-05,,,
"""


def status(d, text=EXPORT, name="export.csv", *extra):
    src = write(os.path.join(d, name), text)
    md, js = os.path.join(d, "numbers.md"), os.path.join(d, "numbers.json")
    code, _, err = run(SKILL, SCRIPT, src, *PERIOD, "-o", md, "--json", js, *extra)
    if code != 0:
        return code, err, None, None
    return code, err, read(md), json.loads(read(js))


def plan_file(d, *keys):
    return write(os.path.join(d, "plan.txt"), "# planned keys\n" + "\n".join(keys) + "\n")


class StatusCountsTests(unittest.TestCase):
    def test_counts_with_due_date_plan(self):
        with workdir() as d:
            code, err, _, data = status(d)
        self.assertEqual(code, 0, err)
        self.assertEqual(data["plan_source"], "items due between 2026-09-24 and 2026-09-30")
        self.assertEqual(data["counts"], {"shipped": 2, "in_progress": 1, "blocked": 2, "planned": 5,
                                          "planned_done": 2, "slipped": 3, "unplanned_shipped": 1})
        self.assertEqual(data["shipped"], ["CHK-1", "CHK-6"])
        self.assertEqual(data["slipped"], ["CHK-3", "CHK-4", "CHK-5"])

    def test_red_from_completion_and_blocked_planned_items(self):
        with workdir() as d:
            _, _, report, data = status(d)
        self.assertEqual(data["rag"], "Red")
        self.assertEqual(data["rag_reasons"], [
            "plan completion 40% is below 60%",
            "2 planned items are blocked (Red at 2)",
            "1 High-or-above planned item(s) slipped: CHK-3",
        ])
        self.assertIn("## Suggested RAG: Red", report)
        self.assertIn("| Planned and done | 2 (40%) |", report)

    def test_blocked_by_status_label_and_blocker_text(self):
        with workdir() as d:
            _, _, report, data = status(d)
        self.assertEqual(data["blocked"], [
            {"key": "CHK-4", "owner": "Ana Example", "blocker": "Waiting on vendor sandbox"},
            {"key": "CHK-5", "owner": "", "blocker": ""},
        ])
        self.assertIn("| CHK-5 | Refunds | (none) | (not recorded) | 2026-09-28 |", report)

    def test_data_notes_for_undated_done_and_overdue_items(self):
        with workdir() as d:
            _, _, _, data = status(d)
        self.assertIn("1 done items have no resolved date and are not counted as shipped: CHK-9",
                      data["notes"])
        self.assertIn("1 items were due before this period and are still open: CHK-7", data["notes"])

    def test_risk_candidates_and_wip_by_owner(self):
        with workdir() as d:
            _, _, report, _ = status(d)
        for line in ("- CHK-4 (Payments API): planned for this period and blocked",
                     "- CHK-5 (Refunds): planned for this period with no owner",
                     "- CHK-7 (Old due): top priority (Highest) and not started"):
            self.assertIn(line, report)
        wip = report.split("## Work in progress by owner")[1]
        self.assertLess(wip.index("| (none) | 1 |"), wip.index("| Ana Example | 1 |"))
        self.assertIn("| Cy Example | 1 |", wip)

    def test_sprint_plan(self):
        with workdir() as d:
            _, _, _, data = status(d, EXPORT, "export.csv", "--sprint", "CHK Sprint 14")
        self.assertEqual(data["plan_source"], "items in sprint 'CHK Sprint 14'")
        self.assertEqual(data["counts"]["planned"], 5)  # the cancelled CHK-8 is left out

    def test_sprint_name_matches_whole_name_not_substring(self):
        with workdir() as d:
            _, _, _, data = status(d, EXPORT, "export.csv", "--sprint", "CHK Sprint 1")
        self.assertEqual(data["counts"]["planned"], 0)

    def test_plan_file_green_with_missing_key_noted(self):
        with workdir() as d:
            _, _, _, data = status(d, EXPORT, "export.csv",
                                   "--plan-file", plan_file(d, "CHK-1", "CHK-6", "CHK-99"))
        self.assertEqual(data["plan_source"], "plan file plan.txt (3 keys)")
        self.assertEqual(data["rag"], "Green")
        self.assertEqual((data["counts"]["planned"], data["counts"]["planned_done"],
                          data["counts"]["unplanned_shipped"]), (2, 2, 0))
        self.assertIn("Plan keys not found in the export: CHK-99", data["notes"])

    def test_amber_from_completion_and_one_blocked(self):
        with workdir() as d:
            _, _, _, data = status(d, EXPORT, "export.csv",
                                   "--plan-file", plan_file(d, "CHK-1", "CHK-2", "CHK-6", "CHK-4"))
        self.assertEqual(data["rag"], "Amber")
        self.assertEqual(data["rag_reasons"], ["plan completion 75% is below 85%",
                                               "1 planned item is blocked"])

    def test_rag_thresholds_are_configurable(self):
        with workdir() as d:
            plan = plan_file(d, "CHK-1", "CHK-2", "CHK-6", "CHK-4")
            _, _, _, data = status(d, EXPORT, "export.csv", "--plan-file", plan, "--amber-below", "70")
            self.assertEqual(data["rag_reasons"], ["1 planned item is blocked"])
            _, _, _, data = status(d, EXPORT, "export.csv", "--plan-file", plan, "--red-blocked", "1")
            self.assertEqual(data["rag"], "Red")
            self.assertIn("1 planned items are blocked (Red at 1)", data["rag_reasons"])

    def test_no_plan_with_blocked_items_is_amber(self):
        text = "Key,Summary,Status\nT-1,Thing,Blocked\nT-2,Other,Done\n"
        with workdir() as d:
            _, _, _, data = status(d, text, "e.csv")
        self.assertIsNone(data["plan_source"])
        self.assertEqual(data["rag"], "Amber")
        self.assertEqual(data["rag_reasons"], ["no plan to measure against, and 1 items are blocked"])
        self.assertTrue(any(n.startswith("No plan:") for n in data["notes"]))

    def test_no_plan_and_nothing_blocked_is_green_with_caveat(self):
        text = "Key,Summary,Status\nT-1,Thing,In Progress\n"
        with workdir() as d:
            _, _, _, data = status(d, text, "e.csv")
        self.assertEqual(data["rag"], "Green, with no plan to measure against")

    def test_no_resolved_column_falls_back_to_updated(self):
        text = "Key,Summary,Status,Updated\nT-1,Thing,Done,2026-09-27\nT-2,Older,Done,2026-09-01\n"
        with workdir() as d:
            _, _, _, data = status(d, text, "e.csv")
        self.assertEqual(data["shipped"], ["T-1"])
        self.assertTrue(any("No resolved/completed column" in n for n in data["notes"]))

    def test_linear_json_export_with_map_override(self):
        data = {"nodes": [
            {"identifier": "LIN-1", "title": "Ship it", "state": {"name": "Done"},
             "assignee": {"name": "Ana Example"}, "completedAt": "2026-09-29T12:00:00Z",
             "Waiting on": "Design review"},
            {"identifier": "LIN-2", "title": "Wait", "state": {"name": "In Progress"},
             "Waiting on": "Legal sign-off"},
        ]}
        with workdir() as d:
            code, err, _, out = status(d, json.dumps(data), "e.json", "--map", "blocker=Waiting on")
        self.assertEqual(code, 0, err)
        self.assertEqual(out["shipped"], ["LIN-1"])
        self.assertEqual(out["blocked"], [{"key": "LIN-2", "owner": "", "blocker": "Legal sign-off"}])

    def test_report_to_stdout(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, write(os.path.join(d, "e.csv"), EXPORT), *PERIOD)
        self.assertEqual(code, 0)
        self.assertIn("# Status numbers: 2026-09-24 to 2026-09-30", out)


class StatusCountsErrorTests(unittest.TestCase):
    def test_bad_flags_exit_2(self):
        with workdir() as d:
            src = write(os.path.join(d, "e.csv"), EXPORT)
            cases = [
                (["--from", "next week", "--to", "2026-09-30"], "--from and --to must be YYYY-MM-DD"),
                (["--from", "2026-10-01", "--to", "2026-09-30"], "is after --to"),
                (list(PERIOD) + ["--red-below", "90"], "need 0 <= --red-below <= --amber-below <= 100"),
                (list(PERIOD) + ["--map", "boss=Assignee"], "unknown field 'boss'"),
                (list(PERIOD) + ["--map", "blocker=Nope"], "no such column"),
                (list(PERIOD) + ["--plan-file", os.path.join(d, "none.txt")], "does not exist"),
            ]
            for args, msg in cases:
                code, _, err = run(SKILL, SCRIPT, src, *args)
                self.assertEqual(code, 2, args)
                self.assertIn(msg, err, args)
            code, _, _ = run(SKILL, SCRIPT, src, *PERIOD, "--sprint", "S1",
                             "--plan-file", plan_file(d, "CHK-1"))
            self.assertEqual(code, 2)  # mutually exclusive

    def test_bad_exports_exit_2(self):
        cases = {
            "empty.csv": ("", "is empty"),
            "header.csv": ("Summary,Status\n", "has no issues in it"),
            "nostatus.csv": ("Key,Summary\nK-1,Thing\n", "no status column found"),
            "nosprint.csv": ("Key,Summary,Status\nK-1,Thing,Done\n", "--sprint given but no sprint"),
            "broken.json": ("[{", "is not valid JSON"),
            "e.txt": ("x", "unsupported file type '.txt'"),
        }
        with workdir() as d:
            for name, (text, msg) in cases.items():
                extra = ["--sprint", "S1"] if name == "nosprint.csv" else []
                code, _, err = run(SKILL, SCRIPT, write(os.path.join(d, name), text), *PERIOD, *extra)
                self.assertEqual(code, 2, name)
                self.assertIn(msg, err, name)
                self.assertNotIn("Traceback", err, name)
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.csv"), *PERIOD)
            self.assertEqual(code, 2)
            self.assertIn("does not exist", err)

    def test_non_utf8_export_exits_2(self):
        with workdir() as d:
            path = os.path.join(d, "e.csv")
            with open(path, "wb") as f:
                f.write("Key,Summary,Status\nK-1,Café,Done\n".encode("latin-1"))
            code, _, err = run(SKILL, SCRIPT, path, *PERIOD)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


    def test_non_utf8_plan_file_exits_2(self):
        with workdir() as d:
            plan = os.path.join(d, "plan.txt")
            with open(plan, "wb") as f:
                f.write("CHK-1\nCHK-\u00e9\n".encode("latin-1"))
            code, err, _, _ = status(d, EXPORT, "export.csv", "--plan-file", plan)
        self.assertEqual(code, 2)
        self.assertIn("--plan-file", err)
        self.assertIn("is not UTF-8 text", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

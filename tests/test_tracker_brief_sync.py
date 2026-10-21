import csv
import io
import json
import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

from tests.support import load, run, script_path, workdir, write, read

SKILL, SCRIPT = "tracker-brief-sync", "brief_sync.py"
m = load(SKILL, SCRIPT)

DOC = """# Guest checkout PRD

## Goals

- G1: Let guests buy without an account

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| R1 | Guest can check out with email only | Must |
| R2 | Guest gets an order confirmation email | Should |
| R3 | Guest can save a card for later | Won't |

### R4 Address autocomplete

- R5: Show a delivery estimate

```
| R9 | inside a code fence | Must |
```
"""

AC = ["Given a guest, when they enter an email, then they can pay"]


def spec(items=None, **top):
    if items is None:
        items = [
            {"id": "S1", "type": "story", "title": "Guest checkout", "description": "Guests check out with email.",
             "source": "R1", "parent": "E1", "labels": ["guest-checkout"], "acceptance_criteria": AC},
            {"id": "E1", "type": "epic", "title": "Guest buying", "description": "Goal G1.", "source": "G1",
             "labels": ["guest-checkout"]},
            {"id": "S2", "type": "story", "title": "Confirmation email", "description": "Send it.",
             "source": "R2", "parent": "E1", "acceptance_criteria": ["Given an order, when placed, then an email is sent"]},
        ]
    return json.dumps(dict({"doc": "prd.md", "items": items}, **top))


def export(d, target, spec_text=None, doc=DOC, *extra):
    s = write(os.path.join(d, "spec.json"), spec_text or spec())
    doc_path = write(os.path.join(d, "prd.md"), doc)
    out = os.path.join(d, "out.txt")
    code, _, err = run(SKILL, SCRIPT, "export", s, "--target", target, "--doc", doc_path, "-o", out, *extra)
    return code, err, (read(out) if os.path.exists(out) else None)


def tracker_csv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Issue key", "Summary", "Description", "Status", "Issue Type"])
    w.writerows(rows)
    return buf.getvalue()


TRACKER = tracker_csv([
    ["GC-1", "Guest checkout", "Do it.\n\nSource: prd.md#requirements (R1)", "In Progress", "Story"],
    ["GC-2", "Email", "Covers R2 as discussed", "To Do", "Story"],
    ["GC-3", "Save card", "Source: prd.md#requirements (R3)", "To Do", "Story"],
    ["GC-4", "Dark mode", "Nothing to do with the doc", "To Do", "Task"],
    ["GC-5", "Autocomplete", "Source: prd.md#r4 (R4)", "Cancelled", "Story"],
    ["GC-6", "Old thing", "Source: prd.md#x (R7)", "To Do", "Story"],
])


def drift(d, doc=DOC, tracker=TRACKER, name="tracker.csv", *extra):
    doc_path = write(os.path.join(d, "prd.md"), doc)
    exp = write(os.path.join(d, name), tracker)
    return run(SKILL, SCRIPT, "drift", "--doc", doc_path, "--export", exp, *extra)


class ParseDocTests(unittest.TestCase):
    def test_finds_ids_in_tables_headings_and_lists_and_skips_fences(self):
        with workdir() as d:
            info = m.parse_doc(Path(write(os.path.join(d, "prd.md"), DOC)), r"R\d+", False)
        self.assertEqual(list(info["sections"]), ["G1", "R1", "R2", "R3", "R4", "R5"])
        self.assertEqual(info["required"], ["R1", "R2", "R4", "R5"])  # R3 is Won't, G1 isn't an R id
        self.assertEqual(info["wont"], ["R3"])
        self.assertEqual(info["sections"]["R1"]["moscow"], "M")
        self.assertEqual(info["sections"]["R4"]["text"], "Address autocomplete")

    def test_headings_mode_uses_level_2_and_3_headings(self):
        doc = "# Title\n\n## Checkout flow\n\ntext\n\n### Receipts & email\n\n#### Too deep\n"
        with workdir() as d:
            info = m.parse_doc(Path(write(os.path.join(d, "b.md"), doc)), r"R\d+", True)
        self.assertEqual(info["required"], ["checkout-flow", "receipts-email"])

    def test_headings_mode_ignores_table_ids(self):
        with workdir() as d:
            info = m.parse_doc(Path(write(os.path.join(d, "prd.md"), DOC)), r"R\d+", True)
        self.assertEqual(info["required"], ["goals", "requirements", "r4-address-autocomplete"])


class ExportTests(unittest.TestCase):
    def test_jira_csv_puts_epics_first_with_parent_ids(self):
        with workdir() as d:
            code, err, out = export(d, "jira")
        self.assertEqual(code, 0, err)
        rows = list(csv.reader(io.StringIO(out)))
        self.assertEqual(rows[0], ["Issue Id", "Parent Id", "Issue Type", "Summary", "Description", "Labels"])
        self.assertEqual([r[:4] for r in rows[1:]], [["1", "", "Epic", "Guest buying"],
                                                     ["2", "1", "Story", "Guest checkout"],
                                                     ["3", "1", "Story", "Confirmation email"]])
        self.assertEqual(rows[2][5], "guest-checkout")
        self.assertEqual(rows[2][4], "Guests check out with email.\n\nAcceptance criteria:\n- " + AC[0] +
                         "\n\nSource: prd.md#requirements (R1)")
        self.assertTrue(rows[1][4].endswith("Source: prd.md#goals (G1)"))

    def test_csv_rows_end_in_one_crlf_in_a_file_and_on_stdout(self):
        # A text-mode write on Windows turned each \r\n into \r\r\n: a blank row per issue.
        with workdir() as d:
            s = write(os.path.join(d, "spec.json"), spec())
            doc_path = write(os.path.join(d, "prd.md"), DOC)
            out = os.path.join(d, "out.csv")
            code, _, err = run(SKILL, SCRIPT, "export", s, "--target", "jira", "--doc", doc_path, "-o", out)
            self.assertEqual(code, 0, err)
            with open(out, "rb") as fh:
                raw = fh.read()
            self.assertNotIn(b"\r\r\n", raw)
            self.assertTrue(raw.startswith(b"Issue Id,") and b"\r\n" in raw)
            r = subprocess.run([sys.executable, script_path(SKILL, SCRIPT), "export", s, "--target", "jira",
                                "--doc", doc_path], capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn(b"\r\r\n", r.stdout)

    def test_doc_url_used_in_source_line(self):
        with workdir() as d:
            _, _, out = export(d, "jira", spec(doc_url="https://wiki.example.test/prd"))
        self.assertIn("Source: https://wiki.example.test/prd#requirements (R1)", out)

    def test_plain_csv_target_columns(self):
        with workdir() as d:
            code, err, out = export(d, "csv")
        self.assertEqual(code, 0, err)
        rows = list(csv.DictReader(io.StringIO(out)))
        s1 = next(r for r in rows if r["ID"] == "S1")
        self.assertEqual((s1["Type"], s1["Parent ID"], s1["Parent title"]), ("Story", "E1", "Guest buying"))
        self.assertEqual(s1["Acceptance criteria"], AC[0])
        self.assertEqual(s1["Source"], "Source: prd.md#requirements (R1)")

    def test_github_target_writes_gh_commands(self):
        with workdir() as d:
            code, err, out = export(d, "github")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "#!/usr/bin/env bash")
        self.assertIn("gh label create epic --force >/dev/null", lines)
        self.assertIn("gh label create guest-checkout --force >/dev/null", lines)
        cmds = []  # bodies span lines, so tokenise the whole script and cut at each "gh"
        for tok in shlex.split(out, comments=True):
            if tok == "gh":
                cmds.append([])
            if cmds:
                cmds[-1].append(tok)
        cmds = [c for c in cmds if c[1:3] == ["issue", "create"]]
        self.assertEqual([c[c.index("--title") + 1] for c in cmds],
                         ["Guest buying", "Guest checkout", "Confirmation email"])
        self.assertIn("epic", cmds[0])
        self.assertTrue(cmds[1][cmds[1].index("--body") + 1].startswith("Part of: Guest buying (E1)\n\n"))

    def test_spec_problems_exit_1_and_write_nothing(self):
        bad = [
            {"id": "E1", "type": "epic", "title": "Epic", "description": "d", "source": "G1", "parent": "E2"},
            {"id": "E2", "type": "epic", "title": "Epic 2", "description": "d", "source": "G1"},
            {"id": "S1", "type": "story", "title": "No AC", "description": "d", "source": "R1"},
            {"id": "S2", "type": "story", "title": "Bad parent", "description": "d", "source": "R2",
             "parent": "E9", "acceptance_criteria": AC},
            {"id": "S3", "type": "story", "title": "Not in doc", "description": "d", "source": "R99",
             "acceptance_criteria": AC},
            {"id": "S4", "type": "story", "title": "Won't", "description": "d", "source": "R3",
             "acceptance_criteria": AC, "labels": ["guest checkout"]},
            {"id": "S4", "type": "feature", "title": "", "description": "d", "source": "R4"},
        ]
        with workdir() as d:
            code, err, out = export(d, "jira", spec(bad))
        self.assertEqual(code, 1)
        self.assertIsNone(out)
        for msg in ("duplicate item ids: S4", "E1: an epic can't have a parent",
                    "S1: a story needs acceptance_criteria", "S2: parent 'E9' is not an item in the spec",
                    "S3: source 'R99' is not a section in the doc",
                    "S4: source 'R3' is marked Won't have in the doc",
                    "S4: label 'guest checkout' has a space", "S4: missing 'title'",
                    "S4: type must be epic, story, task or bug, not 'feature'"):
            self.assertIn(msg, err)

    def test_empty_items_is_a_spec_problem(self):
        with workdir() as d:
            code, err, _ = export(d, "jira", json.dumps({"items": []}))
        self.assertEqual(code, 1)
        self.assertIn("spec needs a non-empty 'items' list", err)

    def test_unreadable_spec_or_doc_exits_2(self):
        with workdir() as d:
            code, err, _ = export(d, "jira", "{not json")
            self.assertEqual((code, "is not valid JSON" in err), (2, True))
            code, err, _ = export(d, "jira", "[1, 2]")
            self.assertEqual((code, "spec must be a JSON object" in err), (2, True))
            s = write(os.path.join(d, "s.json"), spec())
            code, _, err = run(SKILL, SCRIPT, "export", s, "--target", "jira",
                               "--doc", os.path.join(d, "missing.md"))
            self.assertEqual((code, "does not exist" in err), (2, True))
            code, err, _ = export(d, "jira", None, DOC, "--id-pattern", "R(")
            self.assertEqual((code, "--id-pattern is not a valid regex" in err), (2, True))


class DriftTests(unittest.TestCase):
    def test_drift_counts(self):
        with workdir() as d:
            code, out, err = drift(d)
        self.assertEqual(code, 0, err)
        self.assertIn("6 sections in the doc (4 need an issue, 1 marked Won't have) · "
                      "6 issues in the export (1 canceled or duplicate, ignored)", out)
        for row in ("| Doc sections with no issue | 2 |", "| Issues with no doc section | 1 |",
                    "| Issues pointing at a section the doc doesn't have | 1 |",
                    "| Issues for a Won't-have requirement | 1 |"):
            self.assertIn(row, out)

    def test_drift_names_each_item(self):
        with workdir() as d:
            _, out, _ = drift(d)
        # R4's only issue is cancelled, so it counts as uncovered
        self.assertIn("- R4: Address autocomplete", out)
        self.assertIn("- R5: Show a delivery estimate", out)
        self.assertIn("- GC-4 Dark mode (To Do, Task)", out)
        self.assertIn("- GC-6 Old thing: points at R7", out)
        self.assertIn("- GC-3 Save card: R3 is Won't have in the doc", out)
        self.assertIn("| R1 | M | GC-1 (In Progress) |", out)

    def test_mention_only_links_are_called_out(self):
        with workdir() as d:
            _, out, _ = drift(d)
        self.assertIn("| R2 | S | GC-2 (To Do) |", out)
        self.assertIn("Linked by mentioning the ID rather than a Source line (check these): GC-2", out)

    def test_round_trip_export_then_drift_has_only_doc_gaps(self):
        with workdir() as d:
            _, _, jira = export(d, "jira")
            rows = list(csv.DictReader(io.StringIO(jira)))
            tracker = tracker_csv([["GC-%s" % r["Issue Id"], r["Summary"], r["Description"], "To Do",
                                    r["Issue Type"]] for r in rows])
            _, out, _ = drift(d, DOC, tracker)
        self.assertIn("| Issues with no doc section | 0 |", out)
        self.assertIn("| Issues pointing at a section the doc doesn't have | 0 |", out)
        self.assertIn("| Doc sections with no issue | 2 |", out)  # R4 and R5 were never in the spec

    def test_headings_mode_drift_uses_source_lines(self):
        doc = "# Brief\n\n## Checkout flow\n\n## Receipts\n"
        tracker = tracker_csv([["B-1", "Flow", "Source: brief.md#checkout-flow (checkout-flow)", "To Do", "Story"]])
        with workdir() as d:
            code, out, err = drift(d, doc, tracker, "tracker.csv", "--headings")
        self.assertEqual(code, 0, err)
        self.assertIn("Sections are ## and ### headings.", out)
        self.assertIn("- receipts: Receipts", out)
        self.assertIn("| Doc sections with no issue | 1 |", out)

    def test_json_export_and_output_file(self):
        data = {"issues": [{"key": "GC-1", "fields": {"summary": "Guest checkout", "status": {"name": "Done"},
                                                      "description": "Source: prd.md#requirements (R1)"}}]}
        with workdir() as d:
            out_path = os.path.join(d, "drift.md")
            code, _, err = drift(d, DOC, json.dumps(data), "tracker.json", "-o", out_path)
            self.assertEqual(code, 0, err)
            self.assertIn("| R1 | M | GC-1 (Done) |", read(out_path))

    def test_drift_bad_inputs_exit_2(self):
        with workdir() as d:
            code, _, err = drift(d, "# Notes\n\nNo ids here.\n")
            self.assertEqual(code, 2)
            self.assertIn("found no sections", err)
            code, _, err = drift(d, DOC, "Key,Status\nK-1,To Do\n")
            self.assertEqual(code, 2)
            self.assertIn("no title column found", err)
            code, _, err = drift(d, DOC, "Summary,Status\n")
            self.assertEqual(code, 2)
            self.assertIn("has no issues in it", err)
            doc = write(os.path.join(d, "prd.md"), DOC)
            code, _, err = run(SKILL, SCRIPT, "drift", "--doc", doc, "--export", os.path.join(d, "nope.csv"))
            self.assertEqual(code, 2)
            self.assertIn("does not exist", err)
            self.assertNotIn("Traceback", err)

    def test_no_subcommand_exits_2(self):
        code, out, _ = run(SKILL, SCRIPT)
        self.assertEqual(code, 2)
        self.assertIn("export", out)


if __name__ == "__main__":
    unittest.main()

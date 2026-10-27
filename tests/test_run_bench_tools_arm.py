"""run_bench.py's scripts-only arm: what it is given, how it is cached, judged and read (RFC-0067)."""
import os
import subprocess
import sys
import unittest
from unittest import mock

from tests.support import ROOT, workdir, write

sys.path.insert(0, ROOT)
import catalog  # noqa: E402
import run_bench  # noqa: E402


def fake_skill(d, script_doc="Count the widgets in a CSV."):
    """A minimal skill folder: instructions, a script, and data the script reads."""
    write(os.path.join(d, "SKILL.md"), "---\nname: widgets\n---\n# widgets\n\nALWAYS-LEAD-WITH-THE-TOTAL rule.\n")
    write(os.path.join(d, "reference.md"), "REFERENCE-ONLY text\n")
    write(os.path.join(d, "manifest.json"), '{"name": "widgets"}\n')
    write(os.path.join(d, "examples", "one.md"), "EXAMPLE text\n")
    write(os.path.join(d, "evals", "evals.json"), '{"evals": []}\n')
    write(os.path.join(d, "templates", "palette.json"), "{}\n")
    write(os.path.join(d, "scripts", "count.py"), '"""%s\n\nMore detail."""\nprint(1)\n' % script_doc)
    write(os.path.join(d, "scripts", "notes.txt"), "not a script\n")
    return d


class StagingTest(unittest.TestCase):
    def test_tools_layout_keeps_scripts_and_data_and_drops_instructions(self):
        with workdir() as skill, workdir() as ws:
            fake_skill(skill)
            with mock.patch.object(catalog, "skill_dir", return_value=skill):
                dest = run_bench.stage_skill("widgets", ws, "tools")
            got = sorted(os.path.relpath(os.path.join(b, n), dest) for b, _, ns in os.walk(dest) for n in ns)
            self.assertEqual(got, ["scripts/count.py", "scripts/notes.txt", "templates/palette.json"])

    def test_full_layout_keeps_the_instructions_but_not_the_evals(self):
        with workdir() as skill, workdir() as ws:
            fake_skill(skill)
            with mock.patch.object(catalog, "skill_dir", return_value=skill):
                dest = run_bench.stage_skill("widgets", ws, "full")
            self.assertTrue(os.path.isfile(os.path.join(dest, "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(dest, "reference.md")))
            self.assertFalse(os.path.exists(os.path.join(dest, "evals")))

    def test_a_real_skill_whose_script_reads_templates_still_has_them(self):
        with workdir() as ws:
            dest = run_bench.stage_skill("deck-builder", ws, "tools")
            self.assertTrue(os.path.isfile(os.path.join(dest, "templates", "palettes.json")))
            self.assertFalse(os.path.exists(os.path.join(dest, "SKILL.md")))
            r = subprocess.run([sys.executable, os.path.join(dest, "scripts", "build_deck.py"), "--help"],
                               capture_output=True, text=True)
            self.assertNotIn("Traceback", r.stderr)


class ToolsSystemTest(unittest.TestCase):
    def test_lists_each_script_with_its_first_docstring_line_and_none_of_the_rules(self):
        with workdir() as skill:
            fake_skill(skill)
            with mock.patch.object(catalog, "skill_dir", return_value=skill):
                text = run_bench.tools_system("widgets")
        self.assertIn("- skills/widgets/scripts/count.py: Count the widgets in a CSV.", text)
        self.assertNotIn("notes.txt", text)
        self.assertNotIn("More detail", text)
        for leaked in ("ALWAYS-LEAD-WITH-THE-TOTAL", "REFERENCE-ONLY", "EXAMPLE text"):
            self.assertNotIn(leaked, text)
        self.assertIn("--help", text)

    def test_has_scripts(self):
        self.assertTrue(run_bench.has_scripts("context-graph"))
        self.assertFalse(run_bench.has_scripts("adr-generator"))

    def test_a_changed_script_changes_the_cache_key(self):
        with workdir() as skill:
            fake_skill(skill)
            with mock.patch.object(catalog, "skill_dir", return_value=skill):
                before = run_bench.scripts_digest("widgets")
                write(os.path.join(skill, "SKILL.md"), "an edit to the instructions only\n")
                self.assertEqual(run_bench.scripts_digest("widgets"), before)
                write(os.path.join(skill, "scripts", "count.py"), '"""Changed."""\n')
                self.assertNotEqual(run_bench.scripts_digest("widgets"), before)

    def test_the_arms_offered(self):
        md = "# skill text"
        with mock.patch.object(run_bench, "BACKEND", "claude-cli"), mock.patch.object(run_bench, "TOOLS_ARM", True):
            self.assertEqual([a for a, _ in run_bench.arm_systems("context-graph", md)], ["skill", "baseline", "tools"])
            self.assertEqual([a for a, _ in run_bench.arm_systems("adr-generator", md)], ["skill", "baseline"])
        with mock.patch.object(run_bench, "BACKEND", "claude-cli"), mock.patch.object(run_bench, "TOOLS_ARM", False):
            self.assertEqual([a for a, _ in run_bench.arm_systems("context-graph", md)], ["skill", "baseline"])


def row(skill, ev, met_skill, met_tools, met_base, pair, tools_vs, skill_vs, two=True):
    def grades(n):
        return [{"pass": i < n} for i in range(4)]
    arm = lambda n: {"output": "", "grades": grades(n), "cost": 0.1, "usage": {"output_tokens": 10}, "stop_reason": "end_turn"}
    r = {"skill": skill, "eval": ev, "model": "m", "trial": 0,
         "arms": {"skill": arm(met_skill), "tools": arm(met_tools), "baseline": arm(met_base)},
         "pairwise": {"winner": pair}, "tools_vs_baseline": {"winner": tools_vs}, "skill_vs_tools": {"winner": skill_vs}}
    if two:
        r.update({"pairwise2": {"winner": pair}, "tools_vs_baseline2": {"winner": tools_vs},
                  "skill_vs_tools2": {"winner": skill_vs}})
    return r


class ReadingTest(unittest.TestCase):
    def test_reading(self):
        self.assertEqual(run_bench.reading(1.0, 0.5, 1.0), "instructions help")
        self.assertEqual(run_bench.reading(0.5, 1.0, 0.0), "the scripts carry it")
        self.assertEqual(run_bench.reading(0.0, 0.0, 0.5), "the plain agent is preferred")
        self.assertEqual(run_bench.reading(0.5, 0.5, 0.5), "mixed")
        self.assertIsNone(run_bench.reading(0.5, None, None))

    def test_summary_and_report(self):
        rows = [row("alpha", 1, 4, 2, 1, "skill", "tools", "skill"),
                row("alpha", 2, 3, 2, 2, "skill", "baseline", "skill"),
                row("beta", 1, 2, 3, 2, "baseline", "tools", "tools"),
                row("gamma", 1, 1, 1, 3, "baseline", "baseline", "tie")]
        with mock.patch.object(run_bench, "held_out_ids", return_value=set()), \
                mock.patch.object(run_bench, "SECOND_JUDGE", "judge-2"):
            s = run_bench.summarize(rows, [], ["m"], {"m": "standard"}, 0.05)
            md = run_bench.report(s, "judge-1", 1, 1.0, {"alpha", "beta", "gamma"})
        t = s["models"]["m"]["tools"]
        self.assertEqual((t["evals"], t["skills"]), (4, 3))
        self.assertAlmostEqual(t["tools"], (0.5 + 0.5 + 0.75 + 0.25) / 4)
        self.assertAlmostEqual(t["win_skill_vs_tools"], (1 + 1 + 0 + 0.5) / 4)
        by = {r["skill"]: r for r in s["skills"]}
        self.assertEqual(by["alpha"]["reading"], "instructions help")
        self.assertEqual(by["beta"]["reading"], "the scripts carry it")
        self.assertEqual(by["gamma"]["reading"], "the plain agent is preferred")
        self.assertIn("## The scripts without the instructions (`m`)", md)
        self.assertIn("| Assertions met | 62% | 50% | 50% |", md)
        self.assertIn("1 instructions help", md)
        self.assertIn("| `gamma` | 1 | 25% / 25% / 75% | 0% / 0% | 0% / 0% | 50% / 50% | the plain agent is preferred |", md)

    def test_judges_that_disagree_read_mixed(self):
        r = row("alpha", 1, 4, 2, 1, "skill", "tools", "skill")
        r["skill_vs_tools2"] = {"winner": "tools"}
        with mock.patch.object(run_bench, "held_out_ids", return_value=set()):
            s = run_bench.summarize([r], [], ["m"], {"m": "standard"}, 0.05)
        self.assertEqual(s["skills"][0]["reading"], "mixed")

    def test_a_run_without_the_tools_arm_reports_no_tools_section(self):
        r = row("alpha", 1, 4, 2, 1, "skill", "tools", "skill")
        for k in ("tools_vs_baseline", "skill_vs_tools", "tools_vs_baseline2", "skill_vs_tools2"):
            del r[k]
        del r["arms"]["tools"]
        with mock.patch.object(run_bench, "held_out_ids", return_value=set()):
            s = run_bench.summarize([r], [], ["m"], {"m": "standard"}, 0.05)
            md = run_bench.report(s, "judge-1", 1, 1.0, set())
        self.assertNotIn("tools", s["models"]["m"])
        self.assertNotIn("reading", s["skills"][0])
        self.assertNotIn("scripts without the instructions", md)


class EstimateTest(unittest.TestCase):
    def test_the_second_judge_and_the_tools_arm_cost_more(self):
        ev = next(e for e in run_bench.load("context-graph", "evals.json")["evals"] if e["id"] == 16)
        units = [("context-graph", ev, "claude-sonnet-5-5", 0)]
        with mock.patch.object(run_bench, "BACKEND", "claude-cli"):
            with mock.patch.object(run_bench, "SECOND_JUDGE", None), mock.patch.object(run_bench, "TOOLS_ARM", False):
                one, _ = run_bench.estimate(units, [], "claude-sonnet-5-5")
            with mock.patch.object(run_bench, "SECOND_JUDGE", "claude-opus-5-5"), mock.patch.object(run_bench, "TOOLS_ARM", False):
                two, _ = run_bench.estimate(units, [], "claude-sonnet-5-5")
            with mock.patch.object(run_bench, "SECOND_JUDGE", "claude-opus-5-5"), mock.patch.object(run_bench, "TOOLS_ARM", True):
                three, _ = run_bench.estimate(units, [], "claude-sonnet-5-5")
        self.assertLess(one, two)
        self.assertLess(two, three)

    def test_fixture_files_and_git_history_count(self):
        self.assertGreater(run_bench.fixture_tokens("context-graph", 16), 1000)
        self.assertEqual(run_bench.fixture_tokens("adr-generator", 999), 0)


class FlagTest(unittest.TestCase):
    def test_tools_arm_refuses_the_api_backend(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "run_bench.py"), "--tools-arm", "--dry-run"],
                           capture_output=True, text=True, cwd=ROOT)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--tools-arm needs --backend claude-cli", r.stderr)


if __name__ == "__main__":
    unittest.main()

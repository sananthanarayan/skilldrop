"""run_bench.py's loop benchmark: what each arm is given, how it is cached, judged and read (RFC-0070)."""
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

from tests.support import ROOT, workdir, write

sys.path.insert(0, ROOT)
import catalog  # noqa: E402
import run_bench  # noqa: E402


def fake_catalogue(root):
    """A loop with two stage skills and a wrapper's `*` stage, and a skill no stage runs."""
    loop = os.path.join(root, "loops", "tidy")
    write(os.path.join(loop, "LOOP.md"), "---\nname: tidy\n---\n# tidy\n\nGATE-G99-NEVER-SKIP rule.\n")
    write(os.path.join(loop, "loop.json"), json.dumps({"name": "tidy", "stages": [
        {"id": "a", "skills": ["sorter"]}, {"id": "b", "skills": ["*"]},
        {"id": "c", "skills": ["checker", "sorter"]}]}))
    write(os.path.join(loop, "evals", "evals.json"), json.dumps({"loop_name": "tidy", "evals": [
        {"id": "one", "prompt": "Tidy this.", "assertions": ["Tidies it"]},
        {"id": "two", "held_out": "2026-11-03", "prompt": "Tidy that.", "assertions": ["Tidies that"]}]}))
    write(os.path.join(loop, "evals", "files", "one", "input.txt"), "mess\n")
    skills = {}
    for name, desc in (("sorter", "Sort a list of things."), ("checker", "Check the sorted list."),
                       ("unused", "Never staged.")):
        d = os.path.join(root, "skills", name)
        write(os.path.join(d, "SKILL.md"), "---\nname: %s\n---\n# %s\n\nSKILL-BODY-%s\n" % (name, name, name))
        write(os.path.join(d, "manifest.json"), json.dumps({"name": name, "description": desc}))
        write(os.path.join(d, "evals", "evals.json"), '{"evals": []}\n')
        skills[name] = d
    return loop, skills


class FakeCatalogue(object):
    """Point catalog at the fake loop and skills for the length of a test."""

    def __init__(self):
        self.ctx = workdir()

    def __enter__(self):
        self.root = self.ctx.__enter__()
        self.loop, self.skills = fake_catalogue(self.root)
        self.patches = [mock.patch.object(catalog, "loop_dir", side_effect=lambda n: self.loop if n == "tidy" else None),
                        mock.patch.object(catalog, "skill_dir", side_effect=lambda n: self.skills.get(n))]
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self.patches:
            p.stop()
        return self.ctx.__exit__(*exc)


class ArmsTest(unittest.TestCase):
    def test_stage_skills_are_in_order_once_and_skip_the_wrapper_star(self):
        with FakeCatalogue():
            self.assertEqual(run_bench.loop_skills("tidy"), ["sorter", "checker"])

    def test_the_stages_arm_lists_each_skill_with_its_description_and_none_of_the_loop(self):
        with FakeCatalogue():
            text = run_bench.stages_system("tidy")
        self.assertIn("- skills/sorter/SKILL.md: Sort a list of things.", text)
        self.assertIn("- skills/checker/SKILL.md: Check the sorted list.", text)
        self.assertNotIn("unused", text)
        for leaked in ("GATE-G99-NEVER-SKIP", "tidy", "SKILL-BODY"):
            self.assertNotIn(leaked, text)
        self.assertTrue(text.startswith(run_bench.NONINTERACTIVE))

    def test_the_loop_arm_carries_loop_md_and_says_where_everything_is(self):
        with FakeCatalogue() as f:
            md = open(os.path.join(f.loop, "LOOP.md"), encoding="utf-8").read()
            text = run_bench.loop_system("tidy", md)
        self.assertIn("GATE-G99-NEVER-SKIP", text)
        self.assertIn("skills/tidy/", text)
        self.assertIn("skills/sorter/, skills/checker/", text)

    def test_three_arms_and_only_the_baseline_stages_nothing(self):
        with FakeCatalogue():
            arms = run_bench.loop_arms("tidy", "# loop")
        self.assertEqual([a for a, _, _, _ in arms], ["loop", "stages", "baseline"])
        self.assertEqual(arms[2][1], run_bench.NONINTERACTIVE)
        self.assertIsNone(arms[2][2])
        self.assertIsNone(arms[2][3])


class StagingTest(unittest.TestCase):
    def listing(self, ws):
        return sorted(os.path.relpath(os.path.join(b, n), ws).replace(os.sep, "/")
                      for b, _, ns in os.walk(ws) for n in ns)

    def test_the_loop_arm_gets_the_loop_and_every_stage_skill_without_evals(self):
        with FakeCatalogue(), workdir() as ws:
            dest = run_bench.stage_loop("tidy", ws, True)
            self.assertEqual(dest, os.path.join(ws, "skills", "tidy"))
            self.assertEqual(self.listing(ws), ["skills/checker/SKILL.md", "skills/checker/manifest.json",
                                                "skills/sorter/SKILL.md", "skills/sorter/manifest.json",
                                                "skills/tidy/LOOP.md", "skills/tidy/loop.json"])

    def test_the_stages_arm_gets_the_skills_and_no_loop(self):
        with FakeCatalogue(), workdir() as ws:
            self.assertIsNone(run_bench.stage_loop("tidy", ws, False))
            got = self.listing(ws)
        self.assertFalse(any(p.startswith("skills/tidy/") for p in got))
        self.assertIn("skills/sorter/SKILL.md", got)

    def test_loop_evals_and_fixtures(self):
        with FakeCatalogue():
            self.assertEqual([e["id"] for e in run_bench.loop_evals("tidy")], ["one", "two"])
            self.assertTrue(os.path.isfile(os.path.join(run_bench.loop_fixtures("tidy", "one"), "input.txt")))
            self.assertIsNone(run_bench.loop_fixtures("tidy", "two"))

    def test_no_stage_skill_with_requirements_means_no_environment(self):
        with FakeCatalogue() as f:
            self.assertIsNone(run_bench.loop_env_skill("tidy"))
            write(os.path.join(f.skills["checker"], "requirements.txt"), "# nothing\n")
            self.assertEqual(run_bench.loop_env_skill("tidy"), "checker")


class CacheTest(unittest.TestCase):
    def test_editing_loop_md_or_a_stage_skill_changes_the_key_and_evals_do_not(self):
        with FakeCatalogue() as f:
            before = run_bench.loop_digest("tidy")
            write(os.path.join(f.loop, "evals", "evals.json"), '{"evals": []}\n')
            write(os.path.join(f.skills["unused"], "SKILL.md"), "changed, but no stage runs it\n")
            self.assertEqual(run_bench.loop_digest("tidy"), before)
            write(os.path.join(f.loop, "LOOP.md"), "an edited loop\n")
            after_loop = run_bench.loop_digest("tidy")
            self.assertNotEqual(after_loop, before)
            write(os.path.join(f.skills["checker"], "SKILL.md"), "an edited stage skill\n")
            self.assertNotEqual(run_bench.loop_digest("tidy"), after_loop)

    def test_the_loop_and_stages_arms_never_share_a_cache_entry(self):
        with FakeCatalogue():
            arms = run_bench.loop_arms("tidy", "# loop")
        keys = {run_bench.cache_path("gen", "m", system, "Tidy this.", 0, None, key) for _, system, _, key in arms}
        self.assertEqual(len(keys), 3)


def row(lp, ev, met_loop, met_stages, met_base, pair, loop_vs, stages_vs, two=True, held=False):
    def grades(n):
        return [{"pass": i < n} for i in range(4)]
    arm = lambda n: {"output": "", "grades": grades(n), "cost": 0.1, "usage": {"output_tokens": 10}, "stop_reason": "end_turn"}
    r = {"loop": lp, "eval": ev, "model": "m", "trial": 0, "held_out": held,
         "arms": {"loop": arm(met_loop), "stages": arm(met_stages), "baseline": arm(met_base)},
         "pairwise": {"winner": pair}, "loop_vs_stages": {"winner": loop_vs}, "stages_vs_baseline": {"winner": stages_vs}}
    if two:
        r.update({"pairwise2": {"winner": pair}, "loop_vs_stages2": {"winner": loop_vs},
                  "stages_vs_baseline2": {"winner": stages_vs}})
    return r


class ReadingTest(unittest.TestCase):
    def test_loop_reading(self):
        self.assertEqual(run_bench.loop_reading(1.0, 0.5, 1.0), "the order helps")
        self.assertEqual(run_bench.loop_reading(0.5, 1.0, 0.0), "the skills carry it")
        self.assertEqual(run_bench.loop_reading(0.0, 0.0, 0.5), "the plain agent is preferred")
        self.assertEqual(run_bench.loop_reading(0.5, 0.5, 0.5), "mixed")

    def test_summary_and_report(self):
        rows = [row("alpha", 1, 4, 2, 1, "loop", "loop", "stages", held=True),
                row("alpha", 2, 3, 2, 2, "loop", "loop", "baseline"),
                row("beta", 1, 2, 3, 2, "baseline", "stages", "stages"),
                row("gamma", 1, 1, 1, 3, "baseline", "tie", "baseline")]
        with mock.patch.object(run_bench, "SECOND_JUDGE", "judge-2"):
            s = run_bench.summarize_loops(rows, [], ["m"], {"m": "standard"})
            md = run_bench.report_loops(s, "judge-1", 1, 1.0)
        d = s["models"]["m"]
        self.assertEqual((d["evals"], d["loops"], d["held_out_evals"]), (4, 3, 1))
        self.assertAlmostEqual(d["stages"], (0.5 + 0.5 + 0.75 + 0.25) / 4)
        self.assertAlmostEqual(d["win_loop_vs_stages"], (1 + 1 + 0 + 0.5) / 4)
        by = {r["loop"]: r for r in s["loops"]}
        self.assertEqual(by["alpha"]["reading"], "the order helps")
        self.assertEqual(by["beta"]["reading"], "the skills carry it")
        self.assertEqual(by["gamma"]["reading"], "the plain agent is preferred")
        self.assertIn("| Assertions met | 62% | 50% | 50% |", md)
        self.assertIn("1 of them held out", md)
        self.assertIn("| `gamma` | 1 | 25% / 25% / 75% | 0% / 0% | 50% / 50% | 0% / 0% | the plain agent is preferred |", md)

    def test_judges_that_disagree_read_mixed(self):
        r = row("alpha", 1, 4, 2, 1, "loop", "loop", "stages")
        r["loop_vs_stages2"] = {"winner": "stages"}
        s = run_bench.summarize_loops([r], [], ["m"], {"m": "standard"})
        self.assertEqual(s["loops"][0]["reading"], "mixed")

    def test_no_held_out_eval_is_called_a_smoke_test(self):
        s = run_bench.summarize_loops([row("alpha", 1, 4, 2, 1, "loop", "loop", "stages", two=False)], [], ["m"],
                                      {"m": "standard"})
        md = run_bench.report_loops(s, "judge-1", 1, 0.0)
        self.assertIn("read this as a smoke test, not a result", md)


class EstimateTest(unittest.TestCase):
    def test_a_second_judge_costs_more(self):
        with FakeCatalogue():
            units = [("tidy", e, "claude-sonnet-5-5", 0) for e in run_bench.loop_evals("tidy")]
            with mock.patch.object(run_bench, "SECOND_JUDGE", None):
                one, fresh = run_bench.estimate_loops(units, [], "claude-sonnet-5-5")
            with mock.patch.object(run_bench, "SECOND_JUDGE", "claude-opus-5-5"):
                two, _ = run_bench.estimate_loops(units, [], "claude-sonnet-5-5")
        self.assertLess(one, two)
        self.assertLessEqual(fresh, 6)


class HeldOutFilterTest(unittest.TestCase):
    def test_through_a_date_keeps_held_out_evals_up_to_that_day(self):
        evals = [("a", {"id": 1}), ("a", {"id": 2, "held_out": "2026-10-18"}),
                 ("a", {"id": 3, "held_out": "2026-10-20"}), ("b", {"id": 4, "held_out": True})]
        args = type("A", (), {"held_out": False, "held_out_through": "2026-10-18"})()
        self.assertEqual([e["id"] for _, e in run_bench.held_out_filter(evals, args)], [2, 4])
        args.held_out_through, args.held_out = None, True
        self.assertEqual([e["id"] for _, e in run_bench.held_out_filter(evals, args)], [2, 3, 4])
        args.held_out = False
        self.assertEqual(len(run_bench.held_out_filter(evals, args)), 4)


class AllowBashTest(unittest.TestCase):
    def test_allow_bash_changes_the_generation_key_and_nothing_else(self):
        with mock.patch.object(run_bench, "BACKEND", "claude-cli"):
            with mock.patch.object(run_bench, "ALLOW_BASH", False):
                gen, jud = (run_bench.cache_path(k, "m", "s", "u", 0) for k in ("gen", "judge"))
            with mock.patch.object(run_bench, "ALLOW_BASH", True):
                gen2, jud2 = (run_bench.cache_path(k, "m", "s", "u", 0) for k in ("gen", "judge"))
        self.assertNotEqual(gen, gen2)
        self.assertEqual(jud, jud2)
        self.assertIn('"allow": ["Bash"]', run_bench.CLI_SANDBOX_ALLOW_BASH)


class FlagTest(unittest.TestCase):
    def run_bench(self, *args):
        return subprocess.run([sys.executable, os.path.join(ROOT, "run_bench.py")] + list(args) + ["--dry-run"],
                              capture_output=True, text=True, cwd=ROOT)

    def test_loops_refuse_the_api_backend(self):
        r = self.run_bench("--loops", "research")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--loops needs --backend claude-cli", r.stderr)

    def test_loops_refuse_skills_and_the_tools_arm(self):
        for extra in (["--skills", "adr-generator"], ["--tools-arm"]):
            r = self.run_bench("--backend", "claude-cli", "--loops", "research", *extra)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("can't be combined", r.stderr)

    def test_allow_bash_refuses_the_api_backend(self):
        r = self.run_bench("--allow-bash", "--skills", "adr-generator")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--allow-bash needs --backend claude-cli", r.stderr)

    def test_an_unknown_loop_is_named(self):
        r = self.run_bench("--backend", "claude-cli", "--loops", "no-such-loop")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown loop(s): no-such-loop", r.stderr)

    def test_a_dry_run_counts_three_arms_per_eval(self):
        r = self.run_bench("--backend", "claude-cli", "--loops", "research", "--evals", "blocked-without-a-decision")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 loop eval(s) (0 held out) across 1 loop(s)", r.stdout)
        self.assertIn("3 generations", r.stdout)
        self.assertIn("3 pairwise judgements", r.stdout)


if __name__ == "__main__":
    unittest.main()

import json
import os
import random
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "judge-audit", "judge_stats.py"

# 20 posts; the expert marks p1-p4 as violations. Run 1 flags p1 p2 p3 p5, run 2 flags p1 p2 p4 p5 p6.
POSTS = ["p%d" % i for i in range(1, 21)]
GOLD = "item_id,label\n" + "".join("%s,%s\n" % (p, "violation" if p in ("p1", "p2", "p3", "p4") else "ok")
                                   for p in POSTS)
RUN1 = "id,flagged\n" + "".join("%s,%s\n" % (p, str(p in ("p1", "p2", "p3", "p5")).lower()) for p in POSTS)
RUN2 = "id,flagged\n" + "".join("%s,%s\n" % (p, str(p in ("p1", "p2", "p4", "p5", "p6")).lower())
                                for p in reversed(POSTS))
RUNS = ("run_1.csv", "run_2.csv", "--gold", "gold.csv", "--map", "true=violation,false=ok",
        "--positive", "violation")

# 1-5 scores: the judge matches the expert on v1 and over-scores three of four v2 answers by one point.
GRADES = ("item,version,score,expert\n"
          "a1,v1,4,4\na2,v1,3,3\na3,v1,2,2\na4,v1,5,5\n"
          "b1,v2,5,4\nb2,v2,4,3\nb3,v2,5,4\nb4,v2,3,3\n")

# Pairwise: `new` is shown first on q1-q3, `old` on q4-q10; the first-shown answer wins q1-q7.
PAIRS = "question_id,judge,winner,first_shown\n" + "".join(
    "q{0},j1,{1},{2}\n".format(i, "new" if i <= 3 or i >= 8 else "old", "new" if i <= 3 else "old")
    for i in range(1, 11))


class JudgeStatsMathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def test_cohen_kappa_corrects_for_chance(self):
        # each rater says pass 9 of 10 times: chance agreement 0.82, observed 0.8
        pairs = [("pass", "pass")] * 8 + [("pass", "fail"), ("fail", "pass")]
        k, po, pe = self.m.cohen(pairs)
        self.assertAlmostEqual(po, 0.8)
        self.assertAlmostEqual(pe, 0.82)
        self.assertAlmostEqual(k, -0.02 / 0.18)

    def test_cohen_kappa_undefined_when_everyone_says_one_label(self):
        self.assertEqual(self.m.cohen([("pass", "pass")] * 5), (None, 1.0, 1.0))
        self.assertEqual(self.m.cohen([]), (None, None, None))

    def test_quadratic_kappa_penalises_far_disagreement(self):
        pairs = [(1, 1), (2, 2), (3, 3), (1, 3)]
        self.assertAlmostEqual(self.m.weighted_kappa(pairs, "quadratic"), 5 / 13)
        self.assertAlmostEqual(self.m.cohen(pairs)[0], 7 / 11)

    def test_fleiss_kappa_three_raters(self):
        table = [["a", "a", "a"], ["a", "a", "b"], ["b", "b", "b"]]
        self.assertAlmostEqual(self.m.fleiss(table), 0.55)

    def test_wilson_interval_bounds(self):
        lo, hi = self.m.wilson(3, 5)
        self.assertAlmostEqual(lo, 0.2307, places=3)
        self.assertAlmostEqual(hi, 0.8824, places=3)
        self.assertEqual(self.m.wilson(0, 10)[0], 0.0)
        self.assertAlmostEqual(self.m.wilson(10, 10)[1], 1.0)
        self.assertIsNone(self.m.wilson(0, 0))

    def test_rare_class_metrics_beside_majority_baseline(self):
        # 120 posts, 6 violations: caught 4, flagged 2 fine posts
        pairs = [("v", "v")] * 4 + [("o", "v")] * 2 + [("v", "o")] * 2 + [("o", "o")] * 112
        cm = self.m.class_metrics(pairs, "v", 0, random.Random(1))
        self.assertEqual((cm["tp"], cm["fp"], cm["fn"], cm["tn"]), (4, 2, 2, 112))
        self.assertEqual(cm["expert_positives"], 6)
        self.assertAlmostEqual(cm["recall"]["rate"], 4 / 6)
        self.assertAlmostEqual(cm["precision"]["rate"], 4 / 6)
        self.assertAlmostEqual(cm["false_positive_rate"]["rate"], 2 / 114)
        self.assertAlmostEqual(cm["majority_baseline"], 0.95)
        self.assertEqual(cm["majority_label"], "o")

    def test_ranks_average_ties_and_spearman(self):
        self.assertEqual(self.m.ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])
        self.assertAlmostEqual(self.m.spearman([(1, 10), (2, 20), (3, 15), (4, 40)]), 0.8)
        self.assertIsNone(self.m.spearman([(1, 1), (2, 2)]))

    def test_natural_sort(self):
        self.assertEqual(sorted(["R10", "R2", "R1"], key=self.m.natural), ["R1", "R2", "R10"])

    def test_norm_label(self):
        self.assertEqual(self.m.norm_label(" PASS "), "pass")
        self.assertEqual(self.m.norm_label("4.0"), "4")
        self.assertEqual(self.m.norm_label("Violation"), "Violation")

    def test_positive_class_defaults(self):
        self.assertEqual(self.m.positive_class({"pass", "fail"}, None), "pass")
        self.assertIsNone(self.m.positive_class({"violation", "ok"}, None))
        self.assertEqual(self.m.positive_class({"Violation", "ok"}, "violation"), "Violation")

    def test_group_value_splits_numeric_column(self):
        col, thr = self.m.parse_group("Tokens>=400")
        self.assertEqual((col, thr), ("tokens", 400.0))
        self.assertEqual(self.m.group_value({"tokens": "399"}, col, thr), "tokens<400")
        self.assertEqual(self.m.group_value({"tokens": "400"}, col, thr), "tokens>=400")
        self.assertEqual(self.m.group_value({"tokens": ""}, col, thr), "(blank)")

    def test_parse_gate_forms(self):
        self.assertEqual(self.m.parse_gate("recall>=90%")["value"], 0.9)
        self.assertEqual(self.m.parse_gate("recall >= 90")["value"], 0.9)
        g = self.m.parse_gate("diff=2")
        self.assertEqual((g["metric"], g["op"], g["value"]), ("bias_diff", "<=", 2.0))
        self.assertEqual(self.m.parse_gate("fp<=0")["metric"], "false_positives")

    def test_judge_gate_clears_fails_cant_tell(self):
        g = self.m.parse_gate("recall>=0.9")
        self.assertEqual(self.m.judge_gate(g, 0.97, [0.92, 0.99]), "clears")
        self.assertEqual(self.m.judge_gate(g, 0.6, [0.23, 0.88]), "fails")
        self.assertTrue(self.m.judge_gate(g, 0.95, [0.8, 0.99]).startswith("can't tell: the point estimate meets it"))
        self.assertEqual(self.m.judge_gate(g, None, None), "not measurable")

    def test_judge_gate_on_absolute_bias(self):
        g = self.m.parse_gate("bias<=1.0")
        self.assertEqual(self.m.judge_gate(g, -0.5, [-0.8, -0.2]), "clears")
        self.assertTrue(self.m.judge_gate(g, 0.1, [-1.5, 0.3]).startswith("can't tell"))
        self.assertEqual(self.m.judge_gate(g, 2.0, [1.5, 2.5]), "fails")


class JudgeStatsCliTest(unittest.TestCase):
    def stats(self, files, *args, as_json=True):
        with workdir() as d:
            for name, text in files.items():
                write(os.path.join(d, name), text)
            extra = ["--json", "--boot", "0"] if as_json else ["--boot", "0"]
            code, out, err = run(SKILL, SCRIPT, *args, *extra, cwd=d)
        if as_json and code == 0:
            return code, json.loads(out), err
        return code, out, err

    def runs(self, *gates):
        return self.stats({"run_1.csv": RUN1, "run_2.csv": RUN2, "gold.csv": GOLD}, *RUNS, *gates)

    # --- two runs of a rare-class judge, joined on id -----------------------------------

    def test_each_run_reported_separately(self):
        code, o, err = self.runs()
        self.assertEqual(code, 0, err)
        self.assertEqual(o["positive_label"], "violation")
        by_trial = o["vs_expert"]["judge"]["by_trial"]
        c1, c2 = by_trial["1"]["classes"], by_trial["2"]["classes"]
        self.assertEqual((c1["tp"], c1["fp"], c1["fn"], c1["tn"]), (3, 1, 1, 15))
        self.assertEqual((c2["tp"], c2["fp"], c2["fn"], c2["tn"]), (3, 2, 1, 14))
        self.assertEqual(c1["expert_positives"], 4)
        self.assertEqual(o["trial_names"], {"1": "run_1.csv", "2": "run_2.csv"})

    def test_flips_joined_on_item_id_not_line_order(self):
        code, o, err = self.runs()
        st = o["stability"]["judge"]
        self.assertEqual((st["items_with_repeats"], st["flipped"]), (20, 3))
        self.assertEqual(st["flipped_items"], ["p3", "p4", "p6"])
        rt = st["retest"][0]
        self.assertEqual(rt["agreed"], 17)
        self.assertEqual(rt["expert_positive_flips"], ["p3", "p4"])
        self.assertEqual(rt["positive_in_both"], ["p1", "p2", "p5"])
        self.assertEqual(rt["expert_positive_missed_in_both"], [])
        self.assertTrue(any("different order" in w for w in o["warnings"]))

    def test_gate_per_run_on_counts_and_rates(self):
        code, o, err = self.runs("--gate", "false_positives<=1", "--gate", "recall>=0.9")
        self.assertEqual(code, 0, err)
        fp, rec = o["gates"]
        self.assertEqual([(r["run"], r["outcome"]) for r in fp["results"]], [("1", "clears"), ("2", "fails")])
        # recall 3/4 with a Wilson interval of about 30%-95%: spans 90%
        self.assertTrue(all(r["outcome"].startswith("can't tell: the point estimate misses it")
                            for r in rec["results"]))

    def test_unmapped_labels_flagged_as_sharing_nothing_with_expert(self):
        code, o, err = self.stats({"run_1.csv": RUN1, "gold.csv": GOLD}, "run_1.csv", "--gold", "gold.csv")
        self.assertEqual(code, 0, err)
        self.assertTrue(any("share no value with the expert labels" in f for f in o["flags"]))

    def test_markdown_report_has_run_table(self):
        code, out, err = self.stats({"run_1.csv": RUN1, "run_2.csv": RUN2, "gold.csv": GOLD}, *RUNS,
                                    as_json=False)
        self.assertEqual(code, 0, err)
        self.assertIn("### Against the expert on `violation`, per judge and run", out)
        self.assertIn("| judge | run 1 (run_1.csv) | 20 |", out)
        self.assertIn("p3 (violation → ok, expert violation)", out)

    # --- ordinal scores grouped by the compared variable --------------------------------

    def test_group_by_exposes_bias_that_differs_by_variant(self):
        code, o, err = self.stats({"grades.csv": GRADES}, "grades.csv", "--group-by", "version")
        self.assertEqual(code, 0, err)
        self.assertEqual(o["scale"], "ordinal")
        self.assertEqual(o["groups"]["v1"]["vs_expert"]["judge"]["all"]["bias"], 0.0)
        self.assertAlmostEqual(o["groups"]["v2"]["vs_expert"]["judge"]["all"]["bias"], 0.75)
        cmp = o["group_compare"][0]
        self.assertEqual((cmp["group"], cmp["reference"]), ("v2", "v1"))
        e = cmp["by_judge"]["judge"]
        self.assertAlmostEqual(e["bias_diff"], 0.75)
        self.assertAlmostEqual(e["judge_mean_all_rows_diff"], 0.75)
        self.assertAlmostEqual(e["expert_mean_diff"], 0.0)

    def test_pooled_ordinal_agreement(self):
        code, o, err = self.stats({"grades.csv": GRADES}, "grades.csv")
        r = o["vs_expert"]["judge"]["all"]
        self.assertEqual((r["n"], r["exact"], r["within_one"], r["judge_higher"], r["judge_lower"]), (8, 5, 8, 3, 0))
        self.assertAlmostEqual(r["bias"], 0.375)
        self.assertAlmostEqual(r["judge_mean"], 3.875)
        self.assertAlmostEqual(r["expert_mean"], 3.5)

    def test_bias_diff_gate_fails_against_users_tolerance(self):
        code, o, err = self.stats({"grades.csv": GRADES}, "grades.csv", "--group-by", "version",
                                  "--gate", "bias_diff<=0.5")
        res = o["gates"][0]["results"]
        self.assertEqual([(r["run"], r["outcome"]) for r in res], [("v2 minus v1", "fails")])

    def test_bias_diff_gate_needs_group_by(self):
        code, o, err = self.stats({"grades.csv": GRADES}, "grades.csv", "--gate", "bias_diff<=0.5")
        self.assertEqual(o["gates"][0]["note"], "bias_diff needs --group-by")

    def test_threshold_turns_scores_into_pass_fail(self):
        code, o, err = self.stats({"grades.csv": GRADES}, "grades.csv", "--threshold", "4")
        self.assertEqual(code, 0, err)
        self.assertEqual(o["scale"], "nominal")
        self.assertEqual(o["positive_label"], "pass")
        fp = o["vs_expert"]["judge"]["all"]["false_pass"]
        self.assertEqual((fp["k"], fp["n"]), (1, 4))  # expert fails a2 a3 b2 b4; judge passes b2 (4 vs 3)

    # --- pairwise position bias ---------------------------------------------------------

    def test_position_bias_counted_and_order_balanced(self):
        code, o, err = self.stats({"pairs.csv": PAIRS}, "pairs.csv")
        self.assertEqual(code, 0, err)
        a = o["pairwise"]["all_judges"]
        self.assertEqual((a["first_shown_won"], a["second_shown_won"], a["order_known"]), (7, 3, 10))
        new, old = a["by_variant"]["new"], a["by_variant"]["old"]
        self.assertEqual((new["shown_first"], new["wins_when_first"], new["wins_when_second"]), (3, 3, 3))
        self.assertAlmostEqual(new["raw_win_rate"], 0.6)
        self.assertAlmostEqual(new["order_balanced_win_rate"], (1 + 3 / 7) / 2)
        self.assertAlmostEqual(old["order_balanced_win_rate"], (4 / 7) / 2)
        self.assertEqual(o["pairwise"]["order_by_item"], {"always new": 3, "always old": 7})
        self.assertTrue(any("`new` was shown first in 3 of 10" in f for f in o["flags"]))
        self.assertTrue(any(f.startswith("no expert labels") for f in o["flags"]))

    # --- several judges -----------------------------------------------------------------

    def test_wide_judges_compared_with_expert_and_each_other(self):
        wide = "item,expert,big,small\ni1,pass,pass,pass\ni2,pass,pass,fail\ni3,fail,fail,fail\ni4,fail,pass,pass\n"
        code, o, err = self.stats({"wide.csv": wide}, "wide.csv", "--judges", "big,small")
        self.assertEqual(code, 0, err)
        self.assertEqual(o["vs_expert"]["big"]["all"]["exact"], 3)
        self.assertEqual(o["vs_expert"]["small"]["all"]["exact"], 2)
        fp = o["vs_expert"]["big"]["all"]["false_pass"]
        self.assertEqual((fp["k"], fp["n"]), (1, 2))
        row = o["between_judges"][0]
        self.assertEqual(row["judges"], ["big", "small"])
        self.assertAlmostEqual(row["all"]["agreement"], 0.75)
        self.assertEqual(row["shared_errors"], {"agreed_on_expert_items": 3, "both_wrong": 1, "items": ["i4"]})
        ad = row["accuracy_diff_vs_expert"]
        self.assertAlmostEqual(ad["diff"], 0.25)
        self.assertEqual((ad["only_a_right"], ad["only_b_right"]), (1, 0))

    def test_fleiss_for_three_judges(self):
        wide = "item,j1,j2,j3\nx1,a,a,a\nx2,a,a,b\nx3,b,b,b\n"
        code, o, err = self.stats({"wide.csv": wide}, "wide.csv", "--judges", "j1,j2,j3")
        self.assertEqual(code, 0, err)
        self.assertAlmostEqual(o["fleiss"]["kappa"], 0.55)
        self.assertEqual((o["fleiss"]["raters"], o["fleiss"]["n"]), (3, 3))

    def test_expert_judge_rows_become_expert_labels(self):
        text = "item,judge,label\ni1,bot,pass\ni1,lead,pass\ni2,bot,pass\ni2,lead,fail\n"
        code, o, err = self.stats({"j.csv": text}, "j.csv", "--expert-judge", "lead")
        self.assertEqual(code, 0, err)
        self.assertEqual(o["judges"], ["bot"])
        self.assertEqual(o["expert_items"], 2)
        self.assertEqual(o["vs_expert"]["bot"]["all"]["exact"], 1)

    def test_jsonl_and_stdin_input(self):
        text = "\n".join(json.dumps({"id": i, "verdict": v, "human": h})
                         for i, v, h in (("1", "pass", "pass"), ("2", "fail", "pass"), ("3", "fail", "fail")))
        with workdir() as d:
            write(os.path.join(d, "j.jsonl"), text)
            code1, out1, err1 = run(SKILL, SCRIPT, "j.jsonl", "--json", "--boot", "0", cwd=d)
        code2, out2, err2 = run(SKILL, SCRIPT, "-", "--json", "--boot", "0", stdin=text)
        self.assertEqual((code1, code2), (0, 0), err1 + err2)
        for out in (out1, out2):
            self.assertEqual(json.loads(out)["vs_expert"]["judge"]["all"]["exact"], 2)

    def test_output_flag_writes_report(self):
        with workdir() as d:
            write(os.path.join(d, "grades.csv"), GRADES)
            code, out, err = run(SKILL, SCRIPT, "grades.csv", "--boot", "0", "-o", "r.md", cwd=d)
            self.assertEqual((code, out), (0, ""), err)
            self.assertTrue(read(os.path.join(d, "r.md")).startswith("# Judge statistics"))

    def test_self_test_passes(self):
        code, out, err = run(SKILL, SCRIPT, "--self-test")
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)

    # --- bad input: exit 2 with a message -----------------------------------------------

    def assert_bad(self, files, *args, msg):
        code, out, err = self.stats(files, *args, as_json=False)
        self.assertEqual(code, 2, out)
        self.assertIn(msg, err)
        self.assertNotIn("Traceback", err)

    def test_missing_file(self):
        self.assert_bad({}, "nope.csv", msg="file not found")

    def test_empty_input(self):
        self.assert_bad({"e.csv": "  \n"}, "e.csv", msg="the input is empty")

    def test_no_item_column(self):
        self.assert_bad({"x.csv": "thing,label\n1,pass\n"}, "x.csv", msg="no 'item' column")

    def test_no_label_or_score_column(self):
        self.assert_bad({"x.csv": "item,note\n1,hi\n"}, "x.csv", msg="need a 'label' or a 'score' column")

    def test_malformed_jsonl_line(self):
        self.assert_bad({"x.jsonl": '{"item": "1", "label": "pass"}\n{oops\n'}, "x.jsonl",
                        msg="line 2 is not valid JSON")

    def test_unknown_gate_metric(self):
        self.assert_bad({"g.csv": GRADES}, "g.csv", "--gate", "vibes>=1", msg="unknown metric 'vibes'")

    def test_group_by_missing_column(self):
        self.assert_bad({"g.csv": GRADES}, "g.csv", "--group-by", "arm", msg="--group-by arm: no such column")

    def test_col_override_missing_column(self):
        self.assert_bad({"g.csv": GRADES}, "g.csv", "--col", "score=points", msg="--col score=points: no such column")

    def test_threshold_without_score_column(self):
        self.assert_bad({"x.csv": "item,label\n1,pass\n"}, "x.csv", "--threshold", "4",
                        msg="--threshold needs a 'score' column")

    def test_gold_with_no_matching_ids(self):
        self.assert_bad({"g.csv": GRADES, "gold.csv": "item,label\nzz,4\n"}, "g.csv", "--gold", "gold.csv",
                        msg="none of its item ids match")


if __name__ == "__main__":
    unittest.main()

import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "behaviour-equivalence", "golden_diff.py"


def jsonl(path, records):
    return write(path, "".join(json.dumps(r) + "\n" for r in records))


def rules_file(path, rules):
    return write(path, json.dumps(rules))


def diff(d, old, new, *args):
    """Write two JSONL sides, run the script with --json, return (code, report, stderr)."""
    a = jsonl(os.path.join(d, "old.jsonl"), old)
    b = jsonl(os.path.join(d, "new.jsonl"), new)
    code, out, err = run(SKILL, SCRIPT, a, b, "--json", *args)
    return code, (json.loads(out) if out.strip() else None), err


class GoldenDiffPathTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_parse_path_reads_keys_any_index_and_fixed_index(self):
        self.assertEqual(self.m.parse_path("body.items[].price"),
                         [("key", "body"), ("key", "items"), ("any_idx", None), ("key", "price")])
        self.assertEqual(self.m.parse_path("$.lines[2]"), [("key", "lines"), ("idx", 2)])
        self.assertEqual(self.m.parse_path("headers.*"), [("key", "headers"), ("any_key", None)])

    def test_dollar_is_the_whole_record(self):
        self.assertEqual(self.m.parse_path("$"), [])

    def test_unreadable_path_is_bad_input(self):
        with self.assertRaises(self.m.BadInput):
            self.m.parse_path("body.items[x]")

    def test_wildcards_match_one_level_only(self):
        pat = self.m.parse_path("body.*")
        self.assertTrue(self.m.matches(pat, ["body", "a"]))
        self.assertFalse(self.m.matches(pat, ["body", "a", "b"]))
        self.assertFalse(self.m.matches(self.m.parse_path("items[]"), ["items", "k"]))


class GoldenDiffVerdictTest(unittest.TestCase):
    def test_identical_sides_exit_0_equivalent(self):
        with workdir() as d:
            recs = [{"case_id": "c1", "status": 200, "body": {"total_cents": 1250}}]
            code, rep, _ = diff(d, recs, recs)
        self.assertEqual(code, 0)
        self.assertEqual(rep["verdict"], "EQUIVALENT")
        self.assertEqual(rep["cases"]["matched"], 1)

    def test_changed_value_exit_1_with_case_path_and_values(self):
        with workdir() as d:
            code, rep, _ = diff(d,
                                [{"case_id": "c1", "body": {"tax_cents": 125}},
                                 {"case_id": "c2", "body": {"tax_cents": 40}}],
                                [{"case_id": "c1", "body": {"tax_cents": 124}},
                                 {"case_id": "c2", "body": {"tax_cents": 40}}])
        self.assertEqual(code, 1)
        self.assertEqual(rep["verdict"], "NOT EQUIVALENT")
        self.assertEqual(rep["mismatched_cases"], ["c1"])
        self.assertEqual(rep["diffs"], [{"case": "c1", "path": "body.tax_cents", "kind": "changed",
                                         "old": 125, "new": 124}])

    def test_case_missing_in_new_is_not_equivalent(self):
        with workdir() as d:
            code, rep, _ = diff(d, [{"case_id": "c1", "v": 1}, {"case_id": "c2", "v": 2}],
                                [{"case_id": "c1", "v": 1}, {"case_id": "c3", "v": 3}])
        self.assertEqual(code, 1)
        self.assertEqual(rep["cases"]["missing_in_new"], ["c2"])
        self.assertEqual(rep["cases"]["extra_in_new"], ["c3"])
        self.assertEqual(rep["cases"]["compared"], 1)

    def test_bool_and_number_are_a_type_change(self):
        with workdir() as d:
            code, rep, _ = diff(d, [{"case_id": "c1", "ok": 1}], [{"case_id": "c1", "ok": True}])
        self.assertEqual(code, 1)
        self.assertEqual(rep["diffs"][0]["kind"], "type number -> bool")

    def test_field_added_and_removed_are_reported(self):
        with workdir() as d:
            _, rep, _ = diff(d, [{"case_id": "c1", "a": 1}], [{"case_id": "c1", "b": 1}])
        kinds = {(x["path"], x["kind"]) for x in rep["diffs"]}
        self.assertEqual(kinds, {("a", "missing in new"), ("b", "added in new")})

    def test_per_field_summary_generalises_list_indexes(self):
        with workdir() as d:
            old = [{"case_id": "c1", "items": [{"p": 1}, {"p": 2}]}, {"case_id": "c2", "items": [{"p": 3}]}]
            new = [{"case_id": "c1", "items": [{"p": 9}, {"p": 9}]}, {"case_id": "c2", "items": [{"p": 9}]}]
            _, rep, _ = diff(d, old, new)
        self.assertEqual(rep["fields"], [{"path": "items[].p", "diffs": 3, "cases": 2,
                                          "case_ids": ["c1", "c2"], "kinds": ["changed"]}])

    def test_max_diffs_limits_the_list_but_not_the_total(self):
        with workdir() as d:
            old = [{"case_id": "c%d" % i, "v": i} for i in range(5)]
            new = [{"case_id": "c%d" % i, "v": i + 1} for i in range(5)]
            _, rep, _ = diff(d, old, new, "--max-diffs", "2")
        self.assertEqual(len(rep["diffs"]), 2)
        self.assertEqual(rep["diffs_total"], 5)

    def test_custom_key_names_the_case_id_field(self):
        with workdir() as d:
            code, rep, _ = diff(d, [{"id": 7, "v": 1}], [{"id": 7, "v": 1}], "--key", "id")
        self.assertEqual(code, 0)
        self.assertEqual(rep["cases"]["matched"], 1)

    def test_directory_side_compares_text_files_line_by_line(self):
        with workdir() as d:
            write(os.path.join(d, "old", "c1.csv"), "id,total\n1,10\n")
            write(os.path.join(d, "new", "c1.csv"), "id,total\n1,11\n")
            write(os.path.join(d, "old", "c2.json"), '{"a": 1}')
            write(os.path.join(d, "new", "c2.json"), '{"a": 1}')
            code, out, _ = run(SKILL, SCRIPT, os.path.join(d, "old"), os.path.join(d, "new"), "--json")
        rep = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(rep["mismatched_cases"], ["c1"])
        self.assertEqual(rep["diffs"][0]["kind"], "line 2 changed")
        self.assertEqual((rep["diffs"][0]["old"], rep["diffs"][0]["new"]), ("1,10", "1,11"))

    def test_text_report_leads_with_the_verdict(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1", "v": 1}])
            b = jsonl(os.path.join(d, "b.jsonl"), [{"case_id": "c1", "v": 2}])
            code, out, _ = run(SKILL, SCRIPT, a, b)
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("Verdict after rules: NOT EQUIVALENT"))
        self.assertIn("c1  v  [changed]  old=1  new=2", out)

    def test_output_flag_writes_the_report_to_a_file(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1", "v": 1}])
            target = os.path.join(d, "report.json")
            code, out, _ = run(SKILL, SCRIPT, a, a, "--json", "-o", target)
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertEqual(json.loads(read(target))["verdict"], "EQUIVALENT")


class GoldenDiffRulesTest(unittest.TestCase):
    def test_ignore_rule_hides_a_noisy_leaf(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "body.issued_at", "rule": "ignore", "reason": "wall-clock time"}]})
            code, rep, _ = diff(d, [{"case_id": "c1", "body": {"issued_at": "10:00", "n": 1}}],
                                [{"case_id": "c1", "body": {"issued_at": "10:01", "n": 1}}], "--rules", r)
        self.assertEqual(code, 0)
        self.assertEqual(rep["rules"][0]["hits"], 2)
        self.assertEqual(rep["warnings"], [])

    def test_ignored_field_present_on_one_side_still_differs(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"body.issued_at": "ignore"})
            code, rep, _ = diff(d, [{"case_id": "c1", "body": {"issued_at": "10:00"}}],
                                [{"case_id": "c1", "body": {}}], "--rules", r)
        self.assertEqual(code, 1)
        self.assertEqual(rep["diffs"][0]["kind"], "missing in new")

    def test_regex_rule_keeps_the_format_check(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "body.id", "rule": "regex", "pattern": "^INV-[0-9]{6}$", "replace": "INV-<id>",
                 "reason": "sequence per call"}]})
            ok, _, _ = diff(d, [{"case_id": "c1", "body": {"id": "INV-000001"}}],
                            [{"case_id": "c1", "body": {"id": "INV-000777"}}], "--rules", r)
            bad, rep, _ = diff(d, [{"case_id": "c1", "body": {"id": "INV-000001"}}],
                               [{"case_id": "c1", "body": {"id": "inv-777"}}], "--rules", r)
        self.assertEqual(ok, 0)
        self.assertEqual(bad, 1)
        self.assertEqual((rep["diffs"][0]["old"], rep["diffs"][0]["new"]), ("INV-<id>", "inv-777"))

    def test_sort_rule_by_key_makes_order_irrelevant(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "items", "rule": "sort", "by": "sku", "reason": "set order"}]})
            code, _, _ = diff(d, [{"case_id": "c1", "items": [{"sku": "b", "q": 1}, {"sku": "a", "q": 2}]}],
                              [{"case_id": "c1", "items": [{"sku": "a", "q": 2}, {"sku": "b", "q": 1}]}],
                              "--rules", r)
        self.assertEqual(code, 0)

    def test_list_order_matters_without_a_sort_rule(self):
        with workdir() as d:
            code, _, _ = diff(d, [{"case_id": "c1", "items": [1, 2]}], [{"case_id": "c1", "items": [2, 1]}])
        self.assertEqual(code, 1)

    def test_round_half_even_and_half_up_differ_on_a_5_boundary(self):
        old, new = [{"case_id": "c1", "r": 0.125}], [{"case_id": "c1", "r": 0.12}]
        with workdir() as d:
            even = rules_file(os.path.join(d, "e.json"), {"rules": [
                {"path": "r", "rule": "round", "digits": 2, "reason": "printed precision"}]})
            up = rules_file(os.path.join(d, "u.json"), {"rules": [
                {"path": "r", "rule": "round", "digits": 2, "mode": "half_up", "reason": "printed precision"}]})
            code_even, _, _ = diff(d, old, new, "--rules", even)
            code_up, rep, _ = diff(d, old, new, "--rules", up)
        self.assertEqual(code_even, 0)
        self.assertEqual(code_up, 1)
        self.assertEqual((rep["diffs"][0]["old"], rep["diffs"][0]["new"]), (0.13, 0.12))

    def test_abs_tolerance_absorbs_small_gaps_and_counts_them(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "fx_rate", "rule": "tolerance", "abs": "0.001", "reason": "float printing"}]})
            code, rep, _ = diff(d, [{"case_id": "c1", "fx_rate": 1.0000}, {"case_id": "c2", "fx_rate": 1.0}],
                                [{"case_id": "c1", "fx_rate": 1.0005}, {"case_id": "c2", "fx_rate": 1.01}],
                                "--rules", r)
        self.assertEqual(code, 1)
        self.assertEqual(rep["mismatched_cases"], ["c2"])
        self.assertEqual(rep["rules"][0]["hits"], 1)
        self.assertIn("rule 1 (tolerance fx_rate) absorbed 1 difference(s)", rep["warnings"])

    def test_rel_tolerance_scales_with_the_value(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "score", "rule": "tolerance", "rel": 0.01, "reason": "model float"}]})
            code, _, _ = diff(d, [{"case_id": "c1", "score": 100}], [{"case_id": "c1", "score": 100.5}],
                              "--rules", r)
        self.assertEqual(code, 0)

    def test_plain_object_and_bare_list_rule_files_are_accepted(self):
        old = [{"case_id": "c1", "t": "a", "n": 1}]
        new = [{"case_id": "c1", "t": "b", "n": 1}]
        with workdir() as d:
            obj = rules_file(os.path.join(d, "o.json"), {"t": {"rule": "ignore", "reason": "clock"}})
            lst = rules_file(os.path.join(d, "l.json"), [{"path": "t", "rule": "ignore", "reason": "clock"}])
            self.assertEqual(diff(d, old, new, "--rules", obj)[0], 0)
            self.assertEqual(diff(d, old, new, "--rules", lst)[0], 0)

    def test_warnings_name_missing_reason_no_hit_subtree_and_money(self):
        with workdir() as d:
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "body", "rule": "ignore", "reason": "differs"},
                {"path": "nowhere", "rule": "ignore", "reason": "typo"},
                {"path": "x", "rule": "regex", "pattern": "a"},
                {"path": "lines[].tax_cents", "rule": "tolerance", "abs": 1, "reason": "rounding"}]})
            code, rep, _ = diff(d, [{"case_id": "c1", "body": {"a": 1}, "x": "a"}],
                                [{"case_id": "c1", "body": {"a": 2}, "x": "a"}], "--rules", r)
        self.assertEqual(code, 0)
        w = rep["warnings"]
        self.assertIn("rule 1 (ignore body) ignores a whole object or list: name the leaf fields instead", w)
        self.assertIn("rule 2 (ignore nowhere) matched nothing: check the path", w)
        self.assertIn("rule 3 (regex x) has no reason", w)
        self.assertIn("rule 4 (tolerance lines[].tax_cents) loosens a money-like field: "
                      "compare money exactly in minor units", w)

    def test_text_report_flags_warnings_in_the_headline(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1", "v": 1}])
            r = rules_file(os.path.join(d, "r.json"), {"nowhere": "ignore"})
            _, out, _ = run(SKILL, SCRIPT, a, a, "--rules", r)
        self.assertIn("EQUIVALENT  (2 warnings at the end: read them before trusting this)", out.splitlines()[0])
        self.assertIn("NO REASON GIVEN", out)

    def test_dollar_regex_normalises_a_whole_text_file(self):
        with workdir() as d:
            write(os.path.join(d, "old", "c1.txt"), "run 1111\n")
            write(os.path.join(d, "new", "c1.txt"), "run 2222\n")
            r = rules_file(os.path.join(d, "r.json"), {"rules": [
                {"path": "$", "rule": "regex", "pattern": "[0-9]{4}", "replace": "<run>", "reason": "run id"}]})
            code, _, _ = run(SKILL, SCRIPT, os.path.join(d, "old"), os.path.join(d, "new"), "--rules", r)
        self.assertEqual(code, 0)


class GoldenDiffAcceptedTest(unittest.TestCase):
    OLD = [{"case_id": "c1", "msg": "Not found"}, {"case_id": "c2", "msg": "Not found"}]
    NEW = [{"case_id": "c1", "msg": "No such order"}, {"case_id": "c2", "msg": "No such order"}]

    def test_accepted_change_with_approver_exits_0_with_its_own_verdict(self):
        with workdir() as d:
            acc = write(os.path.join(d, "acc.json"), json.dumps({"accepted": [
                {"path": "msg", "approver": "Product owner", "reason": "new error copy"}]}))
            code, rep, _ = diff(d, self.OLD, self.NEW, "--accepted", acc)
        self.assertEqual(code, 0)
        self.assertEqual(rep["verdict"], "EQUIVALENT EXCEPT ACCEPTED CHANGES")
        self.assertEqual(rep["cases"]["accepted_only"], 2)
        self.assertEqual(rep["accepted"][0]["approver"], "Product owner")

    def test_accepted_change_limited_to_cases_leaves_others_failing(self):
        with workdir() as d:
            acc = write(os.path.join(d, "acc.json"), json.dumps({"accepted": [
                {"path": "msg", "approver": "Product owner", "cases": ["c1"]}]}))
            code, rep, _ = diff(d, self.OLD, self.NEW, "--accepted", acc)
        self.assertEqual(code, 1)
        self.assertEqual(rep["mismatched_cases"], ["c2"])
        self.assertEqual(rep["cases"]["accepted_only"], 1)

    def test_accepted_change_without_approver_is_refused(self):
        with workdir() as d:
            acc = write(os.path.join(d, "acc.json"), json.dumps({"accepted": [{"path": "msg", "approver": " "}]}))
            code, _, err = diff(d, self.OLD, self.NEW, "--accepted", acc)
        self.assertEqual(code, 2)
        self.assertIn("has no approver", err)

    def test_accepted_change_that_matched_nothing_is_warned(self):
        with workdir() as d:
            acc = write(os.path.join(d, "acc.json"), json.dumps({"accepted": [
                {"path": "other", "approver": "Product owner"}]}))
            code, rep, _ = diff(d, self.OLD, self.OLD, "--accepted", acc)
        self.assertEqual(code, 0)
        self.assertIn("accepted change at other matched no difference", rep["warnings"])


class GoldenDiffBadInputTest(unittest.TestCase):
    def assertBlocked(self, code, err, fragment):
        self.assertEqual(code, 2)
        self.assertIn(fragment, err)
        self.assertNotIn("Traceback", err)

    def test_missing_side_exits_2(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1"}])
            code, _, err = run(SKILL, SCRIPT, a, os.path.join(d, "nope.jsonl"))
        self.assertBlocked(code, err, "not found")

    def test_empty_side_exits_2(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1"}])
            e = write(os.path.join(d, "e.jsonl"), "\n")
            code, _, err = run(SKILL, SCRIPT, a, e)
        self.assertBlocked(code, err, "no cases")

    def test_malformed_line_names_the_line(self):
        with workdir() as d:
            a = write(os.path.join(d, "a.jsonl"), '{"case_id": "c1"}\n{oops\n')
            code, _, err = run(SKILL, SCRIPT, a, a)
        self.assertBlocked(code, err, "line 2: not valid JSON")

    def test_record_without_key_and_duplicate_ids_exit_2(self):
        with workdir() as d:
            nokey = jsonl(os.path.join(d, "k.jsonl"), [{"id": "c1"}])
            dup = jsonl(os.path.join(d, "d.jsonl"), [{"case_id": "c1"}, {"case_id": "c1"}])
            code, _, err = run(SKILL, SCRIPT, nokey, nokey)
            self.assertBlocked(code, err, "no 'case_id' field")
            code, _, err = run(SKILL, SCRIPT, dup, dup)
            self.assertBlocked(code, err, "duplicate case id c1")

    def test_bad_rules_exit_2(self):
        bad = {
            "unknown rule": ({"rules": [{"path": "a", "rule": "fuzzy"}]}, "unknown rule"),
            "no path": ({"rules": [{"rule": "ignore"}]}, "needs a path and a rule"),
            "bad regex": ({"rules": [{"path": "a", "rule": "regex", "pattern": "("}]}, "bad or missing pattern"),
            "tolerance": ({"rules": [{"path": "a", "rule": "tolerance"}]}, "tolerance needs abs or rel"),
            "round": ({"rules": [{"path": "a", "rule": "round", "digits": "2"}]}, "round needs integer digits"),
            "mode": ({"rules": [{"path": "a", "rule": "round", "digits": 2, "mode": "up"}]}, "mode must be"),
        }
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1", "a": 1}])
            for name, (rules, fragment) in bad.items():
                with self.subTest(name):
                    r = rules_file(os.path.join(d, "r.json"), rules)
                    code, _, err = run(SKILL, SCRIPT, a, a, "--rules", r)
                    self.assertBlocked(code, err, fragment)

    def test_unreadable_rules_file_exits_2(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1"}])
            r = write(os.path.join(d, "r.json"), "{not json")
            code, _, err = run(SKILL, SCRIPT, a, a, "--rules", r)
        self.assertBlocked(code, err, "cannot read rules file")

    def test_plain_object_rule_with_non_object_spec_exits_2(self):
        with workdir() as d:
            a = jsonl(os.path.join(d, "a.jsonl"), [{"case_id": "c1", "a": 1}])
            r = rules_file(os.path.join(d, "r.json"), {"a": 5})
            code, _, err = run(SKILL, SCRIPT, a, a, "--rules", r)
        self.assertBlocked(code, err, "rule 1")


if __name__ == "__main__":
    unittest.main()

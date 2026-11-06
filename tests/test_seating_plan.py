import copy
import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "seating-plan", "seating_check.py"


def plan():
    """Two tables of four: a family that sits together, two guests kept apart, one wheelchair user."""
    return {"room": {"width": 10, "depth": 6}, "exits": [[0, 3]],
            "tables": [{"id": "A", "capacity": 4, "at": [2.5, 3], "accessible": True},
                       {"id": "B", "capacity": 4, "at": [7, 3]}],
            "guests": [{"id": "g1", "name": "Ama Lind", "party": "Lind", "needs": ["wheelchair"]},
                       {"id": "g2", "name": "Bo Lind", "party": "Lind"},
                       {"id": "g3", "name": "Cy Moss", "party": "Moss", "dietary": "vegan"},
                       {"id": "g4", "name": "Di Moss", "party": "Moss"},
                       {"id": "g5", "name": "Ed Park", "party": "Park"},
                       {"id": "g6", "name": "Fay Park", "party": "Park"}],
            "together": [["g1", "g2"]],
            "apart": [["g2", "g5"]],
            "fixed": {"g3": "B"},
            "assignments": {"A": ["g1", "g2"], "B": ["g3", "g4", "g5", "g6"]}}


class SeatingCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, p, **kw):
        return self.m.check(self.m.load(p), **kw)

    def test_good_plan_passes_clean(self):
        r = self.check(plan())
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["warns"], [])
        self.assertEqual((r["seated"], r["guests"], r["seats"]), (6, 6, 8))

    def test_unseated_guest_fails(self):
        p = plan()
        p["assignments"]["B"].remove("g6")
        self.assertIn("Fay Park has no seat", self.check(p)["fails"])

    def test_guest_seated_twice_fails(self):
        p = plan()
        p["assignments"]["A"].append("g6")
        fails = self.check(p)["fails"]
        self.assertTrue(any("Fay Park is seated more than once (A, B)" in f for f in fails))

    def test_over_capacity_fails(self):
        p = plan()
        p["tables"][1]["capacity"] = 3
        self.assertIn("table B has 4 guests for 3 seats", self.check(p)["fails"])

    def test_together_group_split_fails(self):
        p = plan()
        p["assignments"] = {"A": ["g1", "g5"], "B": ["g3", "g4", "g2", "g6"]}
        p["apart"] = []
        fails = self.check(p)["fails"]
        self.assertTrue(any(f.startswith("must sit together but are split: Ama Lind (A), Bo Lind (B)") for f in fails))

    def test_apart_pair_at_one_table_fails(self):
        p = plan()
        p["assignments"] = {"A": ["g1", "g2", "g5"], "B": ["g3", "g4", "g6"]}
        self.assertTrue(any("Bo Lind and Ed Park must be kept apart" in f for f in self.check(p)["fails"]))

    def test_wheelchair_at_inaccessible_table_fails(self):
        p = plan()
        p["tables"][0]["accessible"] = False
        self.assertTrue(any("Ama Lind uses a wheelchair but table A" in f for f in self.check(p)["fails"]))

    def test_fixed_seat_moved_fails(self):
        p = plan()
        p["fixed"] = {"g3": "A"}
        self.assertTrue(any("Cy Moss has a fixed seat at table A but sits at B" in f for f in self.check(p)["fails"]))

    def test_failures_mark_their_tables(self):
        p = plan()
        p["tables"][1]["capacity"] = 3
        self.assertEqual(self.check(p)["bad_tables"], ["B"])

    def test_split_household_and_half_empty_table_warn(self):
        p = plan()
        p["tables"].append({"id": "C", "capacity": 4})
        p["assignments"] = {"A": ["g1", "g2", "g6"], "B": ["g3", "g4", "g5"], "C": []}
        p["apart"] = []
        warns = self.check(p)["warns"]
        self.assertIn("the Park party (2) is split across tables A, B", warns)
        self.assertIn("table C is empty", warns)

    def test_household_bigger_than_any_table_may_split_without_a_warning(self):
        p = plan()
        for g in p["guests"]:
            g["party"] = "Everyone"
        p["guests"][0]["party"] = "Everyone"
        self.assertFalse(any("split across" in w for w in self.check(p)["warns"]))

    def test_lone_guest_among_one_other_party_warns(self):
        p = plan()
        p["guests"].append({"id": "g7", "name": "Gil Rae"})
        p["assignments"]["A"] = ["g3", "g4", "g7"]
        p["assignments"]["B"] = ["g1", "g2", "g5", "g6"]
        p["tables"][1]["accessible"] = True
        p["apart"], p["fixed"] = [], {}
        p["guests"][3]["party"] = "Moss"
        warns = self.check(p)["warns"]
        self.assertTrue(any("Gil Rae came alone and is the only guest at table A not in the Moss party" in w for w in warns))

    def test_near_exit_guest_far_from_any_exit_warns(self):
        p = plan()
        p["guests"][4]["needs"] = ["near exit"]
        self.assertTrue(any("Ed Park needs to be near an exit but table B is 7.0 m" in w
                            for w in self.check(p, exit_distance=5)["warns"]))

    def test_bad_inputs_are_named(self):
        cases = [({"tables": [], "guests": [{"id": "g"}]}, "no tables"),
                 ({"tables": [{"id": "A"}], "guests": []}, "no guests"),
                 ({"tables": [{"id": "A"}, {"id": "A"}], "guests": [{"id": "g"}]}, "two tables are called"),
                 ({"tables": [{"id": "A", "capacity": 2.5}], "guests": [{"id": "g"}]}, "whole number"),
                 ({"tables": [{"id": "A"}], "guests": [{"id": "g"}], "assignments": {"Z": ["g"]}}, "table 'Z'"),
                 ({"tables": [{"id": "A"}], "guests": [{"id": "g"}], "assignments": {"A": ["x"]}}, "guest 'x'"),
                 ({"tables": [{"id": "A"}], "guests": [{"id": "g"}], "apart": [["g"]]}, "exactly two"),
                 ({"tables": [{"id": "A"}], "guests": [{"id": "g"}], "fixed": ["g"]}, "fixed must map")]
        for data, msg in cases:
            with self.assertRaises(self.m.BadInput, msg=msg) as cm:
                self.m.load(data)
            self.assertIn(msg, str(cm.exception))


class SeatingCheckCliTest(unittest.TestCase):
    def test_pass_and_svg(self):
        with workdir() as d:
            f = write(os.path.join(d, "seating.json"), json.dumps(plan()))
            out = os.path.join(d, "room.svg")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--svg", out)
            self.assertEqual(code, 0)
            self.assertIn("PASS", stdout)
            self.assertIn("B (round, 4/4; 1 vegan): Cy Moss, Di Moss, Ed Park, Fay Park", stdout)
            svg = read(out)
            self.assertIn(">Fay Park</text>", svg)
            self.assertIn("accessible", svg)
            self.assertIn("EXIT", svg)

    def test_failure_exits_1_and_marks_the_table_in_red(self):
        p = plan()
        p["tables"][1]["capacity"] = 3
        with workdir() as d:
            f = write(os.path.join(d, "seating.json"), json.dumps(p))
            out = os.path.join(d, "room.svg")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--svg", out)
            self.assertEqual(code, 1)
            self.assertIn("FAIL table B has 4 guests for 3 seats", stdout)
            self.assertIn("#c62828", read(out))

    def test_json_output(self):
        with workdir() as d:
            f = write(os.path.join(d, "seating.json"), json.dumps(plan()))
            code, stdout, _ = run(SKILL, SCRIPT, f, "--json")
            self.assertEqual(code, 0)
            doc = json.loads(stdout)
            self.assertTrue(doc["pass"])
            self.assertEqual([t["seated"] for t in doc["tables"]], [2, 4])

    def test_bad_input_exits_2(self):
        p = copy.deepcopy(plan())
        p["assignments"]["A"].append("nobody")
        with workdir() as d:
            f = write(os.path.join(d, "seating.json"), json.dumps(p))
            code, out, _ = run(SKILL, SCRIPT, f)
            self.assertEqual(code, 2)
            self.assertIn("not on the guest list", out)
            self.assertEqual(run(SKILL, SCRIPT, os.path.join(d, "missing.json"))[0], 2)
            write(os.path.join(d, "broken.json"), "{not json")
            self.assertEqual(run(SKILL, SCRIPT, os.path.join(d, "broken.json"))[0], 2)


if __name__ == "__main__":
    unittest.main()

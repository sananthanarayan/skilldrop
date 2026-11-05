import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "floor-plan-layout", "plan_check.py"


def plan():
    """A 6 × 4 floor: a hall at the front door, a living room and a bedroom off it."""
    return {"units": "m", "outline": [[0, 0], [6, 0], [6, 4], [0, 4]],
            "rooms": [{"name": "Hall", "rect": [0, 0, 2, 4]},
                      {"name": "Living", "rect": [2, 0, 4, 2], "target_area": 8, "habitable": True},
                      {"name": "Bedroom", "rect": [2, 2, 4, 2], "target_area": 8, "habitable": True}],
            "doors": [{"between": ["outside", "Hall"], "at": [1, 0]},
                      {"between": ["Hall", "Living"], "at": [2, 1]},
                      {"between": ["Hall", "Bedroom"], "at": [2, 3]}],
            "windows": [{"room": "Living", "at": [4, 0]}, {"room": "Bedroom", "at": [6, 3]}]}


class PlanCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, p):
        return self.m.check(self.m.load(p))

    def test_good_plan_passes_clean(self):
        r = self.check(plan())
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["warns"], [])
        self.assertAlmostEqual(r["room_area"], 24)

    def test_overlap_fails(self):
        p = plan()
        p["rooms"][1]["rect"] = [1.5, 0, 4.5, 2]
        self.assertTrue(any("overlap" in f for f in self.check(p)["fails"]))

    def test_room_outside_outline_fails(self):
        p = plan()
        p["rooms"][2]["rect"] = [2, 2, 4.5, 2]
        self.assertTrue(any("outside the outline" in f for f in self.check(p)["fails"]))

    def test_room_across_an_inside_corner_fails(self):
        p = plan()
        p["outline"] = [[0, 0], [6, 0], [6, 3], [5, 3], [5, 4], [0, 4]]
        self.assertTrue(any("Bedroom runs outside" in f for f in self.check(p)["fails"]))

    def test_door_not_on_shared_wall_fails(self):
        p = plan()
        p["doors"][1]["at"] = [3, 1]
        fails = self.check(p)["fails"]
        self.assertTrue(any("not on a wall both sides share" in f for f in fails))
        self.assertTrue(any("Living cannot be reached" in f for f in fails))

    def test_no_entrance_fails(self):
        p = plan()
        p["doors"] = p["doors"][1:]
        self.assertTrue(any("no door to outside" in f for f in self.check(p)["fails"]))

    def test_room_reached_through_another_room_is_reachable(self):
        p = plan()
        p["doors"][2] = {"between": ["Living", "Bedroom"], "at": [4, 2]}
        self.assertEqual(self.check(p)["fails"], [])

    def test_area_off_target_narrow_room_and_narrow_door_warn(self):
        p = plan()
        p["rooms"][1]["target_area"] = 10
        p["rooms"][0]["min_width"] = 2.4
        p["doors"][0]["width"] = 0.7
        warns = self.check(p)["warns"]
        self.assertTrue(any("Living" in w and "-20 %" in w for w in warns))
        self.assertTrue(any("Hall" in w and "minimum width" in w for w in warns))
        self.assertTrue(any("door 1" in w for w in warns))

    def test_habitable_room_without_outside_window_warns(self):
        p = plan()
        p["windows"] = p["windows"][:1]
        self.assertTrue(any("Bedroom is habitable" in w for w in self.check(p)["warns"]))

    def test_unallocated_area_warns(self):
        p = plan()
        p["outline"] = [[0, 0], [7, 0], [7, 4], [0, 4]]
        p["windows"][1]["at"] = [4, 4]
        self.assertTrue(any("in no room" in w for w in self.check(p)["warns"]))

    def test_l_shaped_room_counts_once_and_loses_its_inner_wall(self):
        p = plan()
        p["rooms"][0] = {"name": "Hall", "rects": [[0, 0, 2, 4], [2, 0, 1, 2]]}
        p["rooms"][1]["rect"] = [3, 0, 3, 2]
        p["rooms"][1]["target_area"] = 6
        p["doors"][1]["at"] = [3, 1]
        plan_ = self.m.load(p)
        r = self.m.check(plan_)
        self.assertEqual(r["fails"], [])
        self.assertAlmostEqual(plan_["rooms"][0]["area"], 10)
        walls = self.m.room_walls(plan_["rooms"][0]["rects"])
        self.assertNotIn(((2.0, 0.0), (2.0, 2.0)), walls)
        self.assertIn(((2.0, 2.0), (2.0, 4.0)), walls)


class PlanCheckCliTest(unittest.TestCase):
    def test_pass_and_svg(self):
        with workdir() as d:
            f = write(os.path.join(d, "plan.json"), json.dumps(plan()))
            out = os.path.join(d, "plan.svg")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--svg", out)
            self.assertEqual(code, 0)
            self.assertIn("PASS", stdout)
            svg = read(out)
            self.assertIn(">Bedroom</text>", svg)
            self.assertIn("6 m</text>", svg)
            self.assertIn("schematic, not for construction", svg)

    def test_failure_exits_1(self):
        p = plan()
        p["doors"] = []
        with workdir() as d:
            f = write(os.path.join(d, "plan.json"), json.dumps(p))
            self.assertEqual(run(SKILL, SCRIPT, f)[0], 1)

    def test_bad_input_exits_2(self):
        p = plan()
        p["doors"][0]["between"] = ["Hall", "Garage"]
        with workdir() as d:
            f = write(os.path.join(d, "plan.json"), json.dumps(p))
            code, out, _ = run(SKILL, SCRIPT, f)
            self.assertEqual(code, 2)
            self.assertIn("no room called 'Garage'", out)


if __name__ == "__main__":
    unittest.main()

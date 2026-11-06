import copy
import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "furniture-layout", "layout_check.py"


def room():
    """A 4 × 3.5 m bedroom: door on the south wall, a double bed against the north wall."""
    return {"units": "m", "size": [4.0, 3.5],
            "doors": [{"name": "Door", "at": [3.4, 0], "width": 0.8, "hinge": "right", "swing": "in", "entrance": True}],
            "windows": [{"at": [2.0, 3.5], "width": 1.2, "sill": 0.9}],
            "furniture": [
                {"name": "Bed", "type": "bed", "width": 1.6, "depth": 2.0, "at": [1.2, 1.5], "facing": "S"},
                {"name": "Left nightstand", "type": "nightstand", "width": 0.45, "depth": 0.4, "at": [0.7, 3.1]},
                {"name": "Right nightstand", "type": "nightstand", "width": 0.45, "depth": 0.4, "at": [2.85, 3.1]},
            ]}


class LayoutCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, d):
        return self.m.check(self.m.load(d))

    def has(self, r, text):
        return any(text in f for f in r["fails"])

    def test_good_layout_passes_clean(self):
        r = self.check(room())
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["warns"], [])
        self.assertAlmostEqual(r["floor"], 14.0)

    def test_template_passes(self):
        d = json.loads(read(os.path.join(os.path.dirname(self.m.__file__), "..", "templates", "layout.json")))
        self.assertEqual(self.check(d)["fails"], [])

    def test_overlap_fails(self):
        d = room()
        d["furniture"][1]["at"] = [1.0, 3.1]
        r = self.check(d)
        self.assertTrue(self.has(r, "Bed and Left nightstand overlap"))

    def test_rug_may_sit_under_furniture(self):
        d = room()
        d["furniture"].append({"name": "Rug", "type": "rug", "width": 2.4, "depth": 1.6, "at": [0.8, 1.2]})
        self.assertEqual(self.check(d)["fails"], [])

    def test_piece_outside_the_room_fails(self):
        d = room()
        d["furniture"][0]["at"] = [2.6, 1.5]
        self.assertTrue(self.has(self.check(d), "Bed runs outside the room"))

    def test_piece_across_an_inside_corner_fails(self):
        d = room()
        del d["size"]
        d["outline"] = [[0, 0], [4, 0], [4, 2.5], [3, 2.5], [3, 3.5], [0, 3.5]]
        d["furniture"] = [{"name": "Desk", "type": "desk", "width": 1.4, "depth": 0.7, "at": [2.5, 2.4], "facing": "S"}]
        self.assertTrue(self.has(self.check(d), "Desk runs outside the room"))

    def test_non_rectilinear_outline_is_bad_input(self):
        d = room()
        del d["size"]
        d["outline"] = [[0, 0], [4, 0], [3, 3.5], [0, 3.5]]
        with self.assertRaises(self.m.InputError):
            self.m.load(d)

    def test_piece_in_the_door_swing_fails(self):
        d = room()
        # right-hinged, viewed from inside: the hinge is at x = 3.0, so the leaf sweeps x 3.0–3.8
        d["furniture"].append({"name": "Chair", "type": "other", "width": 0.4, "depth": 0.4, "at": [3.3, 0.2]})
        self.assertTrue(self.has(self.check(d), "Chair is in the swing of Door"))

    def test_door_swing_follows_the_hinge_side(self):
        d = room()
        g = self.m.door_geometry(self.m.load(d)["doors"][0], self.m.load(d)["outline"])
        self.assertAlmostEqual(g["hinge"][0], 3.0)   # standing inside facing south, the right hand is west
        self.assertAlmostEqual(g["latch"][0], 3.8)
        d["doors"][0]["hinge"] = "left"
        g = self.m.door_geometry(self.m.load(d)["doors"][0], self.m.load(d)["outline"])
        self.assertAlmostEqual(g["hinge"][0], 3.8)

    def test_outward_and_sliding_doors_sweep_nothing_inside(self):
        for swing in ("out", "sliding"):
            d = room()
            d["doors"][0]["swing"] = swing
            d["furniture"].append({"name": "Chair", "type": "other", "width": 0.4, "depth": 0.4, "at": [3.3, 0.6]})
            self.assertFalse(self.has(self.check(d), "in the swing"), swing)

    def test_blocked_bed_side_fails(self):
        d = room()
        d["furniture"].append({"name": "Dresser", "type": "dresser", "width": 0.9, "depth": 0.45, "at": [2.85, 1.8], "facing": "E"})
        # standing at the foot facing the bed, the east side is its right
        self.assertTrue(self.has(self.check(d), "Bed's right clearance (0.60 m) is blocked by Dresser"))

    def test_bed_side_clearance_leaves_room_for_nightstands(self):
        zones = dict(self.m.zones(self.m.load(room())["pieces"][0]))
        x, y, w, h = zones["right"]
        self.assertAlmostEqual(y + h, 3.5 - self.m.BED_HEAD)

    def test_clearance_into_the_wall_fails(self):
        d = room()
        d["furniture"] = [{"name": "Desk", "type": "desk", "width": 1.2, "depth": 0.6, "at": [0.5, 0.3], "facing": "S"}]
        self.assertTrue(self.has(self.check(d), "Desk's front clearance (0.90 m) runs into the wall"))

    def test_clearance_override_removes_a_side(self):
        d = room()
        d["furniture"] = [{"name": "Table", "type": "dining_table", "width": 1.2, "depth": 0.8, "at": [0, 1.2],
                           "facing": "E", "clearance": {"back": 0}}]
        self.assertEqual(self.check(d)["fails"], [])

    def test_no_route_to_a_piece_fails(self):
        d = room()
        # a wardrobe and a bookcase wall off the bed's left side from the door
        d["furniture"] += [{"name": "Wardrobe", "type": "wardrobe", "width": 1.2, "depth": 0.6, "at": [0, 0.5], "facing": "E"},
                           {"name": "Shelf", "type": "bookcase", "width": 1.5, "depth": 0.35, "at": [0.6, 1.2], "facing": "S",
                            "clearance": {"front": 0}}]
        r = self.check(d)
        self.assertTrue(self.has(r, "reaches Bed (its left side)"))

    def test_a_wider_walkway_closes_a_narrow_gap(self):
        # a sideboard across the room leaves a 1.0 m gap on the east; the armchair is beyond it
        d = {"units": "m", "size": [4.0, 4.0], "doors": [{"name": "Door", "at": [0.8, 0], "width": 0.8, "swing": "out"}],
             "furniture": [{"name": "Sideboard", "type": "other", "width": 3.0, "depth": 0.4, "at": [0, 1.6]},
                           {"name": "Armchair", "type": "armchair", "width": 0.85, "depth": 0.85, "at": [1.0, 3.0], "facing": "S"}]}
        r = self.check(d)
        self.assertEqual(r["fails"], [])
        self.assertTrue(r["routes"])
        d["min_walkway"] = 1.2
        self.assertTrue(self.has(self.check(d), "no clear 1.20 m route from the entrance reaches Armchair"))

    def test_blocked_entrance_fails(self):
        d = room()
        d["furniture"].append({"name": "Trunk", "type": "other", "width": 1.0, "depth": 0.6, "at": [2.9, 0.85]})
        self.assertTrue(self.has(self.check(d), "clears the way in at Door"))

    def test_accessible_needs_a_turning_circle(self):
        d = room()
        d["accessible"] = True
        r = self.check(d)
        self.assertEqual(len(r["turns"]), 1)
        self.assertTrue(r["turns"][0][2])
        # the coordinates are reported, so a reply can say where the circle is
        self.assertIn("Turning circle (1.5 m) for turning space: centre at", self.m.report(self.m.load(d), r))
        d["size"] = [2.4, 2.6]
        d["doors"][0]["at"] = [1.9, 0]
        d["windows"] = []
        d["furniture"] = [{"name": "Bed", "type": "single_bed", "width": 0.9, "depth": 2.0, "at": [0, 0.6], "facing": "E",
                           "clearance": {"front": 0}}]
        self.assertTrue(self.has(self.check(d), "turning circle"))

    def test_named_turning_circle_is_checked_and_drawn_where_it_is_given(self):
        d = room()
        d["turning_circles"] = [{"at": [0.85, 0.8], "for": "Noor"}]   # clear of the walls and the bed's corner
        plan = self.m.load(d)
        r = self.m.check(plan)
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["turns"], [((0.85, 0.8), "Noor", True, 1.5)])
        out = self.m.svg(plan, r)
        X, Y = self.m_point(plan, 0.85, 0.8)
        self.assertIn('<circle cx="%.1f" cy="%.1f"' % (X, Y), out)
        self.assertIn(">Noor<", out)
        self.assertEqual(self.m.as_json(plan, r)["turning_circles"], [{"for": "Noor", "at": [0.85, 0.8], "clear": True, "diameter": 1.5}])

    def m_point(self, plan, x, y):
        """The SVG's own projection, recomputed: a turning circle must be drawn exactly at its point."""
        o = plan["outline"]
        xs, ys = [p[0] for p in o], [p[1] for p in o]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        s = 720 / max(x1 - x0, y1 - y0)
        H = (y1 - y0) * s + 2 * 80 + 70
        return 80 + (x - x0) * s, H - 80 - 30 - (y - y0) * s

    def test_named_turning_circle_fails_when_crowded_or_on_furniture(self):
        d = room()
        d["turning_circles"] = [{"at": [0.4, 0.5], "for": "Noor"}]
        self.assertTrue(self.has(self.check(d), "turning circle for Noor at (0.4, 0.5) is not clear"))
        d["turning_circles"] = [{"at": [2.0, 2.5], "for": "Noor"}]
        self.assertTrue(self.has(self.check(d), "turning circle for Noor at (2, 2.5) sits on furniture"))

    def test_bad_turning_circles_input(self):
        d = room()
        d["turning_circles"] = [{"for": "Noor"}]
        with self.assertRaises(self.m.InputError):
            self.m.load(d)

    def test_dining_chairs_and_desk_chair_are_drawn(self):
        d = {"units": "m", "size": [5.0, 4.0],
             "doors": [{"name": "Door", "at": [4.4, 0], "width": 0.8, "hinge": "right", "swing": "in", "entrance": True}],
             "furniture": [{"name": "Table", "type": "dining_table", "width": 1.8, "depth": 0.9, "at": [1.2, 1.6], "facing": "S"},
                           {"name": "Desk", "type": "desk", "width": 1.2, "depth": 0.6, "at": [3.6, 3.4], "facing": "S"}]}
        plan = self.m.load(d)
        table = next(p for p in plan["pieces"] if p["name"] == "Table")
        desk = next(p for p in plan["pieces"] if p["name"] == "Desk")
        self.assertEqual(len(self.m.chairs(table)), 6)   # three a long side, at 0.6 m each
        self.assertEqual(len(self.m.chairs(desk)), 1)
        out = self.m.svg(plan, self.m.check(plan))
        self.assertEqual(out.count('rx="2"'), 7)

    def test_piece_on_a_column_fails(self):
        d = room()
        d["obstacles"] = [{"name": "Column", "type": "column", "rect": [0.0, 0.0, 0.3, 0.3]}]
        d["furniture"].append({"name": "Plant", "type": "other", "width": 0.4, "depth": 0.4, "at": [0.1, 0.1]})
        self.assertTrue(self.has(self.check(d), "Plant sits on the column"))

    def test_tall_piece_in_front_of_a_window_warns(self):
        d = room()
        d["furniture"].append({"name": "Bookcase", "type": "bookcase", "width": 1.0, "depth": 0.35, "at": [0.0, 1.0],
                               "facing": "E"})
        d["windows"].append({"at": [0, 1.5], "width": 1.0, "sill": 0.8})
        r = self.check(d)
        self.assertTrue(any("Bookcase (1.80 m tall) stands in front of the window" in w for w in r["warns"]))

    def test_radiator_and_coverage_warn(self):
        d = room()
        d["obstacles"] = [{"name": "Radiator", "type": "radiator", "rect": [0.0, 1.0, 0.1, 1.0]}]
        d["furniture"].append({"name": "Chest", "type": "other", "width": 0.5, "depth": 0.5, "at": [0.15, 1.2]})
        d["max_coverage"] = 0.2
        warns = self.check(d)["warns"]
        self.assertTrue(any("Chest stands against the radiator" in w for w in warns))
        self.assertTrue(any("covers" in w and "over 20 %" in w for w in warns))

    def test_feet_are_converted(self):
        d = {"units": "ft", "size": [13, 11.5],
             "doors": [{"at": [11, 0], "width": 2.7, "hinge": "right"}],
             "furniture": [{"name": "Bed", "type": "bed", "width": 5, "depth": 6.67, "at": [4, 4.83], "facing": "S"}]}
        p = self.m.load(d)
        self.assertAlmostEqual(p["walkway"], 0.9)
        self.assertAlmostEqual(p["pieces"][0]["rect"][2], 5 * 0.3048)
        r = self.m.check(p)
        self.assertEqual(r["fails"], [])
        self.assertIn("ft", self.m.report(p, r))

    def test_bad_inputs(self):
        for bad in ({}, {"size": [4, 3]}, {"size": [4, 3], "doors": [{"at": [1, 0]}]},
                    {"size": [4, 3], "doors": [{"at": [1, 0]}], "furniture": [{"name": "X", "type": "spaceship",
                                                                                "width": 1, "depth": 1, "at": [0, 0]}]},
                    {"size": [4, 3], "doors": [{"at": [1, 0]}], "furniture": [{"name": "X", "width": 1, "depth": 1,
                                                                                "at": [0, 0], "rotation": 45}]}):
            with self.assertRaises(self.m.InputError):
                self.m.load(bad)


class CommandLineTest(unittest.TestCase):
    def test_exit_codes_svg_and_json(self):
        with workdir() as d:
            good, bad, broken = (os.path.join(d, n) for n in ("good.json", "bad.json", "broken.json"))
            write(good, json.dumps(room()))
            r = room()
            r["furniture"][1]["at"] = [1.0, 3.1]
            write(bad, json.dumps(r))
            write(broken, "{ not json")
            svg = os.path.join(d, "bedroom.svg")
            code, out, _ = run(SKILL, SCRIPT, good, "--svg", svg)
            self.assertEqual(code, 0, out)
            self.assertIn("PASS", out)
            body = read(svg)
            self.assertIn("<svg", body)
            for mark in ("Bed", "1.6×2", "N</text>", "4 m", "stroke-dasharray=\"6 3\""):
                self.assertIn(mark, body)
            code, out, _ = run(SKILL, SCRIPT, bad, "--json")
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertFalse(data["pass"])
            self.assertTrue(any(not p["ok"] for p in data["pieces"]))
            self.assertEqual(run(SKILL, SCRIPT, broken)[0], 2)
            self.assertEqual(run(SKILL, SCRIPT, os.path.join(d, "missing.json"))[0], 2)


def lobby():
    """A 1.35 m wide entrance lobby: entrance at the south end, the bathroom door at the north end."""
    return {"units": "m", "size": [1.35, 4.0],
            "doors": [{"name": "Entrance", "at": [0.675, 0], "width": 0.8, "hinge": "left", "entrance": True},
                      {"name": "Bathroom door", "at": [0.675, 4.0], "width": 0.8, "hinge": "right", "swing": "out"}],
            "furniture": [{"name": "Luggage rack", "type": "other", "width": 0.6, "depth": 0.4, "at": [0.0, 1.2]}]}


def cafe():
    """A café about 8 × 12 m: two-tops and four-tops with their chair clearances, a column, a counter,
    two doors, accessible, and two place-tied turning circles."""
    tables = []
    for k, (x, y) in enumerate([(1.0, 1.4), (3.6, 1.4), (6.0, 1.4), (1.0, 4.4), (3.6, 4.4),
                                (6.0, 4.4), (1.0, 7.4), (3.6, 7.4), (6.0, 7.4), (6.4, 9.6)], 1):
        tables.append({"name": f"Table {k}", "type": "dining_table", "width": 1.2 if k % 2 else 0.7,
                       "depth": 0.75 if k % 2 else 0.7, "at": [x, y],
                       "clearance": {"front": 0.75, "back": 0.75, "left": 0, "right": 0}})
    tables.append({"name": "Counter", "type": "other", "width": 3.0, "depth": 0.7, "at": [0.6, 11.3], "height": 1.1})
    return {"units": "m", "size": [8.0, 12.0],
            "doors": [{"name": "Entrance", "at": [4.0, 0], "width": 1.0, "hinge": "left", "entrance": True},
                      {"name": "WC door", "at": [8.0, 11.0], "width": 0.9, "hinge": "right", "swing": "out"}],
            "obstacles": [{"name": "Column", "type": "column", "rect": [3.0, 6.3, 0.4, 0.4]}],
            "furniture": tables, "min_walkway": 1.2, "accessible": True,
            "turning_circles": [{"near": "WC door", "side": "front", "within": 1.2, "for": "WC"},
                                {"near": "Table 9", "side": "front", "within": 1.5, "for": "wheelchair place"}]}


class PlaceTiedTurningCircleTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, d):
        return self.m.check(self.m.load(d))

    def test_circle_in_front_of_a_door_passes_when_that_zone_is_clear(self):
        d = room()
        d["turning_circles"] = [{"near": "Door", "side": "front", "within": 1.2, "for": "Noor"}]
        r = self.check(d)
        self.assertEqual(r["fails"], [])
        (cx, cy), who, ok, dm = r["turns"][0]
        self.assertTrue(ok)
        self.assertEqual((who, dm), ("Noor", 1.5))
        self.assertLessEqual(((cx - 3.4) ** 2 + cy ** 2) ** 0.5, 1.2 + 1e-6)   # the centre is in the zone

    def test_tight_lobby_fails_and_reports_the_clear_diameter(self):
        d = lobby()
        d["turning_circles"] = [{"near": "Bathroom door", "side": "front", "within": 1.2, "for": "guest"}]
        r = self.check(d)
        msg = [f for f in r["fails"] if "turning circle for guest in front of Bathroom door" in f]
        self.assertEqual(len(msg), 1, r["fails"])
        self.assertIn("doesn't fit: the largest clear circle there is 1.35 m across", msg[0])
        self.assertFalse(r["turns"][0][2])

    def test_a_clear_circle_elsewhere_never_passes_a_place_tied_one(self):
        d = lobby()
        d["size"] = [3.0, 4.0]                 # room enough by the entrance, not by the bathroom door
        d["doors"][0]["at"], d["doors"][1]["at"] = [1.5, 0], [0.5, 4.0]
        d["furniture"] = [{"name": "Wardrobe", "type": "other", "width": 2.0, "depth": 0.6, "at": [1.0, 2.4]},
                          {"name": "Bench", "type": "other", "width": 0.4, "depth": 1.0, "at": [0.95, 3.0]}]
        d["turning_circles"] = [{"near": "Bathroom door", "side": "front", "within": 0.9}]
        r = self.check(d)
        self.assertTrue(any("doesn't fit" in f or "no clear" in f for f in r["fails"]), r["fails"])
        d.pop("turning_circles")
        d["accessible"] = True
        self.assertTrue(self.check(d)["turns"][0][2])   # anywhere in the room, there is room to turn

    def test_circle_beside_a_piece_searches_that_side(self):
        d = room()
        d["turning_circles"] = [{"near": "Bed", "side": "front", "within": 1.4, "diameter": 1.2, "for": "foot of bed"}]
        r = self.check(d)
        (cx, cy), _, ok, dm = r["turns"][0]
        self.assertTrue(ok, r["fails"])
        self.assertEqual(dm, 1.2)
        self.assertTrue(1.2 <= cx <= 2.8 and 0.1 <= cy <= 1.5)   # in the band in front of the bed's foot

    def test_bad_place_tied_input(self):
        for bad in ({"near": "Sofa"}, {"near": "Door", "side": "back"}, {"near": "Bed", "side": "up"},
                    {"near": "Door", "within": 0}):
            d = room()
            d["turning_circles"] = [bad]
            with self.assertRaises(self.m.InputError, msg=str(bad)):
                self.m.load(d)


class SpeedTest(unittest.TestCase):
    def test_a_cafe_sized_layout_checks_in_under_five_seconds(self):
        import time
        m = load(SKILL, SCRIPT)
        plan = m.load(cafe())
        t0 = time.monotonic()
        r = m.check(plan)
        self.assertLess(time.monotonic() - t0, 5.0)
        self.assertFalse(r["incomplete"])
        self.assertEqual(len(r["turns"]), 2)

    def test_max_seconds_stops_the_long_checks_and_says_so(self):
        with workdir() as d:
            f = os.path.join(d, "cafe.json")
            write(f, json.dumps(cafe()))
            code, out, _ = run(SKILL, SCRIPT, f, "--max-seconds", "0.000001")
            self.assertEqual(code, 2, out)
            self.assertIn("INCOMPLETE", out)
            self.assertNotIn("PASS", out)
            code, out, _ = run(SKILL, SCRIPT, f, "--max-seconds", "0.000001", "--json")
            data = json.loads(out)
            self.assertTrue(data["incomplete"])
            self.assertFalse(data["pass"])
            self.assertEqual(run(SKILL, SCRIPT, f, "--max-seconds", "0")[0], 2)
            self.assertIn(run(SKILL, SCRIPT, f)[0], (0, 1))


if __name__ == "__main__":
    unittest.main()

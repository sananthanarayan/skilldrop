import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "run-of-show", "show_check.py"


def show():
    """Two rooms, a 15-minute turnaround in the hall, a 5-minute walk between them."""
    return {"published_end": "12:30",
            "rooms": [{"name": "Hall", "open": "08:00", "close": "13:00", "turnaround": 15},
                      {"name": "Studio", "open": "09:00", "close": "13:00", "turnaround": 10}],
            "travel": [{"between": ["Hall", "Studio"], "minutes": 5}],
            "items": [{"id": "doors", "title": "Doors", "room": "Hall", "start": "08:30", "end": "09:00"},
                      {"id": "key", "title": "Keynote", "room": "Hall", "start": "09:15", "duration": 45,
                       "people": ["Ana"], "setup": 15},
                      {"id": "ws", "title": "Workshop", "room": "Studio", "start": "10:10", "end": "11:00",
                       "people": ["Ana"]},
                      {"id": "panel", "title": "Panel", "room": "Hall", "start": "10:15", "end": "11:15",
                       "people": ["Joe"], "changeover": 20},
                      {"id": "close", "title": "Close", "room": "Hall", "start": "11:35", "end": "12:00",
                       "people": ["Joe"]}]}


def item(s, iid):
    return next(i for i in s["items"] if i["id"] == iid)


class ShowCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, s, **kw):
        return self.m.check(self.m.load(s), **kw)

    def test_good_show_passes_clean(self):
        r = self.check(show())
        self.assertEqual(r["fails"], [])
        self.assertEqual(r["warns"], [])

    def test_end_before_start_fails(self):
        s = show()
        item(s, "ws")["end"] = "10:00"
        self.assertTrue(any("Workshop (10:10) ends at 10:00, not after it starts" in f for f in self.check(s)["fails"]))

    def test_overlap_in_one_room_fails(self):
        s = show()
        item(s, "panel")["start"] = "09:50"
        r = self.check(s)
        self.assertTrue(any("Keynote (09:15) and Panel (09:50) overlap in Hall by 10 min" in f for f in r["fails"]))
        self.assertEqual(r["bad"], ["key", "panel"])

    def test_short_turnaround_fails(self):
        s = show()
        item(s, "panel")["start"] = "10:05"
        self.assertTrue(any("Hall: 5 min between Keynote (09:15) and Panel (10:05), 15 min needed for the room's turnaround" in f
                            for f in self.check(s)["fails"]))

    def test_short_setup_and_changeover_fail(self):
        s = show()
        item(s, "panel")["setup"] = 30
        self.assertTrue(any("30 min needed for Panel's setup" in f for f in self.check(s)["fails"]))
        s = show()
        item(s, "close")["start"] = "11:30"
        self.assertTrue(any("15 min between Panel (10:15) and Close (11:30), 20 min needed for Panel's changeover" in f
                            for f in self.check(s)["fails"]))

    def test_outside_venue_hours_fails(self):
        s = show()
        item(s, "ws")["start"] = "08:50"
        self.assertTrue(any("Workshop (08:50) starts before Studio opens at 09:00" in f for f in self.check(s)["fails"]))
        s = show()
        item(s, "doors")["start"], item(s, "doors")["end"] = "07:50", "08:20"
        self.assertTrue(any("starts before Hall opens" in f for f in self.check(s)["fails"]))
        s = show()
        item(s, "close")["end"] = "13:10"
        self.assertTrue(any("ends at 13:10, after Hall closes at 13:00" in f for f in self.check(s)["fails"]))

    def test_setup_before_opening_fails(self):
        s = show()
        item(s, "key")["setup"] = 90
        item(s, "doors")["start"], item(s, "doors")["end"] = "08:00", "08:10"
        self.assertTrue(any("Keynote (09:15) starts with 90 min setup before Hall opens" in f for f in self.check(s)["fails"]))

    def test_person_in_two_places_fails(self):
        s = show()
        item(s, "ws")["start"] = "09:40"
        self.assertTrue(any("Ana is needed at Keynote (09:15) in Hall and Workshop (09:40) in Studio at once" in f
                            for f in self.check(s)["fails"]))

    def test_no_time_to_walk_fails(self):
        s = show()
        item(s, "ws")["start"] = "10:02"
        self.assertTrue(any("Ana has 2 min to get from Hall to Studio between Keynote and Workshop; the walk takes 5" in f
                            for f in self.check(s)["fails"]))

    def test_no_break_long_gap_and_overrun_warn(self):
        s = show()
        item(s, "close")["start"], item(s, "close")["end"] = "12:20", "12:45"
        item(s, "panel")["people"] = ["Ana"]
        item(s, "ws")["start"], item(s, "ws")["end"] = "11:20", "12:20"
        item(s, "ws")["people"] = []
        warns = self.check(s, max_hours=1.5, brk=20)["warns"]
        self.assertTrue(any(w.startswith("Ana works from 09:15 to 11:15 without a 20-minute break") for w in warns))
        self.assertIn("Hall is empty for 65 min between Panel and Close", warns)
        self.assertTrue(any("Close ends at 12:45, 15 min after the published end of 12:30" in w for w in warns))

    def test_days_are_checked_apart(self):
        s = show()
        for it in s["items"]:
            it["day"] = "Day 1"
        s["items"].append({"id": "d2", "title": "Keynote again", "room": "Hall", "start": "09:15", "end": "10:00",
                           "people": ["Ana"], "day": "Day 2"})
        self.assertEqual(self.check(s)["fails"], [])

    def test_bad_inputs_are_named(self):
        base = {"items": [{"title": "X", "room": "R", "start": "09:00", "end": "10:00"}]}
        for change, msg in ((lambda d: d["items"][0].update(start="9.30"), "24-hour time"),
                            (lambda d: d["items"][0].pop("end"), "needs an end or a duration"),
                            (lambda d: d["items"][0].update(room=""), "needs a room"),
                            (lambda d: d.update(items=[]), "no items"),
                            (lambda d: d.update(travel=[{"between": ["R"], "minutes": 5}]), "travel 1"),
                            (lambda d: d["items"][0].update(setup=-5), "number of minutes")):
            d = json.loads(json.dumps(base))
            change(d)
            with self.assertRaises(self.m.BadInput) as cm:
                self.m.load(d)
            self.assertIn(msg, str(cm.exception))


class ShowCheckCliTest(unittest.TestCase):
    def test_pass_and_svg(self):
        with workdir() as d:
            f = write(os.path.join(d, "show.json"), json.dumps(show()))
            out = os.path.join(d, "timeline.svg")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--svg", out)
            self.assertEqual(code, 0)
            self.assertIn("09:15–10:00  Hall: Keynote — Ana", stdout)
            self.assertIn("PASS", stdout)
            svg = read(out)
            self.assertIn(">Studio</text>", svg)
            self.assertIn("10:10–11:00", svg)

    def test_clash_exits_1_and_marks_red(self):
        s = show()
        item(s, "panel")["start"] = "09:50"
        with workdir() as d:
            f = write(os.path.join(d, "show.json"), json.dumps(s))
            out = os.path.join(d, "timeline.svg")
            code, stdout, _ = run(SKILL, SCRIPT, f, "--svg", out)
            self.assertEqual(code, 1)
            self.assertIn("FAIL Keynote (09:15) and Panel (09:50) overlap", stdout)
            self.assertIn("#c62828", read(out))

    def test_json_output(self):
        with workdir() as d:
            f = write(os.path.join(d, "show.json"), json.dumps(show()))
            code, stdout, _ = run(SKILL, SCRIPT, f, "--json")
            doc = json.loads(stdout)
            self.assertEqual(code, 0)
            self.assertTrue(doc["pass"])
            self.assertEqual(doc["items"][0]["start"], "08:30")

    def test_bad_input_exits_2(self):
        with workdir() as d:
            f = write(os.path.join(d, "show.json"), json.dumps({"items": [{"title": "X", "room": "R", "start": "nine"}]}))
            code, out, _ = run(SKILL, SCRIPT, f)
            self.assertEqual(code, 2)
            self.assertIn("24-hour time", out)
            self.assertEqual(run(SKILL, SCRIPT, os.path.join(d, "missing.json"))[0], 2)


if __name__ == "__main__":
    unittest.main()

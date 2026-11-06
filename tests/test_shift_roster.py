import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "shift-roster", "roster_check.py"


def roster():
    """Two people, two shifts, every rule met."""
    return {"rules": {"min_rest_hours": 11, "max_consecutive_days": 6, "max_hours_per_day": 12},
            "staff": [{"id": "a", "name": "Ana", "skills": ["till", "keyholder"], "max_hours": 40, "contracted_hours": 16},
                      {"id": "b", "name": "Bo", "skills": ["till"], "max_hours": 40, "contracted_hours": 16}],
            "shifts": [{"id": "mon", "day": "Mon", "start": "09:00", "end": "17:00", "needs": {"keyholder": 1, "till": 1}},
                       {"id": "tue", "day": "Tue", "start": "09:00", "end": "17:00", "needs": {"keyholder": 1, "till": 1}}],
            "assignments": {"mon": ["a", "b"], "tue": ["a", "b"]}}


class RosterCheckTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def check(self, doc):
        return self.m.check(self.m.load(doc))

    def fails(self, doc):
        return self.check(doc)["fails"]

    def test_good_rota_passes_clean(self):
        res = self.check(roster())
        self.assertEqual(res["fails"], [])
        self.assertEqual(res["warns"], [])
        self.assertEqual(res["people"]["a"]["hours"], 16)

    def test_short_of_a_needed_skill_fails(self):
        d = roster()
        d["assignments"]["mon"] = ["b"]
        self.assertTrue(any("is short 1 keyholder" in f for f in self.fails(d)))

    def test_people_are_matched_to_needs_one_each(self):
        # Ana could fill either need, but only she holds keys: Bo takes the till, Ana the keys.
        d = roster()
        d["assignments"]["mon"] = ["b", "a"]
        self.assertEqual(self.fails(d), [])
        # two people who can only work the till don't cover a keyholder need
        d["staff"].append({"id": "c", "name": "Cy", "skills": ["till"]})
        d["assignments"]["mon"] = ["b", "c"]
        self.assertTrue(any("short 1 keyholder" in f for f in self.fails(d)))

    def test_overlapping_shifts_fail(self):
        d = roster()
        d["shifts"].append({"id": "mon-late", "day": "Mon", "start": "16:00", "end": "22:00", "needs": {"till": 1}})
        d["assignments"]["mon-late"] = ["b"]
        self.assertTrue(any("Bo is on mon and mon-late, which overlap" in f for f in self.fails(d)))

    def test_rostered_while_unavailable_fails(self):
        d = roster()
        d["staff"][1]["unavailable"] = [{"day": "Tue", "start": "12:00", "end": "14:00", "reason": "dentist"}]
        self.assertTrue(any("Bo is on tue but is unavailable then (dentist)" in f for f in self.fails(d)))

    def test_over_weekly_maximum_fails(self):
        d = roster()
        d["staff"][1]["max_hours"] = 12
        self.assertTrue(any("Bo works 16 h in week 1, over their 12 h maximum" in f for f in self.fails(d)))

    def test_over_daily_maximum_fails(self):
        d = roster()
        d["shifts"][0]["end"] = "23:00"
        self.assertTrue(any("over the 12 h daily maximum" in f for f in self.fails(d)))

    def test_short_rest_across_midnight_fails(self):
        d = roster()
        # a late shift ending at 01:00 Tuesday, then the 09:00 Tuesday shift: 8 h rest
        d["shifts"][0].update(start="17:00", end="01:00")
        f = self.fails(d)
        self.assertTrue(any("gets 8 h rest between mon" in x and "under the 11 h minimum" in x for x in f), f)

    def test_overnight_shift_counts_its_hours_and_ends_next_day(self):
        d = roster()
        d["shifts"] = [{"id": "night", "day": "Mon", "start": "22:00", "end": "06:00", "needs": {"till": 1}}]
        d["assignments"] = {"night": ["b"]}
        res = self.check(d)
        self.assertEqual(res["people"]["b"]["hours"], 8)
        self.assertEqual(res["people"]["b"]["night"], 1)

    def test_rest_across_the_week_boundary_of_a_fortnight(self):
        d = roster()
        d["shifts"] = [{"id": "sun", "day": "Sun", "start": "14:00", "end": "23:00", "needs": {"till": 1}},
                       {"id": "mon2", "day": "Mon", "week": 2, "start": "06:00", "end": "12:00", "needs": {"till": 1}}]
        d["assignments"] = {"sun": ["b"], "mon2": ["b"]}
        self.assertTrue(any("gets 7 h rest" in f for f in self.fails(d)))

    def test_too_many_consecutive_days_fails(self):
        d = roster()
        d["shifts"] = [{"id": f"d{i}", "day": day, "start": "09:00", "end": "13:00", "needs": {"till": 1}}
                       for i, day in enumerate(self.m.DAYS)]
        d["assignments"] = {f"d{i}": ["b"] for i in range(7)}
        self.assertTrue(any("Bo works 7 days in a row" in f for f in self.fails(d)))

    def test_filling_a_role_without_the_skill_fails(self):
        d = roster()
        d["assignments"]["mon"] = ["a", {"id": "b", "as": "keyholder"}]
        f = self.fails(d)
        self.assertTrue(any("Bo is on mon as keyholder but doesn't have that skill" in x for x in f))

    def test_someone_with_none_of_the_needed_skills_fails(self):
        d = roster()
        d["staff"].append({"id": "c", "name": "Cy", "skills": ["stock"]})
        d["assignments"]["mon"] = ["a", "b", "c"]
        self.assertTrue(any("Cy is on mon but has none of the skills it needs" in f for f in self.fails(d)))

    def test_any_need_matches_everyone(self):
        d = roster()
        d["shifts"][0]["needs"] = {"any": 2}
        self.assertEqual(self.fails(d), [])

    def test_hours_far_from_contracted_warns(self):
        d = roster()
        d["staff"][0]["contracted_hours"] = 37.5
        self.assertTrue(any("Ana works 16 h against 37.5 h contracted" in w for w in self.check(d)["warns"]))

    def test_uneven_weekends_warn(self):
        d = roster()
        d["shifts"] = [{"id": f"w{i}", "day": day, "start": "09:00", "end": "13:00", "needs": {"till": 1}}
                       for i, day in enumerate(["Sat", "Sun"])]
        d["assignments"] = {"w0": ["a"], "w1": ["a"]}
        warns = self.check(d)["warns"]
        self.assertTrue(any("weekend shifts fall unevenly: Ana has 2, Bo has 0" in w for w in warns), warns)

    def test_short_shift_names_who_is_free_to_take_it(self):
        d = roster()
        d["assignments"]["tue"] = ["a"]
        res = self.check(d)
        self.assertTrue(any("tue is short 1 till, and qualified people are free to take it: Bo" in w for w in res["warns"]))

    def test_dates_work_like_days(self):
        d = roster()
        d["shifts"][0].pop("day")
        d["shifts"][1].pop("day")
        d["shifts"][0]["date"], d["shifts"][1]["date"] = "2026-11-09", "2026-11-10"
        self.assertEqual(self.fails(d), [])

    def test_summary_is_read_from_the_checked_rota(self):
        d = roster()
        d["shifts"][1]["day"] = "Sat"
        r = self.m.load(d)
        sm = self.m.summary(r, self.m.check(r))
        ana = next(p for p in sm["people"] if p["id"] == "a")
        self.assertEqual((ana["hours"], ana["shifts"], ana["weekend_days"], ana["days_in_a_row"]), (16, 2, 1, 1))
        self.assertTrue(any("as keyholder" in t for t in ana["on"]))
        self.assertEqual(sm["shifts"][0]["cover"], {"keyholder": [1, 1], "till": [1, 1]})
        self.assertEqual(sm["shifts"][0]["who"], ["Ana", "Bo"])

    def test_days_in_a_row_counts_the_longest_run(self):
        d = roster()
        d["shifts"].append({"id": "wed", "day": "Wed", "start": "09:00", "end": "17:00", "needs": {"till": 1}})
        d["assignments"]["wed"] = ["a"]
        r = self.m.load(d)
        sm = self.m.summary(r, self.m.check(r))
        self.assertEqual(next(p for p in sm["people"] if p["id"] == "a")["days_in_a_row"], 3)

    def test_compare_lists_only_what_moved(self):
        new, old = roster(), roster()
        old["assignments"]["tue"] = ["a"]
        new["assignments"]["mon"] = ["a", "b"]
        changes = self.m.compare(self.m.load(new), self.m.load(old))
        self.assertEqual(len(changes), 1)
        self.assertEqual((changes[0]["shift"], changes[0]["added"], changes[0]["removed"]), ("tue", ["Bo"], []))
        self.assertEqual(self.m.compare(self.m.load(roster()), self.m.load(roster())), [])

    def test_bad_input_is_an_input_error(self):
        for doc in ({}, {"staff": [], "shifts": []}, dict(roster(), assignments={"nope": ["a"]}),
                    dict(roster(), assignments={"mon": ["zed"]})):
            with self.assertRaises(self.m.InputError):
                self.m.load(doc)
        d = roster()
        d["shifts"][0]["start"] = "9am"
        with self.assertRaises(self.m.InputError):
            self.m.load(d)


class RosterCheckCliTest(unittest.TestCase):
    def test_exit_codes_and_svg(self):
        with workdir() as d:
            good = write(os.path.join(d, "good.json"), json.dumps(roster()))
            code, out, _ = run(SKILL, SCRIPT, good, "--svg", os.path.join(d, "week.svg"))
            self.assertEqual(code, 0, out)
            svg = read(os.path.join(d, "week.svg"))
            self.assertIn("<svg", svg)
            self.assertIn("Ana", svg)
            bad = roster()
            bad["assignments"]["mon"] = ["b"]
            code, out, _ = run(SKILL, SCRIPT, write(os.path.join(d, "bad.json"), json.dumps(bad)))
            self.assertEqual(code, 1)
            self.assertIn("FAIL", out)
            code, out, _ = run(SKILL, SCRIPT, write(os.path.join(d, "broken.json"), "{not json"))
            self.assertEqual(code, 2)
            code, out, _ = run(SKILL, SCRIPT, os.path.join(d, "missing.json"))
            self.assertEqual(code, 2)

    def test_summary_and_compare_on_the_command_line(self):
        with workdir() as d:
            new, old = roster(), roster()
            old["assignments"]["tue"] = ["a"]
            n = write(os.path.join(d, "new.json"), json.dumps(new))
            o = write(os.path.join(d, "old.json"), json.dumps(old))
            code, out, _ = run(SKILL, SCRIPT, n, "--summary", "--compare", o)
            self.assertEqual(code, 0, out)
            self.assertIn("Per person", out)
            self.assertIn("Per shift", out)
            self.assertIn("added Bo", out)
            code, out, _ = run(SKILL, SCRIPT, n, "--json", "--summary", "--compare", o)
            doc = json.loads(out)
            self.assertIn("summary", doc)
            self.assertEqual(doc["changes"][0]["added"], ["Bo"])
            code, out, _ = run(SKILL, SCRIPT, n, "--compare", os.path.join(d, "missing.json"))
            self.assertEqual(code, 2)

    def test_json_output(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, write(os.path.join(d, "r.json"), json.dumps(roster())), "--json")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["fails"], [])


if __name__ == "__main__":
    unittest.main()

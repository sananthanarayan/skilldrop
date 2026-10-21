import copy
import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "web-performance-review", "lh_summary.py"
SITE = "https://shop.example.test"
CDN = "https://cdn.chatter.example"


def lhr():
    """A small Lighthouse result: mobile default throttling, a lazy-loaded hero image as LCP."""
    return {
        "lighthouseVersion": "12.0.0",
        "requestedUrl": SITE + "/",
        "finalDisplayedUrl": SITE + "/",
        "fetchTime": "2026-10-01T10:00:00.000Z",
        "configSettings": {
            "formFactor": "mobile", "throttlingMethod": "simulate",
            "throttling": {"rttMs": 150, "throughputKbps": 1638.4, "cpuSlowdownMultiplier": 4},
            "screenEmulation": {"mobile": True, "width": 412, "height": 823, "deviceScaleFactor": 1.75},
        },
        "environment": {"benchmarkIndex": 1500},
        "runWarnings": ["The page loaded too slowly to finish within the time limit."],
        "categories": {"performance": {"score": 0.62}},
        "entities": [
            {"name": "ChatterBox", "origins": [CDN]},
            {"name": "Shop", "isFirstParty": True, "origins": [SITE]},
        ],
        "audits": {
            "first-contentful-paint": {"numericValue": 1500, "displayValue": "1.5 s"},
            "largest-contentful-paint": {"numericValue": 3100, "displayValue": "3.1 s"},
            "total-blocking-time": {"numericValue": 650, "displayValue": "650 ms"},
            "cumulative-layout-shift": {"numericValue": 0.1, "displayValue": "0.1"},
            "speed-index": {"numericValue": 4000},
            "interaction-to-next-paint": {"scoreDisplayMode": "notApplicable"},
            "largest-contentful-paint-element": {
                "scoreDisplayMode": "informative",
                "details": {"type": "list", "items": [
                    {"type": "node", "selector": "main > img.hero", "nodeLabel": "Hero",
                     "snippet": '<img class="hero" src="hero.jpg" loading="lazy">'},
                    {"type": "table", "items": [
                        {"phase": "TTFB", "timing": 600},
                        {"phase": "Load Delay", "timing": 1500},
                        {"phase": "Load Time", "timing": 700},
                        {"phase": "Render Delay", "timing": 200},
                    ]},
                ]},
            },
            "lcp-lazy-loaded": {"score": 0, "scoreDisplayMode": "binary", "title": "LCP image was lazily loaded"},
            "prioritize-lcp-image": {
                "score": 0, "scoreDisplayMode": "metricSavings", "title": "Preload the LCP image",
                "metricSavings": {"LCP": 1200},
                "details": {"type": "opportunity", "overallSavingsMs": 1200,
                            "items": [{"url": SITE + "/hero.jpg"}]},
            },
            "render-blocking-resources": {
                "score": 0.5, "scoreDisplayMode": "metricSavings", "title": "Eliminate render-blocking resources",
                "metricSavings": {"FCP": 300, "LCP": 300},
                "details": {"type": "opportunity", "overallSavingsMs": 300,
                            "items": [{"url": SITE + "/app.css", "totalBytes": 20480, "wastedMs": 300.4}]},
            },
            "unused-javascript": {
                "score": 0.3, "scoreDisplayMode": "metricSavings", "title": "Reduce unused JavaScript",
                "metricSavings": {"TBT": 150},
                "details": {"type": "opportunity", "overallSavingsMs": 150,
                            "items": [{"url": CDN + "/loader.js"}]},
            },
            "modern-image-formats": {
                "score": 0.4, "scoreDisplayMode": "metricSavings", "title": "Serve images in modern formats",
                "metricSavings": {"FCP": 0, "LCP": 0},
                "details": {"type": "opportunity", "overallSavingsMs": 900, "overallSavingsBytes": 1228800,
                            "items": [{"url": SITE + "/grid.jpg"}, {"url": SITE + "/hero.jpg"}]},
            },
            "unsized-images": {
                "score": 0, "scoreDisplayMode": "metricSavings", "title": "Image elements lack width and height",
                "metricSavings": {"CLS": 0},
                "details": {"type": "table", "items": [
                    {"url": SITE + "/banner.png", "node": {"selector": "img.banner"}}]},
            },
            "uses-long-cache-ttl": {"score": 1, "scoreDisplayMode": "metricSavings", "title": "Cache policy"},
            "layout-shifts": {
                "scoreDisplayMode": "informative",
                "details": {"type": "table", "items": [
                    {"node": {"selector": "h1"}, "score": 0.02,
                     "subItems": {"items": [{"cause": "Web font loaded", "extra": {"url": "font.woff2"}}]}},
                    {"node": {"selector": "div.ad"}, "score": 0.06,
                     "subItems": {"items": [{"cause": "Injected iframe"}]}},
                ]},
            },
            "long-tasks": {
                "scoreDisplayMode": "informative",
                "details": {"type": "table", "items": [
                    {"url": SITE + "/app.js", "duration": 90, "startTime": 1200},
                    {"url": CDN + "/loader.js", "duration": 170.4, "startTime": 3100},
                    {"url": CDN + "/loader.js", "duration": 60, "startTime": 3500},
                ]},
            },
            "third-party-summary": {
                "scoreDisplayMode": "informative",
                "details": {"type": "table", "items": [
                    {"entity": "ChatterBox", "mainThreadTime": 412.3, "blockingTime": 120, "transferSize": 51200}]},
            },
        },
    }


def psi(lighthouse_result=None):
    doc = {"loadingExperience": {
        "id": SITE + "/", "origin_fallback": True,
        "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2400, "distributions": [
                {"min": 0, "max": 2500, "proportion": 0.81}, {"min": 2500, "max": 4000, "proportion": 0.12}]},
            "INTERACTION_TO_NEXT_PAINT": {"percentile": 180},
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 14},
        }}}
    if lighthouse_result is not None:
        doc["lighthouseResult"] = lighthouse_result
    return doc


def crux():
    return {"record": {
        "key": {"origin": SITE, "formFactor": "PHONE"},
        "collectionPeriod": {"firstDate": {"year": 2026, "month": 9, "day": 1},
                             "lastDate": {"year": 2026, "month": 9, "day": 28}},
        "metrics": {
            "cumulative_layout_shift": {"percentiles": {"p75": "0.05"},
                                        "histogram": [{"start": "0.00", "end": "0.10", "density": 0.9}]},
            "largest_contentful_paint": {"percentiles": {"p75": 4100}},
        }}}


def dump(d, name, doc):
    return write(os.path.join(d, name), json.dumps(doc))


class LhSummaryTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def summary(self, *args, docs=None):
        """Run the CLI with --json on the given documents and return the parsed output."""
        with workdir() as d:
            paths = [dump(d, f"r{i}.json", doc) for i, doc in enumerate(docs or [lhr()])]
            code, out, err = run(SKILL, SCRIPT, *paths, *args, "--json", cwd=d)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    # ---- thresholds and field verdicts

    def test_rate_boundaries_are_inclusive_for_good_and_exclusive_for_poor(self):
        thr = self.m.FIELD_THRESHOLDS["LCP"]
        self.assertEqual(self.m.rate(2500, thr), "good")
        self.assertEqual(self.m.rate(4000, thr), "needs-improvement")
        self.assertEqual(self.m.rate(4001, thr), "poor")
        self.assertEqual(self.m.rate(0.1, self.m.FIELD_THRESHOLDS["CLS"]), "good")
        self.assertIsNone(self.m.rate(None, thr))

    def test_cwv_outcome_passed_failed_and_unassessable(self):
        def field(**p75):
            return {"metrics": {k: {"p75": v, "rating": self.m.rate(v, self.m.FIELD_THRESHOLDS[k])}
                                for k, v in p75.items()}}
        self.assertEqual(self.m.cwv_outcome(field(LCP=2000, INP=150, CLS=0.05)), "PASSED")
        self.assertEqual(self.m.cwv_outcome(field(LCP=2000, CLS=0.05)), "PASSED (no INP data)")
        self.assertEqual(self.m.cwv_outcome(field(LCP=2600, INP=600, CLS=0.05)),
                         "FAILED: LCP needs-improvement, INP poor")
        self.assertTrue(self.m.cwv_outcome(field(LCP=2000, INP=150)).startswith("cannot be assessed: no CLS"))

    def test_psi_field_divides_cls_by_100_and_flags_origin_fallback(self):
        r = self.summary(docs=[psi(lhr())])
        f = r["fields"][0]
        self.assertEqual(f["scope"], "url")
        self.assertTrue(f["origin_fallback"])
        self.assertAlmostEqual(f["metrics"]["CLS"]["p75"], 0.14)
        self.assertEqual(f["metrics"]["CLS"]["rating"], "needs-improvement")
        self.assertEqual(f["metrics"]["LCP"]["good_share"], 0.81)
        self.assertEqual(f["core_web_vitals"], "FAILED: CLS needs-improvement")

    def test_psi_markdown_states_origin_fallback(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, dump(d, "psi.json", psi(lhr())))
        self.assertEqual(code, 0, err)
        self.assertIn("ORIGIN FALLBACK", out)
        self.assertIn("| CLS | 0.14 | needs-improvement | - |", out)
        self.assertIn("| LCP | 2.40 s | good | 81% |", out)

    def test_crux_record_read_as_origin_field_data_only(self):
        r = self.summary(docs=[crux()])
        self.assertIsNone(r["lab"])
        f = r["fields"][0]
        self.assertEqual((f["source"], f["scope"], f["form_factor"]), ("CrUX API", "origin", "PHONE"))
        self.assertEqual(f["period"], ["2026-09-01", "2026-09-28"])
        self.assertEqual(f["metrics"]["CLS"]["p75"], 0.05)
        self.assertEqual(f["metrics"]["CLS"]["good_share"], 0.9)
        self.assertEqual(f["core_web_vitals"], "FAILED: LCP poor")

    def test_manual_p75_flags_become_field_data(self):
        r = self.summary("--lcp-p75", "3100", "--inp-p75", "420", "--cls-p75", "0.04",
                         "--field-source", "RUM")
        f = r["fields"][0]
        self.assertEqual(f["source"], "RUM")
        self.assertEqual({k: v["rating"] for k, v in f["metrics"].items()},
                         {"LCP": "needs-improvement", "INP": "needs-improvement", "CLS": "good"})

    def test_field_flag_adds_crux_data_to_a_lighthouse_report(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, dump(d, "lh.json", lhr()),
                                 "--field", dump(d, "crux.json", crux()), "--json")
        self.assertEqual(code, 0, err)
        r = json.loads(out)
        self.assertEqual(r["fields"][0]["source"], "CrUX API")
        self.assertIsNotNone(r["lab"])

    def test_no_field_data_says_cwv_cannot_be_stated(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, dump(d, "lh.json", lhr()))
        self.assertEqual(code, 0, err)
        self.assertIn("Core Web Vitals pass/fail cannot be stated from lab data", out)

    # ---- lab run

    def test_run_info_names_default_mobile_preset_and_simulation(self):
        run_ = self.summary()["run"]
        self.assertEqual(run_["form_factor"], "mobile")
        self.assertEqual(run_["screen"], "412x823 @1.75x")
        self.assertTrue(run_["preset"].startswith("Lighthouse default mobile"))
        self.assertIn("simulated", run_["method_note"])
        self.assertEqual(len(run_["run_warnings"]), 1)

    def test_run_info_desktop_and_provided_presets(self):
        doc = lhr()
        doc["configSettings"]["throttling"] = {"rttMs": 40, "throughputKbps": 10240, "cpuSlowdownMultiplier": 1}
        self.assertTrue(self.m.run_info(doc)["preset"].startswith("Lighthouse desktop preset"))
        doc["configSettings"]["throttlingMethod"] = "provided"
        self.assertTrue(self.m.run_info(doc)["preset"].startswith("no throttling applied"))

    def test_lab_metrics_rated_against_thresholds_and_score_scaled(self):
        lab = self.summary()["lab"]
        self.assertEqual(lab["performance_score"], 62)
        got = {m["metric"]: (m["value"], m["rating"]) for m in lab["metrics"]}
        self.assertEqual(got, {"FCP": (1500, "good"), "LCP": (3100, "needs-improvement"),
                               "TBT": (650, "poor"), "CLS": (0.1, "good"), "Speed Index": (4000, None)})

    def test_lcp_element_phases_and_dominant_phase(self):
        lcp = self.summary()["lcp"]
        self.assertEqual(lcp["element"]["selector"], "main > img.hero")
        self.assertEqual([(p["phase"], p["ms"], p["share"]) for p in lcp["phases"]], [
            ("TTFB", 600, "20%"), ("Resource load delay", 1500, "50%"),
            ("Resource load duration", 700, "23%"), ("Element render delay", 200, "7%")])
        self.assertEqual(lcp["dominant_phase"], "Resource load delay")
        self.assertIn("loading=lazy", lcp["dominant_phase_points_to"])

    def test_lcp_lazy_loaded_fetchpriority_and_resource(self):
        lcp = self.summary()["lcp"]
        self.assertTrue(lcp["lazy_loaded"])
        self.assertFalse(lcp["fetchpriority_high"])
        self.assertEqual(lcp["element_tag"], "img")
        self.assertEqual(lcp["lcp_resource_url"], SITE + "/hero.jpg")
        self.assertEqual(lcp["prioritize_savings_ms"], 1200)

    def test_layout_shifts_sorted_by_score_with_causes(self):
        cls = self.summary()["cls"]
        self.assertEqual([(s["element"]["selector"], s["score"]) for s in cls["shifts"]],
                         [("div.ad", 0.06), ("h1", 0.02)])
        self.assertEqual(cls["shifts"][1]["causes"], ["Web font loaded (font.woff2)"])
        self.assertEqual(cls["unsized_images"][0]["url"], SITE + "/banner.png")

    # ---- opportunities

    def test_opportunities_rank_by_vital_saving_and_load_only_goes_last(self):
        ops = self.summary()["opportunities"]
        ids = [o["id"] for o in ops]
        self.assertEqual(ids[:3], ["prioritize-lcp-image", "render-blocking-resources", "unused-javascript"])
        self.assertEqual(ids[-1], "modern-image-formats")
        self.assertNotIn("uses-long-cache-ttl", ids)
        self.assertNotIn("largest-contentful-paint", ids)
        last = ops[-1]
        self.assertEqual(last["metric_savings"], {})
        self.assertIn("LOAD-TIME ONLY", last["note"])

    def test_direct_effect_audit_gets_note_not_load_time_only(self):
        ops = {o["id"]: o for o in self.summary()["opportunities"]}
        self.assertIn("acts on CLS directly", ops["unsized-images"]["note"])

    def test_overlapping_savings_on_the_same_url_are_marked(self):
        ops = {o["id"]: o for o in self.summary()["opportunities"]}
        self.assertEqual(ops["prioritize-lcp-image"]["overlaps_with"], ["modern-image-formats (1 shared)"])
        self.assertEqual(ops["modern-image-formats"]["overlaps_with"], ["prioritize-lcp-image (1 shared)"])
        self.assertNotIn("overlaps_with", ops["render-blocking-resources"])

    def test_audit_moving_a_failing_field_vital_ranks_first(self):
        ops = self.summary("--cls-p75", "0.3")["opportunities"]
        self.assertEqual(ops[0]["id"], "unsized-images")
        self.assertEqual(ops[0]["moves_failing_field_vital"], ["CLS"])

    def test_tbt_saving_counts_as_moving_failing_field_inp(self):
        ops = self.summary("--inp-p75", "600")["opportunities"]
        self.assertEqual(ops[0]["id"], "unused-javascript")
        self.assertEqual(ops[0]["moves_failing_field_vital"], ["INP"])

    def test_top_limits_rows(self):
        self.assertEqual(len(self.summary("--top", "2")["opportunities"]), 2)

    # ---- main thread and render-blocking

    def test_long_tasks_attributed_to_entities_and_grouped_by_origin(self):
        mt = self.summary()["main_thread"]
        self.assertEqual([(t["by"], t["duration_ms"]) for t in mt["long_tasks"]],
                         [("ChatterBox", 170), ("Shop (1st party)", 90), ("ChatterBox", 60)])
        self.assertEqual(mt["long_tasks_by_origin"], [
            {"by": "ChatterBox", "count": 2, "total_ms": 230},
            {"by": "Shop (1st party)", "count": 1, "total_ms": 90}])
        self.assertEqual(mt["third_parties"], [
            {"entity": "ChatterBox", "main_thread_ms": 412, "blocking_ms": 120, "transfer_kb": 50}])

    def test_render_blocking_resources_listed(self):
        self.assertEqual(self.summary()["render_blocking"],
                         [{"url": SITE + "/app.css", "kb": 20, "wasted_ms": 300}])

    # ---- two reports

    def test_two_identical_setups_are_comparable_with_deltas(self):
        after = lhr()
        after["audits"]["largest-contentful-paint"]["numericValue"] = 2500
        after["categories"]["performance"]["score"] = 0.71
        c = self.summary(docs=[lhr(), after])["comparison"]
        self.assertTrue(c["comparable"])
        self.assertEqual(c["score"], [62, 71])
        self.assertIn({"metric": "LCP", "before": 3100, "after": 2500, "delta": -600}, c["deltas"])

    def test_different_device_or_throttling_is_not_comparable(self):
        after = copy.deepcopy(lhr())
        after["configSettings"]["formFactor"] = "desktop"
        after["configSettings"]["throttling"]["rttMs"] = 40
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, dump(d, "a.json", lhr()), dump(d, "b.json", after))
        self.assertEqual(code, 0, err)
        self.assertIn("NOT COMPARABLE", out)
        self.assertIn("form_factor: mobile -> desktop", out)
        self.assertIn("rtt_ms: 150 -> 40", out)

    # ---- CLI plumbing

    def test_markdown_out_file_and_stdin(self):
        with workdir() as d:
            target = os.path.join(d, "summary.md")
            code, out, err = run(SKILL, SCRIPT, "-", "-o", target, stdin=json.dumps(lhr()))
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")
            text = read(target)
        self.assertIn("# Lighthouse summary", text)
        self.assertIn("| LCP | 3.10 s | needs-improvement |", text)
        self.assertIn("Dominant phase: Resource load delay", text)

    def test_lighthouse_report_wrapped_in_lhr_key_is_accepted(self):
        r = self.summary(docs=[{"lhr": lhr()}])
        self.assertEqual(r["lab"]["performance_score"], 62)

    # ---- bad input: exit 2 with a message

    def assert_rejected(self, text, needle):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "in.json"), text))
        self.assertEqual(code, 2, out)
        self.assertIn(needle, err)
        self.assertNotIn("Traceback", err)

    def test_missing_file_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "absent.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_not_json_exits_2(self):
        self.assert_rejected("<html>not a report</html>", "is not JSON")

    def test_json_array_exits_2(self):
        self.assert_rejected("[]", "expected a JSON object")

    def test_unrelated_json_object_exits_2(self):
        self.assert_rejected('{"name": "package"}', "not a Lighthouse result")

    def test_runtime_error_report_exits_2(self):
        doc = lhr()
        doc["runtimeError"] = {"code": "NO_FCP", "message": "The page did not paint any content."}
        self.assert_rejected(json.dumps(doc), "Lighthouse run failed (NO_FCP")

    def test_user_flow_report_exits_2_with_hint(self):
        self.assert_rejected('{"steps": []}', "user-flow report")

    def test_more_than_two_reports_exits_2(self):
        with workdir() as d:
            p = dump(d, "a.json", lhr())
            code, _, err = run(SKILL, SCRIPT, p, p, p)
        self.assertEqual(code, 2)
        self.assertIn("pass one report, or two", err)

    def test_psi_with_failed_lighthouse_run_exits_2(self):
        failed = {"lighthouseVersion": "12.0.0", "audits": {},
                  "runtimeError": {"code": "NO_FCP", "message": "The page did not paint any content."}}
        self.assert_rejected(json.dumps(psi(failed)), "Lighthouse run failed")

    def test_non_utf8_file_exits_2_without_traceback(self):
        with workdir() as d:
            path = os.path.join(d, "utf16.json")
            with open(path, "w", encoding="utf-16") as f:
                f.write(json.dumps(lhr()))
            code, _, err = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

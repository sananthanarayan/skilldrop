import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "privacy-policy-check", "policy_scan.py"

PKG = {"dependencies": {"next": "15.0.0", "posthog-js": "1.0.0", "@sentry/nextjs": "8.0.0", "openai": "4.0.0",
                        "@stripe/stripe-js": "4.0.0"},
       "devDependencies": {"@segment/analytics-next": "1.0.0"}}
PAGE = '<script async src="https://connect.facebook.net/en_US/fbevents.js"></script>\n'
POLICY = """# Privacy Policy
We do not sell or share your personal information with third parties.
Payments are handled by Stripe.
Contact privacy@example.com. You can delete your account at any time; we delete data within 30 days.
"""


def app(d, pkg=PKG, page=PAGE):
    write(os.path.join(d, "app", "package.json"), json.dumps(pkg))
    write(os.path.join(d, "app", "src", "layout.tsx"), page)
    write(os.path.join(d, "app", "node_modules", "x", "index.js"), "fetch('https://api.mixpanel.com')")
    return os.path.join(d, "app")


class PolicyScanTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def scan(self, **kw):
        with workdir() as d:
            return self.m.scan_code(app(d, **kw))

    def test_finds_runtime_dependencies_and_script_tags_only(self):
        names = {i["service"][0] for i in self.scan()}
        self.assertEqual(names, {"PostHog", "Sentry", "OpenAI", "Stripe", "Meta Pixel / Facebook SDK"})

    def test_skips_node_modules_and_dev_dependencies(self):
        names = {i["service"][0] for i in self.scan()}
        self.assertNotIn("Mixpanel", names)
        self.assertNotIn("Segment", names)

    def test_other_manifests(self):
        with workdir() as d:
            write(os.path.join(d, "requirements.txt"), "anthropic==0.40.0\nsentry-sdk>=2\n# posthog\n")
            write(os.path.join(d, "pubspec.yaml"), "name: x\ndependencies:\n  firebase_analytics: ^11.0.0\n  flutter:\n    sdk: flutter\n")
            write(os.path.join(d, "Podfile"), "pod 'Mixpanel-swift'\n")
            names = {i["service"][0] for i in self.m.scan_code(d)}
        self.assertEqual(names, {"Anthropic", "Sentry", "Firebase Analytics", "Mixpanel"})

    def test_undisclosed_surprising_service_fails_and_processor_warns(self):
        r = self.m.check(self.scan(), POLICY)
        self.assertTrue(any(f.startswith("OpenAI") for f in r["fails"]))
        self.assertTrue(any(f.startswith("PostHog") for f in r["fails"]))
        self.assertTrue(any(w.startswith("Sentry") for w in r["warns"]))
        self.assertFalse(any("Stripe" in f for f in r["fails"] + r["warns"]))

    def test_contradicted_claim_fails_once(self):
        r = self.m.check(self.scan(), POLICY)
        contradictions = [f for f in r["fails"] if "contradicts" in f]
        self.assertEqual(len(contradictions), 1)
        self.assertIn("We do not sell or share your personal information with third parties.", contradictions[0])
        self.assertIn("Meta Pixel", contradictions[0])

    def test_no_contradiction_without_an_ad_service(self):
        r = self.m.check(self.scan(page="<p>hi</p>\n"), POLICY)
        self.assertFalse(any("contradicts" in f for f in r["fails"]))

    def test_kind_only_disclosure_passes(self):
        policy = POLICY + "We use analytics tools and an AI model provider. Errors go to an error monitoring service.\n"
        rows = {s["service"]: s["policy"] for s in self.m.check(self.scan(page=""), policy)["services"]}
        self.assertEqual(rows["PostHog"], "kind only")
        self.assertEqual(rows["OpenAI"], "kind only")

    def test_short_aliases_match_whole_words(self):
        self.assertFalse(self.m.mentions(" we store metadata ", "meta"))
        self.assertTrue(self.m.mentions(" shared with meta for ads ", "meta"))
        self.assertFalse(self.m.mentions(" as we said ", "ai"))
        self.assertTrue(self.m.mentions(" our advertising partners ", "advertis"))

    def test_missing_sections_warn(self):
        r = self.m.check(self.scan(), POLICY)
        warned = " ".join(r["warns"])
        for what in ("cookies", "transfers", "children"):
            self.assertIn(what, warned)
        self.assertNotIn("how long data is kept", warned)
        self.assertNotIn("how to contact", warned)

    def test_html_policy_is_read_as_text(self):
        with workdir() as d:
            p = write(os.path.join(d, "p.html"), "<html><style>x{}</style><p>We use <b>PostHog</b> &amp; Sentry.</p></html>")
            self.assertIn("We use PostHog & Sentry.", " ".join(self.m.read_policy(p).split()))


class PolicyScanCliTest(unittest.TestCase):
    def test_fail_and_list_only(self):
        with workdir() as d:
            code_dir = app(d)
            pol = write(os.path.join(d, "policy.md"), POLICY)
            code, out, _ = run(SKILL, SCRIPT, "--code", code_dir, "--policy", pol)
            self.assertEqual(code, 1)
            self.assertIn("| OpenAI | AI model API | package.json (openai) | not disclosed |", out)
            code, out, _ = run(SKILL, SCRIPT, "--code", code_dir)
            self.assertEqual(code, 0)
            self.assertNotIn("FAIL", out)

    def test_bad_paths_exit_2(self):
        with workdir() as d:
            self.assertEqual(run(SKILL, SCRIPT, "--code", os.path.join(d, "nope"))[0], 2)
            self.assertEqual(run(SKILL, SCRIPT, "--code", d, "--policy", os.path.join(d, "nope.md"))[0], 2)


if __name__ == "__main__":
    unittest.main()

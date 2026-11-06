#!/usr/bin/env python3
"""Compare a privacy policy with the third-party services an app's code actually uses. Stdlib only.

Scans a code folder (its dependency manifests, and the script tags, SDK calls and API hosts in
its source) for services that receive users' data: analytics, advertising pixels, session
replay, error monitoring, payments, sign-in, email and SMS, support chat, AI model APIs, maps,
push notifications. Then reads the privacy policy and reports:
  - each service found, where, and whether the policy names it or its kind
  - a policy claim the code contradicts ("we do not sell or share", "we don't use cookies",
    "no analytics") while an advertising pixel, cookie-setting tracker or analytics SDK is there
  - sections a policy for these services needs and lacks: contact, rights, retention, cookies,
    international transfers, children
It reads only the folder and file it is given and contacts no network.

Usage:
  python3 policy_scan.py --code ./app --policy ./privacy-policy.md [--json]
  python3 policy_scan.py --code ./app             (list the services only)
Exit codes: 0 no failures, 1 a failure, 2 a path can't be read.
"""
import argparse
import html
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree

# name, kind, words that disclose it in a policy, package names, hosts/strings in source,
#   flags: ads (shares data for advertising), cookies (sets cookies on the web), content (user content leaves)
SERVICES = [
    ("Google Analytics", "analytics", ["google analytics", "google"], ["react-ga", "react-ga4", "ga-4-react", "vue-gtag", "ngx-google-analytics", "@analytics/google-analytics", "nextjs-google-analytics"], ["google-analytics.com", "googletagmanager.com/gtag", "gtag("], {"cookies"}),
    ("Google Tag Manager", "analytics", ["google tag manager", "google"], ["react-gtm-module", "@next/third-parties"], ["googletagmanager.com/gtm.js"], {"cookies"}),
    ("Firebase Analytics", "analytics", ["firebase", "google analytics", "google"], ["@react-native-firebase/analytics", "firebase_analytics", "FirebaseAnalytics", "firebase-analytics"], ["getAnalytics(", "logEvent(analytics"], set()),
    ("Firebase Crashlytics", "crash reporting", ["crashlytics", "firebase", "google"], ["@react-native-firebase/crashlytics", "firebase_crashlytics", "FirebaseCrashlytics", "firebase-crashlytics"], [], set()),
    ("Meta Pixel / Facebook SDK", "advertising", ["facebook", "meta"], ["react-facebook-pixel", "facebook-nodejs-business-sdk", "react-native-fbsdk-next", "FBSDKCoreKit", "facebook-android-sdk", "facebook_app_events"], ["connect.facebook.net", "fbq("], {"ads", "cookies"}),
    ("Google Ads / AdMob", "advertising", ["google ads", "admob", "google"], ["react-native-google-mobile-ads", "google_mobile_ads", "Google-Mobile-Ads-SDK", "play-services-ads"], ["googleadservices.com", "doubleclick.net", "googlesyndication.com"], {"ads", "cookies"}),
    ("TikTok Pixel", "advertising", ["tiktok"], ["tiktok-pixel"], ["analytics.tiktok.com", "ttq.load"], {"ads", "cookies"}),
    ("LinkedIn Insight Tag", "advertising", ["linkedin"], [], ["snap.licdn.com", "_linkedin_partner_id"], {"ads", "cookies"}),
    ("X (Twitter) Pixel", "advertising", ["twitter", "x (formerly twitter)", "x corp"], [], ["static.ads-twitter.com", "twq("], {"ads", "cookies"}),
    ("Segment", "analytics", ["segment"], ["@segment/analytics-next", "analytics-node", "@segment/analytics-node", "@segment/analytics-react-native", "analytics-python", "segment-analytics-python"], ["cdn.segment.com", "api.segment.io"], {"cookies"}),
    ("Mixpanel", "analytics", ["mixpanel"], ["mixpanel", "mixpanel-browser", "mixpanel-react-native", "mixpanel_flutter", "Mixpanel-swift"], ["api.mixpanel.com", "api-js.mixpanel.com"], {"cookies"}),
    ("Amplitude", "analytics", ["amplitude"], ["@amplitude/analytics-browser", "@amplitude/analytics-react-native", "amplitude-js", "amplitude-analytics", "amplitude_flutter"], ["api.amplitude.com", "api2.amplitude.com", "cdn.amplitude.com"], {"cookies"}),
    ("PostHog", "analytics and session replay", ["posthog"], ["posthog-js", "posthog-node", "posthog", "posthog-react-native", "posthog_flutter"], ["posthog.com", "i.posthog.com"], {"cookies"}),
    ("Heap", "analytics", ["heap"], ["heap-api", "@heap/heap-react-native"], ["cdn.heapanalytics.com", "heap.load("], {"cookies"}),
    ("Plausible", "analytics", ["plausible"], ["plausible-tracker", "next-plausible"], ["plausible.io/js"], set()),
    ("Vercel Analytics", "analytics", ["vercel"], ["@vercel/analytics", "@vercel/speed-insights"], [], set()),
    ("Hotjar", "session replay", ["hotjar"], ["@hotjar/browser", "react-hotjar"], ["static.hotjar.com"], {"cookies"}),
    ("FullStory", "session replay", ["fullstory"], ["@fullstory/browser", "@fullstory/react-native"], ["fullstory.com/s/fs.js", "edge.fullstory.com"], {"cookies"}),
    ("Microsoft Clarity", "session replay", ["clarity", "microsoft"], ["@microsoft/clarity", "react-microsoft-clarity"], ["clarity.ms/tag"], {"cookies"}),
    ("LogRocket", "session replay", ["logrocket"], ["logrocket", "logrocket-react", "@logrocket/react-native"], ["cdn.logr-in.com", "LogRocket.init("], set()),
    ("Sentry", "error monitoring", ["sentry"], ["@sentry/browser", "@sentry/react", "@sentry/nextjs", "@sentry/node", "@sentry/react-native", "@sentry/vue", "sentry-sdk", "sentry-ruby", "sentry_flutter", "Sentry", "sentry-android", "sentry-go"], ["sentry.io", "Sentry.init("], set()),
    ("Bugsnag", "error monitoring", ["bugsnag"], ["@bugsnag/js", "@bugsnag/react-native", "bugsnag", "bugsnag_flutter"], ["sessions.bugsnag.com"], set()),
    ("Datadog", "monitoring", ["datadog"], ["@datadog/browser-rum", "@datadog/browser-logs", "dd-trace", "ddtrace", "@datadog/mobile-react-native"], ["browser-intake-datadoghq.com"], set()),
    ("Stripe", "payments", ["stripe"], ["stripe", "@stripe/stripe-js", "@stripe/react-stripe-js", "@stripe/stripe-react-native", "stripe-go", "flutter_stripe", "StripePaymentSheet", "stripe-android"], ["js.stripe.com", "api.stripe.com"], set()),
    ("PayPal", "payments", ["paypal"], ["@paypal/react-paypal-js", "@paypal/paypal-js", "@paypal/checkout-server-sdk", "paypalrestsdk", "paypal-rest-sdk"], ["paypal.com/sdk/js"], set()),
    ("Razorpay", "payments", ["razorpay"], ["razorpay", "react-native-razorpay", "razorpay_flutter"], ["checkout.razorpay.com"], set()),
    ("Paddle", "payments", ["paddle"], ["@paddle/paddle-js", "@paddle/paddle-node-sdk"], ["cdn.paddle.com"], set()),
    ("Auth0", "sign-in", ["auth0"], ["auth0", "@auth0/auth0-react", "@auth0/nextjs-auth0", "@auth0/auth0-spa-js", "react-native-auth0", "auth0-python"], [".auth0.com"], set()),
    ("Clerk", "sign-in", ["clerk"], ["@clerk/nextjs", "@clerk/clerk-react", "@clerk/clerk-js", "@clerk/clerk-expo", "@clerk/backend"], ["clerk.accounts.dev"], set()),
    ("Firebase Authentication", "sign-in", ["firebase", "google"], ["@react-native-firebase/auth", "firebase_auth", "FirebaseAuth", "firebase-auth"], ["signInWithPopup(", "firebaseapp.com"], set()),
    ("Supabase", "database and sign-in hosting", ["supabase"], ["@supabase/supabase-js", "@supabase/ssr", "supabase", "supabase_flutter"], [".supabase.co"], {"content"}),
    ("SendGrid", "email delivery", ["sendgrid", "twilio"], ["@sendgrid/mail", "sendgrid"], ["api.sendgrid.com"], set()),
    ("Mailchimp", "email marketing", ["mailchimp", "intuit"], ["@mailchimp/mailchimp_marketing", "@mailchimp/mailchimp_transactional", "mailchimp3", "mailchimp-marketing"], ["list-manage.com"], set()),
    ("Postmark", "email delivery", ["postmark"], ["postmark", "postmarker"], ["api.postmarkapp.com"], set()),
    ("Resend", "email delivery", ["resend"], ["resend"], ["api.resend.com"], set()),
    ("Mailgun", "email delivery", ["mailgun"], ["mailgun.js", "mailgun-js", "mailgun"], ["api.mailgun.net"], set()),
    ("Twilio", "SMS and calls", ["twilio"], ["twilio", "@twilio/voice-sdk"], ["api.twilio.com"], set()),
    ("Intercom", "support chat", ["intercom"], ["@intercom/messenger-js-sdk", "react-use-intercom", "intercom-client", "@intercom/intercom-react-native", "intercom_flutter"], ["widget.intercom.io", "Intercom("], {"cookies"}),
    ("Zendesk", "support", ["zendesk"], ["node-zendesk", "zendesk", "zenpy"], ["static.zdassets.com"], {"cookies"}),
    ("Crisp", "support chat", ["crisp"], ["crisp-sdk-web", "crisp-api"], ["client.crisp.chat"], {"cookies"}),
    ("HubSpot", "CRM and marketing", ["hubspot"], ["@hubspot/api-client", "hubspot-api-client"], ["js.hs-scripts.com", "js.hsforms.net"], {"cookies"}),
    ("OpenAI", "AI model API", ["openai", "chatgpt", "gpt"], ["openai", "@ai-sdk/openai", "@langchain/openai", "langchain-openai"], ["api.openai.com"], {"content"}),
    ("Anthropic", "AI model API", ["anthropic", "claude"], ["@anthropic-ai/sdk", "anthropic", "@ai-sdk/anthropic", "@langchain/anthropic", "langchain-anthropic"], ["api.anthropic.com"], {"content"}),
    ("Google Gemini", "AI model API", ["gemini", "google"], ["@google/generative-ai", "@google/genai", "google-generativeai", "google-genai", "@ai-sdk/google"], ["generativelanguage.googleapis.com"], {"content"}),
    ("Mistral", "AI model API", ["mistral"], ["@mistralai/mistralai", "mistralai"], ["api.mistral.ai"], {"content"}),
    ("Cohere", "AI model API", ["cohere"], ["cohere-ai", "cohere"], ["api.cohere.ai", "api.cohere.com"], {"content"}),
    ("Google Maps", "maps and location", ["google maps", "google"], ["@react-google-maps/api", "@googlemaps/js-api-loader", "@vis.gl/react-google-maps", "google_maps_flutter", "googlemaps"], ["maps.googleapis.com"], set()),
    ("Mapbox", "maps and location", ["mapbox"], ["mapbox-gl", "@rnmapbox/maps", "react-map-gl", "mapbox_maps_flutter"], ["api.mapbox.com"], set()),
    ("OneSignal", "push notifications", ["onesignal"], ["onesignal", "react-onesignal", "react-native-onesignal", "onesignal_flutter", "@onesignal/node-onesignal"], ["cdn.onesignal.com"], set()),
    ("LaunchDarkly", "feature flags", ["launchdarkly"], ["launchdarkly-js-client-sdk", "@launchdarkly/node-server-sdk", "launchdarkly-react-client-sdk", "launchdarkly-server-sdk"], ["app.launchdarkly.com"], set()),
    ("Algolia", "search", ["algolia"], ["algoliasearch", "react-instantsearch"], [".algolia.net"], set()),
    ("Cloudinary", "media hosting", ["cloudinary"], ["cloudinary", "next-cloudinary", "@cloudinary/react"], ["res.cloudinary.com", "api.cloudinary.com"], {"content"}),
    ("Google reCAPTCHA", "bot protection", ["recaptcha", "google"], ["react-google-recaptcha", "react-google-recaptcha-v3", "django-recaptcha"], ["google.com/recaptcha", "recaptcha.net"], {"cookies"}),
    ("Calendly", "scheduling", ["calendly"], ["react-calendly"], ["assets.calendly.com", "calendly.com/"], {"cookies"}),
]

KIND_WORDS = {
    "analytics": ["analytics", "usage data", "how you use"],
    "analytics and session replay": ["analytics", "session recording", "session replay"],
    "session replay": ["session recording", "session replay", "record your session", "heatmap"],
    "crash reporting": ["crash report", "crash data", "diagnostic"],
    "error monitoring": ["error report", "error monitoring", "crash report", "diagnostic"],
    "monitoring": ["monitoring", "performance data", "diagnostic"],
    "advertising": ["advertis", "marketing partner", "retarget", "ad partner"],
    "payments": ["payment processor", "payment provider", "process payments", "payment information"],
    "sign-in": ["authentication", "sign-in provider", "login provider", "identity provider"],
    "database and sign-in hosting": ["hosting provider", "database", "cloud provider", "infrastructure provider"],
    "email delivery": ["email provider", "email service", "send you email", "transactional email"],
    "email marketing": ["newsletter", "marketing email", "email marketing"],
    "SMS and calls": ["sms", "text message", "phone number"],
    "support chat": ["support chat", "live chat", "customer support", "help desk"],
    "support": ["customer support", "help desk", "support ticket"],
    "CRM and marketing": ["crm", "marketing"],
    "AI model API": ["artificial intelligence", "ai model", "language model", "ai provider", "ai", "machine learning"],
    "maps and location": ["location", "maps"],
    "push notifications": ["push notification"],
    "feature flags": ["feature flag", "service provider"],
    "search": ["search provider", "search queries"],
    "media hosting": ["image hosting", "media hosting", "uploads", "cloud storage"],
    "bot protection": ["captcha", "spam", "bot"],
    "scheduling": ["scheduling", "book a call", "calendar"],
}

CLAIMS = [
    ("ads", re.compile(r"\b(?:we\s+(?:do\s+not|don['’]t|never|will\s+not|won['’]t)\s+(?:sell|share|rent|trade|disclose)"
                       r"[^.]{0,80}?(?:personal|your|any)?\s*(?:data|information)?[^.]{0,40}?(?:third[\s-]part|anyone|advertis|others))", re.I),
     "it says data isn't sold or shared with third parties"),
    ("ads", re.compile(r"\bwe\s+(?:do\s+not|don['’]t|never)\s+sell\b", re.I), "it says data is never sold"),
    ("cookies", re.compile(r"\bwe\s+(?:do\s+not|don['’]t|never)\s+use\s+(?:any\s+)?(?:cookies|trackers|tracking)", re.I),
     "it says no cookies or tracking are used"),
    ("analytics", re.compile(r"\b(?:we\s+(?:do\s+not|don['’]t|never)\s+(?:use|collect)\s+(?:any\s+)?(?:analytics|usage data|tracking))|\bno\s+(?:analytics|tracking)\b", re.I),
     "it says there is no analytics or tracking"),
    ("content", re.compile(r"\b(?:your\s+(?:data|content|messages|files)\s+(?:never|does\s+not|doesn['’]t|will\s+not)\s+leave"
                           r"|(?:stays|stored)\s+only\s+on\s+your\s+device)", re.I),
     "it says user content never leaves the device or service"),
]

SECTIONS = [
    ("contact", re.compile(r"contact\s+us|@[a-z0-9-]+\.[a-z]{2,}|data protection officer|privacy@", re.I), "how to contact you about privacy"),
    ("rights", re.compile(r"\b(?:access|delete|deletion|erase|correct|rectif|portability|opt[\s-]?out)\b", re.I), "the user's rights (access, deletion, correction, opt-out)"),
    ("retention", re.compile(r"\bretain|\bretention|\bkeep\s+(?:your|personal)|\bstore\s+.{0,30}for\b|\bdelete[^.]{0,40}(?:after|within)\b", re.I), "how long data is kept"),
    ("cookies", re.compile(r"\bcookie", re.I), "cookies"),
    ("transfers", re.compile(r"international|transfer|outside\s+(?:the\s+)?(?:eea|eu|uk|european|your country)|united states|standard contractual", re.I), "transfers to other countries"),
    ("children", re.compile(r"\bchild|\bminor|under\s+(?:the\s+age\s+of\s+)?1[3-8]|\bage\s+of\s+1[3-8]", re.I), "children"),
]

SURPRISING = {"advertising", "analytics", "analytics and session replay", "session replay", "AI model API"}

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "vendor", ".venv", "venv", "__pycache__", "Pods",
             ".gradle", "coverage", ".dart_tool", "target", ".expo", "out", ".turbo", ".svelte-kit"}
SOURCE_EXT = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".py",
              ".rb", ".php", ".swift", ".kt", ".java", ".dart", ".go", ".erb", ".liquid", ".hbs", ".ejs"}
MANIFESTS = {"package.json", "requirements.txt", "requirements-prod.txt", "pyproject.toml", "Pipfile", "Gemfile",
             "go.mod", "pubspec.yaml", "Podfile", "build.gradle", "build.gradle.kts", "composer.json", "Cargo.toml"}


def manifest_packages(path, name):
    """Package names a manifest ships with (runtime dependencies, not dev tools where the format says so)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if name in ("package.json", "composer.json"):
        try:
            data = json.loads(text)
        except ValueError:
            return []
        keys = ("dependencies", "peerDependencies", "optionalDependencies") if name == "package.json" else ("require",)
        out = []
        for k in keys:
            if isinstance(data.get(k), dict):
                out += list(data[k])
        return out
    if name.startswith("requirements"):
        return [re.split(r"[\s=<>!~\[;]", l.strip(), maxsplit=1)[0] for l in text.splitlines()
                if l.strip() and not l.strip().startswith(("#", "-"))]
    if name == "go.mod":
        return re.findall(r"^\s*(?:require\s+)?([\w.\-/]+)\s+v\d", text, re.M)
    if name == "pubspec.yaml":
        m = re.search(r"^dependencies:\s*\n((?:[ \t]+.*\n?)*)", text, re.M)
        return re.findall(r"^[ \t]{2}([\w]+):", m.group(1), re.M) if m else []
    if name == "Podfile":
        return re.findall(r"pod\s+['\"]([^'\"/]+)", text)
    if name.startswith("build.gradle"):
        return [g.split(":")[1] for g in re.findall(r"(?:implementation|api)\s*\(?\s*['\"]([^'\"]+)['\"]", text) if ":" in g]
    if name == "Gemfile":
        return re.findall(r"^\s*gem\s+['\"]([^'\"]+)", text, re.M)
    if name == "Cargo.toml":
        m = re.search(r"^\[dependencies\]\s*\n((?:(?!\[).*\n?)*)", text, re.M)
        return re.findall(r"^([\w\-]+)\s*=", m.group(1), re.M) if m else []
    # pyproject.toml, Pipfile: quoted or bare names in dependency blocks
    return re.findall(r"^\s*['\"]?([A-Za-z0-9_.\-]+)['\"]?\s*(?:[=<>~!]|$)", text, re.M) + \
        re.findall(r"['\"]([A-Za-z0-9_.\-]+)\s*(?:[=<>~!\[][^'\"]*)?['\"]", text)


def scan_code(root):
    found = {}

    def add(svc, where):
        found.setdefault(svc[0], {"service": svc, "where": []})
        if where not in found[svc[0]]["where"]:
            found[svc[0]]["where"].append(where)

    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, root)
            if f in MANIFESTS or f.startswith("requirements") and f.endswith(".txt"):
                try:
                    pkgs = {p.lower() for p in manifest_packages(path, f)}
                except OSError:
                    continue
                for svc in SERVICES:
                    for p in svc[3]:
                        if p.lower() in pkgs:
                            add(svc, f"{rel} ({p})")
                continue
            if os.path.splitext(f)[1].lower() not in SOURCE_EXT:
                continue
            try:
                if os.path.getsize(path) > 2_000_000:
                    continue
                with open(path, encoding="utf-8", errors="replace") as fh:
                    lines = fh.read().splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines, 1):
                for svc in SERVICES:
                    for h in svc[4]:
                        if h in line:
                            add(svc, f"{rel}:{n}")
                            break
    return [found[k] for k in sorted(found)]


def read_policy(path):
    if path.lower().endswith(".docx"):
        w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        return "\n".join("".join(t.text or "" for t in p.iter(w + "t")) for p in root.iter(w + "p"))
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    if path.lower().endswith((".html", ".htm")):
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return text


def sentence(text, at):
    """The sentence around position `at`, trimmed to 160 characters."""
    start = max(text.rfind(c, 0, at) for c in ".!?\n") + 1
    ends = [e for e in (text.find(c, at) for c in ".!?\n") if e != -1]
    end = min(ends) + 1 if ends else len(text)
    out = " ".join(text[start:end].split())
    return out if len(out) <= 160 else out[:157] + "…"


def mentions(text, word):
    """Match at a word start, so "ai" doesn't match "said". Short words must also end there, so
    "meta" doesn't match "metadata"; longer ones are stems ("advertis" matches "advertising")."""
    w = word.strip()
    tail = r"(?![a-z0-9])" if len(w) <= 6 else ""
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(w) + tail, text))


def check(services, policy):
    fails, warns, rows = [], [], []
    low = " " + re.sub(r"\s+", " ", policy.lower()) + " "
    for item in services:
        name, kind, words, _, _, flags = item["service"]
        named = any(mentions(low, w) for w in words)
        by_kind = any(mentions(low, w) for w in KIND_WORDS.get(kind, []))
        status = "named" if named else "kind only" if by_kind else "not disclosed"
        rows.append({"service": name, "kind": kind, "where": item["where"], "policy": status})
        if status == "not disclosed":
            msg = f"{name} ({kind}) is in the code ({item['where'][0]}) but the policy names neither it nor its kind"
            # what a user wouldn't expect fails; a processor that only runs the service warns
            (fails if kind in SURPRISING or "content" in flags else warns).append(msg)
    present_flags = set()
    for item in services:
        present_flags |= item["service"][5]
        if item["service"][1] in ("analytics", "analytics and session replay", "session replay"):
            present_flags.add("analytics")
    reported = set()
    for flag, rx, what in CLAIMS:
        m = rx.search(policy)
        if m and flag in present_flags and not any(a <= m.start() < b for a, b in reported):
            reported.add((m.start(), m.end()))
            culprits = [i["service"][0] for i in services if flag in i["service"][5] or
                        (flag == "analytics" and i["service"][1] in ("analytics", "analytics and session replay", "session replay"))]
            fails.append(f"the policy contradicts the code: {what} (“{sentence(policy, m.start())}”), "
                         f"but the code uses {', '.join(culprits)}")
    needed = ["contact", "rights", "retention", "children"]
    if "cookies" in present_flags:
        needed.append("cookies")
    if services:
        needed.append("transfers")
    for key, rx, what in SECTIONS:
        if key in needed and not rx.search(policy):
            warns.append(f"the policy doesn't cover {what}")
    return {"services": rows, "fails": fails, "warns": warns}


def report(r, policy_given):
    L = ["# Privacy policy against the code", ""]
    if not r["services"]:
        L.append("No third-party services that receive user data were found in the code.")
    else:
        L += ["| Service | Kind | Found in | Policy |", "|---|---|---|---|"]
        for s in r["services"]:
            where = ", ".join(s["where"][:3]) + (f" (+{len(s['where']) - 3} more)" if len(s["where"]) > 3 else "")
            L.append(f"| {s['service']} | {s['kind']} | {where} | {s['policy'] if policy_given else ''} |")
    if policy_given:
        L.append("")
        if not r["fails"]:
            L.append("PASS every service users wouldn't expect is disclosed, and no policy claim contradicts the code.")
        L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compare a privacy policy with the services the code uses.")
    ap.add_argument("--code", required=True, help="the app's code folder")
    ap.add_argument("--policy", help="the privacy policy (.md, .txt, .html or .docx)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.code):
        print(f"FAIL {args.code} is not a folder")
        return 2
    services = scan_code(args.code)
    policy = ""
    if args.policy:
        try:
            policy = read_policy(args.policy)
        except (OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as e:
            print(f"FAIL cannot read {args.policy}: {e}")
            return 2
    r = check(services, policy) if args.policy else {"services": [
        {"service": i["service"][0], "kind": i["service"][1], "where": i["where"], "policy": ""} for i in services],
        "fails": [], "warns": []}
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(report(r, bool(args.policy)), end="")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Summarise a Lighthouse report (and field data, when given) for a performance review. Stdlib only.

Input is either the Lighthouse result JSON (`lighthouse <url> --output=json`), or a PageSpeed
Insights API v5 response, which embeds that result as `lighthouseResult` and carries field data
(CrUX p75) in `loadingExperience` / `originLoadingExperience`. A CrUX API `records:queryRecord`
response is also read, as field data only.

It prints, in order: how the run was made (device, throttling, Lighthouse version, warnings);
lab metrics against the thresholds; field p75 metrics with good / needs-improvement / poor and
the Core Web Vitals outcome; the LCP element and its phase breakdown; layout-shift culprits;
failing opportunities and diagnostics with the metric each one moves; long tasks and third
parties by main-thread time; render-blocking resources. Given two reports, it also says whether
they are comparable and prints the lab deltas.

Usage:
  lighthouse https://example.test --output=json --output-path=report.json
  python3 lh_summary.py report.json [--json] [-o summary.md]
  python3 lh_summary.py psi.json
  python3 lh_summary.py report.json --field crux.json
  python3 lh_summary.py report.json --lcp-p75 3100 --inp-p75 420 --cls-p75 0.04   # RUM numbers
  python3 lh_summary.py before.json after.json          # comparability check + deltas
  cat report.json | python3 lh_summary.py -

Exit codes: 0 summary written; 2 bad input (unreadable, not JSON, not a Lighthouse/PSI/CrUX file).
Estimated savings are Lighthouse's lab estimates for one simulated load. They are not field
changes, and savings from audits that touch the same resources overlap and must not be added.
"""
import argparse
import json
import re
import sys
from urllib.parse import urlsplit

# Core Web Vitals and supporting field thresholds at p75: (good <=, poor >).
FIELD_THRESHOLDS = {
    "LCP": (2500, 4000),
    "INP": (200, 500),
    "CLS": (0.1, 0.25),
    "FCP": (1800, 3000),
    "TTFB": (800, 1800),
}
CWV = ("LCP", "INP", "CLS")

# Lab metrics: audit id, label, (good <=, poor >) or None, unit.
LAB_METRICS = (
    ("first-contentful-paint", "FCP", (1800, 3000), "ms"),
    ("largest-contentful-paint", "LCP", (2500, 4000), "ms"),
    ("total-blocking-time", "TBT", (200, 600), "ms"),
    ("cumulative-layout-shift", "CLS", (0.1, 0.25), ""),
    ("speed-index", "Speed Index", None, "ms"),
    ("interactive", "TTI", None, "ms"),
    ("server-response-time", "Server response (lab TTFB)", None, "ms"),
    ("interaction-to-next-paint", "INP (timespan run)", (200, 500), "ms"),
)
METRIC_IDS = {m[0] for m in LAB_METRICS if m[0] != "server-response-time"} | {
    "max-potential-fid", "first-meaningful-paint", "metrics"}
# Audits that describe elements rather than propose a fix; reported in their own sections.
DESCRIPTIVE = {"largest-contentful-paint-element", "layout-shift-elements",
               "long-tasks", "third-party-summary", "main-thread-tasks", "network-requests",
               "screenshot-thumbnails", "final-screenshot", "diagnostics", "resource-summary",
               "network-rtt", "network-server-latency", "script-treemap-data"}

# Audits Lighthouse reports with a zero or missing metric saving even though the fix acts on a
# vital directly; never label these "load-time only".
DIRECT_EFFECT = {
    "lcp-lazy-loaded": "LCP", "prioritize-lcp-image": "LCP", "lcp-discovery-insight": "LCP",
    "server-response-time": "LCP, FCP", "document-latency-insight": "LCP, FCP", "redirects": "LCP, FCP",
    "uses-rel-preconnect": "LCP, FCP", "unsized-images": "CLS", "font-display": "CLS, FCP",
    "font-display-insight": "CLS, FCP", "non-composited-animations": "CLS", "cls-culprits-insight": "CLS",
    "layout-shifts": "CLS",
}

PSI_FIELD_KEYS = {
    "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
    "INTERACTION_TO_NEXT_PAINT": "INP",
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
    "FIRST_CONTENTFUL_PAINT_MS": "FCP",
    "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB",
}
CRUX_FIELD_KEYS = {
    "largest_contentful_paint": "LCP",
    "interaction_to_next_paint": "INP",
    "cumulative_layout_shift": "CLS",
    "first_contentful_paint": "FCP",
    "experimental_time_to_first_byte": "TTFB",
}
PHASE_NAMES = {
    "ttfb": "TTFB", "timetofirstbyte": "TTFB",
    "loaddelay": "Resource load delay", "resourceloaddelay": "Resource load delay",
    "loadtime": "Resource load duration", "resourceloadtime": "Resource load duration",
    "resourceloadduration": "Resource load duration",
    "renderdelay": "Element render delay", "elementrenderdelay": "Element render delay",
}
PHASE_FIX = {
    "TTFB": "slow server or redirects: cache the HTML at the edge, cut redirects, fix backend time",
    "Resource load delay": "LCP resource requested late: check loading=lazy, discovery in the HTML (not JS or CSS), fetchpriority=high or preload",
    "Resource load duration": "LCP resource too heavy: smaller/responsive image, modern format, CDN",
    "Element render delay": "resource arrived but paint waited: render-blocking CSS/JS, client-side rendering, long tasks",
}


def die(msg):
    print(f"lh_summary: {msg}", file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    except OSError as exc:
        die(f"cannot read {path}: {exc.strerror}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"{path} is not JSON ({exc.msg} at line {exc.lineno})")


def classify(doc, path):
    """Return (lhr or None, list of field dicts)."""
    if not isinstance(doc, dict):
        die(f"{path}: expected a JSON object")
    if "steps" in doc and "lhr" not in doc:
        die(f"{path}: this is a Lighthouse user-flow report; export one step's lhr and pass that")
    fields = []
    if "lighthouseResult" in doc or "loadingExperience" in doc:
        for key, scope in (("loadingExperience", "url"), ("originLoadingExperience", "origin")):
            f = psi_field(doc.get(key), scope)
            if f:
                fields.append(f)
        lhr = doc.get("lighthouseResult")
        if lhr is not None and not isinstance(lhr, dict):
            die(f"{path}: lighthouseResult is not an object")
        return lhr, fields
    if "record" in doc and isinstance(doc["record"], dict):
        f = crux_field(doc["record"])
        if not f:
            die(f"{path}: CrUX record has no metrics")
        return None, [f]
    if "lhr" in doc and isinstance(doc["lhr"], dict):
        doc = doc["lhr"]
    if "audits" in doc and "lighthouseVersion" in doc:
        if doc.get("runtimeError"):
            err = doc["runtimeError"]
            die(f"{path}: Lighthouse run failed ({err.get('code')}: {err.get('message')})")
        return doc, fields
    die(f"{path}: not a Lighthouse result, PageSpeed Insights response or CrUX record")


def rate(value, thresholds):
    if value is None or thresholds is None:
        return None
    good, poor = thresholds
    if value <= good:
        return "good"
    if value > poor:
        return "poor"
    return "needs-improvement"


def psi_field(le, scope):
    if not isinstance(le, dict) or not le.get("metrics"):
        return None
    out = {"source": "CrUX via PageSpeed Insights", "scope": scope, "id": le.get("id"),
           "origin_fallback": bool(le.get("origin_fallback")), "metrics": {}}
    for key, name in PSI_FIELD_KEYS.items():
        m = le["metrics"].get(key)
        if not m or m.get("percentile") is None:
            continue
        p75 = m["percentile"]
        if name == "CLS":
            p75 = p75 / 100.0  # PSI reports CLS p75 multiplied by 100
        good_share = None
        for d in m.get("distributions") or []:
            if d.get("min") == 0:
                good_share = d.get("proportion")
        out["metrics"][name] = {"p75": p75, "rating": rate(p75, FIELD_THRESHOLDS[name]),
                                "good_share": good_share}
    return out if out["metrics"] else None


def crux_field(rec):
    key = rec.get("key") or {}
    period = rec.get("collectionPeriod") or {}

    def d(x):
        return "{:04d}-{:02d}-{:02d}".format(x.get("year", 0), x.get("month", 0), x.get("day", 0)) if x else None
    out = {"source": "CrUX API", "scope": "url" if "url" in key else "origin",
           "id": key.get("url") or key.get("origin"), "form_factor": key.get("formFactor", "ALL"),
           "period": [d(period.get("firstDate")), d(period.get("lastDate"))], "metrics": {}}
    for k, name in CRUX_FIELD_KEYS.items():
        m = (rec.get("metrics") or {}).get(k)
        if not m:
            continue
        p75 = (m.get("percentiles") or {}).get("p75")
        if p75 is None:
            continue
        p75 = float(p75)
        good_share = None
        hist = m.get("histogram") or []
        if hist and "density" in hist[0]:
            good_share = hist[0]["density"]
        out["metrics"][name] = {"p75": p75, "rating": rate(p75, FIELD_THRESHOLDS[name]),
                                "good_share": good_share}
    return out if out["metrics"] else None


def manual_field(args):
    m = {}
    for name, val in (("LCP", args.lcp_p75), ("INP", args.inp_p75), ("CLS", args.cls_p75)):
        if val is not None:
            m[name] = {"p75": val, "rating": rate(val, FIELD_THRESHOLDS[name]), "good_share": None}
    if not m:
        return None
    return {"source": args.field_source, "scope": "as given", "id": None, "metrics": m}


def cwv_outcome(field):
    m = field["metrics"]
    if "LCP" not in m or "CLS" not in m:
        have = ", ".join(f"{k} {m[k]['rating']}" for k in CWV if k in m) or "no vitals"
        return f"cannot be assessed: no {' or '.join(k for k in ('LCP', 'CLS') if k not in m)} at p75 ({have})"
    failing = [k for k in CWV if k in m and m[k]["rating"] != "good"]
    missing = [k for k in CWV if k not in m]
    if failing:
        return "FAILED: " + ", ".join(f"{k} {m[k]['rating']}" for k in failing)
    return "PASSED" + (f" (no {', '.join(missing)} data)" if missing else "")


# ---------------------------------------------------------------- Lighthouse result readers

def audit(lhr, aid):
    a = (lhr.get("audits") or {}).get(aid)
    if not isinstance(a, dict) or a.get("scoreDisplayMode") in ("notApplicable", "error"):
        return None
    return a


def items_of(a):
    if not a:
        return []
    det = a.get("details") or {}
    return [i for i in det.get("items") or [] if isinstance(i, dict)]


def node_desc(node):
    if not isinstance(node, dict):
        return None
    return {k: node.get(k) for k in ("selector", "nodeLabel", "snippet") if node.get(k)}


def origin(url):
    try:
        p = urlsplit(url or "")
        return f"{p.scheme}://{p.netloc}" if p.netloc else (url or "")
    except ValueError:
        return url or ""


def entity_map(lhr):
    out = {}
    for e in lhr.get("entities") or []:
        for o in e.get("origins") or []:
            out[o] = {"name": e.get("name"), "first_party": bool(e.get("isFirstParty"))}
    return out


def run_info(lhr):
    cs = lhr.get("configSettings") or {}
    th = cs.get("throttling") or {}
    method = cs.get("throttlingMethod")
    se = cs.get("screenEmulation") or {}
    info = {
        "url": lhr.get("finalDisplayedUrl") or lhr.get("finalUrl") or lhr.get("mainDocumentUrl") or lhr.get("requestedUrl"),
        "fetch_time": lhr.get("fetchTime"),
        "lighthouse_version": lhr.get("lighthouseVersion"),
        "form_factor": cs.get("formFactor") or ("mobile" if se.get("mobile") else "desktop" if se else None),
        "screen": f"{se.get('width')}x{se.get('height')} @{se.get('deviceScaleFactor')}x" if se.get("width") else None,
        "throttling_method": method,
        "rtt_ms": th.get("requestLatencyMs") if method == "devtools" else th.get("rttMs"),
        "throughput_kbps": th.get("downloadThroughputKbps") if method == "devtools" else th.get("throughputKbps"),
        "cpu_slowdown": th.get("cpuSlowdownMultiplier"),
        "benchmark_index": (lhr.get("environment") or {}).get("benchmarkIndex"),
        "run_warnings": lhr.get("runWarnings") or [],
    }
    if method == "provided":
        info["preset"] = "no throttling applied by Lighthouse (provided)"
    elif info["rtt_ms"] == 150 and info["cpu_slowdown"] == 4:
        info["preset"] = "Lighthouse default mobile: slow 4G (150 ms RTT, ~1.6 Mbps), 4x CPU slowdown"
    elif info["rtt_ms"] == 40 and info["cpu_slowdown"] == 1:
        info["preset"] = "Lighthouse desktop preset: 40 ms RTT, ~10 Mbps, no CPU slowdown"
    else:
        info["preset"] = "custom throttling"
    if method == "simulate":
        info["method_note"] = "simulated: metrics are modelled from an unthrottled load"
    return info


def lab_metrics(lhr):
    out = []
    for aid, label, thr, unit in LAB_METRICS:
        a = audit(lhr, aid)
        if not a or a.get("numericValue") is None:
            continue
        v = a["numericValue"]
        out.append({"id": aid, "metric": label, "value": round(v, 3 if unit == "" else 0),
                    "display": a.get("displayValue"), "rating": rate(v, thr),
                    "threshold": f"good <= {thr[0]}{unit}, poor > {thr[1]}{unit}" if thr else None})
    perf = (lhr.get("categories") or {}).get("performance") or {}
    score = perf.get("score")
    return {"performance_score": None if score is None else round(score * 100), "metrics": out}


def norm_phase(name):
    return PHASE_NAMES.get(re.sub(r"[^a-z]", "", str(name).lower()), str(name))


def lcp_info(lhr):
    out = {"element": None, "phases": [], "lazy_loaded": None, "fetchpriority_high": None,
           "discovery_checks": [], "lcp_resource_url": None, "prioritize_savings_ms": None}
    sources = [audit(lhr, "largest-contentful-paint-element"), audit(lhr, "lcp-breakdown-insight"),
               audit(lhr, "lcp-phases-insight"), audit(lhr, "lcp-discovery-insight")]
    for a in sources:
        if not a:
            continue
        det = a.get("details") or {}
        blocks = det.get("items") if det.get("type") == "list" else [det]
        for blk in blocks or []:
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "node" and not out["element"]:
                out["element"] = node_desc(blk)
            if blk.get("type") == "checklist":
                for k, c in (blk.get("items") or {}).items():
                    out["discovery_checks"].append({"check": c.get("label", k), "passed": bool(c.get("value"))})
            rows = blk.get("items") if isinstance(blk.get("items"), list) else []
            phases = []
            for it in rows:
                if not isinstance(it, dict):
                    continue
                if it.get("node") and not out["element"]:
                    out["element"] = node_desc(it["node"])
                name = it.get("phase") or it.get("subpart") or it.get("label")
                t = it.get("timing", it.get("duration"))
                if name is not None and isinstance(t, (int, float)):
                    phases.append({"phase": norm_phase(name), "ms": round(t)})
            if phases and not out["phases"]:
                out["phases"] = phases
    total = sum(p["ms"] for p in out["phases"])
    for p in out["phases"]:
        p["share"] = f"{round(100 * p['ms'] / total)}%" if total else None
    if out["phases"]:
        dom = max(out["phases"], key=lambda p: p["ms"])
        out["dominant_phase"] = dom["phase"]
        out["dominant_phase_points_to"] = PHASE_FIX.get(dom["phase"])
    lazy = audit(lhr, "lcp-lazy-loaded")
    if lazy and lazy.get("score") is not None:
        out["lazy_loaded"] = lazy["score"] == 0
    snippet = (out["element"] or {}).get("snippet", "")
    if snippet:
        if re.search(r'loading\s*=\s*["\']?lazy', snippet, re.I):
            out["lazy_loaded"] = True
        out["fetchpriority_high"] = bool(re.search(r'fetchpriority\s*=\s*["\']?high', snippet, re.I))
        m = re.match(r"<\s*([a-zA-Z0-9-]+)", snippet)
        out["element_tag"] = m.group(1).lower() if m else None
    pri = audit(lhr, "prioritize-lcp-image")
    if pri:
        for it in items_of(pri):
            out["lcp_resource_url"] = out["lcp_resource_url"] or it.get("url")
        ms = (pri.get("metricSavings") or {}).get("LCP")
        out["prioritize_savings_ms"] = ms if ms is not None else (pri.get("details") or {}).get("overallSavingsMs")
    return out


def cls_info(lhr):
    shifts = []
    a = audit(lhr, "layout-shifts") or audit(lhr, "layout-shift-elements")
    for it in items_of(a):
        causes = []
        for sub in ((it.get("subItems") or {}).get("items") or []):
            c = sub.get("cause")
            extra = sub.get("extra") or {}
            val = extra.get("value") or extra.get("url") if isinstance(extra, dict) else None
            if c:
                causes.append(f"{c}{' (' + str(val) + ')' if val else ''}")
        shifts.append({"element": node_desc(it.get("node")), "score": it.get("score"), "causes": causes})
    shifts.sort(key=lambda s: -(s["score"] or 0))
    def failing(aid):
        a = audit(lhr, aid)
        return items_of(a) if a and a.get("score") != 1 else []
    unsized = [{"url": it.get("url"), "element": node_desc(it.get("node"))} for it in failing("unsized-images")]
    fonts = [{"url": it.get("url"), "wasted_ms": it.get("wastedMs")} for it in failing("font-display")]
    return {"shifts": shifts, "unsized_images": unsized, "fonts_without_display": fonts}


def item_urls(a):
    urls = set()
    for it in items_of(a):
        u = it.get("url") or (it.get("node") or {}).get("snippet")
        if isinstance(u, str):
            urls.add(u)
    return urls


def opportunities(lhr, top, field_failing=()):
    """field_failing: vitals (LCP, INP, CLS) that real users fail at p75; audits moving them rank first."""
    rows = []
    for aid, a in (lhr.get("audits") or {}).items():
        if aid in METRIC_IDS or aid in DESCRIPTIVE or not isinstance(a, dict):
            continue
        mode = a.get("scoreDisplayMode")
        if mode in ("notApplicable", "error", "manual"):
            continue
        det = a.get("details") or {}
        ms = a.get("metricSavings") or {}
        score = a.get("score")
        failing = isinstance(score, (int, float)) and score < 0.9
        informative_hit = mode == "informative" and any(v for v in ms.values() if isinstance(v, (int, float)))
        if not (failing or informative_hit):
            continue
        affects = {k: v for k, v in ms.items() if isinstance(v, (int, float)) and v > 0}
        cwv_affects = {k: v for k, v in affects.items() if k in ("LCP", "TBT", "INP", "CLS")}
        row = {"id": aid, "title": a.get("title"), "display": a.get("displayValue"),
               "kind": "opportunity" if det.get("type") == "opportunity" else "diagnostic",
               "overall_savings_ms": det.get("overallSavingsMs"),
               "overall_savings_bytes": det.get("overallSavingsBytes"),
               "metric_savings": affects}
        direct = DIRECT_EFFECT.get(aid)
        if direct and not cwv_affects:
            row["note"] = f"acts on {direct} directly; Lighthouse gives no saving estimate for it"
        elif not ms:
            row["note"] = "no per-metric savings in this report (Lighthouse < 11, or not estimated)"
        elif not cwv_affects:
            row["note"] = "LOAD-TIME ONLY in this run: no LCP, TBT or CLS saving estimated"
        moves = set(cwv_affects) | {m.strip() for m in (direct or "").split(",") if m.strip()}
        moves = {"INP" if m == "TBT" else m for m in moves}
        hits = sorted(moves & set(field_failing))
        if hits:
            row["moves_failing_field_vital"] = hits
        row["_rank"] = (1 if hits else 0, 1 if (cwv_affects or direct) else 0, max(cwv_affects.get("LCP", 0), cwv_affects.get("TBT", 0),
                        cwv_affects.get("INP", 0)), cwv_affects.get("CLS", 0), row["overall_savings_ms"] or 0)
        row["_urls"] = item_urls(a)
        rows.append(row)
    rows.sort(key=lambda r: r["_rank"], reverse=True)
    for r in rows:
        overlaps = []
        if not (r["overall_savings_ms"] or r["metric_savings"]):
            continue
        for o in rows:
            if o is r or not (o["overall_savings_ms"] or o["metric_savings"]):
                continue
            shared = r["_urls"] & o["_urls"]
            if shared:
                overlaps.append(f"{o['id']} ({len(shared)} shared)")
        if overlaps:
            r["overlaps_with"] = overlaps
    for r in rows:
        r.pop("_rank")
        r.pop("_urls")
    return rows[:top]


def main_thread(lhr, top):
    emap = entity_map(lhr)

    def who(url):
        o = origin(url)
        e = emap.get(o)
        if e:
            return f"{e['name']}{' (1st party)' if e['first_party'] else ''}"
        return o
    tasks = sorted(items_of(audit(lhr, "long-tasks")), key=lambda t: -(t.get("duration") or 0))
    long_tasks = [{"url": t.get("url"), "by": who(t.get("url")), "duration_ms": round(t.get("duration") or 0),
                   "start_ms": round(t.get("startTime") or 0)} for t in tasks[:top]]
    by_origin = {}
    for t in tasks:
        k = who(t.get("url"))
        by_origin.setdefault(k, [0, 0])
        by_origin[k][0] += 1
        by_origin[k][1] += t.get("duration") or 0
    tp = []
    tpa = audit(lhr, "third-party-summary") or audit(lhr, "third-parties-insight")
    for it in items_of(tpa):
        ent = it.get("entity")
        if isinstance(ent, dict):
            ent = ent.get("text") or ent.get("url")
        tp.append({"entity": ent, "main_thread_ms": round(it.get("mainThreadTime") or 0),
                   "blocking_ms": round(it.get("blockingTime") or 0) if it.get("blockingTime") is not None else None,
                   "transfer_kb": round((it.get("transferSize") or 0) / 1024)})
    tp.sort(key=lambda r: -r["main_thread_ms"])
    boot = sorted(items_of(audit(lhr, "bootup-time")), key=lambda b: -(b.get("total") or 0))
    scripts = [{"url": b.get("url"), "by": who(b.get("url")), "total_ms": round(b.get("total") or 0),
                "scripting_ms": round(b.get("scripting") or 0)} for b in boot[:top] if isinstance(b.get("url"), str)]
    mtw = audit(lhr, "mainthread-work-breakdown")
    return {"long_tasks": long_tasks,
            "long_tasks_by_origin": [{"by": k, "count": v[0], "total_ms": round(v[1])}
                                     for k, v in sorted(by_origin.items(), key=lambda kv: -kv[1][1])],
            "third_parties": tp, "script_bootup": scripts,
            "main_thread_total_ms": round(mtw["numericValue"]) if mtw and mtw.get("numericValue") is not None else None}


def render_blocking(lhr):
    a = audit(lhr, "render-blocking-resources") or audit(lhr, "render-blocking-insight")
    if not a or a.get("score") == 1:
        return []
    return [{"url": it.get("url"), "kb": round((it.get("totalBytes") or 0) / 1024),
             "wasted_ms": round(it.get("wastedMs") or 0)} for it in items_of(a)]


def summarise(lhr, fields, top):
    r = {"fields": [], "lab": None}
    for f in fields:
        f = dict(f)
        f["core_web_vitals"] = cwv_outcome(f)
        r["fields"].append(f)
    failing = set()
    if r["fields"]:
        f0 = next((f for f in r["fields"] if f["scope"] != "origin"), r["fields"][0])
        failing = {k for k in CWV if k in f0["metrics"] and f0["metrics"][k]["rating"] != "good"}
    if lhr:
        r.update({"run": run_info(lhr), "lab": lab_metrics(lhr), "lcp": lcp_info(lhr), "cls": cls_info(lhr),
                  "opportunities": opportunities(lhr, top, failing), "main_thread": main_thread(lhr, top),
                  "render_blocking": render_blocking(lhr)})
    return r


def compare(a, b):
    ra, rb = a.get("run") or {}, b.get("run") or {}
    diffs = []
    for k in ("url", "lighthouse_version", "form_factor", "throttling_method", "rtt_ms", "throughput_kbps",
              "cpu_slowdown", "screen"):
        if ra.get(k) != rb.get(k):
            diffs.append(f"{k}: {ra.get(k)} -> {rb.get(k)}")
    ma = {m["metric"]: m["value"] for m in (a.get("lab") or {}).get("metrics", [])}
    mb = {m["metric"]: m["value"] for m in (b.get("lab") or {}).get("metrics", [])}
    deltas = [{"metric": k, "before": ma[k], "after": mb[k], "delta": round(mb[k] - ma[k], 3)}
              for k in ma if k in mb]
    sa, sb = (a.get("lab") or {}).get("performance_score"), (b.get("lab") or {}).get("performance_score")
    return {"comparable": not diffs, "differences": diffs, "score": [sa, sb], "deltas": deltas}


# ---------------------------------------------------------------- Markdown rendering

def fmt_v(metric, v):
    if v is None:
        return "-"
    if metric.startswith("CLS"):
        return f"{v:.2f}"
    return f"{v / 1000:.2f} s" if v >= 1000 else f"{round(v)} ms"


def to_md(r, title="Lighthouse summary"):
    L = [f"# {title}", ""]
    run = r.get("run")
    if run:
        L += [f"URL: {run['url']}", f"Fetched: {run['fetch_time']} | Lighthouse {run['lighthouse_version']}",
              f"Device: {run['form_factor']} {run['screen'] or ''} | Throttling: {run['throttling_method']}, "
              f"{run['preset']} (RTT {run['rtt_ms']} ms, {run['throughput_kbps']} Kbps, CPU x{run['cpu_slowdown']})"
              + (f" | {run['method_note']}" if run.get("method_note") else ""),
              f"Host benchmarkIndex: {run['benchmark_index']}",
              "This is ONE lab run: metrics vary run to run; compare medians of 3-5 runs, or field data."]
        for w in run["run_warnings"]:
            L.append(f"RUN WARNING: {w}")
        L.append("")
    L.append("## Field data (real users, p75): decides whether there is a problem")
    if not r["fields"]:
        L.append("None in this input. Core Web Vitals pass/fail cannot be stated from lab data.")
    for f in r["fields"]:
        head = f['source'] + (f", {f['scope']}-level" if f["scope"] in ("url", "origin") else "") + \
            (f" ({f['id']})" if f.get("id") else "")
        if f.get("form_factor"):
            head += f", form factor {f['form_factor']}"
        if f.get("period") and f["period"][0]:
            head += f", {f['period'][0]} to {f['period'][1]}"
        if f.get("origin_fallback"):
            head += " | ORIGIN FALLBACK: not enough data for this URL, these are whole-origin numbers"
        L += [head, "", "| Metric | p75 | Rating | Share good |", "|---|---|---|---|"]
        for k in ("LCP", "INP", "CLS", "FCP", "TTFB"):
            m = f["metrics"].get(k)
            if m:
                gs = f"{round(m['good_share'] * 100)}%" if isinstance(m.get("good_share"), (int, float)) else "-"
                L.append(f"| {k} | {fmt_v(k, m['p75'])} | {m['rating']} | {gs} |")
        L += ["", f"Core Web Vitals (field): {f['core_web_vitals']}",
              "Thresholds at p75: LCP <= 2.5 s good, > 4 s poor; INP <= 200 ms, > 500 ms; CLS <= 0.1, > 0.25.", ""]
    lab = r.get("lab")
    if lab:
        L += ["## Lab metrics (this run): explains why", "",
              f"Performance score: {lab['performance_score']} (a lab weighting, not a Core Web Vitals result)", "",
              "| Metric | Value | Lab rating | Threshold |", "|---|---|---|---|"]
        for m in lab["metrics"]:
            L.append(f"| {m['metric']} | {fmt_v(m['metric'], m['value'])} | {m['rating'] or '-'} | {m['threshold'] or '-'} |")
        L += ["", "TBT is a lab proxy for INP, not INP. A navigation run has no interactions.", ""]
    lcp = r.get("lcp")
    if lcp:
        L.append("## LCP element")
        el = lcp["element"]
        if el:
            L.append(f"Selector: {el.get('selector')} | Label: {el.get('nodeLabel')}")
            L.append(f"Snippet: {el.get('snippet')}")
        else:
            L.append("Not reported in this run.")
        flags = []
        if lcp["lazy_loaded"] is not None:
            flags.append("LAZY-LOADED (loading=lazy on the LCP element)" if lcp["lazy_loaded"] else "not lazy-loaded")
        if lcp.get("element_tag") and lcp["element_tag"] != "img" and not lcp["lcp_resource_url"]:
            flags.append(f"<{lcp['element_tag']}> element: text or CSS background, no <img> to prioritise")
        elif lcp["fetchpriority_high"] is not None:
            flags.append("fetchpriority=high present" if lcp["fetchpriority_high"] else "no fetchpriority=high")
        if lcp["lcp_resource_url"]:
            flags.append(f"resource {lcp['lcp_resource_url']}")
        if lcp["prioritize_savings_ms"]:
            flags.append(f"preload/prioritise est. LCP saving {fmt_v('LCP', lcp['prioritize_savings_ms'])}")
        if flags:
            L.append("Flags: " + "; ".join(flags))
        for c in lcp["discovery_checks"]:
            L.append(f"- {'pass' if c['passed'] else 'FAIL'}: {c['check']}")
        if lcp["phases"]:
            L += ["", "| Phase | Time | Share |", "|---|---|---|"]
            for p in lcp["phases"]:
                L.append(f"| {p['phase']} | {fmt_v('LCP', p['ms'])} | {p['share']} |")
            L.append(f"Dominant phase: {lcp['dominant_phase']}, which points to: {lcp['dominant_phase_points_to']}")
        L.append("")
    cls = r.get("cls")
    if cls and (cls["shifts"] or cls["unsized_images"] or cls["fonts_without_display"]):
        L.append("## Layout shift culprits (load window only; shifts after load are not in a lab run)")
        for s in cls["shifts"]:
            el = s["element"] or {}
            L.append(f"- {el.get('selector') or el.get('nodeLabel')}: {s['score']:.3f}"
                     + (f", cause: {'; '.join(s['causes'])}" if s["causes"] else ""))
        for u in cls["unsized_images"]:
            L.append(f"- unsized image: {u['url']}")
        for f in cls["fonts_without_display"]:
            L.append(f"- font without font-display: {f['url']}")
        L.append("")
    ops = r.get("opportunities")
    if ops:
        L += ["## Failing opportunities and diagnostics, ranked by the vital they move",
              "Savings are lab estimates for this run; overlapping savings do not add."
              + (" Rows marked * move a vital that fails in the field data." if any(
                  o.get("moves_failing_field_vital") for o in ops) else ""), "",
              "| Audit | Est. load saving | Metric savings | Note |", "|---|---|---|---|"]
        for o in ops:
            ms = ", ".join(f"{k} {fmt_v(k, v)}" for k, v in o["metric_savings"].items()) or "none"
            sav = []
            if o["overall_savings_ms"]:
                sav.append(fmt_v("x", o["overall_savings_ms"]))
            if o["overall_savings_bytes"]:
                sav.append(f"{round(o['overall_savings_bytes'] / 1024)} KiB")
            note = o.get("note", "")
            if o.get("overlaps_with"):
                note = (note + "; " if note else "") + "overlaps " + ", ".join(o["overlaps_with"])
            star = "* " if o.get("moves_failing_field_vital") else ""
            L.append(f"| {star}{o['id']}: {o['title']} | {' / '.join(sav) or '-'} | {ms} | {note} |")
        L.append("")
    mt = r.get("main_thread")
    if mt and (mt["long_tasks"] or mt["third_parties"] or mt["script_bootup"]):
        L.append("## Main thread (lab TBT; field INP is the real check)")
        if mt["main_thread_total_ms"] is not None:
            L.append(f"Main-thread work: {fmt_v('x', mt['main_thread_total_ms'])}")
        if mt["long_tasks"]:
            L += ["", "Long tasks:", "| Script | By | Duration | Start |", "|---|---|---|---|"]
            for t in mt["long_tasks"]:
                L.append(f"| {t['url']} | {t['by']} | {t['duration_ms']} ms | {t['start_ms']} ms |")
            L.append("Long tasks by origin: " + "; ".join(
                f"{o['by']} {o['count']} task{'s' if o['count'] != 1 else ''} / {o['total_ms']} ms" for o in mt["long_tasks_by_origin"]))
        if mt["third_parties"]:
            L += ["", "Third parties:", "| Entity | Main thread | Blocking | Transfer |", "|---|---|---|---|"]
            for t in mt["third_parties"]:
                b = f"{t['blocking_ms']} ms" if t["blocking_ms"] is not None else "-"
                L.append(f"| {t['entity']} | {t['main_thread_ms']} ms | {b} | {t['transfer_kb']} KiB |")
        if mt["script_bootup"]:
            L += ["", "Script execution:", "| Script | By | Total | Scripting |", "|---|---|---|---|"]
            for s in mt["script_bootup"]:
                L.append(f"| {s['url']} | {s['by']} | {s['total_ms']} ms | {s['scripting_ms']} ms |")
        L.append("")
    rb = r.get("render_blocking")
    if rb:
        L += ["## Render-blocking resources", "| URL | Size | Est. wasted |", "|---|---|---|"]
        for x in rb:
            L.append(f"| {x['url']} | {x['kb']} KiB | {x['wasted_ms']} ms |")
        L.append("")
    return "\n".join(L)


def cmp_md(c):
    L = ["# Comparison of the two runs", ""]
    if c["comparable"]:
        L.append("Same URL, Lighthouse version, device and throttling.")
    else:
        L.append("NOT COMPARABLE: the runs differ in " + "; ".join(c["differences"]))
    L += [f"Performance score: {c['score'][0]} -> {c['score'][1]}", "", "| Metric | Before | After | Delta |",
          "|---|---|---|---|"]
    for d in c["deltas"]:
        L.append(f"| {d['metric']} | {d['before']} | {d['after']} | {d['delta']:+} |")
    L += ["", "Two single runs: a difference is not an improvement until it holds across the median of 3-5 runs "
          "per side with identical settings, or shows up in field data."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reports", nargs="+", help="Lighthouse JSON, PSI JSON or CrUX JSON path, or - for stdin (max 2)")
    ap.add_argument("--field", help="extra field data: a PSI response or CrUX API record JSON")
    ap.add_argument("--lcp-p75", type=float, help="field LCP p75 in ms (e.g. from RUM)")
    ap.add_argument("--inp-p75", type=float, help="field INP p75 in ms")
    ap.add_argument("--cls-p75", type=float, help="field CLS p75 (unitless)")
    ap.add_argument("--field-source", default="provided (RUM or other)", help="label for --*-p75 numbers")
    ap.add_argument("--top", type=int, default=10, help="rows per list (default 10)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    ap.add_argument("-o", "--out", help="write here instead of stdout")
    args = ap.parse_args()
    if len(args.reports) > 2:
        die("pass one report, or two to compare")

    extra = []
    if args.field:
        _, extra = classify(load(args.field), args.field)
    mf = manual_field(args)
    if mf:
        extra.append(mf)

    results = []
    for path in args.reports:
        lhr, fields = classify(load(path), path)
        results.append(summarise(lhr, fields + extra, args.top))

    if len(results) == 2:
        c = compare(results[0], results[1])
        payload = {"before": results[0], "after": results[1], "comparison": c}
        text = json.dumps(payload, indent=2) if args.json else "\n\n".join(
            [cmp_md(c), to_md(results[0], "Run 1: " + args.reports[0]), to_md(results[1], "Run 2: " + args.reports[1])])
    else:
        text = json.dumps(results[0], indent=2) if args.json else to_md(results[0])

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()

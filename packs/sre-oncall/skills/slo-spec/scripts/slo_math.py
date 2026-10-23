#!/usr/bin/env python3
"""Error-budget and burn-rate arithmetic for one or more SLOs.

Stdlib only; runs on Python 3.9+.

For each SLO it prints:
  * the error budget as a fraction, as minutes of full outage per window, and
    (when traffic is given) as bad requests per window at that traffic;
  * a multi-window, multi-burn-rate alert table: burn rate, long and short
    windows, the error rate that trips it, the budget consumed when it fires,
    the time from a full budget to exhaustion at that burn, and the expected
    number of bad events in each window at the threshold;
  * the share of the budget a full outage of a given length spends (--outage);
  * flags: windows with fewer than --min-events expected bad events (too noisy
    to alert on), thresholds above 100% (the alert can never fire), a long
    window longer than the SLO window, and a target above what the hard
    dependencies in series allow.

Usage (one SLO):
  python3 slo_math.py --target 99.9 --window 30 --rpd 1200000
  python3 slo_math.py --target 99.5% --window 28 --rph 40 \
      --alerts "14.4:1h:5m:page,6:6h:30m:page,1:3d:6h:ticket" --dep 99.9 --json

Usage (several SLOs from a JSON file, or "-" for stdin):
  python3 slo_math.py --batch slos.json [--json] [-o out.txt]

  slos.json is a list of objects:
    {"name": "checkout availability", "target": 99.9, "window_days": 30,
     "requests_per_day": 1200000,          # or "requests_per_hour"
     "alerts": "standard",                 # optional; or the --alerts string
     "dependencies": [99.95, 99.9],        # optional; hard deps in series
     "outages_minutes": [40, 50]}          # optional; full outages to price

Standard alert set (Google SRE workbook, chapter 5, tuned for a 30-day window):
  14.4x  long 1h  short 5m   page
  6x     long 6h  short 30m  page
  1x     long 3d  short 6h   ticket

Traffic is treated as an even average. Minutes of full outage are
time-based; for a request-based SLI they equal bad requests only if traffic
is uniform, so peak hours burn budget faster than the minutes suggest.

Exit codes: 0 ok, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from typing import Any, Dict, List, Optional

STANDARD_ALERTS = "14.4:1h:5m:page,6:6h:30m:page,1:3d:6h:ticket"
DEFAULT_MIN_EVENTS = 10.0


class InputError(Exception):
    pass


# ---------------------------------------------------------------- parsing

def parse_target(value: Any) -> float:
    """Return the target as a fraction in (0, 1). Accepts 99.9, '99.9%', 0.999."""
    text = str(value).strip().rstrip("%").strip()
    try:
        num = float(text)
    except ValueError:
        raise InputError("target must be a number like 99.9 or 99.9%%, got %r" % value)
    if math.isnan(num) or math.isinf(num):
        raise InputError("target must be a finite number, got %r" % value)
    frac = num / 100.0 if num > 1.0 else num
    if frac >= 1.0:
        raise InputError("a 100% target leaves no error budget: every failure is a breach "
                         "and nothing can ever ship safely. Pick a target below 100%.")
    if frac <= 0.0:
        raise InputError("target must be above 0%%, got %r" % value)
    return frac


def parse_duration_hours(text: str) -> float:
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhdw])\s*", str(text).lower())
    if not m:
        raise InputError("duration must look like 5m, 1h, 6h, 3d or 1w, got %r" % text)
    n, unit = float(m.group(1)), m.group(2)
    if n <= 0:
        raise InputError("duration must be positive, got %r" % text)
    return n * {"s": 1 / 3600.0, "m": 1 / 60.0, "h": 1.0, "d": 24.0, "w": 168.0}[unit]


def parse_alerts(spec: Optional[str]) -> List[Dict[str, Any]]:
    if spec is None or str(spec).strip().lower() in ("", "standard"):
        spec = STANDARD_ALERTS
    rows = []
    for chunk in str(spec).split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(":")
        if len(parts) not in (3, 4):
            raise InputError("alert must be burn:long:short[:severity], e.g. 14.4:1h:5m:page, "
                             "got %r" % chunk)
        try:
            burn = float(parts[0].rstrip("x"))
        except ValueError:
            raise InputError("burn rate must be a number, got %r" % parts[0])
        if burn <= 0 or math.isinf(burn) or math.isnan(burn):
            raise InputError("burn rate must be a positive number, got %r" % parts[0])
        long_h = parse_duration_hours(parts[1])
        short_h = parse_duration_hours(parts[2])
        if short_h >= long_h:
            raise InputError("short window (%s) must be shorter than long window (%s)"
                             % (parts[2], parts[1]))
        severity = parts[3].strip() if len(parts) == 4 and parts[3].strip() else "page"
        rows.append({"burn": burn, "long": parts[1].strip(), "short": parts[2].strip(),
                     "long_hours": long_h, "short_hours": short_h, "severity": severity})
    if not rows:
        raise InputError("no alerts given")
    return rows


def positive(value: Any, name: str, allow_zero: bool = False) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise InputError("%s must be a number, got %r" % (name, value))
    if math.isnan(num) or math.isinf(num) or num < 0 or (num == 0 and not allow_zero):
        raise InputError("%s must be %s, got %r" % (name, "zero or more" if allow_zero
                                                    else "greater than zero", value))
    return num


# ---------------------------------------------------------------- maths

def compute(name: str, target: Any, window_days: Any, rpd: Optional[float],
            alerts_spec: Optional[str], deps: List[Any], min_events: float,
            outages: Optional[List[Any]] = None) -> Dict[str, Any]:
    frac = parse_target(target)
    days = positive(window_days, "window (days)")
    budget = 1.0 - frac
    window_h = days * 24.0
    window_min = days * 1440.0
    rph = rpd / 24.0 if rpd is not None else None
    flags: List[str] = []

    result: Dict[str, Any] = {
        "name": name,
        "target_pct": round(frac * 100.0, 6),
        "window_days": days,
        "budget_fraction": round(budget, 12),
        "budget_pct": round(budget * 100.0, 6),
        "budget_minutes_full_outage": round(budget * window_min, 4),
        "requests_per_day": rpd,
        "requests_in_window": round(rpd * days, 2) if rpd is not None else None,
        "budget_bad_requests": round(budget * rpd * days, 2) if rpd is not None else None,
        "alerts": [],
        "dependencies": None,
        "outages": [],
        "flags": flags,
    }
    if rpd is None:
        flags.append("No traffic given: the budget in bad requests and the noise checks "
                     "are not computed.")
    elif result["budget_bad_requests"] < min_events:
        flags.append("The whole window's budget is %s bad requests: one or two failures "
                     "spend it. Use a longer window or synthetic probes."
                     % fmt_count(result["budget_bad_requests"]))

    for a in parse_alerts(alerts_spec):
        threshold = a["burn"] * budget
        row = {
            "burn_rate": a["burn"],
            "long_window": a["long"],
            "short_window": a["short"],
            "severity": a["severity"],
            "error_rate_threshold_pct": round(threshold * 100.0, 6),
            "budget_consumed_at_fire_pct": round(a["burn"] * a["long_hours"] / window_h * 100.0, 4),
            "hours_to_exhaustion": round(window_h / a["burn"], 4),
            "can_fire": threshold <= 1.0,
            "expected_bad_long": None,
            "expected_bad_short": None,
            "min_requests_per_hour_for_long": None,
            "min_requests_per_hour_for_short": None,
            "noisy": [],
        }
        label = "%gx %s/%s" % (a["burn"], a["long"], a["short"])
        if threshold > 1.0:
            flags.append("%s: the error rate that trips it is %.4g%%, above 100%%, so it can "
                         "never fire. Lower the burn rate for this target."
                         % (label, threshold * 100.0))
        if a["long_hours"] > window_h:
            flags.append("%s: the long window is longer than the %g-day SLO window."
                         % (label, days))
        if rph is not None:
            bad_long = threshold * rph * a["long_hours"]
            bad_short = threshold * rph * a["short_hours"]
            row["expected_bad_long"] = round(bad_long, 3)
            row["expected_bad_short"] = round(bad_short, 3)
            row["min_requests_per_hour_for_long"] = round(
                min_events / (threshold * a["long_hours"]), 2)
            row["min_requests_per_hour_for_short"] = round(
                min_events / (threshold * a["short_hours"]), 2)
            for which, n in (("long", bad_long), ("short", bad_short)):
                if n < min_events:
                    row["noisy"].append(which)
            if row["can_fire"] and "long" in row["noisy"]:
                flags.append("%s: only %s bad events in the long window at the threshold "
                             "(under %g) at %s requests/hour - a handful of failures fires it, "
                             "so it is too noisy to alert on. Needs %s requests/hour, a longer "
                             "window, or synthetic probes."
                             % (label, fmt_count(bad_long), min_events, fmt_count(rph),
                                fmt_count(row["min_requests_per_hour_for_long"])))
            elif row["can_fire"] and "short" in row["noisy"]:
                flags.append("%s: only %s bad events in the %s short window at the threshold "
                             "(under %g) - the short window will flap. Lengthen it (needs %s "
                             "requests/hour for %s)."
                             % (label, fmt_count(bad_short), a["short"], min_events,
                                fmt_count(row["min_requests_per_hour_for_short"]), a["short"]))
        result["alerts"].append(row)

    for o in outages or []:
        mins = positive(o, "outage minutes")
        share = mins / (budget * window_min) * 100.0
        result["outages"].append({"minutes": mins, "budget_spent_pct": round(share, 2)})
        if share >= 100.0:
            flags.append("A %g-minute full outage spends %.0f%% of the budget on its own."
                         % (mins, share))

    if deps:
        dep_fracs = [parse_target(d) for d in deps]
        ceiling = 1.0
        for d in dep_fracs:
            ceiling *= d
        dep_unavail = 1.0 - ceiling
        share = dep_unavail / budget * 100.0
        result["dependencies"] = {
            "slos_pct": [round(d * 100.0, 6) for d in dep_fracs],
            "serial_ceiling_pct": round(ceiling * 100.0, 6),
            "budget_used_by_dependencies_pct": round(share, 2),
            "achievable_without_redundancy": frac <= ceiling,
        }
        if frac > ceiling:
            flags.append("Target %s%% is above %s%%, what the hard dependencies allow in series "
                         "(they alone would spend %.0f%% of the budget at their own SLOs). "
                         "Not achievable without redundancy, caching or a fallback path."
                         % (fmt_pct(frac), fmt_pct(ceiling), share))
        elif share >= 50.0:
            flags.append("The hard dependencies at their own SLOs would spend %.0f%% of the "
                         "budget, leaving %.0f%% for this service's own failures."
                         % (share, 100.0 - share))
    return result


# ---------------------------------------------------------------- output

def fmt_pct(frac: float) -> str:
    return ("%.6f" % (frac * 100.0)).rstrip("0").rstrip(".")


def fmt_count(n: Optional[float]) -> str:
    if n is None:
        return "-"
    if abs(n - round(n)) < 1e-9 and abs(n) >= 1:
        return "{:,}".format(int(round(n)))
    if abs(n) >= 100:
        return "{:,.0f}".format(n)
    return ("%.2f" % n).rstrip("0").rstrip(".")


def fmt_hours(h: float) -> str:
    total_min = int(round(h * 60))
    d, rem = divmod(total_min, 1440)
    hh, mm = divmod(rem, 60)
    parts = []
    if d:
        parts.append("%dd" % d)
    if hh:
        parts.append("%dh" % hh)
    if mm or not parts:
        parts.append("%dm" % mm)
    return " ".join(parts)


def fmt_minutes(m: float) -> str:
    whole = int(m)
    secs = int(round((m - whole) * 60))
    if secs == 60:
        whole, secs = whole + 1, 0
    human = fmt_hours(whole / 60.0) if whole else "0m"
    if secs:
        human += " %ds" % secs
    return human


def render_text(r: Dict[str, Any]) -> str:
    out = []
    title = r["name"] or "SLO"
    out.append("%s: %s%% over %g days" % (title, fmt_pct(r["target_pct"] / 100.0), r["window_days"]))
    out.append("  Error budget: %s%% of valid events" % fmt_pct(r["budget_fraction"]))
    out.append("  = %s minutes of full outage per window (%s)"
               % (("%.2f" % r["budget_minutes_full_outage"]).rstrip("0").rstrip("."),
                  fmt_minutes(r["budget_minutes_full_outage"])))
    if r["requests_per_day"] is not None:
        out.append("  = %s bad requests per window at %s requests/day (%s requests in window)"
                   % (fmt_count(r["budget_bad_requests"]), fmt_count(r["requests_per_day"]),
                      fmt_count(r["requests_in_window"])))
    out.append("")
    head = ["burn", "long", "short", "severity", "trips at err%", "budget at fire",
            "exhaust in", "bad(long)", "bad(short)"]
    rows = [head]
    for a in r["alerts"]:
        rows.append([
            "%gx" % a["burn_rate"], a["long_window"], a["short_window"], a["severity"],
            ("%.4f" % a["error_rate_threshold_pct"]).rstrip("0").rstrip(".") + "%",
            ("%.2f" % a["budget_consumed_at_fire_pct"]).rstrip("0").rstrip(".") + "%",
            fmt_hours(a["hours_to_exhaustion"]),
            fmt_count(a["expected_bad_long"]) + (" *" if "long" in a["noisy"] else ""),
            fmt_count(a["expected_bad_short"]) + (" *" if "short" in a["noisy"] else ""),
        ])
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(head))]
    for i, row in enumerate(rows):
        out.append("  " + "  ".join(str(c).ljust(widths[j]) for j, c in enumerate(row)).rstrip())
        if i == 0:
            out.append("  " + "  ".join("-" * w for w in widths))
    if any(a["noisy"] for a in r["alerts"]):
        out.append("  * fewer than the minimum expected bad events in that window (see flags)")
    if r["outages"]:
        out.append("")
        for o in r["outages"]:
            out.append("  A %g-minute full outage spends %s%% of this budget"
                       % (o["minutes"], ("%.2f" % o["budget_spent_pct"]).rstrip("0").rstrip(".")))
    if r["dependencies"]:
        d = r["dependencies"]
        out.append("")
        out.append("  Hard dependencies in series: %s -> ceiling %s%%; at their SLOs they "
                   "spend %s%% of this budget"
                   % (", ".join(fmt_pct(x / 100.0) + "%" for x in d["slos_pct"]),
                      fmt_pct(d["serial_ceiling_pct"] / 100.0),
                      ("%.2f" % d["budget_used_by_dependencies_pct"]).rstrip("0").rstrip(".")))
    if r["flags"]:
        out.append("")
        out.append("  Flags:")
        for f in r["flags"]:
            out.append("  - " + f)
    return "\n".join(out)


# ---------------------------------------------------------------- CLI

def load_batch(path: str) -> List[Dict[str, Any]]:
    try:
        if path == "-":
            data = json.load(sys.stdin)
        else:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    except json.JSONDecodeError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        raise InputError("batch file must hold a non-empty list of SLO objects")
    return data


def traffic_from(obj: Dict[str, Any]) -> Optional[float]:
    rpd, rph = obj.get("requests_per_day"), obj.get("requests_per_hour")
    if rpd is not None and rph is not None:
        raise InputError("give requests_per_day or requests_per_hour, not both")
    if rpd is not None:
        return positive(rpd, "requests_per_day", allow_zero=True)
    if rph is not None:
        return positive(rph, "requests_per_hour", allow_zero=True) * 24.0
    return None


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Error budget and burn-rate alert arithmetic.")
    p.add_argument("--target", help="SLO target, e.g. 99.9 or 99.9%% or 0.999")
    p.add_argument("--window", help="SLO window in days, e.g. 30 or 28")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--rpd", help="valid requests (events) per day")
    g.add_argument("--rph", help="valid requests (events) per hour")
    p.add_argument("--alerts", default="standard",
                   help='"standard" or "burn:long:short[:severity],..." e.g. "14.4:1h:5m:page"')
    p.add_argument("--outage", action="append", default=[],
                   help="minutes of a full outage to price against the budget (repeatable)")
    p.add_argument("--dep", action="append", default=[],
                   help="SLO of a hard dependency called in series (repeatable), e.g. 99.9")
    p.add_argument("--name", default="", help="label for the SLO")
    p.add_argument("--batch", help="JSON file (or - for stdin) with a list of SLOs")
    p.add_argument("--min-events", default=str(DEFAULT_MIN_EVENTS),
                   help="expected bad events below which a window is too noisy (default 10)")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    p.add_argument("-o", "--out", help="write output to this path instead of stdout")
    args = p.parse_args(argv)

    try:
        min_events = positive(args.min_events, "--min-events")
        results = []
        if args.batch:
            for i, obj in enumerate(load_batch(args.batch), 1):
                if not isinstance(obj, dict):
                    raise InputError("batch entry %d is not an object" % i)
                for key in ("target", "window_days"):
                    if key not in obj:
                        raise InputError("batch entry %d is missing %r" % (i, key))
                deps = obj.get("dependencies") or []
                if not isinstance(deps, list):
                    raise InputError("batch entry %d: dependencies must be a list" % i)
                outages = obj.get("outages_minutes") or []
                if not isinstance(outages, list):
                    raise InputError("batch entry %d: outages_minutes must be a list" % i)
                results.append(compute(str(obj.get("name", "SLO %d" % i)), obj["target"],
                                       obj["window_days"], traffic_from(obj),
                                       obj.get("alerts"), deps, min_events,
                                       outages))
        else:
            if args.target is None or args.window is None:
                raise InputError("give --target and --window, or --batch FILE")
            rpd = None
            if args.rpd is not None:
                rpd = positive(args.rpd, "--rpd", allow_zero=True)
            elif args.rph is not None:
                rpd = positive(args.rph, "--rph", allow_zero=True) * 24.0
            results.append(compute(args.name, args.target, args.window, rpd,
                                   args.alerts, args.dep, min_events, args.outage))
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        text = json.dumps(results if args.batch else results[0], indent=2)
    else:
        text = "\n\n".join(render_text(r) for r in results)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

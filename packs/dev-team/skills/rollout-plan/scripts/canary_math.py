#!/usr/bin/env python3
"""How long each exposure step of a canary or flag rollout must run before its
numbers can detect the regression you care about.

Uses the normal approximation to the two-proportion z-test. The flag-on cohort
(treatment) is compared with a concurrent flag-off cohort (control). By default
the control is everyone not exposed (100% - exposure); pass --control-pct to fix
it at a holdback size instead.

For each step it prints the units (requests or users) each arm needs and the
hours that takes at the given traffic, flags steps that cannot reach that in
--max-hours, says the smallest regression the step *can* detect in that window,
and suggests the smallest exposure that reaches sufficiency in the window.

Rates and regressions accept a fraction (0.008), a percent ("0.8%") or, for an
absolute regression, percentage points ("0.3pp").

Usage:
    python3 canary_math.py --baseline 0.8% --detect-abs 0.3pp --traffic 9000
    python3 canary_math.py --baseline 3.1% --detect-rel 10% --direction down \\
        --traffic 9000 --steps 1,5,25,50 --unit users
    python3 canary_math.py ... --json

Exit codes: 0 printed, 2 bad input.
"""

import argparse
import json
import math
import sys
from statistics import NormalDist

Z = NormalDist()


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


def parse_rate(text, name, allow_pp=False):
    s = str(text).strip().lower().replace(" ", "")
    try:
        if s.endswith("pp"):
            if not allow_pp:
                fail(name + ": 'pp' only applies to --detect-abs")
            return float(s[:-2]) / 100.0
        if s.endswith("%"):
            return float(s[:-1]) / 100.0
        v = float(s)
    except ValueError:
        fail(name + ": not a number: " + str(text))
    return v


def fmt_pct(x, digits=2):
    return ("{:." + str(digits) + "f}").format(x * 100).rstrip("0").rstrip(".") + "%"


def fmt_pp(x):
    return "{:.3f}".format(x * 100).rstrip("0").rstrip(".") + " pp"


def fmt_hours(h):
    if h is None:
        return "n/a"
    if h < 1:
        return "{:.0f} min".format(max(1, math.ceil(h * 60)))
    if h < 48:
        return "{:.1f} h".format(h)
    return "{:.1f} h ({:.1f} d)".format(h, h / 24)


def z_values(alpha, power, one_sided):
    za = Z.inv_cdf(1 - alpha) if one_sided else Z.inv_cdf(1 - alpha / 2)
    zb = Z.inv_cdf(power)
    return za, zb


def equal_arm_n(p1, p2, za, zb):
    """Units per arm for two equal arms."""
    pbar = (p1 + p2) / 2
    num = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return math.ceil((num / (p2 - p1)) ** 2)


def hours_needed(p1, p2, e, c, traffic, za, zb):
    """Hours until a treatment arm of share e and control of share c is powered.

    n1 = traffic*e*t (treatment, rate p2), n2 = traffic*c*t (control, rate p1).
    Both arms scale with t, so the power equation solves in closed form.
    """
    if e <= 0 or c <= 0:
        return None
    pbar = (e * p2 + c * p1) / (e + c)
    a = za * math.sqrt(pbar * (1 - pbar) * (1 / e + 1 / c))
    b = zb * math.sqrt(p2 * (1 - p2) / e + p1 * (1 - p1) / c)
    return ((a + b) / abs(p2 - p1)) ** 2 / traffic


def detectable_in(p1, direction, e, c, traffic, za, zb, hours):
    """Smallest absolute regression detectable in `hours` (bisection)."""
    if e <= 0 or c <= 0:
        return None
    hi = (1 - p1) if direction == "up" else p1
    hi *= 0.999
    lo = 1e-9
    if hours_needed(p1, p1 + hi if direction == "up" else p1 - hi, e, c, traffic, za, zb) > hours:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        p2 = p1 + mid if direction == "up" else p1 - mid
        if hours_needed(p1, p2, e, c, traffic, za, zb) <= hours:
            hi = mid
        else:
            lo = mid
    return hi


def smallest_sufficient_exposure(p1, p2, traffic, za, zb, max_hours, control_pct):
    """Smallest exposure (0.1% steps, up to 50%) that is powered within max_hours."""
    for tenth in range(1, 501):
        e = tenth / 1000.0
        c = control_pct if control_pct is not None else 1 - e
        if e + c > 1 + 1e-9:
            break
        h = hours_needed(p1, p2, e, c, traffic, za, zb)
        if h is not None and h <= max_hours:
            return e, h
    return None, None


def main():
    ap = argparse.ArgumentParser(description="Hours each canary/flag exposure step must run to detect a regression.")
    ap.add_argument("--baseline", required=True, help="baseline rate of the metric in control, e.g. 0.8%% or 0.008")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--detect-abs", help="smallest regression worth catching, absolute: 0.3pp or 0.003")
    g.add_argument("--detect-rel", help="smallest regression worth catching, relative to baseline: 25%% or 0.25")
    ap.add_argument("--traffic", required=True, type=float, help="units per hour across all users (requests or users)")
    ap.add_argument("--unit", default="requests", help="what --traffic counts; use the unit the flag randomises on (default: requests)")
    ap.add_argument("--steps", default="1,5,25,50,100", help="exposure percentages, comma-separated (default: 1,5,25,50,100)")
    ap.add_argument("--control-pct", help="fixed control (holdback) size in percent; default: everyone not exposed")
    ap.add_argument("--direction", choices=["up", "down"], default="up",
                    help="up = a rise is the regression (error rate, default); down = a fall is (conversion)")
    ap.add_argument("--alpha", type=float, default=0.05, help="false-alarm rate (default 0.05)")
    ap.add_argument("--power", type=float, default=0.8, help="chance of catching a real regression (default 0.8)")
    ap.add_argument("--one-sided", action="store_true", help="one-sided test (only the regression direction); default two-sided")
    ap.add_argument("--max-hours", type=float, default=72.0, help="longest sensible step (default 72)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a markdown table")
    args = ap.parse_args()

    p1 = parse_rate(args.baseline, "--baseline")
    if not 0 < p1 < 1:
        fail("--baseline must be between 0 and 100%")
    if args.detect_abs is not None:
        d = parse_rate(args.detect_abs, "--detect-abs", allow_pp=True)
    else:
        d = parse_rate(args.detect_rel, "--detect-rel") * p1
    if d <= 0:
        fail("the regression to detect must be greater than zero")
    p2 = p1 + d if args.direction == "up" else p1 - d
    if not 0 < p2 < 1:
        fail("baseline plus the regression falls outside 0-100%")
    if not math.isfinite(args.traffic) or args.traffic <= 0:
        fail("--traffic must be a finite number greater than zero")
    if not 0 < args.alpha < 1 or not 0 < args.power < 1:
        fail("--alpha and --power must be between 0 and 1")
    if args.max_hours <= 0:
        fail("--max-hours must be greater than zero")
    control = None
    if args.control_pct is not None:
        control = parse_rate(args.control_pct.rstrip("%") + "%", "--control-pct")
        if not 0 < control < 1:
            fail("--control-pct must be between 0 and 100")
    try:
        steps = [float(s.strip().rstrip("%")) / 100.0 for s in args.steps.split(",") if s.strip()]
    except ValueError:
        fail("--steps must be comma-separated percentages, e.g. 1,5,25,50,100")
    if not steps or any(not 0 < s <= 1 for s in steps):
        fail("--steps must be percentages between 0 and 100")

    za, zb = z_values(args.alpha, args.power, args.one_sided)
    n_equal = equal_arm_n(p1, p2, za, zb)

    rows = []
    for e in steps:
        c = control if control is not None else 1 - e
        row = {"exposure_pct": round(e * 100, 4), "control_pct": round(c * 100, 4)}
        if e + c > 1 + 1e-9:
            row.update(status="invalid", note="exposure plus control exceeds 100%")
        elif c <= 1e-9:
            row.update(status="no-control", hours=None,
                       note="no concurrent control at 100%: promote on the previous step's comparison, "
                            "or keep a holdback (--control-pct) to keep comparing")
        else:
            h = hours_needed(p1, p2, e, c, args.traffic, za, zb)
            row["hours"] = round(h, 3)
            row["treatment_units"] = math.ceil(h * args.traffic * e)
            row["control_units"] = math.ceil(h * args.traffic * c)
            if h <= args.max_hours:
                row["status"] = "sufficient"
            else:
                row["status"] = "insufficient"
                mde = detectable_in(p1, args.direction, e, c, args.traffic, za, zb, args.max_hours)
                row["detectable_in_max_hours_abs"] = None if mde is None else round(mde, 6)
        rows.append(row)

    best_e, best_h = smallest_sufficient_exposure(p1, p2, args.traffic, za, zb, args.max_hours, control)

    result = {
        "baseline": p1, "regression_abs": round(d, 6), "regressed_rate": round(p2, 6),
        "direction": args.direction, "alpha": args.alpha, "power": args.power,
        "test": "one-sided" if args.one_sided else "two-sided",
        "traffic_per_hour": args.traffic, "unit": args.unit, "max_hours": args.max_hours,
        "equal_arm_units_per_arm": n_equal, "steps": rows,
        "smallest_sufficient_exposure_pct": None if best_e is None else round(best_e * 100, 1),
        "smallest_sufficient_exposure_hours": None if best_h is None else round(best_h, 2),
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    u = args.unit
    print("# Canary sufficiency")
    print()
    print("- Metric: baseline {} -> regression to catch {} ({} rate {}), {} test, alpha {}, power {}".format(
        fmt_pct(p1, 3), fmt_pp(d), "rising to" if args.direction == "up" else "falling to",
        fmt_pct(p2, 3), result["test"], args.alpha, args.power))
    print("- Traffic: {:,.0f} {} per hour; control = {}".format(
        args.traffic, u, "fixed {} holdback".format(fmt_pct(control)) if control is not None else "everyone not exposed"))
    print("- Equal arms would need {:,} {} per arm".format(n_equal, u))
    print()
    print("| Exposure | Control | Treatment {u} needed | Control {u} needed | Minimum time | Status |".format(u=u))
    print("|---|---|---|---|---|---|")
    for r in rows:
        exp = fmt_pct(r["exposure_pct"] / 100)
        ctl = fmt_pct(r["control_pct"] / 100)
        if r["status"] in ("no-control", "invalid"):
            print("| {} | {} | - | - | n/a | {} |".format(exp, ctl, r["note"]))
            continue
        status = "ok" if r["status"] == "sufficient" else "INSUFFICIENT: over {:g} h".format(args.max_hours)
        if r["status"] == "insufficient":
            m = r.get("detectable_in_max_hours_abs")
            status += "; in {:g} h it can only catch {}".format(
                args.max_hours, "nothing measurable" if m is None else ">= " + fmt_pp(m))
        print("| {} | {} | {:,} | {:,} | {} | {} |".format(
            exp, ctl, r["treatment_units"], r["control_units"], fmt_hours(r["hours"]), status))
    print()
    if best_e is None:
        print("No exposure up to 50% reaches sufficiency within {:g} h. Catch a larger regression, "
              "run longer, or pick a metric with a higher baseline rate.".format(args.max_hours))
    else:
        print("Smallest exposure that reaches sufficiency within {:g} h: {} (about {}).".format(
            args.max_hours, fmt_pct(best_e, 1), fmt_hours(best_h)))
    print()
    print("Minimum time is statistics only. A step also runs through at least one daily peak "
          "and any delayed effect (nightly jobs, next-day emails) before it is promoted.")


if __name__ == "__main__":
    main()

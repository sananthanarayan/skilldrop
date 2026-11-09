#!/usr/bin/env python3
"""Work out vesting schedules for founder stock, restricted stock, options and RSUs. Stdlib only.

Reads a vesting.json (each grant's holder, type, shares, grant date, vesting start, months,
cliff and frequency, and any acceleration, leaving date or change of control) and prints:
  - each grant's cliff date and amount, the date it fully vests, and what is vested on a date
  - a dated schedule (every vesting date, how many vest, the running total), whole shares only,
    with the rounding left to the last date so the total is exact
  - what happens when someone leaves: vested, unvested (forfeited or repurchasable), and the
    last day to exercise options
  - single- and double-trigger acceleration on a change of control
  - for US restricted stock (and early-exercised options), the 83(b) election deadline: 30 days
    from the grant, moved to the next business day when it falls on a weekend or federal holiday
A vesting date on the 29th–31st falls on the last day of shorter months.

Usage:
  python3 vesting.py vesting.json [--as-of 2027-06-30] [--csv schedule.csv] [--full]
Exit codes: 0 computed, 1 a check failed (a schedule that doesn't sum to its grant, a passed
83(b) deadline), 2 bad input.
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import math
import sys

STEP = {"monthly": 1, "quarterly": 3, "annual": 12, "annually": 12, "yearly": 12}
STOCK = {"founder stock", "restricted stock", "rsa"}


class InputError(Exception):
    pass


def day(v, what, allow_none=False):
    if v is None and allow_none:
        return None
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError:
        raise InputError(f"{what} must be a date as YYYY-MM-DD")


def add_months(d, n, anchor_day=None):
    """d plus n months, on anchor_day or the month's last day when the month is shorter."""
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    want = anchor_day or d.day
    return dt.date(y, m + 1, min(want, calendar.monthrange(y, m + 1)[1]))


def nth_weekday(y, m, weekday, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def last_weekday(y, m, weekday):
    d = dt.date(y, m, calendar.monthrange(y, m)[1])
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def us_holidays(y):
    """US federal legal holidays, plus DC Emancipation Day, as observed (IRC §7503 counts both)."""
    fixed = [dt.date(y, 1, 1), dt.date(y, 6, 19), dt.date(y, 7, 4), dt.date(y, 11, 11), dt.date(y, 12, 25),
             dt.date(y, 4, 16)]
    out = set()
    for d in fixed:
        if d.weekday() == 5:
            out.add(d - dt.timedelta(days=1))
        elif d.weekday() == 6:
            out.add(d + dt.timedelta(days=1))
        else:
            out.add(d)
    out |= {nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3), last_weekday(y, 5, 0), nth_weekday(y, 9, 0, 1),
            nth_weekday(y, 10, 0, 2), nth_weekday(y, 11, 3, 4)}
    return out


def next_business_day(d):
    while d.weekday() >= 5 or d in us_holidays(d.year) or d in us_holidays(d.year + 1):
        d += dt.timedelta(days=1)
    return d


def load(data):
    if not isinstance(data, dict) or not isinstance(data.get("grants"), list) or not data["grants"]:
        raise InputError("vesting.json needs `grants`: a list of grants")
    grants = []
    for i, g in enumerate(data["grants"], 1):
        if not isinstance(g, dict) or not str(g.get("holder", "")).strip():
            raise InputError(f"grant {i} needs a `holder`")
        who = str(g["holder"]).strip()
        shares = g.get("shares")
        if isinstance(shares, bool) or not isinstance(shares, int) or shares < 1:
            raise InputError(f"{who}: shares must be a whole number of at least 1")
        months = g.get("months", 48)
        cliff = g.get("cliff_months", 12)
        for v, what in ((months, "months"), (cliff, "cliff_months")):
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise InputError(f"{who}: {what} must be a whole number")
        if months < 1 or cliff > months:
            raise InputError(f"{who}: the cliff can't be longer than the vesting period")
        freq = str(g.get("frequency", "monthly")).lower()
        if freq not in STEP:
            raise InputError(f"{who}: frequency must be monthly, quarterly or annual")
        kind = str(g.get("type", "option")).lower()
        acc = g.get("acceleration") or {}
        if not isinstance(acc, dict):
            raise InputError(f"{who}: acceleration must be an object")
        for k in ("single", "double"):
            v = acc.get(k)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 100):
                raise InputError(f"{who}: acceleration.{k} must be a fraction (0.5) or a percent (50)")
        grant_date = day(g.get("grant_date") or g.get("vesting_start"), f"{who}: grant_date")
        grants.append({
            "holder": who, "type": kind, "shares": shares, "grant_date": grant_date,
            "start": day(g.get("vesting_start") or g.get("grant_date"), f"{who}: vesting_start"),
            "months": months, "cliff": cliff, "step": STEP[freq], "frequency": freq,
            "single": frac(acc.get("single")), "double": frac(acc.get("double")),
            "window": int(acc.get("window_months", 12)),
            "leave": day(g.get("leave_date"), f"{who}: leave_date", True),
            "pte_days": g.get("exercise_window_days"),
            "repurchase_days": g.get("repurchase_window_days"),
            "early_exercise": day(g.get("early_exercise_date"), f"{who}: early_exercise_date", True),
            "already_filed_83b": bool(g.get("filed_83b", False)),
        })
    return {"company": str(data.get("company", "The company")),
            "change_of_control": day(data.get("change_of_control"), "change_of_control", True),
            "us": str(data.get("jurisdiction", "US")).upper() in ("US", "USA", "UNITED STATES"),
            "grants": grants}


def frac(v):
    if v is None:
        return 0.0
    return v / 100 if v > 1 else float(v)


def schedule(g):
    """[(date, vesting now, cumulative)] in whole shares. Each date's total is the grant times the
    months elapsed over the months in all, rounded down, so rounding never runs ahead of the
    grant and the last date carries the remainder. A cliff that falls between two vesting dates
    vests on the cliff date itself."""
    ks = set(range(g["step"], g["months"] + 1, g["step"])) | {g["months"]}
    if g["cliff"]:
        ks.add(g["cliff"])
    rows, done = [], 0
    for k in sorted(k for k in ks if k >= g["cliff"]):
        cum = g["shares"] if k == g["months"] else math.floor(g["shares"] * k / g["months"])
        rows.append((add_months(g["start"], k, g["start"].day), cum - done, cum))
        done = cum
    return rows


def vested_on(rows, when):
    return max((c for d, _, c in rows if d <= when), default=0)


def outcome(cap, g, as_of):
    rows = schedule(g)
    fails, warns, notes = [], [], []
    if rows[-1][2] != g["shares"] or sum(n for _, n, _ in rows) != g["shares"]:
        fails.append(f"{g['holder']}: the schedule sums to {rows[-1][2]:,}, not {g['shares']:,}")
    cliff_date = add_months(g["start"], g["cliff"], g["start"].day) if g["cliff"] else None
    end = rows[-1][0]
    stop = g["leave"]
    coc = cap["change_of_control"]
    at = min(as_of, stop) if stop else as_of
    single = double = 0
    if coc and g["single"] and coc <= at:
        single = math.floor((g["shares"] - vested_on(rows, coc)) * g["single"])
        notes.append(f"single-trigger acceleration on the change of control ({coc}): {single:,} more shares vest")
    if coc and g["double"] and stop and coc <= stop <= add_months(coc, g["window"]):
        double = math.floor((g["shares"] - vested_on(rows, stop) - single) * g["double"])
        notes.append(f"double-trigger acceleration: left on {stop}, within {g['window']} months of the change of "
                     f"control, so {double:,} more shares vest")
    elif coc and g["double"] and stop is None:
        notes.append("double-trigger acceleration applies only if they are let go (or resign for good reason) "
                     f"within {g['window']} months of the change of control")
    # double trigger only counts once its second trigger (leaving) has happened by the date asked about
    vested = min(g["shares"], vested_on(rows, at) + single + (double if stop and at >= stop else 0))
    leave = None
    if stop:
        at_leave = min(g["shares"], vested_on(rows, stop) + double +
                       (single if coc and coc <= stop else 0))
        unvested = g["shares"] - at_leave
        vested_leave = at_leave
        if g["type"] in STOCK or g["early_exercise"]:
            leave = f"left {stop}: {vested_leave:,} vested, {unvested:,} unvested shares the company can buy back"
            if isinstance(g["repurchase_days"], int):
                leave += f"; the company must exercise the buy-back by {stop + dt.timedelta(days=g['repurchase_days'])} " \
                         f"({g['repurchase_days']} days), or it lapses"
            else:
                warns.append(f"{g['holder']}: the buy-back window isn't given; read it from the stock purchase agreement")
        else:
            days = g["pte_days"] if isinstance(g["pte_days"], int) else 90
            if not isinstance(g["pte_days"], int):
                warns.append(f"{g['holder']}: exercise window after leaving not given; assumed 90 days, the usual term")
            leave = (f"left {stop}: {vested_leave:,} vested, {unvested:,} forfeited; last day to exercise the vested options "
                     f"{stop + dt.timedelta(days=days)} ({days} days)")
    election = None
    needs_83b = cap["us"] and (g["type"] in STOCK or g["early_exercise"])
    if needs_83b:
        start = g["early_exercise"] or g["grant_date"]
        raw = start + dt.timedelta(days=30)
        deadline = next_business_day(raw)
        moved = f" (day 30, {raw}, is a weekend or holiday)" if deadline != raw else ""
        election = {"from": start, "deadline": deadline, "moved": moved}
        if as_of > deadline and not g["already_filed_83b"]:
            fails.append(f"{g['holder']}: the 83(b) deadline was {deadline}; it has passed unless it was filed")
    if g["start"].day > 28:
        nth = {29: "29th", 30: "30th", 31: "31st"}[g["start"].day]
        notes.append(f"vests on the {nth}, so on the last day of shorter months")
    return {"holder": g["holder"], "type": g["type"], "shares": g["shares"], "rows": rows, "cliff_date": cliff_date,
            "cliff_amount": vested_on(rows, cliff_date) if cliff_date else rows[0][2], "fully_vested": end,
            "vested": vested, "unvested": g["shares"] - vested, "as_of": at, "leave": leave, "election": election,
            "notes": notes, "fails": fails, "warns": warns}


def report(cap, results, full):
    L = [f"# {cap['company']}: vesting", "",
         "| Holder | Type | Shares | Cliff | Fully vested | Vested on date | Unvested |", "|---|---|---:|---|---|---:|---:|"]
    for r in results:
        cliff = f"{r['cliff_date']}: {r['cliff_amount']:,}" if r["cliff_date"] else "none"
        L.append(f"| {r['holder']} | {r['type']} | {r['shares']:,} | {cliff} | {r['fully_vested']} | "
                 f"{r['vested']:,} ({r['as_of']}) | {r['unvested']:,} |")
    for r in results:
        L += ["", f"## {r['holder']}"]
        if r["election"]:
            e = r["election"]
            L.append(f"- 83(b) election: file by **{e['deadline']}**, 30 days from {e['from']}{e['moved']}.")
        if r["leave"]:
            L.append(f"- {r['leave']}")
        for n in r["notes"]:
            L.append(f"- {n}")
        rows = r["rows"] if full or len(r["rows"]) <= 8 else (
            r["rows"][:2] + [x for x in r["rows"][2:-1] if x[0].month == r["rows"][0][0].month] + r["rows"][-1:])
        L += ["", "| Date | Vests | Total vested |", "|---|---:|---:|"]
        for d, n, c in rows:
            L.append(f"| {d} | {n:,} | {c:,} |")
        if rows is not r["rows"]:
            L.append(f"| … {len(r['rows'])} vesting dates in all (--full for every one) | | |")
    for r in results:
        L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Vesting schedules, leavers, acceleration and 83(b) deadlines.")
    ap.add_argument("vesting")
    ap.add_argument("--as-of", help="YYYY-MM-DD to report what is vested (default: today)")
    ap.add_argument("--csv", help="write every vesting date for every grant here")
    ap.add_argument("--full", action="store_true", help="show every vesting date, not one a year")
    args = ap.parse_args(argv)
    try:
        with open(args.vesting, encoding="utf-8-sig") as f:
            cap = load(json.load(f))
        as_of = day(args.as_of, "--as-of") if args.as_of else dt.date.today()
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"FAIL cannot read input: {e}")
        return 2
    except InputError as e:
        print(f"FAIL {e}")
        return 2
    results = [outcome(cap, g, as_of) for g in cap["grants"]]
    print(report(cap, results, args.full), end="")
    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Holder", "Date", "Vests", "Total vested"])
            for r in results:
                for d, n, c in r["rows"]:
                    w.writerow([r["holder"], d.isoformat(), n, c])
    return 1 if any(r["fails"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())

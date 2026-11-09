#!/usr/bin/env python3
"""Turn a commercial lease's terms into the dates and money a tenant has to plan around. Stdlib only.

Reads a terms.json (start, length, rent and how it changes, rent-free months, service charge,
deposit, break clauses, renewal option, notice periods) and prints:
  - rent year by year through stepped rents, fixed and index-linked reviews (with any cap and
    collar), rent-free months and upward-only reviews
  - what the tenant is committed to pay up to each break date and to the end of the term,
    rent and service charge together
  - every deadline as a date: each break notice, the renewal option's window, notice to leave,
    each rent review, the end of the rent-free period
  - deadlines already passed on the given date, and terms that can't all be true (a break
    after the end of the term, a notice longer than the time left, rent-free longer than the term)
An open-market review can't be priced in advance; it is shown as unknown from that date on.

Usage:
  python3 lease_terms.py terms.json [--as-of 2027-03-01] [--json]
Exit codes: 0 computed, 1 a deadline passed or the terms contradict each other, 2 bad input.
"""
import argparse
import calendar
import datetime as dt
import json
import math
import sys


class InputError(Exception):
    pass


def day(v, what):
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError:
        raise InputError(f"{what} must be a date as YYYY-MM-DD")


def add_months(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return dt.date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def num(v, what, lo=0.0):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < lo:
        raise InputError(f"{what} must be a number of at least {lo:g}")
    return float(v)


def rate(v, what):
    v = num(v, what, -100)
    return v / 100 if abs(v) >= 1 else v


def whole(v, what, lo=0):
    if isinstance(v, bool) or not isinstance(v, int) or v < lo:
        raise InputError(f"{what} must be a whole number of months")
    return v


def load(d):
    if not isinstance(d, dict):
        raise InputError("terms.json must be an object")
    start = day(d.get("start"), "start")
    term = whole(d.get("term_months"), "term_months", 1)
    rent = d.get("rent") or {}
    if not isinstance(rent, dict) or "annual" not in rent:
        raise InputError("`rent` needs `annual`, the starting yearly rent")
    reviews = []
    for i, r in enumerate(rent.get("reviews") or [], 1):
        kind = str(r.get("type", "fixed")).lower()
        if kind not in ("fixed", "index", "cpi", "rpi", "open market", "market"):
            raise InputError(f"review {i}: type must be fixed, index (cpi/rpi) or open market")
        rv = {"month": whole(r.get("month"), f"review {i}: month", 1), "type": kind,
              "upward_only": bool(r.get("upward_only", True))}
        if kind == "fixed":
            rv["increase"] = rate(r.get("increase", 0), f"review {i}: increase")
        elif kind in ("index", "cpi", "rpi"):
            rv["assumed"] = rate(r.get("assumed", 0), f"review {i}: assumed index rise")
            rv["cap"] = rate(r["cap"], f"review {i}: cap") if r.get("cap") is not None else None
            rv["collar"] = rate(r["collar"], f"review {i}: collar") if r.get("collar") is not None else None
            rv["compounded_years"] = whole(r.get("years", 1), f"review {i}: years", 1)
        reviews.append(rv)
    steps = [{"month": whole(s.get("from_month"), "stepped rent: from_month", 1),
              "annual": num(s.get("annual"), "stepped rent: annual")} for s in rent.get("stepped") or []]
    breaks = []
    for i, b in enumerate(d.get("breaks") or [], 1):
        bdate = day(b["date"], f"break {i}: date") if b.get("date") else None
        if bdate is None and b.get("month") is None:
            raise InputError(f"break {i}: give `month` (months from the start) or the lease's own `date`")
        if bdate is not None:
            months = (bdate.year - start.year) * 12 + bdate.month - start.month + (1 if bdate.day >= start.day - 1 else 0)
            b = dict(b, month=b.get("month", max(1, months)))
        breaks.append({"month": whole(b.get("month"), f"break {i}: month", 1), "date": bdate,
                       "notice": whole(b.get("notice_months"), f"break {i}: notice_months", 0),
                       "party": str(b.get("party", "tenant")),
                       "conditions": [str(c) for c in b.get("conditions") or []],
                       "penalty_months": num(b.get("penalty_months", 0), f"break {i}: penalty_months")})
    sc = d.get("service_charge") or {}
    dep = d.get("deposit") or {}
    renewal = d.get("renewal_option")
    return {
        "currency": str(d.get("currency", "GBP")), "start": start, "term": term,
        "annual": num(rent["annual"], "rent.annual"), "payable": str(rent.get("payable", "quarterly")).lower(),
        "rent_free": whole(rent.get("rent_free_months", 0), "rent_free_months"),
        "reviews": sorted(reviews, key=lambda r: r["month"]), "steps": sorted(steps, key=lambda s: s["month"]),
        "service": num(sc.get("annual", 0), "service_charge.annual"),
        "service_cap": num(sc["cap"], "service_charge.cap") if sc.get("cap") is not None else None,
        "deposit": num(dep["amount"], "deposit.amount") if dep.get("amount") is not None else (
            num(dep.get("months", 0), "deposit.months") / 12 * num(rent["annual"], "rent.annual")),
        "breaks": sorted(breaks, key=lambda b: b["month"]),
        "renewal": None if not renewal else {
            "notice": whole(renewal.get("notice_months"), "renewal_option.notice_months", 0),
            "earliest": whole(renewal.get("earliest_months_before_end", renewal.get("notice_months", 0)),
                              "renewal_option.earliest_months_before_end", 0)},
        "leave_notice": whole(d["notice_to_leave_months"], "notice_to_leave_months")
        if d.get("notice_to_leave_months") is not None else None,
    }


def rent_by_month(t):
    """Yearly rate in force for each month, and None once an open-market review makes it unknown."""
    rates = []
    current = t["annual"]
    steps = {s["month"]: s["annual"] for s in t["steps"]}
    reviews = {r["month"]: r for r in t["reviews"]}
    notes = []
    for m in range(t["term"]):
        if m in steps and current is not None:
            current = steps[m]
        if m in reviews and m > 0 and current is not None:
            r = reviews[m]
            if r["type"] == "fixed":
                new = current * (1 + r["increase"])
            elif r["type"] in ("index", "cpi", "rpi"):
                rise = (1 + r["assumed"]) ** r["compounded_years"] - 1
                lo = ((1 + r["collar"]) ** r["compounded_years"] - 1) if r["collar"] is not None else None
                hi = ((1 + r["cap"]) ** r["compounded_years"] - 1) if r["cap"] is not None else None
                if hi is not None:
                    rise = min(rise, hi)
                if lo is not None:
                    rise = max(rise, lo)
                new = current * (1 + rise)
            else:
                new = None
                notes.append(f"open-market review at month {m}: rent unknown from then; budget for an increase")
            if new is not None and r["upward_only"]:
                new = max(new, current)
            current = new
        rates.append(current)
    return rates, notes


def cost(t, rates, months):
    """Rent (after rent-free) and service charge payable in the first `months` months."""
    rent = 0.0
    unknown = False
    for m in range(min(months, t["term"])):
        if m < t["rent_free"]:
            continue
        if rates[m] is None:
            unknown = True
            continue
        rent += rates[m] / 12
    service = t["service"] * min(months, t["term"]) / 12
    if t["service_cap"] is not None:
        service = min(service, t["service_cap"] * min(months, t["term"]) / 12)
    return rent, service, unknown


def analyse(t, as_of):
    rates, notes = rent_by_month(t)
    end = add_months(t["start"], t["term"]) - dt.timedelta(days=1)   # a 5-year lease from 1 Jan ends on 31 Dec
    fails, warns, deadlines = [], [], []
    if t["rent_free"] >= t["term"]:
        fails.append("the rent-free period is as long as the term")
    if t["rent_free"]:
        deadlines.append(("rent starts", add_months(t["start"], t["rent_free"]), f"after {t['rent_free']} months rent-free"))
    for r in t["reviews"]:
        when = add_months(t["start"], r["month"])
        if r["month"] >= t["term"]:
            fails.append(f"a rent review at month {r['month']} falls after the lease ends")
        deadlines.append(("rent review", when, r["type"] + (", upward only" if r["upward_only"] else "")))
    commitments = []
    for b in t["breaks"]:
        bdate = b["date"] or add_months(t["start"], b["month"])
        notice_by = add_months(bdate, -b["notice"])
        if b["month"] >= t["term"]:
            fails.append(f"a break at month {b['month']} ({bdate}) is after the lease ends ({end})")
            continue
        if notice_by < t["start"]:
            fails.append(f"the break on {bdate} needs {b['notice']} months' notice, which runs back before the lease starts")
        deadlines.append((f"{b['party']} break notice", notice_by, f"for the break on {bdate}"
                          + (f"; conditions: {'; '.join(b['conditions'])}" if b["conditions"] else "")))
        rent, service, unknown = cost(t, rates, b["month"])
        penalty = (rates[b["month"] - 1] or 0) / 12 * b["penalty_months"] if b["penalty_months"] else 0
        commitments.append((f"to the break on {bdate}", rent + penalty, service, unknown, penalty))
        if b["party"].lower() in ("landlord", "mutual", "either"):
            warns.append(f"the landlord can end the lease on {bdate}; plan for having to move then")
        if b["conditions"]:
            warns.append(f"the break on {bdate} is conditional ({'; '.join(b['conditions'])}): one unmet condition, "
                         "such as a small unpaid sum, can make it fail")
    rent, service, unknown = cost(t, rates, t["term"])
    commitments.append((f"to the end of the term ({end})", rent, service, unknown, 0))
    if t["renewal"]:
        latest = add_months(end, -t["renewal"]["notice"])
        earliest = add_months(end, -t["renewal"]["earliest"])
        deadlines.append(("renewal option", latest, f"window opens {earliest}" if earliest < latest else "exact date"))
    if t["leave_notice"] is not None:
        deadlines.append(("notice to leave at the end", add_months(end, -t["leave_notice"]), f"for the end on {end}"))
    deadlines.sort(key=lambda d: d[1])
    for what, when, _ in deadlines:
        if as_of and when < as_of and what not in ("rent review", "rent starts"):
            fails.append(f"the {what} deadline ({when}) has already passed")
    years = []
    for y in range(math.ceil(t["term"] / 12)):
        ms = range(12 * y, min(12 * (y + 1), t["term"]))
        known = [rates[m] for m in ms if rates[m] is not None]
        paid = sum((rates[m] or 0) / 12 for m in ms if m >= t["rent_free"])
        years.append({"year": y + 1, "from": add_months(t["start"], 12 * y),
                      "rate": known[-1] if len(known) == len(ms) else None, "rent_paid": paid,
                      "unknown": len(known) < len(ms)})
    return {"end": end, "years": years, "commitments": commitments, "deadlines": deadlines,
            "notes": notes, "fails": fails, "warns": warns, "deposit": t["deposit"]}


def money(v, cur):
    sym = {"GBP": "£", "USD": "$", "EUR": "€", "INR": "₹", "AUD": "A$", "CAD": "C$"}.get(cur.upper(), "")
    return f"{sym}{v:,.0f}" if sym else f"{v:,.0f} {cur}"


def report(t, r):
    cur = t["currency"]
    L = ["# Lease: dates and money", "", f"Term: {t['start']} to {r['end']} ({t['term']} months).", "",
         "## Deadlines", "", "| Date | What | Detail |", "|---|---|---|"]
    for what, when, detail in r["deadlines"]:
        L.append(f"| {when} | {what} | {detail} |")
    L += ["", "## Committed cost", "", "| Up to | Rent | Service charge | Total |", "|---|---:|---:|---:|"]
    for label, rent, service, unknown, penalty in r["commitments"]:
        flag = " + unknown open-market rent" if unknown else ""
        pen = f" (incl. {money(penalty, cur)} break penalty)" if penalty else ""
        L.append(f"| {label} | {money(rent, cur)}{pen}{flag} | {money(service, cur)} | {money(rent + service, cur)}{flag} |")
    L += ["", "## Rent by year", "", "| Year | From | Yearly rent | Paid that year |", "|---:|---|---:|---:|"]
    for y in r["years"]:
        rate_s = money(y["rate"], cur) if y["rate"] is not None else "unknown (open market)"
        L.append(f"| {y['year']} | {y['from']} | {rate_s} | {money(y['rent_paid'], cur)}{' + unknown' if y['unknown'] else ''} |")
    if r["deposit"]:
        L += ["", f"Deposit: {money(r['deposit'], cur)}."]
    L += [""] + [f"NOTE {n}" for n in r["notes"]]
    L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="A lease's dates and money.")
    ap.add_argument("terms")
    ap.add_argument("--as-of", help="YYYY-MM-DD; deadlines before it are reported as passed")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        with open(args.terms, encoding="utf-8-sig") as f:
            t = load(json.load(f))
        as_of = day(args.as_of, "--as-of") if args.as_of else None
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"FAIL cannot read input: {e}")
        return 2
    except InputError as e:
        print(f"FAIL {e}")
        return 2
    r = analyse(t, as_of)
    print(json.dumps(r, indent=2, default=str) if args.json else report(t, r), end="" if not args.json else "\n")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Summarise a cloud cost export: totals, month-over-month change, untagged
share, top movers, cost hot spots and commitment coverage.

Stdlib only; runs on Python 3.9+. Reads one CSV in long format (one row per
line item): AWS CUR (legacy or 2.0), a flattened GCP billing export, an Azure
cost details export, or the generic layout. Column mapping: ../reference.md.

Usage:
  python3 cost_summary.py cost.csv [--format auto|aws-cur|aws-cur2|gcp|azure|generic]
      [--tag team --tag env] [--month 2026-09] [--top 10]
      [--out summary.md] [--json summary.json]

Exit codes: 0 ok, 2 bad input.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


class InputError(Exception):
    pass


# --------------------------------------------------------------- formats
# Each logical field lists candidate headers, matched case-insensitively.

FORMATS = {
    "aws-cur": {
        "detect": "lineitem/unblendedcost",
        "date": ["lineItem/UsageStartDate"],
        "cost": ["lineItem/UnblendedCost"],
        "service": ["product/ProductName", "lineItem/ProductCode"],
        "account": ["lineItem/UsageAccountId"],
        "region": ["product/region", "product/regionCode"],
        "usage_type": ["lineItem/UsageType"],
        "resource_id": ["lineItem/ResourceId"],
        "line_type": ["lineItem/LineItemType"],
        "sp_effective": ["savingsPlan/SavingsPlanEffectiveCost"],
        "ri_effective": ["reservation/EffectiveCost"],
        "tag_prefix": ["resourceTags/"],
        "tags_json": [],
    },
    "aws-cur2": {
        "detect": "line_item_unblended_cost",
        "date": ["line_item_usage_start_date"],
        "cost": ["line_item_unblended_cost"],
        "service": ["product_product_name", "line_item_product_code"],
        "account": ["line_item_usage_account_id"],
        "region": ["product_region_code", "product_region"],
        "usage_type": ["line_item_usage_type"],
        "resource_id": ["line_item_resource_id"],
        "line_type": ["line_item_line_item_type"],
        "sp_effective": ["savings_plan_savings_plan_effective_cost"],
        "ri_effective": ["reservation_effective_cost"],
        "tag_prefix": ["resource_tags_"],
        "tags_json": ["resource_tags"],
    },
    "gcp": {
        "detect": "usage_start_time",
        "date": ["usage_start_time"],
        "cost": ["cost"],
        "credits": ["credits_total", "credits"],
        "service": ["service_description", "service.description"],
        "account": ["project_id", "project.id"],
        "region": ["location_region", "location.region"],
        "usage_type": ["sku_description", "sku.description"],
        "resource_id": ["resource_global_name", "resource_name", "resource.name"],
        "line_type": ["cost_type"],
        "tag_prefix": ["label_", "labels_"],
        "tags_json": ["labels"],
    },
    "azure": {
        "detect": "metercategory",
        "date": ["date", "UsageDateTime"],
        "cost": ["costInBillingCurrency", "CostInBillingCurrency", "PreTaxCost", "Cost"],
        "service": ["meterCategory", "ServiceName"],
        "account": ["subscriptionName", "SubscriptionName", "subscriptionId", "SubscriptionGuid"],
        "region": ["resourceLocation", "ResourceLocation"],
        "usage_type": ["meterSubCategory", "MeterSubCategory"],
        "usage_type2": ["meterName", "MeterName"],
        "resource_id": ["resourceId", "ResourceId", "InstanceId"],
        "line_type": ["chargeType", "ChargeType"],
        "pricing": ["pricingModel", "PricingModel"],
        "tag_prefix": [],
        "tags_json": ["tags", "Tags"],
    },
    "generic": {
        "detect": None,
        "date": ["date"],
        "cost": ["cost"],
        "service": ["service"],
        "account": ["account"],
        "region": ["region"],
        "usage_type": ["usage_type"],
        "resource_id": ["resource_id"],
        "line_type": ["line_type"],
        "pricing": ["pricing_model"],
        "tag_prefix": ["tag_"],
        "tags_json": ["tags"],
    },
}

COMPUTE_RE = re.compile(r"BoxUsage|DedicatedUsage|HostUsage|Fargate-(vCPU|GB)-Hours|Lambda-GB-Second|InstanceUsage|NodeUsage|"
                        r"Instance Core|Instance Ram|vCPU", re.I)
GENERIC_COMPUTE_SERVICE_RE = re.compile(r"compute|virtual machine|\bvm\b|ec2|fargate|lambda|functions", re.I)
HOTSPOTS = [
    ("nat_gateway", re.compile(r"NatGateway|NAT Gateway|Cloud NAT", re.I)),
    ("data_transfer", re.compile(r"DataTransfer|Data Transfer|Egress|Bandwidth|Inter-?Region|InterZone|Inter Zone|"
                                 r"Network Internet|Networking", re.I)),
    ("idle_address", re.compile(r"IdleAddress|Unused IP|Static IP Charge", re.I)),
    ("snapshot", re.compile(r"Snapshot", re.I)),
    ("storage", re.compile(r"TimedStorage|VolumeUsage|Storage|Disk|Blob", re.I)),
    ("observability", re.compile(r"CloudWatch|Logging|Log Analytics|Azure Monitor|Cloud Monitoring|DataProcessing-Bytes", re.I)),
]


def detect_format(headers: list) -> str:
    low = [h.lower() for h in headers]
    for name, spec in FORMATS.items():
        if spec["detect"] and spec["detect"] in low:
            if name == "azure" and "usage_start_time" in low:
                continue
            return name
    if "date" in low and "cost" in low:
        return "generic"
    raise InputError("cannot recognise the export format from its header. Pass --format, or rename columns to "
                     "the generic layout (date, cost, service, ...). Header starts: %s" % ", ".join(headers[:8]))


def resolve(headers: list, spec: dict) -> dict:
    low = {h.lower(): h for h in headers}
    m = {}
    for field, cands in spec.items():
        if field in ("detect", "tag_prefix", "tags_json"):
            continue
        m[field] = next((low[c.lower()] for c in cands if c.lower() in low), None)
    m["tags_json"] = next((low[c.lower()] for c in spec["tags_json"] if c.lower() in low), None)
    m["tag_cols"] = {}
    for pre in spec["tag_prefix"]:
        for h in headers:
            if h.lower().startswith(pre.lower()) and h != m["tags_json"] and len(h) > len(pre):
                key = h[len(pre):]
                key = key[5:] if key.lower().startswith("user:") else key
                key = key[5:] if key.lower().startswith("user_") else key
                m["tag_cols"][key] = h
    for need in ("date", "cost"):
        if not m.get(need):
            raise InputError("no %s column found. Tried: %s" % (need, ", ".join(spec[need])))
    return m


# --------------------------------------------------------------- parsing

def num(raw, where):
    s = (raw or "").strip().replace(",", "")
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        raise InputError("%s: cost value %r is not a number" % (where, raw))


def day(raw, where):
    s = (raw or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s) or re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        raise InputError("%s: cannot read date %r (expected YYYY-MM-DD... or MM/DD/YYYY)" % (where, raw))
    try:
        if "/" in m.group(0):
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        raise InputError("%s: invalid date %r" % (where, raw))


def parse_tags(raw):
    s = (raw or "").strip()
    if not s:
        return {}
    for cand in (s, "{" + s + "}"):
        try:
            v = json.loads(cand)
        except ValueError:
            continue
        if isinstance(v, dict):
            return {str(k).replace("user:", ""): str(x) for k, x in v.items()}
        if isinstance(v, list):
            return {str(i.get("key")): str(i.get("value")) for i in v if isinstance(i, dict)}
    return {}


def credits_value(raw):
    s = (raw or "").strip()
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        pass
    try:
        v = json.loads(s)
        return sum(float(c.get("amount", 0)) for c in v) if isinstance(v, list) else 0.0
    except ValueError:
        return 0.0


def classify(fmt, r, m, where):
    """Return (kind, pricing, cost, od_equiv). kind: usage, commitment_fee, tax, credit, refund, skip."""
    g = lambda f: (r.get(m[f]) or "").strip() if m.get(f) else ""
    cost = num(r.get(m["cost"]), where)
    lt = g("line_type")
    ut = g("usage_type")
    ltl = lt.lower()
    if fmt in ("aws-cur", "aws-cur2"):
        if lt == "SavingsPlanNegation":
            return "skip", None, cost, 0.0
        if lt in ("SavingsPlanRecurringFee", "SavingsPlanUpfrontFee", "RIFee", "Fee"):
            return "commitment_fee", None, cost, 0.0
        if lt == "Tax":
            return "tax", None, cost, 0.0
        if lt in ("Credit", "BundledDiscount", "EdpDiscount", "PrivateRateDiscount", "SppDiscount", "Discount"):
            return "credit", None, cost, 0.0
        if lt == "Refund":
            return "refund", None, cost, 0.0
        if lt == "SavingsPlanCoveredUsage":
            eff = g("sp_effective")
            return "usage", "commitment", num(eff, where) if eff else cost, cost
        if lt == "DiscountedUsage":
            eff = g("ri_effective")
            return "usage", "commitment", num(eff, where) if eff else cost, cost
        return "usage", ("spot" if "SpotUsage" in ut else "on_demand"), cost, cost
    if fmt == "gcp":
        net = cost + (credits_value(r.get(m["credits"])) if m.get("credits") else 0.0)
        if ltl == "tax":
            return "tax", None, cost, 0.0
        if ut.lower().startswith("commitment"):
            return "commitment_fee", None, net, 0.0
        pr = "spot" if re.search(r"spot|preemptible", ut, re.I) else "unknown"
        return "usage", pr, net, net
    if fmt == "azure":
        pm = g("pricing").lower()
        if ltl == "purchase":
            return "commitment_fee", None, cost, 0.0
        if ltl == "refund":
            return "refund", None, cost, 0.0
        if ltl in ("tax",):
            return "tax", None, cost, 0.0
        if ltl.startswith("unused"):
            return "usage", "unused_commitment", cost, 0.0
        pr = {"ondemand": "on_demand", "reservation": "commitment", "savingsplan": "commitment",
              "spot": "spot"}.get(pm.replace(" ", ""), "unknown" if not pm else "on_demand")
        return "usage", pr, cost, cost
    # generic
    kind = ltl if ltl in ("usage", "commitment_fee", "tax", "credit", "refund") else "usage"
    pm = g("pricing").lower().replace("-", "_")
    pr = pm if pm in ("on_demand", "commitment", "spot", "unused_commitment") else "unknown"
    return kind, (pr if kind == "usage" else None), cost, cost


def load(path: Path, fmt_arg: str):
    if not path.exists():
        raise InputError("file not found: %s" % path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = [h.strip() for h in (reader.fieldnames or [])]
        if not headers:
            raise InputError("%s is empty or has no header row" % path)
        reader.fieldnames = headers
        fmt = detect_format(headers) if fmt_arg == "auto" else fmt_arg
        m = resolve(headers, FORMATS[fmt])
        rows = []
        for i, r in enumerate(reader, start=2):
            where = "line %d" % i
            kind, pricing, cost, od = classify(fmt, r, m, where)
            g = lambda f: (r.get(m[f]) or "").strip() if m.get(f) else ""
            ut = g("usage_type")
            if m.get("usage_type2") and g("usage_type2"):
                ut = (ut + " " + g("usage_type2")).strip()
            tags = parse_tags(r.get(m["tags_json"])) if m["tags_json"] else {}
            for k, col in m["tag_cols"].items():
                v = (r.get(col) or "").strip()
                if v:
                    tags[k] = v
            rows.append({"day": day(r.get(m["date"]), where), "kind": kind, "pricing": pricing, "cost": cost,
                         "od": od, "service": g("service") or "(none)", "account": g("account") or "(none)",
                         "region": g("region") or "(none)", "usage_type": ut or "(none)",
                         "resource": g("resource_id"), "tags": tags})
    if not rows:
        raise InputError("%s has a header but no rows" % path)
    used = {k: v for k, v in m.items() if v and k not in ("tag_cols",)}
    used["tag_columns"] = sorted(m["tag_cols"].values())
    return fmt, used, rows


# --------------------------------------------------------------- analysis

def mkey(d):
    return "%04d-%02d" % (d.year, d.month)


def r2(x):
    return round(x, 2)


def change(cur, prev, cur_days, prev_days, normalise):
    if normalise:
        cur_v, prev_v = cur / cur_days if cur_days else 0.0, prev / prev_days if prev_days else 0.0
    else:
        cur_v, prev_v = cur, prev
    delta = cur_v - prev_v
    pct = None if prev_v == 0 else delta / prev_v
    return delta, pct


def analyse(rows, tags_wanted, month_arg, top, fmt="generic"):
    months = sorted({mkey(r["day"]) for r in rows})
    cur_m = month_arg or months[-1]
    if cur_m not in months:
        raise InputError("--month %s not in the data (months present: %s)" % (cur_m, ", ".join(months)))
    idx = months.index(cur_m)
    prev_m = months[idx - 1] if idx > 0 else None
    notes = []
    days_seen = defaultdict(set)
    for r in rows:
        days_seen[mkey(r["day"])].add(r["day"])

    def coverage_of(m):
        y, mo = int(m[:4]), int(m[5:])
        n = monthrange(y, mo)[1]
        return len(days_seen[m]), n

    cur_days, cur_cal = coverage_of(cur_m)
    prev_days, prev_cal = coverage_of(prev_m) if prev_m else (0, 0)
    monthly_grain = all(len(v) == 1 for v in days_seen.values())
    partial = (not monthly_grain) and (cur_days < cur_cal or (prev_m is not None and prev_days < prev_cal))
    if monthly_grain:
        notes.append("Each month has a single date, so the export looks monthly. Totals are compared as they are; "
                     "the script cannot tell whether a month is complete.")
    if partial:
        notes.append("At least one month is partial (%s: %d of %d days%s). Month-over-month change is computed on "
                     "average daily spend, not totals." % (cur_m, cur_days, cur_cal,
                                                           "; %s: %d of %d days" % (prev_m, prev_days, prev_cal) if prev_m else ""))
    if prev_m is None:
        notes.append("No month before %s in the data, so there is no month-over-month change or movers list." % cur_m)
    elif (int(cur_m[:4]) * 12 + int(cur_m[5:])) - (int(prev_m[:4]) * 12 + int(prev_m[5:])) != 1:
        notes.append("The comparison month %s is not the calendar month before %s; a month is missing from the data." % (prev_m, cur_m))

    usage = [r for r in rows if r["kind"] == "usage"]
    in_m = lambda r, m: m is not None and mkey(r["day"]) == m

    def total(rs, m):
        return sum(r["cost"] for r in rs if in_m(r, m))

    # non-usage lines
    other = {}
    for kind in ("commitment_fee", "tax", "credit", "refund", "skip"):
        other[kind] = {"current": r2(total([r for r in rows if r["kind"] == kind], cur_m)),
                       "previous": r2(total([r for r in rows if r["kind"] == kind], prev_m)) if prev_m else None}

    cur_total, prev_total = total(usage, cur_m), total(usage, prev_m) if prev_m else 0.0
    d, p = change(cur_total, prev_total, cur_days, prev_days, partial) if prev_m else (None, None)
    headline = {"usage_cost_current": r2(cur_total), "usage_cost_previous": r2(prev_total) if prev_m else None,
                "change": r2(d) if d is not None else None, "change_pct": round(p, 4) if p is not None else None,
                "basis": "average daily spend (change columns are per day)" if partial else "monthly totals"}

    def group(keyf, rs=None):
        rs = usage if rs is None else rs
        acc = defaultdict(lambda: [0.0, 0.0])
        for r in rs:
            if in_m(r, cur_m):
                acc[keyf(r)][0] += r["cost"]
            elif in_m(r, prev_m):
                acc[keyf(r)][1] += r["cost"]
        out = []
        for k, (c, pv) in acc.items():
            dd, pp = change(c, pv, cur_days, prev_days, partial) if prev_m else (None, None)
            out.append({"key": k, "current": r2(c), "previous": r2(pv) if prev_m else None,
                        "change": r2(dd) if dd is not None else None,
                        "change_pct": round(pp, 4) if pp is not None else None,
                        "share_of_current": round(c / cur_total, 4) if cur_total else None,
                        "status": ("new" if prev_m and pv == 0 and c != 0 else "gone" if prev_m and c == 0 and pv != 0 else "")})
        return out

    by_service = sorted(group(lambda r: r["service"]), key=lambda x: -x["current"])
    by_account = sorted(group(lambda r: r["account"]), key=lambda x: -x["current"])
    by_region = sorted(group(lambda r: r["region"]), key=lambda x: -x["current"])
    lines = group(lambda r: "%s / %s" % (r["service"], r["usage_type"]))
    movers = sorted([x for x in lines if x["change"] is not None], key=lambda x: -abs(x["change"]))[:top] if prev_m else []
    res_rows = [r for r in usage if r["resource"]]
    top_resources = sorted(group(lambda r: "%s / %s / %s" % (r["resource"], r["service"], r["usage_type"]), res_rows),
                           key=lambda x: -x["current"])[:top]

    # tags
    tag_report = {}
    for t in tags_wanted:
        per = {}
        for m in [x for x in (prev_m, cur_m) if x]:
            tot = total(usage, m)
            un = sum(r["cost"] for r in usage if in_m(r, m) and not r["tags"].get(t))
            taggable = [r for r in usage if in_m(r, m) and r["resource"]]
            ttot = sum(r["cost"] for r in taggable)
            tun = sum(r["cost"] for r in taggable if not r["tags"].get(t))
            per[m] = {"untagged_cost": r2(un), "untagged_share": round(un / tot, 4) if tot else None,
                      "untagged_share_of_taggable": round(tun / ttot, 4) if ttot else None,
                      "spend_without_resource_id": r2(tot - ttot)}
        values = sorted(group(lambda r: r["tags"].get(t) or "(untagged)"), key=lambda x: -x["current"])
        untagged_svcs = sorted(group(lambda r: r["service"], [r for r in usage if not r["tags"].get(t)]),
                               key=lambda x: -x["current"])[:5]
        tag_report[t] = {"by_month": per, "by_value": values, "top_untagged_services": untagged_svcs}
    all_keys = sorted({k for r in usage for k in r["tags"]})
    if tags_wanted and not any(t in all_keys for t in tags_wanted):
        notes.append("None of the requested tag keys (%s) appear in the data. Tag keys found: %s."
                     % (", ".join(tags_wanted), ", ".join(all_keys) or "none"))

    # hot spots
    def category(r):
        for name, rx in HOTSPOTS:
            if rx.search(r["usage_type"]) or rx.search(r["service"]):
                return name
        return None

    hot = {}
    for name, _rx in HOTSPOTS:
        sel = [r for r in usage if category(r) == name]
        c, pv = total(sel, cur_m), total(sel, prev_m) if prev_m else 0.0
        top_lines = sorted(group(lambda r: "%s / %s / %s / %s" % (r["account"], r["region"], r["service"], r["usage_type"]), sel),
                           key=lambda x: -x["current"])[:5]
        hot[name] = {"current": r2(c), "previous": r2(pv) if prev_m else None,
                     "share_of_current": round(c / cur_total, 4) if cur_total else None, "top_lines": top_lines}

    # commitments
    comp = [r for r in usage if in_m(r, cur_m) and (COMPUTE_RE.search(r["usage_type"]) or r["service"] == "Virtual Machines"
                                                  or (fmt == "generic" and GENERIC_COMPUTE_SERVICE_RE.search(r["service"]))
                                                  or r["pricing"] == "commitment")]
    covered_od = sum(r["od"] for r in comp if r["pricing"] == "commitment")
    covered_eff = sum(r["cost"] for r in comp if r["pricing"] == "commitment")
    on_demand = sum(r["od"] for r in comp if r["pricing"] == "on_demand")
    spot = sum(r["cost"] for r in comp if r["pricing"] == "spot")
    unknown = sum(r["cost"] for r in comp if r["pricing"] == "unknown")
    unused = sum(r["cost"] for r in usage if in_m(r, cur_m) and r["pricing"] == "unused_commitment")
    od_by_svc = defaultdict(float)
    for r in comp:
        if r["pricing"] == "on_demand":
            od_by_svc[r["service"]] += r["od"]
    commit = {"compute_on_demand": r2(on_demand),
              "on_demand_by_service": {k: r2(v) for k, v in sorted(od_by_svc.items(), key=lambda kv: -kv[1])}, "compute_covered_on_demand_equivalent": r2(covered_od),
              "compute_covered_effective_cost": r2(covered_eff), "compute_spot": r2(spot),
              "compute_pricing_unknown": r2(unknown), "unused_commitment_lines": r2(unused),
              "coverage": round(covered_od / (covered_od + on_demand), 4) if (covered_od + on_demand) and not unknown else None,
              "commitment_fees": other["commitment_fee"]["current"]}
    fees = other["commitment_fee"]["current"]
    if fees and covered_eff:
        commit["utilisation_estimate"] = round(min(covered_eff / fees, 9.99), 4)
    if unknown and not (covered_od + on_demand):
        notes.append("Commitment coverage not computed: this export does not mark which compute usage is on demand "
                     "and which is covered. Use the provider's coverage report, or add a pricing_model column.")
    # steady on-demand floor
    daily = defaultdict(float)
    for r in comp:
        if r["pricing"] == "on_demand":
            daily[r["day"]] += r["od"]
    if cur_days >= 20 and daily:
        vals = sorted(daily.get(d, 0.0) for d in days_seen[cur_m])
        k = max(0, int(round(0.10 * (len(vals) - 1))))
        commit["daily_on_demand_compute_min"] = r2(vals[0])
        commit["daily_on_demand_compute_p10"] = r2(vals[k])
        commit["daily_on_demand_compute_median"] = r2(vals[len(vals) // 2])
        per = defaultdict(lambda: defaultdict(float))
        for r in comp:
            if r["pricing"] == "on_demand":
                per[r["service"]][r["day"]] += r["od"]
        commit["daily_on_demand_min_by_service"] = {
            k: r2(min(v.get(d, 0.0) for d in days_seen[cur_m])) for k, v in per.items()}
    elif daily and not monthly_grain:
        notes.append("The data is not daily (or the month has under 20 days), so no steady on-demand floor is computed.")

    neg = [r for r in usage if in_m(r, cur_m) and r["cost"] < 0]
    if neg:
        notes.append("%d usage line(s) in %s have negative cost; check for credits recorded as usage." % (len(neg), cur_m))

    return {"current_month": cur_m, "previous_month": prev_m, "months_in_data": months,
            "days_with_data": {cur_m: cur_days, **({prev_m: prev_days} if prev_m else {})},
            "headline": headline, "non_usage_lines": other, "by_service": by_service, "by_account": by_account,
            "by_region": by_region, "top_movers": movers, "top_resources": top_resources, "tags": tag_report,
            "tag_keys_in_data": all_keys, "hot_spots": hot, "commitments": commit, "notes": notes}


# --------------------------------------------------------------- render

def money(x):
    if x is None:
        return "n/a"
    return ("-$%s" if x < 0 else "$%s") % "{:,.2f}".format(abs(x))


def pc(x):
    return "n/a" if x is None else "%+.1f%%" % (x * 100)


def share(x):
    return "n/a" if x is None else "%.1f%%" % (x * 100)


CHANGE_LABEL = ["Change"]


def table(items, label, limit=None):
    out = ["| %s | Current | Previous | %s | Change %% | Share |" % (label, CHANGE_LABEL[0]), "|---|---:|---:|---:|---:|---:|"]
    for x in items[:limit] if limit else items:
        st = " (%s)" % x["status"] if x["status"] else ""
        out.append("| %s%s | %s | %s | %s | %s | %s |" % (str(x["key"]).replace("|", "\\|"), st, money(x["current"]), money(x["previous"]),
                                                          money(x["change"]), pc(x["change_pct"]), share(x["share_of_current"])))
    return out


def render(fmt, used, a, top):
    h = a["headline"]
    CHANGE_LABEL[0] = "Change per day" if h["basis"].startswith("average") else "Change"
    o = ["# Cloud cost summary: %s vs %s" % (a["current_month"], a["previous_month"] or "n/a"), ""]
    o.append("Format: %s. Days with data: %s. Change basis: %s. Amounts are usage line items at effective cost; "
             "tax, credits, refunds and commitment fees are listed separately." %
             (fmt, ", ".join("%s=%d" % kv for kv in a["days_with_data"].items()), h["basis"]))
    o.append("")
    o.append("| | %s | %s | %s |" % (a["current_month"], a["previous_month"] or "previous", CHANGE_LABEL[0]))
    o.append("|---|---:|---:|---:|")
    o.append("| Usage cost | %s | %s | %s (%s) |" % (money(h["usage_cost_current"]), money(h["usage_cost_previous"]),
                                                    money(h["change"]), pc(h["change_pct"])))
    for k, lab in (("commitment_fee", "Commitment fees"), ("tax", "Tax"), ("credit", "Credits and discounts"),
                   ("refund", "Refunds"), ("skip", "Excluded (savings plan negation)")):
        v = a["non_usage_lines"][k]
        if v["current"] or v["previous"]:
            o.append("| %s | %s | %s | |" % (lab, money(v["current"]), money(v["previous"])))
    o += ["", "## By service", ""] + table(a["by_service"], "Service", top)
    o += ["", "## By account / project / subscription", ""] + table(a["by_account"], "Account", top)
    o += ["", "## By region", ""] + table(a["by_region"], "Region", top)
    if a["top_movers"]:
        o += ["", "## Top movers (service / usage type)", ""] + table(a["top_movers"], "Line")
    o += ["", "## Top resources by current cost", ""] + table(a["top_resources"], "Resource / service / usage type")
    for t, rep in a["tags"].items():
        o += ["", "## Tag `%s`" % t, ""]
        o.append("| Month | Untagged cost | Untagged share | Untagged share of spend with a resource id | Spend with no resource id |")
        o.append("|---|---:|---:|---:|---:|")
        for m, v in rep["by_month"].items():
            o.append("| %s | %s | %s | %s | %s |" % (m, money(v["untagged_cost"]), share(v["untagged_share"]),
                                                  share(v["untagged_share_of_taggable"]), money(v["spend_without_resource_id"])))
        o += [""] + table(rep["by_value"], "Value of %s" % t, top)
        o += ["", "Top services with no `%s` tag:" % t, ""] + table(rep["top_untagged_services"], "Service")
    o += ["", "## Hot spots", "", "| Category | Current | Previous | Share of usage |", "|---|---:|---:|---:|"]
    for name, v in a["hot_spots"].items():
        o.append("| %s | %s | %s | %s |" % (name.replace("_", " "), money(v["current"]), money(v["previous"]), share(v["share_of_current"])))
    for name, v in a["hot_spots"].items():
        if v["current"] > 0 and v["top_lines"]:
            o += ["", "Top %s lines (account / region / service / usage type):" % name.replace("_", " "), ""]
            o += table(v["top_lines"], "Line")
    c = a["commitments"]
    o += ["", "## Commitments (%s, compute usage)" % a["current_month"], "", "| Measure | Value |", "|---|---:|"]
    for k in ("compute_on_demand", "compute_covered_on_demand_equivalent", "compute_covered_effective_cost",
              "compute_spot", "compute_pricing_unknown", "commitment_fees", "unused_commitment_lines"):
        o.append("| %s | %s |" % (k.replace("_", " "), money(c[k])))
    for svc_name, v in c["on_demand_by_service"].items():
        o.append("| on demand: %s | %s |" % (svc_name, money(v)))
    o.append("| coverage (covered / covered + on demand, on-demand-equivalent basis) | %s |" % share(c["coverage"]))
    if "utilisation_estimate" in c:
        o.append("| utilisation estimate (covered effective cost / commitment fees) | %s |" % share(c["utilisation_estimate"]))
    for k in ("daily_on_demand_compute_min", "daily_on_demand_compute_p10", "daily_on_demand_compute_median"):
        if k in c:
            o.append("| %s | %s |" % (k.replace("_", " "), money(c[k])))
    for svc_name, v in c.get("daily_on_demand_min_by_service", {}).items():
        o.append("| daily on demand min: %s | %s |" % (svc_name, money(v)))
    o += ["", "## Column mapping used", ""]
    for k, v in used.items():
        o.append("- %s: %s" % (k, ", ".join(v) if isinstance(v, list) else v))
    if a["tag_keys_in_data"]:
        o.append("- tag keys found: %s" % ", ".join(a["tag_keys_in_data"]))
    if a["notes"]:
        o += ["", "## Notes", ""] + ["- " + n for n in a["notes"]]
    return "\n".join(o) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarise a cloud cost export CSV.")
    ap.add_argument("csv")
    ap.add_argument("--format", default="auto", choices=["auto"] + list(FORMATS))
    ap.add_argument("--tag", action="append", default=[], help="tag/label key to report untagged share for (repeatable)")
    ap.add_argument("--month", help="month to analyse, YYYY-MM (default: latest in data)")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    try:
        if args.month and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
            raise InputError("--month must be YYYY-MM, got %r" % args.month)
        if args.top < 1:
            raise InputError("--top must be at least 1")
        fmt, used, rows = load(Path(args.csv), args.format)
        a = analyse(rows, args.tag, args.month, args.top, fmt)
    except InputError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    report = render(fmt, used, a, args.top)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
        print("wrote %s" % args.out, file=sys.stderr)
    else:
        sys.stdout.write(report)
    if args.json:
        payload = json.dumps({"format": fmt, "columns": used, **a}, indent=2, default=str)
        if args.json == "-":
            print(payload)
        else:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(payload + "\n", encoding="utf-8")
            print("wrote %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

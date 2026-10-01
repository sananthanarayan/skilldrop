#!/usr/bin/env python3
"""Compute DORA software delivery metrics and flow metrics from CSV exports.

Stdlib only; runs on Python 3.9+.

Inputs (CSV, header row required):
  --deployments  one row per production deployment             (required)
  --incidents    one row per production incident               (optional)
  --prs          one row per pull request / work item          (optional)

Column contracts live in ../reference.md. Every timestamp must carry a UTC
offset ("Z" or "+01:00"). A timestamp without one is an error unless you pass
--assume-tz, and every row that needed it is counted in the report.

Usage:
  python3 delivery_metrics.py --deployments deploys.csv \
      [--incidents incidents.csv] [--prs prs.csv] \
      [--service checkout-api] [--from 2026-07-06 --to 2026-08-30] \
      [--assume-tz +00:00] [--out report.md] [--json metrics.json]

Exit codes: 0 ok, 2 bad input (missing file, missing column, bad value).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FAILED_STATUSES = {"failed", "rolled_back", "rollback", "rolledback", "hotfixed"}
TRUE_VALUES = {"1", "true", "yes", "y", "t"}
FALSE_VALUES = {"0", "false", "no", "n", "f", ""}
LOW_N = 10  # below this many observations a percentile is reported but flagged


class InputError(Exception):
    pass


# ---------------------------------------------------------------- parsing

def parse_offset(text: str) -> timezone:
    m = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", text.strip())
    if text.strip().upper() in ("Z", "UTC"):
        return timezone.utc
    if not m:
        raise InputError("--assume-tz must look like +00:00, -05:00 or Z, got %r" % text)
    sign = 1 if m.group(1) == "+" else -1
    return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))


class Clock:
    """Parses timestamps and counts the ones that needed an assumed zone."""

    def __init__(self, assume_tz):
        self.assume_tz = assume_tz
        self.assumed = 0

    def parse(self, raw, where: str):
        if raw is None or not str(raw).strip():
            return None
        s = str(raw).strip()
        if s.endswith("Z") or s.endswith("z"):
            s = s[:-1] + "+00:00"
        s = s.replace(" ", "T", 1) if re.match(r"\d{4}-\d{2}-\d{2} \d", s) else s
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            raise InputError("%s: cannot parse timestamp %r (use ISO 8601, e.g. 2026-07-06T14:03:00Z)" % (where, raw))
        if dt.tzinfo is None:
            if self.assume_tz is None:
                raise InputError(
                    "%s: timestamp %r has no UTC offset. Add one to the export, or rerun with "
                    "--assume-tz <offset> if you know the zone the tool wrote it in." % (where, raw))
            self.assumed += 1
            dt = dt.replace(tzinfo=self.assume_tz)
        return dt.astimezone(timezone.utc)


def parse_bool(raw, where: str):
    s = (raw or "").strip().lower()
    if s in TRUE_VALUES:
        return True
    if s in FALSE_VALUES:
        return False
    raise InputError("%s: expected true/false, got %r" % (where, raw))


def read_csv(path: Path, required: list, label: str) -> list:
    if not path.exists():
        raise InputError("%s file not found: %s" % (label, path))
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise InputError("%s file %s is empty or has no header row" % (label, path))
        headers = [h.strip() for h in reader.fieldnames]
        missing = [c for c in required if c not in headers]
        if missing:
            raise InputError("%s file %s is missing required column(s): %s. Found: %s"
                             % (label, path, ", ".join(missing), ", ".join(headers)))
        rows = []
        for row in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
        return rows


# ---------------------------------------------------------------- math

def percentile(values: list, p: float):
    """Linear interpolation between closest ranks (same as numpy's default)."""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return xs[int(k)]
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def dist(hours: list) -> dict:
    return {
        "n": len(hours),
        "p50_hours": rnd(percentile(hours, 50)),
        "p85_hours": rnd(percentile(hours, 85)),
        "p95_hours": rnd(percentile(hours, 95)),
        "low_n": len(hours) < LOW_N,
    }


def rnd(x, nd=2):
    return None if x is None else round(x, nd)


def hours_between(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600.0


def week_start(d: datetime) -> date:
    day = d.date()
    return day - timedelta(days=day.weekday())


def weeks_in(start: date, end: date) -> list:
    out, w = [], start - timedelta(days=start.weekday())
    while w <= end:
        out.append(w)
        w += timedelta(days=7)
    return out


def fmt_h(h):
    if h is None:
        return "n/a"
    if h < 1:
        return "%d min" % round(h * 60)
    if h < 48:
        return "%.1f h" % h
    return "%.1f d" % (h / 24.0)


def pct(x):
    return "n/a" if x is None else "%.1f%%" % (x * 100)


# ---------------------------------------------------------------- core

def compute(args) -> dict:
    clock = Clock(parse_offset(args.assume_tz) if args.assume_tz else None)
    notes, quality = [], {}

    dep_rows = read_csv(Path(args.deployments), ["deploy_id", "service", "deployed_at", "status"], "deployments")
    inc_rows = read_csv(Path(args.incidents), ["incident_id", "service", "started_at", "resolved_at"], "incidents") if args.incidents else None
    pr_rows = read_csv(Path(args.prs), ["pr_id", "opened_at", "merged_at"], "prs") if args.prs else None

    services_seen = sorted({r["service"] for r in dep_rows if r["service"]})
    svc = args.service

    # ---- deployments
    deploys, skipped_no_ts, non_prod = [], 0, 0
    for i, r in enumerate(dep_rows, start=2):
        where = "deployments line %d" % i
        if svc and r["service"] != svc:
            continue
        env = r.get("environment", "").lower()
        if env and env not in ("production", "prod"):
            non_prod += 1
            continue
        ts = clock.parse(r["deployed_at"], where)
        if ts is None:
            skipped_no_ts += 1
            continue
        status = r["status"].lower()
        if status not in FAILED_STATUSES and status not in ("success", "succeeded", "ok"):
            raise InputError("%s: unknown status %r (use success, failed, rolled_back or hotfixed)" % (where, r["status"]))
        deploys.append({
            "id": r["deploy_id"],
            "service": r["service"],
            "at": ts,
            "failed": status in FAILED_STATUSES,
            "first_commit_at": clock.parse(r.get("first_commit_at"), where) if "first_commit_at" in r else None,
            "recovered_at": clock.parse(r.get("recovered_at"), where) if "recovered_at" in r else None,
            "unplanned": parse_bool(r.get("unplanned"), where) if "unplanned" in r else None,
            "has_unplanned_col": "unplanned" in r,
        })
    quality["deploy_rows_read"] = len(dep_rows)
    quality["deploy_rows_skipped_missing_deployed_at"] = skipped_no_ts
    quality["deploy_rows_skipped_non_production"] = non_prod
    if not deploys:
        raise InputError("no production deployments left after filtering%s" % (" for service %r" % svc if svc else ""))

    # ---- window
    first = min(d["at"] for d in deploys).date()
    last = max(d["at"] for d in deploys).date()
    start = date.fromisoformat(args.date_from) if args.date_from else first
    end = date.fromisoformat(args.date_to) if args.date_to else last
    if end < start:
        raise InputError("--to (%s) is before --from (%s)" % (end, start))
    in_win = lambda dt: dt is not None and start <= dt.date() <= end
    deploys = [d for d in deploys if in_win(d["at"])]
    if not deploys:
        raise InputError("no deployments fall inside %s .. %s" % (start, end))
    days = (end - start).days + 1
    weeks = weeks_in(start, end)
    if days < 28:
        notes.append("The window is %d days. Per-week rates from under four weeks are not a trend; "
                     "read them as a snapshot." % days)
    if start.weekday() != 0 or end.weekday() != 6:
        notes.append("The window does not start on a Monday and end on a Sunday, so the first and/or last "
                     "week in the weekly series is partial. Read their counts as lower bounds.")

    by_id = {d["id"]: d for d in deploys}

    # ---- incidents
    incidents, open_inc, inc_no_start = [], 0, 0
    if inc_rows is not None:
        for i, r in enumerate(inc_rows, start=2):
            where = "incidents line %d" % i
            if svc and r["service"] != svc:
                continue
            st = clock.parse(r["started_at"], where)
            if st is None:
                inc_no_start += 1
                continue
            rs = clock.parse(r["resolved_at"], where)
            if rs is not None and rs < st:
                raise InputError("%s: resolved_at is before started_at" % where)
            if rs is None:
                open_inc += 1
            incidents.append({"id": r["incident_id"], "start": st, "end": rs,
                              "deploy": r.get("caused_by_deploy", ""), "severity": r.get("severity", "")})
        incidents = [x for x in incidents if in_win(x["start"])]
        quality["incident_rows_read"] = len(inc_rows)
        quality["incidents_unresolved_excluded_from_restore_time"] = open_inc
        quality["incident_rows_skipped_missing_started_at"] = inc_no_start

    # incidents linked to a deployment mark that deployment failed
    linked = {}
    for x in incidents:
        if x["deploy"]:
            if x["deploy"] in by_id:
                by_id[x["deploy"]]["failed"] = True
                linked.setdefault(x["deploy"], []).append(x)
            else:
                notes.append("Incident %s names deployment %s, which is not in the window or the deployments file."
                             % (x["id"], x["deploy"]))

    # ---- deployment frequency
    n = len(deploys)
    per_week = {w.isoformat(): 0 for w in weeks}
    for d in deploys:
        per_week[week_start(d["at"]).isoformat()] = per_week.get(week_start(d["at"]).isoformat(), 0) + 1
    deploy_days = len({d["at"].date() for d in deploys})
    gaps = [hours_between(a["at"], b["at"]) for a, b in zip(sorted(deploys, key=lambda d: d["at"]),
                                                         sorted(deploys, key=lambda d: d["at"])[1:])]
    freq = {
        "deployments": n,
        "days_in_window": days,
        "per_day": rnd(n / days, 3),
        "per_week_mean": rnd(n / (days / 7.0), 2),
        "days_with_a_deployment": deploy_days,
        "share_of_days_with_a_deployment": rnd(deploy_days / days, 3),
        "median_hours_between_deployments": rnd(percentile(gaps, 50)),
        "weekly": per_week,
    }

    # ---- change fail rate
    failed = [d for d in deploys if d["failed"]]
    fail_week = {w.isoformat(): [0, 0] for w in weeks}
    for d in deploys:
        k = week_start(d["at"]).isoformat()
        fail_week.setdefault(k, [0, 0])
        fail_week[k][1] += 1
        if d["failed"]:
            fail_week[k][0] += 1
    cfr = {
        "failed_deployments": len(failed),
        "deployments": n,
        "rate": rnd(len(failed) / n, 4),
        "weekly": {k: {"failed": v[0], "deployments": v[1], "rate": rnd(v[0] / v[1], 4) if v[1] else None}
                   for k, v in fail_week.items()},
        "failure_signal": "status in (failed, rolled_back, hotfixed) or named by an incident's caused_by_deploy",
    }

    # ---- failed deployment recovery time
    rec_hours, no_recovery = [], []
    for d in failed:
        end_ts = d["recovered_at"]
        if end_ts is None and d["id"] in linked:
            ends = [x["end"] for x in linked[d["id"]]]
            end_ts = max(ends) if all(e is not None for e in ends) else None
        if end_ts is None:
            no_recovery.append(d["id"])
            continue
        if end_ts < d["at"]:
            raise InputError("deployment %s recovered before it was deployed" % d["id"])
        rec_hours.append(hours_between(d["at"], end_ts))
    fdrt = dist(rec_hours)
    fdrt["measured_from"] = "deployed_at of the failed deployment"
    fdrt["measured_to"] = "recovered_at on the deployment, else resolved_at of the linked incident(s)"
    fdrt["failed_deployments_without_recovery_time"] = no_recovery

    # ---- time to restore service (all incidents, the pre-2023 framing)
    ttr = None
    if inc_rows is not None:
        ttr = dist([hours_between(x["start"], x["end"]) for x in incidents if x["end"] is not None])
        ttr["incidents_in_window"] = len(incidents)
        ttr["not_caused_by_a_deployment"] = len([x for x in incidents if not x["deploy"]])

    # ---- lead time for changes
    lead, lead_source = [], None
    if pr_rows is not None and "deploy_id" in pr_rows[0] and "first_commit_at" in pr_rows[0]:
        lead_source = "prs.first_commit_at -> deployed_at of prs.deploy_id"
        unlinked = 0
        for i, r in enumerate(pr_rows, start=2):
            if svc and r.get("service") and r["service"] != svc:
                continue
            fc = clock.parse(r.get("first_commit_at"), "prs line %d" % i)
            dep = by_id.get(r.get("deploy_id", ""))
            if fc is None or dep is None:
                unlinked += 1
                continue
            if dep["at"] < fc:
                raise InputError("prs line %d: deployed before its first commit" % i)
            lead.append(hours_between(fc, dep["at"]))
        quality["prs_without_a_deploy_in_window_or_first_commit"] = unlinked
    elif any(d["first_commit_at"] for d in deploys):
        lead_source = "deployments.first_commit_at -> deployed_at"
        for d in deploys:
            if d["first_commit_at"] is not None:
                lead.append(hours_between(d["first_commit_at"], d["at"]))
        quality["deployments_missing_first_commit_at"] = len([d for d in deploys if d["first_commit_at"] is None])
    lt = dist(lead) if lead_source else None
    if lt is not None:
        lt["source"] = lead_source
    else:
        notes.append("Lead time for changes not computed: give either prs.first_commit_at + prs.deploy_id, "
                     "or deployments.first_commit_at.")

    # ---- deployment rework rate (optional)
    rework = None
    if deploys[0]["has_unplanned_col"]:
        unpl = len([d for d in deploys if d["unplanned"]])
        rework = {"unplanned_deployments": unpl, "deployments": n, "rate": rnd(unpl / n, 4)}

    # ---- flow metrics from PRs
    flow = None
    if pr_rows is not None:
        items, start_field = [], None
        for i, r in enumerate(pr_rows, start=2):
            where = "prs line %d" % i
            if svc and r.get("service") and r["service"] != svc:
                continue
            opened = clock.parse(r["opened_at"], where)
            if opened is None:
                raise InputError("%s: opened_at is empty" % where)
            fc = clock.parse(r.get("first_commit_at"), where) if "first_commit_at" in r else None
            begun = fc if fc is not None and fc <= opened else opened
            merged = clock.parse(r["merged_at"], where)
            closed = clock.parse(r.get("closed_at"), where) if "closed_at" in r else None
            done = merged or closed
            if done is not None and done < begun:
                raise InputError("%s: merged/closed before it was started" % where)
            items.append({"begun": begun, "merged": merged, "done": done})
        start_field = "earlier of first_commit_at and opened_at" if "first_commit_at" in pr_rows[0] else "opened_at"
        merged_in = [x for x in items if x["merged"] is not None and in_win(x["merged"])]
        thr = {w.isoformat(): 0 for w in weeks}
        for x in merged_in:
            k = week_start(x["merged"]).isoformat()
            thr[k] = thr.get(k, 0) + 1
        wip = {}
        for w in weeks:
            snap = datetime.combine(min(w + timedelta(days=7), end + timedelta(days=1)),
                                    datetime.min.time(), tzinfo=timezone.utc)
            wip[w.isoformat()] = len([x for x in items if x["begun"] < snap and (x["done"] is None or x["done"] >= snap)])
        cyc = dist([hours_between(x["begun"], x["merged"]) for x in merged_in])
        cyc["measured_from"] = start_field
        cyc["measured_to"] = "merged_at"
        flow = {
            "cycle_time": cyc,
            "throughput_merged_per_week": thr,
            "throughput_mean_per_week": rnd(len(merged_in) / (days / 7.0), 2),
            "wip_at_week_end": wip,
            "abandoned_in_window": len([x for x in items if x["merged"] is None and x["done"] is not None and in_win(x["done"])]),
        }

    if not svc and len(services_seen) > 1:
        notes.append("Aggregated across %d services (%s). DORA metrics are meant per application or service; "
                     "rerun with --service for each." % (len(services_seen), ", ".join(services_seen)))
    if clock.assumed:
        notes.append("%d timestamp(s) had no UTC offset and were read as %s (--assume-tz)." % (clock.assumed, args.assume_tz))
    quality["timestamps_with_assumed_offset"] = clock.assumed

    return {
        "generated_for": {"service": svc or "all", "services_in_file": services_seen,
                          "from": start.isoformat(), "to": end.isoformat(),
                          "week_basis": "ISO weeks starting Monday, UTC"},
        "dora": {
            "deployment_frequency": freq,
            "lead_time_for_changes": lt,
            "change_fail_rate": cfr,
            "failed_deployment_recovery_time": fdrt,
            "deployment_rework_rate": rework,
        },
        "time_to_restore_service_all_incidents": ttr,
        "flow": flow,
        "data_quality": quality,
        "notes": notes,
    }


# ---------------------------------------------------------------- report

def dist_row(name, d, extra=""):
    if d is None:
        return "| %s | not computed | | | | %s |" % (name, extra)
    flag = " (low n)" if d["low_n"] else ""
    return "| %s | %d%s | %s | %s | %s | %s |" % (
        name, d["n"], flag, fmt_h(d["p50_hours"]), fmt_h(d["p85_hours"]), fmt_h(d["p95_hours"]), extra)


def render(m: dict) -> str:
    g, dora = m["generated_for"], m["dora"]
    f, c = dora["deployment_frequency"], dora["change_fail_rate"]
    out = []
    out.append("# Delivery metrics: %s" % g["service"])
    out.append("")
    out.append("Window: %s to %s (%d days). Weeks: %s." % (g["from"], g["to"], f["days_in_window"], g["week_basis"]))
    out.append("")
    out.append("## DORA software delivery metrics")
    out.append("")
    out.append("| Metric | Value |")
    out.append("|---|---|")
    out.append("| Deployment frequency | %d deployments; %.2f per week; deployed on %d of %d days (%s) |"
               % (f["deployments"], f["per_week_mean"], f["days_with_a_deployment"], f["days_in_window"],
                  pct(f["share_of_days_with_a_deployment"])))
    out.append("| Change fail rate | %d of %d deployments (%s) |" % (c["failed_deployments"], c["deployments"], pct(c["rate"])))
    rw = dora["deployment_rework_rate"]
    out.append("| Deployment rework rate | %s |" % ("%d of %d deployments (%s)" % (rw["unplanned_deployments"], rw["deployments"], pct(rw["rate"])) if rw else "not computed (no `unplanned` column)"))
    out.append("")
    out.append("| Duration metric | n | p50 | p85 | p95 | Measured |")
    out.append("|---|---|---|---|---|---|")
    lt = dora["lead_time_for_changes"]
    out.append(dist_row("Lead time for changes", lt, lt["source"] if lt else "needs first_commit_at"))
    fd = dora["failed_deployment_recovery_time"]
    out.append(dist_row("Failed deployment recovery time", fd, "failed deploy -> recovered"))
    ttr = m["time_to_restore_service_all_incidents"]
    out.append(dist_row("Time to restore service (all incidents)", ttr, "incident start -> resolved" if ttr else "no incidents file"))
    out.append("")
    if fd["failed_deployments_without_recovery_time"]:
        out.append("Failed deployments with no recovery time recorded: %s." % ", ".join(fd["failed_deployments_without_recovery_time"]))
        out.append("")
    out.append("## Weekly series")
    out.append("")
    flow = m["flow"]
    head = "| Week of | Deploys | Failed | Fail rate |"
    sep = "|---|---|---|---|"
    if flow:
        head += " Merged | WIP at week end |"
        sep += "---|---|"
    out.append(head)
    out.append(sep)
    for wk, cnt in f["weekly"].items():
        cw = c["weekly"].get(wk, {"failed": 0, "rate": None})
        row = "| %s | %d | %d | %s |" % (wk, cnt, cw["failed"], pct(cw["rate"]))
        if flow:
            row += " %d | %d |" % (flow["throughput_merged_per_week"].get(wk, 0), flow["wip_at_week_end"].get(wk, 0))
        out.append(row)
    out.append("")
    if flow:
        cy = flow["cycle_time"]
        out.append("## Flow")
        out.append("")
        out.append("| Measure | Value |")
        out.append("|---|---|")
        out.append("| Cycle time p50 / p85 | %s / %s (n=%d%s; %s -> merged) |" % (
            fmt_h(cy["p50_hours"]), fmt_h(cy["p85_hours"]), cy["n"], ", low n" if cy["low_n"] else "", cy["measured_from"]))
        out.append("| Throughput | %.2f merged per week |" % flow["throughput_mean_per_week"])
        out.append("| Abandoned (closed unmerged) in window | %d |" % flow["abandoned_in_window"])
        out.append("")
    out.append("## Data quality")
    out.append("")
    for k, v in m["data_quality"].items():
        out.append("- %s: %s" % (k.replace("_", " "), v))
    if m["notes"]:
        out.append("")
        out.append("## Notes")
        out.append("")
        for n in m["notes"]:
            out.append("- " + n)
    out.append("")
    out.append("Percentiles use linear interpolation between ranks. \"low n\" means fewer than %d observations." % LOW_N)
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DORA + flow metrics from deployment, incident and PR CSV exports.")
    ap.add_argument("--deployments", required=True)
    ap.add_argument("--incidents")
    ap.add_argument("--prs")
    ap.add_argument("--service", help="only rows for this service")
    ap.add_argument("--from", dest="date_from", help="window start, YYYY-MM-DD (UTC, inclusive)")
    ap.add_argument("--to", dest="date_to", help="window end, YYYY-MM-DD (UTC, inclusive)")
    ap.add_argument("--assume-tz", help="offset for timestamps that lack one, e.g. +00:00")
    ap.add_argument("--out", help="write the markdown report here (default: stdout)")
    ap.add_argument("--json", help="write the metrics JSON here ('-' for stdout after the report)")
    args = ap.parse_args(argv)
    try:
        for flag in ("date_from", "date_to"):
            v = getattr(args, flag)
            if v:
                try:
                    date.fromisoformat(v)
                except ValueError:
                    raise InputError("--%s must be YYYY-MM-DD, got %r" % (flag.replace("date_", ""), v))
        m = compute(args)
    except InputError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    report = render(m)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
        print("wrote %s" % args.out, file=sys.stderr)
    else:
        sys.stdout.write(report)
    if args.json:
        payload = json.dumps(m, indent=2)
        if args.json == "-":
            print(payload)
        else:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(payload + "\n", encoding="utf-8")
            print("wrote %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

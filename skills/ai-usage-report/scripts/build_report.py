#!/usr/bin/env python3
"""Build an AI usage report from a usage-event log.

Reads a CSV or JSONL file of usage events and writes a markdown report.
See ../templates/usage-event-schema.md for the input schema.

Usage:
    python3 build_report.py events.csv --view per-user --period week -o report.md
    python3 build_report.py events.jsonl --view team-rollup --from 2026-05-01 --to 2026-05-31 -o report.md
    python3 build_report.py events.csv --view effectiveness --period week -o report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

VIEWS = ("per-user", "team-rollup", "effectiveness")
MIN_USERS_FOR_ROLLUP = 5


def load_events(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    if suffix in (".jsonl", ".ndjson"):
        events = []
        with path.open() as f:
            for line in f:
                s = line.strip()
                if s:
                    events.append(json.loads(s))
        return events
    raise SystemExit(f"error: unsupported file type {suffix!r} (use .csv or .jsonl)")


def parse_ts(s) -> datetime | None:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = str(s).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Try date-only
        try:
            dt = datetime.fromisoformat(s + "T00:00:00+00:00")
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_bool(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "t"):
        return True
    if s in ("0", "false", "no", "n", "f"):
        return False
    return None


def resolve_period(period: str, from_arg: str | None, to_arg: str | None):
    if from_arg or to_arg:
        if not (from_arg and to_arg):
            raise SystemExit("error: --from and --to must be used together")
        start = parse_ts(from_arg)
        end = parse_ts(to_arg)
        if start is None or end is None:
            raise SystemExit(f"error: could not parse --from / --to dates")
        # If user passed date-only for --to, push to end of day
        if len(to_arg) <= 10:
            end = end + timedelta(days=1, seconds=-1)
        return start, end
    now = datetime.now(timezone.utc)
    if period == "week":
        return now - timedelta(days=7), now
    if period == "month":
        return now - timedelta(days=30), now
    raise SystemExit(f"error: unknown --period {period!r} (use week, month, or --from/--to)")


def detect_signals(events: list[dict]) -> dict:
    """Which optional fields are populated in the input."""
    keys_present = set()
    for e in events[:1000]:  # sample
        for k, v in e.items():
            if v not in (None, ""):
                keys_present.add(k)
    return {
        "session_id": "session_id" in keys_present,
        "output_consumed": "output_consumed" in keys_present,
        "consumed_at": "consumed_at" in keys_present,
        "outcome": "outcome" in keys_present,
    }


def filter_to_period(events: list[dict], start: datetime, end: datetime) -> list[dict]:
    out = []
    for e in events:
        ts = parse_ts(e.get("timestamp"))
        if ts and start <= ts <= end:
            out.append({**e, "_ts": ts})
    return out


def aggregate(events: list[dict], signals: dict):
    per_user = defaultdict(lambda: {
        "invocations": 0,
        "sessions": set(),
        "tools": set(),
        "session_counts": defaultdict(int),
        "consumed_known": 0,
        "consumed_yes": 0,
    })
    tool_counter: Counter = Counter()

    for e in events:
        u = e.get("user")
        if not u:
            continue
        d = per_user[u]
        d["invocations"] += 1
        tool = e.get("tool") or "(unknown)"
        d["tools"].add(tool)
        tool_counter[tool] += 1

        if signals["session_id"]:
            sid = e.get("session_id")
            if sid:
                d["sessions"].add(sid)
                d["session_counts"][sid] += 1

        if signals["output_consumed"]:
            b = parse_bool(e.get("output_consumed"))
            if b is not None:
                d["consumed_known"] += 1
                if b:
                    d["consumed_yes"] += 1

    return per_user, tool_counter


def fmt_pct(num, denom) -> str:
    if not denom:
        return "—"
    return f"{100 * num / denom:.0f}%"


def per_user_metrics(d: dict, signals: dict) -> dict:
    n_sessions = len(d["sessions"]) if signals["session_id"] else None
    avg_per_session = (d["invocations"] / n_sessions) if n_sessions else None
    single_shot = sum(1 for c in d["session_counts"].values() if c == 1) if n_sessions else None
    eff_rate_pct = (
        100 * d["consumed_yes"] / d["consumed_known"]
        if signals["output_consumed"] and d["consumed_known"]
        else None
    )
    single_rate_pct = (100 * single_shot / n_sessions) if (n_sessions and single_shot is not None) else None
    return {
        "invocations": d["invocations"],
        "sessions": n_sessions,
        "avg_per_session": avg_per_session,
        "distinct_tools": len(d["tools"]),
        "effectiveness_rate_pct": eff_rate_pct,
        "single_shot_rate_pct": single_rate_pct,
    }


def build_data_caveats_line(signals: dict) -> str:
    missing = [k for k, v in signals.items() if not v]
    if not missing:
        return "**Data signals available:** all optional fields present — full report."
    return (
        "**Data caveats:** input is missing "
        + ", ".join(f"`{m}`" for m in missing)
        + " — affected metrics shown as `—`."
    )


def build_missing_signals_section(signals: dict) -> str:
    lines = []
    if not signals["session_id"]:
        lines.append("- `session_id` absent → **session count, avg/session, and single-shot rate** could not be computed.")
    if not signals["output_consumed"]:
        lines.append("- `output_consumed` absent → **effectiveness rate** could not be computed.")
    if not signals["consumed_at"]:
        lines.append("- `consumed_at` absent → **output-to-shipped lag** could not be computed.")
    if not signals["outcome"]:
        lines.append("- `outcome` absent → cannot filter out errored invocations; raw counts include errors.")
    if not lines:
        return "All optional signals were present; the report contains all available columns."
    return "\n".join(lines)


def load_template(name: str, script_dir: Path) -> str:
    p = script_dir.parent / "templates" / name
    if not p.exists():
        raise SystemExit(f"error: template not found: {p}")
    return p.read_text()


# --------------------------------------------------------------------- views


def render_per_user(per_user, tool_counter, signals, ctx, sort_for_effectiveness=False):
    template = load_template(
        "report-per-user.md" if not sort_for_effectiveness else "report-per-user.md",
        ctx["script_dir"],
    )

    metrics_by_user = {u: per_user_metrics(d, signals) for u, d in per_user.items()}

    if sort_for_effectiveness:
        # Highest single-shot rate first (most theatrical pattern); tie-break by lowest effectiveness
        def key(u):
            m = metrics_by_user[u]
            ss = m["single_shot_rate_pct"] if m["single_shot_rate_pct"] is not None else -1
            er = m["effectiveness_rate_pct"] if m["effectiveness_rate_pct"] is not None else 101
            return (-ss, er)
        users_sorted = sorted(metrics_by_user.keys(), key=key)
    else:
        users_sorted = sorted(metrics_by_user.keys())

    rows = []
    for u in users_sorted:
        m = metrics_by_user[u]
        sessions_str = str(m["sessions"]) if m["sessions"] is not None else "—"
        avg_str = f"{m['avg_per_session']:.1f}" if m["avg_per_session"] is not None else "—"
        eff_str = f"{m['effectiveness_rate_pct']:.0f}%" if m["effectiveness_rate_pct"] is not None else "—"
        ss_str = f"{m['single_shot_rate_pct']:.0f}%" if m["single_shot_rate_pct"] is not None else "—"
        rows.append(
            f"| {u} | {m['invocations']} | {sessions_str} | {avg_str} | "
            f"{m['distinct_tools']} | {eff_str} | {ss_str} |"
        )

    total_invocations = sum(tool_counter.values())
    top_tools_rows = "\n".join(
        f"| {t} | {c} | {100 * c / total_invocations:.0f}% |"
        for t, c in tool_counter.most_common(10)
    )

    return template.format(
        team_name=ctx["team_name"],
        start_date=ctx["start"].date().isoformat(),
        end_date=ctx["end"].date().isoformat(),
        n_days=(ctx["end"] - ctx["start"]).days,
        n_users=len(per_user),
        n_invocations=total_invocations,
        n_distinct_tools=len(tool_counter),
        data_caveats_line=ctx["caveats_line"],
        per_user_rows="\n".join(rows),
        top_tools_rows=top_tools_rows,
        missing_signals_section=ctx["missing_section"],
        generated_at=ctx["generated_at"],
        input_file=ctx["input_file"],
    )


def render_team_rollup(per_user, tool_counter, signals, ctx):
    if len(per_user) < MIN_USERS_FOR_ROLLUP:
        raise SystemExit(
            f"error: team-rollup requires ≥{MIN_USERS_FOR_ROLLUP} users in scope; "
            f"got {len(per_user)}. Aggregate views aren't anonymous at that size. "
            f"Use --view per-user and treat the output as identifying."
        )

    template = load_template("report-team-rollup.md", ctx["script_dir"])
    n_days = max(1, (ctx["end"] - ctx["start"]).days)

    invocations_per_user_per_day = [
        d["invocations"] / n_days for d in per_user.values()
    ]
    distinct_tools_per_user = [len(d["tools"]) for d in per_user.values()]

    # Effectiveness (team avg, weighted by known events)
    total_known = sum(d["consumed_known"] for d in per_user.values())
    total_yes = sum(d["consumed_yes"] for d in per_user.values())
    team_eff = (
        f"{100 * total_yes / total_known:.0f}%"
        if signals["output_consumed"] and total_known
        else "—"
    )

    # Single-shot (team avg, weighted by sessions)
    total_sessions = sum(len(d["sessions"]) for d in per_user.values())
    total_single_shot = sum(
        sum(1 for c in d["session_counts"].values() if c == 1)
        for d in per_user.values()
    )
    team_ss = (
        f"{100 * total_single_shot / total_sessions:.0f}%"
        if signals["session_id"] and total_sessions
        else "—"
    )

    # Engagement tiers (normalized to weekly thresholds)
    week_scale = 7 / n_days
    tiers = {"heavy": 0, "moderate": 0, "light": 0, "inactive": 0}
    for d in per_user.values():
        weekly = d["invocations"] * week_scale
        if weekly == 0:
            tiers["inactive"] += 1
        elif weekly > 20:
            tiers["heavy"] += 1
        elif weekly >= 5:
            tiers["moderate"] += 1
        else:
            tiers["light"] += 1

    n_active = sum(1 for d in per_user.values() if d["invocations"] > 0)

    if signals["output_consumed"] and total_known:
        eff_block = (
            f"Team-wide, **{100 * total_yes / total_known:.0f}%** of invocations "
            f"with a known outcome had their output consumed in a shipped artifact "
            f"({total_yes:,} of {total_known:,}). The remaining "
            f"{total_known - total_yes:,} invocations produced output that was either "
            f"discarded, never reviewed, or not yet tracked as consumed."
        )
    else:
        eff_block = (
            "**Effectiveness signal is unavailable** — the input lacks `output_consumed` "
            "data. Volume and engagement-tier metrics above are still valid, but the "
            "performative-vs-effective distinction cannot be computed from this input."
        )

    total_invocations = sum(tool_counter.values())
    top_tools_rows = "\n".join(
        f"| {t} | {c} | {100 * c / total_invocations:.0f}% |"
        for t, c in tool_counter.most_common(10)
    )

    return template.format(
        team_name=ctx["team_name"],
        start_date=ctx["start"].date().isoformat(),
        end_date=ctx["end"].date().isoformat(),
        n_days=n_days,
        n_users=len(per_user),
        n_invocations=total_invocations,
        data_caveats_line=ctx["caveats_line"],
        median_invocations_per_user_per_day=f"{median(invocations_per_user_per_day):.1f}" if invocations_per_user_per_day else "0",
        median_distinct_tools_per_user=f"{median(distinct_tools_per_user):.0f}" if distinct_tools_per_user else "0",
        team_effectiveness_rate=team_eff,
        team_single_shot_rate=team_ss,
        n_active_users=n_active,
        n_heavy=tiers["heavy"],
        n_moderate=tiers["moderate"],
        n_light=tiers["light"],
        n_inactive=tiers["inactive"],
        top_tools_rows=top_tools_rows,
        effectiveness_block=eff_block,
        missing_signals_section=ctx["missing_section"],
        generated_at=ctx["generated_at"],
        input_file=ctx["input_file"],
    )


# --------------------------------------------------------------------- driver


def main(argv) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("input", help="Path to events file (.csv or .jsonl)")
    ap.add_argument("--view", choices=VIEWS, default="per-user")
    ap.add_argument("--period", choices=("week", "month"), default="week")
    ap.add_argument("--from", dest="from_arg", default=None, help="ISO date — overrides --period")
    ap.add_argument("--to", dest="to_arg", default=None, help="ISO date — overrides --period")
    ap.add_argument("--team-name", default="Team")
    ap.add_argument("-o", "--out", default=None, help="Output markdown path")
    args = ap.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        sys.stderr.write(f"error: input file not found: {input_path}\n")
        return 1

    events = load_events(input_path)
    if not events:
        sys.stderr.write("error: input file has no events\n")
        return 1

    signals = detect_signals(events)
    start, end = resolve_period(args.period, args.from_arg, args.to_arg)
    events = filter_to_period(events, start, end)
    if not events:
        sys.stderr.write(f"error: no events fell within {start.isoformat()} → {end.isoformat()}\n")
        return 1

    per_user, tool_counter = aggregate(events, signals)

    script_dir = Path(__file__).resolve().parent
    ctx = {
        "team_name": args.team_name,
        "start": start,
        "end": end,
        "caveats_line": build_data_caveats_line(signals),
        "missing_section": build_missing_signals_section(signals),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_file": str(input_path.name),
        "script_dir": script_dir,
    }

    if args.view == "per-user":
        out = render_per_user(per_user, tool_counter, signals, ctx)
    elif args.view == "effectiveness":
        out = render_per_user(per_user, tool_counter, signals, ctx, sort_for_effectiveness=True)
    else:  # team-rollup
        out = render_team_rollup(per_user, tool_counter, signals, ctx)

    out_path = Path(args.out).expanduser().resolve() if args.out else input_path.with_suffix(".report.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out)
    print(f"wrote {out_path} ({len(events)} events, {len(per_user)} users, view={args.view})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

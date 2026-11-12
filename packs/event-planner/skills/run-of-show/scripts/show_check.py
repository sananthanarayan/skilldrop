#!/usr/bin/env python3
"""Check an event's run of show for clashes and draw it as a timeline. Stdlib only.

Reads a show.json: the rooms (opening hours, turnaround between items), the items (title,
room, start, end or duration, the people needed, setup minutes needed in the room before it
starts, changeover minutes needed after it), the travel minutes between rooms, and the
published end of the day. It fails a show where
  - an item ends before it starts
  - two items overlap in one room
  - the gap between two items in a room is shorter than the turnaround, the next item's
    setup or the last item's changeover
  - an item, with its setup, runs outside its room's opening hours
  - a person is needed in two places at once, or has less than the travel time between
    rooms
and warns where
  - a person works more than --max-hours without a break of --break minutes
  - a room sits empty for more than --max-gap minutes between items
  - the last item ends after the published end
Then it prints the running order, and with --svg draws one lane per room with each item as
a block at its times, failures in red.

Times are 24-hour "HH:MM". Items on several days carry a "day" (any label, such as
"2026-06-12" or "Day 2"); each day is checked on its own.

Usage:
  python3 show_check.py show.json [--svg timeline.svg] [--json]
                        [--max-hours 3] [--break 15] [--max-gap 45]
Exit codes: 0 no failures, 1 a failure, 2 bad input.
"""
import argparse
import json
import math
import re
import sys

TIME = re.compile(r"^([01]?\d|2[0-4]):([0-5]\d)$")


class BadInput(ValueError):
    pass


def minutes(v, what):
    """'09:30' -> 570. Raises BadInput."""
    m = TIME.match(str(v).strip()) if v is not None else None
    if not m or (int(m.group(1)) == 24 and m.group(2) != "00"):
        raise BadInput(f"{what} must be a 24-hour time like 09:30, got {v!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def hhmm(n):
    return f"{int(n) // 60:02d}:{int(n) % 60:02d}"


def _mins(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        raise BadInput(f"{what} must be a number of minutes, got {v!r}")
    return float(v)


def load(data):
    if not isinstance(data, dict):
        raise BadInput("the file must hold a JSON object")
    default_turn = _mins(data.get("turnaround", 0), "turnaround")
    rooms = {}
    for i, r in enumerate(data.get("rooms") or []):
        if not isinstance(r, dict) or not r.get("name"):
            raise BadInput(f"room {i + 1} needs a name")
        n = str(r["name"])
        rooms[n] = {"name": n, "open": minutes(r["open"], f"room {n} open") if r.get("open") else None,
                    "close": minutes(r["close"], f"room {n} close") if r.get("close") else None,
                    "turnaround": _mins(r.get("turnaround", default_turn), f"room {n} turnaround")}
    items = []
    for i, it in enumerate(data.get("items") or []):
        if not isinstance(it, dict) or not it.get("title"):
            raise BadInput(f"item {i + 1} needs a title")
        iid = str(it.get("id") or f"item {i + 1}")
        room = str(it.get("room") or "")
        if not room:
            raise BadInput(f"{iid} ({it['title']}) needs a room")
        if room not in rooms:
            rooms[room] = {"name": room, "open": None, "close": None, "turnaround": default_turn}
        start = minutes(it.get("start"), f"{iid} start")
        if it.get("end") is not None:
            end = minutes(it["end"], f"{iid} end")
        elif it.get("duration") is not None:
            end = start + _mins(it["duration"], f"{iid} duration")
        else:
            raise BadInput(f"{iid} ({it['title']}) needs an end or a duration")
        people = it.get("people") or []
        if isinstance(people, str):
            people = [people]
        items.append({"id": iid, "title": str(it["title"]), "room": room, "day": str(it.get("day") or ""),
                      "start": start, "end": end, "people": [str(p) for p in people],
                      "setup": _mins(it.get("setup", 0), f"{iid} setup"),
                      "changeover": _mins(it.get("changeover", 0), f"{iid} changeover")})
    if not items:
        raise BadInput("no items")
    travel = {}
    for i, t in enumerate(data.get("travel") or []):
        if not isinstance(t, dict) or not isinstance(t.get("between"), list) or len(t["between"]) != 2:
            raise BadInput(f"travel {i + 1} must be {{\"between\": [room, room], \"minutes\": n}}")
        a, b = (str(x) for x in t["between"])
        travel[frozenset((a, b))] = _mins(t.get("minutes"), f"travel {i + 1} minutes")
    end = minutes(data["published_end"], "published_end") if data.get("published_end") else None
    return {"rooms": rooms, "items": items, "travel": travel, "published_end": end}


def check(show, max_hours=3.0, brk=15.0, max_gap=45.0):
    fails, warns, bad = [], [], set()
    items = show["items"]
    label = lambda it: f"{it['title']} ({hhmm(it['start'])}{', ' + it['day'] if it['day'] else ''})"
    for it in items:
        if it["end"] <= it["start"]:
            fails.append(f"{label(it)} ends at {hhmm(it['end'])}, not after it starts")
            bad.add(it["id"])
    ok = [it for it in items if it["end"] > it["start"]]
    groups = {}
    for it in ok:
        groups.setdefault((it["day"], it["room"]), []).append(it)
    for (day, room), lane in groups.items():
        r = show["rooms"][room]
        lane.sort(key=lambda it: it["start"])
        for it in lane:
            if r["open"] is not None and it["start"] - it["setup"] < r["open"]:
                need = f" with {it['setup']:.0f} min setup" if it["setup"] else ""
                fails.append(f"{label(it)} starts{need} before {room} opens at {hhmm(r['open'])}")
                bad.add(it["id"])
            if r["close"] is not None and it["end"] > r["close"]:
                fails.append(f"{label(it)} ends at {hhmm(it['end'])}, after {room} closes at {hhmm(r['close'])}")
                bad.add(it["id"])
        for a, b in zip(lane, lane[1:]):
            gap = b["start"] - a["end"]
            if gap < 0:
                fails.append(f"{label(a)} and {label(b)} overlap in {room} by {-gap:.0f} min")
                bad.update((a["id"], b["id"]))
                continue
            need = max(r["turnaround"], b["setup"], a["changeover"])
            if gap < need:
                why = ("the room's turnaround" if need == r["turnaround"] else
                       f"{b['title']}'s setup" if need == b["setup"] else f"{a['title']}'s changeover")
                fails.append(f"{room}: {gap:.0f} min between {label(a)} and {label(b)}, "
                             f"{need:.0f} min needed for {why}")
                bad.update((a["id"], b["id"]))
            elif gap > max_gap:
                warns.append(f"{room} is empty for {gap:.0f} min between {a['title']} and {b['title']}")
    people = {}
    for it in ok:
        for p in it["people"]:
            people.setdefault((it["day"], p), []).append(it)
    for (day, p), mine in people.items():
        mine.sort(key=lambda it: it["start"])
        for a, b in zip(mine, mine[1:]):
            gap = b["start"] - a["end"]
            if gap < 0:
                fails.append(f"{p} is needed at {label(a)} in {a['room']} and {label(b)} in {b['room']} at once")
                bad.update((a["id"], b["id"]))
            elif a["room"] != b["room"]:
                t = show["travel"].get(frozenset((a["room"], b["room"])))
                if t is not None and gap < t:
                    fails.append(f"{p} has {gap:.0f} min to get from {a['room']} to {b['room']} "
                                 f"between {a['title']} and {b['title']}; the walk takes {t:.0f}")
                    bad.update((a["id"], b["id"]))
        run_start, last_end = None, None
        for it in mine:
            if last_end is None or it["start"] - last_end >= brk:
                run_start = it["start"]
            last_end = max(last_end or it["end"], it["end"])
            if last_end - run_start > max_hours * 60:
                warns.append(f"{p} works from {hhmm(run_start)} to {hhmm(last_end)}"
                             f"{' on ' + day if day else ''} without a {brk:.0f}-minute break")
                run_start = math.inf  # one warning per stretch
        # an inf run_start makes the difference negative until the next break resets it
    if show["published_end"] is not None:
        for day in sorted({it["day"] for it in ok}):
            last = max((it for it in ok if it["day"] == day), key=lambda it: it["end"])
            if last["end"] > show["published_end"]:
                warns.append(f"{last['title']} ends at {hhmm(last['end'])}{', ' + day if day else ''}, "
                             f"{last['end'] - show['published_end']:.0f} min after the published end "
                             f"of {hhmm(show['published_end'])}")
    return {"fails": fails, "warns": warns, "bad": sorted(bad)}


def order(show):
    return sorted(show["items"], key=lambda it: (it["day"], it["start"], it["room"]))


def report(show, r):
    out, day = [], None
    for it in order(show):
        if it["day"] != day and it["day"]:
            out.append(it["day"])
        day = it["day"]
        who = f" — {', '.join(it['people'])}" if it["people"] else ""
        out.append(f"  {hhmm(it['start'])}–{hhmm(it['end'])}  {it['room']}: {it['title']}{who}")
    out += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    out.append("PASS" if not r["fails"] else f"{len(r['fails'])} failure(s)")
    return "\n".join(out) + "\n"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(show, r, px=3.0, lane=64):
    """One panel per day: a lane per room, a block per item, a tick every 30 minutes."""
    days = sorted({it["day"] for it in show["items"]})
    rooms = list(show["rooms"])
    out_body, y = [], 50
    width = 0
    for day in days:
        its = [it for it in show["items"] if it["day"] == day]
        t0 = min(min(it["start"] for it in its), *(show["rooms"][it["room"]]["open"] or it["start"] for it in its))
        t1 = max(max(it["end"] for it in its), *(show["rooms"][it["room"]]["close"] or it["end"] for it in its))
        t0, t1 = 30 * math.floor(t0 / 30), 30 * math.ceil(t1 / 30)
        scale = min(px, 1100.0 / max(t1 - t0, 30))  # a long day still fits a page
        X = lambda t, t0=t0, scale=scale: 150 + (t - t0) * scale
        width = max(width, X(t1) + 30)
        if day:
            out_body.append(f'<text x="20" y="{y:.0f}" font-size="14" font-weight="bold">{esc(day)}</text>')
            y += 14
        top = y + 10
        for t in range(int(t0), int(t1) + 1, 30):
            major = t % 60 == 0
            out_body.append(f'<line x1="{X(t):.1f}" y1="{top:.0f}" x2="{X(t):.1f}" y2="{top + lane * len(rooms):.0f}" '
                            f'stroke="{"#cfd8dc" if major else "#eceff1"}"/>')
            if major:
                out_body.append(f'<text x="{X(t):.1f}" y="{top - 3:.0f}" font-size="10" text-anchor="middle" fill="#607d8b">{hhmm(t)}</text>')
        for k, room in enumerate(rooms):
            ly = top + k * lane
            rm = show["rooms"][room]
            out_body.append(f'<text x="20" y="{ly + lane / 2 + 4:.0f}" font-size="12" fill="#263238">{esc(room)}</text>'
                            f'<line x1="150" y1="{ly + lane:.0f}" x2="{X(t1):.1f}" y2="{ly + lane:.0f}" stroke="#b0bec5"/>')
            if rm["open"] is not None and rm["close"] is not None:
                out_body.append(f'<rect x="{X(rm["open"]):.1f}" y="{ly + 2:.0f}" width="{(rm["close"] - rm["open"]) * scale:.1f}" '
                                f'height="{lane - 4}" fill="#f1f8e9" opacity="0.6"/>')
            for it in its:
                if it["room"] != room:
                    continue
                bad = it["id"] in r["bad"]
                x0, w = X(it["start"]), max((it["end"] - it["start"]) * scale, 2)
                if it["setup"]:
                    out_body.append(f'<rect x="{x0 - it["setup"] * scale:.1f}" y="{ly + 8:.0f}" width="{it["setup"] * scale:.1f}" '
                                    f'height="{lane - 16}" fill="#fff8e1" stroke="#ffb300" stroke-dasharray="3,2"/>')
                out_body.append(f'<rect x="{x0:.1f}" y="{ly + 6:.0f}" width="{w:.1f}" height="{lane - 12}" rx="4" '
                                f'fill="{"#ffebee" if bad else "#e3f2fd"}" stroke="{"#c62828" if bad else "#1565c0"}" '
                                f'stroke-width="{2.5 if bad else 1}"/>')
                title = it["title"] if len(it["title"]) * 6 < w - 6 else it["title"][: max(int((w - 10) / 6), 1)] + "…"
                out_body.append(f'<text x="{x0 + 4:.1f}" y="{ly + 24:.0f}" font-size="10" fill="#0d47a1">{esc(title)}</text>'
                                f'<text x="{x0 + 4:.1f}" y="{ly + 38:.0f}" font-size="9" fill="#546e7a">'
                                f'{hhmm(it["start"])}–{hhmm(it["end"])}{" ✗" if bad else ""}</text>')
        y = top + lane * len(rooms) + 30
    status = "PASS: no clashes" if not r["fails"] else f"{len(r['fails'])} clash(es): items marked ✗ in red"
    out_body.append(f'<text x="20" y="{y:.0f}" font-size="12" fill="{"#2e7d32" if not r["fails"] else "#c62828"}">{esc(status)}</text>'
                    f'<text x="20" y="{y + 16:.0f}" font-size="10" fill="#666">Dashed amber: setup before an item · '
                    f'green band: room open</text>')
    H, W = y + 34, max(width, 520)
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
            'font-family="Helvetica, Arial, sans-serif">', f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>',
            '<text x="20" y="28" font-size="16" font-weight="bold">Run of show</text>']
    return "\n".join(head + out_body + ["</svg>"]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a run of show for clashes and draw it as a timeline.")
    ap.add_argument("show")
    ap.add_argument("--svg", help="write the timeline here")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--max-hours", type=float, default=3.0, help="hours a person may work without a break (default 3)")
    ap.add_argument("--break", dest="brk", type=float, default=15.0, help="minutes that count as a break (default 15)")
    ap.add_argument("--max-gap", type=float, default=45.0, help="minutes a room may sit empty between items (default 45)")
    args = ap.parse_args(argv)
    try:
        with open(args.show, encoding="utf-8") as fh:
            show = load(json.load(fh))
    except (OSError, ValueError) as e:
        print(f"FAIL cannot read {args.show}: {e}")
        return 2
    r = check(show, args.max_hours, args.brk, args.max_gap)
    if args.json:
        print(json.dumps({"pass": not r["fails"], "fails": r["fails"], "warns": r["warns"],
                          "items": [dict(it, start=hhmm(it["start"]), end=hhmm(it["end"])) for it in order(show)]},
                         indent=1))
    else:
        print(report(show, r), end="")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as fh:
            fh.write(svg(show, r))
        if not args.json:
            print(f"\nWrote {args.svg}")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

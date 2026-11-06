#!/usr/bin/env python3
"""Check a table seating plan against its rules and draw the room. Stdlib only.

Reads a seating.json: the tables (capacity, shape, position in metres, accessible or not),
the guests (name, party or household, needs), the rules (groups that sit together, pairs
kept apart, fixed seats) and the assignments (table -> guests). It fails a plan where
  - a guest is unseated, or seated twice
  - a table holds more guests than its capacity
  - a together group is split across tables
  - an apart pair shares a table
  - a wheelchair user sits at a table not marked accessible
  - a guest with a fixed seat is not at that table
and warns where
  - a household or party that would fit at one table is split
  - a table is under half full, or empty
  - a guest who came alone sits at a table where everyone else is one other party
  - a guest who needs to be near an exit is further than --exit-distance from one (when
    the room's exits are given)
Then it lists every table with its guests and dietary needs, and with --svg draws the room:
tables at their positions, labelled with their fill, names around each, failures in red.

Usage:
  python3 seating_check.py seating.json [--svg room.svg] [--json] [--exit-distance 8]
Exit codes: 0 no failures, 1 a failure, 2 bad input.
"""
import argparse
import json
import math
import sys


class BadInput(ValueError):
    pass


def _num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise BadInput(f"{what} must be a number, got {v!r}")
    return float(v)


def _point(v, what):
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise BadInput(f"{what} must be [x, y] in metres")
    return (_num(v[0], what + " x"), _num(v[1], what + " y"))


def load(data):
    """Validate the raw JSON and return a normalised plan. Raises BadInput."""
    if not isinstance(data, dict):
        raise BadInput("the file must hold a JSON object")
    tables, guests = {}, {}
    for i, t in enumerate(data.get("tables") or []):
        if not isinstance(t, dict) or not t.get("id"):
            raise BadInput(f"table {i + 1} needs an id")
        tid = str(t["id"])
        if tid in tables:
            raise BadInput(f"two tables are called {tid!r}")
        cap = _num(t.get("capacity", 10), f"table {tid} capacity")
        if cap < 1 or cap != int(cap):
            raise BadInput(f"table {tid} capacity must be a whole number of seats")
        shape = str(t.get("shape", "round"))
        if shape not in ("round", "rect"):
            raise BadInput(f"table {tid} shape must be round or rect")
        tables[tid] = {"id": tid, "capacity": int(cap), "shape": shape,
                       "at": _point(t["at"], f"table {tid} position") if "at" in t else None,
                       "accessible": bool(t.get("accessible", False)), "label": str(t.get("label", ""))}
    if not tables:
        raise BadInput("no tables")
    for i, g in enumerate(data.get("guests") or []):
        if not isinstance(g, dict) or not g.get("id"):
            raise BadInput(f"guest {i + 1} needs an id")
        gid = str(g["id"])
        if gid in guests:
            raise BadInput(f"two guests have the id {gid!r}")
        needs = g.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        guests[gid] = {"id": gid, "name": str(g.get("name") or gid), "party": str(g.get("party") or ""),
                       "needs": [str(n).lower() for n in needs], "dietary": str(g.get("dietary") or "")}
    if not guests:
        raise BadInput("no guests")

    def known(gid, where):
        if str(gid) not in guests:
            raise BadInput(f"{where} names a guest {gid!r} who is not on the guest list")
        return str(gid)

    together = []
    for i, grp in enumerate(data.get("together") or []):
        if not isinstance(grp, list) or len(grp) < 2:
            raise BadInput(f"together group {i + 1} must list two or more guests")
        together.append([known(x, f"together group {i + 1}") for x in grp])
    apart = []
    for i, pair in enumerate(data.get("apart") or []):
        if not isinstance(pair, list) or len(pair) != 2:
            raise BadInput(f"apart pair {i + 1} must list exactly two guests")
        apart.append([known(x, f"apart pair {i + 1}") for x in pair])
    fixed = {}
    if not isinstance(data.get("fixed") or {}, dict):
        raise BadInput("fixed must map a guest id to a table id")
    for gid, tid in (data.get("fixed") or {}).items():
        if str(tid) not in tables:
            raise BadInput(f"the fixed seat for {gid} names a table {tid!r} that does not exist")
        fixed[known(gid, "fixed")] = str(tid)

    raw = data.get("assignments") or {}
    if not isinstance(raw, dict):
        raise BadInput("assignments must map each table id to a list of guest ids")
    seats = {tid: [] for tid in tables}
    for tid, gl in raw.items():
        if str(tid) not in tables:
            raise BadInput(f"assignments name a table {tid!r} that does not exist")
        if not isinstance(gl, list):
            raise BadInput(f"assignments for table {tid} must be a list of guest ids")
        seats[str(tid)] += [known(g, f"table {tid}") for g in gl]
    exits = [_point(e, f"exit {i + 1}") for i, e in enumerate(data.get("exits") or [])]
    room = data.get("room") or {}
    if not isinstance(room, dict):
        raise BadInput("room must be {\"width\": metres, \"depth\": metres}")
    return {"tables": tables, "guests": guests, "together": together, "apart": apart, "fixed": fixed,
            "seats": seats, "exits": exits,
            "room": (_num(room["width"], "room width"), _num(room["depth"], "room depth"))
            if room.get("width") and room.get("depth") else None}


def check(plan, exit_distance=8.0):
    tables, guests, seats = plan["tables"], plan["guests"], plan["seats"]
    fails, warns, bad_tables = [], [], set()
    where = {}
    for tid, gl in seats.items():
        for g in gl:
            where.setdefault(g, []).append(tid)
    name = lambda g: guests[g]["name"]
    for g in guests:
        at = where.get(g, [])
        if not at:
            fails.append(f"{name(g)} has no seat")
        elif len(at) > 1:
            fails.append(f"{name(g)} is seated more than once ({', '.join(at)})")
            bad_tables.update(at)
    table_of = {g: at[0] for g, at in where.items() if len(at) == 1}
    for tid, gl in seats.items():
        t = tables[tid]
        if len(gl) > t["capacity"]:
            fails.append(f"table {tid} has {len(gl)} guests for {t['capacity']} seats")
            bad_tables.add(tid)
    for grp in plan["together"]:
        at = {table_of.get(g) for g in grp if g in table_of}
        if len(at) > 1:
            fails.append("must sit together but are split: " + ", ".join(f"{name(g)} ({table_of.get(g, 'unseated')})" for g in grp))
            bad_tables.update(t for t in at if t)
    for a, b in plan["apart"]:
        if a in table_of and table_of.get(a) == table_of.get(b):
            fails.append(f"{name(a)} and {name(b)} must be kept apart but both sit at table {table_of[a]}")
            bad_tables.add(table_of[a])
    for g, tid in table_of.items():
        if "wheelchair" in guests[g]["needs"] and not tables[tid]["accessible"]:
            fails.append(f"{name(g)} uses a wheelchair but table {tid} is not marked accessible")
            bad_tables.add(tid)
    for g, tid in plan["fixed"].items():
        if table_of.get(g) != tid:
            fails.append(f"{name(g)} has a fixed seat at table {tid} but sits at {table_of.get(g, 'no table')}")
            bad_tables.add(tid)

    biggest = max(t["capacity"] for t in tables.values())
    parties = {}
    for g, info in guests.items():
        if info["party"]:
            parties.setdefault(info["party"], []).append(g)
    for party, members in sorted(parties.items()):
        at = sorted({table_of[g] for g in members if g in table_of})
        if len(at) > 1 and len(members) <= biggest:
            warns.append(f"the {party} party ({len(members)}) is split across tables {', '.join(at)}")
    for tid, gl in seats.items():
        cap = tables[tid]["capacity"]
        if not gl:
            warns.append(f"table {tid} is empty")
        elif len(gl) < cap / 2:
            warns.append(f"table {tid} is under half full ({len(gl)} of {cap})")
    in_group = {g for grp in plan["together"] for g in grp}
    for g, tid in table_of.items():
        p = guests[g]["party"]
        alone = (not p or len(parties.get(p, [])) == 1) and g not in in_group
        others = [o for o in seats[tid] if o != g]
        other_parties = {guests[o]["party"] for o in others}
        if alone and len(others) >= 2 and len(other_parties) == 1 and "" not in other_parties:
            warns.append(f"{name(g)} came alone and is the only guest at table {tid} not in the {other_parties.pop()} party")
    if plan["exits"]:
        for g, tid in table_of.items():
            t = tables[tid]
            if "near exit" in guests[g]["needs"] and t["at"]:
                d = min(math.dist(t["at"], e) for e in plan["exits"])
                if d > exit_distance:
                    warns.append(f"{name(g)} needs to be near an exit but table {tid} is {d:.1f} m from the nearest")
    return {"fails": fails, "warns": warns, "bad_tables": sorted(bad_tables), "table_of": table_of,
            "seated": len(table_of), "guests": len(guests),
            "seats": sum(t["capacity"] for t in tables.values())}


def table_rows(plan, r):
    rows = []
    for tid, t in plan["tables"].items():
        gl = plan["seats"][tid]
        diet = {}
        for g in gl:
            d = plan["guests"][g]["dietary"]
            if d:
                diet[d] = diet.get(d, 0) + 1
        rows.append({"table": tid, "shape": t["shape"], "capacity": t["capacity"], "accessible": t["accessible"],
                     "seated": len(gl), "guests": [plan["guests"][g]["name"] for g in gl], "dietary": diet,
                     "ok": tid not in r["bad_tables"]})
    return rows


def report(plan, r):
    out = [f"{r['seated']} of {r['guests']} guests seated, {len(plan['tables'])} tables, {r['seats']} seats."]
    for row in table_rows(plan, r):
        flags = ("accessible, " if row["accessible"] else "") + f"{row['seated']}/{row['capacity']}"
        diet = ("; " + ", ".join(f"{n} {d}" for d, n in sorted(row["dietary"].items()))) if row["dietary"] else ""
        out.append(f"  {row['table']} ({row['shape']}, {flags}{diet}): {', '.join(row['guests']) or '-'}")
    out += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    out.append("PASS" if not r["fails"] else f"{len(r['fails'])} failure(s)")
    return "\n".join(out) + "\n"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def layout(plan):
    """Positions for every table: given ones, or a grid for tables without one."""
    pos, n = {}, 0
    for tid, t in plan["tables"].items():
        if t["at"]:
            pos[tid] = t["at"]
    cols = max(1, math.ceil(math.sqrt(len(plan["tables"]))))
    for tid, t in plan["tables"].items():
        if tid not in pos:
            pos[tid] = (2.5 + 4.0 * (n % cols), 2.5 + 4.0 * (n // cols))
            n += 1
    return pos


def svg(plan, r, scale=40):
    pos = layout(plan)
    radius = lambda t: 0.45 + 0.09 * t["capacity"]  # metres, so a 10-seat round is about 1.35 m
    xs = [p[0] for p in pos.values()] + [e[0] for e in plan["exits"]]
    ys = [p[1] for p in pos.values()] + [e[1] for e in plan["exits"]]
    w, d = plan["room"] or (max(xs) + 3, max(ys) + 3)
    W, H = w * scale + 80, d * scale + 110
    P = lambda x, y: (40 + x * scale, 60 + y * scale)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
           'font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>',
           f'<text x="40" y="30" font-size="16" font-weight="bold">Seating plan: {r["seated"]} of {r["guests"]} guests, '
           f'{len(plan["tables"])} tables</text>',
           f'<rect x="40" y="60" width="{w * scale:.0f}" height="{d * scale:.0f}" fill="#fafafa" stroke="#444" stroke-width="2"/>']
    for i, e in enumerate(plan["exits"]):
        x, y = P(*e)
        out.append(f'<rect x="{x - 14:.0f}" y="{y - 6:.0f}" width="28" height="12" fill="#2e7d32"/>'
                   f'<text x="{x:.0f}" y="{y + 22:.0f}" font-size="10" text-anchor="middle" fill="#2e7d32">EXIT</text>')
    for tid, t in plan["tables"].items():
        x, y = P(*pos[tid])
        rad = radius(t) * scale
        bad = tid in r["bad_tables"]
        stroke, fill = ("#c62828", "#ffebee") if bad else ("#455a64", "#eceff1")
        if t["shape"] == "round":
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad:.0f}" fill="{fill}" stroke="{stroke}" stroke-width="{3 if bad else 1.5}"/>')
        else:
            out.append(f'<rect x="{x - rad * 1.4:.0f}" y="{y - rad * 0.6:.0f}" width="{rad * 2.8:.0f}" height="{rad * 1.2:.0f}" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="{3 if bad else 1.5}"/>')
        gl = plan["seats"][tid]
        mark = " ✗" if bad else ""
        acc = " · accessible" if t["accessible"] else ""
        out.append(f'<text x="{x:.0f}" y="{y - 2:.0f}" font-size="13" font-weight="bold" text-anchor="middle" '
                   f'fill="{stroke}">{esc(tid)}{mark}</text>'
                   f'<text x="{x:.0f}" y="{y + 13:.0f}" font-size="10" text-anchor="middle" fill="#555">{len(gl)}/{t["capacity"]}{acc}</text>')
        rx, ry = (rad + 8, rad + 8) if t["shape"] == "round" else (rad * 1.4 + 10, rad * 0.6 + 10)
        for k, g in enumerate(gl):
            a = -math.pi / 2 + 2 * math.pi * k / max(len(gl), 1)
            gx, gy = x + rx * math.cos(a), y + ry * math.sin(a)
            anchor = "start" if math.cos(a) > 0.2 else ("end" if math.cos(a) < -0.2 else "middle")
            out.append(f'<text x="{gx:.0f}" y="{gy + 3:.0f}" font-size="9" text-anchor="{anchor}" fill="#222">'
                       f'{esc(plan["guests"][g]["name"])}</text>')
    ly = 60 + d * scale + 28
    status = "PASS: every rule met" if not r["fails"] else f"{len(r['fails'])} rule(s) broken: tables marked ✗ in red"
    out.append(f'<text x="40" y="{ly:.0f}" font-size="12" fill="{"#2e7d32" if not r["fails"] else "#c62828"}">{esc(status)}</text>')
    out.append(f'<text x="40" y="{ly + 18:.0f}" font-size="10" fill="#666">Positions in metres, '
               f'1 m = {scale} px · names run clockwise from the top of each table</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a seating plan against its rules and draw the room.")
    ap.add_argument("seating")
    ap.add_argument("--svg", help="write the room plan here")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--exit-distance", type=float, default=8.0,
                    help="metres from an exit that counts as near one (default 8)")
    args = ap.parse_args(argv)
    try:
        with open(args.seating, encoding="utf-8") as fh:
            plan = load(json.load(fh))
    except (OSError, ValueError) as e:  # BadInput and JSONDecodeError are ValueErrors
        print(f"FAIL cannot read {args.seating}: {e}")
        return 2
    r = check(plan, args.exit_distance)
    if args.json:
        print(json.dumps({"pass": not r["fails"], "fails": r["fails"], "warns": r["warns"],
                          "seated": r["seated"], "guests": r["guests"], "tables": table_rows(plan, r)}, indent=1))
    else:
        print(report(plan, r), end="")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as fh:
            fh.write(svg(plan, r))
        if not args.json:
            print(f"\nWrote {args.svg}")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

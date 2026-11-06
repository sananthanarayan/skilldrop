#!/usr/bin/env python3
"""Check a schematic floor plan and draw it as a dimensioned SVG. Stdlib only.

Reads a plan.json: the floor's outline, each room as one or more rectangles, the doors
between rooms (and to "outside"), and the windows. It fails a plan where
  - two rooms overlap, or a room runs outside the outline
  - a door does not sit on a wall its two rooms share (or on the outline, for "outside")
  - a room cannot be reached from an outside door, or there is no outside door at all
and warns where
  - a room's area is more than the tolerance (default 10 %) off its target
  - a room is narrower than its min_width, or a door is narrower than min_door_width
  - a room marked habitable has no window on the outline
  - more than 5 % of the outline is not in any room
Then it draws the plan: outline, rooms with name, size and area, door swings, windows,
overall dimension strings, a scale bar and a north arrow.

Usage:
  python3 plan_check.py plan.json [--svg plan.svg]
Exit codes: 0 no failures, 1 a failure, 2 bad input.
"""
import argparse
import json
import math
import sys

EPS = 1e-6


class InputError(Exception):
    pass


def number(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise InputError(f"{what} must be a number")
    return float(v)


def poly_area(poly):
    s = 0.0
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def point_in_poly(p, poly):
    """True when p is inside or on the boundary."""
    if on_outline(p, poly):
        return True
    x, y = p
    inside = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def on_segment(p, a, b, tol=EPS * 10):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    L = math.hypot(x2 - x1, y2 - y1)
    if L < EPS:
        return math.hypot(x - x1, y - y1) <= tol
    cross = abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) / L
    dot = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / L
    return cross <= tol and -tol <= dot <= L + tol


def on_outline(p, poly):
    return any(on_segment(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def rect_edges(r):
    x, y, w, h = r
    c = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    return [(c[i], c[(i + 1) % 4]) for i in range(4)]


def on_rect_edge(p, r):
    return any(on_segment(p, a, b) for a, b in rect_edges(r))


def overlap(r1, r2):
    w = min(r1[0] + r1[2], r2[0] + r2[2]) - max(r1[0], r2[0])
    h = min(r1[1] + r1[3], r2[1] + r2[3]) - max(r1[1], r2[1])
    return w * h if w > EPS and h > EPS else 0.0


def rect_in_poly(r, poly):
    x, y, w, h = r
    corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    if not all(point_in_poly(c, poly) for c in corners):
        return False
    # an outline corner strictly inside the rectangle means the outline cuts into it
    return not any(x + EPS < px < x + w - EPS and y + EPS < py < y + h - EPS for px, py in poly)


def load(data):
    if not isinstance(data, dict):
        raise InputError("plan.json must be a JSON object")
    units = data.get("units", "m")
    if units not in ("m", "ft"):
        raise InputError("`units` must be \"m\" or \"ft\"")
    outline = data.get("outline")
    if not isinstance(outline, list) or len(outline) < 3:
        raise InputError("`outline` must list at least three [x, y] corners")
    try:
        outline = [(number(p[0], "outline x"), number(p[1], "outline y")) for p in outline]
    except (TypeError, IndexError):
        raise InputError("every corner in `outline` must be [x, y]")
    rooms = []
    seen = set()
    for i, rm in enumerate(data.get("rooms") or [], 1):
        if not isinstance(rm, dict) or not str(rm.get("name", "")).strip():
            raise InputError(f"room {i} needs a `name`")
        name = str(rm["name"]).strip()
        if name.lower() in seen or name.lower() == "outside":
            raise InputError(f"room name {name!r} is used twice or is reserved")
        seen.add(name.lower())
        rects = rm.get("rects") or ([rm["rect"]] if "rect" in rm else None)
        if not isinstance(rects, list) or not rects:
            raise InputError(f"{name}: give `rect` [x, y, width, depth] or `rects`")
        clean = []
        for r in rects:
            if not isinstance(r, list) or len(r) != 4:
                raise InputError(f"{name}: each rectangle is [x, y, width, depth]")
            r = [number(v, f"{name}: rectangle") for v in r]
            if r[2] <= EPS or r[3] <= EPS:
                raise InputError(f"{name}: rectangle width and depth must be above zero")
            clean.append(r)
        t = rm.get("target_area")
        mw = rm.get("min_width")
        rooms.append({"name": name, "rects": clean,
                      "target": number(t, f"{name}: target_area") if t is not None else None,
                      "min_width": number(mw, f"{name}: min_width") if mw is not None else None,
                      "habitable": bool(rm.get("habitable", False))})
    if not rooms:
        raise InputError("`rooms` must list at least one room")
    names = {r["name"].lower(): r["name"] for r in rooms}
    doors = []
    for i, d in enumerate(data.get("doors") or [], 1):
        if not isinstance(d, dict):
            raise InputError(f"door {i} must be an object")
        btw = d.get("between")
        if not isinstance(btw, list) or len(btw) != 2 or not all(isinstance(b, str) for b in btw):
            raise InputError(f"door {i}: `between` must name two rooms (or a room and \"outside\")")
        resolved = []
        for b in btw:
            if b.lower() == "outside":
                resolved.append("outside")
            elif b.lower() in names:
                resolved.append(names[b.lower()])
            else:
                raise InputError(f"door {i}: no room called {b!r}")
        at = d.get("at")
        if not isinstance(at, list) or len(at) != 2:
            raise InputError(f"door {i}: `at` must be the [x, y] of the door's centre")
        doors.append({"between": resolved, "at": (number(at[0], "door x"), number(at[1], "door y")),
                      "width": number(d.get("width", 0.9 if units == "m" else 3.0), f"door {i}: width")})
    windows = []
    for i, w in enumerate(data.get("windows") or [], 1):
        if not isinstance(w, dict) or str(w.get("room", "")).lower() not in names:
            raise InputError(f"window {i}: `room` must name a room")
        at = w.get("at")
        if not isinstance(at, list) or len(at) != 2:
            raise InputError(f"window {i}: `at` must be the [x, y] of the window's centre")
        windows.append({"room": names[w["room"].lower()], "at": (number(at[0], "window x"), number(at[1], "window y")),
                        "width": number(w.get("width", 1.2 if units == "m" else 4.0), f"window {i}: width")})
    default_door = 0.8 if units == "m" else 32 / 12
    return {"units": units, "title": str(data.get("title", "Floor plan")), "outline": outline,
            "rooms": rooms, "doors": doors, "windows": windows,
            "min_door_width": number(data.get("min_door_width", default_door), "min_door_width"),
            "tolerance": number(data.get("tolerance", 0.10), "tolerance"),
            "north": number(data.get("north", 0), "north"),
            "wall": number(data.get("wall", 0.2 if units == "m" else 0.5), "wall")}


def check(plan):
    fails, warns = [], []
    rooms, outline = plan["rooms"], plan["outline"]
    by_name = {r["name"]: r for r in rooms}
    for r in rooms:
        r["area"] = sum(x[2] * x[3] for x in r["rects"])
        r["area"] -= sum(overlap(a, b) for i, a in enumerate(r["rects"]) for b in r["rects"][i + 1:])
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            ov = sum(overlap(x, y) for x in a["rects"] for y in b["rects"])
            if ov > EPS:
                fails.append(f"{a['name']} and {b['name']} overlap by {ov:.2f}")
    for r in rooms:
        if not all(rect_in_poly(x, outline) for x in r["rects"]):
            fails.append(f"{r['name']} runs outside the outline")
        if r["target"]:
            off = (r["area"] - r["target"]) / r["target"]
            if abs(off) > plan["tolerance"] + EPS:
                warns.append(f"{r['name']}: {r['area']:.1f} against a target of {r['target']:g} ({off * 100:+.0f} %)")
        if r["min_width"] is not None:
            narrow = min(min(x[2], x[3]) for x in r["rects"])
            if narrow < r["min_width"] - EPS:
                warns.append(f"{r['name']}: {narrow:g} wide, under its minimum width {r['min_width']:g}")
    graph = {r["name"]: set() for r in rooms}
    graph["outside"] = set()
    for i, d in enumerate(plan["doors"], 1):
        a, b = d["between"]
        label = f"door {i} ({a} – {b})"
        if a == b:
            fails.append(f"{label} joins a room to itself")
            continue
        ok = True
        for side in (a, b):
            if side == "outside":
                ok = ok and on_outline(d["at"], outline)
            else:
                ok = ok and any(on_rect_edge(d["at"], x) for x in by_name[side]["rects"])
        if not ok:
            fails.append(f"{label} at ({d['at'][0]:g}, {d['at'][1]:g}) is not on a wall both sides share")
            continue
        if d["width"] < plan["min_door_width"] - EPS:
            warns.append(f"{label} is {d['width']:g} wide, under {plan['min_door_width']:.2f}")
        graph[a].add(b)
        graph[b].add(a)
    if not graph["outside"]:
        fails.append("no door to outside: the plan has no entrance")
    else:
        seen, todo = {"outside"}, ["outside"]
        while todo:
            for n in graph[todo.pop()]:
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        for r in rooms:
            if r["name"] not in seen:
                fails.append(f"{r['name']} cannot be reached from an entrance")
    for w in plan["windows"]:
        if not on_outline(w["at"], outline) or not any(on_rect_edge(w["at"], x) for x in by_name[w["room"]]["rects"]):
            warns.append(f"window in {w['room']} at ({w['at'][0]:g}, {w['at'][1]:g}) is not on an outside wall of that room")
    lit = {w["room"] for w in plan["windows"] if on_outline(w["at"], outline)}
    for r in rooms:
        if r["habitable"] and r["name"] not in lit:
            warns.append(f"{r['name']} is habitable but has no window on an outside wall")
    out_area = poly_area(outline)
    room_area = sum(r["area"] for r in rooms)
    spare = out_area - room_area
    if out_area > 0 and spare / out_area > 0.05 + EPS:
        warns.append(f"{spare:.1f} ({spare / out_area * 100:.0f} %) of the outline is in no room; label it (hall, stair, shaft) or remove it")
    return {"fails": fails, "warns": warns, "outline_area": out_area, "room_area": room_area}


def report(plan, r):
    a = "m²" if plan["units"] == "m" else "sq ft"
    u = plan["units"]
    L = [f"# {plan['title']}: plan check", "", f"| Room | Size ({u}) | Area ({a}) | Target ({a}) |", "|---|---|---:|---:|"]
    for rm in plan["rooms"]:
        size = " + ".join(f"{x[2]:g} × {x[3]:g}" for x in rm["rects"])
        L.append(f"| {rm['name']} | {size} | {rm['area']:.1f} | {rm['target'] if rm['target'] is not None else ''} |")
    L += [f"| **Rooms** | | **{r['room_area']:.1f}** | |",
          f"| **Outline** | | **{r['outline_area']:.1f}** | |", ""]
    if not r["fails"]:
        L.append("PASS no overlaps, every door on a shared wall, every room reachable.")
    L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    return "\n".join(L) + "\n"


# ---------- drawing ----------

def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(plan, r, draw=760):
    o, u = plan["outline"], plan["units"]
    xs, ys = [p[0] for p in o], [p[1] for p in o]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    s = draw / max(x1 - x0, y1 - y0)
    m = 80
    W = (x1 - x0) * s + 2 * m + 40
    H = (y1 - y0) * s + 2 * m + 70
    am = "m²" if u == "m" else "sq ft"

    def P(x, y):
        return (m + (x - x0) * s, H - m - 30 - (y - y0) * s)

    def pts(poly):
        return " ".join("%.1f,%.1f" % P(*p) for p in poly)

    wall = max(plan["wall"] * s, 2)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" '
           'font-family="Helvetica, Arial, sans-serif" font-size="11">',
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff"/>',
           f'<text x="20" y="28" font-size="16" font-weight="bold">{esc(plan["title"])}</text>',
           f'<text x="20" y="46" fill="#444">Rooms {r["room_area"]:.1f} {am} · outline {r["outline_area"]:.1f} {am} · schematic, not for construction</text>']
    fills = ["#eef4f1", "#f5f0e6", "#eef0f6", "#f6eef0", "#f0f6ee", "#f3f3f3"]
    for i, rm in enumerate(plan["rooms"]):
        for x, y, w, h in rm["rects"]:
            X, Y = P(x, y + h)
            out.append(f'<rect x="{X:.1f}" y="{Y:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" fill="{fills[i % len(fills)]}"/>')
    for rm in plan["rooms"]:
        for (ax, ay), (bx, by) in room_walls(rm["rects"]):
            A, B = P(ax, ay), P(bx, by)
            out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#333" stroke-width="{wall / 2:.1f}" stroke-linecap="square"/>')
    out.append(f'<polygon points="{pts(o)}" fill="none" stroke="#111" stroke-width="{wall:.1f}" stroke-linejoin="miter"/>')
    for rm in plan["rooms"]:
        x, y, w, h = max(rm["rects"], key=lambda q: q[2] * q[3])
        X, Y = P(x + w / 2, y + h / 2)
        size = " + ".join(f"{q[2]:g}×{q[3]:g}" for q in rm["rects"]) + f" · {rm['area']:.1f} {am}"
        fs = 12 if min(w, h) * s > 60 else 9
        if len(size) * (fs - 1) * 0.55 > w * s - 6:
            size = f"{rm['area']:.1f} {am}"
        out.append(f'<text x="{X:.1f}" y="{Y - 4:.1f}" text-anchor="middle" font-weight="bold" font-size="{fs}">{esc(rm["name"])}</text>')
        out.append(f'<text x="{X:.1f}" y="{Y + 9:.1f}" text-anchor="middle" font-size="{fs - 1}" fill="#444">{size}</text>')
    for w in plan["windows"]:
        out += opening(P, s, w["at"], w["width"], plan, wall, window=True)
    for d in plan["doors"]:
        out += opening(P, s, d["at"], d["width"], plan, wall, window=False)
    # overall dimension strings
    bx, by = P(x0, y0)
    ex, _ = P(x1, y0)
    out += dim_line(bx, by + 28, ex, by + 28, f"{x1 - x0:g} {u}")
    _, ty = P(x0, y1)
    out += dim_line(bx - 28, by, bx - 28, ty, f"{y1 - y0:g} {u}", vertical=True)
    out += north(W - 40, 40, plan["north"]) + scale(m, H - 18, s, max(x1 - x0, y1 - y0), u)
    out.append("</svg>")
    return "\n".join(out)


def opening(P, s, at, width, plan, wall, window):
    """A door (gap plus swing) or window (gap plus glazing lines), on whichever wall it sits."""
    vertical = is_vertical(at, plan)
    x, y = at
    half = width / 2
    a = P(x, y - half) if vertical else P(x - half, y)
    b = P(x, y + half) if vertical else P(x + half, y)
    out = [f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#fff" stroke-width="{wall + 1:.1f}"/>']
    if window:
        for off in (-wall / 3, 0, wall / 3):
            dx, dy = (off, 0) if vertical else (0, off)
            out.append(f'<line x1="{a[0] + dx:.1f}" y1="{a[1] + dy:.1f}" x2="{b[0] + dx:.1f}" y2="{b[1] + dy:.1f}" stroke="#2b6cb0" stroke-width="1"/>')
    else:
        r = width * s
        if vertical:
            leaf = (a[0] + r, a[1])
            out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{leaf[0]:.1f}" y2="{leaf[1]:.1f}" stroke="#b5531a" stroke-width="1.5"/>')
            out.append(f'<path d="M {leaf[0]:.1f} {leaf[1]:.1f} A {r:.1f} {r:.1f} 0 0 0 {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="#b5531a" stroke-width="0.8" stroke-dasharray="3 2"/>')
        else:
            leaf = (a[0], a[1] - r)
            out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{leaf[0]:.1f}" y2="{leaf[1]:.1f}" stroke="#b5531a" stroke-width="1.5"/>')
            out.append(f'<path d="M {leaf[0]:.1f} {leaf[1]:.1f} A {r:.1f} {r:.1f} 0 0 1 {b[0]:.1f} {b[1]:.1f}" fill="none" stroke="#b5531a" stroke-width="0.8" stroke-dasharray="3 2"/>')
    return out


def room_walls(rects):
    """Each rectangle's edges, less the stretches it shares with another rectangle of the same room."""
    walls = []
    for i, (x, y, w, h) in enumerate(rects):
        others = [q for j, q in enumerate(rects) if j != i]
        for fixed, lo, hi, horizontal, side in ((y, x, x + w, True, -1), (y + h, x, x + w, True, 1),
                                                (x, y, y + h, False, -1), (x + w, y, y + h, False, 1)):
            cover = []
            for ox, oy, ow, oh in others:
                if horizontal and abs((oy + oh if side < 0 else oy) - fixed) < EPS:
                    cover.append((ox, ox + ow))
                if not horizontal and abs((ox + ow if side < 0 else ox) - fixed) < EPS:
                    cover.append((oy, oy + oh))
            pieces = [(lo, hi)]
            for c0, c1 in cover:
                nxt = []
                for p0, p1 in pieces:
                    if c1 <= p0 + EPS or c0 >= p1 - EPS:
                        nxt.append((p0, p1))
                        continue
                    if c0 > p0 + EPS:
                        nxt.append((p0, c0))
                    if c1 < p1 - EPS:
                        nxt.append((c1, p1))
                pieces = nxt
            for p0, p1 in pieces:
                walls.append(((p0, fixed), (p1, fixed)) if horizontal else ((fixed, p0), (fixed, p1)))
    return walls


def is_vertical(at, plan):
    """Whether the wall under a point runs north-south, judged from the rectangle edges and outline it sits on."""
    segs = [e for rm in plan["rooms"] for q in rm["rects"] for e in rect_edges(q)]
    o = plan["outline"]
    segs += [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]
    for a, b in segs:
        if on_segment(at, a, b):
            return abs(b[0] - a[0]) < abs(b[1] - a[1])
    return False


def dim_line(x1, y1, x2, y2, label, vertical=False):
    out = [f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#555" stroke-width="0.8"/>']
    for x, y in ((x1, y1), (x2, y2)):
        out.append(f'<line x1="{x - 4:.1f}" y1="{y + 4:.1f}" x2="{x + 4:.1f}" y2="{y - 4:.1f}" stroke="#555" stroke-width="1.2"/>')
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if vertical:
        out.append(f'<text x="{mx - 6:.1f}" y="{my:.1f}" text-anchor="middle" transform="rotate(-90 {mx - 6:.1f} {my:.1f})">{esc(label)}</text>')
    else:
        out.append(f'<text x="{mx:.1f}" y="{my - 5:.1f}" text-anchor="middle">{esc(label)}</text>')
    return out


def north(x, y, deg):
    return [f'<g transform="translate({x:.0f} {y:.0f}) rotate({deg:.1f})"><polygon points="0,-20 7,9 0,4 -7,9" fill="#111"/>'
            '<text x="0" y="-25" text-anchor="middle" font-weight="bold">N</text></g>']


def scale(x, y, s, span, u):
    step = 1.0
    for mlt in (1, 2, 5):
        for e in range(-1, 5):
            v = mlt * 10 ** e
            if step < v <= span / 5:
                step = v
    w = step * s
    return [f'<rect x="{x}" y="{y - 6:.1f}" width="{w / 2:.1f}" height="6" fill="#111"/>',
            f'<rect x="{x + w / 2:.1f}" y="{y - 6:.1f}" width="{w / 2:.1f}" height="6" fill="#fff" stroke="#111"/>',
            f'<text x="{x + w + 6:.1f}" y="{y:.1f}">{step:g} {u}</text>']


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a schematic floor plan and draw it.")
    ap.add_argument("plan")
    ap.add_argument("--svg", help="write the dimensioned plan here")
    args = ap.parse_args(argv)
    try:
        with open(args.plan, encoding="utf-8-sig") as f:
            plan = load(json.load(f))
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"FAIL cannot read {args.plan}: {e}")
        return 2
    except InputError as e:
        print(f"FAIL {e}")
        return 2
    r = check(plan)
    print(report(plan, r), end="")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(plan, r))
        print(f"\nWrote {args.svg}")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

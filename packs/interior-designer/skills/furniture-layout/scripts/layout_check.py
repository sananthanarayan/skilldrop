#!/usr/bin/env python3
"""Check a room's furniture layout and draw it as a dimensioned SVG. Stdlib only.

Reads a layout.json: the room's outline (a rectangle or a rectilinear polygon), its doors
with their swing, its windows with their sill height, fixed obstacles (columns, radiators)
and the furniture, each piece with a type, a size, a position and the way its front faces.
It fails a layout where
  - two pieces overlap, a piece runs outside the room or sits on an obstacle
  - a piece sits in the swing of a door that opens into the room
  - a piece's use clearance (a bed side, a chair pull-back, a desk chair, a wardrobe door,
    a sofa's legroom) is blocked by another piece, an obstacle or a wall
  - there is no clear route at the walkway width from an entrance door to each piece's
    access side, or nothing clears the first stretch inside an entrance
  - with "accessible": true, there is no clear 1.5 m turning circle the route reaches
  - a turning circle named in "turning_circles" is not clear, or no route reaches it. Give it
    at a point ({"at": [x, y]}) or tied to a place ({"near": "WC door", "side": "front",
    "within": 1.0}): a place-tied circle is searched for only in that zone, so a circle clear
    somewhere else in the room never passes it. "diameter" defaults to 1.5 m
and warns where
  - a piece taller than a window's sill stands in front of the window
  - the furniture covers more of the floor than max_coverage (default 50 %)
  - a piece stands against a radiator
Then it draws the plan: walls, door swings, windows, obstacles, every piece with its name
and size, use clearances shaded, the walking routes, failures in red, overall dimension
strings, a scale bar and a north arrow.

Routes are found on a grid of 2.5 to 10 cm, so a gap is measured to within one grid step.
A room up to 60 m across checks in a second or two; --max-seconds (default 20) stops the
route and turning checks if they run long, and says so.

Usage:
  python3 layout_check.py layout.json [--svg layout.svg] [--json] [--max-seconds 20]
Exit codes: 0 no failures, 1 a failure, 2 bad input or a check that didn't finish.
"""
import argparse
import json
import math
import sys
import time
from collections import deque

EPS = 1e-6
FT = 0.3048

# Use clearances (metres) by type, measured from the piece's sides as seen from its front:
# front, back, left, right. "access" says which clearance the walking route has to reach:
# "front", "sides" (every side with a clearance), "any" (at least one), or None.
TYPES = {
    "bed":          {"left": 0.6, "right": 0.6, "front": 0.6, "height": 0.6, "access": "sides"},
    "single_bed":   {"right": 0.6, "front": 0.5, "height": 0.6, "access": "any"},
    "sofa":         {"front": 0.35, "height": 0.85, "access": "front"},
    "armchair":     {"front": 0.35, "height": 0.9, "access": "front"},
    "coffee_table": {"height": 0.45, "access": None},
    "side_table":   {"height": 0.55, "access": None},
    "nightstand":   {"height": 0.55, "access": None},
    "dining_table": {"front": 0.9, "back": 0.9, "left": 0.9, "right": 0.9, "height": 0.75, "access": "any"},
    "desk":         {"front": 0.9, "height": 0.75, "access": "front"},
    "wardrobe":     {"front": 0.6, "height": 2.0, "access": "front"},
    "dresser":      {"front": 0.6, "height": 0.85, "access": "front"},
    "sideboard":    {"front": 0.6, "height": 0.85, "access": "front"},
    "bookcase":     {"front": 0.45, "height": 1.8, "access": "front"},
    "tv_unit":      {"height": 0.5, "access": None},
    "rug":          {"height": 0.0, "access": None},
    "other":        {"height": 0.75, "access": None},
}
SIDES = ("front", "back", "left", "right")
FACING = {"S": 0, "E": 90, "N": 180, "W": 270}
BED_HEAD = 0.55  # a bed's side clearance starts this far from the head, where nightstands go


class InputError(Exception):
    pass


class TimeUp(Exception):
    """The route and turning checks ran past --max-seconds."""


DEADLINE = None   # time.monotonic() after which the long checks stop; set by main


def tick():
    if DEADLINE is not None and time.monotonic() > DEADLINE:
        raise TimeUp()


def number(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise InputError(f"{what} must be a number")
    if abs(v) > 1000:
        raise InputError(f"{what} is {v:g}; nothing in one room is over 1000 across")
    return float(v)


def positive(v, what):
    v = number(v, what)
    if v <= EPS:
        raise InputError(f"{what} must be above zero")
    return v


# ---------- geometry ----------

def on_segment(p, a, b, tol=1e-4):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    L = math.hypot(x2 - x1, y2 - y1)
    if L < EPS:
        return math.hypot(x - x1, y - y1) <= tol
    cross = abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) / L
    dot = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / L
    return cross <= tol and -tol <= dot <= L + tol


def point_in_poly(p, poly):
    x, y = p
    inside = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        if on_segment(p, (x1, y1), (x2, y2)):
            return True
        if (y1 > y) != (y2 > y):
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x:
                inside = not inside
    return inside


def poly_area(poly):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2


def overlap(a, b):
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > EPS and h > EPS else 0.0


def rect_in_poly(r, poly):
    x, y, w, h = r
    if not all(point_in_poly(c, poly) for c in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))):
        return False
    return not any(x + EPS < px < x + w - EPS and y + EPS < py < y + h - EPS for px, py in poly)


def rect_gap(a, b):
    """Shortest distance between two rectangles (0 when they touch or overlap)."""
    dx = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]), 0)
    dy = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), 0)
    return math.hypot(dx, dy)


def inward_normal(a, b, poly):
    """The unit normal of wall a-b that points into the room."""
    tx, ty = b[0] - a[0], b[1] - a[1]
    L = math.hypot(tx, ty)
    n = (-ty / L, tx / L)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    probe = (mid[0] + n[0] * 0.01, mid[1] + n[1] * 0.01)
    return n if point_in_poly(probe, poly) and not on_segment(probe, a, b) else (-n[0], -n[1])


def wall_at(p, poly):
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if on_segment(p, a, b):
            return a, b
    return None


# ---------- input ----------

MAX_SPAN = 60.0  # metres; a bigger "room" is a floor, and the route grid would grow past what's useful


def items(data, key):
    v = data.get(key)
    if v is None:
        return []
    if not isinstance(v, list):
        raise InputError(f"`{key}` must be a list")
    return v


def load(data):
    if not isinstance(data, dict):
        raise InputError("layout.json must be a JSON object")
    units = data.get("units", "m")
    if units not in ("m", "ft"):
        raise InputError("`units` must be \"m\" or \"ft\"")
    k = FT if units == "ft" else 1.0

    def L(v, what):
        return number(v, what) * k

    if "size" in data and "outline" not in data:
        s = data["size"]
        if not isinstance(s, list) or len(s) != 2:
            raise InputError("`size` must be [width, depth]")
        w, d = positive(s[0], "size width") * k, positive(s[1], "size depth") * k
        outline = [(0.0, 0.0), (w, 0.0), (w, d), (0.0, d)]
    else:
        o = data.get("outline")
        if not isinstance(o, list) or len(o) < 4:
            raise InputError("give `size` [width, depth] or an `outline` of at least four [x, y] corners")
        try:
            outline = [(L(p[0], "outline x"), L(p[1], "outline y")) for p in o]
        except (TypeError, IndexError, KeyError):
            raise InputError("every corner in `outline` must be [x, y]")
        for i, a in enumerate(outline):
            b = outline[(i + 1) % len(outline)]
            if abs(a[0] - b[0]) > EPS and abs(a[1] - b[1]) > EPS:
                raise InputError("the outline must be rectilinear: every wall runs along x or along y")
        if poly_area(outline) <= EPS:
            raise InputError("the outline encloses no floor")
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    if max(xs) - min(xs) > MAX_SPAN or max(ys) - min(ys) > MAX_SPAN:
        raise InputError(f"the room is more than {MAX_SPAN:g} m across; lay out one room at a time")

    doors = []
    for i, d in enumerate(items(data, "doors"), 1):
        if not isinstance(d, dict) or not isinstance(d.get("at"), list) or len(d["at"]) != 2:
            raise InputError(f"door {i}: `at` must be the [x, y] of the door's centre on a wall")
        hinge = d.get("hinge", "left")
        swing = d.get("swing", "in")
        if hinge not in ("left", "right") or swing not in ("in", "out", "sliding"):
            raise InputError(f"door {i}: `hinge` is left or right, `swing` is in, out or sliding")
        doors.append({"name": str(d.get("name") or f"Door {i}"), "at": (L(d["at"][0], "door x"), L(d["at"][1], "door y")),
                      "width": positive(d.get("width", 0.9 / k), f"door {i}: width") * k,
                      "hinge": hinge, "swing": swing, "entrance": bool(d.get("entrance", False))})
    if not doors:
        raise InputError("`doors` must list at least one door, so the route has somewhere to start")
    if not any(d["entrance"] for d in doors):
        for d in doors:
            d["entrance"] = True

    windows = []
    for i, w in enumerate(items(data, "windows"), 1):
        if not isinstance(w, dict) or not isinstance(w.get("at"), list) or len(w["at"]) != 2:
            raise InputError(f"window {i}: `at` must be the [x, y] of the window's centre on a wall")
        windows.append({"at": (L(w["at"][0], "window x"), L(w["at"][1], "window y")),
                        "width": positive(w.get("width", 1.2 / k), f"window {i}: width") * k,
                        "sill": number(w.get("sill", 0.9 / k), f"window {i}: sill") * k})

    obstacles = []
    for i, o in enumerate(items(data, "obstacles"), 1):
        if not isinstance(o, dict) or not isinstance(o.get("rect"), list) or len(o["rect"]) != 4:
            raise InputError(f"obstacle {i}: `rect` must be [x, y, width, depth]")
        r = [L(v, f"obstacle {i}") for v in o["rect"]]
        if r[2] <= EPS or r[3] <= EPS:
            raise InputError(f"obstacle {i}: width and depth must be above zero")
        kind = str(o.get("type", "column"))
        obstacles.append({"name": str(o.get("name") or kind.capitalize()), "type": kind, "rect": r})

    pieces, seen = [], set()
    for i, f in enumerate(items(data, "furniture"), 1):
        if not isinstance(f, dict) or not str(f.get("name", "")).strip():
            raise InputError(f"furniture {i} needs a `name`")
        name = str(f["name"]).strip()
        if name.lower() in seen:
            raise InputError(f"two pieces are called {name!r}")
        seen.add(name.lower())
        kind = f.get("type", "other")
        if not isinstance(kind, str) or kind not in TYPES:
            raise InputError(f"{name}: unknown type {kind!r}; use one of {', '.join(sorted(TYPES))}")
        if not isinstance(f.get("at"), list) or len(f["at"]) != 2:
            raise InputError(f"{name}: `at` must be the [x, y] of the piece's corner nearest the origin")
        if "facing" in f:
            if not isinstance(f["facing"], str) or f["facing"] not in FACING:
                raise InputError(f"{name}: `facing` is N, S, E or W")
            rot = FACING[f["facing"]]
        else:
            rot = int(number(f.get("rotation", 0), f"{name}: rotation")) % 360
            if rot not in (0, 90, 180, 270):
                raise InputError(f"{name}: rotation must be 0, 90, 180 or 270")
        w = positive(f.get("width"), f"{name}: width") * k
        dpt = positive(f.get("depth"), f"{name}: depth") * k
        x, y = L(f["at"][0], f"{name}: x"), L(f["at"][1], f"{name}: y")
        rect = [x, y, w, dpt] if rot in (0, 180) else [x, y, dpt, w]
        spec = TYPES[kind]
        clear = {s: spec.get(s, 0.0) for s in SIDES}
        given = f.get("clearance") or {}
        if not isinstance(given, dict) or any(s not in SIDES for s in given):
            raise InputError(f"{name}: `clearance` takes front, back, left and right")
        for s, v in given.items():
            clear[s] = number(v, f"{name}: clearance {s}") * k
        access = f.get("access", spec["access"])
        if access not in ("front", "sides", "any", None, False):
            raise InputError(f"{name}: `access` is front, sides, any or false")
        pieces.append({"name": name, "type": kind, "rect": rect, "rot": rot, "size": (w, dpt),
                       "height": number(f.get("height", spec["height"] / k), f"{name}: height") * k,
                       "clear": clear, "access": access or None})
    if not pieces:
        raise InputError("`furniture` must list at least one piece")

    turning = []
    raw_tc = data.get("turning_circles") or []
    if not isinstance(raw_tc, list):
        raise InputError("`turning_circles` must be a list of {\"at\": [x, y]} or {\"near\": \"door or piece\"}")
    doors_by = {d["name"].lower(): d for d in doors}
    pieces_by = {p["name"].lower(): p for p in pieces}
    for t in raw_tc:
        if not isinstance(t, dict):
            raise InputError("each turning circle needs `at` as [x, y], or `near` naming a door or a piece")
        diam = positive(t.get("diameter", 1.5 / k), "turning circle diameter") * k
        who = str(t.get("for", "turning space"))
        at = t.get("at")
        if at is not None:
            if not isinstance(at, (list, tuple)) or len(at) != 2:
                raise InputError("each turning circle needs `at` as [x, y], or `near` naming a door or a piece")
            turning.append({"at": (number(at[0], "turning circle x") * k, number(at[1], "turning circle y") * k),
                            "for": who, "d": diam})
            continue
        near = t.get("near")
        if not isinstance(near, str) or not near.strip():
            raise InputError("each turning circle needs `at` as [x, y], or `near` naming a door or a piece")
        side = t.get("side", "any")
        if side not in ("front", "back", "left", "right", "any"):
            raise InputError(f"turning circle near {near!r}: `side` is front, back, left, right or any")
        target = doors_by.get(near.strip().lower()) or pieces_by.get(near.strip().lower())
        if target is None:
            raise InputError(f"turning circle near {near!r}: no door or piece has that name")
        kind = "door" if near.strip().lower() in doors_by else "piece"
        if kind == "door" and side == "back":
            raise InputError(f"turning circle near {near!r}: a door's `side` is front, left, right or any")
        within = positive(t.get("within", diam / k), f"turning circle near {near!r}: within") * k
        turning.append({"near": target["name"], "kind": kind, "side": side, "within": within, "for": who, "d": diam})

    walkway = positive(data.get("min_walkway", 0.9 / k), "min_walkway") * k
    accessible = bool(data.get("accessible", False))
    if accessible:
        walkway = max(walkway, 0.9)
    return {"units": units, "k": k, "title": str(data.get("title", "Furniture layout")), "outline": outline,
            "doors": doors, "windows": windows, "obstacles": obstacles, "pieces": pieces,
            "walkway": walkway, "accessible": accessible, "turning_circles": turning,
            "max_coverage": number(data.get("max_coverage", 0.5), "max_coverage"),
            "north": number(data.get("north", 0), "north")}


# ---------- a piece's frame ----------

def frame(p):
    """front, right and back unit vectors (right as seen standing at the front, facing the piece)."""
    f = {0: (0, -1), 90: (1, 0), 180: (0, 1), 270: (-1, 0)}[p["rot"]]
    return {"front": f, "back": (-f[0], -f[1]), "right": (-f[1], f[0]), "left": (f[1], -f[0])}


def side_zone(rect, direction, depth):
    x, y, w, h = rect
    return {(0, -1): (x, y - depth, w, depth), (0, 1): (x, y + h, w, depth),
            (1, 0): (x + w, y, depth, h), (-1, 0): (x - depth, y, depth, h)}[direction]


def zones(p):
    """Each use clearance as (side, rect). A bed's sides start clear of the head, where nightstands go."""
    out = []
    fr = frame(p)
    for s in SIDES:
        d = p["clear"][s]
        if d <= EPS:
            continue
        z = side_zone(p["rect"], fr[s], d)
        if p["type"] in ("bed", "single_bed") and s in ("left", "right"):
            z = trim_bed(p, z)
        out.append((s, z))
    return out


def chairs(p):
    """The chairs a dining table or desk implies, as rects in its clearance zone, so the drawing
    shows every seat. Drawn only: the clearance zone is what the check keeps free for them."""
    if p["type"] not in ("dining_table", "desk"):
        return []
    fr, out = frame(p), []
    cw, cd, gap = 0.45, 0.45, 0.05
    sides = ["front"] if p["type"] == "desk" else ["front", "back"]
    x, y, w, h = p["rect"]
    for side in sides:
        if p["clear"].get(side, 0) < cd - EPS and p["type"] == "dining_table":
            continue
        d = fr[side]
        along_x = d[1] != 0          # the side runs along x when its normal is vertical
        span = w if along_x else h
        n = 1 if p["type"] == "desk" else max(1, int((span + EPS) // 0.6))
        step = span / n
        for k in range(n):
            c = (x if along_x else y) + step * (k + 0.5)
            if along_x:
                cy = y - gap - cd if d == (0, -1) else y + h + gap
                out.append((c - cw / 2, cy, cw, cd))
            else:
                cx = x - gap - cd if d == (-1, 0) else x + w + gap
                out.append((cx, c - cw / 2, cd, cw))
    return out


def trim_bed(p, z):
    """Cut the head end off a bed's side clearance."""
    back = frame(p)["back"]
    x, y, w, h = z
    if back[0]:                       # the bed runs along x; its head is at +x or -x
        cut = min(BED_HEAD, w / 2)
        return (x, y, w - cut, h) if back[0] > 0 else (x + cut, y, w - cut, h)
    cut = min(BED_HEAD, h / 2)
    return (x, y, w, h - cut) if back[1] > 0 else (x, y + cut, w, h - cut)


# ---------- the checks ----------

def door_geometry(d, outline):
    wall = wall_at(d["at"], outline)
    if not wall:
        return None
    a, b = wall
    n = inward_normal(a, b, outline)
    t = ((b[0] - a[0]), (b[1] - a[1]))
    tl = math.hypot(*t)
    t = (t[0] / tl, t[1] / tl)
    # standing inside facing the door, you look along d = -n; your right hand is (d.y, -d.x) = (-n.y, n.x)
    right = (-n[1], n[0])
    half = d["width"] / 2
    side = 1 if d["hinge"] == "right" else -1
    hinge = (d["at"][0] + right[0] * half * side, d["at"][1] + right[1] * half * side)
    latch = (d["at"][0] - right[0] * half * side, d["at"][1] - right[1] * half * side)
    return {"n": n, "t": t, "hinge": hinge, "latch": latch}


def in_swing(pt, d, g):
    if d["swing"] != "in":
        return False
    vx, vy = pt[0] - g["hinge"][0], pt[1] - g["hinge"][1]
    if math.hypot(vx, vy) >= d["width"] - 1e-3:
        return False
    lx, ly = g["latch"][0] - g["hinge"][0], g["latch"][1] - g["hinge"][1]
    return vx * g["n"][0] + vy * g["n"][1] > 1e-3 and vx * lx + vy * ly > -1e-3


def rect_in_swing(r, d, g, step=0.025):
    x, y, w, h = r
    nx, ny = max(2, int(w / step) + 1), max(2, int(h / step) + 1)
    return any(in_swing((x + w * i / (nx - 1), y + h * j / (ny - 1)), d, g) for i in range(nx) for j in range(ny))


def edt1(f):
    """1-D squared distance transform of a sampled function (Felzenszwalb and Huttenlocher)."""
    n = len(f)
    d, v, z = [0.0] * n, [0] * n, [0.0] * (n + 1)
    k, z[0], z[1] = 0, -1e30, 1e30
    for q in range(1, n):
        s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        while s <= z[k]:
            k -= 1
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
        k += 1
        v[k], z[k], z[k + 1] = q, s, 1e30
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


class Grid(object):
    def __init__(self, plan):
        xs, ys = [p[0] for p in plan["outline"]], [p[1] for p in plan["outline"]]
        self.x0, self.y0 = min(xs), min(ys)
        span = (max(xs) - self.x0) * (max(ys) - self.y0)
        self.c = 0.025 if span <= 60 else 0.05 if span <= 250 else 0.1
        # one cell of outside all round, so the walls count as obstacles in the distance transform
        self.x0, self.y0 = self.x0 - self.c, self.y0 - self.c
        self.nx = int(math.ceil((max(xs) - self.x0) / self.c)) + 1
        self.ny = int(math.ceil((max(ys) - self.y0) / self.c)) + 1
        self.blocked = [[False] * self.nx for _ in range(self.ny)]
        for j in range(self.ny):
            tick()
            yc = self.y0 + (j + 0.5) * self.c
            # scanline: the outline's crossings at this height
            xs_in = []
            o = plan["outline"]
            for i, (x1, y1) in enumerate(o):
                x2, y2 = o[(i + 1) % len(o)]
                if (y1 > yc) != (y2 > yc):
                    xs_in.append(x1 + (yc - y1) * (x2 - x1) / (y2 - y1))
            xs_in.sort()
            row = self.blocked[j]
            for i in range(self.nx):
                xc = self.x0 + (i + 0.5) * self.c
                row[i] = sum(1 for v in xs_in if v < xc) % 2 == 0
        for r in [p["rect"] for p in plan["pieces"] if p["type"] != "rug"] + [o["rect"] for o in plan["obstacles"]]:
            self.fill(r)

    def cell(self, x, y):
        return int((x - self.x0) / self.c), int((y - self.y0) / self.c)

    def centre(self, i, j):
        return self.x0 + (i + 0.5) * self.c, self.y0 + (j + 0.5) * self.c

    def fill(self, r):
        x, y, w, h = r
        i0 = max(0, int(math.floor((x - self.x0) / self.c + 0.5 - EPS)))
        i1 = min(self.nx - 1, int(math.ceil((x + w - self.x0) / self.c - 0.5 + EPS)) - 1)
        j0 = max(0, int(math.floor((y - self.y0) / self.c + 0.5 - EPS)))
        j1 = min(self.ny - 1, int(math.ceil((y + h - self.y0) / self.c - 0.5 + EPS)) - 1)
        for j in range(j0, j1 + 1):
            row = self.blocked[j]
            for i in range(i0, i1 + 1):
                row[i] = True

    def distances(self):
        """Euclidean distance, in metres, from each cell's centre to the nearest blocked cell's
        centre (Felzenszwalb and Huttenlocher's two-pass transform)."""
        if getattr(self, "_dist", None) is None:
            INF = float(self.nx * self.nx + self.ny * self.ny)
            cols = []
            for i in range(self.nx):
                tick()
                cols.append(edt1([0.0 if self.blocked[j][i] else INF for j in range(self.ny)]))
            rows = []
            for j in range(self.ny):
                tick()
                rows.append(edt1([cols[i][j] for i in range(self.nx)]))
            self._dist = [[math.sqrt(v) * self.c for v in row] for row in rows]
        return self._dist

    def clear(self, width):
        """Cells where a walker `width` across (a disc) stands clear of everything, to within a grid step."""
        dist, r = self.distances(), width / 2
        return [[dist[j][i] >= r - 1e-9 for i in range(self.nx)] for j in range(self.ny)]

    def reach(self, ok, starts):
        parent = {}
        q = deque()
        for s in starts:
            parent[s] = None
            q.append(s)
        n = 0
        while q:
            n += 1
            if n % 4096 == 0:
                tick()
            i, j = q.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                a, b = i + di, j + dj
                if 0 <= a < self.nx and 0 <= b < self.ny and ok[b][a] and (a, b) not in parent:
                    if di and dj and not (ok[j][a] and ok[b][i]):
                        continue
                    parent[(a, b)] = (i, j)
                    q.append((a, b))
        return parent


def check(plan):
    fails, warns = [], []
    pieces, outline = plan["pieces"], plan["outline"]
    solid = [p for p in pieces if p["type"] != "rug"]
    bad = set()
    blocked_zones = []
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            ov = overlap(a["rect"], b["rect"])
            if ov > EPS:
                fails.append(f"{a['name']} and {b['name']} overlap by {fmt_a(plan, ov)}")
                bad.update((a["name"], b["name"]))
    for p in pieces:
        if not rect_in_poly(p["rect"], outline):
            fails.append(f"{p['name']} runs outside the room")
            bad.add(p["name"])
        for o in plan["obstacles"]:
            if p["type"] != "rug" and overlap(p["rect"], o["rect"]) > EPS:
                fails.append(f"{p['name']} sits on the {o['name'].lower()}")
                bad.add(p["name"])
            elif o["type"] == "radiator" and p["type"] != "rug" and rect_gap(p["rect"], o["rect"]) < 0.1:
                warns.append(f"{p['name']} stands against the {o['name'].lower()}: it blocks the heat and dries out")
    geo = []
    for d in plan["doors"]:
        g = door_geometry(d, outline)
        geo.append(g)
        if not g:
            fails.append(f"{d['name']} at {fmt_pt(plan, d['at'])} is not on a wall")
            continue
        for p in solid:
            if rect_in_swing(p["rect"], d, g):
                fails.append(f"{p['name']} is in the swing of {d['name']}: the door can't open fully")
                bad.add(p["name"])
    for p in solid:
        for side, z in zones(p):
            why = None
            if not rect_in_poly(z, outline):
                why = "runs into the wall"
            else:
                for o in solid:
                    if o is not p and overlap(z, o["rect"]) > EPS:
                        why = f"is blocked by {o['name']}"
                        break
                else:
                    for o in plan["obstacles"]:
                        if overlap(z, o["rect"]) > EPS:
                            why = f"is blocked by the {o['name'].lower()}"
                            break
            if why:
                fails.append(f"{p['name']}'s {side} clearance ({fmt_l(plan, p['clear'][side])}) {why}")
                bad.add(p["name"])
                blocked_zones.append(z)

    routes, turns, grid_c, incomplete = [], [], None, False
    try:
        grid_c = _routes_and_turns(plan, geo, fails, bad, routes, turns)
    except TimeUp:
        incomplete = True
    return _finish(plan, fails, warns, bad, blocked_zones, routes, turns, geo, grid_c, incomplete)


def _routes_and_turns(plan, geo, fails, bad, routes, turns):
    """The grid checks: walking routes at the walkway width, and the turning circles. These are
    the slow part, so they stop at the deadline."""
    outline, solid = plan["outline"], [p for p in plan["pieces"] if p["type"] != "rug"]
    grid = Grid(plan)
    ok = grid.clear(plan["walkway"])
    starts, door_of = [], {}
    for d, g in zip(plan["doors"], geo):
        if not g or not d["entrance"]:
            continue
        px = d["at"][0] + g["n"][0] * (plan["walkway"] / 2 + grid.c)
        py = d["at"][1] + g["n"][1] * (plan["walkway"] / 2 + grid.c)
        found = []
        reach_r = d["width"] / 2 + grid.c
        ci, cj = grid.cell(px, py)
        span = int(reach_r / grid.c) + 1
        for j in range(cj - span, cj + span + 1):
            for i in range(ci - span, ci + span + 1):
                if 0 <= i < grid.nx and 0 <= j < grid.ny and ok[j][i]:
                    x, y = grid.centre(i, j)
                    if math.hypot(x - px, y - py) <= reach_r:
                        found.append((i, j))
        if not found:
            fails.append(f"nothing {fmt_l(plan, plan['walkway'])} wide clears the way in at {d['name']}")
            continue
        best = min(found, key=lambda c: math.hypot(grid.centre(*c)[0] - px, grid.centre(*c)[1] - py))
        starts.append(best)
        door_of[best] = d["at"]
    parent = grid.reach(ok, starts) if starts else {}
    half = plan["walkway"] / 2 + grid.c + 1e-6   # the walker touches the clearance, to within a grid step
    for p in solid:
        tick()
        if not p["access"] or not starts:
            continue
        targets = [(s, z) for s, z in zones(p)]
        if p["access"] == "front" or not targets:
            fr = frame(p)
            z = [z for s, z in targets if s == "front"] or [side_zone(p["rect"], fr["front"], 0.05)]
            targets = [("front", z[0])]
        need = targets if p["access"] == "sides" else [None]
        missing = []
        hits = []
        for want in need:
            cand = targets if want is None else [want]
            hit = None
            for side, z in cand:
                hit = nearest_reached(grid, parent, z, half)
                if hit:
                    hits.append((hit, z))
                    break
            if not hit:
                missing.append("its " + (want[0] if want else " or ".join(s for s, _ in cand)) + " side")
        if missing:
            fails.append(f"no clear {fmt_l(plan, plan['walkway'])} route from the entrance reaches {p['name']} ({', '.join(missing)})")
            bad.add(p["name"])
        for h, z in hits:
            pts = path(grid, parent, h, door_of)
            cx, cy = pts[-1]
            x, y, w, hh = z
            pts.append((min(max(cx, x), x + w), min(max(cy, y), y + hh)))
            routes.append(pts)
    # (centre, for whom, clear, diameter): drawn exactly where they are checked
    if plan.get("turning_circles"):
        dist = grid.distances()
        for t in plan["turning_circles"]:
            d, r = t["d"], t["d"] / 2
            if "at" in t:
                i, j = grid.cell(*t["at"])
                where = f"for {t['for']} at {fmt_pt(plan, t['at'])}"
                if not (0 <= i < grid.nx and 0 <= j < grid.ny) or grid.blocked[j][i]:
                    fails.append(f"the {fmt_d(plan, d)} turning circle {where} sits on furniture or outside the room")
                    turns.append((t["at"], t["for"], False, d))
                elif dist[j][i] < r - grid.c / 2 - 1e-9:
                    fails.append(f"the {fmt_d(plan, d)} turning circle {where} is not clear: the clear circle there is "
                                 f"{fmt_l(plan, 2 * dist[j][i])} across")
                    turns.append((t["at"], t["for"], False, d))
                elif (i, j) not in parent:
                    fails.append(f"no clear {fmt_l(plan, plan['walkway'])} route from the entrance reaches the turning circle {where}")
                    turns.append((t["at"], t["for"], False, d))
                else:
                    turns.append((t["at"], t["for"], True, d))
                continue
            rel = {"front": "in front of", "back": "behind", "left": "to the left of", "right": "to the right of",
                   "any": "by"}[t["side"]]
            where = (f"for {t['for']} " if t["for"] != "turning space" else "") + \
                    f"{rel} {t['near']}, within {fmt_l(plan, t['within'])}"
            best, best_reached = near_search(plan, grid, dist, parent, t, geo)
            if best is None:
                fails.append(f"the {fmt_d(plan, d)} turning circle {where}: there is no clear floor there at all")
                continue
            if best_reached and best_reached[0] >= r - grid.c / 2 - 1e-9:
                turns.append((best_reached[1], t["for"], True, d))
            elif best[0] >= r - grid.c / 2 - 1e-9:
                fails.append(f"no clear {fmt_l(plan, plan['walkway'])} route from the entrance reaches the "
                             f"{fmt_d(plan, d)} turning circle {where}")
                turns.append((best[1], t["for"], False, d))
            else:
                fails.append(f"the {fmt_d(plan, d)} turning circle {where} doesn't fit: the largest clear circle there "
                             f"is {fmt_l(plan, 2 * best[0])} across, centred at {fmt_pt(plan, best[1])}")
                turns.append((best[1], t["for"], False, d))
    elif plan["accessible"]:
        found = turning_circle(grid, parent, 0.75)
        if found:
            turns.append((found, "turning space", True, 1.5))
        else:
            fails.append("there is no clear 1.5 m turning circle the route reaches")
    return grid.c


def _finish(plan, fails, warns, bad, blocked_zones, routes, turns, geo, grid_c, incomplete):
    outline = plan["outline"]
    solid = [p for p in plan["pieces"] if p["type"] != "rug"]
    for w in plan["windows"]:
        wall = wall_at(w["at"], outline)
        if not wall:
            warns.append(f"window at {fmt_pt(plan, w['at'])} is not on a wall")
            continue
        a, b = wall
        n = inward_normal(a, b, outline)
        horiz = abs(a[1] - b[1]) < EPS
        hw = w["width"] / 2
        win = (w["at"][0] - hw, w["at"][1], w["width"], 0) if horiz else (w["at"][0], w["at"][1] - hw, 0, w["width"])
        for p in solid:
            if p["height"] > w["sill"] + EPS and rect_gap(p["rect"], win) < 0.3:
                x, y, pw, ph = p["rect"]
                along = (min(x + pw, win[0] + win[2]) - max(x, win[0])) if horiz else (min(y + ph, win[1] + win[3]) - max(y, win[1]))
                if along > EPS:
                    warns.append(f"{p['name']} ({fmt_l(plan, p['height'])} tall) stands in front of the window at "
                                 f"{fmt_pt(plan, w['at'])}, whose sill is {fmt_l(plan, w['sill'])}")
    floor = poly_area(outline)
    covered = sum(p["rect"][2] * p["rect"][3] for p in solid)
    if floor > EPS and covered / floor > plan["max_coverage"] + EPS:
        warns.append(f"the furniture covers {covered / floor * 100:.0f} % of the floor, over {plan['max_coverage'] * 100:.0f} %")
    return {"fails": fails, "warns": warns, "floor": floor, "covered": covered, "bad": bad,
            "routes": routes, "blocked_zones": blocked_zones, "turns": turns, "geo": geo, "grid": grid_c,
            "incomplete": incomplete}


def nearest_reached(grid, parent, z, half):
    x, y, w, h = z
    i0, j0 = grid.cell(x - half, y - half)
    i1, j1 = grid.cell(x + w + half, y + h + half)
    best = None
    for j in range(max(0, j0), min(grid.ny - 1, j1) + 1):
        for i in range(max(0, i0), min(grid.nx - 1, i1) + 1):
            if (i, j) in parent:
                cx, cy = grid.centre(i, j)
                gap = math.hypot(max(x - cx, cx - (x + w), 0), max(y - cy, cy - (y + h), 0))
                if gap <= half and (best is None or gap < best[0]):
                    best = (gap, (i, j))
    return best[1] if best else None


def path(grid, parent, cell, door_of=None):
    pts = []
    while cell is not None:
        pts.append(grid.centre(*cell))
        first = cell
        cell = parent[cell]
    pts = pts[::-1]
    if door_of and first in door_of:
        pts.insert(0, door_of[first])
    return simplify(pts, 0.08)


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    L = math.hypot(x2 - x1, y2 - y1) or 1e-9
    far, idx = 0, 0
    for i, (x, y) in enumerate(pts[1:-1], 1):
        d = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1)) / L
        if d > far:
            far, idx = d, i
    if far <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def near_search(plan, grid, dist, parent, t, geo):
    """The largest clear circle whose centre lies in the zone a place-tied turning circle names:
    within `within` of the door (on its room side, or to its left or right as you face it from
    inside) or of the piece's given side. Returns (best, best reached by the route), each as
    (clear radius, centre) or None."""
    w = t["within"]
    if t["kind"] == "door":
        d = next(x for x in plan["doors"] if x["name"] == t["near"])
        g = geo[plan["doors"].index(d)]
        if not g:
            return None, None
        cx, cy = d["at"]
        right = (-g["n"][1], g["n"][0])
        box = (cx - w, cy - w, 2 * w, 2 * w)

        def inside(x, y):
            vx, vy = x - cx, y - cy
            if math.hypot(vx, vy) > w + 1e-9 or vx * g["n"][0] + vy * g["n"][1] <= 0:
                return False
            if t["side"] == "right":
                return vx * right[0] + vy * right[1] > 0
            if t["side"] == "left":
                return vx * right[0] + vy * right[1] < 0
            return True
    else:
        p = next(x for x in plan["pieces"] if x["name"] == t["near"])
        if t["side"] == "any":
            x0, y0, pw, ph = p["rect"]
            box = (x0 - w, y0 - w, pw + 2 * w, ph + 2 * w)

            def inside(x, y):
                gap = math.hypot(max(x0 - x, x - (x0 + pw), 0), max(y0 - y, y - (y0 + ph), 0))
                return 0 < gap <= w + 1e-9
        else:
            box = side_zone(p["rect"], frame(p)[t["side"]], w)

            def inside(x, y):
                bx, by, bw, bh = box
                return bx - 1e-9 <= x <= bx + bw + 1e-9 and by - 1e-9 <= y <= by + bh + 1e-9
    i0, j0 = grid.cell(box[0], box[1])
    i1, j1 = grid.cell(box[0] + box[2], box[1] + box[3])
    best = best_reached = None
    for j in range(max(0, j0), min(grid.ny - 1, j1) + 1):
        tick()
        for i in range(max(0, i0), min(grid.nx - 1, i1) + 1):
            if grid.blocked[j][i]:
                continue
            x, y = grid.centre(i, j)
            if not inside(x, y):
                continue
            cand = (dist[j][i], (round(x, 3), round(y, 3)))
            if best is None or cand[0] > best[0]:
                best = cand
            if (i, j) in parent and (best_reached is None or cand[0] > best_reached[0]):
                best_reached = cand
    return best, best_reached


def turning_circle(grid, parent, radius):
    """A reached cell with a clear disc of `radius` round it (the centre nearest the entrance)."""
    dist = grid.distances()
    for cell in parent:   # in breadth-first order, so the first is the nearest to the door
        i, j = cell
        if dist[j][i] >= radius - 1e-9:
            return grid.centre(i, j)
    return None


# ---------- report ----------

def disp(plan, v):
    return v / plan["k"]


def fmt_l(plan, v):
    return f"{disp(plan, v):.2f} {plan['units']}".replace(".00 ", " ")


def fmt_d(plan, v):
    """A circle's diameter as people write it: 1.5 m, 5 ft."""
    return f"{disp(plan, v):g} {plan['units']}"


def fmt_a(plan, a):
    return f"{a / plan['k'] ** 2:.2f} {'m²' if plan['units'] == 'm' else 'sq ft'}"


def fmt_pt(plan, p):
    return f"({disp(plan, p[0]):g}, {disp(plan, p[1]):g})"


def facing(p):
    return {0: "S", 90: "E", 180: "N", 270: "W"}[p["rot"]]


def report(plan, r):
    u = plan["units"]
    L = [f"# {plan['title']}: layout check", "",
         f"| Piece | Type | Size ({u}) | At ({u}) | Front faces | Clearances ({u}) |", "|---|---|---|---|---|---|"]
    for p in plan["pieces"]:
        w, d = p["size"]
        cl = ", ".join(f"{s} {disp(plan, v):g}" for s, v in p["clear"].items() if v > EPS) or "none"
        mark = " ✗" if p["name"] in r["bad"] else ""
        L.append(f"| {p['name']}{mark} | {p['type']} | {disp(plan, w):g} × {disp(plan, d):g} | "
                 f"{disp(plan, p['rect'][0]):g}, {disp(plan, p['rect'][1]):g} | {facing(p)} | {cl} |")
    L += ["", f"Floor {fmt_a(plan, r['floor'])} · furniture {fmt_a(plan, r['covered'])} "
              f"({r['covered'] / r['floor'] * 100:.0f} %) · walkway {fmt_l(plan, plan['walkway'])}"
              + (" · accessible" if plan["accessible"] else ""), ""]
    if not r["fails"] and not r.get("incomplete"):
        L.append("PASS no overlaps, every piece in the room, no door swing blocked, every clearance clear, "
                 "every piece reached at the walkway width" + (", a turning circle reached." if plan["accessible"] else "."))
    for at, who, ok, dm in r["turns"]:
        L.append(f"Turning circle ({fmt_d(plan, dm)}) for {who}: centre at {fmt_pt(plan, at)}, {'clear' if ok else 'not clear'}")
    if r["turns"]:
        L.append("")
    L += [f"FAIL {f}" for f in r["fails"]] + [f"WARN {w}" for w in r["warns"]]
    if r.get("incomplete"):
        L += ["", "INCOMPLETE the walking-route and turning-circle checks did not finish in time, so this is not a pass. "
                  "Rerun with a larger --max-seconds, or split the room."]
    return "\n".join(L) + "\n"


def as_json(plan, r):
    return {"title": plan["title"], "units": plan["units"], "pass": not r["fails"] and not r.get("incomplete"),
            "incomplete": bool(r.get("incomplete")), "fails": r["fails"], "warns": r["warns"],
            "floor_area": round(r["floor"] / plan["k"] ** 2, 3), "furniture_area": round(r["covered"] / plan["k"] ** 2, 3),
            "walkway": round(disp(plan, plan["walkway"]), 3),
            "pieces": [{"name": p["name"], "type": p["type"], "rect": [round(disp(plan, v), 3) for v in p["rect"]],
                        "facing": facing(p), "ok": p["name"] not in r["bad"]} for p in plan["pieces"]],
            "turning_circles": [{"for": who, "at": [round(disp(plan, at[0]), 3), round(disp(plan, at[1]), 3)], "clear": ok,
                                 "diameter": round(disp(plan, dm), 3)} for at, who, ok, dm in r["turns"]]}


# ---------- drawing ----------

def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(plan, r, draw=720):
    o, u = plan["outline"], plan["units"]
    xs, ys = [p[0] for p in o], [p[1] for p in o]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    s = draw / max(x1 - x0, y1 - y0)
    m = 80
    W = (x1 - x0) * s + 2 * m + 40
    H = (y1 - y0) * s + 2 * m + 70

    def P(x, y):
        return (m + (x - x0) * s, H - m - 30 - (y - y0) * s)

    def R(rect, **attrs):
        x, y, w, h = rect
        X, Y = P(x, y + h)
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        return f'<rect x="{X:.1f}" y="{Y:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" {a}/>'

    wall = max(0.12 * s, 3)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" '
           'font-family="Helvetica, Arial, sans-serif" font-size="11">',
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="#fff"/>',
           f'<text x="20" y="28" font-size="16" font-weight="bold">{esc(plan["title"])}</text>',
           f'<text x="20" y="46" fill="#444">Floor {esc(fmt_a(plan, r["floor"]))} · walkway {esc(fmt_l(plan, plan["walkway"]))} · '
           f'{"checked: passes" if not r["fails"] else str(len(r["fails"])) + " failure(s)"} · schematic</text>',
           f'<polygon points="{" ".join("%.1f,%.1f" % P(*p) for p in o)}" fill="#faf8f4"/>']
    for p in plan["pieces"]:
        if p["type"] == "rug":
            out.append(R(p["rect"], fill="#efe6d6", stroke="#c8b999", stroke_width="0.8", stroke_dasharray="1 2"))
    for p in plan["pieces"]:
        for side, z in zones(p):
            hit = z in r["blocked_zones"]
            out.append(R(z, fill="#e05a47" if hit else "#7fb3d5", fill_opacity="0.25" if hit else "0.18",
                         stroke="#c0392b" if hit else "#5d8fb0", stroke_width="0.6", stroke_dasharray="3 2"))
    labels = []
    for ob in plan["obstacles"]:
        out.append(R(ob["rect"], fill="#bbb", stroke="#555", stroke_width="1"))
        x, y, w, h = ob["rect"]
        X, Y = P(x + w / 2, y + h / 2)
        labels.append((X, Y + 3 if min(w, h) >= 0.25 else Y + (14 if P(x, y)[1] < H / 2 else -8), ob["name"]))
    for route in r["routes"]:
        if len(route) > 1:
            out.append('<polyline points="' + " ".join("%.1f,%.1f" % P(*q) for q in route) +
                       '" fill="none" stroke="#2e8b57" stroke-width="1.6" stroke-dasharray="6 3" stroke-linecap="round"/>')
    for at, who, ok, dm in r["turns"]:
        X, Y = P(*at)
        col = "#2e8b57" if ok else "#c0392b"
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{dm / 2 * s:.1f}" fill="{col}" fill-opacity="0.06" stroke="{col}" stroke-width="1.2" stroke-dasharray="3 2"/>')
        out.append(f'<text x="{X:.1f}" y="{Y - 2:.1f}" text-anchor="middle" font-size="9" fill="{col}">⌀{esc(fmt_d(plan, dm))} turn</text>')
        if who != "turning space":
            out.append(f'<text x="{X:.1f}" y="{Y + 9:.1f}" text-anchor="middle" font-size="8" fill="{col}">{esc(who)}</text>')
    for p in plan["pieces"]:
        for c in chairs(p):
            out.append(R(c, fill="#fff", stroke="#6b6b6b", stroke_width="0.9", rx="2"))
    for p in plan["pieces"]:
        failed = p["name"] in r["bad"]
        if p["type"] != "rug":
            out.append(R(p["rect"], fill="#e9e4dc", stroke="#c0392b" if failed else "#4a4a4a",
                         stroke_width="2.2" if failed else "1.2"))
            x, y, w, h = p["rect"]
            f = frame(p)["front"]
            a = {(0, -1): ((x, y), (x + w, y)), (0, 1): ((x, y + h), (x + w, y + h)),
                 (1, 0): ((x + w, y), (x + w, y + h)), (-1, 0): ((x, y), (x, y + h))}[f]
            A, B = P(*a[0]), P(*a[1])
            out.append(f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#1f1f1f" stroke-width="2.4"/>')
        x, y, w, h = p["rect"]
        X, Y = P(x + w / 2, y + h / 2)
        pw, pd = p["size"]
        if p["type"] == "rug":
            X, Y = P(x + 0.08, y + h - 0.12)
            out.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="8" fill="#8a7a5c">{esc(p["name"])} '
                       f'{esc(f"{disp(plan, pw):g}×{disp(plan, pd):g}")}</text>')
            continue
        size = f"{disp(plan, pw):g}×{disp(plan, pd):g}"
        fs = 11 if min(w, h) * s > 45 else 8
        out.append(f'<text x="{X:.1f}" y="{Y - 2:.1f}" text-anchor="middle" font-weight="bold" font-size="{fs}">{esc(p["name"])}</text>')
        out.append(f'<text x="{X:.1f}" y="{Y + fs:.1f}" text-anchor="middle" font-size="{fs - 1}" fill="#444">{esc(size)}</text>')
    out.append(f'<polygon points="{" ".join("%.1f,%.1f" % P(*p) for p in o)}" fill="none" stroke="#111" stroke-width="{wall:.1f}" stroke-linejoin="miter"/>')
    for w in plan["windows"]:
        out += opening(P, s, w["at"], w["width"], o, wall, None, None)
    for d, g in zip(plan["doors"], r["geo"]):
        out += opening(P, s, d["at"], d["width"], o, wall, d, g)
    for X, Y, name in labels:
        out.append(f'<text x="{X:.1f}" y="{Y:.1f}" text-anchor="middle" font-size="8" fill="#333">{esc(name)}</text>')
    bx, by = P(x0, y0)
    ex, _ = P(x1, y0)
    out += dim_line(bx, by + 30, ex, by + 30, f"{disp(plan, x1 - x0):g} {u}")
    _, ty = P(x0, y1)
    out += dim_line(bx - 30, by, bx - 30, ty, f"{disp(plan, y1 - y0):g} {u}", vertical=True)
    out += north(W - 40, 40, plan["north"]) + scale(m, H - 18, s, max(x1 - x0, y1 - y0), plan)
    out.append("</svg>")
    return "\n".join(out) + "\n"


def opening(P, s, at, width, outline, wall, door, g):
    seg = wall_at(at, outline)
    vertical = bool(seg) and abs(seg[0][0] - seg[1][0]) < EPS
    x, y = at
    half = width / 2
    a = P(x, y - half) if vertical else P(x - half, y)
    b = P(x, y + half) if vertical else P(x + half, y)
    out = [f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#fff" stroke-width="{wall + 1:.1f}"/>']
    if door is None:
        for off in (-wall / 3, 0, wall / 3):
            dx, dy = (off, 0) if vertical else (0, off)
            out.append(f'<line x1="{a[0] + dx:.1f}" y1="{a[1] + dy:.1f}" x2="{b[0] + dx:.1f}" y2="{b[1] + dy:.1f}" stroke="#2b6cb0" stroke-width="1"/>')
        return out
    if not g or door["swing"] == "sliding":
        out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#b5531a" stroke-width="2" stroke-dasharray="4 2"/>')
        return out
    n = g["n"] if door["swing"] == "in" else (-g["n"][0], -g["n"][1])
    hx, hy = g["hinge"]
    leaf = (hx + n[0] * width, hy + n[1] * width)
    H0, L0, T0 = P(hx, hy), P(*leaf), P(*g["latch"])
    # sweep from the open leaf to the latch; the screen flips y, so pick the flag from the cross product
    cross = (leaf[0] - hx) * (g["latch"][1] - hy) - (leaf[1] - hy) * (g["latch"][0] - hx)
    sweep = 0 if cross > 0 else 1
    out.append(f'<line x1="{H0[0]:.1f}" y1="{H0[1]:.1f}" x2="{L0[0]:.1f}" y2="{L0[1]:.1f}" stroke="#b5531a" stroke-width="1.6"/>')
    out.append(f'<path d="M {L0[0]:.1f} {L0[1]:.1f} A {width * s:.1f} {width * s:.1f} 0 0 {sweep} {T0[0]:.1f} {T0[1]:.1f}" '
               'fill="none" stroke="#b5531a" stroke-width="0.8" stroke-dasharray="3 2"/>')
    if door["entrance"]:
        mx, my = P(at[0] - g["n"][0] * 0.35, at[1] - g["n"][1] * 0.35)
        out.append(f'<text x="{mx:.1f}" y="{my + 3:.1f}" text-anchor="middle" font-size="9" fill="#b5531a">{esc(door["name"])}</text>')
    return out


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


def scale(x, y, s, span, plan):
    u, k = plan["units"], plan["k"]
    span_u = span / k
    step = 1.0
    for mlt in (1, 2, 5):
        for e in range(-1, 4):
            v = mlt * 10 ** e
            if step < v <= span_u / 4:
                step = v
    w = step * k * s
    return [f'<rect x="{x}" y="{y - 6:.1f}" width="{w / 2:.1f}" height="6" fill="#111"/>',
            f'<rect x="{x + w / 2:.1f}" y="{y - 6:.1f}" width="{w / 2:.1f}" height="6" fill="#fff" stroke="#111"/>',
            f'<text x="{x + w + 6:.1f}" y="{y:.1f}">{step:g} {u}</text>']


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a room's furniture layout and draw it.")
    ap.add_argument("layout")
    ap.add_argument("--svg", help="write the dimensioned plan here")
    ap.add_argument("--json", action="store_true", help="print the result as JSON instead of a table")
    ap.add_argument("--max-seconds", type=float, default=20.0,
                    help="stop the route and turning checks after this long, and say they are incomplete (default 20)")
    args = ap.parse_args(argv)
    global DEADLINE
    if args.max_seconds <= 0:
        print("FAIL --max-seconds must be above zero")
        return 2
    try:
        with open(args.layout, encoding="utf-8-sig") as f:
            plan = load(json.load(f))
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"FAIL cannot read {args.layout}: {e}")
        return 2
    except InputError as e:
        print(f"FAIL {e}")
        return 2
    DEADLINE = time.monotonic() + args.max_seconds
    try:
        r = check(plan)
    finally:
        DEADLINE = None
    if args.json:
        print(json.dumps(as_json(plan, r), indent=2, ensure_ascii=False))
    else:
        print(report(plan, r), end="")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(plan, r))
        if not args.json:
            print(f"\nWrote {args.svg}")
    if r["incomplete"]:
        return 2
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

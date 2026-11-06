#!/usr/bin/env python3
"""Check a staff rota against its shifts' needs and the working-time rules, and draw the week. Stdlib only.

Reads a roster.json: the staff (skills, weekly maximum and contracted hours, times they
can't work), the shifts (day or date, start and end, overnight allowed, and how many of each
skill they need), who is assigned to each shift, and the rules (minimum rest between
shifts, maximum consecutive days, maximum hours in a day). It fails a rota where
  - a shift is short of a skill it needs (people are matched to needs, one need each)
  - someone is on two shifts that overlap
  - someone works a shift during a time they marked unavailable
  - someone goes over their weekly maximum hours, or the daily maximum
  - someone gets less than the minimum rest between two shifts, across midnight and days
  - someone works more consecutive days than the limit
  - someone fills a role they don't have the skill for, or has none of the skills a shift needs
and warns where
  - someone's hours are well off their contracted hours
  - weekend or night shifts fall unevenly across the people working that period
  - a shift is short while qualified people are free to take it (they are named)
Then it can draw the week: a grid of staff rows by day columns, each shift as a block with
its times and role, failures marked in red, and a coverage row per day.

With --summary it also prints, from the rota as checked, each person's shifts, hours, nights,
weekend days and longest run of days, and each shift's cover against its needs. With
--compare ORIGINAL.json it lists every assignment the rota adds or removes against the
original, shift by shift.

Usage:
  python3 roster_check.py roster.json [--svg week.svg] [--json] [--summary] [--compare original.json]
Exit codes: 0 no failures, 1 a failure, 2 bad input.
"""
import argparse
import datetime as dt
import json
import sys

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DEFAULT_RULES = {"min_rest_hours": 11, "max_consecutive_days": 6, "max_hours_per_day": 12}
ANY = "any"


class InputError(Exception):
    pass


def hhmm(s, what):
    if not isinstance(s, str) or ":" not in s:
        raise InputError(f"{what} must be a time like 07:30")
    h, _, m = s.partition(":")
    if not (h.isdigit() and m.isdigit()):
        raise InputError(f"{what} must be a time like 07:30")
    h, m = int(h), int(m)
    if h == 24 and m == 0:
        return 1440
    if not (0 <= h < 24 and 0 <= m < 60):
        raise InputError(f"{what} is not a time of day: {s}")
    return h * 60 + m


def fmt(mins):
    mins %= 1440
    return "%02d:%02d" % (mins // 60, mins % 60)


def num(v, what, lo=0):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v < lo:
        raise InputError(f"{what} must be a number of at least {lo}")
    return float(v)


class Calendar(object):
    """Turns a day name (with an optional week number) or an ISO date into a day index from
    the roster's first day, so every time is minutes from one origin."""

    def __init__(self, items):
        dates = [i["date"] for i in items if isinstance(i, dict) and "date" in i]
        days = [i for i in items if isinstance(i, dict) and "day" in i]
        if dates and days:
            raise InputError("use either a day name or a date for every shift and absence, not both")
        self.by_date = bool(dates)
        if self.by_date:
            try:
                self.origin = min(dt.date.fromisoformat(d) for d in dates)
            except (TypeError, ValueError):
                raise InputError("a date must look like 2026-11-09")
            self.origin -= dt.timedelta(days=self.origin.weekday())  # start the grid on a Monday

    def index(self, item, what):
        if self.by_date:
            if "date" not in item:
                raise InputError(f"{what} needs a date, like the rest of the roster")
            try:
                d = dt.date.fromisoformat(item["date"])
            except (TypeError, ValueError):
                raise InputError(f"{what}: a date must look like 2026-11-09")
            return (d - self.origin).days
        day = item.get("day")
        if day not in DAYS:
            raise InputError(f"{what}: day must be one of {', '.join(DAYS)}")
        week = item.get("week", 1)
        if isinstance(week, bool) or not isinstance(week, int) or week < 1:
            raise InputError(f"{what}: week must be 1, 2, ...")
        return (week - 1) * 7 + DAYS.index(day)

    def label(self, idx):
        if self.by_date:
            return (self.origin + dt.timedelta(days=idx)).strftime("%a %d %b")
        return DAYS[idx % 7] + (f" wk{idx // 7 + 1}" if idx >= 7 else "")


def load(doc):
    if not isinstance(doc, dict):
        raise InputError("the roster must be a JSON object")
    staff_in, shifts_in = doc.get("staff"), doc.get("shifts")
    if not isinstance(staff_in, list) or not staff_in:
        raise InputError("no staff: the roster needs a staff list")
    if not isinstance(shifts_in, list) or not shifts_in:
        raise InputError("no shifts: the roster needs a shifts list")
    rules = dict(DEFAULT_RULES)
    given = doc.get("rules") or {}
    if not isinstance(given, dict):
        raise InputError("rules must be an object")
    for k, v in given.items():
        if k not in DEFAULT_RULES:
            raise InputError(f"unknown rule {k!r}; known rules are {', '.join(DEFAULT_RULES)}")
        rules[k] = num(v, f"rules.{k}")
    for i, p in enumerate(staff_in):
        if isinstance(p, dict) and not isinstance(p.get("unavailable", []), list):
            raise InputError(f"staff[{i}].unavailable must be a list")
    absences = [a for p in staff_in if isinstance(p, dict) for a in (p.get("unavailable") or []) if isinstance(a, dict)]
    cal = Calendar([s for s in shifts_in if isinstance(s, dict)] + absences)

    staff, order = {}, []
    for i, p in enumerate(staff_in):
        if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"]:
            raise InputError(f"staff[{i}] needs an id")
        sid = p["id"]
        if sid in staff:
            raise InputError(f"staff id {sid!r} appears twice")
        skills = p.get("skills", [])
        if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            raise InputError(f"{sid}: skills must be a list of names")
        away = []
        for j, a in enumerate(p.get("unavailable") or []):
            if not isinstance(a, dict):
                raise InputError(f"{sid}: unavailable[{j}] must be an object")
            d = cal.index(a, f"{sid} unavailable[{j}]")
            st = hhmm(a["start"], f"{sid} unavailable[{j}].start") if "start" in a else 0
            en = hhmm(a["end"], f"{sid} unavailable[{j}].end") if "end" in a else 1440
            if en <= st:
                en += 1440
            away.append((d * 1440 + st, d * 1440 + en, a.get("reason", "")))
        staff[sid] = {"id": sid, "name": str(p.get("name") or sid), "skills": set(skills),
                      "max_hours": num(p["max_hours"], f"{sid}.max_hours") if "max_hours" in p else None,
                      "contracted": num(p["contracted_hours"], f"{sid}.contracted_hours") if "contracted_hours" in p else None,
                      "away": away}
        order.append(sid)

    shifts, sorder = {}, []
    for i, s in enumerate(shifts_in):
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not s["id"]:
            raise InputError(f"shifts[{i}] needs an id")
        hid = s["id"]
        if hid in shifts:
            raise InputError(f"shift id {hid!r} appears twice")
        d = cal.index(s, f"shift {hid}")
        st, en = hhmm(s.get("start"), f"{hid}.start"), hhmm(s.get("end"), f"{hid}.end")
        if en <= st:
            en += 1440  # overnight
        needs = s.get("needs") or {}
        if not isinstance(needs, dict):
            raise InputError(f"{hid}: needs must map a skill to a count")
        if "label" in s and not isinstance(s["label"], str):
            raise InputError(f"{hid}: label must be text")
        clean = {}
        for k, v in needs.items():
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise InputError(f"{hid}: needs.{k} must be a whole number")
            if v:
                clean[k] = v
        shifts[hid] = {"id": hid, "day": d, "start": d * 1440 + st, "end": d * 1440 + en,
                       "needs": clean, "label": s.get("label") or hid, "assigned": []}
        sorder.append(hid)

    assign = doc.get("assignments", {})
    pairs = []
    if assign is None:
        assign = {}
    if isinstance(assign, dict):
        pairs = list(assign.items())
    elif isinstance(assign, list):
        for j, a in enumerate(assign):
            if not isinstance(a, dict) or "shift" not in a:
                raise InputError(f"assignments[{j}] needs a shift")
            pairs.append((a["shift"], a.get("staff", [])))
    else:
        raise InputError("assignments must map a shift id to its staff")
    for s in shifts_in:
        if isinstance(s, dict) and s.get("assigned"):
            pairs.append((s["id"], s["assigned"]))
    for hid, people in pairs:
        if not isinstance(hid, str) or hid not in shifts:
            raise InputError(f"assignments name shift {hid!r}, which is not in the shifts list")
        if isinstance(people, (str, dict)):
            people = [people]
        if not isinstance(people, list):
            raise InputError(f"assignments.{hid} must be a list of staff ids")
        for x in people:
            sid, role = (x.get("id"), x.get("as")) if isinstance(x, dict) else (x, None)
            if role is not None and not isinstance(role, str):
                raise InputError(f"shift {hid}: a role given with \"as\" must be a skill name")
            if not isinstance(sid, str) or sid not in staff:
                raise InputError(f"shift {hid} names staff {sid!r}, who is not in the staff list")
            if any(a[0] == sid for a in shifts[hid]["assigned"]):
                raise InputError(f"{sid} is assigned to {hid} twice")
            shifts[hid]["assigned"].append((sid, role))
    return {"rules": rules, "staff": staff, "order": order, "shifts": shifts, "sorder": sorder, "cal": cal,
            "ndays": max(7, 7 * ((max(s["day"] for s in shifts.values()) // 7) + 1))}


def hours(shift):
    return (shift["end"] - shift["start"]) / 60.0


def cover(shift, staff):
    """Match assigned people to the shift's needs, one need each, preferring the role a
    person was assigned as. Returns (filled per skill, short per skill, {sid: skill or None},
    [role errors])."""
    slots = [k for k, n in sorted(shift["needs"].items()) for _ in range(n)]
    people = shift["assigned"]
    errors = []

    def can(sid, role, skill):
        if role is not None:
            return role == skill
        return skill == ANY or skill in staff[sid]["skills"]

    for sid, role in people:
        if role is not None and role != ANY and role not in staff[sid]["skills"]:
            errors.append(f"{staff[sid]['name']} is on {shift['label']} as {role} but doesn't have that skill")
    match = {}  # slot index -> person index

    def augment(pi, seen):
        sid, role = people[pi]
        if role is not None and role != ANY and role not in staff[sid]["skills"]:
            return False
        for si, skill in enumerate(slots):
            if si in seen or not can(sid, role, skill):
                continue
            seen.add(si)
            if si not in match or augment(match[si], seen):
                match[si] = pi
                return True
        return False

    for pi in range(len(people)):
        augment(pi, set())
    filled, short = {}, {}
    for si, skill in enumerate(slots):
        if si in match:
            filled[skill] = filled.get(skill, 0) + 1
        else:
            short[skill] = short.get(skill, 0) + 1
    role_of = {people[pi][0]: slots[si] for si, pi in match.items()}
    for sid, role in people:
        if sid not in role_of and role is None and shift["needs"] and not (
                staff[sid]["skills"] & set(shift["needs"]) or ANY in shift["needs"]):
            errors.append(f"{staff[sid]['name']} is on {shift['label']} but has none of the skills it needs "
                          f"({', '.join(sorted(shift['needs']))})")
        role_of.setdefault(sid, None)
    return filled, short, role_of, errors


def overlaps(a0, a1, b0, b1):
    return a0 < b1 and b0 < a1


def is_night(shift):
    return shift["end"] - shift["day"] * 1440 > 1440 or (shift["start"] % 1440) >= 20 * 60


def is_weekend(shift):
    return shift["day"] % 7 in (5, 6)


def check(r):
    staff, shifts, rules = r["staff"], r["shifts"], r["rules"]
    fails, warns = [], []
    bad_shift, bad_cell = set(), set()  # shift ids short; (sid, shift id) involved in a failure
    roles, coverage = {}, {}
    for hid in r["sorder"]:
        sh = shifts[hid]
        filled, short, role_of, errs = cover(sh, staff)
        roles[hid] = role_of
        coverage[hid] = {"needs": sh["needs"], "filled": filled, "short": short}
        for e in errs:
            fails.append(e)
            for sid, _ in sh["assigned"]:
                if staff[sid]["name"] in e:
                    bad_cell.add((sid, hid))
        if short:
            bad_shift.add(hid)
            fails.append(f"{sh['label']} ({r['cal'].label(sh['day'])} {fmt(sh['start'])}–{fmt(sh['end'])}) is short "
                         + ", ".join(f"{n} {k}" for k, n in sorted(short.items())))

    worked = {sid: sorted((shifts[h] for h in r["sorder"] if any(a[0] == sid for a in shifts[h]["assigned"])),
                          key=lambda s: s["start"]) for sid in r["order"]}
    per = {}
    for sid in r["order"]:
        p, mine = staff[sid], worked[sid]
        name = p["name"]
        for a, b in zip(mine, mine[1:]):
            if overlaps(a["start"], a["end"], b["start"], b["end"]):
                fails.append(f"{name} is on {a['label']} and {b['label']}, which overlap")
                bad_cell |= {(sid, a["id"]), (sid, b["id"])}
            else:
                rest = (b["start"] - a["end"]) / 60.0
                if rest < rules["min_rest_hours"]:
                    fails.append(f"{name} gets {rest:g} h rest between {a['label']} (ends {r['cal'].label(a['end'] // 1440)} "
                                 f"{fmt(a['end'])}) and {b['label']}, under the {rules['min_rest_hours']:g} h minimum")
                    bad_cell |= {(sid, a["id"]), (sid, b["id"])}
        for sh in mine:
            for a0, a1, why in p["away"]:
                if overlaps(sh["start"], sh["end"], a0, a1):
                    fails.append(f"{name} is on {sh['label']} but is unavailable then" + (f" ({why})" if why else ""))
                    bad_cell.add((sid, sh["id"]))
                    break
        weeks = {}
        for sh in mine:
            weeks.setdefault(sh["day"] // 7, []).append(sh)
        for w, lst in sorted(weeks.items()):
            total = sum(hours(s) for s in lst)
            if p["max_hours"] is not None and total > p["max_hours"] + 1e-9:
                fails.append(f"{name} works {total:g} h in week {w + 1}, over their {p['max_hours']:g} h maximum")
                bad_cell |= {(sid, s["id"]) for s in lst}
        days = {}
        for sh in mine:
            days.setdefault(sh["day"], []).append(sh)
        for d, lst in sorted(days.items()):
            total = sum(hours(s) for s in lst)
            if total > rules["max_hours_per_day"] + 1e-9:
                fails.append(f"{name} works {total:g} h on {r['cal'].label(d)}, over the {rules['max_hours_per_day']:g} h daily maximum")
                bad_cell |= {(sid, s["id"]) for s in lst}
        run, best, prev, run_days = 0, (0, []), None, []
        for d in sorted(days):
            run = run + 1 if prev is not None and d == prev + 1 else 1
            run_days = run_days + [d] if run > 1 else [d]
            if run > best[0]:
                best = (run, list(run_days))
            prev = d
        if best[0] > rules["max_consecutive_days"]:
            fails.append(f"{name} works {best[0]} days in a row ({r['cal'].label(best[1][0])} to {r['cal'].label(best[1][-1])}), "
                         f"over the {rules['max_consecutive_days']:g}-day limit")
            bad_cell |= {(sid, s["id"]) for d in best[1] for s in days[d]}
        total = sum(hours(s) for s in mine)
        nweeks = max(1, r["ndays"] // 7)
        per[sid] = {"name": name, "hours": total, "shifts": len(mine),
                    "weekend": sum(1 for s in mine if is_weekend(s)), "night": sum(1 for s in mine if is_night(s)),
                    "weekend_days": len({s["day"] for s in mine if is_weekend(s)}),
                    "days_in_a_row": best[0], "worked": [s["id"] for s in mine],
                    "contracted": p["contracted"], "max": p["max_hours"]}
        if p["contracted"] is not None:
            want = p["contracted"] * nweeks
            if abs(total - want) > max(4.0, 0.2 * want):
                warns.append(f"{name} works {total:g} h against {want:g} h contracted")

    for kind, test in (("weekend", is_weekend), ("night", is_night)):
        if not any(test(s) for s in shifts.values()):
            continue
        # among the people who could work those shifts: anyone with a skill one of them needs
        needed = {k for s in shifts.values() if test(s) for k in s["needs"]}
        pool = [sid for sid in r["order"] if ANY in needed or staff[sid]["skills"] & needed]
        counts = {sid: per[sid][kind] for sid in pool}
        if len(counts) > 1 and max(counts.values()) - min(counts.values()) >= 2:
            hi = max(counts, key=counts.get)
            lo = min(counts, key=counts.get)
            warns.append(f"{kind} shifts fall unevenly: {staff[hi]['name']} has {counts[hi]}, "
                         f"{staff[lo]['name']} has {counts[lo]}")

    for hid in r["sorder"]:
        short = coverage[hid]["short"]
        if not short:
            continue
        sh = shifts[hid]
        for skill in sorted(short):
            free = []
            for sid in r["order"]:
                p = staff[sid]
                if any(a[0] == sid for a in sh["assigned"]):
                    continue
                if skill != ANY and skill not in p["skills"]:
                    continue
                if any(overlaps(sh["start"], sh["end"], a0, a1) for a0, a1, _ in p["away"]):
                    continue
                clash = False
                for o in worked[sid]:
                    gap = max(o["start"] - sh["end"], sh["start"] - o["end"]) / 60.0
                    if overlaps(o["start"], o["end"], sh["start"], sh["end"]) or gap < rules["min_rest_hours"]:
                        clash = True
                        break
                week = sum(hours(o) for o in worked[sid] if o["day"] // 7 == sh["day"] // 7)
                if clash or (p["max_hours"] is not None and week + hours(sh) > p["max_hours"] + 1e-9):
                    continue
                free.append(p["name"])
            if free:
                warns.append(f"{sh['label']} is short {short[skill]} {skill}, and qualified people are free to take it: "
                             + ", ".join(free))
    return {"fails": fails, "warns": warns, "coverage": coverage, "people": per, "roles": roles,
            "bad_shift": bad_shift, "bad_cell": bad_cell}


def report(r, res):
    out = []
    sh, cal = r["shifts"], r["cal"]
    out.append("Coverage")
    for hid in r["sorder"]:
        s, c = sh[hid], res["coverage"][hid]
        need = ", ".join(f"{k} {c['filled'].get(k, 0)}/{n}" for k, n in sorted(c["needs"].items())) or "no stated needs"
        who = ", ".join(r["staff"][sid]["name"] for sid, _ in s["assigned"]) or "nobody"
        out.append(f"  {'SHORT' if c['short'] else 'ok   '} {s['label']:<14} {cal.label(s['day']):<10} "
                   f"{fmt(s['start'])}–{fmt(s['end'])}  {need}  [{who}]")
    out.append("")
    out.append("Hours")
    for sid in r["order"]:
        p = res["people"][sid]
        extra = []
        if p["contracted"] is not None:
            extra.append(f"contracted {p['contracted']:g}")
        if p["max"] is not None:
            extra.append(f"max {p['max']:g}")
        out.append(f"  {p['name']:<16} {p['hours']:>5g} h  {p['shifts']} shifts, {p['weekend']} weekend, "
                   f"{p['night']} night" + (f"  ({', '.join(extra)})" if extra else ""))
    out.append("")
    for f in res["fails"]:
        out.append("FAIL " + f)
    for w in res["warns"]:
        out.append("WARN " + w)
    out.append(f"{len(res['fails'])} failure(s), {len(res['warns'])} warning(s).")
    return "\n".join(out) + "\n"


def shift_text(r, sh, sid=None, res=None):
    role = res["roles"].get(sh["id"], {}).get(sid) if (res and sid) else None
    return (f"{sh['label']} {r['cal'].label(sh['day'])} {fmt(sh['start'])}–{fmt(sh['end'])}"
            + (f" as {role}" if role and role != ANY else ""))


def summary(r, res):
    """What the final rota says, per person and per shift: the facts a reply quotes, so its
    notes can't drift from the schedule."""
    people = []
    for sid in r["order"]:
        p = res["people"][sid]
        people.append({"id": sid, "name": p["name"], "hours": p["hours"], "shifts": p["shifts"],
                       "nights": p["night"], "weekend_days": p["weekend_days"],
                       "days_in_a_row": p["days_in_a_row"], "contracted": p["contracted"], "max": p["max"],
                       "on": [shift_text(r, r["shifts"][h], sid, res) for h in p["worked"]]})
    shifts = []
    for hid in r["sorder"]:
        sh, c = r["shifts"][hid], res["coverage"][hid]
        shifts.append({"id": hid, "shift": shift_text(r, sh),
                       "cover": {k: [c["filled"].get(k, 0), n] for k, n in sorted(c["needs"].items())},
                       "short": c["short"], "who": [r["staff"][sid]["name"] for sid, _ in sh["assigned"]]})
    return {"people": people, "shifts": shifts}


def summary_text(sm):
    out = ["Per person"]
    for p in sm["people"]:
        bits = [f"{p['hours']:g} h", f"{p['shifts']} shifts", f"{p['nights']} nights",
                f"{p['weekend_days']} weekend days", f"{p['days_in_a_row']} days in a row at most"]
        if p["contracted"] is not None:
            bits.append(f"contracted {p['contracted']:g} h")
        out.append(f"  {p['name']}: " + ", ".join(bits))
        for t in p["on"]:
            out.append(f"    {t}")
    out.append("")
    out.append("Per shift")
    for s in sm["shifts"]:
        cover = ", ".join(f"{k} {a}/{b}" for k, (a, b) in s["cover"].items()) or "no stated needs"
        out.append(f"  {'SHORT' if s['short'] else 'ok   '} {s['shift']}: {cover} [{', '.join(s['who']) or 'nobody'}]")
    return "\n".join(out) + "\n"


def compare(r, orig):
    """Every assignment the final rota adds or removes against the original, by shift."""
    changes = []
    for hid in r["sorder"] + [h for h in orig["sorder"] if h not in r["shifts"]]:
        now = {sid for sid, _ in r["shifts"][hid]["assigned"]} if hid in r["shifts"] else set()
        was = {sid for sid, _ in orig["shifts"][hid]["assigned"]} if hid in orig["shifts"] else set()
        if now == was:
            continue
        sh = r["shifts"].get(hid) or orig["shifts"][hid]
        name = lambda sid: (r["staff"].get(sid) or orig["staff"].get(sid) or {"name": sid})["name"]
        changes.append({"shift": hid, "when": shift_text(r if hid in r["shifts"] else orig, sh),
                        "added": sorted(name(s) for s in now - was), "removed": sorted(name(s) for s in was - now)})
    return changes


def compare_text(changes):
    if not changes:
        return "No assignment changed against the original.\n"
    out = [f"{len(changes)} shift(s) changed against the original"]
    for c in changes:
        bits = ([f"added {', '.join(c['added'])}"] if c["added"] else []) + \
               ([f"removed {', '.join(c['removed'])}"] if c["removed"] else [])
        out.append(f"  {c['when']}: " + "; ".join(bits))
    return "\n".join(out) + "\n"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(r, res):
    cal, sh, staff = r["cal"], r["shifts"], r["staff"]
    ndays = r["ndays"]
    name_w, col_w, head_h, blk_h, pad = 150, 112, 76, 30, 6
    cells = {}
    for hid in r["sorder"]:
        for sid, _ in sh[hid]["assigned"]:
            cells.setdefault((sid, sh[hid]["day"]), []).append(hid)
    row_h = {sid: max([len(v) for (s, _), v in cells.items() if s == sid] + [1]) * (blk_h + 4) + 2 * pad
             for sid in r["order"]}
    per_day = {}
    for hid in r["sorder"]:
        per_day.setdefault(sh[hid]["day"], []).append(hid)
    cov_h = max([len(v) for v in per_day.values()] + [1]) * 18 + 2 * pad + 18
    width = name_w + ndays * col_w + 20
    height = head_h + sum(row_h.values()) + cov_h + 40
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
         f'font-family="Helvetica, Arial, sans-serif" font-size="11">',
         f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
         f'<text x="10" y="22" font-size="15" font-weight="bold">Rota</text>',
         f'<text x="10" y="40" fill="#555">{len(res["fails"])} failure(s), {len(res["warns"])} warning(s). '
         f'Red marks a shift or a person the check failed.</text>']
    for d in range(ndays):
        x = name_w + d * col_w
        fill = "#f4f4f6" if d % 7 in (5, 6) else "#ffffff"
        o.append(f'<rect x="{x}" y="{head_h - 16}" width="{col_w}" height="{height - head_h - 24}" fill="{fill}" stroke="#ddd"/>')
        o.append(f'<text x="{x + col_w / 2}" y="{head_h - 4}" text-anchor="middle" font-weight="bold">{esc(cal.label(d))}</text>')
    y = head_h
    for sid in r["order"]:
        h = row_h[sid]
        p = res["people"][sid]
        o.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#ccc"/>')
        o.append(f'<text x="10" y="{y + 18}" font-weight="bold">{esc(p["name"])}</text>')
        o.append(f'<text x="10" y="{y + 32}" fill="#555">{p["hours"]:g} h'
                 + (f' / {p["contracted"]:g} contracted' if p["contracted"] is not None else "") + '</text>')
        for (s2, d), hids in sorted(cells.items()):
            if s2 != sid:
                continue
            for k, hid in enumerate(hids):
                s = sh[hid]
                bx, by = name_w + d * col_w + 4, y + pad + k * (blk_h + 4)
                bad = (sid, hid) in res["bad_cell"]
                role = res["roles"][hid].get(sid)
                o.append(f'<rect x="{bx}" y="{by}" width="{col_w - 8}" height="{blk_h}" rx="4" '
                         f'fill="{"#fde2e2" if bad else "#e6f0fb"}" stroke="{"#c62828" if bad else "#4a7fc1"}" '
                         f'stroke-width="{2 if bad else 1}"/>')
                o.append(f'<text x="{bx + 5}" y="{by + 12}">{fmt(s["start"])}–{fmt(s["end"])}'
                         f'{" +1" if s["end"] - s["day"] * 1440 > 1440 else ""}</text>')
                both = f"{role} · {s['label']}" if role else s["label"]
                line = both if len(both) <= 17 else (role or s["label"])
                o.append(f'<text x="{bx + 5}" y="{by + 25}" fill="#555">{esc(line[:17])}</text>')
        y += h
    o.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#999"/>')
    o.append(f'<text x="10" y="{y + 18}" font-weight="bold">Coverage</text>')
    for d, hids in per_day.items():
        for k, hid in enumerate(hids):
            c = res["coverage"][hid]
            need, got = sum(c["needs"].values()), sum(c["filled"].values())
            short = bool(c["short"])
            o.append(f'<text x="{name_w + d * col_w + 6}" y="{y + 18 + k * 18}" fill="{"#c62828" if short else "#2e7d32"}" '
                     f'font-weight="{"bold" if short else "normal"}">{esc(sh[hid]["label"])[:13]} {got}/{need}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def jsonable(r, res):
    cal = r["cal"]
    return {"fails": res["fails"], "warns": res["warns"],
            "coverage": {h: dict(res["coverage"][h], day=cal.label(r["shifts"][h]["day"])) for h in r["sorder"]},
            "people": res["people"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a staff rota against its shifts' needs and the working-time rules.")
    ap.add_argument("roster")
    ap.add_argument("--svg", help="draw the week grid here")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--summary", action="store_true",
                    help="also print per person (shifts, hours, nights, weekend days, days in a row) and per shift (cover against need)")
    ap.add_argument("--compare", metavar="ORIGINAL", help="also list every assignment added or removed against this original roster")
    args = ap.parse_args(argv)
    paths = [args.roster] + ([args.compare] if args.compare else [])
    loaded = []
    for path in paths:
        try:
            with open(path, encoding="utf-8-sig") as f:
                loaded.append(load(json.load(f)))
        except (OSError, ValueError, UnicodeDecodeError) as e:
            print(f"FAIL cannot read {path}: {e}")
            return 2
        except InputError as e:
            print(f"FAIL {path}: {e}" if path != args.roster else f"FAIL {e}")
            return 2
    r = loaded[0]
    res = check(r)
    sm = summary(r, res) if args.summary else None
    changes = compare(r, loaded[1]) if args.compare else None
    if args.json:
        out = jsonable(r, res)
        if sm is not None:
            out["summary"] = sm
        if changes is not None:
            out["changes"] = changes
        print(json.dumps(out, indent=1))
    else:
        print(report(r, res), end="")
        if sm is not None:
            print("\n" + summary_text(sm), end="")
        if changes is not None:
            print("\n" + compare_text(changes), end="")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(r, res))
        if not args.json:
            print(f"\nWrote {args.svg}")
    return 1 if res["fails"] else 0


if __name__ == "__main__":
    sys.exit(main())

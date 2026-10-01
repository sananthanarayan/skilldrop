"""catalog.py — the one place that knows where skills, loops and packs live (RFC-0034).

Every skill sits at packs/<pack>/skills/<name>/ and every loop at packs/<pack>/loops/<name>/,
so membership is the folder a thing is in. packs/<pack>/pack.json carries the pack's metadata,
and the root catalogue.json carries pack display order plus the outcome axis (RFC-0026).

The build scripts, validate.py and pack.py all read through this module, so moving a folder
is the whole edit. Stdlib only.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
PACKS_DIR = os.path.join(ROOT, "packs")
INDEX = os.path.join(ROOT, "catalogue.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _children(d, marker):
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x, marker)))


def index():
    """catalogue.json: {version, packs: [display order], outcomes}."""
    return _read(INDEX)


def pack_names():
    """Packs in display order: catalogue.json's order first, then any pack folder it misses
    (validate.py fails that case, so the order list cannot silently drop a pack)."""
    on_disk = _children(PACKS_DIR, "pack.json")
    listed = [p for p in index().get("packs", []) if p in on_disk]
    return listed + [p for p in on_disk if p not in listed]


def pack_meta(name):
    return _read(os.path.join(PACKS_DIR, name, "pack.json"))


def pack_skills(name):
    return _children(os.path.join(PACKS_DIR, name, "skills"), "SKILL.md")


def pack_loops(name):
    return _children(os.path.join(PACKS_DIR, name, "loops"), "loop.json")


def packs():
    """{name: pack.json + derived `skills` and `loops`} in display order — the shape the old
    packs.json `packs` block had, so readers did not have to change what they index."""
    out = {}
    for n in pack_names():
        p = dict(pack_meta(n))
        p["skills"] = pack_skills(n)
        p["loops"] = pack_loops(n)
        out[n] = p
    return out


def outcomes():
    return index().get("outcomes", {})


def _homes(kind):
    """{name: [pack, ...]} — more than one entry means two packs hold a same-named folder."""
    homes = {}
    for n in _children(PACKS_DIR, "pack.json"):
        for x in (pack_skills(n) if kind == "skills" else pack_loops(n)):
            homes.setdefault(x, []).append(n)
    return homes


def skill_homes():
    return _homes("skills")


def loop_homes():
    return _homes("loops")


def skills():
    """{skill name: absolute folder}, sorted by name. First pack wins on a duplicate name."""
    return {s: os.path.join(PACKS_DIR, hs[0], "skills", s) for s, hs in sorted(skill_homes().items())}


def loops():
    """{loop name: absolute folder}, sorted by name."""
    return {l: os.path.join(PACKS_DIR, hs[0], "loops", l) for l, hs in sorted(loop_homes().items())}


def skill_dir(name):
    return skills().get(name)


def loop_dir(name):
    return loops().get(name)


def rel(path):
    """Repo-relative, forward-slash path — for messages and GitHub URLs."""
    return os.path.relpath(path, ROOT).replace(os.sep, "/")

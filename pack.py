#!/usr/bin/env python3
"""Install skilldrop skill packs. Stdlib only, run from the repo root.

    python3 pack.py                          # list packs
    python3 pack.py <pack>                   # list the skills in a pack
    python3 pack.py <pack> --install         # copy into ~/.claude/skills/ (user scope)
    python3 pack.py <pack> --install --project   # copy into ./.claude/skills/ (project scope)
    python3 pack.py <pack> --install --dest <dir># copy into any directory (e.g. .cursor/skills)

Packs are defined in packs.json. For non-Claude IDEs, --dest points at your
tool's skills location; the per-IDE wiring steps stay as documented in README.md.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PACKS = json.load(open(os.path.join(ROOT, "packs.json")))["packs"]


def main():
    args = sys.argv[1:]
    if not args:
        width = max(len(n) for n in PACKS)
        for name, p in PACKS.items():
            print(f"{name:<{width}}  ({len(p['skills'])} skills)  {p['description']}")
        return

    name = args[0]
    if name not in PACKS:
        sys.exit(f"unknown pack '{name}' — run with no arguments to list packs")
    skills = PACKS[name]["skills"]

    if "--install" not in args:
        print("\n".join(skills))
        return

    if "--dest" in args:
        dest = args[args.index("--dest") + 1]
    elif "--project" in args:
        dest = os.path.join(os.getcwd(), ".claude", "skills")
    else:
        dest = os.path.expanduser("~/.claude/skills")
    os.makedirs(dest, exist_ok=True)

    deps = []
    for s in skills:
        src = os.path.join(ROOT, "skills", s)
        shutil.copytree(src, os.path.join(dest, s), dirs_exist_ok=True)
        if os.path.exists(os.path.join(src, "requirements.txt")):
            deps.append(s)
        print(f"installed {s} -> {dest}")
    print(f"\n{len(skills)} skills installed from pack '{name}'.")
    for s in deps:
        print(f"note: {s} has Python deps — run: cd {os.path.join(dest, s)} && python3 -m pip install -r requirements.txt")


if __name__ == "__main__":
    main()

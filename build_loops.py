#!/usr/bin/env python3
"""build_loops.py — render every loop's Mermaid diagram from its loop.json.

RFC-0028, one-declared-producer rule. Before this script the repo had two
hand-maintained .mmd files that duplicated two README code blocks, with no
producer relationship between them: editing one silently left the other stale.
Now `loop.json` is the single source and both outputs are generated.

Outputs:
  docs/loops/<name>.mmd                    — the standalone Mermaid source
  README.md between <!-- loop:<name>:start/end --> markers

Usage:
  python3 build_loops.py            # write
  python3 build_loops.py --check    # exit 1 if anything on disk is stale
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LOOPS = os.path.join(ROOT, "loops")
OUTDIR = os.path.join(ROOT, "docs", "loops")

HEADER = ("%%{init: {'theme':'base','themeVariables':{'fontFamily':'Segoe UI, Helvetica, Arial',"
          "'fontSize':'15px','lineColor':'#9AA5B1'},'flowchart':{'curve':'basis','rankSpacing':70,"
          "'nodeSpacing':50,'padding':16}}}%%")
CLASSDEFS = [
    "classDef gen    fill:#E8F0FE,stroke:#4C7DF0,stroke-width:1.5px,color:#1A3A8F;",
    "classDef review fill:#FDEAEA,stroke:#E05B5B,stroke-width:1.5px,color:#8A1F1F;",
    "classDef gate   fill:#FBE3A2,stroke:#D9971E,stroke-width:2px,color:#6B4500,font-weight:bold;",
    "classDef ship   fill:#E6F7EC,stroke:#34A853,stroke-width:2px,color:#0F6B33,font-weight:bold;",
]
CLS = {"generate": "gen", "verify": "review", "gate": "gate"}


def _skills(stage):
    s = stage["skills"]
    return "·".join(s) if len(s) <= 2 else f"{s[0]} +{len(s) - 1}"


def render(spec, terminals):
    vclass = {v: m["class"] for v, m in terminals["verdicts"].items()}
    stages = spec["stages"]
    cap = spec.get("cap", 3)
    out = ["flowchart LR", *(f"    {c}" for c in CLASSDEFS), ""]

    for st in stages:
        out.append(f'    {st["id"]}["{st["id"]}<br/><small>{_skills(st)}</small>"]:::{CLS[st["type"]]}')
    for st in stages:
        if "gate" in st:
            g = st["gate"]
            out.append(f'    {g["id"].replace(".", "_")}{{"{g["id"]} · {g["kind"]}"}}:::gate')
    out.append('    DONE(["complete"]):::ship')
    out.append("")

    # Forward spine: stage -> (its gate) -> next stage, last hop into DONE.
    for i, st in enumerate(stages):
        nxt = stages[i + 1]["id"] if i + 1 < len(stages) else "DONE"
        if "gate" in st:
            g = st["gate"]; gid = g["id"].replace(".", "_")
            passing = next((v for v in g["verdicts"] if vclass.get(v) == "pass"), "pass")
            out.append(f'    {st["id"]} --> {gid}')
            out.append(f'    {gid} == "{passing}" ==> {nxt}')
        else:
            out.append(f'    {st["id"]} --> {nxt}')

    # Revision edges, drawn after the spine so the layout stays left-to-right.
    rev = []
    for st in stages:
        g = st.get("gate")
        if g and g.get("revise_to"):
            label = next((v for v in g["verdicts"] if vclass.get(v) == "revise"), "revise")
            rev.append(f'    {g["id"].replace(".", "_")} -- "{label} (max {cap})" --> {g["revise_to"]}')
    if rev:
        out.append("")
        out.extend(rev)
    return "\n".join(out) + "\n"


def build():
    terminals = json.load(open(os.path.join(ROOT, "contracts", "terminals.json")))
    specs = {}
    for d in sorted(os.listdir(LOOPS)):
        p = os.path.join(LOOPS, d, "loop.json")
        if os.path.exists(p):
            specs[d] = json.load(open(p))
    return {name: render(spec, terminals) for name, spec in specs.items()}


def readme_blocks(rendered):
    """Return (updated_readme_text, [names missing a marker pair])."""
    path = os.path.join(ROOT, "README.md")
    text = open(path, encoding="utf-8").read()
    missing = []
    for name, body in rendered.items():
        start, end = f"<!-- loop:{name}:start -->", f"<!-- loop:{name}:end -->"
        pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pat.search(text):
            missing.append(name)
            continue
        text = pat.sub(f"{start}\n\n```mermaid\n{HEADER}\n{body}```\n\n{end}", text)
    return text, missing


def main():
    check = "--check" in sys.argv
    rendered = build()
    stale = []

    os.makedirs(OUTDIR, exist_ok=True)
    for name, body in rendered.items():
        dest = os.path.join(OUTDIR, f"{name}.mmd")
        content = f"{HEADER}\n{body}"
        current = open(dest, encoding="utf-8").read() if os.path.exists(dest) else None
        if current != content:
            stale.append(os.path.relpath(dest, ROOT))
            if not check:
                open(dest, "w", encoding="utf-8").write(content)

    new_readme, missing = readme_blocks(rendered)
    rp = os.path.join(ROOT, "README.md")
    if open(rp, encoding="utf-8").read() != new_readme:
        stale.append("README.md")
        if not check:
            open(rp, "w", encoding="utf-8").write(new_readme)
    for m in missing:
        print(f"build_loops: README.md has no <!-- loop:{m}:start/end --> markers", file=sys.stderr)

    if check:
        if stale or missing:
            for s in stale:
                print(f"build_loops: {s} is stale — run `python3 build_loops.py`", file=sys.stderr)
            return 1
        print("build_loops: all generated diagrams are current")
        return 0
    for s in stale:
        print(f"wrote {s}")
    if not stale:
        print("build_loops: nothing to do")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())


def stale():
    """Paths whose generated content differs from disk. Consumed by validate.py."""
    out, rendered = [], build()
    for name, body in rendered.items():
        dest = os.path.join(OUTDIR, f"{name}.mmd")
        content = f"{HEADER}\n{body}"
        cur = open(dest, encoding="utf-8").read() if os.path.exists(dest) else None
        if cur != content:
            out.append(os.path.relpath(dest, ROOT))
    new_readme, missing = readme_blocks(rendered)
    if open(os.path.join(ROOT, "README.md"), encoding="utf-8").read() != new_readme:
        out.append("README.md")
    out += [f"README.md (no markers for loop '{m}')" for m in missing]
    return out

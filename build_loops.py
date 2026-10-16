#!/usr/bin/env python3
"""build_loops.py — render every loop's Mermaid diagram from its loop.json.

RFC-0028, one-declared-producer rule. Before this script the repo had two
hand-maintained .mmd files that duplicated two README code blocks, with no
producer relationship between them: editing one silently left the other stale.
Now `loop.json` is the single source and both outputs are generated.

Outputs:
  docs/loops/<name>.mmd                    — the standalone Mermaid source
  guides/reference/loops.md between <!-- loop:<name>:start/end --> markers
  (the README carried these until RFC-0035 moved the loop reference into a guide)
  docs/loops/operating-model.svg           — every loop on one picture (RFC-0044), drawn by
                                             the operating-model guide and the site

Usage:
  python3 build_loops.py            # write
  python3 build_loops.py --check    # exit 1 if anything on disk is stale
"""
import json
import os
import re
import sys

import catalog  # where loops live (RFC-0034)

ROOT = os.path.dirname(os.path.abspath(__file__))
DIAGRAM_REL = "guides/reference/loops.md"
DIAGRAM_DOC = os.path.join(ROOT, *DIAGRAM_REL.split("/"))
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
    for d, ldir in catalog.loops().items():
        specs[d] = json.load(open(os.path.join(ldir, "loop.json")))
    return {name: render(spec, terminals) for name, spec in specs.items()}


# ── The operating-model picture (RFC-0044) ────────────────────────────────────
# One SVG with the five lifecycle loops on a rail, each gate where it sits, the two loops
# outside the lifecycle, and the packs that work at any stage. Stages, skills, gates, who
# decides and which pack a loop ships in are all read from loop.json and the pack folders;
# only the plain-English lines for each loop live here, and a loop without them fails --check.
SVG_REL = "docs/loops/operating-model.svg"
SVG_PATH = os.path.join(ROOT, *SVG_REL.split("/"))

# loop: (heading, start here when, ends with). Dict order is lifecycle order.
LIFECYCLE = {
    "discover": ("Find the problem worth solving", "A request, a complaint or a strategy question arrives.",
                 "a requirement a person ratified"),
    "design":   ("Decide how to build it", "The problem is agreed, but not the approach.",
                 "a recorded decision (ADR)"),
    "build":    ("Build it", "The work is clear enough to write down. Bug fixes start here.",
                 "merged code"),
    "release":  ("Ship it", "A merged change needs to reach users safely.",
                 "a live, reversible rollout"),
    "operate":  ("Run it", "The service is live, or something just broke.",
                 "a postmortem and runbook changes"),
}
OUTSIDE = {
    "ship-a-draft": ("Wrap any draft", "Before and after any generator, at any stage.",
                     "a document ready for its reader"),
    "apply":        ("Apply for a job", "One person, one job posting, one resume.",
                     "an application ready to send"),
}
COLOUR = {"discover": "#6d4aff", "design": "#2563eb", "build": "#15803d", "release": "#be185d",
          "operate": "#0e7490"}
NEUTRAL = "#57534e"
WHO = {"mechanical": "a script decides", "review": "a review panel decides", "human": "you decide"}

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"
W, RAIL_X, CARD_X, PAD = 820, 36, 72, 20
CARD_W = W - CARD_X - 24


def _x(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _tw(text, size, mono=False, bold=False):
    """Estimated rendered width. The picture uses system fonts, so this errs wide."""
    return len(text) * size * (0.61 if mono else (0.54 if bold else 0.51))


def _wrap(text, size, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and _tw(trial, size) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def _flow(spec):
    """The loop as tokens: ("skills", text) for each stage, ("gate", text) after a gated one."""
    out = []
    for st in spec["stages"]:
        out.append(("skills", "any generator" if st["skills"] == ["*"] else " / ".join(st["skills"])))
        if "gate" in st:
            g = st["gate"]
            out.append(("gate", f'{g["id"]} · {WHO[g["kind"]]}'))
    return out


def _layout_flow(tokens, width):
    """Place tokens left to right, wrapping; an arrow joins each pair. Returns rows of
    (x, kind, text) with x relative to the flow's left edge."""
    rows, row, x = [], [], 0.0
    for kind, text in tokens:
        w = _tw(text, 12, mono=True) if kind == "skills" else _tw(text, 11.5, bold=True) + 20
        arrow = 22 if row else 0
        if row and x + arrow + w > width:
            rows.append(row)
            row, x, arrow = [("arrow", 0, None)], 22, 0
        if arrow:
            row.append(("arrow", x, None))
            x += arrow
        row.append((kind, x, text))
        x += w
    if row:
        rows.append(row)
    return rows


def _flow_svg(rows, left, top):
    out, y = [], top
    for row in rows:
        for kind, x, text in row:
            if kind == "arrow":
                out.append(f'<text x="{left + x + 5:.1f}" y="{y + 14}" class="arrow">→</text>')
            elif kind == "skills":
                out.append(f'<text x="{left + x:.1f}" y="{y + 14}" class="mono">{_x(text)}</text>')
            else:
                w = _tw(text, 11.5, bold=True) + 20
                out.append(f'<rect x="{left + x:.1f}" y="{y}" width="{w:.1f}" height="20" rx="10" class="gate"/>'
                           f'<text x="{left + x + 10:.1f}" y="{y + 14}" class="gatet">{_x(text)}</text>')
        y += 28
    return out, y


def _card(name, spec, pack, copy, colour, x, y, width, stage_no=None, dashed=False):
    """One loop's card. Returns (svg parts, height)."""
    heading, start, ends = copy
    inner = width - 2 * PAD
    label = (f"STAGE {stage_no} · {name}" if stage_no else name).upper()
    chip_w = _tw(pack, 11, mono=True) + 16
    start_lines = _wrap(f"Start here when {start}", 13, inner)
    rows = _layout_flow(_flow(spec), inner)
    h = 46 + 24 + 18 * len(start_lines) + 10 + 28 * len(rows) + 30
    out = [f'<rect x="{x}" y="{y}" width="{width}" height="{h}" rx="12" class="card{" dashed" if dashed else ""}"/>']
    if not dashed:
        out.append(f'<rect x="{x}" y="{y + 12}" width="4" height="{h - 24}" rx="2" fill="{colour}"/>')
    out.append(f'<text x="{x + PAD}" y="{y + 26}" class="label" fill="{colour}">{_x(label)}</text>')
    cx = x + width - PAD - chip_w
    out.append(f'<rect x="{cx:.1f}" y="{y + 12}" width="{chip_w:.1f}" height="20" rx="10" fill="{colour}" '
               f'fill-opacity=".08" stroke="{colour}" stroke-opacity=".35"/>'
               f'<text x="{cx + 8:.1f}" y="{y + 26}" class="chip" fill="{colour}">{_x(pack)}</text>')
    out.append(f'<text x="{x + PAD}" y="{y + 54}" class="h">{_x(heading)}</text>')
    ty = y + 54 + 24
    for i, line in enumerate(start_lines):
        if i == 0:  # the label, then the rest of the first line
            line = f'<tspan class="startl">Start here when</tspan>{_x(line[len("Start here when"):])}'
        else:
            line = _x(line)
        out.append(f'<text x="{x + PAD}" y="{ty}" class="muted">{line}</text>')
        ty += 18
    flow, fy = _flow_svg(rows, x + PAD, ty - 4)
    out += flow
    out.append(f'<text x="{x + PAD}" y="{fy + 14}" class="ends"><tspan class="endsl">Ends with</tspan> {_x(ends)}</text>')
    return out, h


def operating_model_svg(specs, homes, pack_order):
    """The whole picture as an SVG string. `homes` maps a loop to its pack."""
    body, desc = [], ["Five lifecycle loops, in order."]
    y = 112
    centres = []
    for n, (name, copy) in enumerate(LIFECYCLE.items(), 1):
        part, h = _card(name, specs[name], homes[name], copy, COLOUR[name], CARD_X, y, CARD_W, stage_no=n)
        body += part
        centres.append((y + 22, COLOUR[name], n))
        gates = ", ".join(f'{g["id"]} where {WHO[g["kind"]]}' for g in
                          (st["gate"] for st in specs[name]["stages"] if "gate" in st))
        desc.append(f"Stage {n}, {name}, in the {homes[name]} pack: {copy[0]}. "
                    f"Start here when {copy[1][0].lower()}{copy[1][1:]} Gates: {gates}. Ends with {copy[2]}.")
        y += h + 22
    rail = [f'<line x1="{RAIL_X}" y1="{centres[0][0]}" x2="{RAIL_X}" y2="{centres[-1][0]}" class="rail"/>']
    for cy, colour, n in centres:
        rail.append(f'<circle cx="{RAIL_X}" cy="{cy}" r="14" fill="{colour}"/>'
                    f'<text x="{RAIL_X}" y="{cy + 5}" class="num">{n}</text>')

    y += 8
    body.append(f'<text x="{CARD_X}" y="{y}" class="section">OUTSIDE THE LIFECYCLE</text>')
    y += 14
    half = (CARD_W - 16) / 2
    tallest = 0
    for i, (name, copy) in enumerate(OUTSIDE.items()):
        part, h = _card(name, specs[name], homes[name], copy, NEUTRAL, CARD_X + i * (half + 16), y, half,
                        dashed=True)
        body += part
        tallest = max(tallest, h)
        gates = ", ".join(f'{g["id"]} where {WHO[g["kind"]]}' for g in
                          (st["gate"] for st in specs[name]["stages"] if "gate" in st))
        desc.append(f"Outside the lifecycle, {name}, in the {homes[name]} pack: {copy[0]}. Gates: {gates}.")
    y += tallest + 34

    looped = set(homes.values())
    anystage = [p for p in pack_order if p not in looped]
    body.append(f'<text x="{CARD_X}" y="{y}" class="section">PACKS FOR ANY STAGE</text>')
    y += 14
    x = CARD_X
    for p in anystage:
        w = _tw(p, 12, mono=True) + 20
        if x + w > CARD_X + CARD_W:
            x, y = CARD_X, y + 32
        body.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" class="pack"/>'
                    f'<text x="{x + 10:.1f}" y="{y + 16}" class="mono">{_x(p)}</text>')
        x += w + 8
    desc.append("Packs for any stage: " + ", ".join(anystage) + ".")
    y += 24 + 28
    body.append(f'<text x="{CARD_X}" y="{y}" class="foot">Generated from each loop.json by build_loops.py. '
                f'Codes like G3 are what a loop prints when it stops at a gate.</text>')
    height = y + 22

    style = (f".s,text{{font-family:{SANS};}}"
             f".title{{font-size:24px;font-weight:700;fill:#17171a;}}"
             f".sub{{font-size:14px;fill:#6a6a66;}}"
             f".label{{font-size:11px;font-weight:700;letter-spacing:.08em;}}"
             f".h{{font-size:19px;font-weight:700;fill:#17171a;}}"
             f".muted{{font-size:13px;fill:#5c5c58;}}"
             f".mono,.chip{{font-family:{MONO};font-size:12px;fill:#2a2a2e;}}"
             f".chip{{font-size:11px;}}"
             f".arrow{{font-size:13px;fill:#9a9a94;}}"
             f".gate{{fill:#FBE3A2;stroke:#D9971E;stroke-width:1.2;}}"
             f".gatet{{font-size:11.5px;font-weight:700;fill:#6B4500;}}"
             f".ends{{font-size:13px;fill:#17171a;}}.endsl,.startl{{font-weight:700;}}.startl{{fill:#3f3f3c;}}"
             f".card{{fill:#fff;stroke:#e4e4e0;}}.dashed{{fill:#fafaf9;stroke:#b8b8b2;stroke-dasharray:5 4;}}"
             f".rail{{stroke:#d6d3e6;stroke-width:3;}}"
             f".num{{font-size:13px;font-weight:700;fill:#fff;text-anchor:middle;}}"
             f".section{{font-size:11px;font-weight:700;letter-spacing:.08em;fill:#6a6a66;}}"
             f".pack{{fill:#fff;stroke:#d9d9d4;}}"
             f".foot{{font-size:11.5px;fill:#8a8a85;}}")
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" '
        f'role="img" aria-labelledby="om-title om-desc">',
        '<title id="om-title">How work moves through skilldrop</title>',
        f'<desc id="om-desc">{_x(" ".join(desc))}</desc>',
        f"<style>{style}</style>",
        f'<rect width="{W}" height="{height}" rx="16" fill="#fafaf9"/>',
        f'<text x="{RAIL_X - 14}" y="48" class="title">How work moves through skilldrop</text>',
        f'<text x="{RAIL_X - 14}" y="74" class="sub">Start at the stage your work is in. Each loop stops at its gold gates,'
        f' where a script,</text>',
        f'<text x="{RAIL_X - 14}" y="94" class="sub">a review panel or you decide whether the work moves on.</text>',
    ]
    return "\n".join(head + rail + body + ["</svg>"]) + "\n"


def build_svg():
    specs, homes = {}, {}
    for name, ldir in catalog.loops().items():
        specs[name] = json.load(open(os.path.join(ldir, "loop.json")))
        homes[name] = os.path.basename(os.path.dirname(os.path.dirname(ldir)))
    missing = sorted(set(specs) - set(LIFECYCLE) - set(OUTSIDE))
    gone = sorted((set(LIFECYCLE) | set(OUTSIDE)) - set(specs))
    if missing or gone:
        return None, [f"{SVG_REL}: build_loops.py has no lines for loop '{m}' — add it to LIFECYCLE or OUTSIDE"
                      for m in missing] + [f"{SVG_REL}: build_loops.py names loop '{g}', which does not exist"
                                           for g in gone]
    return operating_model_svg(specs, homes, catalog.pack_names()), []


def readme_blocks(rendered):
    """Return (updated_readme_text, [names missing a marker pair])."""
    path = DIAGRAM_DOC
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
    rp = DIAGRAM_DOC
    if open(rp, encoding="utf-8").read() != new_readme:
        stale.append(DIAGRAM_REL)
        if not check:
            open(rp, "w", encoding="utf-8").write(new_readme)
    for m in missing:
        print(f"build_loops: {DIAGRAM_REL} has no <!-- loop:{m}:start/end --> markers", file=sys.stderr)

    svg, svg_errors = build_svg()
    for e in svg_errors:
        print(f"build_loops: {e}", file=sys.stderr)
    missing = missing + svg_errors
    if svg is not None:
        current = open(SVG_PATH, encoding="utf-8").read() if os.path.exists(SVG_PATH) else None
        if current != svg:
            stale.append(SVG_REL)
            if not check:
                open(SVG_PATH, "w", encoding="utf-8").write(svg)

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
    if open(DIAGRAM_DOC, encoding="utf-8").read() != new_readme:
        out.append(DIAGRAM_REL)
    out += [f"{DIAGRAM_REL} (no markers for loop '{m}')" for m in missing]
    svg, svg_errors = build_svg()
    out += svg_errors
    if svg is not None:
        cur = open(SVG_PATH, encoding="utf-8").read() if os.path.exists(SVG_PATH) else None
        if cur != svg:
            out.append(SVG_REL)
    return out

#!/usr/bin/env python3
"""build_llms.py — generate llms.txt from the catalogue.

llms.txt is the index a model reads instead of crawling 400+ files. It is generated,
not hand-written, for the same reason the loop diagrams are: a hand-maintained index of a
moving catalogue goes stale silently, and a stale index is worse than none because a model
trusts it. Sources: packs.json, loops/*/loop.json, guides/ frontmatter, contracts/, docs/rfcs/.

Usage:
  python3 build_llms.py            # write llms.txt
  python3 build_llms.py --check    # exit 1 if stale (validate.py runs this for you)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/sananthanarayan/skilldrop/main"
DEST = os.path.join(ROOT, "llms.txt")


def _fm(path, key):
    head = open(path, encoding="utf-8").read().split("---")
    fm = head[1] if len(head) >= 3 else ""
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else ""


def render():
    pkg = json.load(open(os.path.join(ROOT, "package.json")))
    packs_doc = json.load(open(os.path.join(ROOT, "packs.json")))
    packs, outcomes = packs_doc["packs"], packs_doc["outcomes"]
    skills = sorted(d for d in os.listdir(os.path.join(ROOT, "skills"))
                    if os.path.isdir(os.path.join(ROOT, "skills", d)))
    loops = sorted(d for d in os.listdir(os.path.join(ROOT, "loops"))
                   if os.path.exists(os.path.join(ROOT, "loops", d, "loop.json")))
    agents = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, "agents"))
                    if f.endswith(".md") and f != "README.md")

    L = [f"# skilldrop\n"]
    L.append(
        f"> {len(skills)} portable skills for the artifacts knowledge work ships (ADRs, design docs,\n"
        f"> PRDs, runbooks, threat models, decks, postmortems), plus {len(loops)} loops that sequence them\n"
        f"> behind gates. A loop orders skills; a skill never calls a skill, so every one of the\n"
        f"> {len(skills)} installs and runs alone by folder copy in Claude Code, Cursor, Kiro, Codex,\n"
        f"> Copilot and Antigravity. Zero runtime dependencies. This file indexes the docs so a tool\n"
        f"> can read the few relevant pages instead of the whole tree. Links are raw file content.\n"
        f"> Version {pkg['version']}.\n")

    L.append("## Start here\n")
    for path, note in [
        ("README.md", "what the project is, the loops, the install quickstart, and the full skill table."),
        ("ARCHITECTURE.md", "the four primitives, the install contract, the enforcement model, the invariants. Read before proposing a structural change."),
        ("AGENTS.md", "the canonical agent-context file — conventions, file placement, voice, and the pre-commit checklist."),
        ("guides/README.md", "index of the long-form guides, split by Diátaxis kind."),
    ]:
        L.append(f"- [{path}]({RAW}/{path}): {note}")
    L.append("")

    L.append("## Loops — the operating model\n")
    L.append("Four loops cover the lifecycle and are separated by reversibility (how expensive the\n"
             "mistake is to unwind), which is also what decides who may sign off. One wrapper applies\n"
             "to any generator.\n")
    for n in loops:
        spec = json.load(open(os.path.join(ROOT, "loops", n, "loop.json")))
        stages = " -> ".join(st["id"] for st in spec["stages"])
        gates = ", ".join(f"{st['gate']['id']} ({st['gate']['kind']})"
                          for st in spec["stages"] if st.get("gate")) or "none"
        L.append(f"- [{n}]({RAW}/loops/{n}/LOOP.md) — *{spec['kind']}*, cap {spec.get('cap', 3)}. "
                 f"Stages: {stages}. Gates: {gates}.")
    L.append("")

    L.append("## Machine-readable contracts\n")
    L.append("Closed schemas — an unknown key is a failure, not an extension point. Checked by a\n"
             "stdlib JSON Schema subset in validate.py, never by a dependency.\n")
    for f in sorted(os.listdir(os.path.join(ROOT, "contracts"))):
        c = json.load(open(os.path.join(ROOT, "contracts", f))).get("$comment", "")
        # Drop the leading "RFC-0028." / "RFC-0012 / RFC-0029." provenance prefix — the
        # sentence after it is the one that says what the contract is for.
        body = re.sub(r"^(?:RFC-\d+\s*(?:/\s*RFC-\d+\s*)*)[.\u2014-]\s*", "", c).strip()
        blurb = re.split(r"(?<=[.!?])\s", body)[0] if body else ""
        L.append(f"- [contracts/{f}]({RAW}/contracts/{f}): {blurb}")
    L.append("")

    L.append("## Guides\n")
    for g in sorted(glob.glob(os.path.join(ROOT, "guides", "**", "*.md"), recursive=True)):
        if os.path.basename(g) == "README.md":
            continue
        rel = os.path.relpath(g, ROOT)
        L.append(f"- [{_fm(g, 'title')}]({RAW}/{rel}) *({_fm(g, 'kind')})*: {_fm(g, 'summary')}")
    L.append("")

    L.append("## Role packs\n")
    for name, p in packs.items():
        lp = f", loops: {', '.join(p.get('loops', []))}" if p.get("loops") else ""
        L.append(f"- **{name}** ({len(p['skills'])} skills{lp}): {p['description']}")
    L.append("")

    L.append("## Outcomes — browse by why you are here\n")
    for name, o in outcomes.items():
        L.append(f"- **{name}** ({len(o['skills'])} skills): {o['description']}")
    L.append("")

    L.append("## Reviewer subagents\n")
    for a in agents:
        L.append(f"- [{a}]({RAW}/agents/{a}.md): {_fm(os.path.join(ROOT, 'agents', a + '.md'), 'description')}")
    L.append("")

    L.append("## The full catalogue\n")
    L.append(f"- [catalogue.json](https://sananthanarayan.github.io/skilldrop/catalogue.json): every skill, "
             f"loop, pack and outcome as machine-readable JSON — name, description, tier, tags, related. "
             f"Prefer this over scraping the site.")
    L.append(f"- [model-routing.json]({RAW}/model-routing.json): the abstract tier per skill "
             f"(light/standard/heavy) and the provider map that resolves a tier to a concrete model.")
    L.append(f"- [packs.json]({RAW}/packs.json): pack and outcome membership.")
    L.append(f"- All {len(skills)} skills live at `skills/<name>/SKILL.md`; each has a `manifest.json` "
             f"beside it. Fetch one directly: `{RAW}/skills/<name>/SKILL.md`.")
    L.append("")

    L.append("## Optional\n")
    L.append(f"- [CHANGELOG.md]({RAW}/CHANGELOG.md): what shipped in each release.")
    L.append(f"- [docs/rfcs/]({RAW}/docs/rfcs/0000-template.md): {len(glob.glob(os.path.join(ROOT, 'docs', 'rfcs', '*.md'))) - 1} "
             f"accepted RFCs record why each structural decision was made.")
    L.append(f"- [CONTRIBUTING.md]({RAW}/CONTRIBUTING.md): the contributor lanes and gates.")
    return "\n".join(L) + "\n"


def stale():
    want = render()
    have = open(DEST, encoding="utf-8").read() if os.path.exists(DEST) else None
    return ["llms.txt"] if have != want else []


def main():
    if "--check" in sys.argv:
        if stale():
            print("build_llms: llms.txt is stale — run `python3 build_llms.py`", file=sys.stderr)
            return 1
        print("build_llms: llms.txt is current")
        return 0
    open(DEST, "w", encoding="utf-8").write(render())
    print(f"wrote llms.txt ({len(render().splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

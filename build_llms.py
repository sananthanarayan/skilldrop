#!/usr/bin/env python3
"""build_llms.py — generate llms.txt from the catalogue.

llms.txt is the index a model reads instead of crawling 400+ files. It is generated,
not hand-written, for the same reason the loop diagrams are: a hand-maintained index of a
moving catalogue goes stale silently, and a stale index is worse than none because a model
trusts it. Sources: catalogue.json, packs/*/pack.json, packs/*/loops/*/loop.json, guides/
frontmatter, contracts/, docs/rfcs/.

Usage:
  python3 build_llms.py            # write llms.txt
  python3 build_llms.py --check    # exit 1 if stale (validate.py runs this for you)
"""
import glob
import json
import os
import re
import sys

import catalog  # where skills, loops and packs live (RFC-0034)

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
    packs, outcomes = catalog.packs(), catalog.outcomes()
    skills = sorted(catalog.skills())
    loop_dirs = catalog.loops()
    loops = sorted(loop_dirs)
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
        ("README.md", "what the project is, the role packs, and the one-command quick start."),
        ("guides/reference/skill-catalogue.md", "every skill, one line each, grouped by category."),
        ("guides/reference/loops.md", "every loop's stages and gates."),
        ("ARCHITECTURE.md", "the four primitives, the install contract, the enforcement model, the invariants. Read before proposing a structural change."),
        ("AGENTS.md", "the canonical agent-context file — conventions, file placement, voice, and the pre-commit checklist."),
        ("guides/README.md", "index of the long-form guides, split by Diátaxis kind."),
    ]:
        L.append(f"- [{path}]({RAW}/{path}): {note}")
    L.append("")

    L.append("## Loops — the operating model\n")
    L.append("Five loops cover the lifecycle and are separated by reversibility (how expensive the\n"
             "mistake is to unwind), which is also what decides who may sign off. One wrapper applies\n"
             "to any generator.\n")
    for n in loops:
        spec = json.load(open(os.path.join(loop_dirs[n], "loop.json")))
        stages = " -> ".join(st["id"] for st in spec["stages"])
        gates = ", ".join(f"{st['gate']['id']} ({st['gate']['kind']})"
                          for st in spec["stages"] if st.get("gate")) or "none"
        L.append(f"- [{n}]({RAW}/{catalog.rel(loop_dirs[n])}/LOOP.md) — *{spec['kind']}*, cap {spec.get('cap', 3)}. "
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

    L.append("## Packs\n")
    L.append("Each skill and loop sits in exactly one pack folder, `packs/<pack>/`. Every role pack\n"
             "except `claude-api` requires `core`, which installs with it.\n")
    for name, p in packs.items():
        lp = f", loops: {', '.join(p.get('loops', []))}" if p.get("loops") else ""
        req = f", requires {', '.join(p['requires'])}" if p.get("requires") else ""
        L.append(f"- **{name}** ({len(p['skills'])} skills{lp}{req}): {p['description']}")
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
    L.append(f"- [catalogue.json]({RAW}/catalogue.json): pack display order and outcome membership; "
             f"each pack's metadata is in `packs/<pack>/pack.json`.")
    L.append(f"- All {len(skills)} skills live at `packs/<pack>/skills/<name>/SKILL.md`; each has a "
             f"`manifest.json` beside it. Fetch one directly: `{RAW}/packs/<pack>/skills/<name>/SKILL.md`.")
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

#!/usr/bin/env python3
"""Catalogue site generator for skilldrop. No deps, no network. Run from the repo root:

    python3 build_site.py              # writes build/index.html + build/catalogue.json
    python3 build_site.py --out <dir>  # write somewhere else
    python3 build_site.py --check      # exit 1 if build/ differs from a fresh render

Every skill fact on the page comes from packs/<pack>/skills/<name>/manifest.json, catalogue.json, or
model-routing.json. A description typed into this file would be a fourth copy of a
string validate.py already keeps in sync across two (RFC-0011).

The prose (hero, section headings, the tool matrix) is the page's own copy and lives in
the PITCH and TOOLS blocks below — the one place to edit wording. Every claim in it is
checkable against the repo; the tool matrix lists only paths confirmed in
docs/designs/ide-primitive-coverage.md, which is why Gemini CLI is absent.

The page is one self-contained file: CSS and JS inline, no external requests, no absolute
paths. That is what makes it work unchanged under the /skilldrop/ project-pages base path.

RFC-0026 added three sources, all read the same way — never retyped here: the `outcomes`
block in catalogue.json (the second browse axis), CHANGELOG.md (the Recently shipped strip),
and the version in package.json. The changelog's newest version must match package.json or
the build refuses, for the same reason collect() refuses a half-row catalogue.
"""
import argparse
import build_llms  # llms.txt is served at the site root too (RFC-0030)
import catalog     # where skills, loops and packs live (RFC-0034)
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
# Binary assets copied verbatim into the build (og.png is rendered once from assets/og.svg
# with rsvg-convert and committed, so the build itself stays stdlib-only).
BINARY_ASSETS = ["og.png"]
REPO_URL = "https://github.com/sananthanarayan/skilldrop"
NPM_URL = "https://www.npmjs.com/package/skilldrop-cli"
# How many skill rows render before the "show all" button. Past this the list stops being
# scannable and starts being a dump; a query, a filter, or a deep link reveals the rest.
PREVIEW_ROWS = 8
# How many releases the "Recently shipped" strip carries. Three is enough to show a pulse
# without turning the landing page into a changelog.
SHIPPED_ENTRIES = 3
ROADMAP_ENTRIES = 4  # how many upcoming items the "Now" strip shows
SITE_URL = "https://sananthanarayan.github.io/skilldrop/"

def _pack_total(name):
    """Skills one `install --pack <name>` delivers: the pack's own plus what it requires."""
    p = catalog.packs()
    return len(set(p[name]["skills"]).union(*(p[r]["skills"] for r in p[name].get("requires", []))))


# --- page copy -------------------------------------------------------------------
PITCH = {
    "hero_h1": "Your agent can draft anything. What ships is still your call.",
    "hero_lede": (
        "skilldrop is six loops over 63 portable skills, and nothing leaves a loop until its gate "
        "passes — a script, a review panel, or a person, chosen by how expensive the mistake is to "
        "undo. Every skill is still a plain folder you copy into your agent. No runtime, no platform, "
        "no transformation on the way in."
    ),
    "tension_h2": "Generic agents are fluent about everything and opinionated about nothing.",
    "tension_body": (
        "Ask one for an ADR and it returns a plausible document with five hedged options and no "
        "decision. The gap is not model capability — it is that nothing told it what a good ADR "
        "refuses to do. Every skilldrop skill carries that judgment with it."
    ),
    "quality_h2": "The output is a file. You own it.",
    "quality_lede": (
        "Every skill targets a specific deliverable — an ADR, a PRD, a runbook, a deck — not a "
        "conversation. The file is yours to version, review, and ship. Four things are enforced "
        "before a skill lands, by validate.py in CI:"
    ),
    "tools_h2": "One folder. Every major agent.",
    "tools_lede": (
        "Every skill is a plain SKILL.md folder — the Agent Skills open standard — so the same folder "
        "runs unchanged across tools; only the directory differs, and several tools deliberately read "
        "each other's. Paths below are the ones confirmed in the July 2026 survey."
    ),
    "install_h2": "Start in one command.",
    "catalogue_h2": "The catalogue.",
    "shipped_h2": "Still moving.",
    "shipped_lede": (
        "Every release is a version on npm and a line here. Nothing on this page is a roadmap — "
        "it is what already shipped, so it can be checked."
    ),
    "reviewers_h2": "Skills generate. Reviewers push back.",
    "reviewers_lede": (
        "Three reviewer subagents ship alongside the skills — each a separate pass, because "
        "bug-hunting, exploitability and craft pull in different directions and one merged "
        "reviewer dilutes all three. Install the panel in one command and pre-merge-review "
        "fires them in parallel wherever your tool has native subagents."
    ),
    "closing_h2": "Copy a folder. Keep the artifact.",
    "footer_tagline": "Portable skills for the deliverables knowledge work actually ships.",
    "closing_body": (
        "Nothing here needs an account, a runtime, or a migration. Install one skill, run it once, "
        "and keep it only if the output was worth keeping."
    ),
}

QUALITY = [
    ("Quality bar", "A checkable standard for the output — not adjectives. A skill without one is a description, not a generator."),
    ("Anti-patterns", "The specific mistakes the skill refuses to make, named and countered with a passing example beside a failing one."),
    ("Acceptance evals", "Realistic prompts with assertions, plus phrases that should <em>not</em> trigger the skill — so the description stays honest."),
    ("Model tier", "A provider-neutral <code>light</code>/<code>standard</code>/<code>heavy</code> hint that travels with the skill, so cheap work runs cheap."),
]

# Only paths confirmed in docs/designs/ide-primitive-coverage.md. Anything unsurveyed is absent
# rather than guessed — an invented install path is worse than a missing row.
TOOLS = [
    ("Claude Code", "~/.claude/skills/ · .claude/skills/", "skilldrop install", True),
    ("Cursor", ".cursor/skills/ + a .cursor/rules/*.mdc pointer", "skilldrop install --ide cursor", True),
    ("Kiro IDE + CLI", ".kiro/skills/ · ~/.kiro/skills/", "skilldrop install --ide kiro", True),
    ("OpenAI Codex", ".agents/skills/ · ~/.codex/skills/", "skilldrop install --dest .agents/skills", False),
    ("GitHub Copilot", ".github/skills/ — its CLI also reads .claude/skills/ and .agents/skills/", "skilldrop install --dest .github/skills", False),
    ("Antigravity CLI", ".agents/skills/ · ~/.gemini/antigravity-cli/skills/", "skilldrop install --dest .agents/skills", False),
]
# Gemini CLI is absent on purpose, not by omission: Google retired it for free, AI Pro, Ultra
# and individual Code Assist users on 2026-06-18, leaving only Standard/Enterprise licences.
# Antigravity CLI is its successor and is listed above. Listing a tool that no longer serves
# this audience would be worse than the gap.

NAV = [
    ("Why skills", "#problem", False),
    ("Loops", "#loops", False),
    ("Outcomes", "#outcomes", False),
    ("What's in one", "#quality", False),
    ("Portability", "#portability", False),
    ("Catalogue", "catalogue/", False),
    ("Reviewers", "#reviewers", False),
    ("Now", "#now", False),
    ("Docs", "docs/", False),
    ("Shipped", "#shipped", False),
    ("Contributing", f"{REPO_URL}/blob/main/CONTRIBUTING.md", True),
    ("GitHub", REPO_URL, True),
]

# Guides by Diátaxis kind. Each tuple: (title, path-from-repo-root, one-line description).
# Path is used to build the GitHub blob URL; keep it relative to repo root.
GUIDES = {
    "Tutorial": {
        "tagline": "Learn by doing something real.",
        "items": [
            ("Follow one change through the loops",
             "guides/tutorial/follow-a-change-through-the-loops.md",
             "One realistic change from complaint to closed incident — every gate shown"),
            ("From complaint to closed incident", "guides/tutorial/complaint-to-closed-incident.md", "discover → operate: support complaint to root-cause fix and postmortem"),
            ("From idea to shipped feature",      "guides/tutorial/idea-to-shipped-feature.md",      "All four lifecycle loops: idea → design → build → operate → closed incident"),
            ("Dev-team workflow",             "guides/tutorial/dev-team-workflow.md",             "Story → implementation → review panel → release notes"),
            ("Solution architect workflow",   "guides/tutorial/solution-architect-workflow.md",   "Brief → diagrams → ADRs → design doc → threat model → council gate"),
            ("Product manager workflow",      "guides/tutorial/product-manager-workflow.md",      "Signal → PR/FAQ → OKRs → PRD → metrics → critique gate"),
            ("AI engineering workflow",       "guides/tutorial/ai-engineering-workflow.md",       "Use-case triage → readiness → loop design → threat model → evals → usage report"),
        ],
    },
    "How-to": {
        "tagline": "I have a goal — what are the steps?",
        "items": [
            ("Install into your IDE",           "guides/how-to/install-per-ide.md",            "Per-IDE steps for every target, plus dependency installs"),
            ("Install a profile",               "guides/how-to/profiles.md",                   "Named bundles of packs, agents, and loops — one command for a complete setup"),
            ("Author a new skill",              "guides/how-to/author-a-skill.md",             "What a skill must contain and what gates it"),
            ("Author a new loop",               "guides/how-to/author-a-loop.md",              "The closed loop.json contract and the gate rules"),
            ("Wire a skill to an event",        "guides/how-to/wire-a-hook.md",                "Opt-in hooks, projected per target"),
            ("Publish your own catalogue",      "guides/how-to/publish-a-catalogue.md",        "Make skilldrop --from <you> work"),
            ("Upgrade installed skills",        "guides/how-to/upgrade-skills.md",             "Keep installed skills current without clobbering your settings"),
            ("Roll out across your org",        "guides/how-to/enterprise-distribution.md",    "Bootstrap the hosted marketplace for every machine in one command"),
            ("Use with Jira",                   "guides/how-to/integrate-with-jira.md",        "Bug triage, story splitting, implementation loops, and release notes from Jira tickets"),
            ("Use with GitHub Projects",        "guides/how-to/integrate-with-github-projects.md", "Implementation loops, review gates, and release notes linked to GitHub issues"),
            ("Use with Figma",                  "guides/how-to/integrate-with-figma.md",       "Generate diagrams for FigJam, reverse-engineer decisions from mockups"),
            ("Use with Linear",                 "guides/how-to/integrate-with-linear.md",      "Triage, story splitting, implementation tracking, and release notes from Linear issues"),
            ("Supply credentials to skills",    "guides/how-to/supply-credentials.md",         "How to set FIGMA_TOKEN, SONAR_TOKEN, and other env vars locally, in CI, and via secret managers"),
        ],
    },
    "Reference": {
        "tagline": "What exactly does this field or command do?",
        "items": [
            ("Skills that ship scripts", "guides/reference/skills-with-scripts.md", "The two skills with executable helpers and what they do"),
            ("Model routing",            "MODEL-ROUTING.md",                         "Abstract tiers, the provider map, and how to override"),
        ],
    },
    "Explanation": {
        "tagline": "Why is it built this way?",
        "items": [
            ("Architecture",  "ARCHITECTURE.md",              "Four primitives, the install contract, the enforcement table, five invariants"),
            ("Why loops",     "guides/explanation/loops.md",  "Why sequencing is its own primitive and why four lifecycle loops"),
        ],
    },
}

INSTALL_TABS = [
    ("a role pack", "npx skilldrop-cli install --pack solution-architect", f"{_pack_total('solution-architect')} skills a solution architect reaches for, core included, in one command."),
    ("one skill", "npx skilldrop-cli install adr-generator --with-related", "--with-related also pulls the companions it hands off to."),
    ("by hand", "cp -R packs/solution-architect/skills/adr-generator ~/.claude/skills/", "No CLI required. The folder is the whole install."),
    ("stay current", "npx skilldrop-cli outdated && npx skilldrop-cli update", "Skills improve; cp -R never tells you. Files you edited are kept, with the new version beside them as .upstream."),
]


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect():
    """Manifests + packs + tiers -> one list of skill records. Fails loudly."""
    packs = catalog.packs()
    skill_dirs = catalog.skills()
    tiers = read_json(os.path.join(ROOT, "model-routing.json"))["skills"]

    pack_of = {}
    for pack_name, pack in packs.items():
        for s in pack["skills"]:
            pack_of.setdefault(s, []).append(pack_name)

    names = sorted(
        d for d in skill_dirs
        if os.path.isfile(os.path.join(skill_dirs[d], "manifest.json"))
    )
    skills, problems = [], []
    for name in names:
        m = read_json(os.path.join(skill_dirs[name], "manifest.json"))
        if name not in pack_of:
            problems.append(f"{name}: in no pack")
        if name not in tiers:
            problems.append(f"{name}: no entry in model-routing.json")
        skills.append({
            "name": name,
            "path": catalog.rel(skill_dirs[name]),
            "description": m["description"],
            "version": m["version"],
            "tier": m.get("model", {}).get("tier", ""),
            "rationale": m.get("model", {}).get("rationale", ""),
            "tags": m.get("tags", []),
            "related": m.get("related", []),
            "packs": pack_of.get(name, []),
            "deps": bool(m.get("deps", {}).get("pip") or m.get("deps", {}).get("npm")),
            "env": m.get("env", {}).get("required", []),
            "hooks": [h.get("event") for h in m.get("hooks", [])],
        })

    if problems:
        # A half-row on the site is worse than no site: it looks authoritative.
        print("build_site.py: refusing to build — the catalogue is inconsistent:", file=sys.stderr)
        for p in problems:
            print("  FAIL", p, file=sys.stderr)
        sys.exit(1)

    pack_meta = [{"name": k, "description": v["description"],
                  "count": len(v["skills"]), "skills": sorted(v["skills"]),
                  "requires": v.get("requires", [])}
                 for k, v in packs.items()]

    # RFC-0026: outcomes are the second browse axis, read from the same file as packs.
    # validate.py guarantees every skill appears in one, so a chip can never be a dead end.
    doc = {"outcomes": catalog.outcomes()}
    outcome_of = {}
    for oname, o in doc.get("outcomes", {}).items():
        for sk in o["skills"]:
            outcome_of.setdefault(sk, []).append(oname)
    for sk in skills:
        sk["outcomes"] = outcome_of.get(sk["name"], [])
    outcome_meta = [{"name": k, "description": v["description"], "count": len(v["skills"])}
                    for k, v in doc.get("outcomes", {}).items()]

    return skills, pack_meta, outcome_meta


RELEASE_RE = re.compile(r"^##\s+(\d+\.\d+\.\d+)\s+[—-]\s+(\d{4}-\d{2}-\d{2})\s*$")


def changelog():
    """CHANGELOG.md -> [{version, date, bullets}], newest first. The newest entry must match
    package.json, or a release could ship with nothing said about it — the same refuse-to-render
    discipline collect() applies to a half-row skill."""
    path = os.path.join(ROOT, "CHANGELOG.md")
    version = read_json(os.path.join(ROOT, "package.json"))["version"]
    releases, current = [], None
    for line in open(path, encoding="utf-8"):
        m = RELEASE_RE.match(line.rstrip())
        if m:
            current = {"version": m.group(1), "date": m.group(2), "bullets": []}
            releases.append(current)
        elif current is not None and line.startswith("- "):
            current["bullets"].append(line[2:].strip())

    if not releases:
        print("build_site.py: refusing to build — CHANGELOG.md has no `## <version> — <date>` "
              "entries", file=sys.stderr)
        sys.exit(1)
    if releases[0]["version"] != version:
        print(f"build_site.py: refusing to build — CHANGELOG.md leads with "
              f"{releases[0]['version']} but package.json says {version}. One of them is wrong.",
              file=sys.stderr)
        sys.exit(1)
    return version, releases[:SHIPPED_ENTRIES]


def roadmap():
    """ROADMAP.md -> list of bullet strings under ## Upcoming, up to ROADMAP_ENTRIES items."""
    path = os.path.join(ROOT, "ROADMAP.md")
    if not os.path.exists(path):
        print("build_site.py: refusing to build — ROADMAP.md is missing", file=sys.stderr)
        sys.exit(1)
    items, in_upcoming = [], False
    for line in open(path, encoding="utf-8"):
        if line.strip() == "## Upcoming":
            in_upcoming = True
            continue
        if in_upcoming and line.startswith("## "):
            break
        if in_upcoming and line.startswith("- "):
            items.append(line[2:].strip())
    if not items:
        print("build_site.py: refusing to build — ROADMAP.md has no bullets under ## Upcoming",
              file=sys.stderr)
        sys.exit(1)
    return items[:ROADMAP_ENTRIES]


def esc(s):
    return html.escape(str(s), quote=True)


def inline_md(s):
    """Escape first, then re-admit the only two inline marks a changelog bullet uses.
    Anything richer belongs in CHANGELOG.md, not on the landing page."""
    out = esc(s)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)


def card(s):
    """One compact row. The full description is one clamped line — the whole point of the
    redesign is that the page does not dump 49 paragraphs at a reader who hasn't chosen yet.
    Tags and `related` are deliberately absent: they live in catalogue.json and on GitHub."""
    tier = s["tier"]
    return f"""<li class="skill" id="{esc(s['name'])}"
   data-tier="{esc(tier)}" data-packs="{esc(' '.join(s['packs']))}"
   data-outcomes="{esc(' '.join(s.get('outcomes', [])))}"
   data-text="{esc((s['name'] + ' ' + s['description'] + ' ' + ' '.join(s['tags'])).lower())}">
  <a class="skill__link" href="{REPO_URL}/blob/main/{esc(s['path'])}/SKILL.md"
     title="{esc(s['description'])}">
    <span class="skill__name">{esc(s['name'])}</span>
    <span class="skill__desc">{esc(s['description'])}</span>
  </a>
  <span class="tier tier--{esc(tier)}" title="{esc(s['rationale'])}">{esc(tier)}</span>
</li>"""


def terminal(lines):
    body = "".join(
        f'<div class="term__line"><span class="term__prompt">$</span> {esc(c)}</div>'
        for c in lines
    )
    return f"""<div class="term"><div class="term__bar">
  <span class="term__dot"></span><span class="term__dot"></span><span class="term__dot"></span>
</div><div class="term__body">{body}</div></div>"""


def render(skills, packs, outcomes, version, releases):
    tiers = ["light", "standard", "heavy"]
    tier_counts = {t: sum(1 for s in skills if s["tier"] == t) for t in tiers}

    loop_list = loops()
    stats = [(str(len(skills)), "skills"), (str(len(loop_list)), "loops"),
             (str(len(packs)), "packs"), ("0", "runtime deps")]
    stats_html = "".join(
        f'<div class="stat"><div class="stat__n">{esc(n)}</div><div class="stat__l">{esc(l)}</div></div>'
        for n, l in stats)

    quality_html = "".join(
        f'<article class="qcard"><h3>{esc(t)}</h3><p>{b}</p></article>' for t, b in QUALITY)

    tools_html = "".join(
        f"""<tr><th scope="row">{esc(n)}</th><td><code>{esc(p)}</code></td>
        <td><code class="cmd">{esc(c)}</code></td>
        <td class="cap">{'<span class="cap--yes">native flag</span>' if flag else '<span class="cap--no">via --dest</span>'}</td></tr>"""
        for n, p, c, flag in TOOLS)

    tabs = ""
    for i, (label, cmd, note) in enumerate(INSTALL_TABS):
        checked = " checked" if i == 0 else ""
        tabs += f'<input class="tabs__radio" type="radio" name="itab" id="itab{i}"{checked}>'
    labels = "".join(
        f'<label class="tabs__label" for="itab{i}">{esc(l)}</label>'
        for i, (l, _, _) in enumerate(INSTALL_TABS))
    panels = "".join(
        f'<div class="tabs__panel">{terminal([c])}<p class="tabs__note">{esc(n)}</p></div>'
        for _, c, n in INSTALL_TABS)

    def humanize_slug(slug):
        _overrides = {
            "build-on-the-claude-api": "Build on the Claude API",
            "govern-ai-use": "Govern AI use",
        }
        if slug in _overrides:
            return _overrides[slug]
        return slug.replace("-", " ").capitalize()

    outcome_cards = "".join(
        f"""<li class="pack">
      <div class="pack__head">
        <h3 class="pack__name">{esc(humanize_slug(o['name']))}</h3><span class="pack__n">{o['count']} skills</span>
      </div>
      <p class="pack__desc">{esc(o['description'])}</p>
      <button class="pack__cta" data-filter="outcome" data-value="{esc(o['name'])}">Filter the catalogue &rarr;</button>
    </li>""" for o in outcomes)

    guides_html = "".join(
        f"""<div class="guides-group">
      <h3>{esc(kind)}</h3>
      <p class="guides-tagline">{esc(meta['tagline'])}</p>
      <ul>{"".join(
        f'<li><a href="{REPO_URL}/blob/main/{esc(path_)}">{esc(title)}</a>'
        f'<span class="guides-desc">{esc(desc)}</span></li>'
        for title, path_, desc in meta['items']
      )}</ul>
    </div>"""
        for kind, meta in GUIDES.items())

    loop_cards = "".join(
        f"""<li class="pack">
      <div class="pack__head">
        <h3 class="pack__name">{esc(lp['name'])}</h3><span class="pack__n">{esc(lp['kind'])} &middot; cap {lp['cap']}</span>
      </div>
      <p class="pack__desc">{esc(lp['description'])}</p>
      <p class="pack__desc"><code>{esc(' \u2192 '.join(st['id'] for st in lp['stages']))}</code></p>
      <p class="pack__desc">Gates: {esc(', '.join(f"{st['gate']['id']} ({st['gate']['kind']})" for st in lp['stages'] if st['gate']) or 'none')}</p>
      <p class="pack__install"><code>skilldrop install --loop {esc(lp['name'])}</code></p>
    </li>""" for lp in loop_list)

    agent_cards = "".join(
        f"""<li class="pack">
      <div class="pack__head">
        <h3 class="pack__name">{esc(a['name'])}</h3><span class="pack__n">subagent</span>
      </div>
      <p class="pack__desc">{esc(a['description'])}</p>
      <p class="pack__install"><code>skilldrop install --agent {esc(a['name'])}</code></p>
    </li>""" for a in agents())

    pack_cards = "".join(
        f"""<li class="pack">
      <div class="pack__head">
        <h3 class="pack__name"><a href="packs/{esc(p['name'])}/">{esc(p['name'])}</a></h3><span class="pack__n">{p['count']} skills{''.join(' + ' + esc(r) for r in p['requires'])}</span>
      </div>
      <p class="pack__desc">{esc(p['description'])}</p>
      <p class="pack__install"><code>skilldrop install --pack {esc(p['name'])}</code></p>
      <button class="pack__cta" data-filter="pack" data-value="{esc(p['name'])}">See what's inside &rarr;</button>
    </li>""" for p in packs)

    pack_chips = "".join(
        f'<button class="chip" data-filter="pack" data-value="{esc(p["name"])}">{esc(p["name"])} <b>{p["count"]}</b></button>'
        for p in packs)
    tier_chips = "".join(
        f'<button class="chip chip--{t}" data-filter="tier" data-value="{t}">{t} <b>{tier_counts[t]}</b></button>'
        for t in tiers)
    outcome_chips = "".join(
        f'<button class="chip" data-filter="outcome" data-value="{esc(o["name"])}" '
        f'title="{esc(o["description"])}">{esc(o["name"].replace("-", " "))} <b>{o["count"]}</b></button>'
        for o in outcomes)
    roadmap_items = roadmap()
    roadmap_html = "".join(
        f'<li class="roadmap-item">{inline_md(item)}</li>'
        for item in roadmap_items)
    shipped_html = "".join(
        f"""<li class="ship">
      <p class="ship__head"><a class="ship__v" href="{NPM_URL}/v/{esc(r['version'])}">{esc(r['version'])}</a>
        <time class="ship__d" datetime="{esc(r['date'])}">{esc(r['date'])}</time></p>
      <ul class="ship__list">{"".join(f'<li>{inline_md(b)}</li>' for b in r['bullets'])}</ul>
    </li>""" for r in releases)
    cards = "\n".join(card(s) for s in skills)
    preview_cards = "\n".join(card(s) for s in skills[:PREVIEW_ROWS])
    nav_links = "".join(
        f'<li><a class="nav__link{" nav__link--ext" if ext else ""}" href="{esc(href)}">'
        f'{esc(label)}{" <span aria-hidden=\"true\">&#8599;</span>" if ext else ""}</a></li>'
        for label, href, ext in NAV)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skilldrop — portable skills for agentic IDEs</title>
<meta name="description" content="{esc(PITCH['hero_lede'])}">
<link rel="canonical" href="{SITE_URL}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#111113">
<meta property="og:type" content="website">
<meta property="og:site_name" content="skilldrop">
<meta property="og:title" content="skilldrop">
<meta property="og:description" content="{esc(PITCH['hero_h1'])}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="skilldrop — a prompt gets you a draft, a skill gets you a deliverable">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="skilldrop">
<meta name="twitter:description" content="{esc(PITCH['hero_h1'])}">
<meta name="twitter:image" content="{SITE_URL}og.png">
<script type="application/ld+json">{json.dumps(ld_json(skills), separators=(",", ":"))}</script>
<style>
:root {{
  --dark-950:#0d0d0f; --dark-900:#141417; --dark-800:#1d1d21;
  --n-50:#fafaf9; --n-100:#f3f3f1; --n-200:#e4e4e0; --n-600:#6a6a66; --n-900:#17171a;
  --accent:#7c5cff; --accent-300:#a48cff; --accent-700:#4c31d6; --accent-10:rgba(124,92,255,.10);
  --w-06:rgba(255,255,255,.06); --w-10:rgba(255,255,255,.10);
  --w-20:rgba(255,255,255,.20); --w-60:rgba(255,255,255,.60); --w-80:rgba(255,255,255,.80);
  --surface:var(--n-50); --surface-alt:var(--n-100); --fg:var(--n-900);
  --fg-muted:var(--n-600); --border:var(--n-200); --card:#fff;
  --display:clamp(2.4rem,5.5vw,3.9rem); --h2:clamp(1.7rem,3.2vw,2.5rem);
  --gap:clamp(4.5rem,9vw,7.5rem); --pad-x:clamp(1.25rem,5vw,2.5rem); --max:1140px;
  --r-sm:5px; --r:10px; --r-lg:16px;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --surface:#111113; --surface-alt:#17171a; --fg:#ecebe8; --fg-muted:#9a9a95;
    --border:#2a2a2d; --card:#1a1a1d; --accent:#a48cff; --accent-700:#c4b5ff;
    --accent-10:rgba(164,140,255,.12);
  }}
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  margin:0; background:var(--surface); color:var(--fg);
  font:400 1rem/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,sans-serif;
  -webkit-font-smoothing:antialiased;
}}
.visually-hidden {{
  position:absolute; width:1px; height:1px; margin:-1px; padding:0;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0;
}}
.inner {{ max-width:var(--max); margin:0 auto; padding-inline:var(--pad-x); }}
.section {{ padding-block:clamp(3.5rem,7vw,5.5rem); }}
.section--alt {{ background:var(--surface-alt); }}
.eyebrow {{
  font-size:.75rem; font-weight:600; letter-spacing:.10em; text-transform:uppercase;
  color:var(--accent-700); margin:0 0 .9rem;
}}
h2 {{ font-size:var(--h2); line-height:1.18; letter-spacing:-.02em; margin:0 0 .9rem; max-width:20ch; }}
.lede {{ font-size:1.06rem; color:var(--fg-muted); max-width:64ch; margin:0 0 2.4rem; }}
a {{ color:var(--accent-700); }}

/* hero */
.hero {{ background:var(--dark-950); color:#fff; padding-block:clamp(4.5rem,10vw,7.5rem) clamp(3.5rem,7vw,5.5rem); }}
.hero h1 {{
  font-size:var(--display); line-height:1.08; letter-spacing:-.032em;
  font-weight:700; margin:0 0 1.3rem; max-width:17ch;
}}
.hero .lede {{ color:var(--w-60); font-size:1.14rem; max-width:60ch; margin-bottom:2.2rem; }}
.hero .eyebrow {{ color:var(--accent-300); }}
.cta-row {{ display:flex; flex-wrap:wrap; gap:.75rem; margin-bottom:3.2rem; }}
.cta {{
  display:inline-block; padding:.72rem 1.35rem; border-radius:var(--r-sm);
  font-weight:600; font-size:.95rem; text-decoration:none; border:1px solid transparent;
}}
.cta--primary {{ background:var(--accent); color:#0d0d0f; }}
.cta--primary:hover {{ background:var(--accent-300); }}
.cta--ghost {{ border-color:var(--w-20); color:var(--w-80); }}
.cta--ghost:hover {{ background:var(--w-10); }}
.stats {{ display:flex; flex-wrap:wrap; gap:2.6rem; border-top:1px solid var(--w-06); padding-top:1.9rem; }}
.stat__n {{ font-size:1.85rem; font-weight:700; letter-spacing:-.02em; }}
.stat__l {{ font-size:.78rem; color:var(--w-60); text-transform:uppercase; letter-spacing:.08em; }}

/* terminal */
.term {{ background:var(--dark-900); border:1px solid var(--w-10); border-radius:var(--r); overflow:hidden; }}
.term__bar {{ display:flex; gap:6px; padding:9px 12px; border-bottom:1px solid var(--w-06); }}
.term__dot {{ width:10px; height:10px; border-radius:50%; background:var(--w-20); }}
.term__body {{ padding:15px 16px; font:.83rem/1.75 var(--mono); color:#fff; overflow-x:auto; }}
.term__line {{ white-space:pre; }}
.term__prompt {{ color:var(--accent-300); user-select:none; margin-right:.55rem; }}

/* argument + quality cards */
/* Narrow measure goes on a child, never on .inner — .inner has margin:0 auto, so a
   smaller max-width there centres the whole block instead of left-aligning the text. */
.narrow {{ max-width:52ch; }}
.narrow h2 {{ max-width:26ch; }}
.narrow .lede {{ font-size:1.12rem; }}
.grid-4 {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }}
.qcard {{ background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:1.35rem; }}
.qcard h3 {{ margin:0 0 .5rem; font-size:1rem; letter-spacing:-.01em; }}
.qcard p {{ margin:0; font-size:.89rem; color:var(--fg-muted); }}
.qcard code {{ font:.85em var(--mono); background:var(--accent-10); padding:1px 4px; border-radius:3px; }}

/* tool matrix */
.matrix {{ width:100%; border-collapse:collapse; font-size:.87rem; }}
.matrix th, .matrix td {{ text-align:left; padding:.75rem .8rem; border-bottom:1px solid var(--border); vertical-align:top; }}
.matrix thead th {{
  font-size:.72rem; text-transform:uppercase; letter-spacing:.08em;
  color:var(--fg-muted); font-weight:600;
}}
.matrix tbody th {{ font-weight:600; white-space:nowrap; }}
.matrix code {{ font:.86em var(--mono); color:var(--fg-muted); }}
.matrix code.cmd {{ color:var(--fg); }}
.cap--yes, .cap--no {{ font-size:.74rem; padding:2px 8px; border-radius:999px; white-space:nowrap; }}
.cap--yes {{ background:var(--accent-10); color:var(--accent-700); }}
.cap--no {{ border:1px solid var(--border); color:var(--fg-muted); }}
.scroll-x {{ overflow-x:auto; }}

/* install tabs (CSS-only) */
.tabs__radio {{ position:absolute; opacity:0; pointer-events:none; }}
.tabs__labels {{ display:flex; flex-wrap:wrap; gap:.4rem; margin-bottom:1rem; }}
.tabs__label {{
  cursor:pointer; font-size:.85rem; font-weight:500; padding:.42rem .9rem;
  border:1px solid var(--border); border-radius:999px; background:var(--card);
}}
.tabs__panel {{ display:none; }}
.tabs__note {{ margin:.85rem 0 0; font-size:.87rem; color:var(--fg-muted); }}
#itab0:checked~.tabs__labels label[for=itab0], #itab1:checked~.tabs__labels label[for=itab1],
#itab2:checked~.tabs__labels label[for=itab2], #itab3:checked~.tabs__labels label[for=itab3]
  {{ background:var(--accent); border-color:var(--accent); color:#0d0d0f; }}
#itab0:checked~.tabs__panels .tabs__panel:nth-child(1),
#itab1:checked~.tabs__panels .tabs__panel:nth-child(2),
#itab2:checked~.tabs__panels .tabs__panel:nth-child(3),
#itab3:checked~.tabs__panels .tabs__panel:nth-child(4) {{ display:block; }}
.tabs__label:focus-within, .tabs__radio:focus-visible+.tabs__labels {{ outline:2px solid var(--accent); }}

/* packs */
.grid-3 {{ display:grid; gap:1rem; list-style:none; margin:0; padding:0;
  grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); }}
.pack {{
  background:var(--card); border:1px solid var(--border); border-radius:var(--r);
  padding:1.4rem; display:flex; flex-direction:column;
}}
.pack__head {{ display:flex; align-items:baseline; gap:.6rem; margin-bottom:.55rem; }}
.pack__name {{ margin:0; font-size:1rem; font-family:var(--mono); letter-spacing:-.01em; }}
.pack__name a {{ color:inherit; text-decoration:none; }}
.pack__name a:hover {{ color:var(--accent-700); text-decoration:underline; }}
.pack__n {{
  margin-left:auto; font-size:.68rem; text-transform:uppercase; letter-spacing:.07em;
  color:var(--accent-700); background:var(--accent-10); border-radius:999px; padding:2px 9px; white-space:nowrap;
}}
.pack__desc {{ margin:0 0 1rem; font-size:.88rem; color:var(--fg-muted); flex:1; }}
.guides-grid {{ display:grid; gap:2rem; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); margin-bottom:1.5rem; }}
.guides-group h3 {{ font-size:.75rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; color:var(--accent-700); margin:0 0 .2rem; }}
.guides-group .guides-tagline {{ font-size:.81rem; color:var(--fg-muted); margin:0 0 .8rem; font-style:italic; }}
.guides-group ul {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:.55rem; }}
.guides-group li a {{ font-weight:500; text-decoration:none; color:var(--fg); font-size:.91rem; }}
.guides-group li a:hover {{ color:var(--accent-700); text-decoration:underline; }}
.guides-group li .guides-desc {{ font-size:.79rem; color:var(--fg-muted); display:block; margin-top:.1rem; }}
.pack__install {{ margin:0 0 1rem; }}
.pack__install code {{
  display:block; font:.76rem/1.5 var(--mono); color:var(--fg-muted);
  background:var(--surface-alt); border:1px solid var(--border); border-radius:var(--r-sm);
  padding:.45rem .6rem; overflow-x:auto;
}}
.pack__cta {{
  align-self:flex-start; cursor:pointer; font:600 .84rem/1 inherit; color:var(--accent-700);
  background:none; border:0; padding:0;
}}
.pack__cta:hover {{ text-decoration:underline; }}

/* The list is open. Rows past PREVIEW_ROWS are folded by JS, never by markup — with
   scripting off every row renders, because a search box that needs JS must not gate the
   content behind it (RFC-0026). */
.more {{ margin-top:2.6rem; border-top:1px solid var(--border); padding-top:1.6rem; }}
.more__h {{ font-size:1rem; margin:0 0 .2rem; letter-spacing:-.01em; }}
.more__btn {{
  display:block; width:100%; margin-top:1.1rem; padding:.85rem 1rem; cursor:pointer;
  font:600 .88rem/1 inherit; color:var(--accent-700); background:var(--card);
  border:1px solid var(--border); border-radius:var(--r-sm);
}}
.catalogue-cta-row {{ margin-top:1.4rem; }}
.catalogue-cta {{
  display:inline-block; border-color:var(--border); color:var(--accent-700);
  background:var(--card);
}}
.catalogue-cta:hover {{ border-color:var(--accent); background:var(--accent-10); }}
.more__btn:hover {{ border-color:var(--accent); }}
.more__btn:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}

/* now / roadmap */
.roadmap-list {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:.75rem; max-width:72ch; }}
.roadmap-item {{ padding:.75rem 1rem; background:var(--card); border:1px solid var(--border); border-radius:var(--r-sm); font-size:.93rem; line-height:1.5; }}
.roadmap-item strong {{ color:var(--fg); }}

/* recently shipped */
.ships {{ list-style:none; margin:0; padding:0; display:grid; gap:1.1rem;
  grid-template-columns:repeat(auto-fit,minmax(15rem,1fr)); }}
.ship {{ background:var(--card); border:1px solid var(--border); border-radius:var(--r);
  padding:1.1rem 1.2rem; }}
.ship__head {{ display:flex; align-items:baseline; justify-content:space-between; gap:.6rem;
  margin:0 0 .6rem; }}
.ship__v {{ font:700 .95rem var(--mono); text-decoration:none; }}
.ship__v:hover {{ text-decoration:underline; }}
.ship__d {{ font-size:.75rem; color:var(--fg-muted); }}
.ship__list {{ margin:0; padding-left:1.05rem; font-size:.88rem; color:var(--fg-muted); }}
.ship__list li + li {{ margin-top:.35rem; }}

/* catalogue */
.controls {{ position:sticky; top:0; z-index:5; background:var(--surface);
  border-bottom:1px solid var(--border); padding:1rem 0; margin-bottom:1.2rem; }}
#q {{
  width:100%; padding:.7rem .9rem; font-size:1rem; color:var(--fg); background:var(--card);
  border:1px solid var(--border); border-radius:var(--r-sm);
}}
#q:focus {{ outline:2px solid var(--accent); outline-offset:1px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.7rem; align-items:center; }}
.chip {{
  cursor:pointer; font:inherit; font-size:.79rem; color:var(--fg); background:var(--card);
  border:1px solid var(--border); border-radius:999px; padding:.3rem .75rem;
}}
.chip b {{ color:var(--fg-muted); font-weight:600; margin-left:.2rem; }}
.chip[aria-pressed=true] {{ background:var(--accent); border-color:var(--accent); color:#0d0d0f; }}
.chip[aria-pressed=true] b {{ color:#0d0d0f; opacity:.7; }}
.chips__lbl {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); }}
#count {{ font-size:.8rem; color:var(--fg-muted); margin-left:auto; }}
/* one row per skill: name, one clamped line, tier. Scannable at 49 items. */
.skills {{ list-style:none; margin:0; padding:0; border-top:1px solid var(--border); }}
.skill {{ display:flex; align-items:center; gap:1rem; border-bottom:1px solid var(--border); }}
.skill:target {{ background:var(--accent-10); }}
.skill__link {{
  flex:1; min-width:0; display:flex; align-items:baseline; gap:.9rem;
  padding:.7rem .3rem; text-decoration:none; color:inherit;
}}
.skill__link:hover {{ background:var(--surface-alt); }}
.skill__link:hover .skill__name {{ color:var(--accent-700); }}
.skill__name {{ font:.9rem var(--mono); letter-spacing:-.01em; flex:0 0 15.5rem; }}
.skill__desc {{
  flex:1; min-width:0; font-size:.85rem; color:var(--fg-muted);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}}
.tier {{
  flex:0 0 auto; margin-right:.3rem; font-size:.62rem; text-transform:uppercase; letter-spacing:.07em;
  padding:2px 7px; border-radius:3px; white-space:nowrap; border:1px solid var(--border); color:var(--fg-muted);
}}
.tier--heavy {{ background:var(--accent); border-color:var(--accent); color:#0d0d0f; }}
.tier--standard {{ background:var(--accent-10); border-color:transparent; color:var(--accent-700); }}
@media (max-width:640px) {{
  .skill__link {{ flex-direction:column; gap:.2rem; }}
  .skill__name {{ flex:none; }}
  .skill__desc {{ white-space:normal; }}
}}
.empty {{ padding:3rem 0; text-align:center; color:var(--fg-muted); }}

/* nav — sits on the hero background, so it reads as one dark block with it.
   Not sticky: the catalogue's filter bar owns top:0, and two sticky layers fight. */
.skip-nav {{
  position:absolute; left:-9999px; top:0; z-index:20; background:var(--accent);
  color:#0d0d0f; padding:.6rem 1rem; font-weight:600; border-radius:0 0 var(--r-sm) 0;
}}
.skip-nav:focus {{ left:0; }}
.nav {{ background:var(--dark-950); color:#fff; position:relative; }}
.nav__inner {{
  max-width:var(--max); margin-inline:auto; padding:1.05rem var(--pad-x);
  display:flex; align-items:center; justify-content:space-between; gap:1.5rem;
}}
.nav__logo {{
  font:700 1.06rem var(--mono); letter-spacing:-.02em; color:#fff; text-decoration:none;
}}
.nav__logo:hover {{ color:var(--accent-300); }}
.nav__links {{ display:flex; align-items:center; gap:1.65rem; margin:0; padding:0; list-style:none; }}
.nav__link {{ font-size:.87rem; font-weight:500; color:var(--w-80); text-decoration:none; }}
.nav__link:hover {{ color:#fff; }}
.nav__link--ext {{ color:var(--w-60); }}
.nav__cta {{
  display:inline-block; padding:.5rem 1.05rem; border-radius:999px;
  background:var(--accent); color:#0d0d0f; font-size:.87rem; font-weight:600; text-decoration:none;
}}
.nav__cta:hover {{ background:var(--accent-300); }}
.nav__mobile {{ display:none; }}
.nav__toggle {{
  cursor:pointer; list-style:none; width:44px; height:44px;
  display:inline-flex; align-items:center; justify-content:center;
}}
.nav__toggle::-webkit-details-marker {{ display:none; }}
.nav__burger, .nav__burger::before, .nav__burger::after {{
  content:""; display:block; width:22px; height:2px; background:#fff; position:relative;
  transition:transform .18s ease, background-color .18s ease;
}}
.nav__burger::before {{ position:absolute; top:-7px; }}
.nav__burger::after {{ position:absolute; top:7px; }}
.nav__mobile[open] .nav__burger {{ background:transparent; }}
.nav__mobile[open] .nav__burger::before {{ transform:translateY(7px) rotate(45deg); }}
.nav__mobile[open] .nav__burger::after {{ transform:translateY(-7px) rotate(-45deg); }}
.nav__drawer {{
  position:absolute; top:100%; left:0; right:0; z-index:10;
  display:flex; flex-direction:column; gap:1.05rem; margin:0; list-style:none;
  background:var(--dark-950); border-top:1px solid var(--w-06);
  padding:1.35rem var(--pad-x) 1.7rem;
}}
.nav__drawer .nav__cta {{ display:block; text-align:center; margin-top:.4rem; }}
@media (max-width:760px) {{
  .nav__links {{ display:none; }}
  .nav__mobile {{ display:block; }}
}}

/* closing + footer */
.closing {{ background:var(--dark-950); color:#fff; padding-block:clamp(3.5rem,7vw,5.5rem); }}
.closing h2 {{ color:#fff; }}
.closing .lede {{ color:var(--w-60); }}
.footer {{ background:var(--dark-950); color:var(--w-60); font-size:.85rem; padding-bottom:3.2rem; }}
.footer__inner {{
  max-width:var(--max); margin-inline:auto; padding-inline:var(--pad-x);
  border-top:1px solid var(--w-06); padding-top:1.8rem;
  display:flex; flex-wrap:wrap; align-items:center; gap:1rem 1.6rem;
}}
.footer__brand {{ margin:0; font:700 .95rem var(--mono); color:#fff; letter-spacing:-.01em; }}
.footer__links {{ display:flex; flex-wrap:wrap; gap:1.35rem; }}
.footer__cols {{ display:grid; gap:1.6rem 2.6rem; flex-basis:100%;
  grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); margin-top:.6rem; }}
.footer__col h3 {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.09em;
  color:var(--w-60); margin:0 0 .6rem; font-weight:600; }}
.footer__col ul {{ list-style:none; margin:0; padding:0; display:grid; gap:.42rem; }}
.footer__col a {{ color:var(--w-80); text-decoration:none; }}
.footer__col a:hover {{ color:#fff; text-decoration:underline; }}
.footer__links a {{ color:var(--w-80); text-decoration:none; }}
.footer__links a:hover {{ color:#fff; text-decoration:underline; }}
.footer__copy {{ margin:0; flex-basis:100%; color:var(--w-60); font-size:.8rem; }}

/* ── motion ── */
@keyframes fade-up {{
  from {{ opacity:0; transform:translateY(22px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
.hero .eyebrow {{ animation:fade-up .55s cubic-bezier(.16,1,.3,1) both; }}
.hero h1       {{ animation:fade-up .65s .08s cubic-bezier(.16,1,.3,1) both; }}
.hero .lede    {{ animation:fade-up .6s .18s cubic-bezier(.16,1,.3,1) both; }}
.hero .cta-row {{ animation:fade-up .55s .28s cubic-bezier(.16,1,.3,1) both; }}
.hero .stats   {{ animation:fade-up .55s .38s cubic-bezier(.16,1,.3,1) both; }}

.hero {{ position:relative; overflow:hidden; }}
.hero::before {{
  content:''; position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse 60% 55% at 65% 40%, rgba(124,92,255,.18) 0%, transparent 70%);
  animation:orb-drift 12s ease-in-out infinite alternate;
}}
@keyframes orb-drift {{
  from {{ transform:translate(0,0) scale(1); }}
  to   {{ transform:translate(4%,6%) scale(1.08); }}
}}

.reveal {{ opacity:0; transform:translateY(18px);
  transition:opacity .6s cubic-bezier(.16,1,.3,1), transform .6s cubic-bezier(.16,1,.3,1); }}
.reveal.in {{ opacity:1; transform:none; }}
.reveal-delay-1 {{ transition-delay:.07s; }}
.reveal-delay-2 {{ transition-delay:.14s; }}
.reveal-delay-3 {{ transition-delay:.21s; }}

.pack, .ship, .roadmap-item {{
  transition:transform .2s cubic-bezier(.16,1,.3,1), box-shadow .2s cubic-bezier(.16,1,.3,1);
}}
.pack:hover, .ship:hover, .roadmap-item:hover {{
  transform:translateY(-4px);
  box-shadow:0 8px 28px rgba(0,0,0,.10);
}}
@media (prefers-color-scheme:dark) {{
  .pack:hover, .ship:hover, .roadmap-item:hover {{
    box-shadow:0 8px 28px rgba(0,0,0,.35);
  }}
}}

.cta--primary {{ transition:transform .15s ease, box-shadow .2s ease; }}
.cta--primary:hover {{
  transform:translateY(-2px);
  box-shadow:0 0 0 3px rgba(124,92,255,.25), 0 6px 20px rgba(124,92,255,.25);
}}

@keyframes shimmer {{
  from {{ background-position:200% center; }}
  to   {{ background-position:-200% center; }}
}}
.nav__logo {{
  background:linear-gradient(90deg, #fff 0%, var(--accent-300) 50%, #fff 100%);
  background-size:200% auto;
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  animation:shimmer 4s linear infinite;
}}

.nav {{ transition:background .3s, box-shadow .3s; }}
.nav.scrolled {{
  background:rgba(13,13,15,.85);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  box-shadow:0 1px 0 rgba(255,255,255,.06);
}}

/* four-step strip */
.steps-strip {{ background:var(--dark-900); border-bottom:1px solid rgba(255,255,255,.08); }}
.steps {{ display:grid; grid-template-columns:repeat(4,1fr); }}
@media (max-width:700px) {{ .steps {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width:400px) {{ .steps {{ grid-template-columns:1fr; }} }}
.step {{
  padding:1.4rem 1.6rem; border-right:1px solid rgba(255,255,255,.08);
  display:flex; flex-direction:column; gap:.35rem;
}}
.step:last-child {{ border-right:none; }}
@media (max-width:700px) {{
  .step:nth-child(2) {{ border-right:none; }}
  .step:nth-child(1), .step:nth-child(2) {{ border-bottom:1px solid rgba(255,255,255,.08); }}
}}
.step__n {{
  font:.7rem/1 var(--mono); color:var(--accent-300); letter-spacing:.12em;
  text-transform:uppercase; margin:0;
}}
.step__name {{ font:700 1rem/1.2 inherit; color:#fff; margin:0; }}
.step__desc {{ font:.83rem/1.5 inherit; color:rgba(255,255,255,.55); margin:0; }}
</style>
</head>
<body>
<a class="skip-nav" href="#main">Skip to content</a>

<nav class="nav" id="top" aria-label="Primary">
  <div class="nav__inner">
    <a class="nav__logo" href="#top">skilldrop</a>
    <ul class="nav__links">{nav_links}
      <li><a class="nav__cta" href="#install">Install <span aria-hidden="true">&rarr;</span></a></li>
    </ul>
    <details class="nav__mobile">
      <summary class="nav__toggle" aria-label="Toggle navigation menu"><span class="nav__burger" aria-hidden="true"></span></summary>
      <ul class="nav__drawer">{nav_links}
        <li><a class="nav__cta" href="#install">Install <span aria-hidden="true">&rarr;</span></a></li>
      </ul>
    </details>
  </div>
</nav>

<header class="hero">
  <div class="inner">
    <p class="eyebrow">Open catalogue · MIT · no runtime</p>
    <h1>{esc(PITCH['hero_h1'])}</h1>
    <p class="lede">{esc(PITCH['hero_lede'])}</p>
    <div class="cta-row">
      <a class="cta cta--primary" href="#catalogue">Browse {len(skills)} skills</a>
      <a class="cta cta--ghost" href="{REPO_URL}">View on GitHub</a>
    </div>
    <div class="stats">{stats_html}</div>
  </div>
</header>

<div class="steps-strip">
  <div class="inner">
    <div class="steps">
      <div class="step">
        <p class="step__n">Step 01</p>
        <p class="step__name">Discover</p>
        <p class="step__desc">Turn raw signal into a ratified requirement. Gate: you decide.</p>
      </div>
      <div class="step">
        <p class="step__n">Step 02</p>
        <p class="step__name">Design</p>
        <p class="step__desc">Commit the shape before code is written. Gate: council review.</p>
      </div>
      <div class="step">
        <p class="step__n">Step 03</p>
        <p class="step__name">Build</p>
        <p class="step__desc">Implement and gate the change. Gate: review panel.</p>
      </div>
      <div class="step">
        <p class="step__n">Step 04</p>
        <p class="step__name">Operate</p>
        <p class="step__desc">Detect, respond, and close the loop. Gate: postmortem.</p>
      </div>
    </div>
  </div>
</div>

<main id="main">
<section class="section" id="problem">
  <div class="inner"><div class="narrow">
    <p class="eyebrow">The problem</p>
    <h2>{esc(PITCH['tension_h2'])}</h2>
    <p class="lede" style="margin-bottom:0">{esc(PITCH['tension_body'])}</p>
  </div></div>
</section>

<section class="section section--alt" id="loops">
  <div class="inner">
    <p class="eyebrow">Loops</p>
    <h2>A way of operating, not just a bag of parts</h2>
    <p class="lede">A loop is an ordered sequence of stages over these skills, with a gate between them &mdash; nothing leaves a loop until its gate passes. Five cover the lifecycle and are separated by how expensive the mistake is to unwind; one wraps any generator. A loop sequences skills and never contains one, so every skill still installs and runs on its own.</p>
    <ul class="grid-3">{loop_cards}</ul>
    <p class="pack__install" style="margin-top:1.5rem"><code>skilldrop install --loop build</code> &mdash; the loop plus every stage skill it sequences.</p>
  </div>
</section>

<section class="section" id="outcomes">
  <div class="inner">
    <p class="eyebrow">Outcomes</p>
    <h2>Pick the job in front of you.</h2>
    <p class="lede">Each outcome filters the catalogue to the skills that do that job. Pick the one that matches what you need today.</p>
    <ul class="grid-3">{outcome_cards}</ul>
  </div>
</section>

<section class="section" id="quality">
  <div class="inner">
    <p class="eyebrow">What makes a skill</p>
    <h2>{esc(PITCH['quality_h2'])}</h2>
    <p class="lede">{esc(PITCH['quality_lede'])}</p>
    <div class="grid-4">{quality_html}</div>
  </div>
</section>

<section class="section section--alt" id="portability">
  <div class="inner">
    <p class="eyebrow">Portability</p>
    <h2>{esc(PITCH['tools_h2'])}</h2>
    <p class="lede">{esc(PITCH['tools_lede'])}</p>
    <div class="scroll-x"><table class="matrix">
      <thead><tr><th scope="col">Agent</th><th scope="col">Skills directory</th><th scope="col">Install</th><th scope="col">Support</th></tr></thead>
      <tbody>{tools_html}</tbody>
    </table></div>
  </div>
</section>

<section class="section" id="install">
  <div class="inner">
    <p class="eyebrow">Install</p>
    <h2>{esc(PITCH['install_h2'])}</h2>
    <div class="tabs">{tabs}
      <div class="tabs__labels">{labels}</div>
      <div class="tabs__panels">{panels}</div>
    </div>
  </div>
</section>

<section class="section section--alt" id="catalogue">
  <div class="inner">
    <p class="eyebrow">Packs</p>
    <h2>{esc(PITCH['catalogue_h2'])}</h2>
    <p class="lede">Start with a role. Each pack is a folder, every skill sits in exactly one, and every role pack brings <code>core</code> with it. Open a pack to see what to try first.</p>
    <ul class="grid-3">{pack_cards}</ul>

    <div class="more">
      <h3 class="more__h">A sample</h3>
      <ul class="skills">
{preview_cards}
      </ul>
      <p class="catalogue-cta-row">
        <a class="cta cta--ghost catalogue-cta" href="catalogue/">Browse all {len(skills)} skills &rarr;</a>
      </p>
    </div>
  </div>
</section>

<section class="section" id="reviewers">
  <div class="inner">
    <p class="eyebrow">Reviewers</p>
    <h2>{esc(PITCH['reviewers_h2'])}</h2>
    <p class="lede">{esc(PITCH['reviewers_lede'])}</p>
    <ul class="grid-3">{agent_cards}</ul>
    <p class="pack__install" style="margin-top:1.5rem"><code>skilldrop install --panel review</code> &mdash; all three, plus the orchestrator that runs them.</p>
  </div>
</section>

<section class="section" id="now">
  <div class="inner">
    <p class="eyebrow">Now</p>
    <h2>What&rsquo;s being worked on</h2>
    <p class="lede">Not a promise &mdash; a direction. Shipped work moves to the <a href="{REPO_URL}/blob/main/CHANGELOG.md">changelog</a>.</p>
    <ul class="roadmap-list">{roadmap_html}</ul>
  </div>
</section>

<section class="section section--alt" id="docs">
  <div class="inner">
    <p class="eyebrow">Docs</p>
    <h2>Everything you need</h2>
    <p class="lede">Long-form material split by Di&aacute;taxis kind &mdash; tutorial, how-to, reference, explanation. A page declares what job it does in its own frontmatter, and the lint rejects one that is not indexed. <a href="docs/">Open the full docs portal &rarr;</a></p>
    <div class="guides-grid">{guides_html}</div>
    <p class="pack__install" style="margin-top:.5rem"><a href="{REPO_URL}/blob/main/llms.txt"><code>llms.txt</code></a> &mdash; the same index, generated, for a model to read instead of crawling the tree.</p>
  </div>
</section>

<section class="section" id="shipped">
  <div class="inner">
    <p class="eyebrow">Shipped</p>
    <h2>{esc(PITCH['shipped_h2'])}</h2>
    <p class="lede">{esc(PITCH['shipped_lede'])}</p>
    <ul class="ships">{shipped_html}</ul>
    <p class="tabs__note" style="margin-top:1.4rem"><a href="{REPO_URL}/blob/main/CHANGELOG.md">Full changelog &rarr;</a></p>
  </div>
</section>

<section class="closing">
  <div class="inner">
    <h2>{esc(PITCH['closing_h2'])}</h2>
    <p class="lede">{esc(PITCH['closing_body'])}</p>
    <div class="cta-row" style="margin-bottom:0">
      <a class="cta cta--primary" href="{REPO_URL}">Get started</a>
      <a class="cta cta--ghost" href="{REPO_URL}/blob/main/CONTRIBUTING.md">Contribute a skill</a>
    </div>
  </div>
</section>
</main>

<footer class="footer"><div class="footer__inner">
  <p class="footer__brand">skilldrop</p>
  <nav class="footer__cols" aria-label="Footer">
    <div class="footer__col"><h3>Project</h3><ul>
      <li><a href="{REPO_URL}">GitHub</a></li>
      <li><a href="{NPM_URL}">npm</a></li>
      <li><a href="{REPO_URL}/blob/main/LICENSE">MIT licence</a></li>
    </ul></div>
    <div class="footer__col"><h3>Docs</h3><ul>
      <li><a href="{REPO_URL}#readme">README</a></li>
      <li><a href="{REPO_URL}/blob/main/AGENTS.md">AGENTS.md</a></li>
      <li><a href="{REPO_URL}/blob/main/MODEL-ROUTING.md">Model routing</a></li>
      <li><a href="{REPO_URL}/tree/main/docs/rfcs">RFCs</a></li>
    </ul></div>
    <div class="footer__col"><h3>Contribute</h3><ul>
      <li><a href="{REPO_URL}/blob/main/CONTRIBUTING.md">Contributing</a></li>
      <li><a href="{REPO_URL}/blob/main/SECURITY.md">Security</a></li>
      <li><a href="{REPO_URL}/issues">Issues</a></li>
    </ul></div>
    <div class="footer__col"><h3>Release</h3><ul>
      <li><a href="{REPO_URL}/blob/main/CHANGELOG.md">Changelog</a></li>
      <li><a href="{REPO_URL}/releases">Releases</a></li>
      <li><a href="{NPM_URL}/v/{esc(version)}">v{esc(version)}</a></li>
    </ul></div>
  </nav>
  <p class="footer__copy">&copy; 2026 &middot; {esc(PITCH['footer_tagline'])} &middot; v{esc(version)}</p>
</div></footer>

<script>
/* pack CTA -> catalogue page pre-filtered by pack */
document.querySelectorAll(".pack__cta[data-filter='pack']").forEach(function(b) {{
  b.addEventListener('click', function() {{
    window.location.href = 'catalogue/?pack=' + encodeURIComponent(b.dataset.value);
  }});
}});

/* scroll reveal */
(function() {{
  var io = new IntersectionObserver(function(entries) {{
    entries.forEach(function(e) {{
      if (e.isIntersecting) {{ e.target.classList.add('in'); io.unobserve(e.target); }}
    }});
  }}, {{ threshold: 0.12 }});
  document.querySelectorAll('.section h2, .section .lede, .section .eyebrow, .pack, .ship, .roadmap-item, .guides-group, .stat').forEach(function(el) {{
    el.classList.add('reveal');
    io.observe(el);
  }});
}})();

/* animated stat counters */
(function() {{
  function animateCount(el) {{
    var raw = el.querySelector('.stat__n');
    if (!raw) return;
    var target = parseInt(raw.textContent.replace(/[^0-9]/g,''), 10);
    var suffix = raw.textContent.replace(/[0-9]/g,'').trim();
    if (isNaN(target) || target === 0) return;
    var start = performance.now();
    var dur = 800;
    function tick(now) {{
      var p = Math.min((now - start) / dur, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      raw.textContent = Math.round(ease * target) + (suffix ? ' ' + suffix : '');
      if (p < 1) requestAnimationFrame(tick);
    }}
    requestAnimationFrame(tick);
  }}
  var so = new IntersectionObserver(function(entries) {{
    entries.forEach(function(e) {{
      if (e.isIntersecting) {{ animateCount(e.target); so.unobserve(e.target); }}
    }});
  }}, {{ threshold: 0.5 }});
  document.querySelectorAll('.stat').forEach(function(el) {{ so.observe(el); }});
}})();

/* scroll-activated nav backdrop */
(function() {{
  var nav = document.querySelector('.nav');
  if (!nav) return;
  window.addEventListener('scroll', function() {{
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }}, {{ passive:true }});
}})();
</script>
</body>
</html>
"""


def payload(skills, packs, outcomes, version, releases):
    return {"site": SITE_URL, "repo": REPO_URL, "version": version, "releases": releases,
            "packs": packs, "outcomes": outcomes, "loops": loops(), "skills": skills}


def ld_json(skills):
    """Schema.org SoftwareApplication — lets search engines and AI crawlers read what this is
    instead of guessing from prose. Counts come from the catalogue, never hand-typed."""
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "skilldrop",
        "description": PITCH["hero_lede"],
        "url": SITE_URL,
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "license": "https://opensource.org/licenses/MIT",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Person", "name": "Sanjay Ananthanarayan"},
        "codeRepository": REPO_URL,
        "installUrl": "https://www.npmjs.com/package/skilldrop-cli",
        "softwareHelp": REPO_URL + "#readme",
        "keywords": f"agent skills, {len(skills)} skills, Claude Code, Cursor, Codex, Copilot, Kiro, Antigravity",
    }


def loops():
    """The loops (RFC-0028). Read straight from packs/<pack>/loops/<name>/loop.json, so the
    site cannot disagree with the contract validate.py enforces. A loop has no tier: it
    sequences skills and makes no model call of its own."""
    out = []
    for n, ldir in catalog.loops().items():
        f = os.path.join(ldir, "loop.json")
        with open(f, encoding="utf-8") as fh:
            spec = json.load(fh)
        stages = spec.get("stages", [])
        out.append({
            "name": spec["name"], "kind": spec.get("kind", "loop"), "cap": spec.get("cap", 3),
            "path": catalog.rel(ldir),
            "description": spec.get("description", ""),
            "stages": [{"id": st["id"], "type": st["type"], "intent": st.get("intent", ""),
                        "skills": st.get("skills", []),
                        "gate": ({"id": st["gate"]["id"], "kind": st["gate"]["kind"],
                                  "verdicts": st["gate"].get("verdicts", [])}
                                 if st.get("gate") else None)} for st in stages],
        })
    return out


def agents():
    """The reviewer subagents (RFC-0012). Read straight from agents/<name>.md frontmatter, so the
    site can never disagree with the files — same source validate.py checks."""
    d = os.path.join(ROOT, "agents")
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f == "README.md":
            continue
        head = open(os.path.join(d, f), encoding="utf-8").read().split("---")
        fm = head[1] if len(head) >= 3 else ""
        get = lambda k: (re.search(rf"^{k}:\s*(.+)$", fm, re.M) or [None, ""])[1].strip()
        out.append({"name": f[:-3], "description": get("description"), "tools": get("tools")})
    return out


def outputs(skills, packs, outcomes, version, releases):
    return {
        "index.html": render(skills, packs, outcomes, version, releases),
        "catalogue.json": json.dumps(payload(skills, packs, outcomes, version, releases), indent=2) + "\n",
        "favicon.svg": open(os.path.join(ASSETS, "favicon.svg"), encoding="utf-8").read(),
        "llms.txt": build_llms.render(),
        "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n",
        "sitemap.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{SITE_URL}</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
            f"  <url><loc>{SITE_URL}catalogue/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n"
            f"  <url><loc>{SITE_URL}docs/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n"
            f"  <url><loc>{SITE_URL}packs/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"
            + "".join(f"  <url><loc>{SITE_URL}packs/{p['name']}/</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>\n" for p in packs)
            + "</urlset>\n"
        ),
    }


def main():
    ap = argparse.ArgumentParser(description="Generate the skilldrop catalogue site.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="output directory (default: build/)")
    ap.add_argument("--check", action="store_true", help="exit 1 if the output would differ from what is on disk")
    args = ap.parse_args()

    skills, packs, outcomes = collect()
    version, releases = changelog()
    files = outputs(skills, packs, outcomes, version, releases)

    if args.check:
        stale = []
        for name, body in files.items():
            p = os.path.join(args.out, name)
            if not os.path.exists(p):
                stale.append(f"{name}: missing")
            else:
                with open(p, encoding="utf-8") as f:
                    if f.read() != body:
                        stale.append(f"{name}: out of date")
        if stale:
            print("build_site.py --check: site is stale —", "; ".join(stale), file=sys.stderr)
            print("  run: python3 build_site.py", file=sys.stderr)
            sys.exit(1)
        for a in BINARY_ASSETS:
            src, dst = os.path.join(ASSETS, a), os.path.join(args.out, a)
            if not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read():
                print(f"build_site.py --check: {a} missing or stale in {args.out}", file=sys.stderr)
                sys.exit(1)
        marketplace_src = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
        marketplace_dst = os.path.join(args.out, "marketplace.json")
        if not os.path.exists(marketplace_dst) or open(marketplace_src, "rb").read() != open(marketplace_dst, "rb").read():
            print(f"build_site.py --check: marketplace.json missing or stale in {args.out}", file=sys.stderr)
            sys.exit(1)
        print(f"OK: site is current ({len(skills)} skills).")
        return

    os.makedirs(args.out, exist_ok=True)
    for name, body in files.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(body)
        print(f"wrote {os.path.relpath(os.path.join(args.out, name), ROOT)}")
    for a in BINARY_ASSETS:
        shutil.copyfile(os.path.join(ASSETS, a), os.path.join(args.out, a))
        print(f"copied {a}")
    marketplace_src = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    shutil.copyfile(marketplace_src, os.path.join(args.out, "marketplace.json"))
    print("copied marketplace.json")
    print(f"\n{len(skills)} skills rendered. Preview: python3 -m http.server -d {os.path.relpath(args.out, ROOT)}")


if __name__ == "__main__":
    main()

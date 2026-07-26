#!/usr/bin/env python3
"""Catalogue site generator for skilldrop. No deps, no network. Run from the repo root:

    python3 build_site.py              # writes build/index.html + build/catalogue.json
    python3 build_site.py --out <dir>  # write somewhere else
    python3 build_site.py --check      # exit 1 if build/ differs from a fresh render

Every skill fact on the page comes from skills/<name>/manifest.json, packs.json, or
model-routing.json. A description typed into this file would be a fourth copy of a
string validate.py already keeps in sync across two (RFC-0011).

The prose (hero, section headings, the tool matrix) is the page's own copy and lives in
the PITCH and TOOLS blocks below — the one place to edit wording. Every claim in it is
checkable against the repo; the tool matrix lists only paths confirmed in
docs/designs/ide-primitive-coverage.md, which is why Gemini CLI is absent.

The page is one self-contained file: CSS and JS inline, no external requests, no absolute
paths. That is what makes it work unchanged under the /skilldrop/ project-pages base path.
"""
import argparse
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(ROOT, "skills")
REPO_URL = "https://github.com/sananthanarayan/skilldrop"
SITE_URL = "https://sananthanarayan.github.io/skilldrop/"

# --- page copy -------------------------------------------------------------------
PITCH = {
    "hero_h1": "A prompt gets you a draft. A skill gets you a deliverable.",
    "hero_lede": (
        "Portable skills for the artifacts knowledge work actually ships — ADRs, design docs, "
        "PRDs, runbooks, threat models, decks, postmortems. Each one is a plain folder you copy "
        "into your agent. No runtime, no platform, no transformation on the way in."
    ),
    "tension_h2": "Generic agents are fluent about everything and opinionated about nothing.",
    "tension_body": (
        "Ask one for an ADR and it returns a plausible document with five hedged options and no "
        "decision. The gap is not model capability — it is that nothing told it what a good ADR "
        "refuses to do. Every skilldrop skill carries that judgment with it."
    ),
    "quality_h2": "Every skill ships its own quality bar.",
    "quality_lede": (
        "Four things are mandatory before a skill lands, enforced by validate.py in CI — not "
        "conventions someone might have followed."
    ),
    "tools_h2": "One folder. Every major agent.",
    "tools_lede": (
        "The SKILL.md format is identical across tools; only the directory differs, and several "
        "tools deliberately read each other's. Paths below are the ones confirmed in the July 2026 survey."
    ),
    "install_h2": "Start in one command.",
    "catalogue_h2": "The catalogue.",
    "closing_h2": "Copy a folder. Keep the artifact.",
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
]

INSTALL_TABS = [
    ("a role pack", "npx skilldrop-cli install --pack solution-architect", "16 skills a solution architect reaches for, in one command."),
    ("one skill", "npx skilldrop-cli install adr-generator --with-related", "--with-related also pulls the companions it hands off to."),
    ("by hand", "cp -R skills/adr-generator ~/.claude/skills/", "No CLI required. The folder is the whole install."),
    ("stay current", "npx skilldrop-cli outdated && npx skilldrop-cli update", "Skills improve; cp -R never tells you."),
]


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect():
    """Manifests + packs + tiers -> one list of skill records. Fails loudly."""
    packs = read_json(os.path.join(ROOT, "packs.json"))["packs"]
    tiers = read_json(os.path.join(ROOT, "model-routing.json"))["skills"]

    pack_of = {}
    for pack_name, pack in packs.items():
        for s in pack["skills"]:
            pack_of.setdefault(s, []).append(pack_name)

    names = sorted(
        d for d in os.listdir(SKILLS)
        if os.path.isfile(os.path.join(SKILLS, d, "manifest.json"))
    )
    skills, problems = [], []
    for name in names:
        m = read_json(os.path.join(SKILLS, name, "manifest.json"))
        if name not in pack_of:
            problems.append(f"{name}: in no pack (packs.json)")
        if name not in tiers:
            problems.append(f"{name}: no entry in model-routing.json")
        skills.append({
            "name": name,
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

    pack_meta = [{"name": k, "description": v["description"], "count": len(v["skills"])}
                 for k, v in packs.items()]
    return skills, pack_meta


def esc(s):
    return html.escape(str(s), quote=True)


def card(s):
    tier = s["tier"]
    packs = "".join(f'<span class="pill pill--pack">{esc(p)}</span>' for p in s["packs"])
    tags = "".join(f'<span class="pill">{esc(t)}</span>' for t in s["tags"][:6])
    related = "".join(f'<a class="rel" href="#{esc(r)}">{esc(r)}</a>' for r in s["related"])
    flags = ""
    if s["deps"]:
        flags += '<span class="pill pill--flag">deps</span>'
    for e in s["env"]:
        flags += f'<span class="pill pill--flag">env: {esc(e)}</span>'
    for h in s["hooks"]:
        flags += f'<span class="pill pill--flag">hook: {esc(h)}</span>'
    return f"""<article class="skill" id="{esc(s['name'])}"
   data-tier="{esc(tier)}" data-packs="{esc(' '.join(s['packs']))}"
   data-text="{esc((s['name'] + ' ' + s['description'] + ' ' + ' '.join(s['tags'])).lower())}">
  <div class="skill__head">
    <h3 class="skill__name"><a href="{REPO_URL}/blob/main/skills/{esc(s['name'])}/SKILL.md">{esc(s['name'])}</a></h3>
    <span class="tier tier--{esc(tier)}" title="{esc(s['rationale'])}">{esc(tier)}</span>
  </div>
  <p class="skill__desc">{esc(s['description'])}</p>
  <div class="pills">{packs}{flags}{tags}</div>
  {f'<div class="pills rels"><span class="rels__lbl">pairs with</span>{related}</div>' if related else ''}
</article>"""


def terminal(lines):
    body = "".join(
        f'<div class="term__line"><span class="term__prompt">$</span> {esc(c)}</div>'
        for c in lines
    )
    return f"""<div class="term"><div class="term__bar">
  <span class="term__dot"></span><span class="term__dot"></span><span class="term__dot"></span>
</div><div class="term__body">{body}</div></div>"""


def render(skills, packs):
    tiers = ["light", "standard", "heavy"]
    tier_counts = {t: sum(1 for s in skills if s["tier"] == t) for t in tiers}

    stats = [(str(len(skills)), "skills"), (str(len(packs)), "role packs"),
             (str(len(TOOLS)), "agent tools"), ("0", "runtime deps")]
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

    pack_cards = "".join(
        f"""<article class="pack">
      <h3 class="pack__name">{esc(p['name'])} <span class="pack__n">{p['count']}</span></h3>
      <p class="pack__desc">{esc(p['description'])}</p>
      <button class="pack__cta" data-filter="pack" data-value="{esc(p['name'])}">Show these skills &rarr;</button>
    </article>""" for p in packs)

    pack_chips = "".join(
        f'<button class="chip" data-filter="pack" data-value="{esc(p["name"])}">{esc(p["name"])} <b>{p["count"]}</b></button>'
        for p in packs)
    tier_chips = "".join(
        f'<button class="chip chip--{t}" data-filter="tier" data-value="{t}">{t} <b>{tier_counts[t]}</b></button>'
        for t in tiers)
    cards = "\n".join(card(s) for s in skills)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skilldrop — portable skills for agentic IDEs</title>
<meta name="description" content="{esc(PITCH['hero_lede'])}">
<meta property="og:title" content="skilldrop">
<meta property="og:description" content="{esc(PITCH['hero_h1'])}">
<meta property="og:url" content="{SITE_URL}">
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
.grid-3 {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }}
.pack {{
  background:var(--card); border:1px solid var(--border); border-radius:var(--r);
  padding:1.35rem; display:flex; flex-direction:column;
}}
.pack__name {{ margin:0 0 .5rem; font-size:1rem; font-family:var(--mono); letter-spacing:-.01em; }}
.pack__n {{
  font-family:inherit; font-size:.7rem; color:var(--accent-700);
  background:var(--accent-10); border-radius:999px; padding:2px 8px; margin-left:.3rem;
}}
.pack__desc {{ margin:0 0 1.1rem; font-size:.88rem; color:var(--fg-muted); flex:1; }}
.pack__cta {{
  align-self:flex-start; cursor:pointer; font:600 .84rem/1 inherit; color:var(--accent-700);
  background:none; border:0; padding:0;
}}
.pack__cta:hover {{ text-decoration:underline; }}

/* catalogue */
.controls {{ position:sticky; top:0; z-index:5; background:var(--surface-alt);
  border-bottom:1px solid var(--border); padding:1rem 0; margin-bottom:1.6rem; }}
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
.skills {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); }}
.skill {{ background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:1.25rem; }}
.skill:target {{ outline:2px solid var(--accent); }}
.skill__head {{ display:flex; gap:.6rem; align-items:baseline; margin-bottom:.5rem; }}
.skill__name {{ margin:0; font-size:.97rem; font-family:var(--mono); letter-spacing:-.01em; }}
.skill__name a {{ color:var(--fg); text-decoration:none; }}
.skill__name a:hover {{ color:var(--accent-700); text-decoration:underline; }}
.skill__desc {{ margin:0 0 .8rem; font-size:.87rem; color:var(--fg-muted); }}
.tier {{
  margin-left:auto; font-size:.65rem; text-transform:uppercase; letter-spacing:.07em;
  padding:2px 7px; border-radius:3px; white-space:nowrap; border:1px solid var(--border); color:var(--fg-muted);
}}
.tier--heavy {{ background:var(--accent); border-color:var(--accent); color:#0d0d0f; }}
.tier--standard {{ background:var(--accent-10); border-color:transparent; color:var(--accent-700); }}
.pills {{ display:flex; flex-wrap:wrap; gap:.3rem; }}
.pills.rels {{ margin-top:.55rem; align-items:center; }}
.pill {{ font-size:.69rem; padding:2px 7px; border-radius:3px; border:1px solid var(--border); color:var(--fg-muted); }}
.pill--pack {{ border-color:var(--accent); color:var(--accent-700); }}
.rels__lbl {{ font-size:.68rem; text-transform:uppercase; letter-spacing:.07em; color:var(--fg-muted); margin-right:.2rem; }}
.rel {{ font:.71rem var(--mono); color:var(--accent-700); text-decoration:none; }}
.rel:hover {{ text-decoration:underline; }}
.empty {{ padding:3rem 0; text-align:center; color:var(--fg-muted); }}

/* closing + footer */
.closing {{ background:var(--dark-950); color:#fff; padding-block:clamp(3.5rem,7vw,5.5rem); }}
.closing h2 {{ color:#fff; }}
.closing .lede {{ color:var(--w-60); }}
footer {{ background:var(--dark-950); color:var(--w-60); font-size:.84rem; padding-bottom:3rem; }}
footer a {{ color:var(--w-80); }}
footer .inner {{ border-top:1px solid var(--w-06); padding-top:1.6rem; display:flex; flex-wrap:wrap; gap:1rem 1.5rem; }}
</style>
</head>
<body>

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

<main>
<section class="section">
  <div class="inner"><div class="narrow">
    <p class="eyebrow">The problem</p>
    <h2>{esc(PITCH['tension_h2'])}</h2>
    <p class="lede" style="margin-bottom:0">{esc(PITCH['tension_body'])}</p>
  </div></div>
</section>

<section class="section section--alt">
  <div class="inner">
    <p class="eyebrow">What makes a skill</p>
    <h2>{esc(PITCH['quality_h2'])}</h2>
    <p class="lede">{esc(PITCH['quality_lede'])}</p>
    <div class="grid-4">{quality_html}</div>
  </div>
</section>

<section class="section">
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

<section class="section section--alt">
  <div class="inner">
    <p class="eyebrow">Install</p>
    <h2>{esc(PITCH['install_h2'])}</h2>
    <div class="tabs">{tabs}
      <div class="tabs__labels">{labels}</div>
      <div class="tabs__panels">{panels}</div>
    </div>
  </div>
</section>

<section class="section" id="packs">
  <div class="inner">
    <p class="eyebrow">Packs</p>
    <h2>{esc(PITCH['catalogue_h2'])}</h2>
    <p class="lede">Role-based bundles. A pack is a named list — skills never move out of their flat folders, so a pack install is the same copy as any other.</p>
    <div class="grid-3">{pack_cards}</div>
  </div>
</section>

<section class="section section--alt" id="catalogue">
  <div class="inner">
    <p class="eyebrow">All {len(skills)} skills</p>
    <h2 class="visually-hidden">Catalogue</h2>
    <div class="controls">
      <label class="visually-hidden" for="q">Search skills</label>
      <input id="q" type="search" placeholder="Search by name, description, or tag…" autocomplete="off">
      <div class="chips"><span class="chips__lbl">pack</span>{pack_chips}</div>
      <div class="chips"><span class="chips__lbl">tier</span>{tier_chips}
        <button class="chip" id="clear">clear</button><span id="count"></span></div>
    </div>
    <div class="skills" id="grid">
{cards}
    </div>
    <p class="empty" id="empty" hidden>No skill matches those filters.</p>
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

<footer><div class="inner">
  <span>Generated from {len(skills)} manifests by <a href="{REPO_URL}/blob/main/build_site.py">build_site.py</a> — never hand-edited.</span>
  <a href="{REPO_URL}">Repository</a>
  <a href="{REPO_URL}/tree/main/docs/rfcs">RFCs</a>
  <a href="catalogue.json">catalogue.json</a>
  <a href="{REPO_URL}/blob/main/LICENSE">MIT</a>
</div></footer>

<script>
(function () {{
  var q = document.getElementById('q'), grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.children);
  var count = document.getElementById('count'), empty = document.getElementById('empty');
  var active = {{ pack: null, tier: null }};

  function sync() {{
    ['pack', 'tier'].forEach(function (kind) {{
      document.querySelectorAll('.chip[data-filter="' + kind + '"]').forEach(function (o) {{
        o.setAttribute('aria-pressed', String(o.dataset.value === active[kind]));
      }});
    }});
  }}

  function apply() {{
    var text = q.value.trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {{
      var ok = (!text || c.dataset.text.indexOf(text) !== -1)
        && (!active.pack || c.dataset.packs.split(' ').indexOf(active.pack) !== -1)
        && (!active.tier || c.dataset.tier === active.tier);
      c.hidden = !ok;
      if (ok) shown++;
    }});
    count.textContent = shown + ' of ' + cards.length;
    empty.hidden = shown !== 0;
  }}

  document.querySelectorAll('[data-filter]').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var kind = b.dataset.filter, val = b.dataset.value;
      active[kind] = active[kind] === val ? null : val;
      sync(); apply();
      if (b.classList.contains('pack__cta')) {{
        document.getElementById('catalogue').scrollIntoView({{ behavior: 'smooth' }});
      }}
    }});
  }});

  document.getElementById('clear').addEventListener('click', function () {{
    active = {{ pack: null, tier: null }}; q.value = ''; sync(); apply();
  }});

  q.addEventListener('input', apply);
  sync(); apply();
}})();
</script>
</body>
</html>
"""


def payload(skills, packs):
    return {"site": SITE_URL, "repo": REPO_URL, "packs": packs, "skills": skills}


def outputs(skills, packs):
    return {
        "index.html": render(skills, packs),
        "catalogue.json": json.dumps(payload(skills, packs), indent=2) + "\n",
    }


def main():
    ap = argparse.ArgumentParser(description="Generate the skilldrop catalogue site.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="output directory (default: build/)")
    ap.add_argument("--check", action="store_true", help="exit 1 if the output would differ from what is on disk")
    args = ap.parse_args()

    skills, packs = collect()
    files = outputs(skills, packs)

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
        print(f"OK: site is current ({len(skills)} skills).")
        return

    os.makedirs(args.out, exist_ok=True)
    for name, body in files.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(body)
        print(f"wrote {os.path.relpath(os.path.join(args.out, name), ROOT)}")
    print(f"\n{len(skills)} skills rendered. Preview: python3 -m http.server -d {os.path.relpath(args.out, ROOT)}")


if __name__ == "__main__":
    main()

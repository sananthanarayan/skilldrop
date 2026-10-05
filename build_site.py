#!/usr/bin/env python3
"""Catalogue site generator for skilldrop. No deps, no network. Run from the repo root:

    python3 build_site.py              # writes build/index.html + build/catalogue.json
    python3 build_site.py --out <dir>  # write somewhere else
    python3 build_site.py --check      # exit 1 if build/ differs from a fresh render

Every skill fact on the page comes from packs/<pack>/skills/<name>/manifest.json, catalogue.json, or
model-routing.json. A description typed into this file would be a fourth copy of a
string validate.py already keeps in sync across two (RFC-0011).

The prose (hero, section headings, the promises, the own and team lists) is the page's own
copy and lives in the PITCH, PROMISES, OWN and TEAM blocks below — the one place to edit
wording. Every claim in it is checkable against the repo. The home page keeps to six sections
(RFC-0035 follow-up); anything longer has its own page in the nav.

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
from build_docs import render_md, collect_guides  # the proof section and the sitemap
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
# How many releases the "Recently shipped" strip carries. Three is enough to show a pulse
# without turning the landing page into a changelog.
SHIPPED_ENTRIES = 3
SITE_URL = "https://sananthanarayan.github.io/skilldrop/"

def _pack_total(name):
    """Skills one `install --pack <name>` delivers: the pack's own plus what it requires."""
    p = catalog.packs()
    return len(set(p[name]["skills"]).union(*(p[r]["skills"] for r in p[name].get("requires", []))))


# --- page copy -------------------------------------------------------------------
PITCH = {
    "hero_h1": "Your agent can draft anything. What ships is still your call.",
    # Search results cut a description off around 160 characters; the hero lede runs twice that.
    "meta_description": "Portable AI-agent skills for ADRs, PRDs, runbooks, decks and reviews, measured against the agent without them. Copy one folder into Claude Code, Cursor or Kiro.",
    # No counts in the pitch: a number tells a newcomer nothing about what they get back, and it
    # goes stale. Counts stay where they help a choice (pack sizes, catalogue filters).
    "hero_lede": (
        "Skills that produce the files your work actually ships — ADRs, PRDs, runbooks, decks, "
        "reviews — each with a quality bar it is held to, and loops whose gates can say no: a "
        "script, a review panel, or you, chosen by how expensive the mistake is to undo. Every skill "
        "is a plain folder you copy into your agent, and every skill is measured against the agent "
        "without it."
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
    "footer_tagline": "Portable skills, measured against the agent without them.",
    "closing_body": (
        "Nothing here needs an account, a runtime, or a migration. Install one skill, run it once, "
        "and keep it only if the output was worth keeping."
    ),
}

PROMISES = [
    ("Copy, never transform", "What runs in your agent is what was reviewed here."),
    ("A gate that can say no", "A script, a review panel or you decides when work moves on."),
    ("Your edits survive updates", "New versions land beside the files you changed."),
]

# "Yours after it lands" and "Run it for your team": what agent-ready-repo's home page sells and
# ours had the features for but never said.
OWN = [
    ("A folder you can read", "Installing copies plain <code>SKILL.md</code> folders into the directory your agent already reads. No runtime, no service, nothing to keep running.", "docs/how-to/install-per-ide.html"),
    ("Edits that survive updates", "Change a skill to fit your codebase. <code>skilldrop update</code> replaces only files you didn't touch and leaves the new version beside yours as <code>.upstream</code>.", "docs/how-to/upgrade-skills.html"),
    ("Only what you need", "One skill, one pack, one loop, or a whole profile, into Claude Code, Cursor, Kiro, Codex, Copilot or Antigravity.", "docs/how-to/install.html"),
]
TEAM = [
    ("One setup for everyone", "A profile installs a team's packs, loops and reviewer agents in one command.", "skilldrop install --profile starter", "docs/how-to/profiles.html"),
    ("Every machine, no per-session step", "Bootstrap writes the marketplace into Claude Code settings, so each session already sees the catalogue.", "skilldrop bootstrap", "docs/how-to/enterprise-distribution.html"),
    ("Your own catalogue", "Publish your organisation's skills from any repo in the same shape, and install them through the same CLI.", "skilldrop install --pack <name> --from <your-repo>", "docs/how-to/publish-a-catalogue.html"),
]

# The home page's proof: one real worked example, input then output, from a skill's examples/.
PROOF_SKILL = "launch-readiness"


# Gemini CLI is absent on purpose, not by omission: Google retired it for free, AI Pro, Ultra
# and individual Code Assist users on 2026-06-18, leaving only Standard/Enterprise licences.
# Antigravity CLI is its successor and is listed above. Listing a tool that no longer serves
# this audience would be worse than the gap.

# One nav on every page (home, catalogue, packs, skills, docs, changelog), so a reader who
# lands deep never loses the way back. Hrefs are relative to the site root; site_nav()
# prefixes them for the page's depth. The home page's in-page sections are reached by scrolling.
NAV = [
    ("Packs", "packs/", False),
    ("Skills", "catalogue/", False),
    ("Loops", "loops/", False),
    ("Docs", "docs/", False),
    ("What's new", "changelog/", False),
    ("GitHub", REPO_URL, True),
]


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
                  "requires": v.get("requires", []),
                  "starter": (v.get("first-value") or {}).get("starter-task", "")}
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
    outcome_meta = [{"name": k, "description": v["description"], "count": len(v["skills"]), "for": v.get("for", "")}
                    for k, v in doc.get("outcomes", {}).items()]

    return skills, pack_meta, outcome_meta


RELEASE_RE = re.compile(r"^##\s+(\d+\.\d+\.\d+)\s+[—-]\s+(\d{4}-\d{2}-\d{2})\s*$")


def changelog(limit=SHIPPED_ENTRIES):
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
    return version, releases[:limit] if limit else releases




def esc(s):
    return html.escape(str(s), quote=True)


def inline_md(s):
    """Escape first, then re-admit the only two inline marks a changelog bullet uses.
    Anything richer belongs in CHANGELOG.md, not on the landing page."""
    out = esc(s)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)


# Self-contained: literal values, not the page's CSS variables, because the catalogue, pack
# and docs pages each carry their own stylesheet and the nav must look the same on all of them.
NAV_CSS = """/* nav — light, on every page; a hairline separates it from the content.
   Not sticky: the catalogue's filter bar owns top:0, and two sticky layers fight. */
.skip-nav {
  position:absolute; left:-9999px; top:0; z-index:20; background:#7c5cff;
  color:#0d0d0f; padding:.6rem 1rem; font-weight:600; border-radius:0 0 5px 0;
}
.skip-nav:focus { left:0; }
.nav { background:#fff; color:#17171a; position:relative; border-bottom:1px solid #e4e4e0; }
.nav__inner {
  max-width:1140px; margin-inline:auto; padding:1.05rem clamp(1.25rem,5vw,2.5rem);
  display:flex; align-items:center; justify-content:space-between; gap:1.5rem;
}
.nav__logo {
  font:700 1.06rem ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace; letter-spacing:-.02em; color:#17171a; text-decoration:none;
}
.nav__logo:hover { color:#4c31d6; }
.nav__links { display:flex; align-items:center; gap:1.15rem; margin:0; padding:0; list-style:none; }
.nav__link[aria-current=page] { color:#17171a; box-shadow:0 2px 0 #7c5cff; }
.nav__link { font-size:.87rem; font-weight:500; color:#3a3a3f; text-decoration:none; white-space:nowrap; }
.nav__link:hover { color:#4c31d6; }
.nav__link--ext { color:#6a6a66; }
.nav__cta {
  display:inline-block; padding:.5rem 1.05rem; border-radius:999px;
  background:#7c5cff; color:#0d0d0f; font-size:.87rem; font-weight:600; text-decoration:none;
  white-space:nowrap;
}
.nav__cta:hover { background:#a48cff; }
.nav__mobile { display:none; }
.nav__toggle {
  cursor:pointer; list-style:none; width:44px; height:44px;
  display:inline-flex; align-items:center; justify-content:center;
}
.nav__toggle::-webkit-details-marker { display:none; }
.nav__burger, .nav__burger::before, .nav__burger::after {
  content:""; display:block; width:22px; height:2px; background:#17171a; position:relative;
  transition:transform .18s ease, background-color .18s ease;
}
.nav__burger::before { position:absolute; top:-7px; }
.nav__burger::after { position:absolute; top:7px; }
.nav__mobile[open] .nav__burger { background:transparent; }
.nav__mobile[open] .nav__burger::before { transform:translateY(7px) rotate(45deg); }
.nav__mobile[open] .nav__burger::after { transform:translateY(-7px) rotate(-45deg); }
.nav__drawer {
  position:absolute; top:100%; left:0; right:0; z-index:10;
  display:flex; flex-direction:column; gap:1.05rem; margin:0; list-style:none;
  background:#fff; border-top:1px solid #e4e4e0; border-bottom:1px solid #e4e4e0;
  padding:1.35rem clamp(1.25rem,5vw,2.5rem) 1.7rem;
}
.nav__drawer .nav__cta { display:block; text-align:center; margin-top:.4rem; }
@media (max-width:760px) {
  .nav__links { display:none; }
  .nav__mobile { display:block; }
}

/* closing + footer */
.closing { background:#f3f3f1; color:#17171a; padding-block:clamp(3.5rem,7vw,5.5rem); }
.closing h2 { color:#17171a; }
.closing .lede { color:#6a6a66; }
.footer { background:#f3f3f1; color:#6a6a66; border-top:1px solid #e4e4e0; padding-top:.4rem; font-size:.85rem; padding-bottom:3.2rem; }
.footer__inner {
  max-width:1140px; margin-inline:auto; padding-inline:clamp(1.25rem,5vw,2.5rem);
  padding-top:1.8rem;
  display:flex; flex-wrap:wrap; align-items:center; gap:1rem 1.6rem;
}
.footer__brand { margin:0; font:700 .95rem ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace; color:#17171a; letter-spacing:-.01em; }
.footer__links { display:flex; flex-wrap:wrap; gap:1.35rem; }
.footer__cols { display:grid; gap:1.6rem 2.6rem; flex-basis:100%;
  grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); margin-top:.6rem; }
.footer__col h3 { font-size:.72rem; text-transform:uppercase; letter-spacing:.09em;
  color:#6a6a66; margin:0 0 .6rem; font-weight:600; }
.footer__col ul { list-style:none; margin:0; padding:0; display:grid; gap:.42rem; }
.footer__col a { color:#3a3a3f; text-decoration:none; }
.footer__col a:hover { color:#4c31d6; text-decoration:underline; }
.footer__links a { color:#3a3a3f; text-decoration:none; }
.footer__links a:hover { color:#4c31d6; text-decoration:underline; }
.footer__copy { margin:0; flex-basis:100%; color:#6a6a66; font-size:.8rem; }

/* ── motion ── */
@keyframes fade-up {
  from { opacity:0; transform:translateY(22px); }
  to   { opacity:1; transform:translateY(0); }
}
.hero .eyebrow { animation:fade-up .55s cubic-bezier(.16,1,.3,1) both; }
.hero h1       { animation:fade-up .65s .08s cubic-bezier(.16,1,.3,1) both; }
.hero .lede    { animation:fade-up .6s .18s cubic-bezier(.16,1,.3,1) both; }
.hero .cta-row { animation:fade-up .55s .28s cubic-bezier(.16,1,.3,1) both; }
.hero .stats   { animation:fade-up .55s .38s cubic-bezier(.16,1,.3,1) both; }

.hero { position:relative; overflow:hidden; }
.hero::before {
  content:''; position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(ellipse 60% 55% at 65% 40%, rgba(124,92,255,.18) 0%, transparent 70%);
  animation:orb-drift 12s ease-in-out infinite alternate;
}
@keyframes orb-drift {
  from { transform:translate(0,0) scale(1); }
  to   { transform:translate(4%,6%) scale(1.08); }
}

.reveal { opacity:0; transform:translateY(18px);
  transition:opacity .6s cubic-bezier(.16,1,.3,1), transform .6s cubic-bezier(.16,1,.3,1); }
.reveal.in { opacity:1; transform:none; }
.reveal-delay-1 { transition-delay:.07s; }
.reveal-delay-2 { transition-delay:.14s; }
.reveal-delay-3 { transition-delay:.21s; }
/* Reduced motion: nothing animates and nothing starts hidden. Lives in the shared nav CSS, so
   it covers every page's animations (hero fade-up, orb drift, logo shimmer, scroll reveal). */
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior:auto; }
  *, *::before, *::after { animation:none !important; transition:none !important; }
  .reveal { opacity:1; transform:none; }
}

.pack, .ship, .roadmap-item {
  transition:transform .2s cubic-bezier(.16,1,.3,1), box-shadow .2s cubic-bezier(.16,1,.3,1);
}
.pack:hover, .ship:hover, .roadmap-item:hover {
  transform:translateY(-4px);
  box-shadow:0 8px 28px rgba(0,0,0,.10);
}

.cta--primary { transition:transform .15s ease, box-shadow .2s ease; }
.cta--primary:hover {
  transform:translateY(-2px);
  box-shadow:0 0 0 3px rgba(124,92,255,.25), 0 6px 20px rgba(124,92,255,.25);
}

"""


SEARCH_CSS = """
/* site search (RFC-0035 follow-up) — a nav button that opens a <dialog> over one JSON index */
.nav__search {
  display:inline-flex; align-items:center; gap:.45rem; cursor:pointer; text-decoration:none;
  font:500 .84rem/1 inherit; color:#3a3a3f; background:#f3f3f1;
  border:1px solid #e4e4e0; border-radius:999px; padding:.42rem .75rem; white-space:nowrap;
}
.nav__search:hover { color:#17171a; border-color:#c9c9c4; }
.nav__search svg { width:14px; height:14px; }
.nav__search kbd { font:600 .68rem ui-monospace,Menlo,monospace; border:1px solid #c9c9c4; border-radius:4px; padding:0 .3rem; }
.sx {
  width:min(680px,calc(100vw - 2rem)); max-height:min(76vh,720px); margin:9vh auto auto; padding:0;
  border:1px solid #e4e4e0; border-radius:14px; background:#fff; color:#17171a;
  box-shadow:0 24px 70px rgba(0,0,0,.35); overflow:hidden;
  font:400 1rem/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,sans-serif;
}
.sx[open] { display:flex; flex-direction:column; }
.sx::backdrop { background:rgba(10,10,12,.55); backdrop-filter:blur(2px); }
.sx__bar { display:flex; align-items:center; gap:.5rem; padding:.7rem .9rem; border-bottom:1px solid #e4e4e0; margin:0; }
.sx__bar input { flex:1; border:0; outline:0; font:inherit; font-size:1.05rem; background:transparent; color:inherit; padding:.35rem .2rem; }
.sx__close { cursor:pointer; font:600 .72rem ui-monospace,Menlo,monospace; color:#6a6a66; background:none; border:1px solid #e4e4e0; border-radius:5px; padding:.25rem .45rem; }
.sx__status { margin:0; padding:.55rem 1rem 0; font-size:.78rem; color:#6a6a66; }
.sx__results { list-style:none; margin:0; padding:.4rem .5rem .7rem; overflow-y:auto; }
.sx__hit { display:grid; grid-template-columns:4.6rem 1fr; gap:.1rem .7rem; padding:.55rem .6rem; border-radius:8px; text-decoration:none; color:inherit; }
.sx__hit:hover, .sx__hit.is-sel { background:rgba(124,92,255,.10); }
.sx__kind { grid-row:span 2; align-self:start; font:600 .64rem ui-monospace,Menlo,monospace; text-transform:uppercase; letter-spacing:.06em; color:#4c31d6; padding-top:.2rem; }
.sx__title { font-weight:600; font-size:.95rem; }
.sx__snip { font-size:.84rem; color:#6a6a66; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.sx mark { background:rgba(124,92,255,.22); color:inherit; border-radius:2px; padding:0 1px; }
@media (max-width:760px) { .nav__search span, .nav__search kbd { display:none; } }
"""
NAV_CSS += SEARCH_CSS

SEARCH_JS = r"""<script>
/* Site search: one index (search.json, generated by build_pages.py), opened from the nav,
   with "/" or Cmd/Ctrl+K. Results are built with DOM nodes, never innerHTML. */
(function () {
  var dlg = document.getElementById('site-search');
  if (!dlg || typeof dlg.showModal !== 'function') return;  // no <dialog>: the nav link still goes to the docs index
  var root = dlg.getAttribute('data-root') || '';
  var q = document.getElementById('sx-q'), list = document.getElementById('sx-results'), status = document.getElementById('sx-status');
  var data = null, loading = null, sel = -1;
  function load() {
    if (!loading) loading = fetch(root + 'search.json').then(function (r) { return r.json(); })
      .then(function (d) { data = d; run(); })
      .catch(function () { status.textContent = 'Search could not load. Try the docs index instead.'; });
    return loading;
  }
  function open(e) { if (e) e.preventDefault(); if (!dlg.open) dlg.showModal(); q.focus(); q.select(); load(); run(); }
  document.querySelectorAll('.js-search').forEach(function (b) { b.addEventListener('click', open); });
  document.addEventListener('keydown', function (e) {
    var t = e.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
    if ((e.key === '/' && !typing) || ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K'))) open(e);
  });
  function words(s) { return s.toLowerCase().split(/\s+/).filter(Boolean); }
  function score(it, ws) {
    var s = 0, T = it.title.toLowerCase(), S = (it.summary || '').toLowerCase(), B = (it.text || '').toLowerCase();
    for (var i = 0; i < ws.length; i++) {
      var w = ws[i], hit = false;
      if (T.indexOf(w) > -1) { s += T === w ? 40 : (T.indexOf(w) === 0 ? 20 : 12); hit = true; }
      if (S.indexOf(w) > -1) { s += 5; hit = true; }
      if (B.indexOf(w) > -1) { s += 1; hit = true; }
      if (!hit) return 0;  // every word has to appear somewhere
    }
    return s;
  }
  function snippet(it, ws) {
    var S = it.summary || '';
    for (var i = 0; i < ws.length; i++) if (S.toLowerCase().indexOf(ws[i]) > -1) return S;
    var B = it.text || '', lo = B.toLowerCase();
    for (var j = 0; j < ws.length; j++) {
      var at = lo.indexOf(ws[j]);
      if (at > -1) { var a = Math.max(0, at - 60); return (a ? '…' : '') + B.slice(a, at + 120) + '…'; }
    }
    return S;
  }
  function mark(el, text, ws) {
    var lower = text.toLowerCase(), i = 0;
    while (i < text.length) {
      var best = -1, bw = '';
      ws.forEach(function (w) { var j = lower.indexOf(w, i); if (j > -1 && (best < 0 || j < best)) { best = j; bw = w; } });
      if (best < 0) { el.appendChild(document.createTextNode(text.slice(i))); break; }
      if (best > i) el.appendChild(document.createTextNode(text.slice(i, best)));
      var m = document.createElement('mark'); m.textContent = text.slice(best, best + bw.length); el.appendChild(m);
      i = best + bw.length;
    }
  }
  function run() {
    var ws = words(q.value); list.textContent = ''; sel = -1; q.removeAttribute('aria-activedescendant');
    if (!ws.length) { status.textContent = 'Search skills, packs, loops and guides.'; return; }
    if (!data) { status.textContent = 'Loading…'; return; }
    var hits = data.map(function (it) { return [score(it, ws), it]; })
      .filter(function (x) { return x[0] > 0; })
      .sort(function (a, b) { return b[0] - a[0]; }).slice(0, 20);
    status.textContent = hits.length ? hits.length + (hits.length === 20 ? '+' : '') + ' result' + (hits.length === 1 ? '' : 's')
                                     : 'Nothing matches "' + q.value + '".';
    hits.forEach(function (h, n) {
      var it = h[1], li = document.createElement('li'), a = document.createElement('a');
      a.href = root + it.url; a.className = 'sx__hit'; li.id = 'sx-' + n; li.setAttribute('role', 'option');
      var k = document.createElement('span'); k.className = 'sx__kind'; k.textContent = it.type;
      var t = document.createElement('span'); t.className = 'sx__title'; mark(t, it.title, ws);
      var p = document.createElement('span'); p.className = 'sx__snip'; mark(p, snippet(it, ws), ws);
      a.appendChild(k); a.appendChild(t); a.appendChild(p); li.appendChild(a); list.appendChild(li);
    });
  }
  q.addEventListener('input', run);
  q.addEventListener('keydown', function (e) {
    var items = list.querySelectorAll('.sx__hit');
    if (!items.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items.forEach(function (x, i) { x.classList.toggle('is-sel', i === sel); });
      items[sel].scrollIntoView({ block: 'nearest' });
      q.setAttribute('aria-activedescendant', 'sx-' + sel);
    } else if (e.key === 'Enter') { e.preventDefault(); items[sel >= 0 ? sel : 0].click(); }
  });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });  // click on the backdrop
})();
</script>"""


def head_meta(title, desc, url, image_alt="skilldrop — a prompt gets you a draft, a skill gets you a deliverable"):
    """Description, canonical, Open Graph and Twitter tags for one page. Every page carries the
    full set, so a pack or skill page shared in a chat unfurls like the home page does."""
    desc = desc if len(desc) <= 200 else desc[:197].rsplit(" ", 1)[0] + "…"
    return f"""<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<link rel="alternate" type="application/atom+xml" title="skilldrop releases" href="{SITE_URL}changelog/feed.xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="skilldrop">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{SITE_URL}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(image_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE_URL}og.png">"""


def ld(obj):
    """A JSON-LD block. "</" is escaped so a description can never close the script tag."""
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>")


def breadcrumbs_ld(pairs):
    """BreadcrumbList for [(name, absolute url), ...], matching the visible breadcrumb."""
    return ld({"@context": "https://schema.org", "@type": "BreadcrumbList",
               "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": name, "item": url}
                                   for n, (name, url) in enumerate(pairs)]})


def site_nav(root="", current=None):
    """The shared top nav. `root` is the relative path back to the site root ("", "../",
    "../../"); `current` is the NAV href of the page being rendered, marked aria-current."""
    def href(h):
        return h if h.startswith("http") else (root + h if not h.startswith("#") else f"{root or './'}{h}")
    links = "".join(
        f'<li><a class="nav__link{" nav__link--ext" if ext else ""}" href="{esc(href(h))}"'
        f'{" aria-current=\"page\"" if h == current else ""}>'
        f'{esc(label)}{" <span aria-hidden=\"true\">&#8599;</span>" if ext else ""}</a></li>'
        for label, h, ext in NAV)
    cta = f'<li><a class="nav__cta" href="{esc(href("#install"))}">Install <span aria-hidden="true">&rarr;</span></a></li>'
    # Without JavaScript the search button is a plain link to the docs index, which has its own filter.
    search = (f'<li><a class="nav__search js-search" href="{esc(root)}docs/" aria-label="Search the site (press /)">'
              '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
              '<circle cx="7" cy="7" r="5"/><path d="m11 11 3.5 3.5"/></svg><span>Search</span><kbd>/</kbd></a></li>')
    return f"""<a class="skip-nav" href="#main">Skip to content</a>
<nav class="nav" id="top" aria-label="Primary">
  <div class="nav__inner">
    <a class="nav__logo" href="{esc(root or './')}">skilldrop</a>
    <ul class="nav__links">{search}{links}
      {cta}
    </ul>
    <details class="nav__mobile">
      <summary class="nav__toggle" aria-label="Toggle navigation menu"><span class="nav__burger" aria-hidden="true"></span></summary>
      <ul class="nav__drawer">{search}{links}
        {cta}
      </ul>
    </details>
  </div>
</nav>
<dialog class="sx" id="site-search" aria-label="Search skilldrop" data-root="{esc(root)}">
  <form method="dialog" class="sx__bar">
    <input id="sx-q" type="search" placeholder="Search skills, packs, loops and guides…" autocomplete="off" aria-label="Search" aria-controls="sx-results">
    <button class="sx__close" value="close" aria-label="Close search">Esc</button>
  </form>
  <p class="sx__status" id="sx-status" role="status" aria-live="polite"></p>
  <ul class="sx__results" id="sx-results" role="listbox" aria-label="Results"></ul>
</dialog>
{SEARCH_JS}"""


def guide_href(path_):
    """A guides/<kind>/<slug>.md path as its page in the docs portal; anything else on GitHub."""
    m = re.match(r"^guides/([^/]+)/([^/]+)\.md$", path_)
    return f"docs/{m.group(1)}/{m.group(2)}.html" if m else f"{REPO_URL}/blob/main/{path_}"


def example_parts(skill):
    """(title, input_md or None, output_md, note_md, rel_path) from a skill's first
    examples/*.md. The files come in three shapes, read in this order:
      - '## Input given to the skill', then --- , the output, then --- and why it is good
      - '## Input ...' and '## Output ...' headings, with an optional '## Why ...' after
      - anything else: the whole file, as one pane (input None)."""
    d = os.path.join(catalog.skill_dir(skill), "examples")
    files = sorted(f for f in os.listdir(d) if f.endswith(".md")) if os.path.isdir(d) else []
    if not files:
        return None
    rel = catalog.rel(os.path.join(d, files[0]))
    text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    m = re.search(r"^# (.+)$", text, re.M)
    title = m.group(1) if m else files[0]
    body = re.sub(r"^# .+$\n?", "", text, count=1, flags=re.M).strip()
    if re.search(r"^## Input given to the skill\s*$", body, re.M):
        chunks = re.split(r"^-{3,}\s*$", body, flags=re.M)
        if len(chunks) > 1:
            inp = re.sub(r"^## Input given to the skill\s*$", "", chunks[0], flags=re.M).strip()
            return title, inp, chunks[1].strip(), "\n\n".join(c.strip() for c in chunks[2:]).strip(), rel
    mi = re.search(r"^## Input\b.*$", body, re.M)
    mo = re.search(r"^## Output\b.*$", body, re.M)
    if mi and mo and mi.start() < mo.start():
        mw = re.search(r"^## Why\b.*$", body[mo.end():], re.M)
        out_end = mo.end() + mw.start() if mw else len(body)
        inp = body[mi.end():mo.start()].strip().strip("-").strip()
        out = body[mo.end():out_end].strip().strip("-").strip()
        note = body[out_end:].strip() if mw else ""
        return title, inp, out, note, rel
    return title, None, body, "", rel


def proof(skill):
    """The home page's 'see it work' panes: a real input beside the output the skill returned."""
    parts = example_parts(skill)
    if not parts:
        return ""
    title, inp, out, note, rel = parts
    return f"""<div class="proof">
  <div class="proof__pane"><div class="proof__label">Input — what the team pasted</div>
    <div class="proof__body">{render_md(inp, src=rel)}</div></div>
  <div class="proof__pane"><div class="proof__label">Output — what <code>{esc(skill)}</code> returned</div>
    <div class="proof__body">{render_md(out, src=rel)}</div></div>
</div>
<p class="proof__more"><a class="pack__cta" href="skills/{esc(skill)}/#example">Read the whole report on the skill page &rarr;</a></p>"""


def card(s, root="", show_pack=True):
    """One compact row. The full description is one clamped line — the whole point of the
    redesign is that the page does not dump 49 paragraphs at a reader who hasn't chosen yet.
    Tags and `related` are deliberately absent: they live in catalogue.json and on GitHub.
    `root` is the relative path back to the site root, so the pack label links to the
    skill's pack page from any depth; a pack page listing its own skills hides the label."""
    tier = s["tier"]
    home = s["packs"][0] if s["packs"] else ""
    pack = (f'<a class="skill__pack" href="{root}packs/{esc(home)}/" title="In the {esc(home)} pack">{esc(home)}</a>'
            if home and show_pack else "")
    return f"""<li class="skill" id="{esc(s['name'])}"
   data-tier="{esc(tier)}" data-packs="{esc(' '.join(s['packs']))}"
   data-outcomes="{esc(' '.join(s.get('outcomes', [])))}"
   data-text="{esc((s['name'] + ' ' + s['description'] + ' ' + ' '.join(s['tags'])).lower())}">
  <a class="skill__link" href="{root}skills/{esc(s['name'])}/"
     title="{esc(s['description'])}">
    <span class="skill__name">{esc(s['name'])}</span>
    <span class="skill__desc">{esc(s['description'])}</span>
  </a>
  {pack}<span class="tier tier--{esc(tier)}" title="{esc(s['rationale'])}">{esc(tier)}</span>
</li>"""


def terminal(lines):
    body = "".join(
        f'<div class="term__line"><span class="term__prompt">$</span> {esc(c)}</div>'
        for c in lines
    )
    return f"""<div class="term"><div class="term__bar">
  <span class="term__dot"></span><span class="term__dot"></span><span class="term__dot"></span>
</div><div class="term__body">{body}</div></div>"""


def measured_section():
    """The published benchmark summary (RFC-0040) as a short band under the problem statement.
    Generated from docs/benchmarks/latest.json, so the numbers cannot drift from the evals page."""
    path = os.path.join(ROOT, "docs", "benchmarks", "latest.json")
    if not os.path.exists(path):
        return ""
    b = read_json(path)
    d = next(iter(b["models"].values()))
    pc = lambda x: f"{100 * x:.0f}%"
    judges = f"{pc(d['win'])} of pairs" + (f", and a second judge in {pc(d['win2'])}" if d.get("win2") is not None else "")
    lows = [c[0] for c in (d.get("win_ci"), d.get("win2_ci")) if c]
    verdict = ("Both ranges sit above even. Many skills were revised against these same evals, and a sample of them lost on evals they had not seen, so read it as progress, not proof." if lows and min(lows) > 0.5 else
               "That is better than even and not yet a clear preference, and closing it is the current work.")
    return f"""<section class="section" id="measured">
  <div class="inner"><div class="narrow">
    <p class="eyebrow">Measured</p>
    <h2>Every skill is run against the agent without it.</h2>
    <p class="lede" style="margin-bottom:0">Each acceptance eval runs twice as a real agent session, once with the skill and once without. With a skill the agent meets {pc(d['skill'])} of that skill's checks; without, {pc(d['baseline'])}. A blind judge that sees only the request and the two results preferred the skill's in {judges}. {verdict} <a href="evals/">See every skill's numbers and how they were measured &rarr;</a></p>
  </div></div>
</section>
"""


def render(skills, packs, outcomes, version, releases):

    loop_list = loops()
    promises_html = "".join(
        f'<div class="promise"><div class="promise__t">{esc(t)}</div><div class="promise__l">{esc(l)}</div></div>'
        for t, l in PROMISES)



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
            "create-on-brand-collateral": "Create on-brand collateral",
        }
        if slug in _overrides:
            return _overrides[slug]
        return slug.replace("-", " ").capitalize()

    def serving(o):
        """The packs that hold this outcome's skills, most first — so a reader goes from the
        job to the packs that do it, as agent-ready-repo's use cases do."""
        tally = {}
        for sk in skills:
            if o["name"] in sk.get("outcomes", []) and sk["packs"]:
                tally[sk["packs"][0]] = tally.get(sk["packs"][0], 0) + 1
        return [p for p, _ in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))][:3]



    # Plain language on the home page: who decides, at which step. Gate ids, caps and stage
    # contracts live in the loop reference the card links to.
    WHO = {"mechanical": "a script decides", "review": "a review panel decides", "human": "you decide"}

    usecase_rows = "".join(
        f"""<li class="uc">
      <div class="uc__main"><h3>{esc(humanize_slug(o['name']))}</h3>
        {f'<p class="uc__for">{esc(o["for"])}</p>' if o.get("for") else ''}
        <p class="uc__desc">{esc(o['description'])}</p></div>
      <div class="uc__packs">{" ".join(f'<a href="packs/{esc(p)}/">{esc(p)}</a>' for p in serving(o))}
        <a class="uc__open" href="packs/{esc(serving(o)[0])}/">Open {esc(serving(o)[0])} &rarr;</a></div>
    </li>""" for o in outcomes)

    LIFE = [("discover", "Discover", "raw signal to a ratified requirement"),
            ("design", "Design", "a requirement to a recorded decision"),
            ("build", "Build", "a requirement to merged code"),
            ("release", "Release", "merged code to live users, with a way back"),
            ("operate", "Operate", "a live service through incidents and what you learn")]
    by_loop = {lp["name"]: lp for lp in loop_list}
    flow_steps = "".join(
        f"""<li class="flow__step"><a href="loops/{n}/"><span class="flow__n">{k + 1:02d}</span>
      <b>{label}</b><span class="flow__what">{what}</span>
      <span class="flow__who">{esc('; '.join(f"{st['id']}: {WHO.get(st['gate']['kind'], st['gate']['kind'])}" for st in by_loop[n]['stages'] if st['gate']))}</span></a></li>"""
        for k, (n, label, what) in enumerate(LIFE) if n in by_loop)
    own_items = "".join(f'<li><b>{esc(t)}</b><p>{b}</p><a href="{h}">How it works &rarr;</a></li>' for t, b, h in OWN)
    team_items = "".join(f'<li><b>{esc(t)}</b><p>{esc(b)}</p><code>{esc(c)}</code> <a href="{h}">Guide &rarr;</a></li>'
                         for t, b, c, h in TEAM)

    proof_html = proof(PROOF_SKILL)



    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skilldrop — portable skills for agentic IDEs</title>
<meta name="description" content="{esc(PITCH['meta_description'])}">
<link rel="canonical" href="{SITE_URL}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#ffffff">
<meta property="og:type" content="website">
<meta property="og:site_name" content="skilldrop">
<meta property="og:locale" content="en_US">
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
.hero {{ background:linear-gradient(180deg,#fff 0%,var(--surface) 100%); color:var(--fg); padding-block:clamp(4.5rem,10vw,7.5rem) clamp(3.5rem,7vw,5.5rem); }}
.hero h1 {{
  font-size:var(--display); line-height:1.08; letter-spacing:-.032em;
  font-weight:700; margin:0 0 1.3rem; max-width:17ch;
}}
.hero .lede {{ color:var(--fg-muted); font-size:1.14rem; max-width:60ch; margin-bottom:2.2rem; }}
.hero .eyebrow {{ color:var(--accent-700); }}
.cta-row {{ display:flex; flex-wrap:wrap; gap:.75rem; margin-bottom:3.2rem; }}
.cta {{
  display:inline-block; padding:.72rem 1.35rem; border-radius:var(--r-sm);
  font-weight:600; font-size:.95rem; text-decoration:none; border:1px solid transparent;
}}
.cta--primary {{ background:var(--accent); color:#0d0d0f; }}
.cta--primary:hover {{ background:var(--accent-300); }}
.cta--ghost {{ border-color:var(--border); color:var(--fg); background:var(--card); }}
.cta--ghost:hover {{ border-color:var(--accent-700); color:var(--accent-700); }}
.stats {{ display:flex; flex-wrap:wrap; gap:2.6rem; border-top:1px solid var(--w-06); padding-top:1.9rem; }}
.promises {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:1.6rem 2.4rem; border-top:1px solid var(--border); padding-top:1.9rem; }}
.promise__t {{ font-size:1.02rem; font-weight:700; letter-spacing:-.01em; color:var(--fg); }}
.promise__l {{ font-size:.86rem; color:var(--fg-muted); margin-top:.25rem; }}
.pack__for {{ margin:-.2rem 0 .6rem; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--accent-700); }}
.pack__packs {{ display:flex; flex-wrap:wrap; gap:.4rem; margin:0 0 1rem; }}
.pack__packs a {{ font:.76rem var(--mono); text-decoration:none; color:var(--fg); border:1px solid var(--border); border-radius:999px; padding:2px 9px; }}
.pack__packs a:hover {{ border-color:var(--accent-700); color:var(--accent-700); }}
.usecases {{ list-style:none; margin:0; padding:0; border-top:1px solid var(--border); }}
.uc {{ display:grid; grid-template-columns:minmax(0,1.6fr) minmax(0,1fr); gap:.6rem 2rem; padding:1.1rem 0; border-bottom:1px solid var(--border); align-items:center; }}
@media (max-width:760px) {{ .uc {{ grid-template-columns:1fr; }} }}
.uc h3 {{ margin:0; font-size:1.05rem; letter-spacing:-.01em; }}
.uc__for {{ margin:.15rem 0 .3rem; font-size:.74rem; text-transform:uppercase; letter-spacing:.06em; color:var(--accent-700); }}
.uc__desc {{ margin:0; font-size:.9rem; color:var(--fg-muted); }}
.uc__packs {{ display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; }}
.uc__packs a {{ font:.76rem var(--mono); text-decoration:none; color:var(--fg); border:1px solid var(--border); border-radius:999px; padding:2px 9px; }}
.uc__packs a:hover {{ border-color:var(--accent-700); color:var(--accent-700); }}
.uc__packs .uc__open {{ border:0; font-family:inherit; font-size:.84rem; font-weight:600; color:var(--accent-700); padding:0 0 0 .3rem; }}
.flow {{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(5,1fr); gap:.8rem; }}
@media (max-width:900px) {{ .flow {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width:520px) {{ .flow {{ grid-template-columns:1fr; }} }}
.flow__step a {{ display:flex; flex-direction:column; gap:.3rem; height:100%; background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:1rem; text-decoration:none; color:var(--fg); }}
.flow__step a:hover {{ border-color:var(--accent-700); }}
.flow__n {{ font:600 .7rem var(--mono); color:var(--accent-700); }}
.flow__step b {{ font-size:1.02rem; }}
.flow__what {{ font-size:.86rem; color:var(--fg-muted); }}
.flow__who {{ margin-top:auto; padding-top:.5rem; font-size:.8rem; color:var(--fg); border-top:1px solid var(--border); }}
.flow__more {{ margin:1.2rem 0 0; font-size:.92rem; color:var(--fg-muted); }}
.ownteam {{ display:grid; grid-template-columns:1fr 1fr; gap:1.2rem 3rem; }}
@media (max-width:760px) {{ .ownteam {{ grid-template-columns:1fr; }} }}
.ownteam__col {{ list-style:none; margin:0; padding:0; }}
.ownteam__col li {{ padding:1rem 0; border-top:1px solid var(--border); font-size:.9rem; }}
.ownteam__col b {{ font-size:1rem; }}
.ownteam__col p {{ margin:.3rem 0 .4rem; color:var(--fg-muted); }}
.ownteam__col code {{ font:.8rem var(--mono); background:var(--surface-alt); border:1px solid var(--border); border-radius:4px; padding:1px 6px; }}
.ownteam__col a {{ font-size:.85rem; font-weight:600; text-decoration:none; }}
.pack__who {{ list-style:none; margin:0 0 1rem; padding:0; font-size:.86rem; color:var(--fg-muted); flex:1; }}
.pack__who li {{ margin:.2rem 0; }}
.pack__who b {{ color:var(--fg); font-weight:600; }}
.proof {{ display:grid; grid-template-columns:minmax(0,2fr) minmax(0,3fr); gap:1.2rem; margin-top:1.4rem; }}
@media (max-width:860px) {{ .proof {{ grid-template-columns:1fr; }} }}
.proof__pane {{ background:var(--card); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; }}
.proof__label {{ font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); padding:.7rem 1rem; border-bottom:1px solid var(--border); background:var(--surface-alt); }}
.proof__body {{ padding:.4rem 1.1rem 1rem; font-size:.86rem; max-height:560px; overflow:auto; }}
.proof__body table {{ border-collapse:collapse; width:100%; font-size:.8rem; margin:.6rem 0; }}
.proof__body th, .proof__body td {{ border-bottom:1px solid var(--border); padding:.35rem .45rem; text-align:left; vertical-align:top; }}
.proof__body h1 {{ font-size:1.05rem; margin:.8rem 0 .3rem; }}
.proof__body h2 {{ font-size:.92rem; margin:1rem 0 .3rem; }}
.proof__body code {{ font:.85em var(--mono); background:var(--accent-10); padding:0 3px; border-radius:3px; }}
.proof__more {{ margin-top:1rem; }}
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
  align-self:flex-start; cursor:pointer; font-family:inherit; font-size:.84rem; font-weight:600;
  line-height:1; color:var(--accent-700); background:none; border:0; padding:0; text-decoration:none;
}}
.pack__cta:hover {{ text-decoration:underline; }}
.pack__ctas {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:1.1rem; }}
.pack__cta--sub {{ font-weight:500; color:var(--fg-muted); }}
.pack__start {{ margin:-.4rem 0 1rem; font-size:.84rem; }}
.pack__start b {{ color:var(--accent-700); font-weight:600; }}

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
.skill__pack {{
  flex:0 0 auto; font:.7rem var(--mono); color:var(--fg-muted); text-decoration:none;
  border:1px solid var(--border); border-radius:999px; padding:1px 8px; white-space:nowrap;
}}
.skill__pack:hover {{ color:var(--accent-700); border-color:var(--accent-700); }}
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

{NAV_CSS}
@keyframes shimmer {{
  from {{ background-position:200% center; }}
  to   {{ background-position:-200% center; }}
}}
.nav__logo {{
  background:linear-gradient(90deg, var(--fg) 0%, var(--accent-700) 50%, var(--fg) 100%);
  background-size:200% auto;
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  animation:shimmer 4s linear infinite;
}}

.nav {{ transition:background .3s, box-shadow .3s; }}
.nav.scrolled {{
  background:rgba(255,255,255,.9);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  box-shadow:0 1px 0 rgba(0,0,0,.06);
}}

/* four-step strip */
.steps-strip {{ background:var(--dark-900); border-bottom:1px solid rgba(255,255,255,.08); }}
.steps {{ display:grid; grid-template-columns:repeat(5,1fr); }}
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
{site_nav()}

<header class="hero">
  <div class="inner">
    <p class="eyebrow">Open catalogue · MIT or Apache-2.0 · no runtime</p>
    <h1>{esc(PITCH['hero_h1'])}</h1>
    <p class="lede">{esc(PITCH['hero_lede'])}</p>
    <div class="cta-row">
      <a class="cta cta--primary" href="packs/">Find your pack &rarr;</a>
      <a class="cta cta--ghost" href="#proof">See what a skill produces</a>
    </div>
    <div class="promises">{promises_html}</div>
  </div>
</header>

<main id="main">
<section class="section" id="problem">
  <div class="inner"><div class="narrow">
    <p class="eyebrow">The problem</p>
    <h2>{esc(PITCH['tension_h2'])}</h2>
    <p class="lede" style="margin-bottom:0">{esc(PITCH['tension_body'])}</p>
  </div></div>
</section>

{measured_section()}
<section class="section section--alt" id="proof">
  <div class="inner">
    <p class="eyebrow">See it work</p>
    <h2>One real run: a launch that is not ready yet.</h2>
    <p class="lede">The input is what a team would paste. The output is what <a href="skills/{PROOF_SKILL}/"><code>{PROOF_SKILL}</code></a> returns, unedited, from its worked example. The rollback is fine, so it does not block, but two failure modes nothing would detect send it back.</p>
    {proof_html}
  </div>
</section>

<section class="section" id="outcomes">
  <div class="inner">
    <p class="eyebrow">Use cases</p>
    <h2>Start with the job. Meet the packs second.</h2>
    <ul class="usecases">{usecase_rows}</ul>
  </div>
</section>

<section class="section section--alt" id="loops">
  <div class="inner">
    <p class="eyebrow">How it works</p>
    <h2>The agent does the work. The decisions you can't undo stay yours.</h2>
    <p class="lede">Five loops run skills in order and stop at a gate before anything moves on. The cheaper the mistake, the more a script decides; the harder it is to undo, the more it waits for you.</p>
    <ol class="flow">{flow_steps}</ol>
    <p class="flow__more">Plus <a href="loops/ship-a-draft/"><code>ship-a-draft</code></a>, which wraps any document in intake before and critique after. <a href="loops/">Every loop &rarr;</a></p>
  </div>
</section>

<section class="section" id="own">
  <div class="inner">
    <p class="eyebrow">Yours after it lands</p>
    <h2>Files you can read, diff and edit, for you or your whole team.</h2>
    <div class="ownteam">
      <ul class="ownteam__col">{own_items}</ul>
      <ul class="ownteam__col">{team_items}</ul>
    </div>
  </div>
</section>

<section class="section section--alt" id="install">
  <div class="inner">
    <p class="eyebrow">Install</p>
    <h2>{esc(PITCH['install_h2'])}</h2>
    <div class="tabs">{tabs}
      <div class="tabs__labels">{labels}</div>
      <div class="tabs__panels">{panels}</div>
    </div>
    <p class="flow__more"><a href="packs/">Find your pack &rarr;</a> &nbsp;·&nbsp; <a href="docs/how-to/install.html">Every install route &rarr;</a></p>
  </div>
</section>
</main>

<footer class="footer"><div class="footer__inner">
  <p class="footer__brand">skilldrop</p>
  <nav class="footer__cols" aria-label="Footer">
    <div class="footer__col"><h3>Project</h3><ul>
      <li><a href="{REPO_URL}">GitHub</a></li>
      <li><a href="{NPM_URL}">npm</a></li>
      <li><a href="{REPO_URL}/blob/main/LICENSE">MIT or Apache-2.0</a></li>
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
      <li><a href="evals/">How skills are checked</a></li>
      <li><a href="{REPO_URL}/issues">Issues</a></li>
    </ul></div>
    <div class="footer__col"><h3>Release</h3><ul>
      <li><a href="changelog/">Changelog</a></li>
      <li><a href="changelog/feed.xml">Release feed (Atom)</a></li>
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

var REDUCE = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* scroll reveal — skipped under reduced motion, so nothing starts hidden */
(function() {{
  if (REDUCE || !('IntersectionObserver' in window)) return;
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
  if (REDUCE || !('IntersectionObserver' in window)) return;
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
        "license": ["https://opensource.org/licenses/MIT", "https://www.apache.org/licenses/LICENSE-2.0"],
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
            + f"  <url><loc>{SITE_URL}changelog/</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>\n"
            + "".join(f"  <url><loc>{SITE_URL}changelog/{r['version']}/</loc><lastmod>{r['date']}</lastmod><priority>0.4</priority></url>\n"
                      for r in changelog(limit=None)[1])
            + f"  <url><loc>{SITE_URL}evals/</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>\n"
            + f"  <url><loc>{SITE_URL}loops/</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>\n"
            + "".join(f"  <url><loc>{SITE_URL}loops/{lp['name']}/</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n" for lp in loops())
            + "".join(f"  <url><loc>{SITE_URL}docs/{g['kind']}/{g['slug']}.html</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n"
                      for gs in collect_guides().values() for g in gs)
            + "".join(f"  <url><loc>{SITE_URL}skills/{s['name']}/</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n" for s in skills)
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

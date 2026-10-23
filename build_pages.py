#!/usr/bin/env python3
"""build_pages.py — the site's generated inner pages (RFC-0032, RFC-0035).

  build/start/index.html          get started: install, choose the work, ask, check the result
  build/packs/index.html          every pack, grouped by the outcome it serves, then by role
  build/packs/<pack>/index.html   one pack: at a glance, one install command, what to try first
  build/skills/<skill>/index.html one skill: what it makes, a prompt to try, its quality bar
  build/skills/index.html         redirect to the searchable catalogue
  build/changelog/index.html      every release, rendered from CHANGELOG.md
  build/changelog/<v>/index.html  one release, linkable on its own
  build/changelog/feed.xml        the releases as an Atom feed, for feed readers and Slack
  build/evals/index.html          how every skill is checked: acceptance evals and trigger queries
  build/loops/index.html          every loop, and who decides at each gate
  build/loops/<loop>/index.html   one loop: diagram, stages, gates, install, how to run it
  build/search.json               the site search index the shared nav's search dialog reads
  build/404.html                  the page GitHub Pages serves for a missing URL, with the shared nav

Everything comes from pack.json, the skill manifests and SKILL.md files, loop.json and
CHANGELOG.md, read through the same collect() the home page uses, so an inner page cannot
disagree with the catalogue. Every page carries the shared nav (build_site.site_nav).

Usage:
  python3 build_pages.py [--out build]
"""
import argparse
import html.parser
import json
import os
import re

import catalog
from build_docs import render_md, collect_guides, parse_frontmatter, _slug
from build_site import (collect, card, esc, loops, site_nav, example_parts, head_meta, ld, breadcrumbs_ld, md_plain,
                        NAV_CSS, REPO_URL, SITE_URL, gallery, GALLERY_CSS)
from build_catalogue import CSS

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGE_CSS = """
.trend { margin:1rem 0; color:var(--accent,#6d4aff); } .trend svg { width:100%; max-width:560px; height:auto; display:block; }
.trend circle { fill:currentColor; } .trend__l { font-size:11px; fill:var(--muted,#666); } .trend figcaption { color:var(--muted,#666); font-size:.85rem; }
.pk { padding-block:2.2rem 3.5rem; }
.pk__title { font-size:clamp(1.6rem,3vw,2.1rem); letter-spacing:-.02em; margin:0 0 .4rem; }
.pk__crumb { font-size:.82rem; color:var(--fg-muted); margin:0 0 .6rem; }
.pk__crumb a { color:var(--fg-muted); }
.pk h2 { font-size:1.15rem; margin:2.4rem 0 .7rem; letter-spacing:-.01em; }
.pk__lede { font-size:1.05rem; color:var(--fg-muted); max-width:46rem; margin:.2rem 0 1.4rem; }
.pk pre, .pk__cmd {
  font:.88rem/1.55 var(--mono); background:var(--card); border:1px solid var(--border);
  border-radius:var(--r-sm); padding:.8rem 1rem; white-space:pre-wrap; margin:.4rem 0;
}
.pk__row { position:relative; margin:.4rem 0; }
.pk__row .pk__cmd, .pk__row pre { margin:0; padding-right:5.5rem; }
.copy {
  position:absolute; top:.45rem; right:.45rem; cursor:pointer; font:600 .74rem/1 inherit;
  color:var(--accent-700); background:var(--surface); border:1px solid var(--border);
  border-radius:var(--r-sm); padding:.4rem .6rem;
}
.copy:hover { border-color:var(--accent-700); }
.copy:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
.pk__total { font-size:.9rem; color:var(--fg-muted); margin:.4rem 0 0; }
.pk__other { margin:.6rem 0 0; font-size:.9rem; }
.pk__other summary { cursor:pointer; color:var(--accent-700); font-weight:600; }
.pk__other p { color:var(--fg-muted); margin:.5rem 0 .2rem; }
.pk__glance {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1px;
  background:var(--border); border:1px solid var(--border); border-radius:var(--r); overflow:hidden; margin:0 0 1.6rem;
}
.pk__glance > div { background:var(--card); padding:.9rem 1rem; }
.pk__glance dt { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); margin:0 0 .35rem; }
.pk__glance dd { margin:0; font-size:.9rem; }
.pk__glance ul { margin:0; padding-left:1.1rem; }
.pk__start { background:var(--accent-10); border-radius:var(--r); padding:1.1rem 1.3rem 1.2rem; margin-top:1.8rem; }
.pk__start h2 { margin-top:0; }
.pk__start dt { font-weight:600; margin-top:.9rem; font-size:.9rem; }
.pk__start dd { margin:.2rem 0 0; }
.pk__loops { list-style:none; padding:0; margin:0; }
.pk__loops li { border-top:1px solid var(--border); padding:.7rem 0; }
.pk__stages { font:.82rem var(--mono); color:var(--fg-muted); }
.pk__list { list-style:none; padding:0; margin:0; border-top:1px solid var(--border); }
.pk__list li { border-bottom:1px solid var(--border); padding:.8rem 0; }
.pk__list a { font:600 .95rem var(--mono); text-decoration:none; }
.pk__list p { margin:.2rem 0 0; color:var(--fg-muted); font-size:.9rem; }
.pk__group { margin:2rem 0 0; }
.pk__group h2 { margin:0 0 .2rem; }
.pk__group > p { margin:0 0 .6rem; color:var(--fg-muted); font-size:.92rem; }
.pk__chips { display:flex; flex-wrap:wrap; gap:.5rem; list-style:none; padding:0; margin:0; }
.pk__chips a {
  display:inline-block; font:.85rem var(--mono); text-decoration:none; color:var(--fg);
  background:var(--card); border:1px solid var(--border); border-radius:999px; padding:.3rem .8rem;
}
.pk__chips a:hover { border-color:var(--accent-700); color:var(--accent-700); }
.pk__chips b { color:var(--fg-muted); font-weight:600; margin-left:.3rem; }
.pk__meta { display:flex; flex-wrap:wrap; gap:.5rem 1.4rem; font-size:.88rem; color:var(--fg-muted); margin:0 0 1.2rem; }
.pk__meta b { color:var(--fg); font-weight:600; }
.pk__bar li { margin:.35rem 0; }
.pk__title code { font-size:1em; background:none; border:0; padding:0; }
.pk pre code { background:none; border:0; padding:0; font-size:inherit; }
.pk pre { overflow-x:auto; }
.pk code { font:.86em var(--mono); background:var(--card); border:1px solid var(--border); border-radius:4px; padding:0 .3em; }
.pk__ex { background:var(--card); border:1px solid var(--border); border-radius:var(--r); margin:.8rem 0; overflow:hidden; }
.pk__exlabel { font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); padding:.6rem 1rem; border-bottom:1px solid var(--border); background:var(--surface-alt); }
.pk__exbody { padding:.3rem 1.1rem .9rem; font-size:.9rem; max-height:640px; overflow:auto; }
.pk__exbody table { border-collapse:collapse; width:100%; font-size:.84rem; margin:.6rem 0; }
.pk__exbody th, .pk__exbody td { border-bottom:1px solid var(--border); padding:.4rem .5rem; text-align:left; vertical-align:top; }
.pk__exbody blockquote { margin:.6rem 0; padding:.1rem .9rem; border-left:3px solid var(--accent-700); color:var(--fg-muted); }
.pk__exnote { font-size:.9rem; color:var(--fg-muted); }
.cl h2 { margin:2.2rem 0 .4rem; }
.pk__muted { color:var(--fg-muted); font-size:.85em; }
.pk__badge { font:600 .62rem var(--mono); text-transform:uppercase; letter-spacing:.06em; color:var(--accent-700); background:var(--accent-10); border-radius:999px; padding:2px 8px; vertical-align:middle; }
.pk__diagram { background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:1rem; overflow-x:auto; white-space:pre; }
.pk__tablewrap { overflow-x:auto; }
.pk__table { border-collapse:collapse; width:100%; font-size:.88rem; }
.pk__table th, .pk__table td { border-bottom:1px solid var(--border); padding:.55rem .6rem; text-align:left; vertical-align:top; }
.pk__table td:nth-child(4) { white-space:nowrap; }
.pk__table th { font-size:.7rem; text-transform:uppercase; letter-spacing:.06em; color:var(--fg-muted); }
.pk__doc h2 { font-size:1.15rem; margin:2.4rem 0 .7rem; }
.pk__doc table { border-collapse:collapse; width:100%; font-size:.88rem; }
.pk__doc th, .pk__doc td { border-bottom:1px solid var(--border); padding:.45rem .55rem; text-align:left; vertical-align:top; }
.cl li { margin:.45rem 0; }
.jr { margin-top:1rem; }
.jr__time { color:var(--fg-muted); }
.jr__steps { list-style:none; counter-reset:jr; padding:0; margin:1.2rem 0; }
.jr__steps > li { counter-increment:jr; position:relative; padding:0 0 1.1rem 2.4rem; border-left:2px solid var(--border); margin-left:.8rem; }
.jr__steps > li:last-child { border-left-color:transparent; }
.jr__steps > li::before { content:counter(jr); position:absolute; left:-.85rem; top:0; width:1.6rem; height:1.6rem; border-radius:50%;
  background:var(--accent-10); color:var(--fg); font-size:.8rem; font-weight:700; display:grid; place-items:center; }
.jr__skill { font-weight:600; margin-bottom:.3rem; }
.jr dl { display:grid; grid-template-columns:max-content 1fr; gap:.25rem .8rem; margin:0; font-size:.92rem; }
.jr dt { color:var(--fg-muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; padding-top:.15rem; }
.jr dd { margin:0; }
.jr dt.jr__decide { color:var(--fg); font-weight:700; }
.jr dd.jr__decide { background:var(--accent-10); border-radius:6px; padding:.15rem .5rem; }
.jr__end { margin-top:0; }
.tbl { overflow-x:auto; margin-top:1.4rem; }
.tbl table { border-collapse:collapse; width:100%; font-size:.88rem; }
.tbl th, .tbl td { text-align:left; padding:.45rem .6rem; border-bottom:1px solid var(--border); }
.tbl th { font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:var(--fg-muted); }
@media (max-width:560px) { .jr dl { grid-template-columns:1fr; } }
.cl h2 a { color:inherit; text-decoration:none; }
.cl h2 a:hover { text-decoration:underline; }
.cl__date { color:var(--fg-muted); font-weight:400; font-size:.9em; }
.pk__roles { list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:0 1.6rem; }
.pk__roles li { border-bottom:1px solid var(--border); padding:.55rem 0; display:flex; flex-wrap:wrap; justify-content:space-between; gap:.2rem .8rem; font-size:.92rem; }
.pk__roles b { font-weight:600; }
.pk__or { margin:2.6rem 0 -.6rem; font-size:.78rem !important; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); }
.tb { margin:.6rem 0 1rem; }
.tb > input { position:absolute; opacity:0; width:1px; height:1px; }
.tb > label { display:inline-block; cursor:pointer; font-size:.88rem; font-weight:600; padding:.45rem .85rem; margin:0 .3rem .4rem 0;
  border:1px solid var(--border); border-radius:999px; background:var(--card); color:var(--fg-muted); }
.tb > input:checked + label { background:var(--accent-10); border-color:var(--accent-700); color:var(--fg); }
.tb > input:focus-visible + label { outline:2px solid var(--accent); outline-offset:2px; }
.tb__panels { border:1px solid var(--border); border-radius:var(--r); padding:.4rem 1.1rem .9rem; background:var(--card); }
.tb__panel { display:none; }
.tb__panel .pk__cmd, .tb__panel pre { background:var(--surface); }
.cl__pager { display:flex; justify-content:space-between; margin-top:2.4rem; padding-top:1rem; border-top:1px solid var(--border); }
"""

COPY_JS = """<script>
/* copy buttons — the text to copy lives in data-copy, so the visible label never leaks in */
document.querySelectorAll('.copy').forEach(function (b) {
  b.addEventListener('click', function () {
    var t = b.getAttribute('data-copy');
    var say = function (msg) { b.textContent = msg; setTimeout(function () { b.textContent = 'Copy'; }, 1500); };
    var legacy = function () {
      var a = document.createElement('textarea'); a.value = t; a.setAttribute('readonly', '');
      a.style.position = 'absolute'; a.style.left = '-9999px'; document.body.appendChild(a); a.select();
      var ok = false; try { ok = document.execCommand('copy'); } catch (e) {} document.body.removeChild(a);
      say(ok ? 'Copied' : 'Select & copy');
    };
    // The async API can be refused (permissions, iframes, headless); fall back rather than fail silently.
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(function () { say('Copied'); }, legacy);
    else legacy();
  });
});
</script>"""


def md(text):
    """Escape, then render `code` spans and **bold** — pack and skill strings carry both."""
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)


def copyable(text, tag="div", cls="pk__cmd", label="Copy"):
    """A block of text with a copy button. With scripting off the button does nothing and
    the text is still selectable, so the page never depends on it."""
    return (f'<div class="pk__row"><{tag} class="{cls}">{esc(text)}</{tag}>'
            f'<button class="copy" type="button" data-copy="{esc(text)}" aria-label="{esc(label)}: {esc(text[:60])}">Copy</button></div>')


def install_block(primary, others, note=""):
    """One command a newcomer can paste, and the alternatives folded away. Three equal
    commands make the reader choose before they know the difference."""
    alt = "".join(f"<p>{esc(why)}</p>{copyable(cmd, label='Copy command')}" for why, cmd in others)
    return (copyable(primary, label="Copy command")
            + (f'<p class="pk__total">{note}</p>' if note else "")
            + (f'<details class="pk__other"><summary>Other ways to install</summary>{alt}</details>' if others else ""))


def shell(title, desc, canonical, depth, body, current=None, extra_head="", root=None):
    root = "../" * depth if root is None else root
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — skilldrop</title>
{head_meta(f"{title} — skilldrop", desc, canonical)}
{extra_head}
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111114" media="(prefers-color-scheme: dark)">
<style>
{CSS}{NAV_CSS}{PAGE_CSS}{GALLERY_CSS}</style>
</head>
<body>
{site_nav(root, current)}
{body}
{COPY_JS}
</body>
</html>
"""


def pretty(outcome):
    words = outcome.replace("-", " ").capitalize()
    return re.sub(r"\bai\b", "AI", words.replace("claude api", "Claude API"))


def gates(loop):
    return [(st["gate"], st["id"]) for st in loop["stages"] if st.get("gate")]


def glance(pack, total, own_loops, outcome_counts):
    """The pack's contract before the install: when to use it, what it covers, where a person
    decides, and how big it is — agent-ready-repo's journey strip, from data we already have."""
    gs = [(g, st, l["name"]) for l in own_loops for g, st in gates(l)]
    people = [x for x in gs if x[0]["kind"] in ("human", "review")]
    decide = ("<ul>" + "".join(
        f"<li><b>{esc(g['id'])}</b> {esc(g['kind'])} — {esc(lp)} → {esc(st)}</li>" for g, st, lp in people)
        + "</ul>") if people else "No gated loop of its own; the skills run one at a time."
    covers = ", ".join(f"{esc(pretty(o))} ({n})" for o, n in outcome_counts) or "—"
    size = (f"{total} skills · {len(own_loops)} loop{'s' if len(own_loops) != 1 else ''}"
            + (f" · {len(gs)} gate{'s' if len(gs) != 1 else ''}, {len(people)} need{'s' if len(people) == 1 else ''} a person" if gs else ""))
    return f"""<dl class="pk__glance">
<div><dt>When to use it</dt><dd>{md(pack['description'])}</dd></div>
<div><dt>Covers</dt><dd>{covers}</dd></div>
<div><dt>Where you decide</dt><dd>{decide}</dd></div>
<div><dt>Size</dt><dd>{size}{f'<br>{esc(pack["journey"]["time"])} a session' if pack.get("journey", {}).get("time") else ''}</dd></div>
</dl>"""


def pack_page(name, pack, packs, by_name, loop_by_name, outcome_of):
    title = pack.get("display_name", name)
    reqs = pack.get("requires", [])
    fv = pack.get("first-value")
    total = len(set(pack["skills"]).union(*(packs[r]["skills"] for r in reqs)))
    own_loops = [loop_by_name[l] for l in pack.get("loops", []) if l in loop_by_name]
    counts = {}
    for s in pack["skills"]:
        for o in outcome_of.get(s, []):
            counts[o] = counts.get(o, 0) + 1
    outcome_counts = sorted(counts.items(), key=lambda kv: -kv[1])

    others = []
    if pack.get("loops") or any(packs[r].get("loops") for r in reqs):
        others.append(("The pack's loops too, each as an invokable skill:", f"npx skilldrop-cli install --loop --pack {name}"))
    others.append(("In Claude Code, as a plugin (after /plugin marketplace add sananthanarayan/skilldrop):", f"/plugin install {name}@skilldrop"))
    others.append(("Into Cursor, Kiro or another IDE:", f"npx skilldrop-cli install --pack {name} --ide cursor"))
    note = f"Installs {total} skills" + (
        ", including " + ", ".join(f'<a href="../{esc(r)}/">{esc(r)}</a>' for r in reqs) if reqs else "") + "."

    parts = ['<main class="inner pk" id="main" data-pagefind-body data-pagefind-meta="kind:pack">',
             '<p class="pk__crumb"><a href="../">Packs</a></p>',
             f'<h1 class="pk__title">{esc(title)}</h1>',
             glance(pack, total, own_loops, outcome_counts),
             install_block(f"npx skilldrop-cli install --pack {name}", others, note)]

    if fv:
        pre = "".join(f"<li>{md(p)}</li>" for p in fv["prerequisites"])
        parts.append(f"""<section class="pk__start" aria-labelledby="start">
<h2 id="start">Start here: {esc(fv['starter-task'])}</h2>
<p>Paste this into your agent:</p>
{copyable(fv['starter-prompt'], tag="pre", cls="pk__prompt", label="Copy prompt")}
<dl>
{f'<dt>Before you start</dt><dd><ul>{pre}</ul></dd>' if pre else ''}
<dt>How to tell it worked</dt><dd>{md(fv['verification'])}</dd>
<dt>If nothing happens</dt><dd>{md(fv['recovery'])}</dd>
</dl>
</section>""")

    j = pack.get("journey")
    if j:
        parts.append(journey_section(j, by_name))

    if own_loops:
        items = "".join(
            f"""<li><a href="../../loops/{esc(l['name'])}/"><b>{esc(l['name'])}</b></a> — {esc(l['description'].split(' Use when')[0])}
<div class="pk__stages">{' → '.join(esc(st['id']) + (f" [{esc(st['gate']['id'])}]" if st['gate'] else '') for st in l['stages'])}</div></li>"""
            for l in own_loops)
        parts.append(f'<h2>Loops</h2><ul class="pk__loops">{items}</ul>')

    parts.append(f'<p class="pk__total"><a href="../compare/?a={esc(name)}">Compare {esc(title)} with another pack</a></p>')
    cards = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(pack["skills"]) if s in by_name)
    parts.append(f'<h2>Skills in this pack ({len(pack["skills"])})</h2><ul class="skills">{cards}</ul>')
    for r in reqs:
        rc = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(packs[r]["skills"]) if s in by_name)
        parts.append(f'<h2>Included from <a href="../{esc(r)}/">{esc(r)}</a> ({len(packs[r]["skills"])})</h2><ul class="skills">{rc}</ul>')
    parts.append("</main>")
    crumbs = breadcrumbs_ld([("skilldrop", SITE_URL), ("Packs", f"{SITE_URL}packs/"), (title, f"{SITE_URL}packs/{name}/")])
    return shell(title, pack["description"], f"{SITE_URL}packs/{name}/", 2, "\n".join(parts),
                 current="packs/", extra_head=crumbs)


def journey_section(j, by_name):
    """A typical session: what you type, what you get, and where you decide, step by step."""
    skill = lambda n: f'<a href="../../skills/{esc(n)}/"><code>{esc(n)}</code></a>' if n in by_name else f"<code>{esc(n)}</code>"
    steps = "".join(
        f"""<li><div class="jr__skill">{skill(st['skill'])}</div>
<dl><dt>You</dt><dd>{md(st['you_do'])}</dd><dt>You get</dt><dd>{md(st['you_get'])}</dd>
{f'<dt class="jr__decide">You decide</dt><dd class="jr__decide">{md(st["decide"])}</dd>' if st.get('decide') else ''}</dl></li>"""
        for st in j["steps"])
    bring = "".join(f"<li>{md(b)}</li>" for b in j["you_bring"])
    return f"""<section class="jr" aria-labelledby="session">
<h2 id="session">A typical session</h2>
<p><b>When:</b> {md(j['when'])}{f" <span class='jr__time'>About {esc(j['time'])}.</span>" if j.get('time') else ''}</p>
<p><b>You bring:</b></p><ul>{bring}</ul>
<ol class="jr__steps">{steps}</ol>
<p class="jr__end"><b>You end with:</b> {md(j['you_end_with'])}</p>
</section>"""


# Who reaches for which pack. Every pack but core (which comes with each of them) must be
# placed here, so a new pack can't go missing from "Start with your role".
ROLES = [
    ("Product manager", ["product-manager", "trackers"]),
    ("Software engineer", ["dev-team", "api-builder"]),
    ("Frontend engineer", ["frontend"]),
    ("Solution architect", ["solution-architect"]),
    ("SRE or on-call engineer", ["sre-oncall"]),
    ("Platform or infrastructure engineer", ["infra-as-code"]),
    ("Designer", ["experience-design", "design"]),
    ("Data analyst", ["data-analytics"]),
    ("Researcher", ["research"]),
    ("Compliance, risk or privacy lead", ["grc"]),
    ("AI engineer", ["ai-engineering", "skill-engineering"]),
    ("Writing for leaders or customers", ["stakeholder-comms", "converters"]),
    ("Applying for a job", ["career"]),
]


def roles_section(packs, root=""):
    placed = {p for _, ps in ROLES for p in ps}
    missing = sorted(set(packs) - placed - {"core"})
    unknown = sorted(placed - set(packs))
    if missing or unknown:
        raise SystemExit(f"build_pages.py: ROLES is out of date: missing {missing}, unknown {unknown}")
    rows = "".join(
        f'<li><b>{esc(role)}</b><span>' + " · ".join(
            f'<a href="{root}{esc(n)}/">{esc(packs[n].get("display_name", n))}</a>' for n in ps) + "</span></li>"
        for role, ps in ROLES)
    return f'<section class="pk__group" aria-labelledby="roles"><h2 id="roles">Start with your role</h2><ul class="pk__roles">{rows}</ul></section>'


# The starting jobs the get-started page offers, each answered by one pack's first value.
START_JOBS = [
    ("Build and review code", "dev-team"),
    ("Decide what to build", "product-manager"),
    ("Design the system", "solution-architect"),
    ("Run the service", "sre-oncall"),
    ("Trust the numbers", "data-analytics"),
    ("Finish one document", "core"),
]


def tabs(group, items):
    """Tabs from radio buttons and CSS alone, so they work with scripting off and arrow keys
    move between them. items: [(id, label, panel_html)]; the first is selected."""
    radios = "".join(
        f'<input type="radio" name="{group}" id="{group}-{i}"{" checked" if n == 0 else ""}>'
        f'<label for="{group}-{i}">{esc(label)}</label>' for n, (i, label, _) in enumerate(items))
    panels = "".join(f'<div class="tb__panel" id="{group}-{i}-panel">{body}</div>' for i, _, body in items)
    rules = "".join(f"#{group}-{i}:checked ~ .tb__panels #{group}-{i}-panel {{ display:block; }}" for i, _, _ in items)
    return f'<style>{rules}</style><div class="tb">{radios}<div class="tb__panels">{panels}</div></div>'


def start_page(packs, loop_by_name):
    """Get started in four steps: install, choose the work, ask, then check the result and
    where you decide. Every command and prompt comes from pack.json, so it can't drift."""
    install = tabs("via", [
        ("cli", "Any agent, with the CLI",
         "<p>Needs Node 16.7 or later. Installs one pack into Claude Code's user folder; add <code>--ide cursor</code>, "
         "<code>--ide copilot</code>, <code>--ide kiro</code> or <code>--ide codex</code> for another tool.</p>"
         + copyable("npx skilldrop-cli install --pack core", label="Copy command")
         + "<p>Add <code>--dry-run</code> first to see every file it would write.</p>"),
        ("plugin", "Claude Code plugin",
         "<p>Add the catalogue once, then install the plugin for a pack:</p>"
         + copyable("/plugin marketplace add sananthanarayan/skilldrop", label="Copy command")
         + copyable("/plugin install core@skilldrop", label="Copy command")),
        ("copy", "No CLI: copy a folder",
         "<p>A skill is a plain folder. Copying it is the whole install:</p>"
         + copyable("git clone https://github.com/sananthanarayan/skilldrop && cp -R skilldrop/packs/core/skills/doc-critique ~/.claude/skills/", label="Copy command")),
    ])
    jobs = []
    for label, n in START_JOBS:
        p = packs[n]
        fv, j = p["first-value"], p.get("journey", {})
        jobs.append((n, label, f"""<p><b><a href="../packs/{esc(n)}/">{esc(p.get('display_name', n))}</a>:</b> {esc(fv['starter-task'])}.{f" About {esc(j['time'])}." if j.get('time') else ''}</p>
{copyable(f"npx skilldrop-cli install --pack {n}", label="Copy command")}
<p>Then paste this into your agent:</p>
{copyable(fv['starter-prompt'], tag="pre", cls="pk__prompt", label="Copy prompt")}
<p class="pk__total"><b>How to tell it worked:</b> {md(fv['verification'])}</p>"""))
    more = " · ".join(f'<a href="../packs/{esc(n)}/#start">{esc(p.get("display_name", n))}</a>'
                      for n, p in packs.items() if n not in dict((b, a) for a, b in START_JOBS))
    asks = "".join(f"<li>{esc(packs[n]['first-value']['starter-prompt'])}</li>" for n in ("research", "grc", "converters") if n in packs)
    human = sorted({st["gate"]["id"] for l in loop_by_name.values() for st in l["stages"]
                    if st.get("gate") and st["gate"]["kind"] == "human"}, key=lambda g: [int(x) for x in re.findall(r"\d+", g)])
    body = f"""<main class="inner pk" id="main" data-pagefind-body>
<h1 class="pk__title">Get started</h1>
<p class="pk__lede">Install the skills for the work in front of you, ask for that work in your own words, and check what comes back.</p>
<p>A skill is a folder of instructions your agent reads when your request matches it: a <code>SKILL.md</code>, sometimes a standard-library Python script, and the evals that check it. Installing one copies files you can read, diff and edit, and runs nothing. A skill that needs a command or a network host names it in its manifest.</p>

<h2 id="install">Step 1: install</h2>
{install}

<h2 id="work">Step 2: choose your starting work</h2>
<p>Each pack's first task is chosen so you can judge the result in minutes.</p>
{tabs("job", jobs)}
<p class="pk__total">Other packs, each with its own first task: {more}. Not sure which? <a href="../packs/#roles">Start with your role</a> or <a href="../packs/compare/">compare two packs</a>.</p>

<h2 id="ask">Step 3: make the first request</h2>
<p>Ask in plain language. Your agent picks the skill from what you ask for, so there is no command to remember. You can also name a skill, or type <code>/skill-name</code> in Claude Code. Other first requests that work:</p>
<ul>{asks}</ul>
<p>Looking for a skill by what it does? <code>npx skilldrop-cli search review my sql</code> lists the best matches.</p>

<h2 id="check">Step 4: check the result and where you decide</h2>
<ul class="pk__bar">
<li><b>A review ends with a verdict</b>, such as <code>SHIP IT</code>, <code>SHIP WITH CHANGES</code> or <code>MAJOR REWRITE</code>, and each finding points to the part of the work it is about.</li>
<li><b>A draft marks what it couldn't confirm.</b> Read those marks before anyone relies on the draft.</li>
<li><b>A loop stops at its gates.</b> A script, a review panel or you decide each one. The gates that need a person ({', '.join(esc(g) for g in human)}) are never passed for you; with no one there, the loop stops and says who it needs.</li>
<li><b>Every skill ships with its evals.</b> <a href="../evals/">How skills are checked</a> shows how each one is measured against the agent without it.</li>
</ul>

<h2 id="next">Continue</h2>
<ul class="pk__bar">
<li><a href="../docs/tutorial/follow-a-change-through-the-loops.html">Follow one change through every loop</a>, from idea to operating it.</li>
<li><a href="../docs/explanation/operating-model.html">The operating model</a>: the five stages, the packs in each, and where you decide.</li>
<li><a href="../docs/how-to/install-per-ide.html">Install into Cursor, Copilot, Kiro or Codex</a>, and <a href="../docs/reference/install-options.html">every install option</a>.</li>
<li><a href="../catalogue/">Browse every skill</a> or <a href="../loops/">every loop</a>.</li>
<li><a href="../docs/how-to/upgrade-skills.html">Keep installed skills current</a>.</li>
</ul>
</main>"""
    crumbs = breadcrumbs_ld([("skilldrop", SITE_URL), ("Get started", f"{SITE_URL}start/")])
    return shell("Get started", "Install skilldrop, choose your starting work, make a first request and check the result.",
                 f"{SITE_URL}start/", 1, body, current="start/", extra_head=crumbs)


def index_page(packs, outcomes, home_of):
    """Packs grouped by the job in front of you, then the full list. A newcomer usually knows
    the task ("decide what to build") before they know which pack is theirs."""
    groups = []
    for oname, o in outcomes.items():
        tally = {}
        for s in o["skills"]:
            h = home_of.get(s)
            if h:
                tally[h] = tally.get(h, 0) + 1
        chips = "".join(
            f'<li><a href="{esc(p)}/">{esc(p)}<b>{n}</b></a></li>'
            for p, n in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])))
        groups.append(f"""<section class="pk__group"><h2>{esc(pretty(oname))}</h2>
<p>{esc(o['description'])}</p><ul class="pk__chips">{chips}</ul></section>""")
    items = "".join(
        f"""<li><a href="{esc(n)}/">{esc(p.get('display_name', n))}</a>
<p>{esc(p['description'])}</p>
{f'<p><b>Start here:</b> {esc(p["first-value"]["starter-task"])}</p>' if p.get('first-value') else ''}
{f'<p><a href="{esc(n)}/#session">Walk through a typical session</a>: {" → ".join(esc(st["skill"]) for st in p["journey"]["steps"])}</p>' if p.get('journey') else ''}</li>"""
        for n, p in packs.items())
    body = f"""<main class="inner pk" id="main">
<h1 class="pk__title">Packs</h1>
<p class="pk__lede">Start from your role or the job in front of you. Each pack installs with one command, and every role pack brings <a href="core/">core</a> with it. The number beside a pack is how many of that job's skills it holds. Choosing between two? <a href="compare/">Compare them side by side</a>.</p>
{roles_section(packs)}
<h2 class="pk__or">Or start from the job</h2>
{''.join(groups)}
<h2>Every pack</h2>
<ul class="pk__list">{items}</ul>
</main>"""
    return shell("Packs", "Every skilldrop pack, grouped by the job it does, with what to try first.",
                 f"{SITE_URL}packs/", 1, body, current="packs/")


COMPARE_CSS = """<style>
.cmp__pick{display:flex;flex-wrap:wrap;gap:.8rem 1.2rem;align-items:end;margin:1rem 0 1.4rem}
.cmp__pick label{display:flex;flex-direction:column;gap:.25rem;font-size:.85rem;color:var(--muted);font-weight:600}
.cmp__pick select{font:inherit;padding:.4rem .6rem;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--fg);min-width:14rem}
.cmp{width:100%;border-collapse:collapse;table-layout:fixed}
.cmp th,.cmp td{text-align:left;vertical-align:top;padding:.7rem .7rem;border-top:1px solid var(--border)}
.cmp thead th{border-top:0;font-size:1.15rem}
.cmp thead th:first-child{width:16%}.cmp tbody th{font-size:.85rem;color:var(--muted)}
.cmp ul{margin:0;padding-left:1.1rem}.cmp code{font-size:.85em}
.cmp__chips{display:flex;flex-wrap:wrap;gap:.3rem;list-style:none;padding:0!important}
.cmp__chips li a{display:inline-block;padding:.1rem .5rem;border:1px solid var(--border);border-radius:999px;font-size:.85rem;text-decoration:none}
@media (max-width:700px){.cmp thead th:first-child{width:28%}}
</style>"""

COMPARE_JS = r"""<script>
/* Re-render the comparison for the two packs picked; the default pair is already in the page,
   so with scripting off the page still compares something and links every pack. */
(function () {
  var data = JSON.parse(document.getElementById('cmp-data').textContent);
  var a = document.getElementById('cmp-a'), b = document.getElementById('cmp-b'), table = document.getElementById('cmp');
  var el = function (tag, text, attrs) { var e = document.createElement(tag); if (text != null) e.textContent = text;
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]); return e; };
  var list = function (items) { var u = el('ul'); items.forEach(function (t) { u.appendChild(el('li', t)); }); return u; };
  var chips = function (names) { if (!names.length) return el('span', 'none');
    var u = el('ul', null, { 'class': 'cmp__chips' });
    names.forEach(function (n) { var li = el('li'); li.appendChild(el('a', n, { href: '../../skills/' + n + '/' })); u.appendChild(li); }); return u; };
  var cell = function (row, node) { var td = el('td'); if (typeof node === 'string') td.textContent = node; else td.appendChild(node); row.appendChild(td); };
  var render = function () {
    var A = data[a.value], B = data[b.value];
    if (!A || !B) return;
    var inA = {}, inB = {}; A.skills.forEach(function (n) { inA[n] = 1; }); B.skills.forEach(function (n) { inB[n] = 1; });
    var rows = [
      ['What it is for', function (P) { return P.description; }],
      ['Start it when', function (P) { return P.when; }],
      ['You bring', function (P) { return list(P.bring); }],
      ['Try first', function (P) { return P.starter; }],
      ['Loops and gates', function (P) { return P.loops.length ? list(P.loops) : 'No loop of its own; the skills run one at a time.'; }],
      ['Where a person decides', function (P) { return P.decide; }],
      ['Jobs it covers', function (P) { return P.outcomes.join(', ') || '-'; }],
      ['Size', function (P) { return P.size; }],
      ['Only in this pack', function (P, Q, inQ) { return chips(P.skills.filter(function (n) { return !inQ[n]; })); }],
      ['In both', function (P, Q, inQ) { return chips(P.skills.filter(function (n) { return inQ[n]; })); }],
      ['Install', function (P) { return el('code', P.install); }]
    ];
    var body = el('tbody'), head = el('thead'), hr = el('tr');
    hr.appendChild(el('th', '', { scope: 'col' }));
    [A, B].forEach(function (P) { var th = el('th', null, { scope: 'col' }); th.appendChild(el('a', P.title, { href: '../' + P.name + '/' })); hr.appendChild(th); });
    head.appendChild(hr);
    rows.forEach(function (r) {
      var tr = el('tr'); tr.appendChild(el('th', r[0], { scope: 'row' }));
      if (r[0] === 'In both') { var td = el('td', null, { colspan: '2' }); td.appendChild(r[1](A, B, inB)); tr.appendChild(td); }
      else { cell(tr, r[1](A, B, inB)); cell(tr, r[1](B, A, inA)); }
      body.appendChild(tr);
    });
    table.replaceChildren(head, body);
    history.replaceState(null, '', '?a=' + encodeURIComponent(a.value) + '&b=' + encodeURIComponent(b.value));
  };
  var q = new URLSearchParams(location.search);
  if (data[q.get('a')]) a.value = q.get('a');
  if (data[q.get('b')]) b.value = q.get('b');
  if (a.value === b.value) b.value = Object.keys(data).filter(function (n) { return n !== a.value && n !== 'core'; })[0];
  a.addEventListener('change', render); b.addEventListener('change', render);
  if (q.get('a') || q.get('b')) render();
})();
</script>"""


def compare_data(packs, by_name, loop_by_name, outcome_of):
    """Each pack as the rows the comparison shows. Skills include what `requires` brings, so
    the shared row shows what installing either one gives you anyway."""
    data = {}
    for name, pack in packs.items():
        reqs = pack.get("requires", [])
        skills = sorted(set(pack["skills"]).union(*(packs[r]["skills"] for r in reqs)))
        own_loops = [loop_by_name[l] for l in pack.get("loops", []) if l in loop_by_name]
        gs = [g for l in own_loops for g, _ in gates(l)]
        people = [g for g in gs if g["kind"] in ("human", "review")]
        counts = {}
        for sk in pack["skills"]:
            for o in outcome_of.get(sk, []):
                counts[o] = counts.get(o, 0) + 1
        fv, j = pack.get("first-value") or {}, pack.get("journey") or {}
        data[name] = {
            "name": name, "title": pack.get("display_name", name),
            "description": md_plain(pack["description"]), "when": md_plain(j.get("when", "")) or "-",
            "bring": [md_plain(b) for b in j.get("you_bring", [])], "starter": fv.get("starter-task", "-"),
            "loops": [f"{l['name']}: " + " → ".join(st["id"] + (f" [{st['gate']['id']} {st['gate']['kind']}]" if st.get("gate") else "")
                                                   for st in l["stages"]) for l in own_loops],
            "decide": (", ".join(f"{g['id']} ({g['kind']})" for g in people) if people else "No gate of its own"),
            "outcomes": [pretty(o) for o, _ in sorted(counts.items(), key=lambda kv: -kv[1])],
            "size": f"{len(skills)} skills installed ({len(pack['skills'])} its own)" + (f", {len(own_loops)} loop{'s' if len(own_loops) != 1 else ''}" if own_loops else ""),
            "skills": [x for x in skills if x in by_name],
            "install": f"npx skilldrop-cli install --pack {name}"}
    return data


def compare_page(packs, by_name, loop_by_name, outcome_of, a="product-manager", b="solution-architect"):
    """Two packs side by side for someone choosing between them (or deciding they need both)."""
    data = compare_data(packs, by_name, loop_by_name, outcome_of)
    a, b = (a if a in data else next(iter(data))), (b if b in data else list(data)[1])
    opts = lambda sel: "".join(f'<option value="{esc(n)}"{" selected" if n == sel else ""}>{esc(d["title"])}</option>' for n, d in data.items())
    A, B = data[a], data[b]
    chips = lambda names: ('<ul class="cmp__chips">' + "".join(f'<li><a href="../../skills/{esc(n)}/">{esc(n)}</a></li>' for n in names)
                           + "</ul>") if names else "none"
    ul = lambda items: "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"
    rows = [("What it is for", lambda P, Q: esc(P["description"])), ("Start it when", lambda P, Q: esc(P["when"])),
            ("You bring", lambda P, Q: ul(P["bring"])), ("Try first", lambda P, Q: esc(P["starter"])),
            ("Loops and gates", lambda P, Q: ul(P["loops"]) if P["loops"] else "No loop of its own; the skills run one at a time."),
            ("Where a person decides", lambda P, Q: esc(P["decide"])), ("Jobs it covers", lambda P, Q: esc(", ".join(P["outcomes"]) or "-")),
            ("Size", lambda P, Q: esc(P["size"])),
            ("Only in this pack", lambda P, Q: chips([n for n in P["skills"] if n not in Q["skills"]]))]
    body = "".join(f'<tr><th scope="row">{esc(t)}</th><td>{f(A, B)}</td><td>{f(B, A)}</td></tr>' for t, f in rows)
    body += f'<tr><th scope="row">In both</th><td colspan="2">{chips([n for n in A["skills"] if n in B["skills"]])}</td></tr>'
    body += f'<tr><th scope="row">Install</th><td><code>{esc(A["install"])}</code></td><td><code>{esc(B["install"])}</code></td></tr>'
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html_body = f"""<main class="inner pk" id="main">
<p class="pk__crumb"><a href="../">Packs</a></p>
<h1 class="pk__title">Compare two packs</h1>
<p class="pk__lede">Pick two packs to see what each is for, where a person decides, and which skills only one of them has. Installing both is fine: shared skills install once.</p>
<form class="cmp__pick" onsubmit="return false">
<label>First pack<select id="cmp-a">{opts(a)}</select></label>
<label>Second pack<select id="cmp-b">{opts(b)}</select></label>
</form>
<table class="cmp" id="cmp"><thead><tr><th scope="col"></th><th scope="col"><a href="../{esc(a)}/">{esc(A["title"])}</a></th><th scope="col"><a href="../{esc(b)}/">{esc(B["title"])}</a></th></tr></thead>
<tbody>{body}</tbody></table>
<script type="application/json" id="cmp-data">{payload}</script>
</main>"""
    return shell("Compare two packs", "Two skilldrop packs side by side: what each is for, its loops and gates, and the skills only one has.",
                 f"{SITE_URL}packs/compare/", 2, html_body + COMPARE_JS, current="packs/", extra_head=COMPARE_CSS)


def _section(md_text, heading):
    """The bullet list under `## heading` in a SKILL.md, one string per bullet."""
    m = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", md_text, re.M | re.S)
    if not m:
        return []
    out, cur = [], None
    for line in m.group(1).splitlines():
        if line.startswith("- "):
            cur = line[2:].strip()
            out.append(cur)
        elif cur is not None and line.startswith("  ") and line.strip():
            out[-1] += " " + line.strip()
    return out


def eval_files(sdir):
    load = lambda f: json.load(open(os.path.join(sdir, "evals", f), encoding="utf-8")) \
        if os.path.exists(os.path.join(sdir, "evals", f)) else None
    return (load("evals.json") or {}).get("evals", []), load("eval_queries.json") or []


def checks_section(name, sdir):
    """The skill's acceptance evals and trigger queries, so a reader sees what "working" means
    before installing — the same files the weekly eval run uses."""
    evs, qs = eval_files(sdir)
    if not evs and not qs:
        return ""
    asserts = "".join(f"<li>{md(a)}</li>" for e in evs for a in e.get("assertions", []))
    yes = "".join(f"<li>{esc(q['query'])}</li>" for q in qs if q.get("should_trigger"))
    no = "".join(f"<li>{esc(q['query'])}</li>" for q in qs if not q.get("should_trigger"))
    n_a = sum(len(e.get("assertions", [])) for e in evs)
    return f"""<section aria-labelledby="checked"><h2 id="checked">How it's checked</h2>
{measured_line(name)}
<p class="pk__total">{n_a} assertion{'s' if n_a != 1 else ''} across {len(evs)} acceptance eval{'s' if len(evs) != 1 else ''}, and {len(qs)} trigger queries. <a href="../../evals/">Every skill's checks</a></p>
<details class="pk__other"><summary>What the output must do</summary><ul class="pk__bar">{asserts}</ul></details>
<details class="pk__other"><summary>When it should and shouldn't activate</summary>
<p><b>Should activate:</b></p><ul>{yes}</ul><p><b>Should leave to another skill:</b></p><ul>{no}</ul></details>
</section>"""


BENCH = os.path.join(ROOT, "docs", "benchmarks", "latest.json")
# Skills admitted since the last full run, with the held-out measurement each was admitted on.
ADMISSIONS = os.path.join(ROOT, "docs", "benchmarks", "admissions.json")


def rfc_url(num):
    import glob
    hits = glob.glob(os.path.join(ROOT, "docs", "rfcs", "%s-*.md" % num))
    return f"{REPO_URL}/blob/main/docs/rfcs/{os.path.basename(hits[0])}" if hits else f"{REPO_URL}/tree/main/docs/rfcs"


def admissions():
    if not os.path.exists(ADMISSIONS):
        return {}
    return {r["skill"]: r for r in json.load(open(ADMISSIONS, encoding="utf-8"))["skills"]}


def measured_line(name):
    """One sentence on how this skill scored against plain Claude Code, from the last full run or,
    for a skill admitted since, from its admission measurement."""
    bench = json.load(open(BENCH, encoding="utf-8")) if os.path.exists(BENCH) else {}
    full = {r["skill"]: r for r in reversed(bench.get("skills", []))}
    if name in full:
        r = full[name]
        pref = r["preferred"]
        said = ("preferred it" if pref > .5 else "preferred the agent without it" if pref < .5 else "had no preference")
        return (f'<p class="pk__total"><b>Measured against plain Claude Code</b> ({esc(bench["date"])}): it met '
                f'{100 * r["skill_met"]:.0f}% of its checks, against {100 * r["baseline_met"]:.0f}% without it, and a '
                f'blind judge {said}. <a href="../../evals/">How skills are checked</a></p>')
    a = admissions().get(name)
    if a:
        j1, j2 = a["judge1"], a["judge2"]
        drafts = f", on its {['', '', 'second', 'third', 'fourth'][a['drafts']]} draft" if a["drafts"] > 1 else ""
        return (f'<p class="pk__total"><b>Admitted against plain Claude Code</b>{drafts}: on held-out evals written '
                f'blind from its description, two judges preferred it in {j1[0]} of {j1[1]} and {j2[0]} of {j2[1]} '
                f'pairs, and it met {100 * a["skill_met"]:.0f}% of their checks, against {100 * a["baseline_met"]:.0f}% '
                f'without it (<a href="{rfc_url(a["rfc"])}">RFC-{esc(a["rfc"])}</a>). '
                f'<a href="../../evals/#admitted">How skills are checked</a></p>')
    return ""


def admitted_section(adm):
    if not adm:
        return ""
    rows = "".join(
        f'<tr><td><a href="../skills/{esc(a["skill"])}/"><code>{esc(a["skill"])}</code></a></td>'
        f'<td>{esc(a["evals"])}</td><td>{a["judge1"][0]} of {a["judge1"][1]}</td><td>{a["judge2"][0]} of {a["judge2"][1]}</td>'
        f'<td>{100 * a["skill_met"]:.0f}%</td><td>{100 * a["baseline_met"]:.0f}%</td>'
        f'<td>{a["drafts"]}</td><td><a href="{rfc_url(a["rfc"])}">RFC-{esc(a["rfc"])}</a></td></tr>'
        for a in sorted(adm.values(), key=lambda a: (a["rfc"], a["skill"])))
    return f"""<section aria-labelledby="admitted"><h2 id="admitted">Admitted since the last full run ({len(adm)})</h2>
<p>A new skill ships only if it beats plain Claude Code on <b>held-out evals</b>: requests written by someone who saw only the skill's description, never its instructions. Two judges compare the two answers blind, over two trials, and both must prefer the skill in at least half the pairs. A draft that fails is revised from the judges' reasons and measured again on evals it has never seen. These are the measurements each was admitted on. They join the table above at the next full run.</p>
<div class="tbl"><table>
<thead><tr><th>Skill</th><th>Held-out evals</th><th>Judge 1 preferred it</th><th>Judge 2</th><th>Checks met, with it</th><th>Without</th><th>Drafts</th><th>Record</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</section>"""




def bench_section(b):
    """The latest published run_bench.py summary (RFC-0040): each eval run as an agent session
    with the skill and without it. Numbers are shown with their intervals and their limits."""
    pc = lambda x: "–" if x is None else f"{100 * x:.0f}%"
    rng = lambda c, signed=False: "" if not c else (
        f" ({100 * c[0]:+.0f} to {100 * c[1]:+.0f})" if signed else f" ({100 * c[0]:.0f}% to {100 * c[1]:.0f}%)")
    blocks = []
    for model, d in b["models"].items():
        blocks.append(f"""<dl class="pk__glance">
<div><dt>Assertions met with the skill</dt><dd>{pc(d['skill'])}</dd></div>
<div><dt>Without it</dt><dd>{pc(d['baseline'])}</dd></div>
<div><dt>Lift, points</dt><dd>{100 * d['lift']:+.0f}{rng(d['lift_ci'], True)}</dd></div>
<div><dt>Preferred by a blind judge</dt><dd>{pc(d['win'])}{rng(d['win_ci'])}</dd></div>
{f"""<div><dt>Second judge</dt><dd>{pc(d['win2'])}{rng(d['win2_ci'])}, same side as the first in {d['judges_agree']} of {d['judges_decided']}</dd></div>""" if d.get('second_judge') else ""}
<div><dt>Cost per run</dt><dd>${d['cost_skill']:.2f} with, ${d['cost_baseline']:.2f} without</dd></div>
<div><dt>Model</dt><dd><code>{esc(model)}</code>, {d['evals']} evals</dd></div>
</dl>""")
        kinds = d.get("by_kind", {})
        if len(kinds) == 2:
            rows = "".join(
                f'<tr><td>{name}</td><td>{kinds[k]["evals"]} evals, {kinds[k]["skills"]} skills</td>'
                f'<td>{pc(kinds[k]["skill"])}</td><td>{pc(kinds[k]["baseline"])}</td>'
                f'<td>{pc(kinds[k]["win"])}{rng(kinds[k]["win_ci"])}</td>'
                f'<td>{pc(kinds[k].get("win2"))}{rng(kinds[k].get("win2_ci"))}</td></tr>'
                for k, name in (("author", "Written by the skill&rsquo;s author"),
                                ("held_out", "Written without seeing the skill")))
            blocks.append(f"""<div class="tbl"><table>
<thead><tr><th>Evals</th><th>How many</th><th>Assertions met with the skill</th><th>Without</th><th>Preferred blind</th><th>Second judge</th></tr></thead>
<tbody>{rows}</tbody></table></div>""")
    sj = next((d for d in b["models"].values() if d.get("second_judge")), None)
    second = "" if not sj else (
        f"<li><b>Second judge.</b> A different model, <code>{esc(sj['second_judge'])}</code>, judged the same pairs in the same order. "
        f"The two picked the same side in {sj['judges_agree']} of {sj['judges_decided']} pairs where both chose one, so a single pair's verdict "
        "is weak evidence and the percentage across all pairs is the result. Both judges are models from one family and can share blind spots; "
        "no human has checked them.</li>\n")
    how = ("a Claude Code agent session with file and shell tools, sandboxed in an empty directory"
           if b.get("backend") == "claude-cli" else "one model call with no tools")
    return f"""<section aria-labelledby="measured"><h2 id="measured">Measured: with the skill and without it</h2>
<p class="pk__lede">Each acceptance eval is run twice on the same model, once with the skill and once without, as {how}. Last run {esc(b['date'])}, judged by <code>{esc(b['judge_model'])}</code>, {b['trials']} trial{'s' if b['trials'] != 1 else ''} per eval.</p>
{''.join(blocks)}
<ul class="pk__bar">
<li><b>Assertions met</b> is graded by a judge that doesn't know which run it is reading. The skill's author wrote the assertions, so the run without the skill is graded on a rubric it never saw. A non-answer meets {pc(b.get('floor'))} of them.</li>
<li><b>Preferred by a blind judge</b> is the share of pairs where a judge that saw only the request and both results, in shuffled order, picked the skill's. 50% means no preference.</li>
{second}<li>Ranges are 95% intervals over evals. A lift range that includes 0, or a preference range that includes 50%, is not a result.</li>
<li>Most skills have one eval, so a single row below is an anecdote. The judge is a model. Cost is list price for the tokens used.</li>
<li>Skills that lost were revised after reading the judges' reasons and run again on the same evals, so part of the preference on evals their author wrote is fitted to them. Evals written by someone who never read the skill are counted separately{" above" if any(len(d.get("by_kind", {})) == 2 for d in b["models"].values()) else ""}. Some skills were later revised, or admitted, on the verdicts from those evals too, so that row is the better guide but not a clean one; <a href="../docs/explanation/what-the-benchmark-showed.html">what the benchmark showed</a> separates the evals nothing was decided on.</li>
</ul>
<p>Reproduce it with <code>python3 run_bench.py</code> (<a href="{REPO_URL}/blob/main/docs/rfcs/0040-skill-benchmark.md">RFC-0040</a>).</p>
</section>"""


def retired_section(bench):
    """RFC-0046: skills that left the catalogue because the agent did as well without them.
    Listed here because this is where the evidence for removing them lives."""
    retired = catalog.index().get("retired", {})
    if not retired:
        return ""
    measured = {r["skill"] for r in (bench or {}).get("skills", [])}
    rows = "".join(f'<tr><td><code>{esc(n)}</code></td><td>{esc(r["in"])}</td><td>{esc(r["why"])}</td></tr>'
                   for n, r in sorted(retired.items()))
    note = (" The published run above was made before they left, so its totals include them."
            if measured & set(retired) else "")
    return f"""<h2 id="retired">Retired skills</h2>
<p>A skill that adds only a format, and no rule the agent breaks without it, is removed rather than revised again (<a href="{REPO_URL}/blob/main/docs/rfcs/0046-keep-rebuild-or-retire.md">RFC-0046</a>). An installed copy keeps working; <code>skilldrop outdated</code> says it was retired and why.{note}</p>
<div class="tbl"><table>
<thead><tr><th>Skill</th><th>Retired in</th><th>Why</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""


EVAL_HISTORY = os.environ.get("EVAL_HISTORY", os.path.join(ROOT, ".eval-history"))


def eval_runs():
    """The counts-only summaries the evals workflow appends to the eval-history branch
    (RFC-0055), oldest first. The site build fetches the branch into .eval-history/."""
    d = os.path.join(EVAL_HISTORY, "runs")
    runs = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                try:
                    r = json.load(open(os.path.join(d, f), encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(r, dict) and r.get("date"):
                    runs.append(r)
    return sorted(runs, key=lambda r: r["date"])


def _pct(pair):
    n, d = (pair or [0, 0])
    return f"{100 * n / d:.0f}%" if d else "–"


def trend_section(runs):
    weekly = [r for r in runs if r.get("activation") and r.get("scope", "all") == "all"]
    monthly = [r for r in runs if r.get("assertions") and r.get("scope", "all") == "all"]
    if not weekly and not monthly:
        return ('<h2 id="trend">Week by week</h2><p>No scheduled run yet. The weekly trigger check and the monthly '
                'assertion run start once the repository has an <code>ANTHROPIC_API_KEY</code> secret; each run then '
                'adds a point here.</p>')
    parts = ['<h2 id="trend">Week by week</h2>']
    if weekly:
        last = weekly[-12:]
        pts = [(r["date"], 100 * r["activation"]["passed"] / r["activation"]["total"]) for r in last if r["activation"]["total"]]
        if len(pts) >= 2:
            w, h, pad = 560, 140, 28
            lo = max(0, min(v for _, v in pts) - 5)
            hi = min(100, max(v for _, v in pts) + 5)
            span = (hi - lo) or 1
            xy = [(pad + i * (w - 2 * pad) / (len(pts) - 1), h - pad - (v - lo) / span * (h - 2 * pad)) for i, (_, v) in enumerate(pts)]
            line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
            dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"><title>{esc(d)}: {v:.0f}%</title></circle>'
                           for (x, y), (d, v) in zip(xy, pts))
            parts.append(f'<figure class="trend"><svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="trend-t">'
                         f'<title id="trend-t">Share of trigger queries routed as intended, {esc(pts[0][0])} to {esc(pts[-1][0])}: '
                         f'{pts[0][1]:.0f}% to {pts[-1][1]:.0f}%</title>'
                         f'<text x="{pad}" y="16" class="trend__l">{hi:.0f}%</text><text x="{pad}" y="{h - 8}" class="trend__l">{lo:.0f}%</text>'
                         f'<polyline points="{line}" fill="none" stroke="currentColor" stroke-width="2"/>{dots}</svg>'
                         '<figcaption>Trigger queries routed as intended, per weekly run.</figcaption></figure>')
        rows = "".join(
            f'<tr><td>{esc(r["date"])}</td><td>{_pct([r["activation"]["passed"], r["activation"]["total"]])}</td>'
            f'<td>{_pct(r["activation"].get("triggers"))}</td><td>{_pct(r["activation"].get("quiet"))}</td>'
            f'<td><code>{esc((r.get("models") or {}).get("router", "?"))}</code></td></tr>' for r in reversed(last))
        parts.append('<div class="tbl"><table><thead><tr><th>Run</th><th>Routed as intended</th><th>Picked when it should be</th>'
                     f'<th>Left alone when it should be</th><th>Router model</th></tr></thead><tbody>{rows}</tbody></table></div>')
        if len(weekly) >= 2:
            a, b = weekly[-2]["activation"].get("by_skill", {}), weekly[-1]["activation"].get("by_skill", {})
            moved = []
            for sk in sorted(set(a) & set(b)):
                pa, pb = a[sk], b[sk]
                if pa[1] and pb[1] and pa[0] / pa[1] != pb[0] / pb[1]:
                    moved.append((pb[0] / pb[1] - pa[0] / pa[1], sk, pa, pb))
            if moved:
                items = "".join(f'<li><a href="../skills/{esc(sk)}/"><code>{esc(sk)}</code></a>: {pa[0]}/{pa[1]} → {pb[0]}/{pb[1]}</li>'
                                for _, sk, pa, pb in sorted(moved))
                parts.append(f'<p>Moved since the run before ({len(moved)}), falls first:</p><ul>{items}</ul>')
            else:
                parts.append("<p>No skill's routing changed since the run before.</p>")
    if monthly:
        rows = "".join(
            f'<tr><td>{esc(r["date"])}</td><td>{_pct([r["assertions"]["met"], r["assertions"]["total"]])}</td>'
            f'<td>{r["assertions"].get("evals", 0)}</td><td>{r["assertions"].get("skipped", 0)}</td>'
            f'<td>{"$%.2f" % r.get("spent", 0)}{(" of $%.0f" % r["budget"]) if r.get("budget") else ""}</td></tr>'
            for r in reversed(monthly[-12:]))
        parts.append('<h3>Monthly assertion runs</h3><p>Each eval\'s prompt run through its skill and graded against its assertions, '
                     'under a dollar budget. When the budget runs out first, the rest wait: the order changes each month, so '
                     'every skill is reached over a few months.</p>'
                     '<div class="tbl"><table><thead><tr><th>Run</th><th>Assertions met</th><th>Evals graded</th>'
                     f'<th>Left for next month</th><th>Spent</th></tr></thead><tbody>{rows}</tbody></table></div>')
    return "\n".join(parts)


def evals_page(skills):
    bench = json.load(open(BENCH, encoding="utf-8")) if os.path.exists(BENCH) else None
    measured = {r["skill"]: r for r in (bench or {}).get("skills", [])}  # first model listed wins
    for r in reversed((bench or {}).get("skills", [])):
        measured[r["skill"]] = r
    adm = {k: v for k, v in admissions().items() if k not in measured}
    rows, tot_e, tot_a, tot_q, covered = [], 0, 0, 0, 0
    for s in sorted(skills, key=lambda s: (s["packs"][0], s["name"])):
        sdir = catalog.skill_dir(s["name"])
        evs, qs = eval_files(sdir)
        n_a = sum(len(e.get("assertions", [])) for e in evs)
        pos = sum(1 for q in qs if q.get("should_trigger"))
        tot_e, tot_a, tot_q = tot_e + len(evs), tot_a + n_a, tot_q + len(qs)
        covered += bool(evs and qs)
        src = f"{REPO_URL}/tree/main/{s['path']}/evals"
        m = measured.get(s["name"])
        a = adm.get(s["name"])
        got = "" if not bench else (
            f'<td>{100 * m["skill_met"]:.0f}%</td><td>{100 * m["baseline_met"]:.0f}%</td>'
            f'<td>{"skill" if m["preferred"] > .5 else "no skill" if m["preferred"] < .5 else "tie"}</td>'
            if m else (f'<td>{100 * a["skill_met"]:.0f}%*</td><td>{100 * a["baseline_met"]:.0f}%*</td><td>skill*</td>'
                       if a else "<td>–</td><td>–</td><td>–</td>"))
        rows.append(f'<tr><td><a href="../skills/{esc(s["name"])}/#checked"><code>{esc(s["name"])}</code></a></td>'
                    f'<td>{esc(s["packs"][0])}</td><td>{len(evs)}</td><td>{n_a}</td>{got}'
                    f'<td>{pos} / {len(qs) - pos}</td><td><a href="{src}">files</a></td></tr>')
    body = f"""<main class="inner pk" id="main" data-pagefind-body data-pagefind-meta="kind:evals">
<h1 class="pk__title">How skills are checked</h1>
<p class="pk__lede">Every skill ships two eval files. <b>Acceptance evals</b> are realistic prompts with assertions the output must meet, taken from the skill's own quality bar. <b>Trigger queries</b> are phrasings that should activate the skill, and near-misses that belong to a named sibling instead.</p>
<dl class="pk__glance">
<div><dt>Skills with both files</dt><dd>{covered} of {len(skills)}</dd></div>
<div><dt>Acceptance evals</dt><dd>{tot_e}, with {tot_a} assertions</dd></div>
<div><dt>Trigger queries</dt><dd>{tot_q}</dd></div>
<div><dt>Run</dt><dd>{("Benchmarked " + esc(bench["date"]) + ", by hand") if bench else "By hand"}</dd></div>
</dl>
<p><code>validate.py</code> fails any skill without both files, on every pull request. The acceptance evals are run by hand with <code>run_bench.py</code>, as agent sessions with and without each skill; the latest result is below. A <a href="{REPO_URL}/actions/workflows/evals.yml">scheduled workflow</a> asks a model each week which skill it would load for every trigger query, and once a month runs the acceptance evals under a budget; it is switched off until the repository has an API key. A miss is a prompt to look at the description, not a gate. Run them yourself with <code>python3 run_evals.py</code> and an <code>ANTHROPIC_API_KEY</code>.</p>
<p>The site itself is checked with the catalogue's own skills: <a href="../docs/explanation/own-skills-on-own-site.html">its performance and accessibility reviews, and what was fixed</a>.</p>
{bench_section(bench) if bench else ""}
{admitted_section(adm)}
{trend_section(eval_runs())}
<h2 id="every-skill">Every skill</h2>
<div class="tbl"><table>
<thead><tr><th>Skill</th><th>Pack</th><th>Evals</th><th>Assertions</th>{"<th>Met with skill</th><th>Without</th><th>Blind judge preferred</th>" if bench else ""}<th>Should / shouldn't trigger</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
{'<p class="pk__total">* Measured at admission, on held-out evals; see <a href="#admitted">admitted since the last full run</a>.</p>' if adm else ''}
{retired_section(bench)}
</main>"""
    return shell("How skills are checked", "Every skilldrop skill's acceptance evals and trigger queries, and how they run.",
                 f"{SITE_URL}evals/", 1, body)


def live_examples(name):
    """A skill's examples/*.html: finished pages a reader can open, published beside the skill
    page. Each file's <title> names it. They are copied as they are, never rewritten."""
    d = os.path.join(catalog.skill_dir(name), "examples")
    found = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".html"):
            text = open(os.path.join(d, f), encoding="utf-8").read()
            m = re.search(r"<title>(.*?)</title>", text, re.S)
            found.append((f, html.unescape(m.group(1).strip()) if m else f, text))
    return found


def skill_page(s, by_name, packs, outcome_of):
    name, home = s["name"], s["packs"][0]
    sdir = catalog.skill_dir(name)
    manifest = json.load(open(os.path.join(sdir, "manifest.json"), encoding="utf-8"))
    body_md = open(os.path.join(sdir, "SKILL.md"), encoding="utf-8").read()
    bar = _section(body_md, "Quality bar")
    try_prompt = None
    ev = os.path.join(sdir, "evals", "evals.json")
    if os.path.exists(ev):
        evs = json.load(open(ev, encoding="utf-8")).get("evals", [])
        try_prompt = evs[0]["prompt"] if evs else None

    rel = lambda n: f'<a href="../{esc(n)}/">{esc(n)}</a>' if n in by_name else esc(n)
    meta = (f'<span>Pack <b><a href="../../packs/{esc(home)}/">{esc(home)}</a></b></span>'
            f'<span>Tier <b title="{esc(s["rationale"])}">{esc(s["tier"])}</b></span>'
            + (f'<span>Job <b>{", ".join(esc(pretty(o)) for o in outcome_of.get(name, []))}</b></span>' if outcome_of.get(name) else "")
            + f'<span>v{esc(s["version"])}</span>')
    others = [("With the sibling skills it hands off to:", f"npx skilldrop-cli install {name} --with-related"),
              ("The whole pack it belongs to:", f"npx skilldrop-cli install --pack {home}"),
              ("By hand, from a clone of the repo:", f"cp -R {s['path']} ~/.claude/skills/"),
              (f"In Claude Code, with the {home} plugin installed, invoke it as:", f"/{home}:{name}")]
    parts = ['<main class="inner pk" id="main" data-pagefind-body data-pagefind-meta="kind:skill">',
             f'<p class="pk__crumb"><a href="../../catalogue/">Skills</a> · <a href="../../packs/{esc(home)}/">{esc(home)}</a></p>',
             f'<h1 class="pk__title"><code>{esc(name)}</code></h1>',
             f'<p class="pk__lede">{esc(s["description"])}</p>',
             f'<p class="pk__meta">{meta}</p>',
             install_block(f"npx skilldrop-cli install {name}", others)]
    if try_prompt:
        parts.append(f"""<section class="pk__start" aria-labelledby="try"><h2 id="try">Try it</h2>
<p>A realistic prompt from the skill's acceptance evals:</p>
{copyable(try_prompt, tag="pre", cls="pk__prompt", label="Copy prompt")}</section>""")
    if bar:
        parts.append('<h2>What a good result looks like</h2><ul class="pk__bar">'
                     + "".join(f"<li>{md(b)}</li>" for b in bar) + "</ul>")
    live = live_examples(name)
    if live:
        parts.append('<section aria-labelledby="live"><h2 id="live">Live examples</h2>'
                     '<p>Pages this skill made, as it made them. Each one is a single file that works offline; '
                     f'the specs and inputs they were built from are <a href="{REPO_URL}/tree/main/{esc(s["path"])}/examples">in the repo</a>.</p>'
                     + gallery([(name, f, t) for f, t, _ in live], root="../../", show_skill=False) + "</section>")
    ex = example_parts(name)
    if ex:
        ex_title, ex_in, ex_out, ex_note, ex_rel = ex
        parts.append(f"""<section aria-labelledby="example"><h2 id="example">Example output</h2>
<p class="pk__total">{esc(ex_title.replace('Worked example — ', ''))} · the skill's own worked example, <a href="{REPO_URL}/blob/main/{esc(ex_rel)}">source</a></p>
{f'<div class="pk__ex"><div class="pk__exlabel">Input</div><div class="pk__exbody">{render_md(ex_in, src=ex_rel)}</div></div>' if ex_in else ''}
<div class="pk__ex"><div class="pk__exlabel">{'Output' if ex_in else 'Worked example'}</div><div class="pk__exbody">{render_md(ex_out, src=ex_rel)}</div></div>
{f'<div class="pk__exnote">{render_md(ex_note, src=ex_rel)}</div>' if ex_note else ''}
</section>""")
    parts.append(checks_section(name, sdir))
    hand = manifest.get("handoff") or []
    if hand:
        parts.append("<h2>Hands off to</h2><ul>" + "".join(
            f"<li>{rel(h['to'])} — when {esc(h['when'])}. {esc(h['purpose'])}</li>" for h in hand) + "</ul>")
    related = [r for r in s.get("related", []) if r not in {h["to"] for h in hand}]
    if related:
        parts.append(f"<h2>Related skills</h2><p>{', '.join(rel(r) for r in related)}</p>")
    parts.append(f'<h2>Source</h2><p><a href="{REPO_URL}/blob/main/{esc(s["path"])}/SKILL.md">SKILL.md</a> · '
                 f'<a href="{REPO_URL}/tree/main/{esc(s["path"])}">the whole folder</a> on GitHub.</p></main>')
    url = f"{SITE_URL}skills/{name}/"
    meta = (breadcrumbs_ld([("skilldrop", SITE_URL), ("Skills", f"{SITE_URL}catalogue/"),
                            (home, f"{SITE_URL}packs/{home}/"), (name, url)])
            + ld({"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": name,
                  "description": md_plain(s["description"]), "url": url,
                  "codeRepository": f"{REPO_URL}/tree/main/{s['path']}", "license": ["https://opensource.org/licenses/MIT", "https://www.apache.org/licenses/LICENSE-2.0"],
                  "version": s["version"], "isPartOf": {"@type": "Collection", "name": f"skilldrop {home} pack",
                                                        "url": f"{SITE_URL}packs/{home}/"}}))
    return shell(name, s["description"], url, 2, "\n".join(parts), current="catalogue/", extra_head=meta)


RELEASE_HEAD = re.compile(r"^##\s+(\d+\.\d+\.\d+)\s+[—-]\s+(\d{4}-\d{2}-\d{2})\s*$")


def releases():
    """CHANGELOG.md -> [{version, date, md}], newest first. Wrapped bullet lines are joined first,
    because the docs renderer treats each source line as its own block. The file's own intro is
    for maintainers (format rules), so it is skipped."""
    lines, out = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read().splitlines(), []
    for line in lines:
        if line.startswith("  ") and line.strip() and out and out[-1].startswith("- "):
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    rels = []
    for line in out:
        m = RELEASE_HEAD.match(line)
        if m:
            rels.append({"version": m.group(1), "date": m.group(2), "md": []})
        elif rels:
            rels[-1]["md"].append(line)
    for r in rels:
        r["md"] = "\n".join(r["md"]).strip()
    return rels


def changelog_page(rels):
    """Every release on one page; each heading links to that release's own page."""
    parts = ['<main class="inner pk cl" id="main"><h1 class="pk__title">What\'s new</h1>',
             '<p class="pk__crumb">Every release and what it lets you do. '
             '<a href="feed.xml">Follow the release feed (Atom)</a>.</p>']
    for r in rels:
        parts.append(f'<h2 id="v{esc(r["version"])}"><a href="{esc(r["version"])}/">{esc(r["version"])}</a> '
                     f'<span class="cl__date">— {esc(r["date"])}</span></h2>')
        parts.append(render_md(r["md"], src="CHANGELOG.md", docs_base="../docs/"))
    parts.append("</main>")
    return shell("What's new", "Every skilldrop release and what it lets you do.",
                 f"{SITE_URL}changelog/", 1, "\n".join(parts), current="changelog/")


def release_page(rels, i):
    r = rels[i]
    newer = rels[i - 1] if i > 0 else None
    older = rels[i + 1] if i + 1 < len(rels) else None
    pager = '<nav class="cl__pager" aria-label="Other releases">' + (
        f'<a href="../{esc(older["version"])}/">← {esc(older["version"])}</a>' if older else "<span></span>") + (
        f'<a href="../{esc(newer["version"])}/">{esc(newer["version"])} →</a>' if newer else "<span></span>") + "</nav>"
    body = (f'<main class="inner pk cl" id="main" data-pagefind-body data-pagefind-meta="kind:release"><p class="pk__crumb"><a href="../">What\'s new</a> ›</p>'
            f'<h1 class="pk__title">skilldrop {esc(r["version"])}</h1>'
            f'<p class="pk__crumb">Released {esc(r["date"])} · <code>npx skilldrop-cli@{esc(r["version"])}</code></p>'
            f'{render_md(r["md"], src="CHANGELOG.md", docs_base="../../docs/")}{pager}</main>')
    first = re.sub(r"[`*]", "", next((l[2:] for l in r["md"].splitlines() if l.startswith("- ")), ""))
    return shell(f"skilldrop {r['version']}", first or f"What shipped in skilldrop {r['version']}.",
                 f"{SITE_URL}changelog/{r['version']}/", 2, body, current="changelog/")


def feed(rels):
    """Atom 1.0. Entry ids are the release pages' URLs, which never change, so a reader shows
    each release once. Content is the rendered HTML with links made absolute."""
    def x(t):
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    entries = []
    for r in rels[:30]:
        url = f"{SITE_URL}changelog/{r['version']}/"
        html_body = render_md(r["md"], src="CHANGELOG.md", docs_base=f"{SITE_URL}docs/")
        entries.append(f"""  <entry>
    <title>skilldrop {x(r['version'])}</title>
    <id>{url}</id>
    <link rel="alternate" type="text/html" href="{url}"/>
    <updated>{r['date']}T00:00:00Z</updated>
    <content type="html">{x(html_body)}</content>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>skilldrop releases</title>
  <subtitle>What each skilldrop release lets you do.</subtitle>
  <id>{SITE_URL}changelog/</id>
  <link rel="self" type="application/atom+xml" href="{SITE_URL}changelog/feed.xml"/>
  <link rel="alternate" type="text/html" href="{SITE_URL}changelog/"/>
  <updated>{rels[0]['date']}T00:00:00Z</updated>
  <author><name>skilldrop</name><uri>{REPO_URL}</uri></author>
{chr(10).join(entries)}
</feed>
"""


class _Text(html.parser.HTMLParser):
    """Visible text of rendered HTML, for the search index. A real parser rather than a tag
    regex, so markup in a guide cannot leak into (or hide from) the index."""
    def __init__(self):
        super().__init__()
        self.out = []

    def handle_data(self, data):
        self.out.append(data)


def plain(html_text, limit):
    p = _Text()
    p.feed(html_text)
    return re.sub(r"\s+", " ", " ".join(p.out)).strip()[:limit]


def search_index(skills, packs, loop_list):
    """One flat list for the site search: every skill, pack, loop and guide, each with a
    root-relative URL. Skill and guide bodies are trimmed so the index stays small enough to
    fetch on first use (it is only loaded when someone opens search)."""
    out = []
    for s in skills:
        body = open(os.path.join(catalog.skill_dir(s["name"]), "SKILL.md"), encoding="utf-8").read()
        _, body = parse_frontmatter(body)
        out.append({"type": "skill", "title": s["name"], "summary": s["description"],
                    "url": f"skills/{s['name']}/",
                    "text": " ".join(s.get("tags", [])) + " " + plain(render_md(body), 1800)})
    for n, p in packs.items():
        fv = p.get("first-value") or {}
        out.append({"type": "pack", "title": p.get("display_name", n) + (f" ({n})" if p.get("display_name") else ""),
                    "summary": p["description"], "url": f"packs/{n}/",
                    "text": " ".join([fv.get("starter-task", ""), fv.get("starter-prompt", "")] + p["skills"] + p.get("loops", []))})
    ref = open(os.path.join(ROOT, "guides", "reference", "loops.md"), encoding="utf-8").read()
    anchors = {m.group(1): _slug(re.sub(r"[*`\[\]]", "", m.group(0)[3:]))
               for m in re.finditer(r"^## `([a-z0-9-]+)`.*$", ref, re.M)}
    for l in loop_list:
        out.append({"type": "loop", "title": l["name"], "summary": l["description"],
                    "url": f"loops/{l['name']}/",
                    "text": " ".join(st["id"] + " " + " ".join(st["skills"]) + " " + st.get("intent", "") for st in l["stages"])})
    for kind, guides in collect_guides().items():
        for g in guides:
            _, body = parse_frontmatter(open(g["abs_path"], encoding="utf-8").read())
            out.append({"type": kind, "title": g["title"], "summary": g["summary"],
                        "url": f"docs/{kind}/{g['slug']}.html",
                        "text": plain(render_md(body), 3000)})
    return out


WHO = {"mechanical": "a script decides", "review": "a review panel decides", "human": "you decide"}
MERMAID = ('<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
           'mermaid.initialize({ startOnLoad: true, securityLevel: "strict" });</script>')


def loop_summary(lp):
    return lp["description"].split(" Use when")[0].rstrip(".") + "."


def loop_page(lp, by_name):
    """One loop: what it is for, who decides where, one install command, the generated diagram,
    the stage table, then the loop's own run instructions and quality bar from its LOOP.md."""
    name = lp["name"]
    home = catalog.loop_homes()[name][0]
    spec = json.load(open(os.path.join(catalog.loop_dir(name), "loop.json"), encoding="utf-8"))
    use = lp["description"].split(" Use when", 1)
    gates_ = [(st, st["gate"]) for st in spec["stages"] if st.get("gate")]
    decide = "<ul>" + "".join(f"<li><b>{esc(st['id'].capitalize())}</b> ({esc(g['id'])}): {WHO.get(g['kind'], g['kind'])}</li>"
                              for st, g in gates_) + "</ul>"
    glance = f"""<dl class="pk__glance">
<div><dt>Use it when</dt><dd>{esc(('Use when' + use[1]) if len(use) > 1 else loop_summary(lp))}</dd></div>
<div><dt>Comes with</dt><dd>The <a href="../../packs/{esc(home)}/">{esc(home)}</a> pack</dd></div>
<div><dt>Where you decide</dt><dd>{decide}</dd></div>
<div><dt>Size</dt><dd>{len(spec['stages'])} stages · {len(gates_)} gate{'s' if len(gates_) != 1 else ''} · up to {spec.get('cap', 3)} revision rounds</dd></div>
</dl>"""
    others = [("Every loop in its pack, with their skills:", f"npx skilldrop-cli install --loop --pack {home}"),
              ("The loop alone, without its stage skills (each stage falls back to an inline version):", f"npx skilldrop-cli install --loop {name} --no-skills"),
              (f"In Claude Code, the {home} plugin includes it:", f"/plugin install {home}@skilldrop")]
    mmd_path = os.path.join(ROOT, "docs", "loops", f"{name}.mmd")
    diagram = (f'<pre class="mermaid pk__diagram">{esc(open(mmd_path, encoding="utf-8").read())}</pre>'
               if os.path.exists(mmd_path) else "")
    skill = lambda s: f'<a href="../../skills/{esc(s)}/"><code>{esc(s)}</code></a>' if s in by_name else (
        "any generator" if s == "*" else f"<code>{esc(s)}</code>")
    rows = "".join(
        f"<tr><td>{n + 1}</td><td><b>{esc(st['id'])}</b><br><span class=\"pk__muted\">{esc(st['type'])}</span></td>"
        f"<td>{esc(st.get('intent', ''))}</td><td>{', '.join(skill(x) for x in st['skills'])}</td>"
        f"<td>{(esc(st['gate']['id']) + ' — ' + WHO.get(st['gate']['kind'], st['gate']['kind']) + '<br><span class=\"pk__muted\">' + esc(' · '.join(st['gate'].get('verdicts', []))) + '</span>') if st.get('gate') else '—'}</td></tr>"
        for n, st in enumerate(spec["stages"]))
    table = (f'<div class="pk__tablewrap"><table class="pk__table"><thead><tr><th>#</th><th>Stage</th><th>What it does</th>'
             f'<th>Skills</th><th>Gate</th></tr></thead><tbody>{rows}</tbody></table></div>')
    rel = catalog.rel(os.path.join(catalog.loop_dir(name), "LOOP.md"))
    _, body = parse_frontmatter(open(os.path.join(ROOT, rel), encoding="utf-8").read())
    body = re.sub(r"\A\s*# [^\n]*\n", "", body)                       # the page shows the title
    body = re.sub(r"^## Stages\s*$.*?(?=^## )", "", body, flags=re.M | re.S)  # the table above replaces it
    parts = ['<main class="inner pk" id="main" data-pagefind-body data-pagefind-meta="kind:loop">',
             f'<p class="pk__crumb"><a href="../">Loops</a> · <a href="../../packs/{esc(home)}/">{esc(home)}</a></p>',
             f'<h1 class="pk__title"><code>{esc(name)}</code>{" <span class=\"pk__badge\">wrapper</span>" if lp["kind"] == "wrapper" else ""}</h1>',
             f'<p class="pk__lede">{esc(loop_summary(lp))}</p>',
             glance,
             install_block(f"npx skilldrop-cli install --loop {name}", others,
                           "Installs the loop as an invokable skill, plus every skill its stages run."),
             f"<h2>The loop</h2>{diagram}",
             f"<h2>Stages</h2>{table}",
             f'<div class="pk__doc">{render_md(body, src=rel, docs_base="../../docs/")}</div>',
             f'<h2>Source</h2><p><a href="{REPO_URL}/blob/main/{esc(rel)}">LOOP.md</a> · '
             f'<a href="{REPO_URL}/blob/main/{esc(catalog.rel(os.path.join(catalog.loop_dir(name), "loop.json")))}">loop.json</a> on GitHub · '
             f'<a href="../../docs/explanation/loops.html">Why loops</a></p>',
             MERMAID, "</main>"]
    url = f"{SITE_URL}loops/{name}/"
    crumbs = breadcrumbs_ld([("skilldrop", SITE_URL), ("Loops", f"{SITE_URL}loops/"), (name, url)])
    return shell(name, loop_summary(lp), url, 2, "\n".join(parts), current="loops/", extra_head=crumbs)


LIFECYCLE = ["discover", "design", "build", "release", "operate", "ship-a-draft"]


def loops_index(loop_list):
    loop_list = sorted(loop_list, key=lambda lp: (LIFECYCLE.index(lp["name"]) if lp["name"] in LIFECYCLE else 99, lp["name"]))
    cards = "".join(
        f"""<li><a href="{esc(lp['name'])}/">{esc(lp['name'])}</a>{' <span class="pk__badge">wrapper</span>' if lp['kind'] == 'wrapper' else ''}
<p>{esc(loop_summary(lp))}</p>
<p class="pk__muted">{' · '.join(f"{esc(st['id'].capitalize())}: {WHO.get(st['gate']['kind'], st['gate']['kind'])}" for st in lp['stages'] if st['gate'])}</p></li>"""
        for lp in loop_list)
    body = f"""<main class="inner pk" id="main">
<h1 class="pk__title">Loops</h1>
<p class="pk__lede">A loop runs skills in order and stops at a gate before anything moves on. The cheaper the mistake, the more a script decides; the harder it is to undo, the more it waits for you. Five cover the lifecycle; <code>ship-a-draft</code> wraps any generator. See them all on one page in the <a href="../docs/explanation/operating-model.html">operating model</a>, or read <a href="../docs/explanation/loops.html">why loops</a>.</p>
<ul class="pk__list">{cards}</ul>
</main>"""
    return shell("Loops", "Every skilldrop loop: its stages, and who decides at each gate.", f"{SITE_URL}loops/", 1, body,
                 current="loops/", extra_head=breadcrumbs_ld([("skilldrop", SITE_URL), ("Loops", f"{SITE_URL}loops/")]))


def not_found_page():
    """GitHub Pages serves /404.html for any missing URL, at whatever depth it was asked for,
    so every link here is absolute to the site root rather than relative."""
    root = "/skilldrop/"
    body = f"""<main class="inner pk" id="main">
<h1 class="pk__title">That page isn't here.</h1>
<p class="pk__lede">The link may be from before skills moved into packs (<code>skills/&lt;name&gt;/</code> is now <code>packs/&lt;pack&gt;/skills/&lt;name&gt;/</code> on GitHub), or the page never existed. Search, or start from one of these:</p>
<ul class="pk__list">
<li><a href="{root}packs/">Packs</a><p>Every pack, grouped by the job it does, with what to try first.</p></li>
<li><a href="{root}catalogue/">All skills</a><p>Search and filter every skill by job, pack or tier.</p></li>
<li><a href="{root}loops/">Loops</a><p>The sequences that run skills in order, and who decides at each gate.</p></li>
<li><a href="{root}docs/">Docs</a><p>Install guides, tutorials, the loop reference and the skill catalogue.</p></li>
<li><a href="{root}changelog/">What's new</a><p>Every release and what it lets you do.</p></li>
</ul>
<p><a class="js-search" href="{root}docs/">Search the site</a> (press <kbd>/</kbd>)</p>
</main>"""
    page = shell("Page not found", "This page doesn't exist. Find a pack, a skill or a guide instead.",
                 f"{SITE_URL}404.html", 0, body, root=root)
    return page.replace('<link rel="canonical"', '<meta name="robots" content="noindex">\n<link rel="canonical"', 1)


def render():
    """Return {relative_path: html} for every generated inner page."""
    skills, _, _ = collect()
    by_name = {s["name"]: s for s in skills}
    packs = catalog.packs()
    outcomes = catalog.outcomes()
    outcome_of = {}
    for oname, o in outcomes.items():
        for s in o["skills"]:
            outcome_of.setdefault(s, []).append(oname)
    home_of = {s["name"]: s["packs"][0] for s in skills if s["packs"]}
    loop_by_name = {l["name"]: l for l in loops()}
    rels = releases()
    out = {"packs/index.html": index_page(packs, outcomes, home_of),
           "loops/index.html": loops_index(list(loop_by_name.values())),
           "404.html": not_found_page(),
           "changelog/index.html": changelog_page(rels),
           "changelog/feed.xml": feed(rels),
           "evals/index.html": evals_page(skills),
           "skills/index.html": '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../catalogue/">'
                                '<link rel="canonical" href="' + SITE_URL + 'catalogue/"><a href="../catalogue/">All skills</a>\n'}
    # Renamed packs: the old URL redirects, so links shared before the rename still land.
    for old, new in {"claude-api": "api-builder"}.items():
        out[f"packs/{old}/index.html"] = (f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../{new}/">'
                                          f'<link rel="canonical" href="{SITE_URL}packs/{new}/"><a href="../{new}/">{new}</a>\n')
    for name, pack in packs.items():
        out[f"packs/{name}/index.html"] = pack_page(name, pack, packs, by_name, loop_by_name, outcome_of)
    out["packs/compare/index.html"] = compare_page(packs, by_name, loop_by_name, outcome_of)
    out["start/index.html"] = start_page(packs, loop_by_name)
    for s in skills:
        out[f"skills/{s['name']}/index.html"] = skill_page(s, by_name, packs, outcome_of)
        for f, _, text in live_examples(s["name"]):
            out[f"skills/{s['name']}/examples/{f}"] = text
    for lp in loop_by_name.values():
        out[f"loops/{lp['name']}/index.html"] = loop_page(lp, by_name)
    for i, r in enumerate(rels):
        out[f"changelog/{r['version']}/index.html"] = release_page(rels, i)
    out["search.json"] = json.dumps(search_index(skills, packs, list(loop_by_name.values())),
                                    ensure_ascii=False, separators=(",", ":")) + "\n"
    return out


def main():
    ap = argparse.ArgumentParser(description="Generate the pack, skill and changelog pages.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="build root directory (default: build/)")
    args = ap.parse_args()
    pages = render()
    for rel, body in pages.items():
        p = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    print(f"wrote {len(pages) - 1} pages (packs, skills, changelog, 404) and search.json under {args.out}")


if __name__ == "__main__":
    main()

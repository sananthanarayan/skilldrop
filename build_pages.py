#!/usr/bin/env python3
"""build_pages.py — the site's generated inner pages (RFC-0032, RFC-0035).

  build/packs/index.html          every pack, grouped by the outcome it serves
  build/packs/<pack>/index.html   one pack: at a glance, one install command, what to try first
  build/skills/<skill>/index.html one skill: what it makes, a prompt to try, its quality bar
  build/skills/index.html         redirect to the searchable catalogue
  build/changelog/index.html      every release, rendered from CHANGELOG.md
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
from build_site import (collect, card, esc, loops, site_nav, example_parts, head_meta, ld, breadcrumbs_ld,
                        NAV_CSS, REPO_URL, SITE_URL)
from build_catalogue import CSS

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGE_CSS = """
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
<meta name="theme-color" content="#ffffff">
<style>
{CSS}{NAV_CSS}{PAGE_CSS}</style>
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
<div><dt>Size</dt><dd>{size}</dd></div>
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

    parts = ['<main class="inner pk" id="main">',
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

    if own_loops:
        items = "".join(
            f"""<li><a href="../../loops/{esc(l['name'])}/"><b>{esc(l['name'])}</b></a> — {esc(l['description'].split(' Use when')[0])}
<div class="pk__stages">{' → '.join(esc(st['id']) + (f" [{esc(st['gate']['id'])}]" if st['gate'] else '') for st in l['stages'])}</div></li>"""
            for l in own_loops)
        parts.append(f'<h2>Loops</h2><ul class="pk__loops">{items}</ul>')

    cards = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(pack["skills"]) if s in by_name)
    parts.append(f'<h2>Skills in this pack ({len(pack["skills"])})</h2><ul class="skills">{cards}</ul>')
    for r in reqs:
        rc = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(packs[r]["skills"]) if s in by_name)
        parts.append(f'<h2>Included from <a href="../{esc(r)}/">{esc(r)}</a> ({len(packs[r]["skills"])})</h2><ul class="skills">{rc}</ul>')
    parts.append("</main>")
    crumbs = breadcrumbs_ld([("skilldrop", SITE_URL), ("Packs", f"{SITE_URL}packs/"), (title, f"{SITE_URL}packs/{name}/")])
    return shell(title, pack["description"], f"{SITE_URL}packs/{name}/", 2, "\n".join(parts),
                 current="packs/", extra_head=crumbs)


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
{f'<p><b>Start here:</b> {esc(p["first-value"]["starter-task"])}</p>' if p.get('first-value') else ''}</li>"""
        for n, p in packs.items())
    body = f"""<main class="inner pk" id="main">
<h1 class="pk__title">Packs</h1>
<p class="pk__lede">Start from the job in front of you. Each pack installs with one command, and every role pack brings <a href="core/">core</a> with it. The number beside a pack is how many of that job's skills it holds.</p>
{''.join(groups)}
<h2>Every pack</h2>
<ul class="pk__list">{items}</ul>
</main>"""
    return shell("Packs", "Every skilldrop pack, grouped by the job it does, with what to try first.",
                 f"{SITE_URL}packs/", 1, body, current="packs/")


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
    parts = ['<main class="inner pk" id="main">',
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
    ex = example_parts(name)
    if ex:
        ex_title, ex_in, ex_out, ex_note, ex_rel = ex
        parts.append(f"""<section aria-labelledby="example"><h2 id="example">Example output</h2>
<p class="pk__total">{esc(ex_title.replace('Worked example — ', ''))} · the skill's own worked example, <a href="{REPO_URL}/blob/main/{esc(ex_rel)}">source</a></p>
{f'<div class="pk__ex"><div class="pk__exlabel">Input</div><div class="pk__exbody">{render_md(ex_in, src=ex_rel)}</div></div>' if ex_in else ''}
<div class="pk__ex"><div class="pk__exlabel">{'Output' if ex_in else 'Worked example'}</div><div class="pk__exbody">{render_md(ex_out, src=ex_rel)}</div></div>
{f'<div class="pk__exnote">{render_md(ex_note, src=ex_rel)}</div>' if ex_note else ''}
</section>""")
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
                  "description": s["description"], "url": url,
                  "codeRepository": f"{REPO_URL}/tree/main/{s['path']}", "license": "https://opensource.org/licenses/MIT",
                  "version": s["version"], "isPartOf": {"@type": "Collection", "name": f"skilldrop {home} pack",
                                                        "url": f"{SITE_URL}packs/{home}/"}}))
    return shell(name, s["description"], url, 2, "\n".join(parts), current="catalogue/", extra_head=meta)


def changelog_page():
    """CHANGELOG.md, every release. Wrapped bullet lines are joined first, because the docs
    renderer treats each source line as its own block."""
    lines, out = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read().splitlines(), []
    for line in lines:
        if line.startswith("  ") and line.strip() and out and out[-1].startswith("- "):
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    text = "\n".join(out)
    # The file's own intro is for maintainers (format rules); the page starts at the releases.
    text = text[text.index("\n## ") + 1:] if "\n## " in text else text
    body = (f'<main class="inner pk cl" id="main"><h1 class="pk__title">What\'s new</h1>'
            f'{render_md(text, src="CHANGELOG.md", docs_base="../docs/")}</main>')
    return shell("What's new", "Every skilldrop release and what it lets you do.",
                 f"{SITE_URL}changelog/", 1, body, current="changelog/")


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
    parts = ['<main class="inner pk" id="main">',
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
<p class="pk__lede">A loop runs skills in order and stops at a gate before anything moves on. The cheaper the mistake, the more a script decides; the harder it is to undo, the more it waits for you. Five cover the lifecycle; <code>ship-a-draft</code> wraps any generator. <a href="../docs/explanation/loops.html">Why loops</a>.</p>
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
    out = {"packs/index.html": index_page(packs, outcomes, home_of),
           "loops/index.html": loops_index(list(loop_by_name.values())),
           "404.html": not_found_page(),
           "changelog/index.html": changelog_page(),
           "skills/index.html": '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../catalogue/">'
                                '<link rel="canonical" href="' + SITE_URL + 'catalogue/"><a href="../catalogue/">All skills</a>\n'}
    for name, pack in packs.items():
        out[f"packs/{name}/index.html"] = pack_page(name, pack, packs, by_name, loop_by_name, outcome_of)
    for s in skills:
        out[f"skills/{s['name']}/index.html"] = skill_page(s, by_name, packs, outcome_of)
    for lp in loop_by_name.values():
        out[f"loops/{lp['name']}/index.html"] = loop_page(lp, by_name)
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

#!/usr/bin/env python3
"""build_pages.py — the site's generated inner pages (RFC-0032, RFC-0035).

  build/packs/index.html          every pack, grouped by the outcome it serves
  build/packs/<pack>/index.html   one pack: at a glance, one install command, what to try first
  build/skills/<skill>/index.html one skill: what it makes, a prompt to try, its quality bar
  build/skills/index.html         redirect to the searchable catalogue
  build/changelog/index.html      every release, rendered from CHANGELOG.md

Everything comes from pack.json, the skill manifests and SKILL.md files, loop.json and
CHANGELOG.md, read through the same collect() the home page uses, so an inner page cannot
disagree with the catalogue. Every page carries the shared nav (build_site.site_nav).

Usage:
  python3 build_pages.py [--out build]
"""
import argparse
import json
import os
import re

import catalog
from build_docs import render_md
from build_site import collect, card, esc, loops, site_nav, NAV_CSS, REPO_URL, SITE_URL
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
.pk code { font:.86em var(--mono); background:var(--card); border:1px solid var(--border); border-radius:4px; padding:0 .3em; }
.cl h2 { margin:2.2rem 0 .4rem; }
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


def shell(title, desc, canonical, depth, body, current=None):
    root = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — skilldrop</title>
<meta name="description" content="{esc(desc[:200])}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#111113">
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

    parts = ['<main class="inner pk">',
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
            f"""<li><a href="{REPO_URL}/blob/main/{esc(l['path'])}/LOOP.md"><b>{esc(l['name'])}</b></a> — {esc(l['description'].split(' Use when')[0])}
<div class="pk__stages">{' → '.join(esc(st['id']) + (f" [{esc(st['gate']['id'])}]" if st['gate'] else '') for st in l['stages'])}</div></li>"""
            for l in own_loops)
        parts.append(f'<h2>Loops</h2><ul class="pk__loops">{items}</ul>')

    cards = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(pack["skills"]) if s in by_name)
    parts.append(f'<h2>Skills in this pack ({len(pack["skills"])})</h2><ul class="skills">{cards}</ul>')
    for r in reqs:
        rc = "\n".join(card(by_name[s], root="../../", show_pack=False) for s in sorted(packs[r]["skills"]) if s in by_name)
        parts.append(f'<h2>Included from <a href="../{esc(r)}/">{esc(r)}</a> ({len(packs[r]["skills"])})</h2><ul class="skills">{rc}</ul>')
    parts.append("</main>")
    return shell(title, pack["description"], f"{SITE_URL}packs/{name}/", 2, "\n".join(parts), current="packs/")


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
    body = f"""<main class="inner pk">
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
    parts = ['<main class="inner pk">',
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
    hand = manifest.get("handoff") or []
    if hand:
        parts.append("<h2>Hands off to</h2><ul>" + "".join(
            f"<li>{rel(h['to'])} — when {esc(h['when'])}. {esc(h['purpose'])}</li>" for h in hand) + "</ul>")
    related = [r for r in s.get("related", []) if r not in {h["to"] for h in hand}]
    if related:
        parts.append(f"<h2>Related skills</h2><p>{', '.join(rel(r) for r in related)}</p>")
    parts.append(f'<h2>Source</h2><p><a href="{REPO_URL}/blob/main/{esc(s["path"])}/SKILL.md">SKILL.md</a> · '
                 f'<a href="{REPO_URL}/tree/main/{esc(s["path"])}">the whole folder</a> on GitHub.</p></main>')
    return shell(name, s["description"], f"{SITE_URL}skills/{name}/", 2, "\n".join(parts), current="catalogue/")


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
    body = (f'<main class="inner pk cl"><h1 class="pk__title">What\'s new</h1>'
            f'{render_md(text, src="CHANGELOG.md", docs_base="../docs/")}</main>')
    return shell("What's new", "Every skilldrop release and what it lets you do.",
                 f"{SITE_URL}changelog/", 1, body, current="changelog/")


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
           "changelog/index.html": changelog_page(),
           "skills/index.html": '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../catalogue/">'
                                '<link rel="canonical" href="' + SITE_URL + 'catalogue/"><a href="../catalogue/">All skills</a>\n'}
    for name, pack in packs.items():
        out[f"packs/{name}/index.html"] = pack_page(name, pack, packs, by_name, loop_by_name, outcome_of)
    for s in skills:
        out[f"skills/{s['name']}/index.html"] = skill_page(s, by_name, packs, outcome_of)
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
    print(f"wrote {len(pages)} pages (packs, skills, changelog) under {args.out}")


if __name__ == "__main__":
    main()

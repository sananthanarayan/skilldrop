#!/usr/bin/env python3
"""build_packs.py — one landing page per pack, plus an index (RFC-0032 parts 1–2).

A pack page answers what a new user asks right after installing: what do I try first, how
do I know it worked, and what if it didn't. Everything on it comes from packs.json (the
`first-value` block), the skill manifests, and loop.json, through the same collect() the
main site uses, so a pack page cannot disagree with the catalogue it links back to.

Outputs:
  build/packs/index.html
  build/packs/<name>/index.html

Usage:
  python3 build_packs.py [--out build]
"""
import argparse
import json
import os
import re

from build_site import collect, card, esc, loops, REPO_URL, SITE_URL
from build_catalogue import CSS

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGE_CSS = """
.pk { padding-block:2.4rem 3.5rem; }
.pk h2 { font-size:1.15rem; margin:2.4rem 0 .7rem; letter-spacing:-.01em; }
.pk__lede { font-size:1.05rem; color:var(--fg-muted); max-width:46rem; margin:.2rem 0 1.4rem; }
.pk__req { font-size:.9rem; color:var(--fg-muted); }
.pk pre, .pk__cmd {
  font:.88rem/1.55 var(--mono); background:var(--card); border:1px solid var(--border);
  border-radius:var(--r-sm); padding:.8rem 1rem; white-space:pre-wrap; margin:.4rem 0;
}
.pk__start { background:var(--accent-10); border-radius:var(--r); padding:1.1rem 1.3rem 1.2rem; }
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
.pk code { font:.86em var(--mono); background:var(--card); border:1px solid var(--border); border-radius:4px; padding:0 .3em; }
"""


def md(text):
    """Escape, then render `code` spans — the first-value strings carry shell commands."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


def shell(title, desc, canonical, depth, body):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — skilldrop</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#111113">
<style>
{CSS}{PAGE_CSS}</style>
</head>
<body>
<header class="page-head">
  <a class="page-head__back" href="{up}">&#8592; skilldrop</a>
  <h1 class="page-head__title">{esc(title)}</h1>
  <a class="page-head__count" href="{up}catalogue/">all skills &#8594;</a>
</header>
{body}
</body>
</html>
"""


def pack_page(name, pack, packs, by_name, loop_by_name):
    title = pack.get("display_name", name)
    reqs = pack.get("requires", [])
    fv = pack.get("first-value")

    install = [f"npx skilldrop-cli install --pack {name}"]
    if pack.get("loops") or any(packs[r].get("loops") for r in reqs):
        install.append(f"npx skilldrop-cli install --loop --pack {name}")
    install.append(f"/plugin install {name}@skilldrop   # in Claude Code, after: /plugin marketplace add sananthanarayan/skilldrop")
    parts = [f'<main class="inner pk">',
             f'<p class="pk__lede">{esc(pack["description"])}</p>',
             '<div class="pk__cmd">' + "<br>".join(esc(c) for c in install) + "</div>"]
    if reqs:
        links = ", ".join(f'<a href="../{esc(r)}/">{esc(r)}</a>' for r in reqs)
        parts.append(f'<p class="pk__req">Installs together with {links}, which holds the skills every role uses.</p>')

    if fv:
        pre = "".join(f"<li>{md(p)}</li>" for p in fv["prerequisites"])
        parts.append(f"""<section class="pk__start" aria-labelledby="start">
<h2 id="start">Start here: {esc(fv['starter-task'])}</h2>
<p>Paste this into your agent:</p>
<pre>{esc(fv['starter-prompt'])}</pre>
<dl>
{f'<dt>Before you start</dt><dd><ul>{pre}</ul></dd>' if pre else ''}
<dt>How to tell it worked</dt><dd>{md(fv['verification'])}</dd>
<dt>If nothing happens</dt><dd>{md(fv['recovery'])}</dd>
</dl>
</section>""")

    own_loops = [loop_by_name[l] for l in pack.get("loops", []) if l in loop_by_name]
    if own_loops:
        items = "".join(
            f"""<li><a href="{REPO_URL}/blob/main/loops/{esc(l['name'])}/LOOP.md"><b>{esc(l['name'])}</b></a> — {esc(l['description'].split(' Use when')[0])}
<div class="pk__stages">{' → '.join(esc(st['id']) + (f" [{esc(st['gate']['id'])}]" if st['gate'] else '') for st in l['stages'])}</div></li>"""
            for l in own_loops)
        parts.append(f'<h2>Loops</h2><ul class="pk__loops">{items}</ul>')

    cards = "\n".join(card(by_name[s]) for s in sorted(pack["skills"]) if s in by_name)
    parts.append(f'<h2>Skills in this pack ({len(pack["skills"])})</h2><ul class="skills">{cards}</ul>')
    for r in reqs:
        rc = "\n".join(card(by_name[s]) for s in sorted(packs[r]["skills"]) if s in by_name)
        parts.append(f'<h2>Included from <a href="../{esc(r)}/">{esc(r)}</a> ({len(packs[r]["skills"])})</h2><ul class="skills">{rc}</ul>')
    parts.append("</main>")
    return shell(title, pack["description"], f"{SITE_URL}packs/{name}/", 2, "\n".join(parts))


def index_page(packs):
    items = "".join(
        f"""<li><a href="{esc(n)}/">{esc(p.get('display_name', n))}</a>
<p>{esc(p['description'])}</p>
{f'<p><b>Start here:</b> {esc(p["first-value"]["starter-task"])}</p>' if p.get('first-value') else ''}</li>"""
        for n, p in packs.items())
    body = f"""<main class="inner pk">
<p class="pk__lede">Pick the pack for your role. Each one installs with one command, and every role pack brings <a href="core/">core</a> with it.</p>
<ul class="pk__list">{items}</ul>
</main>"""
    return shell("Packs", "Every skilldrop pack, what it is for, and what to try first.", f"{SITE_URL}packs/", 1, body)


def render():
    """Return {relative_path: html} for every pack page."""
    skills, _, _ = collect()
    by_name = {s["name"]: s for s in skills}
    packs = json.load(open(os.path.join(ROOT, "packs.json"), encoding="utf-8"))["packs"]
    loop_by_name = {l["name"]: l for l in loops()}
    out = {"packs/index.html": index_page(packs)}
    for name, pack in packs.items():
        out[f"packs/{name}/index.html"] = pack_page(name, pack, packs, by_name, loop_by_name)
    return out


def main():
    ap = argparse.ArgumentParser(description="Generate the per-pack pages.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="build root directory (default: build/)")
    args = ap.parse_args()
    pages = render()
    for rel, body in pages.items():
        p = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    print(f"wrote {len(pages)} pack pages under {os.path.join(args.out, 'packs')}")


if __name__ == "__main__":
    main()

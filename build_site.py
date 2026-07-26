#!/usr/bin/env python3
"""Catalogue site generator for skilldrop. No deps, no network. Run from the repo root:

    python3 build_site.py              # writes build/index.html + build/catalogue.json
    python3 build_site.py --out <dir>  # write somewhere else
    python3 build_site.py --check      # exit 1 if build/ is stale vs the manifests

Every fact on the page comes from skills/<name>/manifest.json, packs.json, or
model-routing.json. Nothing is hand-typed here except the page shell — a description
typed into this file would be a fourth copy of a string validate.py already keeps in
sync across two (RFC-0011).

The page is one self-contained file: CSS and JS inline, no external requests, no
absolute paths. That is what makes it work unchanged at a project-pages base path
(/skilldrop/), which is the most common way a GitHub Pages site breaks.
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
    packs = "".join(f'<span class="pill pack">{esc(p)}</span>' for p in s["packs"])
    tags = "".join(f'<span class="pill tag">{esc(t)}</span>' for t in s["tags"])
    related = "".join(
        f'<a class="rel" href="#{esc(r)}">{esc(r)}</a>' for r in s["related"]
    )
    flags = ""
    if s["deps"]:
        flags += '<span class="pill flag">deps</span>'
    for e in s["env"]:
        flags += f'<span class="pill flag">env: {esc(e)}</span>'
    for h in s["hooks"]:
        flags += f'<span class="pill flag">hook: {esc(h)}</span>'
    return f"""<article class="card" id="{esc(s['name'])}"
   data-name="{esc(s['name'])}" data-tier="{esc(tier)}"
   data-packs="{esc(' '.join(s['packs']))}" data-tags="{esc(' '.join(s['tags']))}"
   data-text="{esc((s['name'] + ' ' + s['description'] + ' ' + ' '.join(s['tags'])).lower())}">
  <header>
    <h3><a href="{REPO_URL}/blob/main/skills/{esc(s['name'])}/SKILL.md">{esc(s['name'])}</a></h3>
    <span class="tier tier-{esc(tier)}" title="{esc(s['rationale'])}">{esc(tier)}</span>
  </header>
  <p>{esc(s['description'])}</p>
  <div class="meta">{packs}{flags}</div>
  <div class="meta tags">{tags}</div>
  {f'<div class="meta rels"><span class="lbl">pairs with</span>{related}</div>' if related else ''}
</article>"""


def render(skills, packs):
    tiers = ["light", "standard", "heavy"]
    tier_counts = {t: sum(1 for s in skills if s["tier"] == t) for t in tiers}
    pack_buttons = "".join(
        f'<button class="chip" data-filter="pack" data-value="{esc(p["name"])}" '
        f'title="{esc(p["description"])}">{esc(p["name"])} <b>{p["count"]}</b></button>'
        for p in packs
    )
    tier_buttons = "".join(
        f'<button class="chip tier-{t}" data-filter="tier" data-value="{t}">{t} <b>{tier_counts[t]}</b></button>'
        for t in tiers
    )
    cards = "\n".join(card(s) for s in skills)
    all_tags = sorted({t for s in skills for t in s["tags"]})

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skilldrop — portable skills for agentic IDEs</title>
<meta name="description" content="{len(skills)} portable Claude Skills for the deliverables knowledge workers ship. Copy a folder into Claude Code, Cursor, Kiro, Codex, or Copilot.">
<style>
:root {{
  --bg:#fbfbfa; --fg:#1a1a19; --muted:#6b6b68; --line:#e3e3df; --card:#fff;
  --accent:#3b5bdb; --light:#0b7285; --standard:#5f3dc4; --heavy:#c2255c;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#141413; --fg:#ecebe8; --muted:#9b9b96; --line:#2c2c2a; --card:#1c1c1a;
    --accent:#748ffc; --light:#3bc9db; --standard:#b197fc; --heavy:#f783ac;
  }}
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.55 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;
}}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 20px; }}
header.top {{ border-bottom:1px solid var(--line); padding:44px 0 30px; }}
h1 {{ margin:0 0 8px; font-size:2rem; letter-spacing:-.02em; }}
h1 span {{ color:var(--muted); font-weight:400; }}
.lede {{ margin:0 0 20px; max-width:62ch; color:var(--muted); }}
code.cmd {{
  display:inline-block; background:var(--card); border:1px solid var(--line);
  border-radius:6px; padding:7px 11px; font-size:.86rem;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
}}
.controls {{ position:sticky; top:0; z-index:5; background:var(--bg);
  border-bottom:1px solid var(--line); padding:14px 0; }}
#q {{
  width:100%; padding:10px 13px; font-size:1rem; color:var(--fg);
  background:var(--card); border:1px solid var(--line); border-radius:8px;
}}
#q:focus {{ outline:2px solid var(--accent); outline-offset:1px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:11px; align-items:center; }}
.chip {{
  cursor:pointer; font:inherit; font-size:.8rem; color:var(--fg);
  background:var(--card); border:1px solid var(--line);
  border-radius:999px; padding:5px 11px;
}}
.chip b {{ color:var(--muted); font-weight:600; margin-left:3px; }}
.chip[aria-pressed="true"] {{ background:var(--accent); border-color:var(--accent); color:#fff; }}
.chip[aria-pressed="true"] b {{ color:#fff; opacity:.75; }}
.lbl {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-right:5px; }}
#count {{ font-size:.82rem; color:var(--muted); margin-left:auto; }}
.grid {{ display:grid; gap:14px; padding:24px 0 60px;
  grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 17px; }}
.card:target {{ outline:2px solid var(--accent); }}
.card header {{ display:flex; gap:10px; align-items:baseline; margin-bottom:7px; }}
.card h3 {{ margin:0; font-size:1rem; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
.card h3 a {{ color:var(--fg); text-decoration:none; }}
.card h3 a:hover {{ color:var(--accent); text-decoration:underline; }}
.card p {{ margin:0 0 11px; font-size:.88rem; color:var(--muted); }}
.tier {{ margin-left:auto; font-size:.68rem; text-transform:uppercase;
  letter-spacing:.06em; padding:2px 7px; border-radius:4px; color:#fff; white-space:nowrap; }}
.tier-light {{ background:var(--light); }} .tier-standard {{ background:var(--standard); }}
.tier-heavy {{ background:var(--heavy); }}
.chip.tier-light b, .chip.tier-standard b, .chip.tier-heavy b {{ color:var(--muted); }}
.meta {{ display:flex; flex-wrap:wrap; gap:5px; align-items:center; }}
.meta.tags, .meta.rels {{ margin-top:7px; }}
.pill {{ font-size:.7rem; padding:2px 7px; border-radius:4px; border:1px solid var(--line); color:var(--muted); }}
.pill.pack {{ border-color:var(--accent); color:var(--accent); }}
.rel {{ font-size:.72rem; color:var(--accent); text-decoration:none;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
.rel:hover {{ text-decoration:underline; }}
.empty {{ padding:50px 0; text-align:center; color:var(--muted); }}
footer {{ border-top:1px solid var(--line); padding:26px 0 50px; font-size:.83rem; color:var(--muted); }}
footer a {{ color:var(--accent); }}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>skilldrop <span>— {len(skills)} portable skills for agentic IDEs</span></h1>
  <p class="lede">Each skill is a plain folder: <code>SKILL.md</code> + <code>manifest.json</code>.
  Install by copying it into Claude Code, Cursor, Kiro, Codex, or Copilot — no runtime,
  no lock-in, no transformation on the way in.</p>
  <code class="cmd">npx skilldrop-cli install &lt;skill&gt;</code>
  &nbsp;<code class="cmd">npx skilldrop-cli install --pack dev-team</code>
</div></header>

<div class="controls"><div class="wrap">
  <input id="q" type="search" placeholder="Search {len(skills)} skills — name, description, tag…" autocomplete="off">
  <div class="chips"><span class="lbl">pack</span>{pack_buttons}</div>
  <div class="chips"><span class="lbl">tier</span>{tier_buttons}
    <button class="chip" id="clear">clear</button><span id="count"></span></div>
</div></div>

<main class="wrap"><div class="grid" id="grid">
{cards}
</div><p class="empty" id="empty" hidden>No skill matches those filters.</p></main>

<footer><div class="wrap">
  Generated from {len(skills)} <code>manifest.json</code> files by
  <a href="{REPO_URL}/blob/main/build_site.py">build_site.py</a> — never hand-edited.
  · <a href="{REPO_URL}">Repository</a>
  · <a href="{REPO_URL}/blob/main/CONTRIBUTING.md">Contributing</a>
  · <a href="{REPO_URL}/tree/main/docs/rfcs">RFCs</a>
  · <a href="catalogue.json">catalogue.json</a>
</div></footer>

<script>
(function () {{
  var q = document.getElementById('q'), grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.children);
  var count = document.getElementById('count'), empty = document.getElementById('empty');
  var active = {{ pack: null, tier: null }};

  function apply() {{
    var text = q.value.trim().toLowerCase();
    var shown = 0;
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

  document.querySelectorAll('.chip[data-filter]').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var kind = b.dataset.filter, val = b.dataset.value;
      active[kind] = active[kind] === val ? null : val;
      document.querySelectorAll('.chip[data-filter="' + kind + '"]').forEach(function (o) {{
        o.setAttribute('aria-pressed', String(o.dataset.value === active[kind]));
      }});
      apply();
    }});
  }});

  document.getElementById('clear').addEventListener('click', function () {{
    active = {{ pack: null, tier: null }}; q.value = '';
    document.querySelectorAll('.chip[data-filter]').forEach(function (o) {{
      o.setAttribute('aria-pressed', 'false');
    }});
    apply();
  }});

  q.addEventListener('input', apply);
  apply();
}})();
</script>
</body>
</html>
"""


def build(out_dir):
    skills, packs = collect()
    os.makedirs(out_dir, exist_ok=True)
    page = render(skills, packs)
    index = {
        "site": SITE_URL,
        "repo": REPO_URL,
        "packs": packs,
        "skills": skills,
    }
    files = {
        os.path.join(out_dir, "index.html"): page,
        os.path.join(out_dir, "catalogue.json"): json.dumps(index, indent=2) + "\n",
    }
    for path, body in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    return skills, files


def main():
    ap = argparse.ArgumentParser(description="Generate the skilldrop catalogue site.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"), help="output directory (default: build/)")
    ap.add_argument("--check", action="store_true", help="exit 1 if the output would differ from what is on disk")
    args = ap.parse_args()

    if args.check:
        skills, packs = collect()
        stale = []
        for name, body in (("index.html", render(skills, packs)),
                           ("catalogue.json", json.dumps(
                               {"site": SITE_URL, "repo": REPO_URL, "packs": packs, "skills": skills},
                               indent=2) + "\n")):
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

    skills, files = build(args.out)
    for p in sorted(files):
        print(f"wrote {os.path.relpath(p, ROOT)}")
    print(f"\n{len(skills)} skills rendered. Preview: python3 -m http.server -d {os.path.relpath(args.out, ROOT)}")


if __name__ == "__main__":
    main()

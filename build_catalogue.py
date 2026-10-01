#!/usr/bin/env python3
"""Standalone catalogue page generator for skilldrop. No deps, no network.

    python3 build_catalogue.py              # writes build/catalogue/index.html
    python3 build_catalogue.py --out <dir>  # write somewhere else

The page renders every skill with the same filter/search controls as the main
site, but shows all skills by default (no "show N more" fold). run after
build_site.py so build/ exists.
"""
import argparse
import html
import json
import os
import sys

# Reuse the data layer from build_site — collect(), card(), esc(), and the
# constants are all defined there and kept authoritative.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import collect, card, esc, site_nav, head_meta, breadcrumbs_ld, NAV_CSS, REPO_URL, SITE_URL

ROOT = os.path.dirname(os.path.abspath(__file__))


# Shared with build_pages.py, so the per-pack pages look like the catalogue they link to.
CSS = """:root {
  --dark-950:#0d0d0f; --dark-900:#141417;
  --n-50:#fafaf9; --n-100:#f3f3f1; --n-200:#e4e4e0; --n-600:#6a6a66; --n-900:#17171a;
  --accent:#7c5cff; --accent-300:#a48cff; --accent-700:#4c31d6; --accent-10:rgba(124,92,255,.10);
  --w-06:rgba(255,255,255,.06); --w-10:rgba(255,255,255,.10);
  --w-20:rgba(255,255,255,.20); --w-60:rgba(255,255,255,.60); --w-80:rgba(255,255,255,.80);
  --surface:var(--n-50); --surface-alt:var(--n-100); --fg:var(--n-900);
  --fg-muted:var(--n-600); --border:var(--n-200); --card:#fff;
  --h2:clamp(1.7rem,3.2vw,2.5rem);
  --gap:clamp(4.5rem,9vw,7.5rem); --pad-x:clamp(1.25rem,5vw,2.5rem); --max:1140px;
  --r-sm:5px; --r:10px; --r-lg:16px;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --surface:#111113; --surface-alt:#17171a; --fg:#ecebe8; --fg-muted:#9a9a95;
    --border:#2a2a2d; --card:#1a1a1d; --accent:#a48cff; --accent-700:#c4b5ff;
    --accent-10:rgba(164,140,255,.12);
  }
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  margin:0; background:var(--surface); color:var(--fg);
  font:400 1rem/1.65 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.visually-hidden {
  position:absolute; width:1px; height:1px; margin:-1px; padding:0;
  overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0;
}
.inner { max-width:var(--max); margin:0 auto; padding-inline:var(--pad-x); }
a { color:var(--accent-700); }

/* page header — sits under the shared dark nav, so it is light */
.page-head {
  max-width:var(--max); margin:0 auto; padding:1.6rem var(--pad-x) .2rem;
  display:flex; align-items:baseline; gap:1.2rem;
}
.page-head__title { margin:0; font-size:clamp(1.5rem,3vw,2rem); letter-spacing:-.02em; color:var(--fg); }
.page-head__count { margin-left:auto; font-size:.85rem; color:var(--fg-muted); white-space:nowrap; }

/* controls */
.controls-wrap {
  position:sticky; top:0; z-index:10;
  background:var(--surface); border-bottom:1px solid var(--border);
  padding:.9rem var(--pad-x) .7rem;
}
.controls-inner { max-width:var(--max); margin:0 auto; }
#q {
  width:100%; padding:.7rem .9rem; font-size:1rem; color:var(--fg); background:var(--card);
  border:1px solid var(--border); border-radius:var(--r-sm);
}
#q:focus { outline:2px solid var(--accent); outline-offset:1px; }
.chips { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.7rem; align-items:center; }
.chip {
  cursor:pointer; font:inherit; font-size:.79rem; color:var(--fg); background:var(--card);
  border:1px solid var(--border); border-radius:999px; padding:.3rem .75rem;
}
.chip b { color:var(--fg-muted); font-weight:600; margin-left:.2rem; }
.chip[aria-pressed=true] { background:var(--accent); border-color:var(--accent); color:#0d0d0f; }
.chip[aria-pressed=true] b { color:#0d0d0f; opacity:.7; }
.chips__lbl { font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:var(--fg-muted); }
#count { font-size:.8rem; color:var(--fg-muted); margin-left:auto; }

/* skill list */
.skills { list-style:none; margin:0; padding:0; border-top:1px solid var(--border); }
.skill { display:flex; align-items:center; gap:1rem; border-bottom:1px solid var(--border); }
.skill:target { background:var(--accent-10); }
.skill__link {
  flex:1; min-width:0; display:flex; align-items:baseline; gap:.9rem;
  padding:.7rem var(--pad-x); text-decoration:none; color:inherit;
}
.skill__link:hover { background:var(--surface-alt); }
.skill__link:hover .skill__name { color:var(--accent-700); }
.skill__name { font:.9rem var(--mono); letter-spacing:-.01em; flex:0 0 15.5rem; }
.skill__pack {
  flex:0 0 auto; font:.7rem var(--mono); color:var(--fg-muted); text-decoration:none;
  border:1px solid var(--border); border-radius:999px; padding:1px 8px; white-space:nowrap;
}
.skill__pack:hover { color:var(--accent-700); border-color:var(--accent-700); }
.skill__desc {
  flex:1; min-width:0; font-size:.85rem; color:var(--fg-muted);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.tier {
  flex:0 0 auto; margin-right:var(--pad-x); font-size:.62rem; text-transform:uppercase;
  letter-spacing:.07em; padding:2px 7px; border-radius:3px; white-space:nowrap;
  border:1px solid var(--border); color:var(--fg-muted);
}
.tier--heavy { background:var(--accent); border-color:var(--accent); color:#0d0d0f; }
.tier--standard { background:var(--accent-10); border-color:transparent; color:var(--accent-700); }
@media (max-width:640px) {
  .skill__link { flex-direction:column; gap:.2rem; }
  .skill__name { flex:none; }
  .skill__desc { white-space:normal; }
}
.empty { padding:4rem var(--pad-x); text-align:center; color:var(--fg-muted); }
"""


def render_catalogue(skills, packs, outcomes):
    tiers = ["light", "standard", "heavy"]
    tier_counts = {t: sum(1 for s in skills if s["tier"] == t) for t in tiers}

    pack_chips = "".join(
        f'<button class="chip" data-filter="pack" data-value="{esc(p["name"])}">'
        f'{esc(p["name"])} <b>{p["count"]}</b></button>'
        for p in packs)
    tier_chips = "".join(
        f'<button class="chip chip--{t}" data-filter="tier" data-value="{t}">'
        f'{t} <b>{tier_counts[t]}</b></button>'
        for t in tiers)
    outcome_chips = "".join(
        f'<button class="chip" data-filter="outcome" data-value="{esc(o["name"])}" '
        f'title="{esc(o["description"])}">{esc(o["name"].replace("-", " "))} '
        f'<b>{o["count"]}</b></button>'
        for o in outcomes)

    cards = "\n".join(card(s, root="../") for s in skills)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All skills — skilldrop</title>
{head_meta("All skills — skilldrop", "Search and filter every skilldrop skill by the job it does, the pack it is in, or its model tier.", SITE_URL + "catalogue/")}
{breadcrumbs_ld([("skilldrop", SITE_URL), ("Skills", SITE_URL + "catalogue/")])}
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#111113">
<style>
{CSS}{NAV_CSS}</style>
</head>
<body>
{site_nav("../", "catalogue/")}
<header class="page-head">
  <h1 class="page-head__title">All skills</h1>
  <span class="page-head__count">{len(skills)} skills · <a href="../packs/">browse by pack</a></span>
</header>

<div class="controls-wrap">
  <div class="controls-inner">
    <label class="visually-hidden" for="q">Search skills</label>
    <input id="q" type="search" placeholder="Search by name, description, or tag&hellip;" autocomplete="off">
    <div class="chips"><span class="chips__lbl">outcome</span>{outcome_chips}</div>
    <div class="chips"><span class="chips__lbl">pack</span>{pack_chips}</div>
    <div class="chips"><span class="chips__lbl">tier</span>{tier_chips}
      <button class="chip" id="clear">clear</button><span id="count"></span></div>
  </div>
</div>

<main id="main">
  <ul class="skills" id="grid">
{cards}
  </ul>
  <p class="empty" id="empty" hidden>No skill matches those filters.</p>
</main>

<script>
(function () {{
  var q = document.getElementById('q'), grid = document.getElementById('grid');
  var cards = Array.prototype.slice.call(grid.children);
  var count = document.getElementById('count'), empty = document.getElementById('empty');
  var KINDS = ['outcome', 'pack', 'tier'];
  var active = {{ outcome: null, pack: null, tier: null }};

  function readURL() {{
    var p = new URLSearchParams(location.search);
    var changed = false;
    KINDS.forEach(function(k) {{ if (p.get(k)) {{ active[k] = p.get(k); changed = true; }} }});
    if (p.get('q')) {{ q.value = p.get('q'); changed = true; }}
    return changed;
  }}

  function writeURL() {{
    var p = new URLSearchParams();
    KINDS.forEach(function(k) {{ if (active[k]) p.set(k, active[k]); }});
    if (q.value.trim()) p.set('q', q.value.trim());
    var s = p.toString();
    history.replaceState(null, '', s ? '?' + s : location.pathname);
  }}

  function sync() {{
    KINDS.forEach(function(k) {{
      document.querySelectorAll('[data-filter="' + k + '"]').forEach(function(b) {{
        b.setAttribute('aria-pressed', b.dataset.value === active[k] ? 'true' : 'false');
      }});
    }});
  }}

  function apply() {{
    var text = q.value.trim().toLowerCase();
    var matched = [];
    cards.forEach(function(c) {{
      var ok = (!text || c.dataset.text.indexOf(text) !== -1)
        && (!active.outcome || c.dataset.outcomes.split(' ').indexOf(active.outcome) !== -1)
        && (!active.pack || c.dataset.packs.split(' ').indexOf(active.pack) !== -1)
        && (!active.tier || c.dataset.tier === active.tier);
      if (ok) matched.push(c);
      c.hidden = !ok;
    }});
    count.textContent = matched.length + ' of ' + cards.length;
    empty.hidden = matched.length !== 0;
    writeURL();
  }}

  document.querySelectorAll('[data-filter]').forEach(function(b) {{
    b.addEventListener('click', function() {{
      var kind = b.dataset.filter, val = b.dataset.value;
      active[kind] = active[kind] === val ? null : val;
      sync(); apply();
    }});
  }});

  document.getElementById('clear').addEventListener('click', function() {{
    active = {{ outcome: null, pack: null, tier: null }}; q.value = '';
    sync(); apply();
  }});

  q.addEventListener('input', apply);
  readURL();
  sync(); apply();

  var hash = location.hash.slice(1);
  if (hash) {{
    var el = document.getElementById(hash);
    if (el) el.scrollIntoView({{ block: 'center' }});
  }}
}})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Generate the skilldrop catalogue page.")
    ap.add_argument("--out", default=os.path.join(ROOT, "build"),
                    help="build root directory (default: build/)")
    args = ap.parse_args()

    skills, packs, outcomes = collect()
    body = render_catalogue(skills, packs, outcomes)

    out_dir = os.path.join(args.out, "catalogue")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"wrote {out_path} ({len(skills)} skills)")


if __name__ == "__main__":
    main()

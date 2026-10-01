#!/usr/bin/env python3
"""Check a brand.json before anything is generated from it. Stdlib only.

Checks:
  - every colour role is a 6-digit hex code
  - text on background, and white on primary, reach WCAG AA contrast (4.5:1)
  - each logo file exists, and is PNG or JPG (PowerPoint cannot place SVG or EPS)
  - a referenced .pptx/.potx template exists
  - heading and body fonts are named

Usage:
  python3 check_brand.py path/to/brand.json
Exit code 1 if any check fails; warnings alone exit 0.
"""
import json
import re
import sys
from pathlib import Path

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
ROLES = ("primary", "secondary", "accent", "background", "text")


def luminance(hex_str):
    h = hex_str.lstrip("#")
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = Path(argv[0]).expanduser().resolve()
    base = path.parent
    try:
        brand = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL cannot read {path}: {e}")
        return 1
    fails, warns = [], []

    colors = brand.get("colors") or {}
    for role in ROLES:
        v = colors.get(role)
        if not v:
            warns.append(f"colors.{role} is missing; the generators will derive it from the others")
        elif not HEX.match(v):
            fails.append(f"colors.{role} is {v!r}, not a 6-digit hex code like #1A2A6C")
    for x in colors.get("extra") or []:
        if not HEX.match(str(x.get("hex", ""))):
            fails.append(f"colors.extra {x.get('name', '?')!r} has hex {x.get('hex')!r}")
    if HEX.match(colors.get("text", "")) and HEX.match(colors.get("background", "")):
        r = contrast(colors["text"], colors["background"])
        if r < 4.5:
            fails.append(f"text on background contrast is {r:.2f}:1, below 4.5:1")
        print(f"  text on background   {r:5.2f}:1")
    if HEX.match(colors.get("primary", "")):
        r = contrast("#FFFFFF", colors["primary"])
        msg = f"white text on primary is {r:.2f}:1"
        if r < 4.5:
            warns.append(msg + " — slide title bars and flyer bands will use dark text instead")
        print(f"  white on primary     {r:5.2f}:1")
    if HEX.match(colors.get("accent", "")) and HEX.match(colors.get("background", "")):
        r = contrast(colors["accent"], colors["background"])
        if r < 3:
            warns.append(f"accent on background is {r:.2f}:1 — use the accent for shapes and rules, not text")

    logo = brand.get("logo") or {}
    if isinstance(logo, str):
        logo = {"primary": logo}
    if not logo.get("primary") and not logo.get("on_dark"):
        warns.append("no logo file — decks and flyers will carry the brand name as text instead")
    for field in ("primary", "on_dark", "mark"):
        ref = logo.get(field)
        if not ref:
            continue
        lp = (base / ref) if not Path(ref).is_absolute() else Path(ref)
        if not lp.exists():
            fails.append(f"logo.{field} {ref!r} does not exist (looked in {lp.parent})")
        elif lp.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            warns.append(f"logo.{field} is {lp.suffix}: fine for the flyer, but PowerPoint needs PNG or JPG — export one")

    tpl = (brand.get("templates") or {}).get("pptx")
    if tpl:
        tp = (base / tpl) if not Path(tpl).is_absolute() else Path(tpl)
        if not tp.exists():
            fails.append(f"templates.pptx {tpl!r} does not exist")

    fonts = brand.get("fonts") or {}
    for role in ("heading", "body"):
        f = fonts.get(role)
        fam = f.get("family") if isinstance(f, dict) else f
        if not fam:
            warns.append(f"fonts.{role} is not set; generators fall back to their defaults")

    for w in warns:
        print(f"WARN {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"{'FAILED' if fails else 'OK'}: {path.name} — {len(fails)} failure(s), {len(warns)} warning(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

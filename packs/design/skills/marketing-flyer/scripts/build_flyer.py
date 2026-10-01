#!/usr/bin/env python3
"""Build a print-ready, on-brand flyer as one self-contained HTML file. Stdlib only.

The spec (see templates/flyer-spec.json) gives the content; a brand.json (the brand-kit
skill writes one) gives the logo, colours and fonts. Images are embedded as data URIs, so the
.html file is the whole flyer: open it and print, or save as PDF, at 100% scale.

Usage:
  python3 build_flyer.py spec.json -o flyer.html [--brand brand.json] [--pdf flyer.pdf] [--png flyer.png]

--pdf and --png use a local Chrome or Chromium in headless mode when one is installed; without
one the script says so and the HTML is still the deliverable.
"""
import argparse
import base64
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SIZES = {  # (width, height) in CSS units, portrait
    "letter": ("8.5in", "11in"), "a4": ("210mm", "297mm"), "a5": ("148mm", "210mm"),
    "square": ("1080px", "1080px"), "story": ("1080px", "1920px"),
}
PX = {"letter": (816, 1056), "a4": (794, 1123), "a5": (559, 794), "square": (1080, 1080), "story": (1080, 1920)}
LAYOUTS = ("hero", "split", "event", "minimal")
DEFAULTS = {"primary": "#1A2A6C", "secondary": "#4A5A8C", "accent": "#FDBB2D", "background": "#FFFFFF", "text": "#222222"}
WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"WARN {msg}", file=sys.stderr)


def die(msg):
    print(f"ERROR {msg}", file=sys.stderr)
    sys.exit(1)


def lum(hex_str):
    h = hex_str.lstrip("#")
    def ch(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ink_on(bg, text, light="#FFFFFF"):
    """The readable text colour on a filled band: white or the brand text colour, whichever
    contrasts more — so a pale accent gets dark text instead of illegible white."""
    return light if contrast(light, bg) >= contrast(text, bg) else text


def data_uri(path, label):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        warn(f"{label} not found: {p} — the flyer is built without it")
        return None
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if not mime.startswith("image/"):
        warn(f"{label} {p.name} is not an image ({mime})")
        return None
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"cannot read {path}: {e}")


def resolve(base, ref):
    return None if not ref else (Path(ref) if Path(ref).is_absolute() else (base / ref))


def font_stack(f, generic):
    if not f:
        return generic
    fam = f.get("family") if isinstance(f, dict) else f
    fb = (f.get("fallback") if isinstance(f, dict) else None) or generic
    return f"'{fam}', {fb}" if fam else fb


def esc(s):
    return html.escape(str(s or ""), quote=True)


def build(spec_path, out_path, brand_ref=None):
    spec_path = Path(spec_path).resolve()
    base = spec_path.parent
    spec = load_json(spec_path)

    brand, bbase = {}, base
    ref = brand_ref or spec.get("brand")
    if isinstance(ref, dict):
        brand = ref
    elif ref:
        bp = resolve(base, ref) if not brand_ref else Path(ref).resolve()
        if bp.exists():
            brand, bbase = load_json(bp), bp.parent
        else:
            warn(f"brand file not found: {bp} — using default colours and no logo")
    if not brand:
        warn("no brand supplied — the flyer uses default colours. Run brand-kit, or pass --brand")

    c = {**DEFAULTS, **{k: v for k, v in (brand.get("colors") or {}).items() if k in DEFAULTS and v},
         **{k: v for k, v in (spec.get("colors") or {}).items() if k in DEFAULTS and v}}
    for k, v in c.items():
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            die(f"colour {k} is {v!r}, not a 6-digit hex code")
    if contrast(c["text"], c["background"]) < 4.5:
        die(f"text on background contrast is {contrast(c['text'], c['background']):.2f}:1, below 4.5:1 — fix the brand colours")
    on_primary, on_accent = ink_on(c["primary"], c["text"]), ink_on(c["accent"], c["text"])
    fonts = brand.get("fonts") or {}
    head_font, body_font = font_stack(fonts.get("heading"), "Georgia, serif"), font_stack(fonts.get("body"), "Helvetica, Arial, sans-serif")

    logo = brand.get("logo") or {}
    if isinstance(logo, str):
        logo = {"primary": logo}
    logo_light = data_uri(resolve(bbase, logo.get("primary")), "logo")
    logo_dark = data_uri(resolve(bbase, logo.get("on_dark")), "on-dark logo") or logo_light
    if not logo_light and not logo_dark:
        warn("no logo — the brand name is set as text instead")
    name = brand.get("name") or spec.get("name") or ""

    size = str(spec.get("size", "letter")).lower()
    if size not in SIZES:
        warn(f"unknown size {size!r}; using letter")
        size = "letter"
    w, h = SIZES[size]
    landscape = str(spec.get("orientation", "portrait")).lower() == "landscape"
    if landscape:
        w, h = h, w
    layout = str(spec.get("layout", "hero")).lower()
    if layout not in LAYOUTS:
        warn(f"unknown layout {layout!r}; using hero")
        layout = "hero"

    headline = spec.get("headline") or die("spec needs a headline")
    if len(headline.split()) > 10:
        warn(f"headline is {len(headline.split())} words; ten or fewer read from across a room")
    points = spec.get("points") or []
    if len(points) > 4:
        warn(f"{len(points)} points; a flyer carries four at most — the rest belong on the linked page")
    body = spec.get("body") or ""
    if len(body.split()) > 60:
        warn(f"body is {len(body.split())} words; keep it under 60")
    cta = spec.get("cta")
    if isinstance(cta, list):
        warn("more than one call to action; a flyer gets one — using the first")
        cta = cta[0] if cta else None
    if not cta:
        warn("no call to action — what should a reader do next?")
    img = spec.get("image") or {}
    hero = data_uri(resolve(base, img.get("path")), "image") if isinstance(img, dict) else data_uri(resolve(base, img), "image")
    if hero and isinstance(img, dict) and not img.get("alt"):
        warn("image has no alt text")
    qr = data_uri(resolve(base, spec.get("qr")), "QR code")
    contact = {**(brand.get("contact") or {}), **(spec.get("contact") or {})}
    footer = spec.get("footer") or (brand.get("legal") or {}).get("footer") or ""
    details = spec.get("details") or []

    def logo_img(dark):
        src = logo_dark if dark else logo_light
        return f'<img class="logo" src="{src}" alt="{esc(name)}">' if src else f'<span class="wordmark">{esc(name)}</span>'

    pts = "".join(f"<li>{esc(p)}</li>" for p in points[:4])
    det = "".join(f'<div class="det"><span>{esc(d.get("label"))}</span><b>{esc(d.get("value"))}</b></div>' for d in details)
    cta_html = (f'<div class="cta"><b>{esc(cta.get("text"))}</b>'
                + (f'<span>{esc(cta.get("url"))}</span>' if cta.get("url") else "")
                + (f'<img class="qr" src="{qr}" alt="QR code for {esc(cta.get("url") or cta.get("text"))}">' if qr else "")
                + "</div>") if cta else ""
    contact_line = " · ".join(esc(v) for k, v in contact.items() if v and k in ("website", "email", "phone", "address"))
    img_html = f'<div class="img" style="background-image:url({hero})" role="img" aria-label="{esc(img.get("alt", ""))}"></div>' if hero else ""

    if layout == "split":
        main = f"""<div class="split"><div class="side">{img_html or f'<div class="sideblock">{logo_img(True)}</div>'}</div>
<div class="col">{'' if not img_html else logo_img(False)}<h1>{esc(headline)}</h1>
{f'<p class="sub">{esc(spec.get("subhead"))}</p>' if spec.get("subhead") else ''}
{f'<p class="body">{esc(body)}</p>' if body else ''}<ul class="pts">{pts}</ul><div class="dets">{det}</div>{cta_html}</div></div>"""
    elif layout == "event":
        first = details[0] if details else {}
        main = f"""<header class="band">{logo_img(True)}</header>
<div class="eventtop"><div class="date"><span>{esc(first.get("label", ""))}</span><b>{esc(first.get("value", ""))}</b></div>
<div><h1>{esc(headline)}</h1>{f'<p class="sub">{esc(spec.get("subhead"))}</p>' if spec.get("subhead") else ''}</div></div>
{img_html}<div class="col">{f'<p class="body">{esc(body)}</p>' if body else ''}<ul class="pts">{pts}</ul>
<div class="dets">{"".join(f'<div class="det"><span>{esc(d.get("label"))}</span><b>{esc(d.get("value"))}</b></div>' for d in details[1:])}</div>{cta_html}</div>"""
    elif layout == "minimal":
        main = f"""<div class="col min">{logo_img(False)}<h1>{esc(headline)}</h1>
{f'<p class="sub">{esc(spec.get("subhead"))}</p>' if spec.get("subhead") else ''}{img_html}
{f'<p class="body">{esc(body)}</p>' if body else ''}<ul class="pts">{pts}</ul><div class="dets">{det}</div>{cta_html}</div>"""
    else:  # hero
        main = f"""<header class="band">{logo_img(True)}</header>{img_html}
<div class="col"><h1>{esc(headline)}</h1>{f'<p class="sub">{esc(spec.get("subhead"))}</p>' if spec.get("subhead") else ''}
{f'<p class="body">{esc(body)}</p>' if body else ''}<ul class="pts">{pts}</ul><div class="dets">{det}</div>{cta_html}</div>"""

    unit = "px" if size in ("square", "story") else "pt"
    # Social sizes are set in px. A square has a third less height than a page, so its type is
    # smaller; a story is tall and takes larger type.
    scale = {"square": 1.35, "story": 2.1}.get(size, 1.0)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{esc(headline)} — {esc(name)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@page {{ size: {w} {h}; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #e9e9e6; }}
body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: {w}; height: {h}; margin: {'0' if unit == 'px' else '24px'} auto; background: {c['background']}; color: {c['text']};
  font-family: {body_font}; position: relative; overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 6px 30px rgba(0,0,0,.18); font-size: {11 * scale}{unit}; line-height: 1.45; }}
@media print {{ html, body {{ background: none; }} .page {{ margin: 0; box-shadow: none; }} }}
h1 {{ font-family: {head_font}; color: {c['primary']}; font-size: {40 * scale}{unit}; line-height: 1.05; margin: 0 0 .35em; letter-spacing: -.01em; }}
.sub {{ font-size: {16 * scale}{unit}; margin: 0 0 .9em; color: {c['secondary'] if contrast(c['secondary'], c['background']) >= 4.5 else c['text']}; }}
.body {{ margin: 0 0 .9em; }}
.band {{ background: {c['primary']}; color: {on_primary}; padding: {18 * scale}{unit} {36 * scale}{unit}; display: flex; align-items: center; }}
.logo {{ max-height: {44 * scale}{unit}; max-width: 55%; }}
.wordmark {{ font-family: {head_font}; font-weight: 700; font-size: {20 * scale}{unit}; }}
.band .wordmark {{ color: {on_primary}; }}
.img {{ height: {'26%' if size == 'square' else '34%'}; background-size: cover; background-position: center; }}
.col {{ padding: {28 * scale}{unit} {36 * scale}{unit}; flex: 1; display: flex; flex-direction: column; }}
.col .logo {{ margin-bottom: {18 * scale}{unit}; align-self: flex-start; }}
.pts {{ list-style: none; padding: 0; margin: 0 0 1em; }}
.pts li {{ padding-left: 1.2em; position: relative; margin: .35em 0; font-size: {13 * scale}{unit}; }}
.pts li::before {{ content: ""; position: absolute; left: 0; top: .45em; width: .55em; height: .55em; background: {c['accent']}; border-radius: 2px; }}
.dets {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(30%, 1fr)); gap: .6em 1.2em; margin: 0 0 1.2em; }}
.det span {{ display: block; font-size: {9 * scale}{unit}; text-transform: uppercase; letter-spacing: .08em; color: {c['secondary'] if contrast(c['secondary'], c['background']) >= 4.5 else c['text']}; }}
.det b {{ font-size: {13 * scale}{unit}; }}
.cta {{ margin-top: auto; background: {c['accent']}; color: {on_accent}; border-radius: 10px; padding: {16 * scale}{unit} {20 * scale}{unit};
  display: grid; grid-template-columns: 1fr auto; align-items: center; gap: .2em 1em; }}
.cta b {{ font-family: {head_font}; font-size: {20 * scale}{unit}; }}
.cta span {{ grid-column: 1; font-size: {12 * scale}{unit}; }}
.cta .qr {{ grid-column: 2; grid-row: 1 / span 2; width: {64 * scale}{unit}; height: {64 * scale}{unit}; background: #fff; padding: 4px; border-radius: 4px; }}
.split {{ display: grid; grid-template-columns: 42% 1fr; flex: 1; }}
.split .side .img {{ height: 100%; }}
.sideblock {{ background: {c['primary']}; height: 100%; display: flex; align-items: flex-start; padding: {36 * scale}{unit} {28 * scale}{unit}; }}
.eventtop {{ display: grid; grid-template-columns: auto 1fr; gap: 1.4em; align-items: center; padding: {28 * scale}{unit} {36 * scale}{unit} 0; }}
.date {{ background: {c['accent']}; color: {on_accent}; border-radius: 10px; padding: .8em 1em; text-align: center; min-width: 7em; }}
.date span {{ display: block; font-size: {9 * scale}{unit}; text-transform: uppercase; letter-spacing: .08em; }}
.date b {{ font-family: {head_font}; font-size: {18 * scale}{unit}; line-height: 1.15; }}
.eventtop + .img {{ margin-top: {20 * scale}{unit}; }}
.min {{ justify-content: flex-start; }}
.min .img {{ height: 30%; border-radius: 10px; margin: 0 0 1em; }}
.foot {{ padding: {12 * scale}{unit} {36 * scale}{unit}; font-size: {9 * scale}{unit}; color: {c['text']}; border-top: 1px solid {c['secondary']}33; display: flex; justify-content: space-between; gap: 1em; }}
</style></head>
<body><main class="page">
{main}
<footer class="foot"><span>{contact_line}</span><span>{esc(footer)}</span></footer>
</main></body></html>
"""
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path} ({layout}, {size}{', landscape' if landscape else ''}; "
          f"brand: {'yes' if brand else 'none'}; logo: {'yes' if (logo_light or logo_dark) else 'no'})")
    print(f"  contrast: text {contrast(c['text'], c['background']):.1f}:1 · band {contrast(on_primary, c['primary']):.1f}:1 · "
          f"call to action {contrast(on_accent, c['accent']):.1f}:1")
    return out_path, size, landscape


def chrome():
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(p):
            return p
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if shutil.which(n):
            return shutil.which(n)
    return None


def export(html_path, size, pdf=None, png=None, landscape=False):
    exe = chrome()
    if not exe:
        print("No Chrome or Chromium found: open the .html in a browser and print to PDF at 100% scale, margins none.")
        return
    url = Path(html_path).resolve().as_uri()
    if pdf:
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={Path(pdf).resolve()}", url], check=False, capture_output=True)
        print(f"wrote {Path(pdf).resolve()}" if Path(pdf).exists() else "PDF export failed — print from the browser instead")
    if png:
        pw, ph = PX[size][::-1] if landscape else PX[size]
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={pw},{ph}",
                        f"--screenshot={Path(png).resolve()}", url], check=False, capture_output=True)
        print(f"wrote {Path(png).resolve()}" if Path(png).exists() else "PNG export failed")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--output", default=None, help="output .html (default: alongside the spec)")
    ap.add_argument("--brand", default=None, help="brand.json from brand-kit; overrides the spec's brand field")
    ap.add_argument("--pdf", default=None, help="also write a PDF through headless Chrome, when installed")
    ap.add_argument("--png", default=None, help="also write a PNG (for social sizes) through headless Chrome")
    a = ap.parse_args(argv)
    out = a.output or str(Path(a.spec).with_suffix(".html"))
    html_path, size, landscape = build(a.spec, out, a.brand)
    if a.pdf or a.png:
        export(html_path, size, a.pdf, a.png, landscape)
    if WARNINGS:
        print(f"{len(WARNINGS)} warning(s) — fix them or tell the user before sharing the flyer")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

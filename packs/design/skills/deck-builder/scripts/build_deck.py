#!/usr/bin/env python3
"""Build a .pptx from a JSON deck spec.

The spec schema is documented in templates/deck-spec.json. Top-level fields:
- title:     overall deck title
- audience:  archetype (informational; doesn't change rendering)
- aspect:    "16:9" (default) or "4:3" — ignored when a template is supplied
- template:  path to a .pptx/.potx brand template; its masters, theme fonts,
             colors and slide size are inherited
- layout_map: logical layout -> template layout name or index (template mode)
- palette:   a hex-color block, or a name resolvable from templates/palettes.json
- brand:     path to a brand.json (the brand-kit skill writes one) or the same object
             inline. It supplies anything the spec leaves out: palette colours, template,
             logo files and fonts. --brand on the command line overrides it.
- slide_numbers: true/false (default: true when the deck has more than 10 slides)
- slides:    list of slide specs, each with a `layout` field

Supported layouts: title, section, content, two_column, big_number, quote,
image, table, chart, closing.

Usage:
    python3 build_deck.py <spec.json> [-o output.pptx] [--strict] [--brand brand.json]
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# The design canvas every hardcoded position below is expressed in. Real slide
# geometry comes from Canvas, which scales these to the actual deck size.
DESIGN_W_IN = 13.333
DESIGN_H_IN = 7.5

ASPECTS = {
    "16:9": (13.333, 7.5),
    "4:3": (10.0, 7.5),
    "16:10": (12.0, 7.5),
}

DEFAULT_PALETTE = {
    "primary": "#1A2A6C",
    "secondary": "#4A5A8C",
    "accent": "#FDBB2D",
    "background": "#FFFFFF",
    "text": "#222222",
}

CHART_TYPES = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
    "doughnut": XL_CHART_TYPE.DOUGHNUT,
    "stacked_column": XL_CHART_TYPE.COLUMN_STACKED,
    "stacked_bar": XL_CHART_TYPE.BAR_STACKED,
}

RASTER_OK = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}

WARNINGS: list[str] = []


# Set from brand.json in build(): fonts for the built-in design, and the logo files placed on
# its slides. A supplied template already carries its own fonts and logo, so these are only
# used when a slide renders on the built-in design.
BRAND = {"heading_font": None, "body_font": None, "logo": None, "logo_on_dark": None}


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    sys.stderr.write(f"warning: {msg}\n")


def die(msg: str) -> None:
    sys.stderr.write(f"error: {msg}\n")
    sys.exit(1)


# ----------------------------------------------------------------- geometry


@dataclass
class Canvas:
    """Maps design-canvas inches onto the real slide, whatever size it is."""

    w: int  # EMU
    h: int  # EMU

    @property
    def xr(self) -> float:
        return self.w / Inches(DESIGN_W_IN)

    @property
    def yr(self) -> float:
        return self.h / Inches(DESIGN_H_IN)

    @property
    def fr(self) -> float:
        """Font scale — driven by the tighter axis, floored so text stays legible."""
        return max(0.7, min(self.xr, self.yr))

    def x(self, inches: float) -> int:
        return int(Inches(inches) * self.xr)

    def y(self, inches: float) -> int:
        return int(Inches(inches) * self.yr)

    def pt(self, size: float) -> Pt:
        return Pt(round(size * self.fr, 1))

    @property
    def right_margin_w(self) -> int:
        """Full content width at the standard 0.75in gutter."""
        return self.w - 2 * self.x(0.75)


@dataclass
class Region:
    """A rectangle content gets drawn into."""

    left: int
    top: int
    width: int
    height: int


def default_region(c: Canvas, *, below_title_bar: bool = True) -> Region:
    top = c.y(1.5) if below_title_bar else c.y(0.9)
    return Region(c.x(0.75), top, c.right_margin_w, c.h - top - c.y(0.6))


# ----------------------------------------------------------------- palette


def hex_color(s: str) -> RGBColor:
    return RGBColor.from_string(str(s).lstrip("#").upper())


def resolve_palette(p, script_dir: Path) -> dict:
    """Accepts a dict (use directly) or a string name (look up in templates/palettes.json)."""
    if isinstance(p, dict):
        return {**DEFAULT_PALETTE, **p}
    if isinstance(p, str):
        palettes_path = script_dir.parent / "templates" / "palettes.json"
        if not palettes_path.exists():
            warn(f"palettes file missing at {palettes_path}; using defaults")
            return DEFAULT_PALETTE
        all_palettes = json.loads(palettes_path.read_text())
        if p not in all_palettes:
            warn(f"palette {p!r} not found; using defaults")
            return DEFAULT_PALETTE
        return {**DEFAULT_PALETTE, **all_palettes[p]}
    return DEFAULT_PALETTE


def series_colors(palette: dict, n: int) -> list:
    base = [palette["primary"], palette["accent"], palette["secondary"],
            palette["text"], "#7A8BB5", "#C9A227"]
    return [base[i % len(base)] for i in range(n)]


# ----------------------------------------------------------------- template


def _potx_to_pptx(src: Path, tmpdir: Path) -> Path:
    """python-pptx refuses a .potx content type. Repack it as a .pptx."""
    dst = tmpdir / (src.stem + ".pptx")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                text = data.decode("utf-8")
                text = text.replace(
                    "presentationml.template.main+xml",
                    "presentationml.presentation.main+xml",
                ).replace(
                    "presentationml.template.macroEnabled.main+xml",
                    "presentationml.presentation.macroEnabled.main+xml",
                )
                data = text.encode("utf-8")
            zout.writestr(item, data)
    return dst


def clear_slides(prs) -> int:
    """Drop any slides the template shipped with — we want its masters, not its content."""
    sld_id_lst = prs.slides._sldIdLst
    removed = 0
    for sld_id in list(sld_id_lst):
        prs.part.drop_rel(sld_id.rId)
        sld_id_lst.remove(sld_id)
        removed += 1
    return removed


def open_presentation(spec: dict, spec_dir: Path, tmpdir: Path):
    """Return (prs, canvas, using_template)."""
    tmpl = spec.get("template")
    if not tmpl:
        prs = Presentation()
        aspect = spec.get("aspect", "16:9")
        if aspect not in ASPECTS:
            warn(f"unknown aspect {aspect!r}; using 16:9")
            aspect = "16:9"
        w_in, h_in = ASPECTS[aspect]
        prs.slide_width = Inches(w_in)
        prs.slide_height = Inches(h_in)
        return prs, Canvas(prs.slide_width, prs.slide_height), False

    path = Path(tmpl).expanduser()
    if not path.is_absolute():
        path = (spec_dir / path).resolve()
    if not path.exists():
        die(f"template not found: {path}")
    if path.suffix.lower() in (".potx", ".potm"):
        path = _potx_to_pptx(path, tmpdir)
    elif path.suffix.lower() not in (".pptx", ".pptm"):
        die(f"template must be .pptx or .potx, got {path.suffix!r}")

    try:
        prs = Presentation(str(path))
    except Exception as exc:  # noqa: BLE001 — surface the real reason, don't mask it
        die(f"could not open template {path}: {exc}")

    dropped = clear_slides(prs)
    if dropped:
        print(f"template: dropped {dropped} sample slide(s), kept masters and layouts")
    if spec.get("aspect"):
        warn("`aspect` ignored — the template's own slide size wins")
    return prs, Canvas(prs.slide_width, prs.slide_height), True


def list_layouts(prs) -> str:
    return "\n".join(f"  [{i}] {lay.name}" for i, lay in enumerate(prs.slide_layouts))


def find_layout(prs, ref):
    """Resolve a template layout by index, exact name, or case-insensitive substring."""
    if isinstance(ref, int):
        try:
            return prs.slide_layouts[ref]
        except IndexError:
            warn(f"layout index {ref} out of range ({len(prs.slide_layouts)} layouts)")
            return None
    if not isinstance(ref, str):
        return None
    for lay in prs.slide_layouts:
        if lay.name == ref:
            return lay
    low = ref.lower()
    for lay in prs.slide_layouts:
        if lay.name.lower() == low:
            return lay
    for lay in prs.slide_layouts:
        if low in lay.name.lower():
            return lay
    warn(f"template layout {ref!r} not found; falling back to overlay rendering")
    return None


def blank_layout(prs):
    """The emptiest layout available — index 6 in the default template."""
    for lay in prs.slide_layouts:
        if not lay.placeholders._element.findall(
            ".//{http://schemas.openxmlformats.org/presentationml/2006/main}sp"
        ):
            return lay
    for lay in prs.slide_layouts:
        if lay.name.strip().lower() in ("blank", "blank slide"):
            return lay
    try:
        return prs.slide_layouts[6]
    except IndexError:
        return prs.slide_layouts[-1]


# ------------------------------------------------------------- placeholders


TITLE_PH = (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
BODY_PH = (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.SUBTITLE)
SKIP_PH = (PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.DATE)


def ph_type(shape):
    try:
        return shape.placeholder_format.type
    except (AttributeError, ValueError):
        return None


def placeholders(slide, kinds=None):
    out = []
    for shape in slide.placeholders:
        t = ph_type(shape)
        if t in SKIP_PH:
            continue
        if kinds is None or t in kinds:
            out.append(shape)
    return out


def set_ph_text(shape, text: str, *, size_pt=None) -> None:
    """Write into a placeholder without flattening the template's formatting.

    Assigning `text_frame.text` collapses the paragraph to one unstyled run and
    loses the template's font. Reusing the existing run keeps it.
    """
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = text
        for extra in list(p.runs)[1:]:
            extra._r.getparent().remove(extra._r)
        run = p.runs[0]
    else:
        run = p.add_run()
        run.text = text
    if size_pt is not None:
        run.font.size = size_pt


def set_ph_bullets(shape, bullets, *, bold_first: bool = False) -> None:
    tf = shape.text_frame
    tf.word_wrap = True
    template_p = copy.deepcopy(tf.paragraphs[0]._p)
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    for i, text in enumerate(bullets):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            tf._txBody.append(copy.deepcopy(template_p))
            p = tf.paragraphs[-1]
        if p.runs:
            p.runs[0].text = str(text)
            for extra in list(p.runs)[1:]:
                extra._r.getparent().remove(extra._r)
        else:
            p.add_run().text = str(text)
        if bold_first and i == 0 and p.runs:
            p.runs[0].font.bold = True


def drop_empty_placeholders(slide) -> None:
    """Remove the 'Click to add text' ghosts a template layout leaves behind."""
    for shape in list(slide.placeholders):
        if ph_type(shape) in SKIP_PH:
            continue
        if shape.has_text_frame and not shape.text_frame.text.strip():
            shape._element.getparent().remove(shape._element)


def claim_body_region(slide, c: Canvas, *, below_title_bar=True, kinds=BODY_PH) -> Region:
    """Take the biggest empty body placeholder's rectangle and remove the placeholder.

    Custom content (numbers, tables, charts, images) then lands exactly where the
    template intended content to go, instead of at our own hardcoded coordinates.
    """
    best, best_area = None, 0
    for shape in placeholders(slide, kinds):
        if shape.has_text_frame and shape.text_frame.text.strip():
            continue
        area = (shape.width or 0) * (shape.height or 0)
        if area > best_area:
            best, best_area = shape, area
    if best is None or not best_area:
        return default_region(c, below_title_bar=below_title_bar)
    region = Region(best.left, best.top, best.width, best.height)
    best._element.getparent().remove(best._element)
    return region


# ------------------------------------------------------------- draw helpers


def set_background(slide, hex_str: str) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = hex_color(hex_str)


def add_textbox(slide, text: str, *, left, top, width, height,
                size, bold: bool = False, color: str = "#222222",
                align=PP_ALIGN.LEFT, anchor=None) -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = hex_color(color)
    font = BRAND["heading_font"] if (bold or size >= Pt(24)) else BRAND["body_font"]
    if font:
        run.font.name = font


def add_bullets(slide, bullets, *, left, top, width, height,
                size, color: str = "#222222") -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•  {b}"
        p.space_after = Pt(10)
        for run in p.runs:
            run.font.size = size
            run.font.color.rgb = hex_color(color)
            if BRAND["body_font"]:
                run.font.name = BRAND["body_font"]


def add_rect(slide, *, left, top, width, height, fill: str) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex_color(fill)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def set_notes(slide, notes: str) -> None:
    slide.notes_slide.notes_text_frame.text = notes


def add_slide_number(slide, c: Canvas, n: int, palette: dict) -> None:
    add_textbox(slide, str(n),
                left=c.w - c.x(1.0), top=c.h - c.y(0.55),
                width=c.x(0.5), height=c.y(0.35),
                size=c.pt(11), color=palette["text"], align=PP_ALIGN.RIGHT)


# ------------------------------------------------------------ media helpers


def place_image(slide, path_str: str, region: Region, *, spec_dir: Path,
                palette: dict, strict: bool):
    """Aspect-fit an image into the region. Missing/unsupported files degrade visibly."""
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (spec_dir / path).resolve()

    problem = None
    if not path.exists():
        problem = f"image not found: {path}"
    elif path.suffix.lower() not in RASTER_OK:
        problem = (f"unsupported image format {path.suffix!r} ({path.name}) — "
                   "python-pptx reads raster only; convert SVG/EMF/PDF to PNG first")

    if problem:
        if strict:
            die(problem)
        warn(problem + " — drew a placeholder box instead")
        box = add_rect(slide, left=region.left, top=region.top,
                       width=region.width, height=region.height,
                       fill="#EDEFF4")
        box.line.color.rgb = hex_color(palette["secondary"])
        box.line.width = Pt(1)
        add_textbox(slide, f"[ missing image: {path.name} ]",
                    left=region.left, top=region.top + region.height // 2,
                    width=region.width, height=Emu(int(Inches(0.5))),
                    size=Pt(14), color=palette["secondary"], align=PP_ALIGN.CENTER)
        return None

    pic = slide.shapes.add_picture(str(path), region.left, region.top)
    scale = min(region.width / pic.width, region.height / pic.height)
    pic.width = int(pic.width * scale)
    pic.height = int(pic.height * scale)
    pic.left = region.left + (region.width - pic.width) // 2
    pic.top = region.top + (region.height - pic.height) // 2
    return pic


def place_table(slide, columns, rows, region: Region, c: Canvas, palette: dict) -> None:
    n_rows = len(rows) + 1
    n_cols = max(len(columns), max((len(r) for r in rows), default=0))
    gfx = slide.shapes.add_table(n_rows, n_cols, region.left, region.top,
                                 region.width, region.height)
    table = gfx.table
    table.first_row = True

    body_pt = 16 if n_rows <= 7 else (14 if n_rows <= 10 else 12)

    for j in range(n_cols):
        cell = table.cell(0, j)
        cell.text = str(columns[j]) if j < len(columns) else ""
        cell.fill.solid()
        cell.fill.fore_color.rgb = hex_color(palette["primary"])
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.bold = True
                run.font.size = c.pt(body_pt + 1)
                run.font.color.rgb = hex_color("#FFFFFF")
                if BRAND["heading_font"]:
                    run.font.name = BRAND["heading_font"]

    for i, row in enumerate(rows, start=1):
        for j in range(n_cols):
            cell = table.cell(i, j)
            cell.text = str(row[j]) if j < len(row) else ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = hex_color("#FFFFFF" if i % 2 else "#F2F4F8")
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = c.pt(body_pt)
                    if BRAND["body_font"]:
                        run.font.name = BRAND["body_font"]
                    run.font.color.rgb = hex_color(palette["text"])


def place_chart(slide, chart_spec: dict, region: Region, c: Canvas, palette: dict) -> None:
    kind = str(chart_spec.get("type", "column")).lower()
    if kind not in CHART_TYPES:
        warn(f"unknown chart type {kind!r}; using column")
        kind = "column"

    categories = chart_spec.get("categories") or []
    series = chart_spec.get("series") or []
    if not categories or not series:
        warn("chart slide has no categories or no series; skipped")
        return

    data = CategoryChartData()
    data.categories = categories
    for s in series:
        values = list(s.get("values") or [])
        if len(values) != len(categories):
            warn(f"series {s.get('name', '?')!r} has {len(values)} values "
                 f"for {len(categories)} categories — padded with gaps")
            values = (values + [None] * len(categories))[:len(categories)]
        data.add_series(str(s.get("name", "Series")), values)

    gfx = slide.shapes.add_chart(CHART_TYPES[kind], region.left, region.top,
                                 region.width, region.height, data)
    chart = gfx.chart
    chart.font.size = c.pt(13)
    if BRAND["body_font"]:
        chart.font.name = BRAND["body_font"]
    chart.font.color.rgb = hex_color(palette["text"])

    is_pie = kind in ("pie", "doughnut")
    chart.has_legend = bool(chart_spec.get("legend", is_pie or len(series) > 1))
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False

    colors = series_colors(palette, max(len(series), len(categories)))
    plot = chart.plots[0]
    if is_pie:
        plot.vary_by_categories = True
        for i, point in enumerate(plot.series[0].points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = hex_color(colors[i % len(colors)])
    else:
        plot.vary_by_categories = False
        for i, s in enumerate(chart.series):
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = hex_color(colors[i])
        if kind == "line":
            for i, s in enumerate(chart.series):
                s.format.line.color.rgb = hex_color(colors[i])

    if chart_spec.get("data_labels", is_pie):
        plot.has_data_labels = True
        labels = plot.data_labels
        labels.font.size = c.pt(12)
        if is_pie:
            labels.font.color.rgb = hex_color("#FFFFFF")
        if chart_spec.get("number_format"):
            labels.number_format = chart_spec["number_format"]
            labels.number_format_is_linked = False


# ----------------------------------------------------------------- renderers
#
# Each renderer draws the deck's own design. In template mode the chrome comes
# from the template layout instead, and only the parts a placeholder cannot
# express are drawn here.


def _title_bar(slide, c: Canvas, palette, title: str) -> None:
    add_rect(slide, left=0, top=0, width=c.w, height=c.y(1.0),
             fill=palette["primary"])
    add_textbox(slide, title,
                left=c.x(0.5), top=c.y(0.22),
                width=c.w - c.x(1.0), height=c.y(0.7),
                size=c.pt(26), bold=True, color="#FFFFFF")


def render_title(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    add_rect(slide, left=0, top=c.y(3.0), width=c.w, height=c.y(0.15),
             fill=palette["accent"])
    add_textbox(slide, spec.get("title", "Untitled"),
                left=c.x(0.75), top=c.y(2.0),
                width=c.right_margin_w, height=c.y(1.2),
                size=c.pt(44), bold=True, color=palette["primary"])
    if spec.get("subtitle"):
        add_textbox(slide, spec["subtitle"],
                    left=c.x(0.75), top=c.y(3.4),
                    width=c.right_margin_w, height=c.y(0.8),
                    size=c.pt(24), color=palette["text"])
    footer = "  ·  ".join([s for s in (spec.get("presenter"), spec.get("date")) if s])
    if footer:
        add_textbox(slide, footer,
                    left=c.x(0.75), top=c.y(6.5),
                    width=c.right_margin_w, height=c.y(0.5),
                    size=c.pt(14), color=palette["text"])


def render_section(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["primary"])
    add_textbox(slide, spec.get("title", ""),
                left=c.x(0.75), top=c.y(3.0),
                width=c.right_margin_w, height=c.y(1.5),
                size=c.pt(48), bold=True, color="#FFFFFF")
    add_rect(slide, left=c.x(0.75), top=c.y(4.6),
             width=c.x(2), height=c.y(0.1), fill=palette["accent"])


def render_content(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    _title_bar(slide, c, palette, spec.get("title", ""))
    region = default_region(c)
    if spec.get("bullets"):
        add_bullets(slide, spec["bullets"],
                    left=region.left, top=region.top,
                    width=region.width, height=region.height,
                    size=c.pt(20), color=palette["text"])
    if spec.get("body"):
        top = region.top + (c.y(0.4) * len(spec.get("bullets") or []) if spec.get("bullets") else 0)
        add_textbox(slide, spec["body"],
                    left=region.left, top=top,
                    width=region.width, height=region.height,
                    size=c.pt(18), color=palette["text"])


def render_two_column(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    _title_bar(slide, c, palette, spec.get("title", ""))
    col_w = c.x(6.0)
    for col_key, col_left in (("left", c.x(0.5)), ("right", c.x(6.85))):
        col = spec.get(col_key) or {}
        if col.get("title"):
            add_textbox(slide, col["title"],
                        left=col_left, top=c.y(1.3),
                        width=col_w, height=c.y(0.6),
                        size=c.pt(20), bold=True, color=palette["primary"])
        if col.get("bullets"):
            add_bullets(slide, col["bullets"],
                        left=col_left, top=c.y(2.0),
                        width=col_w, height=c.y(5.0),
                        size=c.pt(18), color=palette["text"])
        elif col.get("body"):
            add_textbox(slide, col["body"],
                        left=col_left, top=c.y(2.0),
                        width=col_w, height=c.y(5.0),
                        size=c.pt(18), color=palette["text"])


def render_big_number(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    _title_bar(slide, c, palette, spec.get("title", ""))
    draw_big_number(slide, c, palette, spec, default_region(c))


def draw_big_number(slide, c, palette, spec, region: Region) -> None:
    number = spec.get("number", "—")
    size = 140 if len(str(number)) <= 6 else (100 if len(str(number)) <= 10 else 72)
    add_textbox(slide, str(number),
                left=region.left, top=region.top,
                width=region.width, height=int(region.height * 0.68),
                size=c.pt(size), bold=True, color=palette["accent"],
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if spec.get("caption"):
        add_textbox(slide, spec["caption"],
                    left=region.left, top=region.top + int(region.height * 0.70),
                    width=region.width, height=int(region.height * 0.25),
                    size=c.pt(22), color=palette["text"], align=PP_ALIGN.CENTER)


def render_quote(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    draw_quote(slide, c, palette, spec,
               Region(c.x(1.4), c.y(2.0), c.right_margin_w - c.x(1.3), c.y(4.0)))


def draw_quote(slide, c, palette, spec, region: Region) -> None:
    add_rect(slide, left=region.left, top=region.top,
             width=c.x(0.12), height=region.height * 7 // 8, fill=palette["accent"])
    text_left = region.left + c.x(0.5)
    text_w = region.width - c.x(0.5)
    add_textbox(slide, f"“{spec.get('quote', '')}”",
                left=text_left, top=region.top,
                width=text_w, height=int(region.height * 0.72),
                size=c.pt(30), color=palette["primary"])
    if spec.get("attribution"):
        add_textbox(slide, f"— {spec['attribution']}",
                    left=text_left, top=region.top + int(region.height * 0.80),
                    width=text_w, height=c.y(0.7),
                    size=c.pt(18), color=palette["text"])


def render_image(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    position = str(spec.get("position", "full")).lower()
    bullets = spec.get("bullets") or []
    if spec.get("title"):
        _title_bar(slide, c, palette, spec["title"])
        top = c.y(1.4)
    else:
        top = c.y(0.6)
    bottom = c.h - c.y(1.0 if spec.get("caption") else 0.5)
    height = bottom - top

    if bullets and position in ("left", "right"):
        half = (c.right_margin_w - c.x(0.5)) // 2
        img_left = c.x(0.75) if position == "left" else c.x(0.75) + half + c.x(0.5)
        txt_left = c.x(0.75) + half + c.x(0.5) if position == "left" else c.x(0.75)
        add_bullets(slide, bullets, left=txt_left, top=top + c.y(0.2),
                    width=half, height=height, size=c.pt(18), color=palette["text"])
        region = Region(img_left, top, half, height)
    else:
        region = Region(c.x(0.75), top, c.right_margin_w, height)

    draw_image(slide, c, palette, spec, region, ctx)


def draw_image(slide, c, palette, spec, region: Region, ctx) -> None:
    src = spec.get("image") or spec.get("path")
    if not src:
        warn("image slide has no `image` path; skipped")
        return
    place_image(slide, src, region, spec_dir=ctx["spec_dir"],
                palette=palette, strict=ctx["strict"])
    if spec.get("caption"):
        add_textbox(slide, spec["caption"],
                    left=region.left, top=region.top + region.height + c.y(0.05),
                    width=region.width, height=c.y(0.4),
                    size=c.pt(13), color=palette["secondary"], align=PP_ALIGN.CENTER)


def render_table(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    _title_bar(slide, c, palette, spec.get("title", ""))
    draw_table(slide, c, palette, spec, default_region(c), ctx)


def draw_table(slide, c, palette, spec, region: Region, ctx) -> None:
    columns = spec.get("columns") or []
    rows = spec.get("rows") or []
    if not columns and not rows:
        warn("table slide has no columns or rows; skipped")
        return
    if len(rows) > 12:
        warn(f"table has {len(rows)} data rows — over 12 stops being readable on a slide")
    height = min(region.height, c.y(0.45) * (len(rows) + 1))
    place_table(slide, columns, rows,
                Region(region.left, region.top, region.width, height), c, palette)
    if spec.get("caption"):
        add_textbox(slide, spec["caption"],
                    left=region.left, top=region.top + height + c.y(0.15),
                    width=region.width, height=c.y(0.4),
                    size=c.pt(13), color=palette["secondary"])


def render_chart(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["background"])
    _title_bar(slide, c, palette, spec.get("title", ""))
    draw_chart(slide, c, palette, spec, default_region(c), ctx)


def draw_chart(slide, c, palette, spec, region: Region, ctx) -> None:
    chart_spec = spec.get("chart") or {}
    takeaway = spec.get("takeaway")
    if takeaway:
        add_textbox(slide, takeaway,
                    left=region.left, top=region.top,
                    width=region.width, height=c.y(0.45),
                    size=c.pt(16), color=palette["text"])
        region = Region(region.left, region.top + c.y(0.55),
                        region.width, region.height - c.y(0.55))
    place_chart(slide, chart_spec, region, c, palette)
    if spec.get("source"):
        add_textbox(slide, f"Source: {spec['source']}",
                    left=region.left, top=region.top + region.height - c.y(0.05),
                    width=region.width, height=c.y(0.35),
                    size=c.pt(11), color=palette["secondary"])


def render_closing(slide, c, palette, spec, ctx) -> None:
    set_background(slide, palette["primary"])
    add_textbox(slide, spec.get("title", "Thank you"),
                left=c.x(0.5), top=c.y(2.5),
                width=c.w - c.x(1.0), height=c.y(1.5),
                size=c.pt(54), bold=True, color="#FFFFFF", align=PP_ALIGN.CENTER)
    if spec.get("subtitle"):
        add_textbox(slide, spec["subtitle"],
                    left=c.x(0.5), top=c.y(4.3),
                    width=c.w - c.x(1.0), height=c.y(0.8),
                    size=c.pt(22), color=palette["accent"], align=PP_ALIGN.CENTER)


RENDERERS = {
    "title": render_title,
    "section": render_section,
    "content": render_content,
    "two_column": render_two_column,
    "big_number": render_big_number,
    "quote": render_quote,
    "image": render_image,
    "table": render_table,
    "chart": render_chart,
    "closing": render_closing,
}

# Layouts a template placeholder can express on its own. Everything else keeps
# the template's chrome but draws its content into the claimed body region.
PLACEHOLDER_NATIVE = {"title", "section", "content", "two_column", "closing"}

CUSTOM_DRAW = {
    "big_number": draw_big_number,
    "quote": draw_quote,
    "image": draw_image,
    "table": draw_table,
    "chart": draw_chart,
}


# ------------------------------------------------------------ template mode


def render_templated(slide, c, palette, spec, ctx, logical: str) -> None:
    """Fill the template layout's placeholders; draw only what they can't hold."""
    title_phs = placeholders(slide, TITLE_PH)
    title_text = spec.get("title")
    if title_text and title_phs:
        set_ph_text(title_phs[0], title_text)
    elif title_text:
        add_textbox(slide, title_text, left=c.x(0.6), top=c.y(0.4),
                    width=c.w - c.x(1.2), height=c.y(0.9),
                    size=c.pt(28), bold=True, color=palette["primary"])

    if logical in CUSTOM_DRAW:
        kinds = BODY_PH + (PP_PLACEHOLDER.PICTURE,) if logical == "image" else BODY_PH
        region = claim_body_region(slide, c, kinds=kinds)
        drawer = CUSTOM_DRAW[logical]
        if logical in ("image", "table", "chart"):
            drawer(slide, c, palette, spec, region, ctx)
        else:
            drawer(slide, c, palette, spec, region)
        drop_empty_placeholders(slide)
        return

    bodies = [b for b in placeholders(slide, BODY_PH) if b not in title_phs]

    if logical == "two_column":
        cols = [spec.get("left") or {}, spec.get("right") or {}]
        targets = sorted(bodies, key=lambda s: s.left or 0)[:2]
        if len(targets) >= 2:
            for target, col in zip(targets, cols):
                items = col.get("bullets") or ([col["body"]] if col.get("body") else [])
                if col.get("title"):
                    items = [col["title"]] + list(items)
                if items:
                    set_ph_bullets(target, items, bold_first=bool(col.get("title")))
        else:
            region = claim_body_region(slide, c)
            half = (region.width - c.x(0.4)) // 2
            for i, col in enumerate(cols):
                left = region.left + i * (half + c.x(0.4))
                if col.get("title"):
                    add_textbox(slide, col["title"], left=left, top=region.top,
                                width=half, height=c.y(0.5),
                                size=c.pt(20), bold=True, color=palette["primary"])
                items = col.get("bullets") or ([col["body"]] if col.get("body") else [])
                if items:
                    add_bullets(slide, items, left=left, top=region.top + c.y(0.6),
                                width=half, height=region.height - c.y(0.6),
                                size=c.pt(18), color=palette["text"])
        drop_empty_placeholders(slide)
        return

    # Sub-headline: prefer a real subtitle placeholder, then any spare body, then
    # a drawn textbox — a `Title Only` layout must not silently swallow the line.
    if spec.get("subtitle"):
        subs = [b for b in bodies if ph_type(b) == PP_PLACEHOLDER.SUBTITLE]
        target = subs[0] if subs else (bodies[0] if bodies and not spec.get("bullets")
                                       and not spec.get("body") else None)
        if target is not None:
            set_ph_text(target, spec["subtitle"])
            bodies = [b for b in bodies if b is not target]
        else:
            top = (title_phs[0].top + title_phs[0].height + c.y(0.2)
                   if title_phs else c.y(1.4))
            add_textbox(slide, spec["subtitle"], left=c.x(0.75), top=top,
                        width=c.right_margin_w, height=c.y(0.8),
                        size=c.pt(20), color=palette["text"])

    payload = spec.get("bullets") or ([spec["body"]] if spec.get("body") else [])
    if payload:
        if bodies:
            set_ph_bullets(bodies[0], payload)
        else:
            region = claim_body_region(slide, c)
            add_bullets(slide, payload, left=region.left, top=region.top,
                        width=region.width, height=region.height,
                        size=c.pt(18), color=palette["text"])

    footer = "  ·  ".join([s for s in (spec.get("presenter"), spec.get("date")) if s])
    if footer and logical == "title":
        add_textbox(slide, footer, left=c.x(0.75), top=c.h - c.y(0.9),
                    width=c.right_margin_w, height=c.y(0.4),
                    size=c.pt(13), color=palette["text"])

    drop_empty_placeholders(slide)


def layout_numbers_slides(layout) -> bool:
    """True when the template's own master already stamps a slide number."""
    for shape in layout.placeholders:
        if ph_type(shape) == PP_PLACEHOLDER.SLIDE_NUMBER:
            return True
    return False


# ----------------------------------------------------------------- driver


def load_brand(ref, base: Path):
    """brand.json path or inline object -> (dict, directory its relative paths resolve from)."""
    if not ref:
        return {}, base
    if isinstance(ref, dict):
        return ref, base
    path = (base / ref).expanduser() if not Path(ref).is_absolute() else Path(ref)
    if not path.exists():
        warn(f"brand file not found: {path}; building without it")
        return {}, base
    try:
        return json.loads(path.read_text()), path.parent
    except json.JSONDecodeError as e:
        warn(f"brand file {path} is not valid JSON ({e}); building without it")
        return {}, base


def apply_brand(spec: dict, brand: dict, brand_dir: Path, spec_dir: Path) -> None:
    """Fill what the spec leaves out from the brand. The spec always wins: a deck can still
    override one colour or swap the template without editing the brand file."""
    colors = {k: v for k, v in (brand.get("colors") or {}).items()
              if k in ("primary", "secondary", "accent", "background", "text") and v}
    if colors and not spec.get("palette"):
        spec["palette"] = colors
    elif colors and isinstance(spec.get("palette"), dict):
        spec["palette"] = {**colors, **spec["palette"]}
    tpl = (brand.get("templates") or {}).get("pptx") or brand.get("template")
    if tpl and not spec.get("template"):
        spec["template"] = str((brand_dir / tpl).resolve()) if not Path(tpl).is_absolute() else tpl
    fonts = brand.get("fonts") or {}
    BRAND["heading_font"] = (fonts.get("heading") or {}).get("family") if isinstance(fonts.get("heading"), dict) else fonts.get("heading")
    BRAND["body_font"] = (fonts.get("body") or {}).get("family") if isinstance(fonts.get("body"), dict) else fonts.get("body")
    logo = brand.get("logo") or {}
    for key, field in (("logo", "primary"), ("logo_on_dark", "on_dark")):
        ref = logo.get(field) if isinstance(logo, dict) else (logo if field == "primary" else None)
        if not ref:
            continue
        lp = (brand_dir / ref) if not Path(ref).is_absolute() else Path(ref)
        if lp.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            warn(f"logo {lp.name} is {lp.suffix or 'not an image'}; PowerPoint needs PNG or JPG. Export the logo as PNG.")
        elif not lp.exists():
            warn(f"logo not found: {lp}")
        else:
            BRAND[key] = str(lp)


def is_dark(hex_str: str) -> bool:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.45


def place_logo(slide, c: "Canvas", palette: dict, logical: str) -> None:
    """The brand logo on the built-in design: large on the cover, small in a fixed corner on
    every other slide, using the on-dark variant on dark slides when there is one."""
    if not BRAND["logo"] and not BRAND["logo_on_dark"]:
        return
    dark_bg = logical in ("section", "closing") and is_dark(palette["primary"]) or \
        (logical == "title" and is_dark(palette["background"]))
    path = (BRAND["logo_on_dark"] or BRAND["logo"]) if dark_bg else (BRAND["logo"] or BRAND["logo_on_dark"])
    if logical == "title":
        slide.shapes.add_picture(path, c.x(0.75), c.y(0.6), height=c.y(0.7))
    elif logical == "closing":
        pic = slide.shapes.add_picture(path, 0, c.h - c.y(1.25), height=c.y(0.6))
        pic.left = int((c.w - pic.width) / 2)
    else:
        slide.shapes.add_picture(path, c.x(0.5), c.h - c.y(0.55), height=c.y(0.32))


def build(spec_path: Path, out_path: Path, script_dir: Path, *, strict: bool, brand_ref=None) -> None:
    spec = json.loads(spec_path.read_text())
    spec_dir = spec_path.parent
    brand, brand_dir = load_brand(brand_ref or spec.get("brand"), spec_dir)
    if brand:
        apply_brand(spec, brand, brand_dir, spec_dir)
    palette = resolve_palette(spec.get("palette"), script_dir)

    slides = spec.get("slides", [])
    if not slides:
        die("spec has no slides")

    with tempfile.TemporaryDirectory() as tmp:
        prs, canvas, using_template = open_presentation(spec, spec_dir, Path(tmp))
        layout_map = spec.get("layout_map") or {}
        if using_template and not layout_map:
            warn("template supplied without a `layout_map` — rendering the deck's own "
                 "design on the template's blank layout. Map logical layouts to the "
                 "template's layout names to inherit its slide designs:\n"
                 + list_layouts(prs))

        blank = blank_layout(prs)
        show_numbers = spec.get("slide_numbers", len(slides) > 10)
        ctx = {"spec_dir": spec_dir, "strict": strict, "template": using_template}

        for i, slide_spec in enumerate(slides, start=1):
            logical = slide_spec.get("layout", "content")
            if logical not in RENDERERS:
                warn(f"unknown layout {logical!r} on slide {i}; falling back to content")
                logical = "content"

            ref = slide_spec.get("layout_name", layout_map.get(logical))
            tmpl_layout = find_layout(prs, ref) if (using_template and ref is not None) else None

            slide = prs.slides.add_slide(tmpl_layout or blank)
            if tmpl_layout is not None:
                render_templated(slide, canvas, palette, slide_spec, ctx, logical)
            else:
                RENDERERS[logical](slide, canvas, palette, slide_spec, ctx)
                if not using_template:  # a template's masters already carry its logo
                    place_logo(slide, canvas, palette, logical)

            if slide_spec.get("notes"):
                set_notes(slide, slide_spec["notes"])
            own_numbering = tmpl_layout is not None and layout_numbers_slides(tmpl_layout)
            if (show_numbers and not own_numbering
                    and logical not in ("title", "section", "closing")):
                add_slide_number(slide, canvas, i, palette)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(out_path))

    mode = "template" if using_template else "built-in design"
    if brand:
        mode += ", brand: " + ", ".join(x for x, on in (("colours", bool(brand.get("colors"))),
                                                         ("logo", bool(BRAND["logo"] or BRAND["logo_on_dark"])),
                                                         ("fonts", bool(BRAND["heading_font"] or BRAND["body_font"]))) if on)
    print(f"wrote {out_path} ({len(slides)} slides, {mode})")
    if WARNINGS:
        print(f"{len(WARNINGS)} warning(s) — see stderr; fix them before presenting")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", help="Path to deck spec JSON")
    ap.add_argument("-o", "--output", default=None,
                    help="Output .pptx path (default: alongside the spec)")
    ap.add_argument("--strict", action="store_true",
                    help="Fail on a missing/unsupported image instead of drawing a placeholder")
    ap.add_argument("--brand", metavar="BRAND_JSON",
                    help="brand.json (from the brand-kit skill): colours, template, logo, fonts. "
                         "Fills anything the spec leaves out")
    ap.add_argument("--list-layouts", metavar="TEMPLATE",
                    help="Print a template's layout names and indices, then exit "
                         "(use them to write layout_map)")
    args = ap.parse_args(argv)

    if args.list_layouts:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(args.list_layouts).expanduser().resolve()
            if not path.exists():
                die(f"template not found: {path}")
            shown = path.name
            if path.suffix.lower() in (".potx", ".potm"):
                path = _potx_to_pptx(path, Path(tmp))
            prs = Presentation(str(path))
            print(f"{shown} — slide size "
                  f"{prs.slide_width / 914400:.2f}in x {prs.slide_height / 914400:.2f}in")
            print(list_layouts(prs))
        return 0

    if not args.spec:
        ap.error("the spec argument is required (or use --list-layouts)")

    spec_path = Path(args.spec).expanduser().resolve()
    if not spec_path.exists():
        die(f"spec file not found: {spec_path}")

    out_path = (Path(args.output).expanduser().resolve()
                if args.output else spec_path.with_suffix(".pptx"))

    build(spec_path, out_path, Path(__file__).resolve().parent, strict=args.strict,
          brand_ref=str(Path(args.brand).expanduser().resolve()) if args.brand else None)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "marketing-flyer", "build_flyer.py"
m = load(SKILL, SCRIPT)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def spec_file(d, **fields):
    spec = {"headline": "Free community health fair",
            "cta": {"text": "Save your spot", "url": "fair.example.org"}}
    spec.update(fields)
    return write(os.path.join(d, "spec.json"), json.dumps(spec))


def png_file(d, name="pic.png"):
    p = os.path.join(d, name)
    with open(p, "wb") as f:
        f.write(PNG)
    return p


def build(d, *args, **fields):
    """Run the CLI on a spec built from fields; return (code, stdout, stderr, html or None)."""
    spec = spec_file(d, **fields)
    out = os.path.join(d, "flyer.html")
    code, so, se = run(SKILL, SCRIPT, spec, "-o", out, *args, cwd=d)
    return code, so, se, (read(out) if os.path.exists(out) else None)


class ContrastHelperTests(unittest.TestCase):
    def test_black_on_white_is_21_to_1_and_symmetric(self):
        self.assertAlmostEqual(m.contrast("#000000", "#FFFFFF"), 21.0)
        self.assertAlmostEqual(m.contrast("#FFFFFF", "#000000"), 21.0)

    def test_same_colour_is_1_to_1(self):
        self.assertAlmostEqual(m.contrast("#1A2A6C", "#1a2a6c"), 1.0)

    def test_mid_grey_777_just_misses_4_5_on_white(self):
        self.assertLess(m.contrast("#777777", "#FFFFFF"), 4.5)
        self.assertGreater(m.contrast("#767676", "#FFFFFF"), 4.5)

    def test_ink_on_dark_band_is_white_and_on_pale_accent_is_brand_text(self):
        self.assertEqual(m.ink_on("#1A2A6C", "#222222"), "#FFFFFF")
        self.assertEqual(m.ink_on("#FDBB2D", "#222222"), "#222222")


class PureHelperTests(unittest.TestCase):
    def test_font_stack_from_dict_string_and_none(self):
        self.assertEqual(m.font_stack({"family": "Inter", "fallback": "Arial, sans-serif"}, "serif"),
                         "'Inter', Arial, sans-serif")
        self.assertEqual(m.font_stack("Lora", "Georgia, serif"), "'Lora', Georgia, serif")
        self.assertEqual(m.font_stack(None, "Georgia, serif"), "Georgia, serif")

    def test_esc_escapes_markup_and_quotes_and_blanks_none(self):
        self.assertEqual(m.esc('<b>"x"</b>'), "&lt;b&gt;&quot;x&quot;&lt;/b&gt;")
        self.assertEqual(m.esc(None), "")

    def test_data_uri_embeds_image_and_rejects_non_image(self):
        import contextlib
        import io
        mod = load(SKILL, SCRIPT)
        with workdir() as d, contextlib.redirect_stderr(io.StringIO()):
            uri = mod.data_uri(png_file(d), "image")
            self.assertTrue(uri.startswith("data:image/png;base64,"))
            txt = write(os.path.join(d, "notes.txt"), "hi")
            self.assertIsNone(mod.data_uri(txt, "image"))
            self.assertIsNone(mod.data_uri(os.path.join(d, "missing.png"), "image"))
            self.assertEqual(len(mod.WARNINGS), 2)

    def test_export_without_chrome_says_print_from_browser(self):
        import contextlib
        import io
        mod = load(SKILL, SCRIPT)
        mod.chrome = lambda: None
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.export("flyer.html", "letter", pdf="flyer.pdf")
        self.assertIn("No Chrome or Chromium found", buf.getvalue())

    def test_export_png_landscape_swaps_window_size(self):
        import contextlib
        import io
        import types
        mod = load(SKILL, SCRIPT)
        calls = []
        mod.chrome = lambda: "chrome"
        mod.subprocess = types.SimpleNamespace(run=lambda cmd, **kw: calls.append(cmd))
        with workdir() as d, contextlib.redirect_stdout(io.StringIO()):
            mod.export(os.path.join(d, "f.html"), "story", png=os.path.join(d, "f.png"),
                       landscape=True)
        self.assertEqual(len(calls), 1)
        self.assertIn("--window-size=1920,1080", calls[0])


class BuildFlyerCliTests(unittest.TestCase):
    def test_minimal_spec_builds_html_with_defaults_and_warns_no_brand(self):
        with workdir() as d:
            code, out, err, html = build(d)
            self.assertEqual(code, 0)
            self.assertIn("<h1>Free community health fair</h1>", html)
            self.assertIn("@page { size: 8.5in 11in", html)
            self.assertIn("#1A2A6C", html)
            self.assertIn("no brand supplied", err)
            self.assertIn("contrast: text 15.9:1", out)
            self.assertIn("(hero, letter;", out)

    def test_default_output_path_is_spec_with_html_suffix(self):
        with workdir() as d:
            spec = spec_file(d)
            code, _, _ = run(SKILL, SCRIPT, spec, cwd=d)
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(os.path.join(d, "spec.html")))

    def test_a4_landscape_swaps_page_dimensions(self):
        with workdir() as d:
            _, out, _, html = build(d, size="A4", orientation="landscape")
            self.assertIn("@page { size: 297mm 210mm", html)
            self.assertIn("a4, landscape", out)

    def test_square_size_uses_px_units_scaled(self):
        with workdir() as d:
            _, _, _, html = build(d, size="square")
            self.assertIn("font-size: 54.0px", html)  # h1: 40 * 1.35

    def test_unknown_size_and_layout_fall_back_with_warnings(self):
        with workdir() as d:
            code, out, err, _ = build(d, size="tabloid", layout="mosaic")
            self.assertEqual(code, 0)
            self.assertIn("unknown size 'tabloid'", err)
            self.assertIn("unknown layout 'mosaic'", err)
            self.assertIn("(hero, letter;", out)

    def test_event_layout_puts_first_detail_in_date_block(self):
        with workdir() as d:
            details = [{"label": "When", "value": "Sat 14 Nov"},
                       {"label": "Where", "value": "Riverside pavilion"}]
            _, _, _, html = build(d, layout="event", details=details)
            self.assertIn('<div class="date"><span>When</span><b>Sat 14 Nov</b></div>', html)
            self.assertEqual(html.count("Sat 14 Nov"), 1)
            self.assertIn("<b>Riverside pavilion</b>", html)

    def test_copy_budget_warnings_and_points_capped_at_four(self):
        with workdir() as d:
            code, out, err, html = build(
                d, headline="one two three four five six seven eight nine ten eleven",
                points=["p1", "p2", "p3", "p4", "p5"], body="word " * 61)
            self.assertEqual(code, 0)
            self.assertIn("headline is 11 words", err)
            self.assertIn("5 points", err)
            self.assertIn("body is 61 words", err)
            self.assertIn("<li>p4</li>", html)
            self.assertNotIn("<li>p5</li>", html)
            self.assertIn("warning(s)", out)

    def test_cta_list_uses_first_and_warns(self):
        with workdir() as d:
            _, _, err, html = build(d, cta=[{"text": "Register"}, {"text": "Learn more"}])
            self.assertIn("more than one call to action", err)
            self.assertIn("<b>Register</b>", html)
            self.assertNotIn("Learn more", html)

    def test_missing_cta_warns(self):
        with workdir() as d:
            _, _, err, html = build(d, cta=None)
            self.assertIn("no call to action", err)
            self.assertNotIn('class="cta"', html)

    def test_text_is_html_escaped(self):
        with workdir() as d:
            _, _, _, html = build(d, headline="Fish & <chips>")
            self.assertIn("Fish &amp; &lt;chips&gt;", html)
            self.assertNotIn("<chips>", html)

    def test_image_is_embedded_and_missing_alt_warned(self):
        with workdir() as d:
            png_file(d)
            _, _, err, html = build(d, image={"path": "pic.png"})
            self.assertIn("background-image:url(data:image/png;base64,", html)
            self.assertIn("image has no alt text", err)

    def test_missing_image_warns_and_still_builds(self):
        with workdir() as d:
            code, _, err, html = build(d, image={"path": "gone.jpg", "alt": "x"})
            self.assertEqual(code, 0)
            self.assertIn("image not found", err)
            self.assertNotIn('class="img"', html)

    def test_brand_file_colours_logo_name_and_contact(self):
        with workdir() as d:
            png_file(d, "logo.png")
            write(os.path.join(d, "brand.json"), json.dumps({
                "name": "Northwind Example", "colors": {"primary": "#0B5D3B"},
                "logo": {"primary": "logo.png"},
                "contact": {"website": "northwind.example.org", "phone": "", "fax": "000"},
                "legal": {"footer": "(c) Example Ltd"}}))
            code, out, err, html = build(d, "--brand", "brand.json")
            self.assertEqual(code, 0)
            self.assertIn("background: #0B5D3B", html)
            self.assertIn('<img class="logo" src="data:image/png;base64,', html)
            self.assertIn('alt="Northwind Example"', html)
            self.assertIn("<span>northwind.example.org</span>", html)
            self.assertNotIn("000", html.split("<footer")[1])
            self.assertIn("(c) Example Ltd", html)
            self.assertIn("brand: yes; logo: yes", out)
            self.assertNotIn("no brand supplied", err)

    def test_cli_brand_overrides_spec_brand_and_spec_colours_override_both(self):
        with workdir() as d:
            write(os.path.join(d, "cli.json"), json.dumps({"colors": {"primary": "#AA0000"}}))
            _, _, _, html = build(d, "--brand", "cli.json",
                                  brand={"colors": {"primary": "#00AA00"}},
                                  colors={"accent": "#333333"})
            self.assertIn("background: #AA0000", html)
            self.assertNotIn("#00AA00", html)
            self.assertIn("background: #333333", html)

    def test_no_logo_sets_brand_name_as_wordmark(self):
        with workdir() as d:
            _, _, err, html = build(d, brand={"name": "Example Co"})
            self.assertIn('<span class="wordmark">Example Co</span>', html)
            self.assertIn("no logo", err)

    def test_missing_brand_file_warns_and_uses_defaults(self):
        with workdir() as d:
            code, _, err, html = build(d, brand="./brand/brand.json")
            self.assertEqual(code, 0)
            self.assertIn("brand file not found", err)
            self.assertIn("#1A2A6C", html)

    def test_low_text_contrast_is_an_error(self):
        with workdir() as d:
            code, _, err, html = build(d, colors={"text": "#BBBBBB"})
            self.assertEqual(code, 1)
            self.assertIn("below 4.5:1", err)
            self.assertIsNone(html)

    def test_non_hex_colour_is_an_error(self):
        with workdir() as d:
            code, _, err, _ = build(d, colors={"primary": "navy"})
            self.assertEqual(code, 1)
            self.assertIn("not a 6-digit hex code", err)

    def test_missing_headline_is_an_error(self):
        with workdir() as d:
            code, _, err, html = build(d, headline="")
            self.assertEqual(code, 1)
            self.assertIn("spec needs a headline", err)
            self.assertIsNone(html)

    def test_missing_and_malformed_spec_fail_clearly(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "none.json"))
            self.assertEqual(code, 1)
            self.assertIn("cannot read", err)
            bad = write(os.path.join(d, "bad.json"), "{not json")
            code, _, err = run(SKILL, SCRIPT, bad)
            self.assertEqual(code, 1)
            self.assertIn("cannot read", err)
            self.assertNotIn("Traceback", err)

    # BUG: a string "image" path is accepted for embedding, then img.get("alt") raises AttributeError.
    @unittest.expectedFailure
    def test_image_given_as_plain_path_string_builds(self):
        with workdir() as d:
            png_file(d)
            code, _, err, html = build(d, image="pic.png")
            self.assertEqual(code, 0, err)
            self.assertIn("data:image/png;base64,", html)

    # BUG: a string "cta" (e.g. "Book now") crashes with AttributeError instead of failing clearly.
    @unittest.expectedFailure
    def test_cta_given_as_string_does_not_traceback(self):
        with workdir() as d:
            _, _, err, _ = build(d, cta="Book now")
            self.assertNotIn("Traceback", err)

    # BUG: a spec whose JSON is not an object (e.g. a list) crashes with AttributeError.
    @unittest.expectedFailure
    def test_spec_that_is_not_an_object_fails_clearly(self):
        with workdir() as d:
            p = write(os.path.join(d, "list.json"), "[1, 2]")
            code, _, err = run(SKILL, SCRIPT, p)
            self.assertEqual(code, 1)
            self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

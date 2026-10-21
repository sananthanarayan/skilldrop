import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "brand-kit", "check_brand.py"

GOOD = {
    "name": "Example Co",
    "logo": {"primary": "logo.png", "on_dark": "logo-white.png"},
    "colors": {"primary": "#0E5A46", "secondary": "#3D7F6B", "accent": "#B5531A",
               "background": "#FFFFFF", "text": "#1F2A28",
               "extra": [{"name": "Mist", "hex": "#E8F1EE"}]},
    "fonts": {"heading": {"family": "Georgia"}, "body": "Arial"},
    "templates": {"pptx": "master.potx"},
}


def brand_dir(d, brand, files=("logo.png", "logo-white.png", "master.potx")):
    for f in files:
        write(os.path.join(d, f), "placeholder")
    return write(os.path.join(d, "brand.json"), json.dumps(brand))


def with_changes(**changes):
    b = json.loads(json.dumps(GOOD))
    for key, value in changes.items():
        section, _, field = key.partition("__")
        if field:
            b[section][field] = value
        else:
            b[section] = value
    return b


class CheckBrandContrastTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_luminance_of_white_and_black(self):
        self.assertAlmostEqual(self.m.luminance("#FFFFFF"), 1.0)
        self.assertAlmostEqual(self.m.luminance("#000000"), 0.0)

    def test_black_on_white_is_21_to_1_either_way_round(self):
        self.assertAlmostEqual(self.m.contrast("#000000", "#FFFFFF"), 21.0)
        self.assertAlmostEqual(self.m.contrast("#FFFFFF", "#000000"), 21.0)

    def test_grey_767676_passes_aa_and_777777_does_not(self):
        self.assertAlmostEqual(self.m.contrast("#767676", "#FFFFFF"), 4.54, places=2)
        self.assertAlmostEqual(self.m.contrast("#777777", "#ffffff"), 4.48, places=2)


class CheckBrandCliTest(unittest.TestCase):
    def check(self, brand, files=("logo.png", "logo-white.png", "master.potx")):
        with workdir() as d:
            path = brand_dir(d, brand, files)
            return run(SKILL, SCRIPT, path)

    def test_complete_brand_passes_with_no_warnings(self):
        code, out, _ = self.check(GOOD)
        self.assertEqual(code, 0, out)
        self.assertIn("OK: brand.json — 0 failure(s), 0 warning(s)", out)
        self.assertIn("text on background", out)

    def test_malformed_hex_fails(self):
        code, out, _ = self.check(with_changes(colors__primary="#0E5A4"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL colors.primary is '#0E5A4', not a 6-digit hex code", out)

    def test_malformed_extra_colour_fails(self):
        code, out, _ = self.check(with_changes(colors__extra=[{"name": "Mist", "hex": "E8F1EE"}]))
        self.assertEqual(code, 1)
        self.assertIn("FAIL colors.extra 'Mist' has hex 'E8F1EE'", out)

    def test_text_contrast_below_4_5_fails(self):
        code, out, _ = self.check(with_changes(colors__text="#777777"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL text on background contrast is 4.48:1, below 4.5:1", out)

    def test_text_contrast_just_above_4_5_passes(self):
        code, out, _ = self.check(with_changes(colors__text="#767676"))
        self.assertEqual(code, 0, out)

    def test_pale_primary_only_warns_about_white_text(self):
        code, out, _ = self.check(with_changes(colors__primary="#FFE680"))
        self.assertEqual(code, 0)
        self.assertIn("WARN white text on primary is", out)

    def test_pale_accent_warns_to_keep_it_off_text(self):
        code, out, _ = self.check(with_changes(colors__accent="#FFE680"))
        self.assertEqual(code, 0)
        self.assertIn("WARN accent on background is", out)

    def test_missing_colour_roles_warn_but_pass(self):
        code, out, _ = self.check(with_changes(colors={"primary": "#0E5A46"}))
        self.assertEqual(code, 0)
        for role in ("secondary", "accent", "background", "text"):
            self.assertIn("WARN colors.{} is missing".format(role), out)

    def test_missing_logo_file_fails(self):
        code, out, _ = self.check(GOOD, files=("logo.png", "master.potx"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL logo.on_dark 'logo-white.png' does not exist", out)

    def test_svg_logo_warns_that_powerpoint_needs_png(self):
        code, out, _ = self.check(with_changes(logo="logo.svg"), files=("logo.svg", "master.potx"))
        self.assertEqual(code, 0)
        self.assertIn("WARN logo.primary is .svg", out)
        self.assertIn("PowerPoint needs PNG or JPG", out)

    def test_logo_as_a_plain_string_and_jpeg_are_accepted(self):
        code, out, _ = self.check(with_changes(logo="logo.JPEG"), files=("logo.JPEG", "master.potx"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("WARN logo", out)

    def test_no_logo_warns_brand_name_as_text(self):
        brand = with_changes()
        del brand["logo"]
        code, out, _ = self.check(brand)
        self.assertEqual(code, 0)
        self.assertIn("WARN no logo file", out)

    def test_missing_template_fails(self):
        code, out, _ = self.check(GOOD, files=("logo.png", "logo-white.png"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL templates.pptx 'master.potx' does not exist", out)

    def test_unset_fonts_warn(self):
        code, out, _ = self.check(with_changes(fonts={"heading": {"family": ""}}))
        self.assertEqual(code, 0)
        self.assertIn("WARN fonts.heading is not set", out)
        self.assertIn("WARN fonts.body is not set", out)

    def test_relative_paths_resolve_from_the_brand_file_not_the_cwd(self):
        with workdir() as d, workdir() as elsewhere:
            path = brand_dir(os.path.join(d, "brand"), GOOD)
            code, out, _ = run(SKILL, SCRIPT, path, cwd=elsewhere)
        self.assertEqual(code, 0, out)

    def test_missing_brand_file_fails_clearly(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, os.path.join(d, "nope.json"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL cannot read", out)
        self.assertNotIn("Traceback", err)

    def test_invalid_json_fails_clearly(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "brand.json"), "{colors:"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL cannot read", out)
        self.assertNotIn("Traceback", err)

    def test_wrong_argument_count_prints_usage_and_exits_2(self):
        code, out, _ = run(SKILL, SCRIPT)
        self.assertEqual(code, 2)
        self.assertIn("Usage:", out)

    # BUG: a brand.json saved as Windows-1252/Latin-1 raises UnicodeDecodeError (not caught) with a traceback.
    @unittest.expectedFailure
    def test_non_utf8_brand_file_fails_clearly(self):
        with workdir() as d:
            path = os.path.join(d, "brand.json")
            with open(path, "wb") as f:
                f.write('{"legal": {"footer": "© 2026 Example Co"}}'.encode("latin-1"))
            code, out, err = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 1)
        self.assertIn("FAIL cannot read", out)
        self.assertNotIn("Traceback", err)

    # BUG: a top-level JSON array crashes with AttributeError ('list' object has no attribute 'get').
    @unittest.expectedFailure
    def test_non_object_brand_file_fails_clearly(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, write(os.path.join(d, "brand.json"), "[]"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)
        self.assertNotIn("Traceback", err)

    # BUG: a non-string colour value ({"primary": 123}) crashes in HEX.match with TypeError.
    @unittest.expectedFailure
    def test_non_string_colour_fails_as_malformed_hex(self):
        code, out, err = self.check(with_changes(colors__primary=123))
        self.assertEqual(code, 1)
        self.assertIn("FAIL colors.primary is 123", out)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()

import json
import os
import unittest

from tests.support import load, run, workdir, write

SKILL, SCRIPT = "locale-check", "locale_check.py"


def problems(rows):
    return [(r["locale"], r["key"], r["problem"]) for r in rows]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def check(self, files, *extra):
        """Write {relative path: text}; run source then targets; return (code, report)."""
        with workdir() as d:
            paths = []
            for rel, text in files.items():
                p = os.path.join(d, *rel.split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                if isinstance(text, bytes):
                    with open(p, "wb") as fh:
                        fh.write(text)
                else:
                    write(p, text)
                paths.append(p)
            extra = [x.replace("{d}", d) for x in extra]
            code, out, err = run(SKILL, SCRIPT, *paths, "--json", *extra)
            return code, (json.loads(out) if out.strip() else {"stderr": err})


class FormatsTest(Base):
    def test_nested_json_with_i18next_plurals(self):
        code, r = self.check({
            "en.json": '{"cart": {"items_one": "{{count}} item", "items_other": "{{count}} items", "t": "Cart"}}',
            "de.json": '{"cart": {"items_one": "{{count}} Artikel", "items_other": "{{count}} Artikel", "t": "Warenkorb"}}'})
        self.assertEqual(code, 0, r)
        self.assertEqual(r["targets"][0]["locale"], "de")
        self.assertEqual(r["targets"][0]["strings"], 2)  # the plural pair is one string

    def test_arb_skips_metadata_and_reads_its_locale(self):
        code, r = self.check({
            "app_en.arb": '{"@@locale": "en", "hi": "Hi {name}", "@hi": {"placeholders": {"name": {}}}}',
            "app_xx.arb": '{"@@locale": "fr", "hi": "Salut"}'})
        self.assertEqual(code, 1)
        self.assertEqual(r["targets"][0]["locale"], "fr")
        self.assertIn(("fr", "hi", "placeholders differ: missing {name}"), problems(r["failures"]))

    def test_po_against_a_pot_with_plurals_and_context(self):
        pot = 'msgctxt "menu"\nmsgid "Open"\nmsgstr ""\n\nmsgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] ""\nmsgstr[1] ""\n'
        po = ('msgid ""\nmsgstr ""\n"Language: pl\\n"\n"Plural-Forms: nplurals=3;\\n"\n\n'
              'msgctxt "menu"\nmsgid "Open"\nmsgstr "Otwórz"\n\n'
              'msgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] "%d plik"\nmsgstr[1] "%d pliki"\nmsgstr[2] "%d plików"\n')
        code, r = self.check({"messages.pot": pot, "pl.po": po})
        self.assertEqual(code, 0, r)
        self.assertEqual(r["targets"][0]["locale"], "pl")

    def test_android_strings_plurals_and_arrays(self):
        src = ('<resources><string name="hi">Hi %1$s</string>'
               '<plurals name="n"><item quantity="one">%d day</item><item quantity="other">%d days</item></plurals>'
               '<string-array name="days"><item>Mon</item><item>Tue</item></string-array>'
               '<string name="brand" translatable="false">Acme</string></resources>')
        tgt = ('<resources><string name="hi">Cześć %1$s</string>'
               '<plurals name="n"><item quantity="one">%d dzień</item><item quantity="few">%d dni</item>'
               '<item quantity="many">%d dni</item><item quantity="other">%d dnia</item></plurals>'
               '<string-array name="days"><item>Pon</item></string-array></resources>')
        code, r = self.check({"values/strings.xml": src, "values-pl/strings.xml": tgt})
        self.assertEqual(code, 1)
        self.assertEqual(r["targets"][0]["locale"], "pl")
        self.assertIn(("pl", "days[1]", "missing"), problems(r["failures"]))
        self.assertNotIn("brand", [k for _, k, _ in problems(r["failures"])])

    def test_android_unescaped_apostrophe_breaks_the_build(self):
        code, r = self.check({"values/strings.xml": '<resources><string name="t">Time</string></resources>',
                              "values-fr/strings.xml": "<resources><string name=\"t\">L'heure</string></resources>"})
        self.assertEqual(code, 1)
        self.assertTrue(any("apostrophe" in p for _, _, p in problems(r["failures"])))

    def test_ios_strings_in_utf16_with_comments(self):
        src = '/* Greeting */\n"bye" = "Goodbye, %@.";\n// a note\n"ok" = "OK";\n'
        tgt = '"bye" = "Au revoir, %@.";\n"ok" = "OK";\n'
        code, r = self.check({"en.lproj/Localizable.strings": src,
                              "fr.lproj/Localizable.strings": b"\xff\xfe" + tgt.encode("utf-16-le")})
        self.assertEqual(code, 0, r)
        self.assertEqual(r["targets"][0]["locale"], "fr")

    def test_stringsdict_plural_rules(self):
        def doc(one, other, extra=""):
            return ('<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>files</key><dict>'
                    '<key>NSStringLocalizedFormatKey</key><string>%#@n@</string><key>n</key><dict>'
                    '<key>NSStringFormatSpecTypeKey</key><string>NSStringPluralRuleType</string>'
                    '<key>NSStringFormatValueTypeKey</key><string>d</string>'
                    '<key>one</key><string>' + one + '</string>' + extra +
                    '<key>other</key><string>' + other + '</string></dict></dict></dict></plist>')
        code, r = self.check({"en.lproj/Localizable.stringsdict": doc("%d file", "%d files"),
                              "ru.lproj/Localizable.stringsdict": doc("%d файл", "%d файла")})
        self.assertEqual(code, 1)
        self.assertTrue(any(k == "files#n" and "few, many missing" in p for _, k, p in problems(r["failures"])))

    def test_a_target_that_does_not_parse_is_a_failure_not_a_crash(self):
        code, r = self.check({"en.json": '{"a": "A"}', "de.json": '{"a": "A",'})
        self.assertEqual(code, 1)
        self.assertEqual(r["failures"][0]["key"], "(file)")


class FailuresTest(Base):
    def test_missing_and_empty_keys(self):
        code, r = self.check({"en.json": '{"a": "Save", "b": "Cancel"}', "es.json": '{"a": ""}'})
        self.assertEqual(code, 1)
        self.assertEqual(sorted(p for _, _, p in problems(r["failures"])), ["empty translation", "missing"])

    def test_printf_reordered_types_changed_and_dropped(self):
        code, r = self.check({"en.json": '{"m": "%s sent %d files", "n": "Hi %1$s, %2$d new"}',
                              "fr.json": '{"m": "%d fichiers envoyés par %s", "n": "%2$d nouveaux, %1$s"}'})
        found = problems(r["failures"])
        self.assertEqual(code, 1)
        self.assertEqual([k for _, k, _ in found], ["m"])      # positional reordering is fine
        fix = r["failures"][0].get("fix", "")
        self.assertEqual(fix, "use %2$d fichiers envoyés par %1$s")

    def test_brace_placeholders_count_and_fix(self):
        code, r = self.check({"en.json": '{"g": "{name} invited {name2}"}', "it.json": '{"g": "{name} ha invitato"}'})
        self.assertEqual(code, 1)
        self.assertEqual(r["failures"][0]["fix"], "restore {name2}")

    def test_icu_that_does_not_parse(self):
        code, r = self.check({"en.json": '{"f": "{n, plural, one {# file} other {# files}}"}',
                              "de.json": '{"f": "{n, plural, one {# Datei} other {# Dateien}"}'})
        self.assertEqual(code, 1)
        self.assertIn("ICU message doesn't parse", r["failures"][0]["problem"])

    def test_icu_select_keyword_translated(self):
        code, r = self.check({"en.json": '{"w": "{g, select, male {He} female {She} other {They}}"}',
                              "fr.json": '{"w": "{g, select, masculin {Il} female {Elle} other {Iels}}"}'})
        self.assertIn("lost keyword male", r["failures"][0]["problem"])

    def test_markup_tags(self):
        code, r = self.check({"en.json": '{"a": "Read <b>the terms</b> or <1>call us</1>."}',
                              "de.json": '{"a": "Lesen Sie <b>die Bedingungen</b> oder <1>rufen Sie an."}'})
        self.assertEqual(code, 1)
        self.assertIn("markup differs", r["failures"][0]["problem"])
        code, r = self.check({"en.json": '{"a": "<b>x</b> <i>y</i>"}', "de.json": '{"a": "<b>x <i>y</b></i>"}'})
        self.assertIn("don't nest", r["failures"][0]["problem"])

    def test_budget_per_key_and_ratio(self):
        code, r = self.check({"en.json": '{"pay": "Pay now", "desc": "Your order ships in two days"}',
                              "de.json": '{"pay": "Jetzt bezahlen", "desc": "Ihre Bestellung wird in zwei Tagen versandt"}',
                              "budget.json": '{"keys": {"pay": 10}, "ratio": 1.3}'},
                             "--budget", "{d}/budget.json")
        # the budget file is also passed as a target by check(); ignore that row
        rows = [x for x in problems(r["failures"]) if x[0] == "de" and x[1] in ("pay", "desc")]
        self.assertEqual(sorted(k for _, k, _ in rows), ["desc", "pay"])
        self.assertTrue(r["lengths_checked"])

    def test_no_budget_says_lengths_were_not_checked(self):
        with workdir() as d:
            write(os.path.join(d, "en.json"), '{"a": "Save"}')
            write(os.path.join(d, "de.json"), '{"a": "Speichern"}')
            code, out, _ = run(SKILL, SCRIPT, os.path.join(d, "en.json"), os.path.join(d, "de.json"))
        self.assertEqual(code, 0)
        self.assertIn("lengths were not checked", out)


class PluralRulesTest(Base):
    def plural(self, locale, forms):
        tgt = {"items_" + c: "{{count}} x" for c in forms}
        return self.check({"en.json": '{"items_one": "{{count}} item", "items_other": "{{count}} items"}',
                           locale + ".json": json.dumps(tgt)})

    def test_arabic_needs_six(self):
        code, r = self.plural("ar", ["one", "other"])
        self.assertIn("zero, two, few, many missing", r["failures"][0]["problem"])
        code, r = self.plural("ar", ["zero", "one", "two", "few", "many", "other"])
        self.assertEqual(code, 0, r)

    def test_polish_needs_few_and_many(self):
        code, r = self.plural("pl", ["one", "other"])
        self.assertIn("few, many missing", r["failures"][0]["problem"])

    def test_french_many_is_a_warning_only(self):
        code, r = self.plural("fr", ["one", "other"])
        self.assertEqual(code, 0)
        self.assertIn("'many' missing", r["warnings"][0]["problem"])

    def test_japanese_needs_only_other_and_one_is_unused(self):
        code, r = self.plural("ja", ["other"])
        self.assertEqual(code, 0, r)
        code, r = self.plural("ja", ["one", "other"])
        self.assertEqual(code, 0)
        self.assertIn("never used in ja", r["warnings"][0]["problem"])

    def test_icu_plural_categories_and_bad_keywords(self):
        code, r = self.check({"en.json": '{"f": "{n, plural, one {# file} other {# files}}"}',
                              "ru.json": '{"f": "{n, plural, one {# файл} few {# файла} lots {# файлов} other {# файла}}"}'})
        msgs = " / ".join(p for _, _, p in problems(r["failures"]))
        self.assertIn("missing many", msgs)
        self.assertIn("lots, which isn't a plural category", msgs)

    def test_gettext_nplurals(self):
        pot = 'msgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] ""\nmsgstr[1] ""\n'
        po = 'msgid ""\nmsgstr ""\n"Language: ar\\n"\n\nmsgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] "a"\nmsgstr[1] "b"\n'
        code, r = self.check({"m.pot": pot, "ar.po": po})
        self.assertIn("ar needs 6", r["failures"][0]["problem"])


class WarningsTest(Base):
    def test_identical_stale_space_punctuation_and_mixed_script(self):
        code, r = self.check({"en.json": '{"a": "Settings", "b": " Next", "c": "Saved.", "d": "Cancel"}',
                              "ru.json": '{"a": "Settings", "b": "Далее", "c": "Сохранено", "d": "Отмeна", "z": "?"}'})
        msgs = {k: p for _, k, p in problems(r["warnings"])}
        self.assertEqual(code, 0, r)
        self.assertIn("identical", msgs["a"])
        self.assertIn("space", msgs["b"])
        self.assertIn("punctuation", msgs["c"])
        self.assertIn("mixes", msgs["d"])
        self.assertIn("not in the source", msgs["z"])


class IcuParserTest(Base):
    def test_parses_nested_plural_select_and_quotes(self):
        args = self.m.icu_parse("{g, select, female {{n, plural, =0 {none} one {# item} other {# items}}} "
                                "other {'{'literal'}' {n, number}}}")
        self.assertEqual(sorted({(a, k) for a, k, _ in args}), [("g", "select"), ("n", "number"), ("n", "plural")])

    def test_rejects_broken_messages(self):
        for bad in ("{n, plural, one {# x}}", "{n, plural, one {# x} other {# y}", "{n, select other {x}}", "}"):
            with self.assertRaises(self.m.IcuError, msg=bad):
                self.m.icu_parse(bad)

    def test_locale_detection_from_paths(self):
        d = self.m.detect_locale
        self.assertEqual(d("/app/res/values-pt-rBR/strings.xml"), "pt-BR")
        self.assertEqual(d("/app/fr.lproj/Localizable.strings"), "fr")
        self.assertEqual(d("/app/locales/de/common.json"), "de")
        self.assertEqual(d("/app/l10n/app_ja.arb"), "ja")
        self.assertEqual(d("/app/i18n/zh-Hant.json"), "zh-Hant")


class ExitCodesTest(Base):
    def test_bad_input_exits_2(self):
        with workdir() as d:
            write(os.path.join(d, "en.json"), '{"a": "A"}')
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "missing.json"), os.path.join(d, "en.json"))
            self.assertEqual(code, 2)
            write(os.path.join(d, "en.txt"), "just text")
            code, _, err = run(SKILL, SCRIPT, os.path.join(d, "en.txt"), os.path.join(d, "en.json"))
            self.assertEqual(code, 2)
            self.assertIn("unknown format", err)
            write(os.path.join(d, "bad.json"), "{")
            code, _, _ = run(SKILL, SCRIPT, os.path.join(d, "bad.json"), os.path.join(d, "en.json"))
            self.assertEqual(code, 2)

    def test_markdown_output_to_a_file(self):
        with workdir() as d:
            write(os.path.join(d, "en.json"), '{"a": "Save"}')
            write(os.path.join(d, "de.json"), '{}')
            out = os.path.join(d, "report.md")
            code, stdout, _ = run(SKILL, SCRIPT, os.path.join(d, "en.json"), os.path.join(d, "de.json"), "-o", out)
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertIn("## Failures", open(out, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()

import base64
import hashlib
import os
import re
import unittest
from html.parser import HTMLParser

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "md-to-html", "md_to_html.py"

# a 1x1 PNG
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==")


def convert(d, md, *flags):
    """Write `md`, convert it, return (exit code, html, stdout, stderr)."""
    src = write(os.path.join(d, "doc.md"), md)
    out = os.path.join(d, "out.html")
    code, so, se = run(SKILL, SCRIPT, src, "-o", out, *flags)
    return code, (read(out) if os.path.exists(out) else ""), so, se


def main_of(page):
    return page.split("<main>", 1)[1].split("</main>", 1)[0].strip()


class TagBalance(HTMLParser):
    VOID = {"meta", "img", "br", "hr", "input", "link"}

    def __init__(self):
        HTMLParser.__init__(self)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag in ("ul", "ol") and self.stack and self.stack[-1] in ("ul", "ol"):
            self.errors.append("<%s> directly inside <%s>" % (tag, self.stack[-1]))
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("unexpected </%s>" % tag)
        else:
            self.stack.pop()


class MdToHtmlTest(unittest.TestCase):
    def test_page_is_one_self_contained_document_with_title_from_first_heading(self):
        with workdir() as d:
            code, page, so, se = convert(d, "# Ops review\n\nAll **green**.\n")
        self.assertEqual(code, 0, se)
        self.assertTrue(page.startswith("<!DOCTYPE html>\n<html lang=\"en\">"))
        self.assertIn("<title>Ops review</title>", page)
        self.assertIn("default-src 'none'", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<link", page)
        self.assertEqual(main_of(page), '<h1 id="ops-review">Ops review<a class="anchor" href="#ops-review" '
                                        'aria-hidden="true">#</a></h1>\n<p>All <strong>green</strong>.</p>')
        self.assertIn("1 headings, 0 tables, 0 code blocks", so)

    def test_heading_anchors_are_stable_and_duplicates_get_a_suffix(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "## Rollout plan!\n\n## Rollout plan\n\n### `cfg` & *flags*\n")
        ids = re.findall(r'<h\d id="([^"]+)"', page)
        self.assertEqual(ids, ["rollout-plan", "rollout-plan-1", "cfg-flags"])

    def test_inline_emphasis_strike_code_and_snake_case(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "**b** *i* ~~s~~ `a*b* <x>` max_retry_count\n")
        self.assertEqual(main_of(page), "<p><strong>b</strong> <em>i</em> <del>s</del> "
                                        "<code>a*b* &lt;x&gt;</code> max_retry_count</p>")

    def test_links_autolinks_and_bare_urls_are_escaped_anchors(self):
        md = "[Guide](https://example.test/?a=1&b=2 \"The guide\"), <https://example.test/x>, https://example.test/y.\n"
        with workdir() as d:
            _, page, _, _ = convert(d, md)
        body = main_of(page)
        self.assertIn('<a href="https://example.test/?a=1&amp;b=2" title="The guide">Guide</a>', body)
        self.assertIn('<a href="https://example.test/x">https://example.test/x</a>', body)
        self.assertIn('<a href="https://example.test/y">https://example.test/y</a>.', body)

    def test_unsafe_link_targets_are_dropped_with_a_warning(self):
        with workdir() as d:
            _, page, _, se = convert(d, "[a](javascript:alert(1)) [b](JavaScript:x) [c](data:text/html,x)\n")
        self.assertEqual(main_of(page), "<p>a b c</p>")
        self.assertIn("warning: dropped an unsafe link target: javascript:alert(1)", se)
        self.assertIn("warning: dropped an unsafe link target: data:text/html,x", se)

    def test_raw_html_is_escaped_by_default_and_passed_with_allow_html(self):
        md = "<div onclick=\"x()\">\n<script>alert(1)</script>\n</div>\n\nInline <b>tag</b>.\n"
        with workdir() as d:
            _, safe, _, se = convert(d, md)
            _, raw, _, se2 = convert(d, md, "--allow-html")
        self.assertNotIn("<script>", main_of(safe))
        self.assertIn('<pre class="raw-html">&lt;div onclick=&quot;x()&quot;&gt;', safe)
        self.assertIn("<p>Inline &lt;b&gt;tag&lt;/b&gt;.</p>", safe)
        self.assertIn("raw HTML found and shown as text (2 place(s))", se)
        self.assertIn('<div onclick="x()">\n<script>alert(1)</script>\n</div>', raw)
        self.assertIn("<p>Inline &lt;b&gt;tag&lt;/b&gt;.</p>", raw)  # inline HTML stays escaped
        self.assertNotIn("raw HTML found", se2)

    def test_lists_ordered_start_nesting_and_tasks(self):
        md = "3. three\n4. four\n   - sub\n\n- [ ] open\n- [x] done\n"
        with workdir() as d:
            _, page, _, _ = convert(d, md)
        self.assertEqual(main_of(page),
                         '<ol start="3">\n<li>three</li>\n<li>four\n<ul>\n<li>sub</li>\n</ul></li>\n</ol>\n'
                         '<ul>\n<li class="task"><input type="checkbox" disabled> open</li>\n'
                         '<li class="task"><input type="checkbox" disabled checked> done</li>\n</ul>')

    def test_loose_list_items_get_paragraphs(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "- one\n\n- two\n")
        self.assertEqual(main_of(page), "<ul>\n<li><p>one</p></li>\n<li><p>two</p></li>\n</ul>")

    def test_table_alignment_padding_and_escaped_pipe(self):
        md = "| Region | Tickets | Note |\n|:--|--:|:-:|\n| North \\| East | 120 |\n"
        with workdir() as d:
            _, page, so, _ = convert(d, md)
        self.assertEqual(main_of(page),
                         '<div class="table-wrap"><table><thead><tr><th style="text-align:left">Region</th>'
                         '<th style="text-align:right">Tickets</th><th style="text-align:center">Note</th>'
                         '</tr></thead><tbody><tr><td style="text-align:left">North | East</td>'
                         '<td style="text-align:right">120</td><td style="text-align:center"></td></tr>'
                         '</tbody></table></div>')
        self.assertIn("1 tables", so)

    def test_fenced_and_indented_code_are_escaped_with_language_class(self):
        with workdir() as d:
            _, page, so, _ = convert(d, "```python\nif a < b:\n    pass\n```\n\n    raw <b>\n")
        self.assertEqual(main_of(page), '<pre><code class="language-python">if a &lt; b:\n    pass</code></pre>\n'
                                        '<pre><code>raw &lt;b&gt;</code></pre>')
        self.assertIn("2 code blocks", so)

    def test_blockquote_hr_and_hard_break(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "> quoted\n> more\n\n---\n\nline one  \nline two\n")
        self.assertEqual(main_of(page), "<blockquote><p>quoted\nmore</p></blockquote>\n<hr>\n"
                                        "<p>line one<br>\nline two</p>")

    def test_local_image_is_embedded_as_data_uri(self):
        with workdir() as d:
            os.makedirs(os.path.join(d, "img"))
            with open(os.path.join(d, "img", "dot.png"), "wb") as f:
                f.write(PNG)
            _, page, so, se = convert(d, '![A dot](img/dot.png "Dot")\n')
        self.assertIn('<img src="data:image/png;base64,%s" alt="A dot" title="Dot">'
                      % base64.b64encode(PNG).decode("ascii"), page)
        self.assertIn("1 images embedded, 0 remote, 0 missing", so)
        self.assertEqual(se, "")

    def test_remote_missing_and_non_image_files_are_reported(self):
        with workdir() as d:
            write(os.path.join(d, "notes.txt"), "x")
            _, page, so, se = convert(d, "![r](https://example.test/r.png) ![m](gone.png) ![t](notes.txt)\n")
        self.assertIn('<img src="https://example.test/r.png" alt="r">', page)
        self.assertIn('<span class="missing-img">[image not found: m]</span>', page)
        self.assertIn('<span class="missing-img">[not an image: t]</span>', page)
        self.assertIn("0 images embedded, 1 remote, 2 missing", so)
        self.assertIn("remote image left as a link (it will not show offline): https://example.test/r.png", se)
        self.assertIn("image not found, alt text shown instead: gone.png", se)
        self.assertIn("not an image file, skipped: notes.txt", se)

    def test_toc_lists_h2_and_h3_after_the_h1(self):
        md = "# Guide\n\n## Setup\n\n### Install\n\n## Use\n\n#### Deep\n"
        with workdir() as d:
            _, page, _, _ = convert(d, md, "--toc")
        body = main_of(page)
        toc = ('<nav class="toc" aria-label="Contents"><p>Contents</p><ul><li><a href="#setup">Setup</a>'
               '<ul><li><a href="#install">Install</a></li></ul></li><li><a href="#use">Use</a></li></ul></nav>')
        self.assertIn("</h1>\n" + toc + "\n<h2", body)
        self.assertNotIn("#deep\">", toc)

    def test_toc_without_section_headings_warns(self):
        with workdir() as d:
            _, page, _, se = convert(d, "# Only a title\n\nText.\n", "--toc")
        self.assertNotIn('<nav class="toc"', page)
        self.assertIn("--toc asked for, but the document has no level-2 or level-3 headings", se)

    # BUG: a ### before the first ## gives <ul><ul> and a stray </li> in the table of contents
    @unittest.expectedFailure
    def test_toc_is_well_formed_when_an_h3_comes_before_any_h2(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "### Note\n\n## Setup\n", "--toc")
        nav = re.search(r'<nav class="toc".*?</nav>', page).group(0)
        checker = TagBalance()
        checker.feed(nav)
        self.assertEqual(checker.errors, [])
        self.assertEqual(checker.stack, [])

    def test_mermaid_kept_as_text_by_default_with_warning(self):
        with workdir() as d:
            _, page, so, se = convert(d, "```mermaid\ngraph TD; A-->B\n```\n")
        self.assertIn('<pre class="mermaid">graph TD; A--&gt;B</pre>', page)
        self.assertNotIn("<script", page)
        self.assertIn("1 Mermaid", so)
        self.assertIn("1 Mermaid diagram(s) kept as text; use --mermaid cdn", se)

    def test_mermaid_cdn_adds_one_pinned_script_allowed_by_its_csp_hash(self):
        with workdir() as d:
            _, page, _, se = convert(d, "```mermaid\ngraph TD; A-->B\n```\n", "--mermaid", "cdn")
        scripts = re.findall(r'<script type="module">(.*?)</script>', page, re.S)
        self.assertEqual(len(scripts), 1)
        self.assertIn("https://cdn.jsdelivr.net/npm/mermaid@11.4.1/", scripts[0])
        digest = base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode("ascii")
        self.assertIn("script-src 'sha256-%s' https://cdn.jsdelivr.net;" % digest, page)
        self.assertNotIn("kept as text", se)

    def test_mermaid_cdn_without_diagrams_adds_no_script(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "Text only.\n", "--mermaid", "cdn")
        self.assertNotIn("<script", page)
        self.assertNotIn("script-src", page)

    def test_brand_colours_fonts_logo_and_footer(self):
        brand = ('{"name": "Riverside Survey", "colors": {"primary": "#0A7F3C", "accent": "orange"},'
                 ' "fonts": {"heading": {"family": "Merri;weather", "fallback": "serif"}},'
                 ' "logo": {"primary": "logo.png"}, "legal": {"footer": "\\u00a9 Riverside <Survey>"}}')
        with workdir() as d:
            with open(os.path.join(d, "logo.png"), "wb") as f:
                f.write(PNG)
            bp = write(os.path.join(d, "brand.json"), brand)
            code, page, _, se = convert(d, "Body only.\n", "--brand", bp)
        self.assertEqual(code, 0, se)
        self.assertIn("--primary:#0A7F3C;", page)
        self.assertIn("--accent:#C8553D;", page)  # bad hex keeps the default
        self.assertIn("font-family:'Merriweather', serif", page)
        self.assertIn('<header class="brand"><img src="data:image/png;base64,', page)
        self.assertIn("<footer>\u00a9 Riverside &lt;Survey&gt;</footer>", page)
        self.assertIn("<title>Riverside Survey</title>", page)  # no heading: the brand name
        self.assertIn("brand colour accent='orange' is not a hex code; using the default", se)

    def test_missing_or_invalid_brand_file_fails_clearly(self):
        with workdir() as d:
            bad = write(os.path.join(d, "bad.json"), "{nope")
            c1, _, _, e1 = convert(d, "x\n", "--brand", os.path.join(d, "none.json"))
            c2, _, _, e2 = convert(d, "x\n", "--brand", bad)
        self.assertNotEqual(c1, 0)
        self.assertIn("brand file not found", e1)
        self.assertNotEqual(c2, 0)
        self.assertIn("brand file is not valid JSON", e2)

    # BUG: a brand.json that is valid JSON but not an object (e.g. []) crashes with AttributeError
    @unittest.expectedFailure
    def test_brand_file_that_is_not_an_object_fails_clearly(self):
        with workdir() as d:
            arr = write(os.path.join(d, "arr.json"), "[]")
            code, _, _, err = convert(d, "x\n", "--brand", arr)
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)

    def test_front_matter_is_dropped(self):
        with workdir() as d:
            _, page, _, _ = convert(d, "---\ntitle: x\n---\n# Real\n")
        self.assertNotIn("title: x", page)
        self.assertIn("<title>Real</title>", page)

    def test_stdin_input_resolves_images_from_cwd(self):
        with workdir() as d:
            with open(os.path.join(d, "dot.png"), "wb") as f:
                f.write(PNG)
            out = os.path.join(d, "o.html")
            code, so, se = run(SKILL, SCRIPT, "-", "-o", out, stdin="# From stdin\n\n![d](dot.png)\n", cwd=d)
            page = read(out)
        self.assertEqual(code, 0, se)
        self.assertIn("<title>From stdin</title>", page)
        self.assertIn("data:image/png;base64,", page)

    def test_bad_inputs_fail_with_a_message(self):
        with workdir() as d:
            empty = write(os.path.join(d, "empty.md"), "  \n")
            with open(os.path.join(d, "bin.md"), "wb") as f:
                f.write(b"\xff\xfe\x00bad")
            cases = [
                ((os.path.join(d, "missing.md"), "-o", os.path.join(d, "o.html")), "input not found"),
                ((empty, "-o", os.path.join(d, "o.html")), "input is empty"),
                ((os.path.join(d, "bin.md"), "-o", os.path.join(d, "o.html")), "is not UTF-8 text"),
                ((write(os.path.join(d, "ok.md"), "x\n"), "-o", os.path.join(d, "no", "o.html")),
                 "output folder does not exist"),
            ]
            for args, msg in cases:
                code, _, err = run(SKILL, SCRIPT, *args)
                self.assertNotEqual(code, 0, args)
                self.assertIn(msg, err)
                self.assertNotIn("Traceback", err)
            self.assertFalse(os.path.exists(os.path.join(d, "o.html")))


class MdToHtmlFunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def test_safe_url_allows_web_mail_and_relative_targets_only(self):
        ctx = self.m.Ctx(None, False, "none")
        for ok in ("https://e.test", "mailto:a@e.test", "tel:+100", "#top", "/abs", "./rel", "../up", "page.html"):
            self.assertEqual(self.m.safe_url(ok, ctx), ok)
        for bad in ("javascript:x", "vbscript:x", "data:text/html,x", "file:///etc/passwd"):
            self.assertIsNone(self.m.safe_url(bad, ctx))

    def test_css_font_strips_characters_that_could_break_out_of_css(self):
        self.assertEqual(self.m.css_font("Inter;}</style><script>"), "Inter/stylescript")


if __name__ == "__main__":
    unittest.main()

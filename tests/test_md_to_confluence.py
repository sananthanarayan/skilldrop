import argparse
import io
import os
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "md-to-confluence", "md_to_confluence.py"
NS = 'xmlns:ac="http://atlassian.com/content" xmlns:ri="http://atlassian.com/resource/identifier"'
AC = "{http://atlassian.com/content}"
CRED_VARS = ("CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN", "CONFLUENCE_PAT")


def parse(body):
    return ET.fromstring("<root %s>%s</root>" % (NS, body))


class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def convert(self, src, base_dir=".", **kw):
        return self.m.convert(src, Path(base_dir), **kw)

    def test_inline_formatting_and_escaping(self):
        body, _, ctx, _ = self.convert("Hello **bold** and *it* `x<y` & co &mdash; ok\n")
        self.assertEqual(body, "<p>Hello <strong>bold</strong> and <em>it</em> "
                               "<code>x&lt;y</code> &amp; co — ok</p>")
        self.assertEqual(ctx.warnings, [])

    def test_first_h1_becomes_title_and_leaves_body(self):
        body, title, _, notes = self.convert("# Deploy checklist\n\nStep one.\n")
        self.assertEqual(title, "Deploy checklist")
        self.assertEqual(body, "<p>Step one.</p>")
        self.assertTrue(any("--keep-h1" in n for n in notes))

    def test_keep_h1_keeps_heading_in_body(self):
        body, title, _, _ = self.convert("# Deploy checklist\n\nStep one.\n", keep_h1=True)
        self.assertEqual(title, "Deploy checklist")
        self.assertTrue(body.startswith("<h1>Deploy checklist</h1>"))

    def test_front_matter_title_wins_and_h1_stays(self):
        body, title, ctx, notes = self.convert("---\ntitle: \"FM Title\"\nowner: x\n---\n# Other\n\nbody\n")
        self.assertEqual(title, "FM Title")
        self.assertTrue(body.startswith("<h1>Other</h1>"))
        self.assertIn("YAML front matter dropped (lines 1-4); its title: is used", ctx.warnings)
        self.assertTrue(any("differs from the page title" in n for n in notes))

    def test_title_argument_overrides_everything(self):
        _, title, _, _ = self.convert("---\ntitle: FM\n---\n# H1\n", title="Given")
        self.assertEqual(title, "Given")

    def test_setext_heading(self):
        body, _, ctx, _ = self.convert("Intro\n\nSection\n-------\n\ntext\n")
        self.assertEqual(body, "<p>Intro</p><h2>Section</h2><p>text</p>")
        self.assertEqual(ctx.headings, [(2, "Section")])

    def test_code_fence_maps_language_alias(self):
        body, _, ctx, _ = self.convert("```python\nprint(1)\n```\n")
        self.assertIn('<ac:parameter ac:name="language">py</ac:parameter>', body)
        self.assertEqual(ctx.counts["code"], 1)

    def test_code_with_cdata_terminator_survives_byte_for_byte(self):
        code = "x = data[arr[0]]>1  # ]]> inside\n\tif a < b && c:"
        body, _, _, _ = self.convert("```\n%s\n```\n" % code)
        text = parse(body).find(AC + "structured-macro").find(AC + "plain-text-body").text
        self.assertEqual(text, code)

    def test_unknown_language_and_mermaid_warn(self):
        body, _, ctx, _ = self.convert("~~~bogus\nx\n~~~\n\n```mermaid\ngraph TD\n```\n")
        self.assertNotIn("ac:name=\"language\"", body)
        self.assertEqual(len(ctx.warnings), 2)
        self.assertIn("code language 'bogus' has no Confluence highlighter", ctx.warnings[0])
        self.assertIn("line 5: Mermaid diagram kept as a code block", ctx.warnings[1])

    def test_indented_code_block(self):
        body, _, _, _ = self.convert("para\n\n    indented\n    more\n")
        self.assertIn("<![CDATA[indented\nmore]]>", body)

    def test_callouts_map_to_panel_macros(self):
        body, _, ctx, _ = self.convert("> **Note:** careful\n\n> [!WARNING]\n> hot\n\n"
                                       "> **Important:** read\n\n> plain quote\n")
        macros = [e.get(AC + "name") for e in parse(body).iter(AC + "structured-macro")]
        self.assertEqual(macros, ["info", "warning", "note"])
        self.assertIn("<blockquote><p>plain quote</p></blockquote>", body)
        self.assertIn("<p>careful</p>", body)
        self.assertEqual(ctx.counts["callouts"], 3)

    def test_task_list_statuses(self):
        body, _, ctx, _ = self.convert("- [ ] open item\n- [x] done item\n")
        tasks = parse(body).find(AC + "task-list").findall(AC + "task")
        self.assertEqual([(t.find(AC + "task-id").text, t.find(AC + "task-status").text,
                           t.find(AC + "task-body").text) for t in tasks],
                         [("1", "incomplete", "open item"), ("2", "complete", "done item")])
        self.assertEqual(ctx.counts["task_lists"], 1)

    def test_mixed_checkbox_list_warns_and_uses_text_boxes(self):
        body, _, ctx, _ = self.convert("- [ ] a\n- b\n")
        self.assertEqual(body, "<ul><li>☐ a</li><li>b</li></ul>")
        self.assertTrue(any("mixes checkboxes" in w for w in ctx.warnings))

    def test_nested_lists(self):
        body, _, _, _ = self.convert("- a\n  - b\n- c\n")
        self.assertEqual(body, "<ul><li>a<ul><li>b</li></ul></li><li>c</li></ul>")

    def test_ordered_list_not_starting_at_one_warns(self):
        body, _, ctx, _ = self.convert("3. three\n4. four\n")
        self.assertEqual(body, "<ol><li>three</li><li>four</li></ol>")
        self.assertTrue(any("starts at 3" in w for w in ctx.warnings))

    def test_code_indented_under_a_step_keeps_one_list(self):
        body, _, ctx, _ = self.convert("1. one\n\n   ```\n   code\n   ```\n2. two\n")
        self.assertEqual(body.count("<ol>"), 1)
        self.assertEqual(parse(body).find("ol").findall("li").__len__(), 2)
        self.assertEqual(ctx.warnings, [])

    def test_table_header_alignment_and_ragged_row(self):
        body, _, ctx, _ = self.convert("| a | b |\n|:--|--:|\n| 1 | 2 | 3 |\n| `x|y` | c \\| d |\n")
        root = parse(body)
        rows = root.find("table").find("tbody").findall("tr")
        self.assertEqual([c.tag for c in rows[0]], ["th", "th"])
        self.assertEqual(len(rows[1]), 2)  # the extra cell is cut
        self.assertIn('<th><p style="text-align: right;">b</p></th>', body)
        self.assertIn("<code>x|y</code>", body)
        self.assertIn("c | d", body)
        self.assertTrue(any("table row 1 has 3 cells, the header has 2; padded or cut" in w for w in ctx.warnings))

    # BUG: a ragged-row warning names the table's last line (ctx.line after the whole table is read),
    # not the line of the row that is short or long.
    @unittest.expectedFailure
    def test_ragged_row_warning_names_its_own_line(self):
        _, _, ctx, _ = self.convert("| a | b |\n|---|---|\n| 1 | 2 | 3 |\n| 4 | 5 |\n")
        self.assertEqual(ctx.warnings, ["line 3: table row 1 has 3 cells, the header has 2; padded or cut"])

    def test_links_unsafe_anchor_bare_and_reference(self):
        body, _, ctx, _ = self.convert(
            "[x](javascript:alert(1)) [y](#sec) see https://example.com/a. [r][k] <https://example.com/b>\n\n"
            "[k]: https://example.org/r \"T\"\n")
        self.assertNotIn("javascript", body)
        self.assertNotIn('href="#sec"', body)
        self.assertIn('<a href="https://example.com/a">https://example.com/a</a>.', body)
        self.assertIn('<a href="https://example.org/r" title="T">r</a>', body)
        self.assertIn('<a href="https://example.com/b">', body)
        self.assertTrue(any("unsafe link target dropped" in w for w in ctx.warnings))
        self.assertTrue(any("in-page link to #sec" in w for w in ctx.warnings))

    def test_dropped_html_and_footnotes_warn_with_line_numbers(self):
        body, _, ctx, _ = self.convert("<details>\n<summary>x</summary>\n</details>\n\n"
                                       "text <b>bold</b> end\n\nfoot[^1]\n\n[^1]: note\n")
        self.assertEqual(body, "<p>text bold end</p><p>foot</p>")
        self.assertIn("line 1: raw HTML block dropped (lines 1-3); rewrite it as Markdown to keep it", ctx.warnings)
        self.assertIn("line 7: footnote reference [^1] dropped (footnotes are not supported)", ctx.warnings)
        self.assertIn("line 9: footnote definition dropped (footnotes are not supported)", ctx.warnings)

    def test_images_attach_by_name_and_flag_clashes(self):
        with workdir() as d:
            with open(os.path.join(d, "flow.png"), "wb") as f:
                f.write(b"\x89PNG")
            os.makedirs(os.path.join(d, "a"))
            os.makedirs(os.path.join(d, "b"))
            src = ("![Flow](flow.png) ![one](a/shot.png) ![two](b/shot.png) "
                   "![r](https://example.com/p.png) ![d](data:image/png;base64,AAA)\n")
            body, _, ctx, _ = self.convert(src, d)
        self.assertIn('<ac:image ac:alt="Flow"><ri:attachment ri:filename="flow.png" /></ac:image>', body)
        self.assertIn('<ri:url ri:value="https://example.com/p.png" />', body)
        self.assertNotIn("data:", body)
        self.assertEqual(sorted(ctx.attachments), ["flow.png", "shot.png"])
        self.assertTrue(ctx.attachments["flow.png"]["found"])
        self.assertFalse(ctx.attachments["shot.png"]["found"])
        self.assertEqual(ctx.counts["images_remote"], 1)
        joined = "\n".join(ctx.warnings)
        self.assertIn("two different images are both named shot.png", joined)
        self.assertIn("image not found next to the Markdown: a/shot.png", joined)
        self.assertIn("image with a data URL dropped", joined)

    def test_toc_macro_and_few_headings_note(self):
        body, _, _, notes = self.convert("## A\n\ntext\n", toc=True)
        self.assertTrue(body.startswith('<ac:structured-macro ac:name="toc" ac:schema-version="1" />'))
        self.assertIn("--toc added, but the page has fewer than two section headings", notes)
        _, _, _, notes = self.convert("## A\n\n## B\n", toc=True)
        self.assertEqual(notes, [])

    def test_control_characters_removed_and_output_well_formed(self):
        body, _, _, _ = self.convert("bad\x07char & <tag attr='1'>kept</tag>\n")
        parse(body)
        self.assertEqual(body, "<p>badchar &amp; kept</p>")

    # BUG: a hard line break ("two spaces" or "\" before a newline) is deleted and the two lines are
    # glued ("firstsecond"): the \x01 placeholder is removed by translate(XML_BAD) inside inline().
    @unittest.expectedFailure
    def test_hard_line_break_becomes_br(self):
        body, _, _, _ = self.convert("first  \nsecond\n")
        self.assertEqual(body, "<p>first<br />second</p>")


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)
        self.calls = []
        self.responses = []
        self.saved_env = {k: os.environ.pop(k, None) for k in CRED_VARS}
        os.environ["CONFLUENCE_EMAIL"] = "someone@example.com"
        os.environ["CONFLUENCE_API_TOKEN"] = "test-token-not-real"

        def fake_call(method, url, auth, payload=None):
            self.calls.append((method, url, auth, payload))
            return self.responses.pop(0)

        self.m.call = fake_call

    def tearDown(self):
        for k, v in self.saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def args(self, **kw):
        base = dict(page_id=None, expected_version=None, parent_id=None, title=None, space="SRE",
                    dry_run=False, inspect=False)
        base.update(kw)
        return argparse.Namespace(**base)

    def publish(self, a, title="Runbook"):
        out = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(out):
            self.m.publish(a, "<p>x</p>", title, "https://ex.atlassian.net/wiki", "ex.atlassian.net")
        return out.getvalue()

    def test_normalize_base_adds_wiki_for_cloud(self):
        self.assertEqual(self.m.normalize_base("https://ex.atlassian.net/"),
                         ("https://ex.atlassian.net/wiki", "ex.atlassian.net"))
        self.assertEqual(self.m.normalize_base("https://wiki.example.com/confluence/"),
                         ("https://wiki.example.com/confluence", "wiki.example.com"))

    def test_normalize_base_refuses_http_and_embedded_credentials(self):
        for bad in ("http://ex.atlassian.net/wiki", "https://u:p@ex.atlassian.net/wiki",
                    "https://ex.atlassian.net/wiki?x=1", None):
            with self.assertRaises(self.m.Refused):
                self.m.normalize_base(bad)

    def test_credentials_basic_for_cloud_and_bearer_for_pat(self):
        auth, desc = self.m.credentials("ex.atlassian.net")
        self.assertTrue(auth.startswith("Basic "))
        self.assertNotIn("test-token-not-real", desc)
        os.environ["CONFLUENCE_PAT"] = "pat-test-not-real"
        self.assertEqual(self.m.credentials("ex.atlassian.net")[0], auth)
        self.assertEqual(self.m.credentials("wiki.example.com")[0], "Bearer pat-test-not-real")
        for k in CRED_VARS:
            del os.environ[k]
        self.assertIsNone(self.m.credentials("wiki.example.com")[0])

    def test_create_checks_title_then_posts(self):
        self.responses = [{"results": []}, {"id": "9", "title": "Runbook", "space": {"key": "SRE"},
                                            "version": {"number": 1}}]
        out = self.publish(self.args(parent_id=42))
        self.assertEqual([c[0] for c in self.calls], ["GET", "POST"])
        self.assertIn("spaceKey=SRE", self.calls[0][1])
        self.assertIn("title=Runbook", self.calls[0][1])
        payload = self.calls[1][3]
        self.assertEqual(payload["title"], "Runbook")
        self.assertEqual(payload["space"], {"key": "SRE"})
        self.assertEqual(payload["ancestors"], [{"id": "42"}])
        self.assertEqual(payload["body"]["storage"], {"value": "<p>x</p>", "representation": "storage"})
        self.assertIn("created page: id 9", out)

    def test_create_refuses_when_title_taken(self):
        self.responses = [{"results": [{"id": "7", "title": "Runbook", "version": {"number": 3}}]}]
        with self.assertRaises(self.m.Refused) as cm:
            self.publish(self.args())
        self.assertIn("--page-id 7", str(cm.exception))
        self.assertEqual(len(self.calls), 1)

    def test_update_sends_next_version_and_keeps_page_title(self):
        cur = {"id": "48213", "title": "Deploy checklist", "space": {"key": "SRE"}, "version": {"number": 7}}
        self.responses = [cur, dict(cur, version={"number": 8})]
        out = self.publish(self.args(page_id=48213, expected_version=7), title="Deploy checklist v2")
        self.assertEqual([c[0] for c in self.calls], ["GET", "PUT"])
        payload = self.calls[1][3]
        self.assertEqual(payload["version"], {"number": 8})
        self.assertEqual(payload["title"], "Deploy checklist")
        self.assertIn("kept the page's current title", out)
        self.assertIn("version 7 -> 8", out)

    def test_update_refuses_stale_expected_version(self):
        self.responses = [{"id": "5", "title": "T", "space": {"key": "SRE"}, "version": {"number": 9}}]
        with self.assertRaises(self.m.Refused) as cm:
            self.publish(self.args(page_id=5, expected_version=7))
        self.assertIn("someone edited it since you checked", str(cm.exception))
        self.assertEqual([c[0] for c in self.calls], ["GET"])

    def test_update_refuses_page_in_other_space(self):
        self.responses = [{"id": "5", "title": "T", "space": {"key": "OPS"}, "version": {"number": 2}}]
        with self.assertRaises(self.m.Refused):
            self.publish(self.args(page_id=5))
        self.assertEqual(len(self.calls), 1)

    def test_dry_run_sends_nothing(self):
        out = self.publish(self.args(dry_run=True, page_id=5))
        self.assertEqual(self.calls, [])
        self.assertIn("dry run: nothing was sent", out)
        self.assertIn("PUT https://ex.atlassian.net/wiki/rest/api/content/5", out)
        self.assertIn("no --expected-version", out)

    def test_inspect_is_read_only(self):
        self.responses = [{"id": "5", "title": "T", "space": {"key": "SRE"},
                           "version": {"number": 4, "by": {"displayName": "Test User"}}}]
        out = self.publish(self.args(inspect=True, page_id=5))
        self.assertEqual([c[0] for c in self.calls], ["GET"])
        self.assertIn("version 4, last edited by Test User", out)
        self.assertIn("--expected-version 4", out)

    def test_no_credentials_refused(self):
        for k in CRED_VARS:
            os.environ.pop(k, None)
        with self.assertRaises(self.m.Refused):
            self.publish(self.args())
        self.assertEqual(self.calls, [])

    def test_http_error_carries_hint(self):
        m = load(SKILL, SCRIPT)

        def raise_409(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 409, "Conflict", {},
                                         io.BytesIO(b'{"message": "stale version"}'))

        m.OPENER.open = raise_409
        with self.assertRaises(m.PublishError) as cm:
            m.call("PUT", "https://ex.atlassian.net/wiki/rest/api/content/5", "Basic x", {"a": 1})
        self.assertIn("HTTP 409 (version conflict", str(cm.exception))
        self.assertIn("stale version", str(cm.exception))


class CliTest(unittest.TestCase):
    def env(self):
        return {k: "" for k in CRED_VARS}

    def test_convert_writes_file_and_summary(self):
        with workdir() as d:
            src = write(os.path.join(d, "rb.md"), "# Runbook\n\n## Step\n\n| a |\n|---|\n| 1 |\n\n![x](gone.png)\n")
            out = os.path.join(d, "rb.xhtml")
            code, so, se = run(SKILL, SCRIPT, src, "-o", out, cwd=d)
            self.assertEqual(code, 0, se)
            body = read(out)
        self.assertTrue(body.startswith("<h2>Step</h2>"))
        self.assertIn('title "Runbook"', so)
        self.assertIn("1 tables", so)
        self.assertIn("gone.png  (from gone.png)  NOT FOUND", so)
        self.assertIn("WARN line 9: image not found", se)
        self.assertIn("1 warning(s)", se)

    def test_stdin_input(self):
        with workdir() as d:
            out = os.path.join(d, "o.xhtml")
            code, _, se = run(SKILL, SCRIPT, "-", "-o", out, stdin="hello\n", cwd=d)
            self.assertEqual(code, 0, se)
            self.assertEqual(read(out), "<p>hello</p>")

    def test_missing_and_empty_input_fail_clearly(self):
        with workdir() as d:
            code, _, se = run(SKILL, SCRIPT, os.path.join(d, "nope.md"), "-o", os.path.join(d, "o.xhtml"))
            self.assertEqual(code, 1)
            self.assertIn("input not found", se)
            empty = write(os.path.join(d, "e.md"), "  \n")
            code, _, se = run(SKILL, SCRIPT, empty, "-o", os.path.join(d, "o.xhtml"))
            self.assertEqual(code, 1)
            self.assertIn("input is empty", se)
            self.assertNotIn("Traceback", se)

    def test_flag_combinations_rejected(self):
        with workdir() as d:
            src = write(os.path.join(d, "a.md"), "# T\n")
            out = os.path.join(d, "o.xhtml")
            cases = [(["--dry-run"], "--dry-run goes with --publish"),
                     (["--publish", "--inspect", "--base-url", "https://x.atlassian.net", "--space", "S"],
                      "not both"),
                     (["--publish"], "need --base-url and --space"),
                     (["--expected-version", "3"], "--expected-version goes with --page-id")]
            for extra, msg in cases:
                code, _, se = run(SKILL, SCRIPT, src, "-o", out, *extra, env=self.env())
                self.assertEqual(code, 1, extra)
                self.assertIn(msg, se)

    def test_publish_over_http_refused_with_exit_2(self):
        with workdir() as d:
            src = write(os.path.join(d, "a.md"), "# T\n\nx\n")
            code, _, se = run(SKILL, SCRIPT, src, "-o", os.path.join(d, "o.xhtml"), "--publish",
                              "--base-url", "http://ex.atlassian.net/wiki", "--space", "SRE", env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("REFUSED: refusing a non-https base URL", se)

    def test_publish_without_credentials_refused_with_exit_2(self):
        with workdir() as d:
            src = write(os.path.join(d, "a.md"), "# T\n\nx\n")
            code, _, se = run(SKILL, SCRIPT, src, "-o", os.path.join(d, "o.xhtml"), "--publish",
                              "--base-url", "https://ex.atlassian.net", "--space", "SRE", env=self.env())
        self.assertEqual(code, 2)
        self.assertIn("REFUSED: no Confluence credentials", se)

    def test_publish_needs_a_title(self):
        with workdir() as d:
            src = write(os.path.join(d, "a.md"), "no heading here\n")
            code, _, se = run(SKILL, SCRIPT, src, "-o", os.path.join(d, "o.xhtml"), "--publish", "--dry-run",
                              "--base-url", "https://ex.atlassian.net", "--space", "SRE", env=self.env())
        self.assertEqual(code, 1)
        self.assertIn("no page title", se)

    def test_dry_run_cli_exits_0_without_credentials(self):
        with workdir() as d:
            src = write(os.path.join(d, "a.md"), "# T\n\nx\n")
            code, so, se = run(SKILL, SCRIPT, src, "-o", os.path.join(d, "o.xhtml"), "--publish", "--dry-run",
                               "--base-url", "https://ex.atlassian.net", "--space", "SRE", env=self.env())
        self.assertEqual(code, 0, se)
        self.assertIn("POST https://ex.atlassian.net/wiki/rest/api/content", so)
        self.assertIn("auth: none found", so)


if __name__ == "__main__":
    unittest.main()

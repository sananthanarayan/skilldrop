import os
import shutil
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "mermaid-render", "render_mermaid.py"
CLEAN = ("flowchart TD\n  A[Start] --> B{Ok?}\n  B -->|yes| C((Done))\n  B -- no --> D[\"Retry (x2)\"]\n"
         "  subgraph S1[\"Group (one)\"]\n    E --> F\n  end\n")


class LintTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def lint(self, text, first_line=1):
        issues, kind = self.m.lint(text, first_line)
        return kind, [(i.line, i.level, i.msg) for i in issues]

    def errors(self, text):
        return [(ln, msg) for ln, lvl, msg in self.lint(text)[1] if lvl == "error"]

    def test_clean_flowchart_passes(self):
        self.assertEqual(self.lint(CLEAN), ("flowchart", []))

    def test_clean_diagrams_of_other_types_pass(self):
        for text in ("graph LR\n  A --> B\n  B --> A\n",
                     "---\ntitle: x\n---\n%%{init: {}}%%\nflowchart LR\n A-->B\n",
                     "sequenceDiagram\n  A->>B: hi\n  alt ok\n    B-->>A: yes\n  else bad\n    B-->>A: no\n  end\n",
                     "erDiagram\n  CUSTOMER ||--o{ ORDER : places\n  ORDER }|..|{ ITEM : has\n",
                     "classDiagram\n  class A {\n    +int x\n  }\n", "pie\n"):
            self.assertEqual(self.lint(text)[1], [], text)

    def test_unknown_type_suggests_closest(self):
        kind, issues = self.lint("flowchar TD\nA-->B")
        self.assertIsNone(kind)
        self.assertEqual(issues, [(1, "error", "unknown diagram type `flowchar` on the first line. "
                                               "Did you mean `flowchart`?")])

    def test_unknown_direction(self):
        self.assertEqual(self.errors("flowchart XY\n  A --> B\n"),
                         [(1, "unknown direction `XY`; use TD, TB, BT, LR or RL")])

    def test_end_as_node_id(self):
        (err,) = self.errors("flowchart TD\n  A --> end\n")
        self.assertEqual(err[0], 2)
        self.assertIn("`end` is reserved", err[1])

    def test_unbalanced_bracket(self):
        self.assertEqual(self.errors("flowchart TD\n  A[Start --> B\n"),
                         [(2, "unbalanced brackets: `A[` is never closed with `]`")])

    def test_unquoted_parentheses_in_label_with_fix(self):
        (err,) = self.errors("flowchart TD\n  A[Call (api)] --> B\n")
        self.assertEqual(err[0], 2)
        self.assertIn('A["Call (api)"]', err[1])

    def test_unquoted_parentheses_in_arrow_label(self):
        (err,) = self.errors("flowchart TD\n  A -->|call (x)| B\n")
        self.assertIn('|"call (x)"|', err[1])

    def test_single_dash_arrow_and_missing_arrow(self):
        self.assertEqual(self.errors("flowchart TD\n  A -> B\n"),
                         [(2, "`->` is not a flowchart arrow; use `-->` (or `==>`)")])
        self.assertEqual(self.errors("flowchart TD\n  A B\n"),
                         [(2, "no arrow between `A` and `B`; join them with `-->`")])
        self.assertEqual(self.errors("flowchart TD\n  A --> \n"), [(2, "an arrow with no node on one side")])

    def test_subgraph_without_end_reports_opening_line(self):
        self.assertEqual(self.errors("flowchart TD\n  A --> B\n  subgraph one\n  C --> D\n"),
                         [(3, "subgraph opened here has no matching `end`")])

    def test_sequence_blocks_and_messages(self):
        self.assertEqual(self.errors("sequenceDiagram\n  A->>B: hi\n  loop every minute\n  B-->>A: ok\n"),
                         [(3, "`loop` block opened here has no matching `end`")])
        self.assertEqual(self.errors("sequenceDiagram\n  A->>B\n  else\n"),
                         [(2, "message without `: text`; write `A->>B: what is sent`"),
                          (3, "`else` outside a `alt` block")])

    def test_unclosed_brace_in_class_diagram(self):
        self.assertEqual(self.errors("classDiagram\n  class A {\n    +int x\n"),
                         [(2, "`{` opened here is never closed")])

    def test_empty_diagram_and_type_without_content(self):
        self.assertEqual(self.lint("\n%% only a comment\n"), (None, [(1, "error", "the diagram is empty")]))
        self.assertEqual(self.lint("flowchart TD\n")[1], [(1, "warning", "the diagram has a type but no content")])

    def test_line_numbers_offset_by_first_line(self):
        self.assertEqual([ln for ln, _, _ in self.lint("flowchart TD\n  A -> B\n", 10)[1]], [11])

    def test_subgraph_id_space_title_is_valid(self):
        self.assertEqual(self.errors("flowchart TB\n  subgraph ide1 [one]\n    a1-->a2\n  end\n"), [])


class HelpersTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)

    def test_extract_fences_line_numbers_and_unclosed(self):
        text = "text\n```mermaid\ngraph TD\nA-->B\n```\n\n~~~mermaid\nsequenceDiagram\n"
        self.assertEqual(self.m.extract_fences(text),
                         [(3, "graph TD\nA-->B", None), (8, "sequenceDiagram\n", "unclosed")])

    def test_mmdc_error_keeps_message_and_drops_stack_trace(self):
        raw = ("Generating single mermaid chart\nError: Parse error on line 2:\n...A-->\n----^\n"
               "    at Parser.parse (file:///x.js:1:2)\n    at more\n")
        self.assertEqual(self.m.mmdc_error(raw), "Error: Parse error on line 2:\n...A-->\n----^")

    def test_html_page_escapes_diagram_and_pins_version(self):
        page = self.m.html_page([("fig <1>", "graph TD\nA[\"<b>x</b>\"] --> B")], "t&t")
        self.assertIn("A[&quot;&lt;b&gt;x&lt;/b&gt;&quot;] --&gt; B", page)
        self.assertIn("<figcaption>fig &lt;1&gt;</figcaption>", page)
        self.assertIn("<title>t&amp;t</title>", page)
        self.assertIn("mermaid@%s" % self.m.MERMAID_VERSION, page)
        self.assertIn("'sha256-%s'" % self.m.MERMAID_INIT_HASH, page)
        self.assertIn('securityLevel:"strict"', page)


class CliTest(unittest.TestCase):
    def test_lint_only_exit_codes(self):
        with workdir() as d:
            good = write(os.path.join(d, "ok.mmd"), CLEAN)
            bad = write(os.path.join(d, "bad.mmd"), "flowchart TD\n  A -> B\n")
            code, out, _ = run(SKILL, SCRIPT, good)
            self.assertEqual(code, 0)
            self.assertIn("ok.mmd: flowchart: ok", out)
            code, out, _ = run(SKILL, SCRIPT, bad)
            self.assertEqual(code, 1)
            self.assertIn("bad.mmd:2: error: `->` is not a flowchart arrow", out)
            self.assertIn("lint: 1 diagram(s), 1 error(s), 0 warning(s)", out)

    def test_markdown_errors_use_file_line_numbers(self):
        with workdir() as d:
            md = write(os.path.join(d, "design.md"),
                       "# Design\n\n```mermaid\ngraph TD\n  A --> B\n```\n\n```mermaid\nflowchart LR\n  X -> Y\n```\n")
            code, out, _ = run(SKILL, SCRIPT, md)
        self.assertEqual(code, 1)
        self.assertIn("design.md: diagram 1 (graph): ok", out)
        self.assertIn("design.md:10: error:", out)

    def test_unclosed_fence_is_an_error(self):
        with workdir() as d:
            md = write(os.path.join(d, "d.md"), "intro\n```mermaid\ngraph TD\n  A --> B\n")
            code, out, _ = run(SKILL, SCRIPT, md)
        self.assertEqual(code, 1)
        self.assertIn("d.md:2: error: the ```mermaid fence is never closed", out)

    def test_bad_input_fails_clearly(self):
        with workdir() as d:
            nofence = write(os.path.join(d, "n.md"), "# no diagrams\n")
            good = write(os.path.join(d, "g.mmd"), CLEAN)
            cases = [([os.path.join(d, "missing.mmd")], "input not found"),
                     ([nofence], "no ```mermaid fences found"),
                     ([good, "-o", os.path.join(d, "out.gif")], "output must end in .svg, .png, .pdf or .html"),
                     ([good, "-o", os.path.join(d, "nodir", "out.html")], "output folder does not exist")]
            for args, msg in cases:
                code, _, se = run(SKILL, SCRIPT, *args)
                self.assertEqual(code, 1, args)
                self.assertIn(msg, se)
                self.assertNotIn("Traceback", se)

    def test_errors_block_render_unless_forced(self):
        with workdir() as d:
            bad = write(os.path.join(d, "bad.mmd"), "flowchart TD\n  A -> B\n")
            out = os.path.join(d, "bad.html")
            code, _, se = run(SKILL, SCRIPT, bad, "-o", out)
            self.assertEqual(code, 1)
            self.assertIn("not rendering", se)
            self.assertFalse(os.path.exists(out))
            code, _, _ = run(SKILL, SCRIPT, bad, "-o", out, "--force")
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(out))

    def test_html_output_holds_every_diagram(self):
        with workdir() as d:
            md = write(os.path.join(d, "design.md"),
                       "```mermaid\ngraph TD\n  A --> B\n```\n\n```mermaid\nsequenceDiagram\n  A->>B: hi\n```\n")
            out = os.path.join(d, "design.html")
            code, so, se = run(SKILL, SCRIPT, md, "-o", out)
            self.assertEqual(code, 0, se)
            page = read(out)
        self.assertEqual(page.count('<pre class="mermaid">'), 2)
        self.assertIn("design.md, diagram 2 (line 7)", page)
        self.assertIn("2 diagram(s)", so)
        self.assertIn("needs network", so)

    @unittest.skipIf(shutil.which("mmdc"), "mmdc is on PATH, so the HTML fallback is not used")
    def test_svg_without_mmdc_falls_back_to_html(self):
        with workdir() as d:
            src = write(os.path.join(d, "arch.mmd"), CLEAN)
            code, so, _ = run(SKILL, SCRIPT, src, "-o", os.path.join(d, "arch.svg"))
            self.assertEqual(code, 0)
            self.assertFalse(os.path.exists(os.path.join(d, "arch.svg")))
            self.assertTrue(os.path.exists(os.path.join(d, "arch.html")))
        self.assertIn("mmdc (mermaid-cli) is not on PATH", so)
        self.assertIn("npm install -g @mermaid-js/mermaid-cli", so)

    @unittest.skipUnless(shutil.which("mmdc"), "mmdc (mermaid-cli) not on PATH")
    def test_svg_render_with_mmdc_numbers_each_diagram(self):
        with workdir() as d:
            md = write(os.path.join(d, "design.md"),
                       "```mermaid\ngraph TD\n  A --> B\n```\n\n```mermaid\ngraph LR\n  C --> D\n```\n")
            code, so, se = run(SKILL, SCRIPT, md, "-o", os.path.join(d, "fig.svg"), timeout=400)
            self.assertEqual(code, 0, se)
            for k in (1, 2):
                self.assertIn("<svg", read(os.path.join(d, "fig-%d.svg" % k)))


if __name__ == "__main__":
    unittest.main()

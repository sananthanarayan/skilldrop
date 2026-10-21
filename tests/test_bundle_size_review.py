import gzip
import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "bundle-size-review", "bundle_stats.py"
m = load(SKILL, SCRIPT)


def webpack_stats():
    """main entry (120,000 emitted bytes) with a CommonJS lodash; a lazy chunk holding echarts."""
    return {
        "version": "5.90.0",
        "assets": [
            {"name": "main.3f2a1b9c.js", "size": 120000},
            {"name": "main.3f2a1b9c.js.map", "size": 400000},
            {"name": "main.css", "size": 5000},
            {"name": "42.abcdef12.js", "size": 60000},
        ],
        "chunks": [
            {"id": 179, "names": ["main"], "files": ["main.3f2a1b9c.js", "main.css", "main.3f2a1b9c.js.map"],
             "initial": True, "entry": True, "size": 300000},
            {"id": 42, "names": [], "files": ["42.abcdef12.js"], "initial": False, "entry": False,
             "size": 150000, "origins": [{"moduleName": "./src/index.js"}]},
        ],
        "modules": [
            {"name": "./src/index.js", "size": 2000, "chunks": [179], "depth": 0,
             "reasons": [{"type": "entry", "moduleName": None}]},
            {"name": "./node_modules/lodash/lodash.js", "size": 70000, "chunks": [179],
             "optimizationBailout": ["ModuleConcatenation bailout: Module is not an ECMAScript module"],
             "reasons": [{"type": "harmony side effect evaluation", "moduleName": "./src/index.js",
                          "userRequest": "lodash"}]},
            {"name": "./src/reports.js", "size": 3000, "chunks": [42],
             "reasons": [{"type": "import()", "moduleName": "./src/index.js", "userRequest": "./reports"}]},
            {"name": "./node_modules/echarts/index.js", "size": 147000, "chunks": [42],
             "reasons": [{"type": "harmony import specifier", "moduleName": "./src/reports.js",
                          "userRequest": "echarts"}]},
        ],
        "entrypoints": {"main": {"chunks": [179]}},
    }


def esbuild_meta():
    return {
        "inputs": {
            "src/main.tsx": {"bytes": 1500, "imports": [
                {"path": "src/lib/util.ts", "kind": "import-statement"},
                {"path": "node_modules/react/index.js", "kind": "import-statement"},
                {"path": "src/routes/Editor.tsx", "kind": "dynamic-import"}]},
            "src/lib/util.ts": {"bytes": 3000, "imports": []},
            "node_modules/react/index.js": {"bytes": 40000, "format": "cjs", "imports": []},
            "src/routes/Editor.tsx": {"bytes": 800, "imports": [
                {"path": "node_modules/monaco-editor/esm/editor.js", "kind": "import-statement"},
                {"path": "src/lib/util.ts", "kind": "import-statement"}]},
            "node_modules/monaco-editor/esm/editor.js": {"bytes": 250000, "imports": []},
        },
        "outputs": {
            "dist/main.js": {"bytes": 50000, "entryPoint": "src/main.tsx", "cssBundle": "dist/main.css",
                             "imports": [{"path": "dist/chunk-AAAA1111.js", "kind": "import-statement"},
                                         {"path": "dist/Editor-BBBB2222.js", "kind": "dynamic-import"}],
                             "inputs": {"src/main.tsx": {"bytesInOutput": 1000},
                                        "node_modules/react/index.js": {"bytesInOutput": 30000}}},
            "dist/main.js.map": {"bytes": 99999, "imports": [], "inputs": {}},
            "dist/main.css": {"bytes": 2000, "imports": [], "inputs": {}},
            "dist/chunk-AAAA1111.js": {"bytes": 3000, "imports": [],
                                       "inputs": {"src/lib/util.ts": {"bytesInOutput": 2900}}},
            "dist/Editor-BBBB2222.js": {"bytes": 200000, "entryPoint": "src/routes/Editor.tsx",
                                        "imports": [{"path": "dist/chunk-AAAA1111.js", "kind": "import-statement"}],
                                        "inputs": {"src/routes/Editor.tsx": {"bytesInOutput": 500},
                                                   "node_modules/monaco-editor/esm/editor.js": {"bytesInOutput": 199000}}},
        },
    }


def rollup_data(gzip_on=True, version=2):
    return {
        "version": version,
        "env": {"rollup": "4.9.0"},
        "options": {"gzip": gzip_on, "brotli": gzip_on},
        "tree": {"name": "root", "children": [{"name": "assets/index-BxK3a9Qz.js"},
                                              {"name": "assets/Chart-Dk4j8sLq.js"}]},
        "nodeParts": {
            "p1": {"renderedLength": 1000, "gzipLength": 400, "brotliLength": 350},
            "p2": {"renderedLength": 40000, "gzipLength": 12000, "brotliLength": 10000},
            "p3": {"renderedLength": 90000, "gzipLength": 30000, "brotliLength": 25000},
            "p4": {"renderedLength": 500, "gzipLength": 200, "brotliLength": 150},
        },
        "nodeMetas": {
            "m1": {"id": "/src/main.ts", "moduleParts": {"assets/index-BxK3a9Qz.js": "p1"},
                   "imported": [{"uid": "m2"}, {"uid": "m4", "dynamic": True}], "importedBy": [], "isEntry": True},
            "m2": {"id": "/node_modules/preact/dist/preact.module.js", "moduleParts": {"assets/index-BxK3a9Qz.js": "p2"},
                   "imported": [], "importedBy": [{"uid": "m1"}]},
            "m3": {"id": "/node_modules/chart.js/dist/chart.js", "moduleParts": {"assets/Chart-Dk4j8sLq.js": "p3"},
                   "imported": [], "importedBy": [{"uid": "m4"}]},
            "m4": {"id": "/src/Chart.ts", "moduleParts": {"assets/Chart-Dk4j8sLq.js": "p4"},
                   "imported": [{"uid": "m3"}], "importedBy": [{"uid": "m1", "dynamic": True}]},
        },
    }


def compare_pair():
    """echarts moves from the lazy reports chunk into main; the total barely moves."""
    def stats(main_bytes, reports_bytes, echarts_chunk, echarts_from, index_size):
        return {
            "assets": [{"name": "main.js", "size": main_bytes}, {"name": "reports.js", "size": reports_bytes}],
            "chunks": [{"id": 0, "names": ["main"], "files": ["main.js"], "initial": True, "entry": True},
                       {"id": 1, "names": ["reports"], "files": ["reports.js"], "initial": False,
                        "origins": [{"moduleName": "./src/index.js"}]}],
            "modules": [
                {"name": "./src/index.js", "size": index_size, "chunks": [0], "reasons": [{"type": "entry"}]},
                {"name": "./src/reports.js", "size": 2000, "chunks": [1],
                 "reasons": [{"type": "import()", "moduleName": "./src/index.js", "userRequest": "./reports"}]},
                {"name": "./node_modules/echarts/index.js", "size": 490000, "chunks": [echarts_chunk],
                 "reasons": [{"type": "harmony import specifier", "moduleName": echarts_from, "userRequest": "echarts"}]},
            ],
            "entrypoints": {"main": {"chunks": [0]}},
        }
    before = stats(100000, 500000, 1, "./src/reports.js", 5000)
    after = stats(600000, 3000, 0, "./src/index.js", 5100)
    return before, after


def dump(d, name, data):
    return write(os.path.join(d, name), json.dumps(data))


def run_json(d, *args, stdin=None):
    code, out, err = run(SKILL, SCRIPT, *args, "--json", cwd=d, stdin=stdin)
    return code, (json.loads(out) if out.strip() else None), err


class TestWebpack(unittest.TestCase):
    def test_entry_initial_js_is_emitted_js_bytes_without_css_or_map(self):
        with workdir() as d:
            code, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()))
        self.assertEqual(code, 0)
        main = next(e for e in res["entries"] if e["name"] == "main")
        self.assertEqual(main["js_raw"], 120000)
        self.assertEqual(main["css_raw"], 5000)
        self.assertIsNone(main["gzip"])
        self.assertIn("after minification", res["raw_basis"])

    def test_lazy_chunk_kept_apart_with_hash_stripped_and_loader_named(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()))
        self.assertEqual(len(res["lazy_chunks"]), 1)
        lazy = res["lazy_chunks"][0]
        self.assertEqual(lazy["key"], "42.js")
        self.assertEqual(lazy["raw"], 60000)
        self.assertEqual(lazy["loaded_from"], ["src/index.js"])
        self.assertEqual(lazy["mostly"][0], {"owner": "echarts", "size": 147000})

    def test_packages_split_initial_and_lazy(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()))
        pk = {p["name"]: p for p in res["packages"]}
        self.assertEqual([p["name"] for p in res["packages"]], ["echarts", "lodash"])
        self.assertEqual((pk["echarts"]["initial_size"], pk["echarts"]["lazy_size"]), (0, 147000))
        self.assertEqual((pk["lodash"]["initial_size"], pk["lodash"]["lazy_size"]), (70000, 0))
        self.assertTrue(pk["lodash"]["commonjs"])
        self.assertFalse(pk["echarts"]["commonjs"])

    def test_whole_library_commonjs_import_is_flagged(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()))
        flags = [(f["kind"], f["package"], f["size"], f["initial"]) for f in res["flags"]]
        self.assertEqual(flags, [("whole-library-commonjs", "lodash", 70000, True)])

    def test_why_gives_chain_through_dynamic_import(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()), "--why", "echarts")
        match = res["why"][0]["matches"][0]
        self.assertEqual(match["install"], "node_modules/echarts")
        self.assertFalse(match["initial"])
        self.assertEqual([s["module"] for s in match["chain"]],
                         ["src/index.js", "src/reports.js", "node_modules/echarts/index.js"])
        self.assertEqual([s.get("via") for s in match["chain"]], [None, "dynamic", "static"])

    def test_why_unknown_name_reports_no_match(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, dump(d, "stats.json", webpack_stats()), "--why", "moment", cwd=d)
        self.assertEqual(code, 0)
        self.assertIn("no module or package by that name", out)

    def test_budget_over_exits_1_and_under_exits_0(self):
        with workdir() as d:
            p = dump(d, "stats.json", webpack_stats())
            code_over, out, _ = run(SKILL, SCRIPT, p, "--budget", "main=100kB", cwd=d)
            code_ok, res, _ = run_json(d, p, "--budget", "main=125kB")
        self.assertEqual(code_over, 1)
        self.assertIn("OVER", out)
        self.assertEqual(code_ok, 0)
        self.assertEqual(res["budgets"][0]["limit"], 125000)
        self.assertTrue(res["budgets"][0]["pass"])

    def test_budget_in_kib_is_1024_bytes(self):
        # 117 KiB = 119,808 bytes, just under the 120,000-byte entry
        with workdir() as d:
            code, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()), "--budget", "main=117KiB")
        self.assertEqual(code, 1)
        self.assertEqual(res["budgets"][0]["limit"], 119808)

    def test_budgets_that_cannot_be_checked_are_noted_not_failed(self):
        with workdir() as d:
            code, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()),
                                    "--budget", "admin=1", "--budget", "main=gzip:1")
        self.assertEqual(code, 0)
        self.assertEqual([r["pass"] for r in res["budgets"]], [None, None])
        self.assertEqual(res["budgets"][0]["note"], "no entry by this name")
        self.assertIn("not measured", res["budgets"][1]["note"])

    def test_dist_gzips_the_built_files(self):
        content = "console.log('bundle');\n" * 300
        with workdir() as d:
            dist = os.path.join(d, "dist")
            write(os.path.join(dist, "main.3f2a1b9c.js"), content)
            expected = len(gzip.compress(content.encode("utf-8"), compresslevel=9))
            p = dump(d, "stats.json", webpack_stats())
            code, res, _ = run_json(d, p, "--dist", dist, "--budget", "main=gzip:%d" % expected)
            code_over, _, _ = run_json(d, p, "--dist", dist, "--budget", "main=gzip:%d" % (expected - 1))
        main = next(e for e in res["entries"] if e["name"] == "main")
        self.assertEqual(main["gzip"], expected)
        self.assertEqual(main["gzip_basis"], "built-file")
        self.assertEqual(code, 0)
        self.assertEqual(code_over, 1)

    def test_without_assets_chunk_size_is_module_sum_before_minification(self):
        stats = webpack_stats()
        del stats["assets"]
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", stats))
        self.assertEqual(res["entries"][0]["js_raw"], 300000)
        self.assertIn("before minification", res["raw_basis"])

    def test_multi_compiler_reads_first_child_with_note(self):
        stats = {"children": [dict(webpack_stats(), name="client"), {"name": "server", "modules": []}]}
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", stats))
        self.assertEqual(res["entries"][0]["js_raw"], 120000)
        self.assertTrue(any("first child (client)" in n for n in res["notes"]))

    def test_module_copied_into_two_lazy_chunks(self):
        stats = {
            "chunks": [{"id": 0, "names": ["main"], "files": ["main.js"], "initial": True, "entry": True, "size": 1000},
                       {"id": 1, "names": ["a"], "files": ["a.js"], "size": 8000},
                       {"id": 2, "names": ["b"], "files": ["b.js"], "size": 8000}],
            "modules": [{"name": "./src/index.js", "size": 1000, "chunks": [0], "reasons": [{"type": "entry"}]},
                        {"name": "./node_modules/dayjs/dayjs.min.js", "size": 7000, "chunks": [1, 2]}],
            "entrypoints": {"main": {"chunks": [0]}},
        }
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", stats))
        self.assertEqual(res["in_several_chunks"],
                         [{"owner": "dayjs", "size": 7000, "extra_copies_size": 7000, "chunks": ["a", "b"], "modules": 1}])
        self.assertEqual(res["packages"][0]["size"], 7000)

    def test_text_report_states_units_and_unmeasured_compression(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, dump(d, "stats.json", webpack_stats()), cwd=d)
        self.assertEqual(code, 0)
        self.assertIn("kB = 1000 bytes", out)
        self.assertIn("main: 120,000 B (120.0 kB)", out)
        self.assertIn("Compressed sizes: not measured", out)


class TestEsbuild(unittest.TestCase):
    def test_entry_counts_static_shared_chunk_not_map_or_lazy(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "meta.json", esbuild_meta()))
        self.assertEqual(res["format"], "esbuild")
        self.assertEqual(len(res["entries"]), 1)
        e = res["entries"][0]
        self.assertEqual(e["name"], "src/main.tsx")
        self.assertEqual(e["js_raw"], 53000)
        self.assertEqual(e["css_raw"], 2000)
        self.assertEqual([c["key"] for c in e["chunks"]], ["src/main.tsx", "shared chunk: src/lib/util.ts"])

    def test_dynamic_entry_is_lazy_and_loaded_from_importer(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "meta.json", esbuild_meta()), "--why", "monaco-editor")
        self.assertEqual([(c["key"], c["raw"], c["loaded_from"]) for c in res["lazy_chunks"]],
                         [("src/routes/Editor.tsx", 200000, ["src/main.tsx"])])
        match = res["why"][0]["matches"][0]
        self.assertFalse(match["initial"])
        self.assertEqual([s["module"] for s in match["chain"]],
                         ["src/main.tsx", "src/routes/Editor.tsx", "node_modules/monaco-editor/esm/editor.js"])

    def test_cjs_input_in_initial_chunk_is_flagged(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "meta.json", esbuild_meta()))
        pk = {p["name"]: p for p in res["packages"]}
        self.assertEqual(pk["react"]["initial_size"], 30000)
        self.assertTrue(pk["react"]["commonjs"])
        self.assertEqual(pk["monaco-editor"]["lazy_size"], 199000)
        self.assertIn(("commonjs-in-initial", "react", 30000), [(f["kind"], f["package"], f["size"]) for f in res["flags"]])

    def test_budget_matches_entry_by_file_stem(self):
        with workdir() as d:
            code, res, _ = run_json(d, dump(d, "meta.json", esbuild_meta()), "--budget", "main=52000")
        self.assertEqual(code, 1)
        self.assertEqual((res["budgets"][0]["entry"], res["budgets"][0]["value"]), ("src/main.tsx", 53000))


class TestRollupVisualizer(unittest.TestCase):
    def test_entry_size_and_visualizer_gzip_brotli(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", rollup_data()))
        self.assertEqual(res["tool"], "rollup 4.9.0 (visualizer raw data)")
        e = res["entries"][0]
        self.assertEqual(e["name"], "src/main.ts")
        self.assertEqual((e["js_raw"], e["gzip"], e["brotli"]), (41000, 12400, 10350))
        self.assertEqual(e["gzip_basis"], "visualizer")
        self.assertEqual([c["key"] for c in e["chunks"]], ["assets/index.js"])

    def test_lazy_chunk_from_dynamic_import(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", rollup_data()))
        self.assertEqual([(c["key"], c["raw"], c["loaded_from"]) for c in res["lazy_chunks"]],
                         [("assets/Chart.js", 90500, ["src/main.ts"])])

    def test_gzip_budget_uses_visualizer_figures(self):
        with workdir() as d:
            p = dump(d, "stats.json", rollup_data())
            over, _, _ = run_json(d, p, "--budget", "main=gzip:12kB")
            ok, _, _ = run_json(d, p, "--budget", "main=gzip:13kB")
        self.assertEqual((over, ok), (1, 0))

    def test_without_gzip_option_notes_no_compressed_sizes(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", rollup_data(gzip_on=False)))
        self.assertIsNone(res["entries"][0]["gzip"])
        self.assertTrue(any("without gzipSize" in n for n in res["notes"]))

    def test_unsupported_data_version_exits_2(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, dump(d, "stats.json", rollup_data(version=9)), cwd=d)
        self.assertEqual(code, 2)
        self.assertIn("not supported", err)


class TestCompare(unittest.TestCase):
    def test_lazy_to_initial_move_is_attributed(self):
        before, after = compare_pair()
        with workdir() as d:
            code, res, _ = run_json(d, "--compare", dump(d, "before.json", before), dump(d, "after.json", after))
        self.assertEqual(code, 0)
        c = res["compare"]
        e = c["entries"][0]
        self.assertEqual((e["name"], e["raw_before"], e["raw_after"], e["raw_delta"]), ("main", 100000, 600000, 500000))
        self.assertEqual(c["totals"]["all_before"], 600000)
        self.assertEqual(c["totals"]["all_after"], 603000)
        self.assertEqual(c["moved_to_initial"], ["echarts"])
        self.assertEqual(c["modules_moved_to_initial"]["count"], 1)
        self.assertEqual(c["modules_moved_to_initial"]["size"], 490000)
        echarts = next(p for p in c["packages"] if p["name"] == "echarts")
        self.assertEqual(echarts["initial_delta"], 490000)
        self.assertEqual([s["module"] for s in echarts["chain_after"]], ["src/index.js", "node_modules/echarts/index.js"])
        self.assertEqual([(x["path"], x["size_before"], x["size_after"]) for x in c["modules_changed"]],
                         [("src/index.js", 5000, 5100)])

    def test_budget_passes_before_and_fails_after(self):
        before, after = compare_pair()
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, "--compare", dump(d, "before.json", before),
                               dump(d, "after.json", after), "--budget", "main=110kB", cwd=d)
        self.assertEqual(code, 1)
        self.assertIn("before 100,000 B (PASS), after 600,000 B (OVER)", out)
        self.assertIn("moved from lazy to initial: echarts", out)

    def test_compare_with_positional_stats_exits_2(self):
        before, after = compare_pair()
        with workdir() as d:
            b, a = dump(d, "before.json", before), dump(d, "after.json", after)
            code, _, err = run(SKILL, SCRIPT, a, "--compare", b, a, cwd=d)
        self.assertEqual(code, 2)
        self.assertIn("not both", err)


class TestProjectFiles(unittest.TestCase):
    def polyfill_stats(self):
        return {
            "chunks": [{"id": 0, "names": ["main"], "files": ["main.js"], "initial": True, "entry": True, "size": 9410}],
            "modules": [
                {"name": "./src/index.js", "size": 4000, "chunks": [0], "reasons": [{"type": "entry"}]},
                {"name": "./node_modules/core-js/modules/es.array.find-last.js", "size": 1200, "chunks": [0]},
                {"name": "./node_modules/core-js/modules/es.promise.js", "size": 4210, "chunks": [0]},
            ],
            "entrypoints": {"main": {"chunks": [0]}},
        }

    def test_polyfills_checked_against_browserslistrc(self):
        with workdir() as d:
            write(os.path.join(d, "package.json"), json.dumps({"name": "fixture-app", "dependencies": {"core-js": "^3.36.0"}}))
            write(os.path.join(d, ".browserslistrc"), "# targets\nsafari >= 15\nchrome >= 100\n")
            write(os.path.join(d, "src", "polyfills.ts"),
                  'import "core-js/modules/es.array.find-last";\nimport "core-js/modules/es.promise";\n')
            write(os.path.join(d, "src", "history.ts"), "export const last = (xs) => xs.findLast((x) => x.ok);\n")
            p = dump(os.path.join(d, "build"), "stats.json", self.polyfill_stats())
            _, res, _ = run_json(d, p)
        ctx = res["project"]
        self.assertEqual(ctx["targets_from"], ".browserslistrc")
        self.assertEqual(ctx["targets"], {"chrome": [100], "safari": [15]})
        poly = {x["module"]: x for x in ctx["polyfills"]}
        self.assertTrue(poly["es.array.find-last"]["verdict"].startswith("NEEDED"))
        self.assertIn("safari 15 < 15.4", poly["es.array.find-last"]["verdict"])
        self.assertEqual(poly["es.array.find-last"]["used_in"], ["src/history.ts"])
        self.assertEqual(poly["es.array.find-last"]["imported_by"], ["src/polyfills.ts"])
        self.assertTrue(poly["es.promise"]["verdict"].startswith("not needed"))
        self.assertIn("polyfill", [f["kind"] for f in res["flags"]])

    def test_build_config_target_used_when_no_browserslist(self):
        with workdir() as d:
            write(os.path.join(d, "package.json"), json.dumps({"name": "fixture-app"}))
            write(os.path.join(d, "vite.config.ts"), 'export default { build: { target: ["safari16", "chrome110"] } };\n')
            write(os.path.join(d, "webpack.config.js"),
                  'module.exports = { performance: { hints: "error", maxEntrypointSize: 320000 } };\n')
            p = dump(d, "stats.json", self.polyfill_stats())
            _, res, _ = run_json(d, p)
        ctx = res["project"]
        self.assertEqual(ctx["targets"], {"chrome": [110], "safari": [16]})
        self.assertEqual(ctx["targets_from"], "vite.config.ts target")
        self.assertIn("package.json browserslist field", ctx["absent"])
        self.assertIn("webpack.config.js maxEntrypointSize: 320000", ctx["budgets"])
        poly = {x["module"]: x for x in ctx["polyfills"]}
        self.assertTrue(poly["es.array.find-last"]["verdict"].startswith("not needed"))

    def test_absent_files_are_listed_and_targets_unknown(self):
        with workdir() as d:
            _, res, _ = run_json(d, dump(d, "stats.json", self.polyfill_stats()))
        ctx = res["project"]
        for name in ("package.json", ".browserslistrc", "lockfile"):
            self.assertIn(name, ctx["absent"])
        self.assertEqual({x["verdict"] for x in ctx["polyfills"]}, {"browser targets unknown"})

    def test_duplicate_versions_and_ranges_from_lockfile(self):
        stats = {
            "chunks": [{"id": 0, "names": ["main"], "files": ["main.js"], "initial": True, "entry": True, "size": 30000}],
            "modules": [
                {"name": "./src/index.js", "size": 3400, "chunks": [0], "reasons": [{"type": "entry"}]},
                {"name": "./node_modules/date-fns/index.js", "size": 18400, "chunks": [0],
                 "reasons": [{"type": "harmony import specifier", "moduleName": "./src/index.js", "userRequest": "date-fns"}]},
                {"name": "./node_modules/@harbor/calendar/index.js", "size": 3000, "chunks": [0],
                 "reasons": [{"type": "harmony import specifier", "moduleName": "./src/index.js", "userRequest": "@harbor/calendar"}]},
                {"name": "./node_modules/@harbor/calendar/node_modules/date-fns/index.js", "size": 5200, "chunks": [0],
                 "reasons": [{"type": "harmony import specifier", "moduleName": "./node_modules/@harbor/calendar/index.js",
                              "userRequest": "date-fns"}]},
            ],
            "entrypoints": {"main": {"chunks": [0]}},
        }
        lock = {"lockfileVersion": 3, "packages": {
            "": {"dependencies": {"date-fns": "^3.6.0", "@harbor/calendar": "^2.3.0"}},
            "node_modules/date-fns": {"version": "3.6.0"},
            "node_modules/@harbor/calendar": {"version": "2.3.0", "dependencies": {"date-fns": "^2.29.0"}},
            "node_modules/@harbor/calendar/node_modules/date-fns": {"version": "2.30.0"},
        }}
        with workdir() as d:
            write(os.path.join(d, "package.json"),
                  json.dumps({"dependencies": {"date-fns": "^3.6.0", "@harbor/calendar": "^2.3.0"}}))
            dump(d, "package-lock.json", lock)
            _, res, _ = run_json(d, dump(d, "stats.json", stats))
        dup = res["duplicates"][0]
        self.assertEqual(dup["package"], "date-fns")
        self.assertEqual([(i["install"], i["version"], i["size"]) for i in dup["installs"]],
                         [("node_modules/date-fns", "3.6.0", 18400),
                          ("node_modules/@harbor/calendar/node_modules/date-fns", "2.30.0", 5200)])
        self.assertEqual(dup["installs"][1]["pulled_in_by"], ["@harbor/calendar (date-fns)"])
        self.assertEqual(res["project"]["dependents"]["date-fns"],
                         ["the app (package.json) ^3.6.0", "@harbor/calendar@2.3.0 ^2.29.0"])
        self.assertEqual(res["project"]["versions"]["date-fns"], {"declared": "^3.6.0", "installed": "3.6.0"})

    def test_namespace_import_with_computed_lookup_is_found(self):
        with workdir() as d:
            write(os.path.join(d, "package.json"), "{}")
            write(os.path.join(d, "src", "Flag.tsx"),
                  'import * as Flags from "worldflags";\nexport const Flag = ({ code }) => Flags[code];\n')
            _, res, _ = run_json(d, dump(d, "stats.json", webpack_stats()))
        self.assertEqual(res["project"]["namespace"], [{"file": "src/Flag.tsx", "package": "worldflags", "name": "Flags"}])

    def test_stdin_reads_no_project_files(self):
        with workdir() as d:
            code, res, _ = run_json(d, "-", stdin=json.dumps(webpack_stats()))
            code_t, out, _ = run(SKILL, SCRIPT, "-", cwd=d, stdin=json.dumps(webpack_stats()))
        self.assertEqual((code, code_t), (0, 0))
        self.assertIsNone(res["project"])
        self.assertIn("Project files: none read", out)

    def test_output_flag_writes_file(self):
        with workdir() as d:
            target = os.path.join(d, "report.json")
            code, out, _ = run(SKILL, SCRIPT, dump(d, "stats.json", webpack_stats()), "--json", "-o", target, cwd=d)
            self.assertEqual((code, out), (0, ""))
            self.assertEqual(json.loads(read(target))["entries"][0]["js_raw"], 120000)


class TestBadInput(unittest.TestCase):
    def assert_exit2(self, *args, contains, stdin=None):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, *[a(d) if callable(a) else a for a in args], cwd=d, stdin=stdin)
        self.assertEqual(code, 2, err)
        self.assertIn(contains, err)
        self.assertNotIn("Traceback", err)

    def test_missing_file_exits_2(self):
        self.assert_exit2(lambda d: os.path.join(d, "nope.json"), contains="cannot read")

    def test_unusable_stats_files_exit_2_with_a_reason(self):
        cases = [("webpack compiled\n{}", "is not JSON"), ("  \n", "is empty"), ("[]", "not an object"),
                 ('{"lighthouseVersion": "12.0.0"}', "Lighthouse report"),
                 ('{"foo": 1}', "is not a webpack stats file"), ('{"modules": []}', "no modules or chunks")]
        for text, msg in cases:
            with self.subTest(text=text):
                self.assert_exit2(lambda d: write(os.path.join(d, "s.json"), text), contains=msg)

    def test_no_stats_argument_exits_2(self):
        self.assert_exit2(contains="give a stats file path")

    def test_malformed_budgets_exit_2(self):
        p = lambda d: dump(d, "s.json", webpack_stats())  # noqa: E731
        self.assert_exit2(p, "--budget", "main:100", contains="ENTRY=SIZE")
        self.assert_exit2(p, "--budget", "main=lots", contains="--budget size")


class TestHelpers(unittest.TestCase):
    def test_parse_budgets_units(self):
        got = m.parse_budgets(["main=170kB", "app=1.5MB", "x=2KiB", "y=gzip:60kB", "z=1000"])
        self.assertEqual(got, [("main", "raw", 170000.0), ("app", "raw", 1500000.0), ("x", "raw", 2048.0),
                               ("y", "gzip", 60000.0), ("z", "raw", 1000.0)])

    def test_strip_hash_keeps_names_and_drops_hashes(self):
        self.assertEqual(m.strip_hash("main.3f2a1b9c.js"), "main.js")
        self.assertEqual(m.strip_hash("index-BxK3a9Qz.js"), "index.js")
        self.assertEqual(m.strip_hash("chunk-vendors.js"), "chunk-vendors.js")
        self.assertEqual(m.strip_hash("my-component.css"), "my-component.css")

    def test_package_of_reads_scoped_nested_pnpm_and_yarn_paths(self):
        self.assertEqual(m.package_of("src/index.js"), None)
        self.assertEqual(m.package_of("node_modules/@harbor/calendar/node_modules/date-fns/index.js"),
                         ("date-fns", "node_modules/@harbor/calendar/node_modules/date-fns", None))
        self.assertEqual(m.package_of("node_modules/.pnpm/@harbor+calendar@2.3.0_react@18.2.0/node_modules/@harbor/calendar/x.js")[::2],
                         ("@harbor/calendar", "2.3.0"))
        self.assertEqual(m.package_of(".yarn/cache/lodash-npm-4.17.21-6382451519-eb835a2e51.zip/node_modules/lodash/lodash.js")[::2],
                         ("lodash", "4.17.21"))

    def test_browserslist_production_section_and_greater_than(self):
        q = m.browserslist_queries("[development]\nchrome >= 120\n[production]\nchrome > 99, safari 15.4\n")
        self.assertEqual(q, ["chrome > 99", "safari 15.4"])
        self.assertEqual(m.parse_browserslist(q), {"chrome": (100,), "safari": (15, 4)})
        self.assertIsNone(m.parse_browserslist(["> 0.5%", "last 2 versions", "not dead"]))

    def test_greater_than_with_minor_version_keeps_the_next_minor(self):
        self.assertLess(m.parse_browserslist(["safari > 15.3"])["safari"], (16,))


if __name__ == "__main__":
    unittest.main()

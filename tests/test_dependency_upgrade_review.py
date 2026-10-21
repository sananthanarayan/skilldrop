import json
import os
import unittest

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "dependency-upgrade-review", "upgrade_diff.py"
SHA_A = "a" * 40
SHA_B = "b" * 40


def fdiff(path, *hunks):
    """One git-style file diff; each hunk is a list of ' '/'+'/'-' prefixed lines."""
    out = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}"]
    for h in hunks:
        old = sum(1 for ln in h if ln[0] in " -")
        new = sum(1 for ln in h if ln[0] in " +")
        out.append(f"@@ -1,{old} +1,{new} @@")
        out += h
    return "\n".join(out) + "\n"


class UpgradeDiffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def analyse(self, diff, title=None):
        return self.m.analyse(self.m.parse_diff(diff), title)

    def named(self, rep, name):
        return [r for r in rep.changes if r["name"] == name]

    # ---------------------------------------------------------- versions

    def test_semver_class_covers_every_jump_kind(self):
        sc = self.m.semver_class
        self.assertEqual(sc("1.4.2", "2.0.0"), "major")
        self.assertEqual(sc("1.4.2", "1.5.0"), "minor")
        self.assertEqual(sc("1.4.2", "1.4.3"), "patch")
        self.assertEqual(sc("0.8.3", "0.9.0"), "minor (0.x: breaking)")
        self.assertEqual(sc("0.0.3", "0.0.4"), "patch (0.0.x: breaking)")
        self.assertEqual(sc("2.1.0", "1.9.9"), "downgrade")
        self.assertEqual(sc("1.2.3", "1.2.3-rc.1"), "prerelease/build")
        self.assertEqual(sc("^1.2.3", "~1.2.3"), "range only")
        self.assertEqual(sc("latest", "1.0.0"), "unknown")

    def test_parse_ver_strips_operators_aliases_and_ranges(self):
        pv = self.m.parse_ver
        self.assertEqual(pv(">=1.2,<2"), (1, 2, 0, ""))
        self.assertEqual(pv("npm:other-pkg@3.1.4"), (3, 1, 4, ""))
        self.assertEqual(pv("==2.31.0"), (2, 31, 0, ""))
        self.assertEqual(pv("v4.1.0"), (4, 1, 0, ""))
        self.assertIsNone(pv("github:owner/repo"))

    def test_host_of_strips_scheme_prefixes_and_credentials(self):
        h = self.m.host_of
        self.assertEqual(h("git+https://user@git.example.test/x.git"), "git.example.test")
        self.assertEqual(h("sparse+https://index.crates.io/"), "index.crates.io")
        self.assertEqual(h("registry+https://github.com/rust-lang/crates.io-index"),
                         "github.com/rust-lang/crates.io-index")
        self.assertIsNone(h(None))

    # ---------------------------------------------------------- diff parsing

    def test_parse_diff_plain_diff_new_file_and_no_newline_marker(self):
        text = ("--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1,2 @@\n"
                "+flask==3.0.0\n+click==8.1.7\n\\ No newline at end of file\n")
        files = self.m.parse_diff(text)
        self.assertEqual([f["path"] for f in files], ["requirements.txt"])
        self.assertEqual(files[0]["hunks"], [[("+", "flask==3.0.0"), ("+", "click==8.1.7")]])

    # ---------------------------------------------------------- npm

    def test_package_json_major_bump_is_merge_after_checks(self):
        diff = fdiff("package.json", ['   "dependencies": {', '-    "quillmark": "^3.4.1",',
                                      '+    "quillmark": "^4.1.0",', '     "other": "1.0.0"'])
        rep, floor, stop, check = self.analyse(diff)
        (r,) = rep.changes
        self.assertEqual((r["name"], r["old"], r["new"], r["class"]), ("quillmark", "^3.4.1", "^4.1.0", "major"))
        self.assertEqual(floor, "MERGE AFTER CHECKS")
        self.assertEqual(stop, [])
        self.assertIn("major: quillmark ^3.4.1 -> ^4.1.0", check)

    def test_package_json_new_postinstall_script_is_do_not_merge(self):
        diff = fdiff("package.json", ['   "scripts": {', '+    "postinstall": "node fetch-binary.js",',
                                      '     "test": "jest"'])
        rep, floor, stop, _ = self.analyse(diff)
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertEqual([f["kind"] for f in rep.flags], ["install-script"])
        self.assertIn("node fetch-binary.js", stop[0])
        self.assertEqual(rep.changes, [])

    def test_package_json_git_dependency_flags_source(self):
        diff = fdiff("package.json", ['   "dependencies": {',
                                      '+    "forked-lib": "git+https://git.example.test/forked-lib.git"'])
        rep, floor, _, _ = self.analyse(diff)
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertEqual(rep.flags[0]["kind"], "source")

    def test_package_lock_transitive_bump_with_install_script_and_moved_host(self):
        diff = fdiff("package-lock.json", [
            '     "node_modules/minimist": {',
            '-      "version": "1.2.5",',
            '-      "resolved": "https://registry.npmjs.org/minimist/-/minimist-1.2.5.tgz",',
            '+      "version": "1.2.8",',
            '+      "resolved": "https://mirror.example.test/minimist/-/minimist-1.2.8.tgz",',
            '+      "hasInstallScript": true,',
            '       "license": "MIT"',
        ])
        rep, floor, stop, _ = self.analyse(diff)
        (r,) = rep.changes
        self.assertEqual((r["old"], r["new"], r["class"]), ("1.2.5", "1.2.8", "patch"))
        self.assertEqual(r["notes"], ["lockfile only (transitive)"])
        self.assertEqual(sorted(f["kind"] for f in rep.flags), ["install-script", "source"])
        self.assertIn("moved from registry.npmjs.org to mirror.example.test",
                      [f["text"] for f in rep.flags if f["kind"] == "source"][0])
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertEqual(len(stop), 2)

    def test_lockfile_change_is_marked_direct_when_manifest_names_it(self):
        diff = (fdiff("package.json", ['   "dependencies": {', '-    "quillmark": "^3.4.1"',
                                       '+    "quillmark": "^4.1.0"'])
                + fdiff("package-lock.json", ['     "node_modules/quillmark": {', '-      "version": "3.4.1",',
                                              '+      "version": "4.1.0",', '       "license": "MIT"']))
        rep, _, _, check = self.analyse(diff)
        lock = [r for r in rep.changes if r["where"] == "lockfile"][0]
        self.assertEqual(lock["notes"][0], "direct")
        # the manifest row is not counted twice in the reasons
        self.assertEqual([c for c in check if c.startswith("major")], ["major: quillmark 3.4.1 -> 4.1.0"])

    def test_nested_lockfile_copy_is_noted(self):
        diff = fdiff("package-lock.json", ['     "node_modules/outer/node_modules/inner": {',
                                           '-      "version": "1.0.0",', '+      "version": "1.0.1",'])
        rep, _, _, _ = self.analyse(diff)
        self.assertEqual(rep.changes[0]["name"], "inner")
        self.assertIn("nested copy under outer", rep.changes[0]["notes"])

    def test_version_lines_with_no_package_in_context_are_unattributed(self):
        diff = fdiff("package-lock.json", ['-      "version": "1.0.0",', '+      "version": "1.0.1",',
                                           '       "license": "MIT"'])
        rep, floor, _, check = self.analyse(diff)
        self.assertEqual(rep.changes, [])
        self.assertEqual(rep.unattributed, {"package-lock.json": 1})
        self.assertEqual(floor, "MERGE AFTER CHECKS")
        self.assertTrue(any("no package name in context" in c for c in check))

    def test_pnpm_requires_build_flags_install_script(self):
        diff = fdiff("pnpm-lock.yaml", ["-  /esbuild@0.19.0:", "+  /esbuild@0.20.0:",
                                        "+    requiresBuild: true", "     dev: true"])
        rep, floor, _, _ = self.analyse(diff)
        (r,) = rep.changes
        self.assertEqual((r["name"], r["old"], r["new"], r["class"]),
                         ("esbuild", "0.19.0", "0.20.0", "minor (0.x: breaking)"))
        self.assertEqual([f["kind"] for f in rep.flags], ["install-script"])
        self.assertEqual(floor, "DO NOT MERGE")

    def test_new_native_npm_helper_is_flagged(self):
        diff = fdiff("package-lock.json", ['+    "node_modules/node-gyp-build": {', '+      "version": "4.8.0",',
                                           '+      "license": "MIT"', '+    },'])
        rep, _, _, _ = self.analyse(diff)
        self.assertEqual(rep.changes[0]["kind"], "added")
        self.assertIn("native", [f["kind"] for f in rep.flags])

    def test_yarn_classic_lock_bump_is_read(self):
        diff = fdiff("yarn.lock", [' lodash@^4.17.20:', '-  version "4.17.20"', '+  version "4.17.21"'])
        rep, _, _, _ = self.analyse(diff)
        self.assertEqual([(r["name"], r["old"], r["new"]) for r in rep.changes], [("lodash", "4.17.20", "4.17.21")])

    # BUG: a Yarn Berry key such as "lodash@npm:^4.17.20": is not recognised, so the bump is unattributed
    @unittest.expectedFailure
    def test_yarn_berry_lock_bump_is_read(self):
        diff = fdiff("yarn.lock", [' "lodash@npm:^4.17.20":', '-  version: 4.17.20', '+  version: 4.17.21'])
        rep, _, _, _ = self.analyse(diff)
        self.assertEqual([(r["name"], r["old"], r["new"]) for r in rep.changes], [("lodash", "4.17.20", "4.17.21")])

    # ---------------------------------------------------------- python

    def test_requirements_patch_bump_has_no_floor_reasons(self):
        diff = fdiff("requirements.txt", ["-requests==2.31.0", "+requests==2.31.1", " flask==3.0.0"])
        rep, floor, stop, check = self.analyse(diff)
        self.assertEqual([(r["name"], r["class"]) for r in rep.changes], [("requests", "patch")])
        self.assertEqual((floor, stop, check), ("none from the diff", [], []))

    def test_requirements_extra_index_url_is_a_stop(self):
        diff = fdiff("requirements-dev.txt", ["+--extra-index-url https://pkgs.example.test/simple", " pytest==8.0.0"])
        rep, floor, _, _ = self.analyse(diff)
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertEqual(rep.flags[0]["kind"], "source")

    def test_requirements_prerelease_target_is_noted(self):
        diff = fdiff("requirements.txt", ["-tidyparse==2.2.0", "+tidyparse==2.3.0rc1"])
        rep, floor, _, _ = self.analyse(diff)
        self.assertIn("target is a prerelease", rep.changes[0]["notes"])
        self.assertEqual(floor, "MERGE AFTER CHECKS")

    def test_poetry_lock_raised_python_floor_is_a_runtime_flag(self):
        diff = fdiff("poetry.lock", [' [[package]]', ' name = "tidyparse"', '-version = "2.2.0"', '+version = "3.0.0"',
                                     '-python-versions = ">=3.8"', '+python-versions = ">=3.10"'])
        rep, floor, _, check = self.analyse(diff)
        self.assertEqual(rep.changes[0]["class"], "major")
        runtime = [f for f in rep.flags if f["kind"] == "runtime"]
        self.assertEqual(len(runtime), 1)
        self.assertIn("requires Python >=3.10 (was >=3.8)", runtime[0]["text"])
        self.assertEqual(floor, "MERGE AFTER CHECKS")

    def test_pyproject_pep508_and_poetry_styles_are_read(self):
        diff = fdiff("pyproject.toml", ['-  "httpx>=0.26,<1",', '+  "httpx>=0.27,<1",',
                                        '-requests = "^2.31"', '+requests = "^2.32"'])
        rep, _, _, _ = self.analyse(diff)
        got = {r["name"]: (r["old"], r["new"]) for r in rep.changes}
        self.assertEqual(got, {"httpx": (">=0.26,<1", ">=0.27,<1"), "requests": ("^2.31", "^2.32")})

    # ---------------------------------------------------------- go, cargo, maven, gradle

    def test_go_mod_and_go_sum_same_bump_reported_once_with_indirect_note(self):
        diff = (fdiff("go.mod", ["-\tgolang.org/x/text v0.13.0 // indirect", "+\tgolang.org/x/text v0.14.0 // indirect"])
                + fdiff("go.sum", ["-golang.org/x/text v0.13.0 h1:AAAA=", "-golang.org/x/text v0.13.0/go.mod h1:BBBB=",
                                   "+golang.org/x/text v0.14.0 h1:CCCC=", "+golang.org/x/text v0.14.0/go.mod h1:DDDD="]))
        rep, _, _, _ = self.analyse(diff)
        (r,) = rep.changes
        self.assertEqual((r["file"], r["class"], r["notes"]), ("go.mod", "minor (0.x: breaking)", ["indirect"]))

    def test_go_mod_replace_directive_is_a_stop(self):
        diff = fdiff("go.mod", ["+replace example.test/lib => ../lib-fork"])
        rep, floor, _, _ = self.analyse(diff)
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertIn("replace directive", rep.flags[0]["text"])

    def test_cargo_lock_new_sys_crate_is_native(self):
        diff = fdiff("Cargo.lock", ["+[[package]]", '+name = "openssl-sys"', '+version = "0.9.99"',
                                    '+source = "registry+https://github.com/rust-lang/crates.io-index"'])
        rep, floor, stop, _ = self.analyse(diff)
        self.assertEqual((rep.changes[0]["kind"], rep.changes[0]["new"]), ("added", "0.9.99"))
        self.assertEqual([f["kind"] for f in rep.flags], ["native"])  # default registry: no source flag
        self.assertEqual((floor, stop), ("MERGE AFTER CHECKS", []))

    def test_pom_and_gradle_versions_are_read(self):
        diff = (fdiff("pom.xml", ["     <artifactId>jackson-databind</artifactId>", "-    <version>2.15.0</version>",
                                  "+    <version>2.16.1</version>", "-    <netty.version>4.1.100</netty.version>",
                                  "+    <netty.version>4.1.104</netty.version>"])
                + fdiff("build.gradle", ["-    implementation 'com.example:okclient:4.9.0'",
                                         "+    implementation 'com.example:okclient:5.0.0'"]))
        rep, _, _, _ = self.analyse(diff)
        got = {r["name"]: (r["ecosystem"], r["class"]) for r in rep.changes}
        self.assertEqual(got, {"jackson-databind": ("maven", "minor"), "netty.version": ("maven", "patch"),
                               "com.example:okclient": ("gradle", "major")})

    def test_npmrc_registry_change_is_a_stop(self):
        diff = fdiff(".npmrc", ["-registry=https://registry.npmjs.org/", "+registry=https://npm.example.test/"])
        rep, floor, _, _ = self.analyse(diff)
        self.assertEqual(floor, "DO NOT MERGE")
        self.assertEqual(len(rep.flags), 1)

    # ---------------------------------------------------------- github actions

    def test_action_tag_to_sha_with_comment_is_unverified_pin(self):
        diff = fdiff(".github/workflows/ci.yml", ["-      - uses: actions/checkout@v4.1.0",
                                                  f"+      - uses: actions/checkout@{SHA_A} # v4.1.1"])
        rep, floor, stop, check = self.analyse(diff)
        (r,) = rep.changes
        self.assertEqual(r["class"], "patch")
        self.assertIn("pin strengthened from tag to SHA", r["notes"])
        pin = [f for f in rep.flags if f["kind"] == "pin"][0]
        self.assertIn("UNVERIFIED", pin["text"])
        self.assertIn("refs/tags/v4.1.1", pin["text"])
        self.assertEqual((floor, stop), ("MERGE AFTER CHECKS", []))

    def test_action_sha_to_tag_is_marked_weakened(self):
        diff = fdiff(".github/workflows/ci.yml", [f"-      - uses: actions/setup-node@{SHA_A} # v4.0.0",
                                                  "+      - uses: actions/setup-node@v4.0.1"])
        rep, floor, _, check = self.analyse(diff)
        self.assertIn("pin WEAKENED from SHA to tag", rep.changes[0]["notes"])
        self.assertTrue(any("WEAKENED" in c for c in check))
        self.assertNotEqual(floor, "none from the diff")

    def test_one_tag_pinned_to_two_shas_is_a_pin_conflict(self):
        diff = (fdiff(".github/workflows/ci.yml", ["-      - uses: actions/cache@v3",
                                                   f"+      - uses: actions/cache@{SHA_A} # v4.0.2"])
                + fdiff(".github/workflows/release.yml", ["-      - uses: actions/cache@v3",
                                                          f"+      - uses: actions/cache@{SHA_B} # v4.0.2"]))
        rep, floor, stop, _ = self.analyse(diff)
        conflict = [f for f in rep.flags if f["kind"] == "pin-conflict"]
        self.assertEqual(len(conflict), 1)
        self.assertIn("pinned to 2 different commits", conflict[0]["text"])
        self.assertEqual(floor, "DO NOT MERGE")

    def test_local_and_docker_actions_are_ignored(self):
        diff = fdiff(".github/workflows/ci.yml", ["+      - uses: ./.github/actions/setup@v1",
                                                  "+      - uses: docker://alpine@3.19"])
        rep, floor, _, _ = self.analyse(diff)
        self.assertEqual((rep.changes, rep.flags, floor), ([], [], "none from the diff"))

    # ---------------------------------------------------------- title

    def test_title_marks_changes_beyond_the_title(self):
        diff = (fdiff("requirements.txt", ["-tidyparse==2.2.0", "+tidyparse==2.2.1",
                                           "-charset-normalizer==3.3.0", "+charset-normalizer==3.3.2"]))
        rep, _, _, _ = self.analyse(diff, "Bump tidyparse from 2.2.0 to 2.2.1")
        self.assertEqual({r["name"]: r["in_title"] for r in rep.changes},
                         {"tidyparse": True, "charset-normalizer": False})

    # BUG: the full-name check is a plain substring, so "ws" counts as named in a title about "aws-sdk"
    @unittest.expectedFailure
    def test_short_name_is_not_matched_inside_another_word(self):
        diff = fdiff("package.json", ['   "dependencies": {', '-    "ws": "^7.0.0",', '+    "ws": "^8.0.0",'])
        rep, _, _, _ = self.analyse(diff, "Bump aws-sdk from 2.0.0 to 3.0.0")
        self.assertFalse(rep.changes[0]["in_title"])


class UpgradeDiffCliTest(unittest.TestCase):
    BUMP = fdiff("requirements.txt", ["-requests==2.31.0", "+requests==3.0.0"])

    def test_json_format_reports_floor_and_changes(self):
        with workdir() as d:
            p = write(os.path.join(d, "pr.diff"), self.BUMP)
            code, out, err = run(SKILL, SCRIPT, p, "--format", "json")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["floor_verdict"], "MERGE AFTER CHECKS")
        self.assertEqual([(c["name"], c["class"]) for c in data["changes"]], [("requests", "major")])
        self.assertEqual(data["files"], [{"path": "requirements.txt", "read": True}])

    def test_markdown_from_stdin_lists_beyond_title_and_other_files(self):
        diff = self.BUMP + fdiff("README.md", ["+hello"])
        code, out, err = run(SKILL, SCRIPT, "-", "--title", "Bump flask", stdin=diff)
        self.assertEqual(code, 0, err)
        self.assertIn("**Floor verdict: MERGE AFTER CHECKS**", out)
        self.assertIn("## Beyond the title (1)", out)
        self.assertIn("not named in the title", out)
        self.assertIn("`README.md`", out.split("Other files in the diff")[1].splitlines()[0])

    def test_output_flag_writes_the_report_to_a_file(self):
        with workdir() as d:
            p = write(os.path.join(d, "pr.diff"), self.BUMP)
            dest = os.path.join(d, "report.md")
            code, out, _ = run(SKILL, SCRIPT, p, "-o", dest)
            self.assertEqual((code, out), (0, ""))
            self.assertIn("# Dependency upgrade diff", read(dest))

    def test_missing_file_exits_2_with_message(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, os.path.join(d, "nope.diff"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        self.assertNotIn("Traceback", err)

    def test_text_that_is_not_a_diff_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin="just some prose\n")
        self.assertEqual(code, 2)
        self.assertIn("no unified diff", err)

    def test_empty_input_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin="")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_diff_with_no_dependency_files_exits_2(self):
        code, _, err = run(SKILL, SCRIPT, "-", stdin=fdiff("src/app.py", ["+print('hi')"]))
        self.assertEqual(code, 2)
        self.assertIn("src/app.py", err)


if __name__ == "__main__":
    unittest.main()

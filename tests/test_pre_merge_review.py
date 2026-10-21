import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

from tests.support import load, run, workdir, write, read

SKILL, SCRIPT = "pre-merge-review", "gate.py"
PY = f'"{sys.executable}"'


def py_cmd(code):
    """A shell command that runs a one-line Python program, on any OS."""
    return f'{PY} -c "{code}"'


class DetectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def detect(self, files, tools=()):
        with workdir() as d:
            for name, text in files.items():
                write(os.path.join(d, name), text)
            which = lambda t: f"/fake/bin/{t}" if t in tools else None
            with mock.patch.object(self.m.shutil, "which", which):
                return self.m.detect(d)

    def test_package_json_scripts_run_in_lint_typecheck_test_order(self):
        pkg = json.dumps({"scripts": {"test": "jest", "typecheck": "tsc", "lint": "eslint ."}})
        self.assertEqual(self.detect({"package.json": pkg}), ["npm run lint", "npm run typecheck", "npm test"])

    def test_package_json_only_lists_scripts_that_exist(self):
        self.assertEqual(self.detect({"package.json": '{"scripts": {"test": "jest"}}'}), ["npm test"])

    def test_malformed_package_json_detects_nothing(self):
        self.assertEqual(self.detect({"package.json": "{not json"}), [])

    def test_python_project_uses_only_installed_tools(self):
        self.assertEqual(self.detect({"pyproject.toml": ""}, tools=("ruff", "mypy", "pytest")),
                         ["ruff check .", "mypy .", "pytest -q"])
        self.assertEqual(self.detect({"pyproject.toml": ""}, tools=()), [])

    def test_mypy_needs_mypy_ini_or_pyproject(self):
        self.assertEqual(self.detect({"setup.py": ""}, tools=("mypy", "pytest")), ["pytest -q"])
        self.assertEqual(self.detect({"setup.py": "", "mypy.ini": ""}, tools=("mypy",)), ["mypy ."])

    def test_go_module_gets_vet_and_test(self):
        self.assertEqual(self.detect({"go.mod": "module example.test/x\n"}), ["go vet ./...", "go test ./..."])

    def test_makefile_targets_are_the_fallback(self):
        mk = "lint:\n\techo lint\ntesting:\n\techo no\ntest: deps\n\techo test\n"
        self.assertEqual(self.detect({"Makefile": mk}), ["make lint", "make test"])

    def test_makefile_ignored_when_another_stack_was_detected(self):
        files = {"Makefile": "lint:\n\techo\n", "go.mod": "module example.test/x\n"}
        self.assertEqual(self.detect(files), ["go vet ./...", "go test ./..."])

    def test_empty_folder_detects_nothing(self):
        self.assertEqual(self.detect({}), [])


class ConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def test_load_config_accepts_dict_or_bare_list(self):
        with workdir() as d:
            a = write(os.path.join(d, "a.json"), '{"commands": ["pytest -q", "ruff check ."]}')
            b = write(os.path.join(d, "b.json"), '["npm test"]')
            self.assertEqual(self.m.load_config(a), ["pytest -q", "ruff check ."])
            self.assertEqual(self.m.load_config(b), ["npm test"])

    def test_load_config_rejects_non_string_commands(self):
        with workdir() as d:
            p = write(os.path.join(d, "bad.json"), '{"commands": ["ok", 3]}')
            with self.assertRaises(SystemExit) as cm:
                self.m.load_config(p)
        self.assertIn("list of command strings", str(cm.exception))


class GateCliTest(unittest.TestCase):
    def test_all_commands_pass_is_green_exit_0(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--cmd", py_cmd("pass"), "--cmd", py_cmd("pass"))
        self.assertEqual(code, 0, err)
        self.assertIn("GATE: GREEN", out)
        self.assertIn("all 2 command(s) passed", out)

    def test_one_failure_is_red_exit_1_and_later_commands_still_run(self):
        with workdir() as d:
            fail = py_cmd("raise SystemExit(3)")
            touch = py_cmd("open('ran.txt', 'w').close()")
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--cmd", fail, "--cmd", touch)
            self.assertTrue(os.path.exists(os.path.join(d, "ran.txt")))
        self.assertEqual(code, 1)
        self.assertIn("rc=3", out)
        self.assertIn("GATE: RED", out)
        self.assertIn("1/2 command(s) failed", out)

    def test_commands_run_in_the_root_folder(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, "--root", d, "--cmd", py_cmd("open('here.txt', 'w').close()"))
            self.assertEqual(code, 0, err)
            self.assertTrue(os.path.exists(os.path.join(d, "here.txt")))

    def test_list_prints_commands_without_running_them(self):
        with workdir() as d:
            touch = py_cmd("open('ran.txt', 'w').close()")
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--cmd", touch, "--list")
            self.assertFalse(os.path.exists(os.path.join(d, "ran.txt")))
        self.assertEqual(code, 0)
        self.assertIn("gate would run, in order:", out)
        self.assertIn("ran.txt", out)

    def test_list_shows_auto_detected_commands(self):
        with workdir() as d:
            write(os.path.join(d, "go.mod"), "module example.test/x\n")
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--list")
        self.assertEqual(code, 0)
        self.assertIn("- go vet ./...", out)
        self.assertIn("- go test ./...", out)

    def test_config_commands_are_run(self):
        with workdir() as d:
            cfg = write(os.path.join(d, "gate.json"), json.dumps({"commands": [py_cmd("raise SystemExit(1)")]}))
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--config", cfg)
        self.assertEqual(code, 1)
        self.assertIn("GATE: RED", out)

    def test_cmd_takes_precedence_over_config(self):
        with workdir() as d:
            cfg = write(os.path.join(d, "gate.json"), json.dumps([py_cmd("raise SystemExit(1)")]))
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--config", cfg, "--cmd", py_cmd("pass"))
        self.assertEqual(code, 0)
        self.assertIn("GATE: GREEN", out)

    def test_nothing_to_run_exits_2_with_message(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, "--root", d)
        self.assertEqual(code, 2)
        self.assertIn("no verify commands", err)
        self.assertNotIn("GATE", out)

    def test_bad_config_shape_exits_with_message(self):
        with workdir() as d:
            cfg = write(os.path.join(d, "gate.json"), '{"commands": "npm test"}')
            code, _, err = run(SKILL, SCRIPT, "--root", d, "--config", cfg)
        self.assertNotEqual(code, 0)
        self.assertIn("--config must hold a list", err)
        self.assertNotIn("Traceback", err)

    # BUG: a missing or malformed --config file ends in a raw traceback, not a gate: message
    @unittest.expectedFailure
    def test_missing_config_file_fails_without_traceback(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, "--root", d, "--config", os.path.join(d, "missing.json"))
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)


class HookTest(unittest.TestCase):
    """install_hook / uninstall_hook with the git lookup stubbed to a plain folder."""

    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, SCRIPT)

    def setUp(self):
        self._wd = workdir()
        self.hooks = os.path.join(self._wd.__enter__(), "hooks")
        patcher = mock.patch.object(self.m, "_hooks_dir", lambda root: self.hooks)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._wd.__exit__, None, None, None)
        self.hook = os.path.join(self.hooks, "pre-commit")

    def quiet(self, fn, *args):
        with mock.patch("builtins.print"):
            return fn(*args)

    def test_install_writes_shebang_marker_and_quoted_commands(self):
        self.assertEqual(self.quiet(self.m.install_hook, ".", ["npm test", "npm run lint"], None), 0)
        body = read(self.hook)
        self.assertTrue(body.startswith("#!/bin/sh\n"))
        self.assertIn("# >>> skilldrop-gate >>>", body)
        self.assertIn("--cmd 'npm test' --cmd 'npm run lint'", body)
        self.assertIn("exit 1", body)

    @unittest.skipIf(os.name == "nt", "POSIX execute bit")
    def test_install_makes_the_hook_executable(self):
        self.quiet(self.m.install_hook, ".", ["npm test"], None)
        self.assertTrue(os.access(self.hook, os.X_OK))

    def test_install_twice_does_not_duplicate_the_block(self):
        self.quiet(self.m.install_hook, ".", ["npm test"], None)
        self.quiet(self.m.install_hook, ".", ["other"], None)
        body = read(self.hook)
        self.assertEqual(body.count("# >>> skilldrop-gate >>>"), 1)
        self.assertNotIn("other", body)

    def test_uninstall_removes_only_the_gate_block(self):
        write(self.hook, "#!/bin/sh\necho existing-hook\n")
        self.quiet(self.m.install_hook, ".", ["npm test"], None)
        self.quiet(self.m.uninstall_hook, ".")
        body = read(self.hook)
        self.assertNotIn("skilldrop-gate", body)
        self.assertIn("echo existing-hook", body)
        self.assertTrue(body.startswith("#!/bin/sh\n"))

    def test_uninstall_leaves_a_foreign_hook_untouched(self):
        write(self.hook, "#!/bin/sh\necho mine\n")
        self.assertEqual(self.quiet(self.m.uninstall_hook, "."), 0)
        self.assertEqual(read(self.hook), "#!/bin/sh\necho mine\n")

    def test_uninstall_with_no_hook_is_a_no_op(self):
        self.assertEqual(self.quiet(self.m.uninstall_hook, "."), 0)
        self.assertFalse(os.path.exists(self.hook))


@unittest.skipUnless(shutil.which("git"), "git not installed")
class HookGitTest(unittest.TestCase):
    def test_install_and_uninstall_in_a_real_repo(self):
        with workdir() as d:
            subprocess.run(["git", "init", "-q", d], check=True, capture_output=True)
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--install-hook", "--cmd", "npm test")
            self.assertEqual(code, 0, err)
            hook = os.path.join(d, ".git", "hooks", "pre-commit")
            self.assertIn("skilldrop-gate", read(hook))
            code, _, _ = run(SKILL, SCRIPT, "--root", d, "--uninstall-hook")
            self.assertEqual(code, 0)
            self.assertNotIn("skilldrop-gate", read(hook))

    def test_install_outside_a_repo_fails_with_message(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, "--root", d, "--install-hook", "--cmd", "npm test",
                               env={"GIT_CEILING_DIRECTORIES": os.path.dirname(d)})
        self.assertNotEqual(code, 0)
        self.assertIn("not a git repository", err)


if __name__ == "__main__":
    unittest.main()

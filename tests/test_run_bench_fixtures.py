"""run_bench.py's fixture copying: real names for .fixture files, and git-history.json replayed
into a real repository (RFC-0058, RFC-0065)."""
import json
import os
import shutil
import subprocess
import sys
import unittest

from tests.support import ROOT, workdir, write

sys.path.insert(0, ROOT)
import run_bench  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitHistoryFixtureTest(unittest.TestCase):
    def log(self, ws):
        return subprocess.run(["git", "log", "--date=short", "--format=%ad|%an|%s", "--name-status"],
                              cwd=ws, capture_output=True, text=True, check=True).stdout

    def test_history_is_replayed_with_dates_authors_writes_and_deletes(self):
        with workdir() as src, workdir() as ws:
            write(os.path.join(src, "svc", "a.py"), "v1\n")
            write(os.path.join(src, "svc", "old.py"), "x\n")
            write(os.path.join(src, "package.json.fixture"), "{}\n")
            write(os.path.join(src, "git-history.json"), json.dumps({
                "start": {"date": "2025-01-10", "author": "Ana", "message": "Import"},
                "commits": [{"date": "2025-03-02", "author": "Ben Ode", "message": "Change a",
                             "files": {"svc/a.py": "v2\n", "svc/new/b.py": "b\n"}},
                            {"date": "2025-04-02", "author": "Ana", "message": "Remove old",
                             "files": {"svc/old.py": None}}]}))
            run_bench.copy_fixtures(src, ws)
            self.assertFalse(os.path.exists(os.path.join(ws, "git-history.json")))
            self.assertTrue(os.path.exists(os.path.join(ws, "package.json")))
            with open(os.path.join(ws, "svc", "a.py")) as fh:
                self.assertEqual(fh.read(), "v2\n")
            self.assertFalse(os.path.exists(os.path.join(ws, "svc", "old.py")))
            log = self.log(ws)
            self.assertIn("2025-04-02|Ana|Remove old", log)
            self.assertIn("2025-03-02|Ben Ode|Change a", log)
            self.assertIn("2025-01-10|Ana|Import", log)
            self.assertIn("A\tsvc/new/b.py", log)

    def test_the_judge_sees_the_history(self):
        with workdir() as src, workdir() as ws:
            write(os.path.join(src, "a.py"), "v1\n")
            write(os.path.join(src, "git-history.json"), json.dumps({
                "commits": [{"date": "2025-03-02", "author": "Ben Ode", "message": "Change a", "files": {"a.py": "v2\n"}}]}))
            run_bench.copy_fixtures(src, ws)
            seen = run_bench.workspace_files(ws, src)
            self.assertIn('<git-history input="true"', seen)
            self.assertIn("Author: Ben Ode", seen)
            self.assertIn("Date: 2025-03-02", seen)
            self.assertIn("+v2", seen)

    def test_a_path_outside_the_fixture_is_refused(self):
        with workdir() as src, workdir() as ws:
            write(os.path.join(src, "git-history.json"), json.dumps({
                "commits": [{"date": "2025-03-02", "message": "Escape", "files": {"../evil.txt": "x"}}]}))
            with self.assertRaises(ValueError):
                run_bench.copy_fixtures(src, ws)


class FixtureNameTest(unittest.TestCase):
    def test_fixture_suffix_is_stripped(self):
        self.assertEqual(run_bench.workspace_name("a/go.mod.fixture"), "a/go.mod")
        self.assertEqual(run_bench.workspace_name("a/notes.md"), "a/notes.md")


if __name__ == "__main__":
    unittest.main()

import calendar
import os
import shutil
import subprocess
import unittest

from tests.support import load, read, run, workdir, write

SKILL = "agent-incident-response"
KEY = "sk-test-FAKEFAKE0000abcd"          # 24 chars; prefix below is its first 12
OTHER = "sk-test-FAKEFAKE9999wxyz"        # same prefix, different key
PREFIX = KEY[:12]
HAS_GIT = shutil.which("git") is not None


class FindSecretExposureTest(unittest.TestCase):
    SCRIPT = "find_secret_exposure.py"

    @classmethod
    def setUpClass(cls):
        cls.m = load(SKILL, cls.SCRIPT)

    def cli(self, *args, stdin=None, cwd=None):
        return run(SKILL, self.SCRIPT, *args, stdin=stdin, cwd=cwd)

    # --- pure helpers -------------------------------------------------------------------

    def test_mask_shows_first_8_last_4_and_length(self):
        self.assertEqual(self.m.mask(KEY), "sk-test-…abcd (len 24)")

    def test_mask_short_token_shows_only_first_4(self):
        self.assertEqual(self.m.mask("abcdefghij"), "abcd… (len 10)")

    def test_line_stamp_converts_offset_to_utc(self):
        self.assertEqual(self.m.line_stamp("2026-10-19 22:15:03+0200 GET /v1 key=x"), "2026-10-19 20:15:03Z")
        self.assertEqual(self.m.line_stamp("2026-10-19T20:15:03.123Z ok"), "2026-10-19 20:15:03Z")

    def test_line_stamp_without_timezone_or_stamp(self):
        self.assertEqual(self.m.line_stamp("2026-10-19 20:15:03 ok"), "2026-10-19 20:15:03 (no timezone on the line)")
        self.assertEqual(self.m.line_stamp("no time here"), "no timestamp on the line")

    def test_needle_suffix_keeps_only_matching_key(self):
        n = self.m.Needle(prefix=PREFIX, suffix="abcd")
        self.assertEqual(n.tokens("a={} b={}".format(KEY, OTHER)), ["sk-test-…abcd (len 24)"])

    def test_needle_full_key_ignores_other_keys_with_same_prefix(self):
        n = self.m.Needle(full=KEY)
        self.assertEqual(n.tokens("x {}.".format(OTHER)), [])
        self.assertEqual(n.tokens("x {}.".format(KEY)), ["sk-test-…abcd (len 24)"])

    # --- logs ---------------------------------------------------------------------------

    def test_log_hits_with_line_numbers_and_stamps_never_the_key(self):
        with workdir() as d:
            log = write(os.path.join(d, "ci.log"),
                        "2026-10-19T20:00:00Z start\n"
                        "2026-10-19T20:01:00Z using key {}\n"
                        "plain line with {}.\n".format(KEY, KEY))
            code, out, err = self.cli("--prefix", PREFIX, "--log", log)
        self.assertEqual(code, 0, err)
        self.assertIn("- line 2, 2026-10-19 20:01:00Z, sk-test-…abcd (len 24)", out)
        self.assertIn("- line 3, no timestamp on the line, sk-test-…abcd (len 24)", out)
        self.assertNotIn(KEY, out)

    def test_two_keys_sharing_prefix_are_reported(self):
        with workdir() as d:
            log = write(os.path.join(d, "ci.log"), "{}\n{}\n".format(KEY, OTHER))
            code, out, err = self.cli("--prefix", PREFIX, "--log", log)
        self.assertIn("2 different keys match this prefix", out)
        self.assertIn("--suffix", out)

    def test_key_from_stdin(self):
        with workdir() as d:
            log = write(os.path.join(d, "ci.log"), "{}\n{}\n".format(OTHER, KEY))
            code, out, err = self.cli("--key-stdin", "--log", log, stdin=KEY + "\n")
        self.assertEqual(code, 0, err)
        self.assertIn("- line 2,", out)
        self.assertNotIn("- line 1,", out)
        self.assertNotIn(KEY, out)

    def test_log_without_key_says_not_found(self):
        with workdir() as d:
            log = write(os.path.join(d, "ci.log"), "nothing here\n")
            code, out, err = self.cli("--prefix", PREFIX, "--log", log)
        self.assertEqual(code, 0, err)
        self.assertIn("Not found.", out)
        self.assertIn("revoke it regardless", out)

    def test_missing_log_reported_not_crashed(self):
        with workdir() as d:
            code, out, err = self.cli("--prefix", PREFIX, "--log", os.path.join(d, "nope.log"))
        self.assertEqual(code, 0, err)
        self.assertIn("Not scanned: no such file", out)

    def test_out_flag_writes_report(self):
        with workdir() as d:
            log = write(os.path.join(d, "ci.log"), KEY + "\n")
            dest = os.path.join(d, "report.md")
            code, out, err = self.cli("--prefix", PREFIX, "--log", log, "-o", dest)
            self.assertEqual(code, 0, err)
            self.assertIn("wrote", out)
            self.assertIn("# Where the key appears", read(dest))

    # --- bad input ----------------------------------------------------------------------

    def test_short_prefix_refused(self):
        code, out, err = self.cli("--prefix", "sk-test", "--log", "x.log")
        self.assertEqual(code, 2)
        self.assertIn("at least 10 characters", err)

    def test_short_stdin_key_refused(self):
        code, out, err = self.cli("--key-stdin", "--log", "x.log", stdin="short")
        self.assertEqual(code, 2)
        self.assertIn("shorter than 10", err)

    def test_needs_repo_or_log(self):
        code, out, err = self.cli("--prefix", PREFIX)
        self.assertEqual(code, 2)
        self.assertIn("give --repo, --log, or both", err)

    def test_prefix_and_stdin_are_exclusive(self):
        code, out, err = self.cli("--prefix", PREFIX, "--key-stdin", "--log", "x.log", stdin=KEY)
        self.assertEqual(code, 2)

    def test_repo_that_is_not_a_folder(self):
        with workdir() as d:
            code, out, err = self.cli("--prefix", PREFIX, "--repo", os.path.join(d, "nope"))
        self.assertEqual(code, 0, err)
        self.assertIn("Not scanned: no such directory", out)

    # --- git history --------------------------------------------------------------------

    def git(self, repo, *args, when=None):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, HOME=repo,
                   GIT_AUTHOR_NAME="Test Author", GIT_AUTHOR_EMAIL="author@example.invalid",
                   GIT_COMMITTER_NAME="Test Author", GIT_COMMITTER_EMAIL="author@example.invalid")
        if when:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = "@{} +0000".format(when)
        subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", repo] + list(args),
                       check=True, capture_output=True, env=env)

    def make_repo(self, d):
        t0 = calendar.timegm((2026, 10, 19, 20, 0, 0))
        self.git(d, "init", "-q")
        self.git(d, "symbolic-ref", "HEAD", "refs/heads/main")
        write(os.path.join(d, "README.md"), "hello\n")
        self.git(d, "add", "README.md")
        self.git(d, "commit", "-q", "-m", "init", when=t0)
        write(os.path.join(d, "config.env"), "API_KEY={}\n".format(KEY))
        self.git(d, "add", "config.env")
        self.git(d, "commit", "-q", "-m", "add config", when=t0 + 60)
        write(os.path.join(d, "config.env"), "API_KEY=${API_KEY}\n")
        self.git(d, "commit", "-q", "-am", "remove key", when=t0 + 120)
        self.git(d, "tag", "v1")

    @unittest.skipUnless(HAS_GIT, "git not installed")
    def test_git_history_finds_adding_and_removing_commits(self):
        with workdir() as d:
            self.make_repo(d)
            res, err = self.m.scan_repo(d, self.m.Needle(prefix=PREFIX))
        self.assertIsNone(err)
        commits = sorted(res["commits"], key=lambda c: c["authored"])
        self.assertEqual([(c["authored"], c["added"], c["removed"]) for c in commits],
                         [("2026-10-19 20:01:00Z", ["config.env"], []),
                          ("2026-10-19 20:02:00Z", [], ["config.env"])])
        self.assertEqual(commits[0]["refs"], ["main", "tag v1"])
        self.assertEqual(res["present"], {"HEAD": [], "working copy": []})

    @unittest.skipUnless(HAS_GIT, "git not installed")
    def test_key_still_in_working_copy_and_head(self):
        with workdir() as d:
            self.make_repo(d)
            write(os.path.join(d, "notes.txt"), "old key was {}\n".format(KEY))
            res, err = self.m.scan_repo(d, self.m.Needle(prefix=PREFIX))
        self.assertEqual(res["present"]["HEAD"], [])
        self.assertEqual(res["present"]["working copy"], ["notes.txt:1"])

    @unittest.skipUnless(HAS_GIT, "git not installed")
    def test_git_report_names_first_commit_and_hides_key(self):
        with workdir() as d:
            self.make_repo(d)
            code, out, err = self.cli("--prefix", PREFIX, "--repo", d)
        self.assertEqual(code, 0, err)
        self.assertIn("First commit that adds it:", out)
        self.assertIn("authored 2026-10-19 20:01:00Z", out)
        self.assertIn("removes it from: config.env", out)
        self.assertIn("In HEAD now: not present", out)
        self.assertNotIn(KEY, out)

    @unittest.skipUnless(HAS_GIT, "git not installed")
    def test_folder_that_is_not_a_git_repo(self):
        with workdir() as d:
            code, out, err = self.cli("--prefix", PREFIX, "--repo", d,
                                      cwd=d)
        self.assertEqual(code, 0, err)
        self.assertIn("Not scanned: not a git repository", out)


CSV = ("date_hour_utc,api_key_name,model,user_agent,requests,cost_usd\n"
       "2026-10-19T18:00,ci-key,model-medium,ci-runner/1.0,10,1.10\n"
       "2026-10-19T20:00,ci-key,model-medium,ci-runner/1.0,20,2.20\n"
       '2026-10-19T21:00,ci-key,model-large,curl/8.0,"1,000","1,234.56"\n'
       "2026-10-19T22:00,ci-key,model-large,curl/8.0,500,$0.10\n")
LARGE = "api_key_name=ci-key | model=model-large | user_agent=curl/8.0"
MEDIUM = "api_key_name=ci-key | model=model-medium | user_agent=ci-runner/1.0"


class UsageSplitTest(unittest.TestCase):
    SCRIPT = "usage_split.py"

    def split(self, csv_text, *args):
        with workdir() as d:
            path = write(os.path.join(d, "usage.csv"), csv_text)
            return run(SKILL, self.SCRIPT, path, *args)

    def test_groups_by_key_model_and_client_largest_first(self):
        code, out, err = self.split(CSV)
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "Rows: 4   Total: $1,237.96")
        self.assertEqual(lines[1], "Grouped by: api_key_name, model, user_agent   Cost column: cost_usd"
                                   "   Time column: date_hour_utc")
        self.assertEqual(lines[3], "$1,234.66  {}  (99.7%)".format(LARGE))
        self.assertEqual(lines[4], "    rows=2 requests=1,500 first=2026-10-19T21:00 last=2026-10-19T22:00")
        self.assertIn("$3.30  {}  (0.3%)".format(MEDIUM), lines)

    def test_cost_summed_exactly(self):
        csv_text = "model,cost\n" + "m,0.10\n" * 3 + "m,0.004\n"
        code, out, err = self.split(csv_text, "--by", "model")
        self.assertEqual(code, 0, err)
        self.assertIn("$0.30  model=m  (100.0%)", out)

    def test_since_drops_earlier_rows(self):
        code, out, err = self.split(CSV, "--since", "2026-10-19T20:00")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("Rows: 3 (2026-10-19T20:00 to end)   Total: $1,236.86"))
        self.assertIn("$2.20  {}".format(MEDIUM), out)

    def test_until_is_exclusive(self):
        code, out, err = self.split(CSV, "--until", "2026-10-19T21:00")
        self.assertTrue(out.startswith("Rows: 2 (start to 2026-10-19T21:00)   Total: $3.30"))
        self.assertNotIn("model-large", out)

    def test_expect_marks_unexplained_traffic(self):
        code, out, err = self.split(CSV, "--expect", "model=model-medium", "--expect", "user_agent=ci-runner/1.0")
        self.assertEqual(code, 0, err)
        self.assertIn("{}  (99.7%)  UNEXPECTED (model, user_agent differs)".format(LARGE), out)
        medium = next(l for l in out.splitlines() if MEDIUM in l)
        self.assertNotIn("UNEXPECTED", medium)

    def test_by_overrides_grouping(self):
        code, out, err = self.split(CSV, "--by", "user_agent")
        self.assertIn("$1,234.66  user_agent=curl/8.0  (99.7%)", out)
        self.assertIn("$3.30  user_agent=ci-runner/1.0  (0.3%)", out)

    def test_cost_flag_picks_column(self):
        csv_text = "model,list_price,billed\nm,9.00,1.25\nm,9.00,0.75\n"
        code, out, err = self.split(csv_text, "--by", "model", "--cost", "billed")
        self.assertIn("Total: $2.00", out)

    def test_unreadable_cost_row_skipped_and_named(self):
        csv_text = "model,cost_usd\nm,1.00\nm,n/a\nm,2.00\n"
        code, out, err = self.split(csv_text)
        self.assertEqual(code, 0, err)
        self.assertIn("Rows: 2   Total: $3.00", out)
        self.assertIn("Skipped rows with an unreadable cost (CSV line numbers): 3", out)

    def test_byte_order_mark_is_ignored(self):
        code, out, err = self.split("﻿model,cost_usd\nm,1.00\n")
        self.assertEqual(code, 0, err)
        self.assertIn("Grouped by: model", out)

    def test_stdin_input(self):
        code, out, err = run(SKILL, self.SCRIPT, "-", stdin=CSV)
        self.assertEqual(code, 0, err)
        self.assertIn("Total: $1,237.96", out)

    def test_output_flag_writes_file(self):
        with workdir() as d:
            path = write(os.path.join(d, "usage.csv"), CSV)
            dest = os.path.join(d, "split.txt")
            code, out, err = run(SKILL, self.SCRIPT, path, "-o", dest)
            self.assertEqual(code, 0, err)
            self.assertTrue(read(dest).startswith("Rows: 4"))

    def test_missing_file_exits_2(self):
        with workdir() as d:
            code, out, err = run(SKILL, self.SCRIPT, os.path.join(d, "nope.csv"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_empty_export_exits_2(self):
        code, out, err = self.split("")
        self.assertEqual(code, 2)
        self.assertIn("no header row", err)

    def test_no_cost_column_exits_2(self):
        code, out, err = self.split("model,tokens\nm,5\n")
        self.assertEqual(code, 2)
        self.assertIn("no cost column found", err)

    def test_unknown_group_column_exits_2(self):
        code, out, err = self.split(CSV, "--by", "region")
        self.assertEqual(code, 2)
        self.assertIn("group columns not in the export: region", err)

    def test_bad_expect_exits_2(self):
        self.assertEqual(self.split(CSV, "--expect", "model")[0], 2)
        code, out, err = self.split(CSV, "--by", "model", "--expect", "user_agent=x")
        self.assertEqual(code, 2)
        self.assertIn("must be one of the group columns", err)

    def test_since_without_time_column_exits_2(self):
        code, out, err = self.split("model,cost_usd\nm,1.00\n", "--since", "2026")
        self.assertEqual(code, 2)
        self.assertIn("need a time column", err)


if __name__ == "__main__":
    unittest.main()

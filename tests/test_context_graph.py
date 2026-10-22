import json
import os
import shutil
import subprocess
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "context-graph", "context_graph.py"


def repo(d, files):
    """Lay out a fixture repo: text is written as UTF-8, bytes as-is, None makes a folder."""
    for rel, content in files.items():
        p = os.path.join(d, *rel.split("/"))
        if content is None:
            os.makedirs(p, exist_ok=True)
        elif isinstance(content, bytes):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(content)
        else:
            write(p, content)
    return d


def adr(title, status, body="", date="2025-01-01"):
    return "# %s\n\nDate: %s\n\n## Status\n\n%s\n\n## Decision\n\n%s\n" % (title, date, status, body)


def graph(d, *args):
    code, out, err = run(SKILL, SCRIPT, "--root", d, "--json", *args)
    if code == 2:
        raise AssertionError("exit 2: " + err)
    return code, json.loads(out)


def recs(g):
    return {r["id"]: r for r in g["records"]}


def found(g, severity=None):
    return ["%s %s" % (f["record"], f["message"]) for f in g["findings"]
            if severity is None or f["severity"] == severity]


class DiscoveryTest(unittest.TestCase):
    def test_default_folders_found_and_readme_template_dotdirs_and_non_markdown_skipped(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-use-kafka.md": adr("Use Kafka", "Accepted"),
                     "docs/adr/README.md": "# ADRs\n",
                     "docs/adr/template.md": adr("Title", "Proposed"),
                     "docs/adr/notes.txt": "ADR-0050\n",
                     "docs/adr/.drafts/0009-draft.md": adr("Draft", "Proposed"),
                     "rfcs/0002-auth.md": adr("Auth", "Accepted")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(sorted(recs(g)), ["ADR-0001", "RFC-0002"])

    def test_docs_flag_reads_a_folder_outside_the_defaults(self):
        with workdir() as d:
            repo(d, {"architecture/records/0003-cache.md": adr("Cache", "Accepted")})
            code, out, err = run(SKILL, SCRIPT, "--root", d)
            self.assertEqual(code, 2)
            self.assertIn("no decision records found", err)
            code, g = graph(d, "--docs", "architecture/records")
            self.assertEqual(code, 0)
            self.assertEqual(list(recs(g)), ["DR-0003"])

    def test_docs_flag_naming_a_missing_folder_exits_2(self):
        with workdir() as d:
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--docs", "nowhere")
            self.assertEqual(code, 2)
            self.assertIn("not a folder: nowhere", err)
            self.assertNotIn("Traceback", err)

    def test_no_records_exits_2(self):
        with workdir() as d:
            repo(d, {"docs/adr/README.md": "# ADRs\n", "src/app.py": "pass\n"})
            code, out, err = run(SKILL, SCRIPT, "--root", d)
            self.assertEqual(code, 2)
            self.assertIn("no decision records found", err)
            self.assertNotIn("Traceback", err)

    def test_non_utf8_record_is_skipped_with_a_note(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-ok.md": adr("Ok", "Accepted"),
                     "docs/adr/0002-latin1.md": b"# Caf\xe9\n\n## Status\n\nAccepted\n"})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(list(recs(g)), ["ADR-0001"])
            self.assertEqual(g["notes"], ["docs/adr/0002-latin1.md is not UTF-8 text; it was skipped"])
            code, out, err = run(SKILL, SCRIPT, "--root", d)
            self.assertIn("is not UTF-8 text; it was skipped", out)

    def test_only_non_utf8_records_exits_2(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-latin1.md": b"# Caf\xe9\n"})
            code, out, err = run(SKILL, SCRIPT, "--root", d)
            self.assertEqual(code, 2)
            self.assertIn("none of the 1 record file(s) could be read", err)
            self.assertNotIn("Traceback", err)


class RecordParsingTest(unittest.TestCase):
    def setUp(self):
        self.m = load(SKILL, SCRIPT)
        self.root = os.path.abspath("fixture-root")

    def parse(self, rel, text):
        return self.m.parse_record(os.path.join(self.root, *rel.split("/")), self.root, text)

    def test_id_from_filename_in_adr_and_rfc_folders(self):
        self.assertEqual(self.parse("docs/adr/0004-use-kafka.md", "# Use Kafka\n")["id"], "ADR-0004")
        self.assertEqual(self.parse("docs/adr/adr-7-queues.md", "# Queues\n")["id"], "ADR-0007")
        self.assertEqual(self.parse("docs/rfcs/0012-auth.md", "# Auth\n")["id"], "RFC-0012")
        self.assertEqual(self.parse("docs/adr/use-kafka.md", "# Use Kafka\n")["id"], "ADR-use-kafka")

    def test_id_from_frontmatter_overrides_filename(self):
        self.assertEqual(self.parse("docs/rfcs/new-auth.md", "---\nid: RFC-0003\n---\n# Auth\n")["id"], "RFC-0003")
        self.assertEqual(self.parse("docs/rfcs/new-auth.md", "---\nrfc: 12\n---\n# Auth\n")["id"], "RFC-0012")
        self.assertEqual(self.parse("docs/adr/x.md", "---\nid: 5\n---\n# X\n")["id"], "ADR-0005")
        self.assertEqual(self.parse("docs/adr/0001-x.md", "---\nid: ADR-0042\n---\n# X\n")["id"], "ADR-0042")

    def test_title_from_heading_drops_the_id_prefix_and_frontmatter_title_wins(self):
        self.assertEqual(self.parse("docs/adr/0004-k.md", "# ADR-0004: Use Kafka\n")["title"], "Use Kafka")
        self.assertEqual(self.parse("docs/adr/0004-k.md", "---\ntitle: Queues\n---\n# ADR-4: Kafka\n")["title"],
                         "Queues")

    def test_id_from_heading_when_filename_has_no_number(self):
        self.assertEqual(self.parse("docs/adr/use-kafka.md", "# ADR-0009: Use Kafka\n")["id"], "ADR-0009")

    def test_adr_whose_filename_mentions_rfc_keeps_adr_kind(self):
        self.assertEqual(self.parse("docs/adr/0005-use-rfc3339-timestamps.md", "# Timestamps\n")["id"], "ADR-0005")

    def test_date_prefixed_filename_is_not_read_as_a_record_number(self):
        self.assertNotEqual(self.parse("docs/adr/2024-01-15-use-kafka.md", "# Use Kafka\n")["id"], "ADR-2024")

    def test_status_from_frontmatter_line_and_section(self):
        self.assertEqual(self.parse("docs/adr/0001-a.md", "---\nstatus: \"Accepted\"\n---\n# A\n")["status"],
                         "accepted")
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\nStatus: Implemented\n")["status"], "implemented")
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\n**Status:** Rejected\n")["status"], "rejected")
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\n## Status\n\nDeprecated\n")["status"], "deprecated")
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\n## Status\nAccepted\n")["status"], "accepted")
        # frontmatter wins over the body
        self.assertEqual(self.parse("docs/adr/0001-a.md", "---\nstatus: proposed\n---\nStatus: Accepted\n")["status"],
                         "proposed")

    def test_status_normalisation_and_unrecognised_and_missing(self):
        r = self.parse("docs/adr/0001-a.md", "# A\n\nStatus: Approved\n")
        self.assertEqual((r["status"], r["status_text"]), ("accepted", "Approved"))
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\nStatus: Draft\n")["status"], "proposed")
        r = self.parse("docs/adr/0001-a.md", "# A\n\n## Status\n\nPending review\n")
        self.assertEqual((r["status"], r["status_text"]), ("unrecognised", "Pending review"))
        r = self.parse("docs/adr/0001-a.md", "# A\n\nNo status here.\n")
        self.assertEqual((r["status"], r["status_text"]), ("unknown", ""))

    def test_status_from_madr_bullet(self):
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\n* Status: accepted\n")["status"], "accepted")

    def test_superseded_by_status_sets_status_and_edge(self):
        r = self.parse("docs/adr/0001-a.md", "# A\n\n## Status\n\nSuperseded by [ADR-0002](0002-b.md)\n")
        self.assertEqual(r["status"], "superseded")
        self.assertEqual(r["superseded_by"], ["ADR-0002"])

    def test_frontmatter_supersedes_list_and_body_amends(self):
        r = self.parse("docs/adr/0003-c.md", "---\nsupersedes: [ADR-0001, ADR-0002]\n---\n# C\n\nAmends ADR-0004.\n")
        self.assertEqual(r["supersedes"], ["ADR-0001", "ADR-0002"])
        self.assertEqual(r["amends"], ["ADR-0004"])

    def test_date_from_frontmatter_and_from_date_line(self):
        self.assertEqual(self.parse("docs/adr/0001-a.md", "---\ndate: 2024-03-02\n---\n# A\n")["date"], "2024-03-02")
        self.assertEqual(self.parse("docs/adr/0001-a.md", "# A\n\n**Date:** 2023-11-30\n")["date"], "2023-11-30")


class StatusChecksTest(unittest.TestCase):
    def test_missing_and_unrecognised_status_are_warnings_exit_0(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": "# A\n\nNothing decided yet.\n",
                     "docs/adr/0002-b.md": adr("B", "Pending review")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g, "problem"), [])
            self.assertIn("ADR-0001 has no status", found(g, "warning"))
            self.assertIn("ADR-0002 has a status this doesn't recognise: 'Pending review'", found(g, "warning"))

    def test_duplicate_ids_are_a_problem_exit_1(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"), "docs/adr/0001-b.md": adr("B", "Accepted")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual(found(g, "problem"),
                             ["ADR-0001 two records use the id ADR-0001: docs/adr/0001-a.md and docs/adr/0001-b.md"])


class SupersessionTest(unittest.TestCase):
    def test_recorded_both_ways_is_clean(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Superseded by ADR-0002"),
                     "docs/adr/0002-sqs.md": adr("SQS", "Accepted", "Supersedes ADR-0001.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(g["findings"], [])
            r = recs(g)
            self.assertEqual(r["ADR-0001"]["status"], "superseded")
            self.assertEqual(r["ADR-0001"]["successors"], ["ADR-0002"])
            self.assertEqual(r["ADR-0001"]["successors_only_claimed_by_successor"], [])
            self.assertEqual(r["ADR-0002"]["supersedes"], ["ADR-0001"])

    def test_only_the_newer_record_says_so_is_a_problem(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Accepted"),
                     "docs/adr/0002-sqs.md": adr("SQS", "Accepted", "Supersedes ADR-0001.")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual(found(g, "problem"), [
                "ADR-0001 is still marked Accepted, but ADR-0002 supersedes it: mark it 'Superseded by ADR-0002'"])
            r = recs(g)["ADR-0001"]
            self.assertEqual(r["successors"], ["ADR-0002"])
            self.assertEqual(r["successors_only_claimed_by_successor"], ["ADR-0002"])

    def test_only_the_older_record_says_so_is_a_warning(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Superseded by ADR-0002"),
                     "docs/adr/0002-sqs.md": adr("SQS", "Accepted")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g), [
                "ADR-0001 says it is superseded by ADR-0002, but ADR-0002 doesn't say it supersedes ADR-0001"])

    def test_dangling_successor_is_a_problem_and_missing_predecessor_a_warning(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Superseded by ADR-0009"),
                     "docs/adr/0002-sqs.md": adr("SQS", "Accepted", "Supersedes ADR-0008.")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual(found(g, "problem"),
                             ["ADR-0001 says it is superseded by ADR-0009, which isn't among the records"])
            self.assertIn("ADR-0002 supersedes ADR-0008, which isn't among the records", found(g, "warning"))

    def test_supersession_cycle_is_a_problem(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Superseded", "Supersedes ADR-0002."),
                     "docs/adr/0002-b.md": adr("B", "Superseded", "Supersedes ADR-0001.")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertIn("ADR-0001 is in a supersession cycle: ADR-0001 -> ADR-0002 -> ADR-0001", found(g, "problem"))
            self.assertIn("ADR-0002 is in a supersession cycle: ADR-0002 -> ADR-0001 -> ADR-0002", found(g, "problem"))

    def test_amends_leaves_both_current_and_clean(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"),
                     "docs/adr/0002-b.md": adr("B", "Accepted", "Amends ADR-0001.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(g["findings"], [])
            r = recs(g)
            self.assertEqual(r["ADR-0002"]["amends"], ["ADR-0001"])
            self.assertEqual(r["ADR-0001"]["successors"], [])

    def test_current_record_citing_a_superseded_one_is_a_warning(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Superseded by ADR-0002"),
                     "docs/adr/0002-sqs.md": adr("SQS", "Accepted", "Supersedes ADR-0001."),
                     "docs/adr/0003-retries.md": adr("Retries", "Accepted", "Builds on ADR-0001."),
                     "docs/adr/0004-dlq.md": adr("DLQ", "Proposed", "Builds on ADR-0001.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g), [
                "ADR-0003 is current but cites ADR-0001, which ADR-0002 supersedes: check it still holds"])


class CitesTest(unittest.TestCase):
    def test_cites_from_ids_and_markdown_links_and_cited_by(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"),
                     "docs/adr/0002-b.md": adr("B", "Accepted"),
                     "docs/adr/0003-c.md": adr("C", "Accepted",
                                               "See ADR-0001 and [the queue decision](0002-b.md).")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            r = recs(g)
            self.assertEqual(r["ADR-0003"]["cites"], ["ADR-0001", "ADR-0002"])
            self.assertEqual(r["ADR-0001"]["cited_by"], ["ADR-0003"])
            self.assertEqual(r["ADR-0002"]["cited_by"], ["ADR-0003"])

    def test_citing_an_unknown_record_is_a_warning(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted", "Follows ADR-0077.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g), ["ADR-0001 refers to ADR-0077, which isn't among the records"])


PATHS_BODY = ("Session code lives in `src/auth/session.py` and `src/billing/`, handlers in `src/payments/*.py`, "
              "config in [the config](../../config/app.yaml). The old `src/legacy/old.py` and `lib/thing.py`. "
              "We use `kafka` and see https://example.invalid/x.")


class GovernedPathsTest(unittest.TestCase):
    def fixture(self, d, status):
        repo(d, {"src/auth/session.py": "pass\n", "src/billing": None, "src/payments/pay.py": "pass\n",
                 "config/app.yaml": "a: 1\n", "docs/adr/0001-auth.md": adr("Auth", status, PATHS_BODY)})

    def test_existing_files_folders_globs_and_links_governed_and_missing_paths_listed(self):
        with workdir() as d:
            self.fixture(d, "Deprecated")
            code, g = graph(d)
            r = recs(g)["ADR-0001"]
            self.assertEqual(r["governs"], ["config/app.yaml", "src/auth/session.py", "src/billing/", "src/payments/"])
            self.assertEqual(r["missing_paths"], ["src/legacy/old.py"])
            # a deprecated record pointing at gone code isn't a problem
            self.assertEqual(code, 0)
            self.assertEqual(found(g, "problem"), [])

    def test_current_record_pointing_at_gone_code_is_a_problem(self):
        with workdir() as d:
            self.fixture(d, "Accepted")
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual(found(g, "problem"),
                             ["ADR-0001 is accepted but points at code that is gone: src/legacy/old.py"])

    def test_dot_folder_path_is_governed(self):
        with workdir() as d:
            repo(d, {".github/workflows/ci.yml": "on: push\n",
                     "docs/adr/0001-ci.md": adr("CI", "Accepted", "Pipeline in `.github/workflows/ci.yml`.")})
            code, g = graph(d)
            self.assertEqual(recs(g)["ADR-0001"]["governs"], [".github/workflows/ci.yml"])


class SamePathTest(unittest.TestCase):
    def test_two_current_records_on_one_path_warn(self):
        with workdir() as d:
            repo(d, {"src/auth/session.py": "pass\n",
                     "docs/adr/0001-a.md": adr("A", "Accepted", "Covers `src/auth/`."),
                     "docs/adr/0002-b.md": adr("B", "Implemented", "Also covers `src/auth/`.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g), [
                "ADR-0001 and ADR-0002 are both current and both govern src/auth/, and neither supersedes or "
                "amends the other: read both before relying on either"])

    def test_nested_scopes_do_not_warn(self):
        # A folder-wide decision and one about a file inside it usually complement each other.
        with workdir() as d:
            repo(d, {"src/auth/session.py": "pass\n",
                     "docs/adr/0001-a.md": adr("A", "Accepted", "Covers `src/auth/`."),
                     "docs/adr/0002-b.md": adr("B", "Implemented", "Covers `src/auth/session.py`.")})
            code, g = graph(d)
            self.assertFalse([f for f in found(g) if "both govern" in f])

    def test_linked_by_amends_or_supersedes_does_not_warn(self):
        for link in ("Amends ADR-0001.", "Supersedes ADR-0001."):
            with workdir() as d:
                repo(d, {"src/auth/session.py": "pass\n",
                         "docs/adr/0001-a.md": adr("A", "Accepted", "Covers `src/auth/`."),
                         "docs/adr/0002-b.md": adr("B", "Accepted", link + " Covers `src/auth/session.py`.")})
                code, g = graph(d)
                self.assertFalse([f for f in found(g) if "both govern" in f], link)


class OutsideReferencesTest(unittest.TestCase):
    def test_rfc_2119_and_rfcs_in_an_adr_only_repo_are_not_missing_records(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted", "The words MUST and SHOULD are as in RFC 2119. "
                                                                 "Dates follow RFC 3339. See ADR-0007.")})
            code, g = graph(d)
            self.assertEqual(found(g, "warning"), ["ADR-0001 refers to ADR-0007, which isn't among the records"])

    def test_block_style_yaml_supersedes_list_is_read(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Superseded by ADR-0003"),
                     "docs/adr/0002-b.md": adr("B", "Superseded by ADR-0003"),
                     "docs/adr/0003-c.md": "---\nstatus: accepted\nsupersedes:\n  - ADR-0001\n  - ADR-0002\n---\n# C\n"})
            code, g = graph(d)
            self.assertEqual(recs(g)["ADR-0003"]["supersedes"], ["ADR-0001", "ADR-0002"])
            self.assertEqual(code, 0, found(g))

    def test_relative_links_resolve_from_the_records_own_folder(self):
        with workdir() as d:
            repo(d, {"services/orders/app.py": "pass\n",
                     "docs/adr/0001-a.md": adr("A", "Accepted", "See [the service](../../services/orders/).")})
            code, g = graph(d)
            self.assertEqual(recs(g)["ADR-0001"]["governs"], ["services/orders/"])


class RevisionTest(unittest.TestCase):
    def test_a_renamed_folder_is_reported_as_moved_not_gone(self):
        with workdir() as d:
            repo(d, {"services/ledger/app.py": "pass\n",
                     "docs/adr/0001-a.md": adr("A", "Accepted", "Runs in `services/ledger-sync/`.")})
            code, g = graph(d)
            self.assertEqual(code, 0)
            self.assertEqual(found(g, "problem"), [])
            self.assertIn("services/ledger-sync (perhaps now services/ledger)", " ".join(found(g, "warning")))

    def test_a_folder_with_no_successor_is_gone(self):
        with workdir() as d:
            repo(d, {"services/orders/app.py": "pass\n",
                     "docs/adr/0001-a.md": adr("A", "Accepted", "Runs in `services/thumbnailer/`.")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual(found(g, "problem"), ["ADR-0001 is accepted but points at code that is gone: services/thumbnailer"])

    def test_a_guide_citing_a_superseded_record_is_flagged(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Superseded by ADR-0002"),
                     "docs/adr/0002-b.md": adr("B", "Accepted", "Supersedes ADR-0001."),
                     "docs/onboarding.md": "# Start here\n\nWe lock jobs as ADR-0001 says.\n",
                     "README.md": "See ADR-0002.\n"})
            code, g = graph(d)
            self.assertIn("ADR-0001 is cited by docs/onboarding.md, which may still describe it as current: ADR-0002 supersedes it",
                          found(g, "warning"))
            self.assertEqual(sorted(x["path"] for x in g["docs"]), ["README.md", "docs/onboarding.md"])

    def test_extends_and_narrows_count_as_amends(self):
        for verb in ("Extends", "Narrows", "Refines"):
            with workdir() as d:
                repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"),
                         "docs/adr/0002-b.md": adr("B", "Accepted", "%s ADR-0001." % verb)})
                code, g = graph(d)
                self.assertEqual(recs(g)["ADR-0002"]["amends"], ["ADR-0001"], verb)


class WhyTest(unittest.TestCase):
    def fixture(self, d):
        repo(d, {"src/auth/session.py": "pass\n", "src/other.py": "pass\n",
                 "docs/adr/0001-a.md": adr("Auth folder", "Accepted", "Covers `src/auth/`.", "2024-01-01"),
                 "docs/adr/0002-b.md": adr("Old sessions", "Superseded by ADR-0003",
                                           "Covers `src/auth/session.py`.", "2023-01-01"),
                 "docs/adr/0003-c.md": adr("New sessions", "Accepted",
                                           "Supersedes ADR-0002. Covers `src/auth/session.py`.", "2025-01-01"),
                 "docs/adr/0004-d.md": adr("Maybe", "Proposed", "Covers `src/auth/`.", "2025-06-01")})

    def test_why_orders_live_current_first_and_marks_superseded(self):
        with workdir() as d:
            self.fixture(d)
            code, g = graph(d, "--why", "src/auth/session.py")
            self.assertEqual(code, 0)
            q = g["query"]
            self.assertEqual((q["kind"], q["path"]), ("why", "src/auth/session.py"))
            self.assertEqual([h["id"] for h in q["hits"]], ["ADR-0003", "ADR-0001", "ADR-0004", "ADR-0002"])
            self.assertEqual([h["current"] for h in q["hits"]], [True, True, False, False])
            h = {h["id"]: h for h in q["hits"]}
            self.assertEqual(h["ADR-0002"]["superseded_by"], ["ADR-0003"])
            self.assertEqual(h["ADR-0001"]["via"], "src/auth/")
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--why", "src/auth/session.py")
            self.assertIn("**ADR-0003 New sessions** (accepted, current, 2025-01-01), via `src/auth/session.py`", out)
            self.assertIn("**ADR-0002 Old sessions** (superseded by ADR-0003, 2023-01-01)", out)

    def test_why_marks_accepted_record_superseded_by_newer_only(self):
        with workdir() as d:
            repo(d, {"src/auth/session.py": "pass\n",
                     "docs/adr/0001-a.md": adr("Old", "Accepted", "Covers `src/auth/`."),
                     "docs/adr/0002-b.md": adr("New", "Superseded", "Supersedes ADR-0001. Covers `src/auth/`.")})
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--why", "src/auth/session.py")
            # exit 0: a query that was answered, even though the check has problems
            self.assertEqual(code, 0)
            self.assertIn("(marked accepted, but superseded by ADR-0002", out)
            self.assertIn("None of these is current", out)

    def test_why_with_no_governing_record(self):
        with workdir() as d:
            self.fixture(d)
            code, g = graph(d, "--why", "src/other.py")
            self.assertEqual((code, g["query"]["hits"]), (0, []))
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--why", "src/other.py")
            self.assertIn("No decision record governs src/other.py", out)


class RecordQueryTest(unittest.TestCase):
    def fixture(self, d):
        repo(d, {"docs/adr/0001-kafka.md": adr("Kafka", "Accepted"),
                 "docs/adr/0002-sqs.md": adr("SQS", "Accepted", "Supersedes ADR-0001.")})

    def test_record_shows_successor_claimed_only_by_newer_record(self):
        with workdir() as d:
            self.fixture(d)
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--record", "adr 1")
            self.assertEqual(code, 0)
            self.assertIn("# ADR-0001 Kafka", out)
            self.assertIn("- Superseded by: ADR-0002 (only ADR-0002 says so; this record doesn't)", out)
            code, g = graph(d, "--record", "ADR-0001")
            self.assertEqual(g["query"]["kind"], "record")
            self.assertEqual(g["query"]["record"]["successors_only_claimed_by_successor"], ["ADR-0002"])

    def test_unknown_record_exits_2(self):
        with workdir() as d:
            self.fixture(d)
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--record", "ADR-0099")
            self.assertEqual(code, 2)
            self.assertIn("no record ADR-0099; the records are ADR-0001, ADR-0002", err)


class OutputTest(unittest.TestCase):
    def test_json_shape(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted")})
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--json", "-o", os.path.join(d, "g.json"))
            self.assertEqual((code, out), (0, ""))
            g = json.loads(read(os.path.join(d, "g.json")))
            self.assertEqual(set(g), {"root", "records", "docs", "findings", "notes", "query"})
            self.assertIsNone(g["query"])
            self.assertEqual(set(g["records"][0]), {
                "id", "title", "status", "status_text", "date", "path", "supersedes", "superseded_by", "amends",
                "cites", "governs", "missing_paths", "commits", "cited_by", "successors",
                "successors_only_claimed_by_successor", "moved", "drift"})
            self.assertEqual(g["records"][0]["path"], "docs/adr/0001-a.md")

    def test_findings_json_and_markdown_put_problems_first(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"),
                     "docs/adr/0002-b.md": adr("B", "Accepted", "Supersedes ADR-0001. See ADR-0050.")})
            code, g = graph(d)
            self.assertEqual(code, 1)
            self.assertEqual([f["severity"] for f in g["findings"]], ["problem", "warning"])
            self.assertEqual(set(g["findings"][0]), {"severity", "record", "message"})
            code, out, err = run(SKILL, SCRIPT, "--root", d)
            self.assertEqual(code, 1)
            self.assertLess(out.index("## Problems (1)"), out.index("## Warnings (1)"))
            self.assertIn("## Graph", out)

    def test_mermaid_nodes_edges_and_gone_class(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-kafka.md": adr("Use Kafka", "Accepted"),
                     "docs/adr/0002-sqs.md": adr("Use SQS", "Accepted", "Supersedes ADR-0001."),
                     "docs/adr/0003-retries.md": adr("Retries", "Accepted", "Amends ADR-0002. See ADR-0001.")})
            mmd = os.path.join(d, "g.mmd")
            run(SKILL, SCRIPT, "--root", d, "--mermaid", mmd)
            text = read(mmd)
            self.assertTrue(text.startswith("flowchart LR\n"))
            self.assertIn('ADR_0001["ADR-0001 Use Kafka (superseded by ADR-0002)"]:::gone', text)
            self.assertIn('ADR_0002["ADR-0002 Use SQS (accepted)"]\n', text)
            self.assertIn("ADR_0002 -->|supersedes| ADR_0001", text)
            self.assertIn("ADR_0003 -.->|amends| ADR_0002", text)
            self.assertIn("ADR_0003 -.- ADR_0001", text)
            self.assertIn("classDef gone", text)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitTest(unittest.TestCase):
    def git(self, d, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="Test Author", GIT_AUTHOR_EMAIL="author@example.invalid",
                   GIT_COMMITTER_NAME="Test Author", GIT_COMMITTER_EMAIL="author@example.invalid")
        subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args], cwd=d,
                       env=env, check=True, capture_output=True)

    def test_git_lists_commits_that_mention_a_record(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted"), "docs/adr/0002-b.md": adr("B", "Accepted")})
            self.git(d, "init", "-q")
            self.git(d, "add", "-A")
            self.git(d, "commit", "-q", "-m", "Add the records")
            write(os.path.join(d, "src", "x.py"), "pass\n")
            self.git(d, "add", "-A")
            self.git(d, "commit", "-q", "-m", "Implement session store", "-m", "Per adr-1.")
            code, g = graph(d, "--git")
            self.assertEqual(g["notes"], [])
            r = recs(g)
            self.assertEqual([c["subject"] for c in r["ADR-0001"]["commits"]], ["Implement session store"])
            self.assertEqual(r["ADR-0002"]["commits"], [])
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--git", "--record", "ADR-0001")
            self.assertRegex(out, r"- Commit [0-9a-f]{4,} \d{4}-\d{2}-\d{2}: Implement session store")

    def test_git_outside_a_repository_adds_a_note(self):
        with workdir() as d:
            repo(d, {"docs/adr/0001-a.md": adr("A", "Accepted")})
            code, out, err = run(SKILL, SCRIPT, "--root", d, "--json", "--git",
                                 env={"GIT_CEILING_DIRECTORIES": os.path.dirname(d)})
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["notes"], ["not a git repository, so no commits were read"])


    def commit(self, d, files, message, author="Test Author", date="2026-01-01T12:00:00"):
        repo(d, files)
        env = dict(os.environ, GIT_AUTHOR_NAME=author, GIT_AUTHOR_EMAIL="a@example.invalid",
                   GIT_COMMITTER_NAME=author, GIT_COMMITTER_EMAIL="a@example.invalid",
                   GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        if not os.path.isdir(os.path.join(d, ".git")):
            subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q"], cwd=d, check=True, capture_output=True)
        for cmd in (["add", "-A"], ["-c", "commit.gpgsign=false", "commit", "-q", "-m", message]):
            subprocess.run(["git", *cmd], cwd=d, env=env, check=True, capture_output=True)

    def test_drift_counts_commits_to_governed_code_since_the_decision_and_who_made_them(self):
        with workdir() as d:
            self.commit(d, {"services/orders/app.py": "v1\n", "docs/adr/0001-orders.md":
                            adr("Orders on SQS", "Accepted", "Publish from `services/orders/`.", date="2026-03-01")},
                        "Start", date="2026-02-01T12:00:00")
            self.commit(d, {"services/orders/app.py": "v2\n"}, "Batch the sends, per ADR-1", author="Ana",
                        date="2026-04-02T12:00:00")
            self.commit(d, {"services/orders/app.py": "v3\n"}, "Switch to Kafka client", author="Ben",
                        date="2026-05-03T12:00:00")
            self.commit(d, {"services/orders/app.py": "v4\n"}, "Retry tweak", author="Ben",
                        date="2026-06-04T12:00:00")
            self.commit(d, {"README.md": "x\n"}, "Unrelated", author="Cy", date="2026-07-01T12:00:00")
            code, g = graph(d, "--git")
            dr = recs(g)["ADR-0001"]["drift"]
            self.assertEqual(dr["since"], "2026-03-01")
            self.assertEqual(dr["count"], 3)
            self.assertEqual(dr["not_citing_record"], 2)
            self.assertEqual(dr["authors"], [{"name": "Ben", "commits": 2}, {"name": "Ana", "commits": 1}])
            self.assertEqual(dr["last_change"], "2026-06-04")
            self.assertEqual(dr["record_last_edited"], "2026-02-01")
            self.assertEqual([c["subject"] for c in dr["commits"]],
                             ["Retry tweak", "Switch to Kafka client", "Batch the sends, per ADR-1"])
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--git")
            self.assertIn("## Code changed since each decision", out)
            self.assertIn("| ADR-0001 Orders on SQS | 2026-03-01 | 3 | 2 | Ben (2), Ana (1) | 2026-06-04 | 2026-02-01 |", out)
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--git", "--why", "services/orders/app.py")
            self.assertIn("Changed since: 3 commits by Ben (2), Ana (1) since 2026-03-01, the last on 2026-06-04; "
                          "2 don't cite the record", out)
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--git", "--record", "ADR-0001")
            self.assertRegex(out, r"  - [0-9a-f]{4,} 2026-04-02 Ana: Batch the sends, per ADR-1 \(cites it\)")

    def test_drift_without_a_date_counts_from_when_the_record_was_committed(self):
        with workdir() as d:
            self.commit(d, {"src/app.py": "v1\n"}, "Start", date="2026-01-01T12:00:00")
            self.commit(d, {"docs/adr/0001-x.md": "# X\n\n## Status\n\nAccepted\n\nIn `src/app.py`.\n"},
                        "Record it", date="2026-02-01T12:00:00")
            self.commit(d, {"src/app.py": "v2\n"}, "Change", date="2026-03-01T12:00:00")
            code, g = graph(d, "--git")
            dr = recs(g)["ADR-0001"]["drift"]
            self.assertEqual((dr["since"], dr["since_from"], dr["count"]), ("2026-02-01", "git", 1))
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--git")
            self.assertIn("| ADR-0001 X | 2026-02-01* | 1 |", out)
            self.assertIn("counts from when it was first committed", out)

    def test_drift_skips_superseded_and_proposed_records_and_says_when_nothing_changed(self):
        with workdir() as d:
            self.commit(d, {"src/a.py": "v1\n",
                            "docs/adr/0001-old.md": adr("Old", "Superseded by ADR-0002", "In `src/a.py`.", date="2026-01-02"),
                            "docs/adr/0002-new.md": adr("New", "Accepted", "Supersedes ADR-0001. In `src/a.py`.", date="2026-01-02"),
                            "docs/adr/0003-idea.md": adr("Idea", "Proposed", "In `src/a.py`.", date="2026-01-02")},
                        "All", date="2026-01-01T12:00:00")
            code, g = graph(d, "--git")
            r = recs(g)
            self.assertIsNone(r["ADR-0001"]["drift"])
            self.assertIsNone(r["ADR-0003"]["drift"])
            self.assertEqual(r["ADR-0002"]["drift"]["count"], 0)
            code, out, _ = run(SKILL, SCRIPT, "--root", d, "--git")
            self.assertIn("No commit has changed the code a current decision governs since it was made.", out)

    def test_without_git_flag_there_is_no_drift(self):
        with workdir() as d:
            self.commit(d, {"src/a.py": "v1\n", "docs/adr/0001-a.md": adr("A", "Accepted", "In `src/a.py`.")}, "All")
            code, g = graph(d)
            self.assertIsNone(recs(g)["ADR-0001"]["drift"])
            code, out, _ = run(SKILL, SCRIPT, "--root", d)
            self.assertNotIn("Code changed since", out)


if __name__ == "__main__":
    unittest.main()

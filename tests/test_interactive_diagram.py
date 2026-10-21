import base64
import contextlib
import copy
import hashlib
import io
import json
import os
import re
import unittest
from html.parser import HTMLParser

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "interactive-diagram", "build_diagram.py"
m = load(SKILL, SCRIPT)
SAID = ["user: the team described it"]


def norm(spec):
    issues = m.Issues()
    return m.normalise(copy.deepcopy(spec), issues), issues


def codes(issues, level="error"):
    return [i["code"] for i in issues.items if i["level"] == level]


def build(spec, *flags, repo=None, base=None):
    """Run main() in-process with -o and --mermaid; return what it printed and wrote."""
    with workdir() as d:
        args = [write(os.path.join(d, "spec.json"), json.dumps(spec))]
        out_html, out_mmd = os.path.join(d, "out", "map.html"), os.path.join(d, "map.mmd")
        args += ["-o", out_html, "--mermaid", out_mmd]
        if repo is not None:
            root = os.path.join(d, "repo")
            os.makedirs(root)
            for rel, text in repo.items():
                write(os.path.join(root, rel), text)
            args += ["--repo-root", root]
        if base is not None:
            args += ["--compare", write(os.path.join(d, "base.json"), json.dumps(base))]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = m.main(args + list(flags))
        return {"code": code, "out": buf.getvalue(),
                "html": read(out_html) if os.path.exists(out_html) else None,
                "mermaid": read(out_mmd) if os.path.exists(out_mmd) else None}


class Page(HTMLParser):
    """The parts of the written page the tests look at."""

    def __init__(self, text):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.tags, self.scripts, self.title = [], [], None
        self._script, self._in_title = None, False
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "script":
            self._script = (a, [])
        elif tag == "title" and self.title is None:
            self.title, self._in_title = "", True

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append((self._script[0], "".join(self._script[1])))
            self._script = None
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._script is not None:
            self._script[1].append(data)
        elif self._in_title:
            self.title += data

    def node_classes(self):
        return {a["data-id"]: a.get("class", "").split() for t, a in self.tags
                if t == "g" and "node" in a.get("class", "").split()}

    def data(self):
        return json.loads(next(body for a, body in self.scripts if a.get("id") == "diagram-data"))


ARCH = {
    "type": "architecture", "title": "What a checkout request touches",
    "question": "What happens when a shopper checks out?",
    "groups": [{"id": "vpc", "label": "Private VPC"}],
    "nodes": [{"id": "web", "label": "Browser", "kind": "client", "assumed": True},
              {"id": "api", "label": "Checkout API", "group": "vpc", "evidence": ["src/api.py:2-3#def checkout"]},
              {"id": "db", "label": "Orders DB", "kind": "database", "group": "vpc", "evidence": ["src/api.py:4#INSERT"]}],
    "edges": [{"from": "web", "to": "api", "label": "POST /checkout", "assumed": True},
              {"from": "api", "to": "db", "label": "insert order", "evidence": ["src/api.py:4"]}],
}
API_PY = "import db\ndef   Checkout(cart):\n    total = sum(cart)\n    db.run('INSERT INTO orders')\n    return total\n"


class TestEvidenceRules(unittest.TestCase):
    def test_file_lines_and_quote_are_parsed(self):
        self.assertEqual(m.parse_evidence("src/api.py:40-52#redis.get("),
                         {"file": "src/api.py", "start": 40, "end": 52, "quote": "redis.get("})
        self.assertEqual(m.parse_evidence("src/api.py:12"), {"file": "src/api.py", "start": 12, "end": 12})
        self.assertEqual(m.parse_evidence("docker-compose.yml"), {"file": "docker-compose.yml"})

    def test_peoples_words_are_quotes_not_files(self):
        self.assertEqual(m.parse_evidence('user: "anything over ten days goes to HR"'),
                         {"said": "anything over ten days goes to HR", "source": "user"})
        self.assertEqual(m.parse_evidence("Doc: failover is manual")["source"], "doc")

    def test_object_form_matches_the_string_form(self):
        self.assertEqual(m.parse_evidence({"file": "a.py", "lines": "3-4", "quote": "x"}),
                         {"file": "a.py", "start": 3, "end": 4, "quote": "x"})
        self.assertEqual(m.parse_evidence({"said": "we approve in the portal"}), {"said": "we approve in the portal"})

    def test_unreadable_citation_is_an_error(self):
        spec = dict(ARCH, nodes=[dict(ARCH["nodes"][1], evidence=[":12"])] + ARCH["nodes"][2:])
        _, issues = norm(spec)
        self.assertIn("evidence/format", codes(issues))

    def test_item_without_evidence_must_be_marked_assumed(self):
        spec = copy.deepcopy(ARCH)
        del spec["nodes"][0]["assumed"]
        _, issues = norm(spec)
        self.assertEqual([i["where"] for i in issues.errors if i["code"] == "evidence/missing"], ["web"])

    def verify(self, citation, files):
        spec, issues = norm(dict(ARCH, nodes=[{"id": "a", "label": "A", "evidence": [citation]}], edges=[]))
        with workdir() as d:
            for rel, text in files.items():
                write(os.path.join(d, "repo", rel), text)
            m.verify_evidence(spec, os.path.join(d, "repo"), issues)
        return spec["nodes"][0]["evidence"][0], codes(issues)

    def test_cited_lines_with_matching_quote_are_verified_ignoring_case_and_spacing(self):
        ev, errs = self.verify("src/api.py:2-3#def checkout(cart)", {"src/api.py": API_PY})
        self.assertEqual(errs, [])
        self.assertIs(ev["verified"], True)
        self.assertEqual(ev["snippet"], "def   Checkout(cart):\n    total = sum(cart)")

    def test_whole_file_citation_is_verified_without_a_snippet(self):
        ev, errs = self.verify("src/api.py", {"src/api.py": API_PY})
        self.assertEqual(errs, [])
        self.assertTrue(ev["verified"])
        self.assertNotIn("snippet", ev)

    def test_each_failed_check_has_its_own_error(self):
        cases = [("src/api.py:9", "evidence/lines"), ("src/api.py:0", "evidence/lines"),
                 ("src/api.py:2#stripe", "evidence/quote"), ("src/missing.py:1", "evidence/file"),
                 ("../outside.py:1", "evidence/outside")]
        for citation, code in cases:
            ev, errs = self.verify(citation, {"src/api.py": API_PY, "../outside.py": "x\n"})
            self.assertEqual(errs, [code], citation)
            self.assertIs(ev["verified"], False, citation)

    def test_line_range_error_says_how_long_the_file_is(self):
        spec, issues = norm(dict(ARCH, nodes=[{"id": "a", "label": "A", "evidence": ["src/api.py:4-9"]}], edges=[]))
        with workdir() as d:
            write(os.path.join(d, "src", "api.py"), API_PY)
            m.verify_evidence(spec, d, issues)
        self.assertIn("src/api.py has 5 lines; cited 4-9", issues.errors[0]["message"])

    def test_secret_looking_lines_are_masked_in_the_snippet(self):
        # AKIAIOSFODNN7EXAMPLE is AWS's own documentation example key, which secret scanners allow.
        text = 'import os\nAPI_KEY = "sk-test-not-a-real-key-000000"\nAWS = "AKIAIOSFODNN7EXAMPLE"\nREGION = "eu"\n'
        ev, _ = self.verify("conf/settings.py:1-4", {"conf/settings.py": text})
        self.assertEqual(ev["snippet"].splitlines(), ["import os", "[line hidden: looks like a secret]",
                                                      "[line hidden: looks like a secret]", 'REGION = "eu"'])

    def test_files_that_hold_secrets_are_verified_but_never_shown(self):
        for name in (".env", "deploy/server.pem", "config/secrets.yaml"):
            ev, errs = self.verify(name + ":1", {name: "DB_HOST=db.internal\n"})
            self.assertEqual(errs, [], name)
            self.assertTrue(ev["verified"], name)
            self.assertNotIn("snippet", ev, name)

    def test_long_citations_show_at_most_14_lines(self):
        text = "".join("line %d\n" % i for i in range(1, 31))
        ev, _ = self.verify("big.py:1-30", {"big.py": text})
        lines = ev["snippet"].splitlines()
        self.assertEqual(lines[:14], ["line %d" % i for i in range(1, 15)])
        self.assertEqual(lines[14:], ["…"])

    def test_without_a_repo_root_citations_are_unchecked(self):
        spec, issues = norm(ARCH)
        m.verify_evidence(spec, None, issues)
        self.assertIsNone(spec["nodes"][1]["evidence"][0]["verified"])
        self.assertEqual(issues.errors, [])

    def test_answers_citations_are_checked_too(self):
        spec = dict(ARCH, answers=[{"question": "Is it the cache?", "answer": "No cache is called", "evidence": ["src/api.py:9"]}])
        res = build(spec, repo={"src/api.py": API_PY})
        self.assertEqual(res["code"], 1)
        self.assertIn("answer 1 [evidence/lines]", res["out"])


class TestSpecChecks(unittest.TestCase):
    def test_unknown_type_missing_title_and_nothing_to_draw_are_errors(self):
        _, issues = norm({"type": "mindmap", "nodes": []})
        self.assertEqual(set(codes(issues)), {"spec/type", "spec/title", "spec/empty"})

    def test_ids_must_be_unique_across_groups_nodes_and_edges(self):
        spec = copy.deepcopy(ARCH)
        spec["nodes"][1]["id"] = "vpc"
        spec["edges"] = [{"id": "db", "from": "web", "to": "vpc", "assumed": True}]
        _, issues = norm(spec)
        self.assertEqual([i["where"] for i in issues.errors if i["code"] == "id/duplicate"], ["vpc", "db"])

    def test_edge_to_a_missing_node_is_an_error(self):
        spec = dict(ARCH, edges=[{"from": "api", "to": "redis", "assumed": True}])
        _, issues = norm(spec)
        self.assertIn("edge/endpoint", codes(issues))

    def test_unnamed_edges_are_numbered_in_order(self):
        spec, _ = norm(ARCH)
        self.assertEqual([e["id"] for e in spec["edges"]], ["e1", "e2"])

    def test_missing_group_and_group_cycle_are_errors(self):
        spec = copy.deepcopy(ARCH)
        spec["groups"] = [{"id": "a", "label": "A", "parent": "b"}, {"id": "b", "label": "B", "parent": "a"}]
        _, issues = norm(spec)
        self.assertIn("group/cycle", codes(issues))
        self.assertIn("node/group", codes(issues))

    def test_story_step_naming_a_missing_id_is_an_error(self):
        _, issues = norm(dict(ARCH, story=[{"text": "The API writes.", "edges": ["e2", "e9"]}]))
        self.assertEqual([i["message"] for i in issues.errors], ["'e9' is not a node or edge id"])

    def test_unknown_kind_long_label_and_isolated_node_are_warnings(self):
        spec = copy.deepcopy(ARCH)
        spec["nodes"].append({"id": "lonely", "label": "x" * 49, "kind": "spaceship", "evidence": SAID})
        _, issues = norm(spec)
        self.assertEqual(issues.errors, [])
        self.assertEqual(set(codes(issues, "warning")), {"node/kind", "node/label-long", "node/isolated"})

    def test_more_than_36_parts_warns(self):
        nodes = [{"id": "n%d" % i, "label": "N%d" % i, "evidence": SAID} for i in range(37)]
        edges = [{"from": "n%d" % i, "to": "n%d" % (i + 1), "evidence": SAID} for i in range(36)]
        _, issues = norm({"type": "workflow", "title": "Big", "nodes": nodes, "edges": edges})
        self.assertEqual(codes(issues, "warning"), ["size/large"])

    def test_frames_need_message_ids_and_only_belong_on_sequences(self):
        _, issues = norm(dict(SEQUENCE, frames=[{"kind": "loop", "from": "m1", "to": "nope"}]))
        self.assertIn("frame/range", codes(issues))
        _, issues = norm(dict(ARCH, frames=[{"kind": "loop", "from": "e1", "to": "e2"}]))
        self.assertIn("frame/type", codes(issues, "warning"))

    def test_non_http_source_url_warns(self):
        _, issues = norm(dict(ARCH, source_url="file:///home/someone/repo"))
        self.assertIn("spec/source-url", codes(issues, "warning"))


SEQUENCE = {
    "type": "sequence", "title": "Sign-in with SSO",
    "participants": [{"id": "u", "label": "User", "kind": "person", "evidence": SAID},
                     {"id": "app", "label": "Web app", "evidence": SAID},
                     {"id": "idp", "label": "Identity provider", "kind": "external", "evidence": SAID}],
    "messages": [{"from": "u", "to": "app", "label": "click Sign in", "evidence": SAID},
                 {"from": "app", "to": "idp", "label": "redirect", "kind": "async", "evidence": SAID},
                 {"id": "back", "from": "idp", "to": "app", "label": "authorization code", "kind": "return", "evidence": SAID}],
    "frames": [{"kind": "alt", "label": "code missing", "from": "back", "to": "back"}],
}


class TestDiagramKinds(unittest.TestCase):
    """Each type builds a page with one mark per part, and Mermaid in that type's syntax."""

    def built(self, spec):
        res = build(spec)
        self.assertEqual(res["code"], 0, res["out"])
        page = Page(res["html"])
        self.assertEqual(set(page.node_classes()), {n["id"] for n in norm(spec)[0]["nodes"]})
        return res["mermaid"].splitlines(), page

    def test_architecture_groups_become_subgraphs_and_assumptions_are_dashed(self):
        mmd, page = self.built(ARCH)
        self.assertEqual(mmd, [
            "flowchart LR", '    web["Browser"]', '    subgraph vpc["Private VPC"]', '        api["Checkout API"]',
            '        db[("Orders DB")]', "    end", '    web -.->|"POST /checkout"| api', '    api -->|"insert order"| db',
            "    classDef assumed stroke-dasharray: 5 4", "    class web assumed"])
        self.assertIn("assumed", page.node_classes()["web"])
        self.assertNotIn("assumed", page.node_classes()["api"])

    def test_architecture_nodes_do_not_overlap_and_sit_inside_their_group(self):
        spec, issues = norm(dict(ARCH, groups=ARCH["groups"] + [{"id": "ext", "label": "Outside"}],
                                 nodes=ARCH["nodes"] + [{"id": "psp", "label": "Card processor", "kind": "external",
                                                         "group": "ext", "evidence": SAID}],
                                 edges=ARCH["edges"] + [{"from": "api", "to": "psp", "evidence": SAID}]))
        geo = m.layout_graph_full(spec)
        boxes = {n["id"]: (n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]) for n in spec["nodes"]}
        overlap = lambda a, b: a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
        ids = sorted(boxes)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                self.assertFalse(overlap(boxes[a], boxes[b]), (a, b))
        groups = {g["id"]: (g["x"], g["y"], g["x"] + g["w"], g["y"] + g["h"]) for g in geo["groups"]}
        self.assertFalse(overlap(groups["vpc"], groups["ext"]))
        for n in spec["nodes"]:
            if n.get("group"):
                g, b = groups[n["group"]], boxes[n["id"]]
                self.assertTrue(g[0] <= b[0] and g[1] <= b[1] and b[2] <= g[2] and b[3] <= g[3], n["id"])
        self.assertLess(boxes["web"][0], boxes["api"][0])  # left to right, in the order of flow

    def test_dataflow_emphasis_and_both_ways_arrows(self):
        spec = {"type": "dataflow", "title": "Money", "nodes": [
            {"id": "a", "label": "Ledger", "evidence": SAID}, {"id": "b", "label": "Bank", "kind": "external", "evidence": SAID}],
            "edges": [{"from": "a", "to": "b", "label": "payout", "emphasis": True, "both": True, "evidence": SAID}]}
        mmd, _ = self.built(spec)
        self.assertIn('    a <==>|"payout"| b', mmd)

    def test_workflow_with_a_loop_and_a_decision_builds(self):
        spec = {"type": "workflow", "title": "Leave approval", "nodes": [
            {"id": "ask", "label": "Request leave", "kind": "start", "evidence": SAID},
            {"id": "ok", "label": "Over ten days?", "kind": "decision", "evidence": SAID},
            {"id": "hr", "label": "HR reviews", "kind": "manual", "evidence": SAID},
            {"id": "done", "label": "Approved", "kind": "end", "evidence": SAID}],
            "edges": [{"from": "ask", "to": "ok", "evidence": SAID}, {"from": "ok", "to": "hr", "label": "yes", "evidence": SAID},
                      {"from": "hr", "to": "ask", "label": "send back", "evidence": SAID},
                      {"from": "ok", "to": "done", "label": "no", "evidence": SAID},
                      {"from": "hr", "to": "hr", "label": "ask again", "evidence": SAID}]}
        mmd, _ = self.built(spec)
        self.assertIn('    ok{"Over ten days?"}', mmd)
        self.assertIn('    ask(["Request leave"])', mmd)
        self.assertIn('    hr -->|"send back"| ask', mmd)

    def test_lifecycle_start_and_end_dots_become_mermaid_star(self):
        spec = {"type": "lifecycle", "title": "Invoice states", "nodes": [
            {"id": "start", "kind": "initial", "evidence": SAID}, {"id": "draft", "label": "Draft", "evidence": SAID},
            {"id": "sent", "label": "Sent", "evidence": SAID}, {"id": "end", "kind": "final", "evidence": SAID}],
            "edges": [{"from": "start", "to": "draft", "evidence": SAID}, {"from": "draft", "to": "sent", "label": "send", "evidence": SAID},
                      {"from": "sent", "to": "end", "evidence": SAID}]}
        mmd, _ = self.built(spec)
        self.assertEqual(mmd, ["stateDiagram-v2", "    direction LR", '    state "Draft" as draft', '    state "Sent" as sent',
                               "    [*] --> draft", "    draft --> sent: send", "    sent --> [*]"])

    def test_erd_cardinality_and_keys(self):
        spec = {"type": "erd", "title": "Orders schema", "nodes": [
            {"id": "customers", "label": "customers", "evidence": SAID,
             "fields": [{"name": "id", "type": "uuid", "key": "pk"}, {"name": "email", "type": "text", "key": "uk"}]},
            {"id": "orders", "label": "orders", "evidence": SAID,
             "fields": [{"name": "id", "type": "uuid", "key": "pk"}, {"name": "customer_id", "type": "uuid", "key": "fk"}]}],
            "edges": [{"from": "orders", "to": "customers", "from_field": "customer_id", "to_field": "id",
                       "from_card": "*", "to_card": "1", "evidence": SAID}]}
        mmd, page = self.built(spec)
        self.assertEqual(mmd, ["erDiagram", '    orders }o--|| customers : "has"',
                               "    customers {", "        uuid id PK", "        text email UK", "    }",
                               "    orders {", "        uuid id PK", "        uuid customer_id FK", "    }"])
        self.assertIn("k-table", page.node_classes()["orders"])

    def test_sequence_arrows_follow_message_kind_and_frames_wrap_messages(self):
        mmd, _ = self.built(SEQUENCE)
        self.assertEqual(mmd, ["sequenceDiagram", "    actor u as User", "    participant app as Web app",
                               "    participant idp as Identity provider", "    u->>app: click Sign in",
                               "    app-)idp: redirect", "    alt code missing", "    idp-->>app: authorization code", "    end"])

    def test_class_relations_aliases_and_stereotypes(self):
        spec = {"type": "class", "title": "Payments model", "classes": [
            {"id": "pm", "label": "PaymentMethod", "kind": "interface", "evidence": SAID,
             "members": [{"name": "charge(amount)", "type": "Receipt", "visibility": "public"}]},
            {"id": "base", "label": "Instrument", "kind": "abstract", "evidence": SAID},
            {"id": "card", "label": "Card", "evidence": SAID},
            {"id": "wallet", "label": "Wallet", "evidence": SAID}],
            "relations": [{"from": "card", "to": "pm", "kind": "realizes", "evidence": SAID},
                          {"from": "card", "to": "base", "kind": "extends", "evidence": SAID},
                          {"from": "wallet", "to": "card", "kind": "owns", "label": "holds", "evidence": SAID}]}
        mmd, page = self.built(spec)
        self.assertEqual(mmd[:5], ["classDiagram", "    class PaymentMethod {", "        <<interface>>",
                                   "        + charge(amount): Receipt", "    }"])
        self.assertEqual(mmd[-3:], ["    Card ..|> PaymentMethod", "    Card --|> Instrument", "    Wallet *-- Card : holds"])
        # the layout flips inherits/implements to put parents on top; the page must still say child -> parent
        ends = {(e["from"], e["to"]) for e in page.data()["edges"]}
        self.assertEqual(ends, {("card", "pm"), ("card", "base"), ("wallet", "card")})

    def test_class_relation_that_is_not_known_is_an_error(self):
        spec = {"type": "class", "title": "M", "classes": [{"id": "a", "evidence": SAID}, {"id": "b", "evidence": SAID}],
                "relations": [{"from": "a", "to": "b", "kind": "befriends", "evidence": SAID}]}
        self.assertIn("edge/relation", codes(norm(spec)[1]))

    def test_tree_lines_come_from_parents_and_count_what_is_inside(self):
        spec = {"type": "tree", "title": "Payments service", "nodes": [
            {"id": "root", "label": "payments/", "kind": "folder", "evidence": SAID},
            {"id": "api", "label": "api/", "kind": "folder", "parent": "root", "evidence": SAID},
            {"id": "models", "label": "models.py", "kind": "file", "parent": "api", "evidence": SAID},
            {"id": "tests", "label": "tests/", "kind": "folder", "parent": "root", "evidence": SAID}]}
        mmd, page = self.built(spec)
        self.assertEqual(mmd[0], "flowchart LR")
        self.assertEqual(mmd[-3:], ["    root --- api", "    api --- models", "    root --- tests"])
        facts = {n["id"]: n["facts"] for n in page.data()["nodes"]}
        self.assertEqual(facts["root"], [["inside it", "3 items"]])
        self.assertEqual(facts["api"], [["inside it", "1 item"]])
        self.assertIsNone(facts["models"])

    def test_tree_ignores_edges_and_rejects_parent_loops(self):
        spec = {"type": "tree", "title": "T", "nodes": [
            {"id": "a", "parent": "b", "evidence": SAID}, {"id": "b", "parent": "a", "evidence": SAID},
            {"id": "c", "parent": "zz", "evidence": SAID}], "edges": [{"from": "a", "to": "b"}]}
        _, issues = norm(spec)
        self.assertIn("edge/ignored", codes(issues, "warning"))
        self.assertIn("parent/cycle", codes(issues))
        self.assertIn("parent/missing", codes(issues))

    def test_timeline_mermaid_has_a_section_per_lane_in_time_order(self):
        mmd, _ = self.built(TIMELINE)
        self.assertEqual(mmd, ["timeline", "    title Payment outage", "    section Monitoring",
                               "        03.00 : Alert fired", "        05.00 : Resolved", "    section ops",
                               "        ~03.30 : Deploy rolled back"])

    def test_waterfall_mermaid_is_a_gantt_with_the_critical_path_marked(self):
        mmd, _ = self.built(WATERFALL)
        self.assertIn("gantt", mmd)
        self.assertIn("    Charge card :crit, pay, 400, 900", mmd)
        self.assertIn("    Send receipt :mail, 950, 1200", mmd)


TIMELINE = {
    "type": "timeline", "title": "Payment outage",
    "groups": [{"id": "mon", "label": "Monitoring"}],
    "events": [{"id": "a", "label": "Alert fired", "at": "2026-10-11T03:00:00Z", "lane": "mon", "kind": "alert", "evidence": SAID},
               {"id": "b", "label": "Deploy rolled back", "at": "2026-10-10T22:30-05:00", "lane": "ops", "approx": True,
                "kind": "change", "evidence": SAID},
               {"id": "c", "label": "Resolved", "at": "2026-10-11T05:00:00Z", "lane": "mon", "kind": "milestone", "evidence": SAID}],
}


def laid_out_timeline(spec):
    s, issues = norm(spec)
    m.layout_timeline(s)
    return s, issues


class TestTimeline(unittest.TestCase):
    def test_times_with_different_offsets_go_on_one_clock(self):
        s, issues = laid_out_timeline(TIMELINE)
        self.assertEqual(issues.errors, [])
        self.assertEqual(s["_findings"], [
            "From 11 Oct 03:00 to 05:00: 2h.",
            "Longest quiet stretch: 1h 30m, between Deploy rolled back (~03:30) and Resolved (05:00).",
            "Approximate times (the source is unsure): Deploy rolled back at ~03:30.",
            "The sources give times in UTC and UTC-05:00; all are shown in UTC."])

    def test_timezone_sets_the_zone_the_reader_sees(self):
        s, _ = laid_out_timeline(dict(TIMELINE, timezone="-05:00"))
        self.assertEqual([n["when"] for n in s["nodes"]], ["10 Oct 22:00", "~10 Oct 22:30", "11 Oct 00:00"])
        self.assertEqual(s["_findings"][0], "From 10 Oct 22:00 to 11 Oct 00:00: 2h.")
        self.assertTrue(s["_findings"][-1].endswith("all are shown in UTC-05:00."))

    LASTING = {"type": "timeline", "title": "Runs", "events": [
        {"id": "a", "label": "Backfill", "at": 0, "end": 30, "evidence": SAID},
        {"id": "b", "label": "Vacuum", "at": 40, "evidence": SAID},
        {"id": "c", "label": "Alert", "at": 45, "evidence": SAID}]}

    def test_quiet_stretch_is_measured_from_the_end_of_an_event_that_lasts(self):
        s, _ = laid_out_timeline(self.LASTING)
        self.assertEqual(s["_findings"][1], "Longest quiet stretch: 10, between Backfill (0 to 30) and Vacuum (40).")

    def test_span_sentence_starts_at_the_first_events_start_when_it_lasts(self):
        s, _ = laid_out_timeline(self.LASTING)
        self.assertEqual(s["_findings"][0], "From 0 to 45: 45.")

    def test_a_long_gap_is_shortened_and_labelled_on_the_axis(self):
        spec = {"type": "timeline", "title": "Gap", "events": [
            {"id": "e%d" % t, "label": "E%d" % t, "at": t, "evidence": SAID} for t in (0, 1, 2, 100)]}
        s, _ = laid_out_timeline(spec)
        self.assertEqual([b[2] for b in s["_timeline"]["breaks"]], ["98"])
        self.assertIn("98 later", m.timeline_svg(s))

    def test_times_written_different_ways_are_an_error(self):
        spec = {"type": "timeline", "title": "Mixed", "events": [
            {"id": "a", "at": "14:05", "evidence": SAID}, {"id": "b", "at": "2026-10-03", "evidence": SAID}]}
        self.assertEqual(codes(norm(spec)[1]), ["time/mixed"])

    def test_unreadable_time_and_end_before_start_are_errors(self):
        spec = {"type": "timeline", "title": "Bad", "events": [
            {"id": "a", "at": "around lunch", "evidence": SAID}, {"id": "b", "at": 10, "end": 5, "evidence": SAID}]}
        self.assertEqual(codes(norm(spec)[1]), ["time/missing", "time/end"])

    def test_parse_when_reads_dates_clock_times_and_numbers(self):
        self.assertEqual(m.parse_when("14:05:30"), (14 * 3600 + 5 * 60 + 30, "clock"))
        self.assertEqual(m.parse_when(12.5), (12.5, "num"))
        self.assertEqual(m.parse_when("2026-10-11T03:41:00Z")[1], "abs:+0000")
        self.assertEqual(m.parse_when("2026-10-11T03:41:00Z")[0], m.parse_when("2026-10-10T22:41-05:00")[0])
        self.assertIsNone(m.parse_when(True))
        self.assertIsNone(m.parse_when("soon"))


WATERFALL = {
    "type": "waterfall", "title": "Where a slow checkout spent its time", "unit": "ms",
    "spans": [{"id": "root", "label": "POST /checkout", "start": 0, "end": 1000, "evidence": SAID},
              {"id": "db", "label": "Read cart", "start": 100, "end": 400, "parent": "root", "service": "db", "evidence": SAID},
              {"id": "pay", "label": "Charge card", "start": 400, "duration": 500, "parent": "root", "service": "stripe",
               "evidence": SAID},
              {"id": "mail", "label": "Send receipt", "start": 950, "end": 1200, "parent": "root", "evidence": SAID}],
}


def laid_out_waterfall(spec):
    s, issues = norm(spec)
    m.layout_waterfall(s)
    return s, issues


class TestWaterfall(unittest.TestCase):
    def test_findings_total_own_work_and_a_span_that_outlives_its_parent(self):
        s, issues = laid_out_waterfall(WATERFALL)
        self.assertEqual(s["_findings"], [
            "The whole of POST /checkout took 1.0 s.",
            "What the whole waited on most: Charge card, 500 ms of its own work (50%); Read cart, 300 ms of its own work (30%); "
            "POST /checkout, 150 ms of its own work (15%).",
            "Send receipt ends 200 ms after POST /checkout does, so nothing waited for it: it runs on after its parent "
            "(fire-and-forget), or the two clocks disagree."])
        self.assertEqual(codes(issues, "warning"), ["span/outside"])

    def test_critical_path_leaves_out_a_fire_and_forget_span(self):
        s, _ = laid_out_waterfall(WATERFALL)
        self.assertEqual(s["_waterfall"]["crit"], ["root", "db", "pay"])
        self.assertEqual(s["_waterfall"]["total"], "1.0 s")

    def test_each_span_gets_start_duration_share_and_own_time(self):
        s, _ = laid_out_waterfall(WATERFALL)
        pay = next(n for n in s["nodes"] if n["id"] == "pay")
        self.assertEqual(pay["facts"], [["starts at", "400 ms"], ["takes", "500 ms"], ["share of the whole", "50%"],
                                        ["time of its own (not in a child span)", "500 ms"], ["on the critical path", "yes"]])

    def test_overlapping_siblings_are_not_summed_and_a_waiting_parent_is_named(self):
        spec = {"type": "waterfall", "title": "Fan-out", "spans": [
            {"id": "r", "label": "Root", "start": 0, "end": 1000, "evidence": SAID},
            {"id": "a", "label": "Fetch A", "start": 0, "end": 600, "parent": "r", "evidence": SAID},
            {"id": "b", "label": "Fetch B", "start": 100, "end": 700, "parent": "r", "evidence": SAID},
            {"id": "c", "label": "Render", "start": 700, "end": 1000, "parent": "r", "evidence": SAID}]}
        s, _ = laid_out_waterfall(spec)
        self.assertIn("Root takes 1.0 s but only 0 ms of it is its own; the rest is waiting on what it calls.", s["_findings"])
        self.assertIn("Fetch A and Fetch B run at the same time for 500 ms: together they take 700 ms, not the 1.2 s "
                      "their durations add up to.", s["_findings"])
        self.assertEqual(s["_waterfall"]["crit"], ["b", "c"])

    def test_clock_times_become_milliseconds(self):
        spec = {"type": "waterfall", "title": "Clock", "spans": [
            {"id": "r", "label": "Job", "start": "14:05:00", "end": "14:05:01.5", "evidence": SAID}]}
        s, _ = laid_out_waterfall(spec)
        self.assertEqual(s["nodes"][0]["facts"][1], ["takes", "1.5 s"])

    def test_span_needs_a_start_and_an_end_after_it(self):
        spec = {"type": "waterfall", "title": "Bad", "spans": [
            {"id": "a", "start": "whenever", "end": 5, "evidence": SAID}, {"id": "b", "start": 5, "evidence": SAID},
            {"id": "c", "start": 9, "end": 3, "evidence": SAID}]}
        self.assertEqual(codes(norm(spec)[1]), ["span/start", "span/end", "span/order"])

    def test_durations_are_said_the_way_a_person_says_them(self):
        cases = [((250, "ms"), "250 ms"), ((1500, "ms"), "1.5 s"), ((12000, "ms"), "12 s"), ((125000, "ms"), "2m 05s"),
                 ((3 * 3600000 + 7 * 60000, "ms"), "3h 07m"), ((1.5, "s"), "1.5 s"), ((-40, "ms"), "-40 ms"),
                 ((2, "furlongs"), "2 furlongs")]
        for args, expect in cases:
            self.assertEqual(m.fmt_dur(*args), expect, args)


class TestCompare(unittest.TestCase):
    BASE = {"type": "architecture", "title": "Before", "nodes": [
        {"id": "api", "label": "API", "evidence": SAID}, {"id": "db", "label": "DB", "kind": "database", "evidence": SAID},
        {"id": "cache", "label": "Cache", "kind": "cache", "evidence": SAID}],
        "edges": [{"from": "api", "to": "db", "label": "insert", "evidence": SAID},
                  {"from": "api", "to": "cache", "label": "get", "evidence": SAID}]}
    HEAD = {"type": "architecture", "title": "After", "nodes": [
        {"id": "api", "label": "Checkout API", "evidence": SAID}, {"id": "db", "label": "DB", "kind": "database", "evidence": SAID},
        {"id": "queue", "label": "Orders queue", "kind": "queue", "evidence": SAID}],
        "edges": [{"from": "api", "to": "db", "label": "insert", "evidence": SAID},
                  {"from": "api", "to": "queue", "label": "publish", "evidence": SAID}]}

    def test_added_removed_and_changed_are_marked_on_the_page(self):
        res = build(self.HEAD, base=self.BASE)
        self.assertEqual(res["code"], 0, res["out"])
        page = Page(res["html"])
        status = {n["id"]: n["status"] for n in page.data()["nodes"]}
        self.assertEqual(status, {"api": "changed", "db": None, "queue": "added", "cache": "removed"})
        edges = {(e["from"], e["to"]): e["status"] for e in page.data()["edges"]}
        self.assertEqual(edges, {("api", "db"): None, ("api", "queue"): "added", ("api", "cache"): "removed"})
        self.assertIn("st-removed", page.node_classes()["cache"])
        self.assertIn("2 added, 1 changed, 2 removed", res["html"])

    def test_removed_parts_are_left_out_of_the_mermaid(self):
        res = build(self.HEAD, base=self.BASE)
        self.assertNotIn("cache", res["mermaid"])
        self.assertIn('api -->|"publish"| queue', res["mermaid"])

    def test_comparing_different_types_is_an_error(self):
        res = build(self.HEAD, base=dict(self.BASE, type="workflow"))
        self.assertEqual(res["code"], 1)
        self.assertIn("[compare/type]", res["out"])
        self.assertIsNone(res["html"])


class TestHtmlPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = dict(ARCH, answers=[{"question": "Is it the cache?", "answer": "No cache is called",
                                    "evidence": ["src/api.py:4#INSERT"]}])
        cls.res = build(spec, "--theme", "dark", repo={"src/api.py": API_PY})
        cls.page = Page(cls.res["html"])

    def test_page_was_written(self):
        self.assertEqual(self.res["code"], 0, self.res["out"])
        self.assertTrue(self.res["html"].startswith("<!doctype html>"))
        self.assertEqual(self.page.title, "What a checkout request touches")

    def test_makes_no_external_requests(self):
        for tag, attrs in self.page.tags:
            self.assertNotEqual(tag, "link")
            for name in ("src", "href"):
                value = attrs.get(name) or ""
                self.assertFalse(re.match(r"^(https?:)?//", value), (tag, name, value))
        self.assertFalse(any("src" in a for a, _ in self.page.scripts))

    def test_content_security_policy_allows_only_the_pages_own_script(self):
        csp = next(a["content"] for t, a in self.page.tags if t == "meta" and a.get("http-equiv") == "Content-Security-Policy")
        self.assertIn("default-src 'none'", csp)
        js = next(body for a, body in self.page.scripts if not a.get("type"))
        digest = base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode()
        self.assertIn("script-src 'sha256-%s'" % digest, csp)

    def test_embedded_data_carries_verified_evidence_and_the_cited_lines(self):
        data = self.page.data()
        api = next(n for n in data["nodes"] if n["id"] == "api")
        self.assertEqual(api["group_label"], "Private VPC")
        ev, = api["evidence"]
        self.assertEqual((ev["file"], ev["start"], ev["end"], ev["verified"]), ("src/api.py", 2, 3, True))
        self.assertEqual(ev["snippet"], "def   Checkout(cart):\n    total = sum(cart)")
        self.assertEqual(data["mermaid"], self.res["mermaid"])

    def test_header_counts_checked_citations_and_assumptions(self):
        self.assertIn("3 of 3 file citations checked against the repository · 2 items drawn dashed as assumptions",
                      self.res["html"])

    def test_answers_table_lists_each_question_with_its_evidence(self):
        self.assertIn("<td>Is it the cache?</td><td>No cache is called</td><td class=\"ev\"><code>src/api.py:4</code> ✓</td>",
                      self.res["html"])

    def test_theme_flag_sets_the_default_theme(self):
        self.assertIn(("html", {"lang": "en", "data-theme-default": "dark"}), self.page.tags)

    def test_text_outline_lists_parts_and_marks_assumptions(self):
        self.assertIn("<li><b>Browser</b> <span class=\"tag warn\">assumption</span></li>", self.res["html"])
        self.assertIn("<li>Checkout API → Orders DB: insert order <span class=\"ev\">(<code>src/api.py:4</code> ✓)</span></li>",
                      self.res["html"])

    def test_markup_in_labels_is_escaped_everywhere(self):
        hostile = "</script><img src=x onerror=alert(1)>"
        spec = dict(ARCH, title="Orders & <img src=y>",
                    nodes=[dict(ARCH["nodes"][0], label=hostile)] + ARCH["nodes"][1:])
        res = build(spec)
        page = Page(res["html"])
        self.assertEqual(page.title, "Orders & <img src=y>")
        self.assertFalse(any(t == "img" for t, _ in page.tags))
        self.assertEqual(sum(1 for a, _ in page.scripts if not a.get("type")), 1)
        self.assertEqual(next(n["label"] for n in page.data()["nodes"] if n["id"] == "web"), hostile)

    def test_unchecked_citations_are_said_to_be_unchecked(self):
        res = build(ARCH)
        self.assertIn("3 file citations, not checked against a repository", res["html"])
        self.assertIn("[evidence/unchecked]", res["out"])


class TestCli(unittest.TestCase):
    def spec_file(self, d, spec, name="spec.json"):
        return write(os.path.join(d, name), json.dumps(spec))

    def test_needs_an_output_or_check(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, self.spec_file(d, ARCH))
        self.assertEqual(code, 2)
        self.assertIn("give -o OUT.html, or --check", err)

    def test_missing_or_invalid_spec_exits_2_without_a_traceback(self):
        with workdir() as d:
            broken = write(os.path.join(d, "broken.json"), '{"type": ')
            for path in (os.path.join(d, "nope.json"), broken):
                code, _, err = run(SKILL, SCRIPT, path, "--check")
                self.assertEqual(code, 2, path)
                self.assertIn("cannot read", err)
                self.assertNotIn("Traceback", err)

    def test_spec_that_is_not_an_object_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, self.spec_file(d, [ARCH]), "--check")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)

    def test_spec_errors_exit_1_and_write_nothing(self):
        with workdir() as d:
            out = os.path.join(d, "map.html")
            mmd = os.path.join(d, "map.mmd")
            code, stdout, _ = run(SKILL, SCRIPT, self.spec_file(d, dict(ARCH, title="")), "-o", out, "--mermaid", mmd)
            self.assertEqual(code, 1)
            self.assertIn("ERROR title [spec/title] the diagram has no title", stdout)
            self.assertIn("1 error(s); nothing written", stdout)
            self.assertFalse(os.path.exists(out))
            self.assertFalse(os.path.exists(mmd))

    def test_a_wrong_citation_stops_the_build(self):
        with workdir() as d:
            write(os.path.join(d, "repo", "src", "api.py"), API_PY)
            out = os.path.join(d, "map.html")
            spec = copy.deepcopy(ARCH)
            spec["nodes"][2]["evidence"] = ["src/api.py:4#UPDATE"]
            code, stdout, _ = run(SKILL, SCRIPT, self.spec_file(d, spec), "-o", out, "--repo-root", os.path.join(d, "repo"))
            self.assertEqual(code, 1)
            self.assertIn("ERROR db [evidence/quote] 'UPDATE' is not on src/api.py:4", stdout)
            self.assertFalse(os.path.exists(out))

    def test_check_validates_and_writes_nothing(self):
        with workdir() as d:
            write(os.path.join(d, "repo", "src", "api.py"), API_PY)
            code, out, _ = run(SKILL, SCRIPT, self.spec_file(d, ARCH), "--check", "--repo-root", os.path.join(d, "repo"))
            self.assertEqual(sorted(os.listdir(d)), ["repo", "spec.json"])
        self.assertEqual(code, 0)
        self.assertIn("OK: 3 nodes, 2 edges, 2 assumed, 3 of 3 file citations verified", out)

    def test_json_receipt_and_titled_link(self):
        with workdir() as d:
            out = os.path.join(d, "nested", "deeper", "map.html")
            code, stdout, _ = run(SKILL, SCRIPT, self.spec_file(d, ARCH), "-o", out, "--json")
            self.assertTrue(os.path.isfile(out))
        self.assertEqual(code, 0)
        receipt = json.loads(stdout)
        self.assertEqual((receipt["ok"], receipt["type"], receipt["nodes"], receipt["edges"], receipt["assumed"],
                          receipt["file_citations"], receipt["verified"]), (True, "architecture", 3, 2, 2, 3, 0))
        self.assertTrue(receipt["reply_first_line"].startswith("[What a checkout request touches]("))
        self.assertTrue(receipt["reply_first_line"].endswith("map.html)"))
        self.assertEqual([w["code"] for w in receipt["warnings"]], ["evidence/unchecked"])

    def test_waterfall_build_prints_the_computed_numbers(self):
        with workdir() as d:
            code, out, _ = run(SKILL, SCRIPT, self.spec_file(d, WATERFALL), "-o", os.path.join(d, "w.html"))
        self.assertEqual(code, 0)
        self.assertIn("Lead the reply with this line", out)
        self.assertIn("- The whole of POST /checkout took 1.0 s.", out)

    def test_missing_compare_base_exits_2(self):
        with workdir() as d:
            code, _, err = run(SKILL, SCRIPT, self.spec_file(d, ARCH), "--check", "--compare", os.path.join(d, "old.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)



class TestShownPath(unittest.TestCase):
    def test_a_path_on_another_drive_is_shown_absolute(self):
        # Windows: os.path.relpath raises ValueError across drives (C: vs D:).
        real = m.os.path.relpath
        def other_drive(*a, **k):
            raise ValueError("path is on mount 'C:', start on mount 'D:'")
        m.os.path.relpath = other_drive
        try:
            self.assertEqual(m.shown("out/diagram.html"), os.path.abspath("out/diagram.html"))
        finally:
            m.os.path.relpath = real

    def test_a_path_under_the_current_folder_is_shown_relative(self):
        self.assertEqual(m.shown(os.path.join("out", "d.html")), os.path.join("out", "d.html"))

if __name__ == "__main__":
    unittest.main()

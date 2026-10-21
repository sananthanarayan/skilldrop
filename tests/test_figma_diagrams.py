"""figma-diagrams: the Figma REST client and the four scripts built on it.

Every test swaps in a fake `requests` module before the script is imported, so nothing
reaches the network and no real token is needed. The fake records each request and answers
from a queue of canned responses.
"""
import contextlib
import io
import json
import os
import sys
import types
import unittest
from unittest import mock

from tests.support import load

SKILL = "figma-diagrams"
FAKE_TOKEN = "figd_fake-token-not-real"


class FakeResponse(object):
    def __init__(self, status=200, body=None, headers=None, text=None):
        self.status_code = status
        self._body = {} if body is None else body
        self.headers = headers or {}
        self.text = json.dumps(self._body) if text is None else text

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._body


def fake_requests():
    mod = types.ModuleType("requests")
    mod.Response = FakeResponse
    mod.calls = []
    mod.queue = []

    def request(method, url, headers=None, timeout=None, **kwargs):
        mod.calls.append(dict(kwargs, method=method, url=url, headers=dict(headers or {}), timeout=timeout))
        if not mod.queue:
            raise AssertionError("unexpected request: %s %s" % (method, url))
        return mod.queue.pop(0)

    mod.request = request
    return mod


class FigmaCase(unittest.TestCase):
    script = None  # set by each subclass

    def setUp(self):
        saved = {k: sys.modules.get(k) for k in ("requests", "_figma_client")}

        def restore():
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        self.addCleanup(restore)
        self.requests = fake_requests()
        sys.modules["requests"] = self.requests
        sys.modules.pop("_figma_client", None)  # a fresh client, bound to this test's fake
        env = mock.patch.dict(os.environ, {"FIGMA_TOKEN": FAKE_TOKEN})
        env.start()
        self.addCleanup(env.stop)
        self.m = load(SKILL, self.script)
        self.client = self.m if self.script == "_figma_client.py" else sys.modules["_figma_client"]
        self.sleeps = []
        self.client.time = types.SimpleNamespace(sleep=self.sleeps.append)

    def respond(self, *responses):
        self.requests.queue.extend(responses)

    def call_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = self.m.main(list(argv))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()


class TestFigmaClient(FigmaCase):
    script = "_figma_client.py"

    def test_extract_file_key_from_design_file_and_board_urls(self):
        for url in ("https://www.figma.com/design/AbC123xyz/Checkout-flow?node-id=1-2",
                    "https://www.figma.com/file/AbC123xyz/Checkout-flow",
                    "https://www.figma.com/board/AbC123xyz/Whiteboard"):
            self.assertEqual(self.m.extract_file_key(url), "AbC123xyz", url)

    def test_extract_file_key_accepts_a_bare_key(self):
        self.assertEqual(self.m.extract_file_key("AbC123xyz"), "AbC123xyz")

    def test_extract_file_key_rejects_something_else_with_exit_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            self.m.extract_file_key("https://example.com/not-figma")
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("could not extract a Figma file key", err.getvalue())

    def test_missing_token_exits_2_with_how_to_set_it_and_sends_nothing(self):
        os.environ.pop("FIGMA_TOKEN")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            self.m.get("/v1/files/KEY")
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("FIGMA_TOKEN is not set", err.getvalue())
        self.assertIn("export FIGMA_TOKEN=", err.getvalue())
        self.assertEqual(self.requests.calls, [])

    def test_get_sends_token_header_to_the_api_and_returns_json(self):
        self.respond(FakeResponse(200, {"name": "Checkout"}))
        data = self.m.get("/v1/files/KEY", params={"depth": 1})
        self.assertEqual(data, {"name": "Checkout"})
        call, = self.requests.calls
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["url"], "https://api.figma.com/v1/files/KEY")
        self.assertEqual(call["headers"]["X-Figma-Token"], FAKE_TOKEN)
        self.assertEqual(call["params"], {"depth": 1})
        self.assertEqual(call["timeout"], 30)

    def test_post_sends_the_body_as_json(self):
        self.respond(FakeResponse(200, {"id": "c1"}))
        self.assertEqual(self.m.post("/v1/files/KEY/comments", {"message": "hi"}), {"id": "c1"})
        call, = self.requests.calls
        self.assertEqual((call["method"], call["json"]), ("POST", {"message": "hi"}))

    def test_429_waits_retry_after_seconds_then_retries(self):
        self.respond(FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200, {"ok": 1}))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.m.get("/v1/files/KEY"), {"ok": 1})
        self.assertEqual(len(self.requests.calls), 2)
        self.assertEqual(self.sleeps, [7])

    def test_429_without_retry_after_waits_2_seconds(self):
        self.respond(FakeResponse(429), FakeResponse(200, {}))
        with contextlib.redirect_stderr(io.StringIO()):
            self.m.get("/v1/files/KEY")
        self.assertEqual(self.sleeps, [2])

    def test_429_three_times_gives_up_after_three_requests_and_exits_1(self):
        self.respond(*[FakeResponse(429, headers={"Retry-After": "1"}) for _ in range(3)])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            self.m.get("/v1/files/KEY")
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(len(self.requests.calls), 3)

    def test_http_error_exits_1_with_status_and_short_body_but_never_the_token(self):
        self.respond(FakeResponse(403, text="Invalid token " + "x" * 500))
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            self.m.get("/v1/files/KEY")
        self.assertEqual(cm.exception.code, 1)
        msg = err.getvalue()
        self.assertIn("GET /v1/files/KEY", msg)
        self.assertIn("403", msg)
        self.assertNotIn("x" * 201, msg)
        self.assertNotIn(FAKE_TOKEN, msg)


class TestInspectFile(FigmaCase):
    script = "inspect_file.py"

    FILE = {"name": "Checkout", "lastModified": "2026-10-01T09:00:00Z", "version": "42",
            "document": {"id": "0:0", "name": "Document", "type": "DOCUMENT", "children": [
                {"id": "0:1", "name": "Page 1", "type": "CANVAS", "children": [
                    {"id": "1:2", "name": "Flow", "type": "FRAME", "children": [
                        {"id": "1:3", "name": "Box", "type": "RECTANGLE"}]}]}]}}

    def test_prints_file_header_and_indented_tree(self):
        self.respond(FakeResponse(200, self.FILE))
        code, out, _ = self.call_main("AbC123xyz")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[:3], ["file: 'Checkout'", "last modified: 2026-10-01T09:00:00Z", "version: 42"])
        self.assertIn("- [DOCUMENT] Document  (id=0:0)", lines)
        self.assertIn("  - [CANVAS] Page 1  (id=0:1)", lines)
        self.assertIn("    - [FRAME] Flow  (id=1:2)", lines)
        self.assertIn("      - [RECTANGLE] Box  (id=1:3)", lines)

    def test_depth_limits_how_deep_the_tree_goes(self):
        self.respond(FakeResponse(200, self.FILE))
        _, out, _ = self.call_main("AbC123xyz", "--depth", "1")
        self.assertIn("[CANVAS] Page 1", out)
        self.assertNotIn("[FRAME]", out)

    def test_url_argument_requests_that_files_key(self):
        self.respond(FakeResponse(200, self.FILE))
        self.call_main("https://www.figma.com/design/AbC123xyz/Checkout")
        self.assertEqual(self.requests.calls[0]["url"], "https://api.figma.com/v1/files/AbC123xyz")


class TestListComments(FigmaCase):
    script = "list_comments.py"

    def test_lists_each_comment_with_author_time_and_resolved_tag(self):
        self.respond(FakeResponse(200, {"comments": [
            {"user": {"handle": "ada"}, "created_at": "2026-10-01T10:00:00Z", "message": "Looks good\nship it"},
            {"user": {"handle": "lin"}, "created_at": "2026-10-02T11:00:00Z", "message": "Fixed", "resolved_at": "2026-10-03"},
            {"created_at": "2026-10-04T12:00:00Z", "message": " anon "}]}))
        code, out, _ = self.call_main("AbC123xyz")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "- 2026-10-01T10:00:00Z  @ada: Looks good ship it",
            "- 2026-10-02T11:00:00Z  @lin [resolved]: Fixed",
            "- 2026-10-04T12:00:00Z  @<unknown>: anon"])
        self.assertEqual(self.requests.calls[0]["url"], "https://api.figma.com/v1/files/AbC123xyz/comments")

    def test_no_comments_says_so(self):
        self.respond(FakeResponse(200, {"comments": []}))
        code, out, _ = self.call_main("AbC123xyz")
        self.assertEqual((code, out.strip()), (0, "(no comments)"))

    def test_wrong_number_of_arguments_returns_2_with_usage(self):
        code, _, err = self.call_main()
        self.assertEqual(code, 2)
        self.assertIn("usage:", err)
        self.assertEqual(self.requests.calls, [])


class TestPostComment(FigmaCase):
    script = "post_comment.py"

    def test_posts_the_message_unpinned_without_node_id(self):
        self.respond(FakeResponse(200, {"id": "c-77"}))
        code, out, _ = self.call_main("AbC123xyz", "Please check the retry path")
        self.assertEqual(code, 0)
        call, = self.requests.calls
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.figma.com/v1/files/AbC123xyz/comments")
        self.assertEqual(call["json"], {"message": "Please check the retry path"})
        self.assertIn("comment_id=c-77", out)

    def test_node_id_pins_the_comment_to_the_nodes_centre(self):
        self.respond(FakeResponse(200, {"nodes": {"1:23": {"document": {
                         "absoluteBoundingBox": {"x": 500, "y": 300, "width": 240, "height": 90}}}}}),
                     FakeResponse(200, {"id": "c-78"}))
        code, _, _ = self.call_main("AbC123xyz", "Here", "--node-id", "1:23")
        self.assertEqual(code, 0)
        get, post = self.requests.calls
        self.assertEqual((get["method"], get["url"], get["params"]),
                         ("GET", "https://api.figma.com/v1/files/AbC123xyz/nodes", {"ids": "1:23"}))
        self.assertEqual(post["json"], {"message": "Here", "client_meta": {
            "node_id": "1:23", "node_offset": {"x": 120.0, "y": 45.0}}})

    def test_unknown_node_returns_1_and_posts_nothing(self):
        self.respond(FakeResponse(200, {"nodes": {}}))
        code, _, err = self.call_main("AbC123xyz", "Here", "--node-id", "9:99")
        self.assertEqual(code, 1)
        self.assertIn("could not resolve node 9:99", err)
        self.assertEqual([c["method"] for c in self.requests.calls], ["GET"])

    # BUG: Figma answers {"nodes": {"<id>": null}} for an unknown id; .get(id, {}) returns None and .get("document") raises AttributeError
    @unittest.expectedFailure
    def test_node_reported_as_null_by_figma_returns_1_and_posts_nothing(self):
        self.respond(FakeResponse(200, {"nodes": {"9:99": None}}))
        code, _, err = self.call_main("AbC123xyz", "Here", "--node-id", "9:99")
        self.assertEqual(code, 1)
        self.assertIn("could not resolve node 9:99", err)


class TestFrameToMermaid(FigmaCase):
    script = "frame_to_mermaid.py"

    FRAME = {"id": "1:1", "name": "Checkout flow", "type": "FRAME", "children": [
        {"id": "1:2", "name": "API", "type": "RECTANGLE"},
        {"id": "1:3", "name": "Start", "type": "ELLIPSE"},
        {"id": "1:4", "name": "Group 7", "type": "GROUP", "children": [
            {"id": "1:5", "name": "Payments", "type": "TEXT", "characters": "Payments"}]},
        {"id": "1:6", "name": "Connector", "type": "CONNECTOR",
         "connectorStart": {"endpointNodeId": "1:2"}, "connectorEnd": {"endpointNodeId": "1:3"}}]}

    def test_safe_id_makes_a_mermaid_safe_identifier(self):
        self.assertEqual(self.m.safe_id("1:23"), "n1_23")
        self.assertEqual(self.m.safe_id("I5:6;7:8"), "nI5_6_7_8")

    def test_best_label_keeps_a_real_name(self):
        self.assertEqual(self.m.best_label({"name": "Order service", "children": [
            {"type": "TEXT", "characters": "ignored"}]}), "Order service")

    def test_best_label_replaces_a_generic_name_with_text_inside(self):
        node = {"name": "Rectangle 12", "type": "RECTANGLE", "children": [
            {"name": "Frame 3", "type": "FRAME", "children": [{"type": "TEXT", "characters": " Ledger "}]}]}
        self.assertEqual(self.m.best_label(node), "Ledger")

    def test_frame_becomes_subgraphs_nodes_and_connector_edges(self):
        self.respond(FakeResponse(200, {"nodes": {"1:1": {"document": self.FRAME}}}))
        code, out, _ = self.call_main("AbC123xyz", "1:1")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "```mermaid",
            "flowchart TB",
            '    subgraph n1_1["Checkout flow"]',
            '    n1_2["API"]',
            '    n1_3(("Start"))',
            '    subgraph n1_4["Payments"]',
            '    n1_5["Payments"]',
            "    end",
            "    end",
            "    n1_1 --- n1_2",
            "    n1_1 --- n1_3",
            "    n1_4 --- n1_5",
            "    n1_2 --> n1_3",
            "```"])
        call, = self.requests.calls
        self.assertEqual((call["url"], call["params"]), ("https://api.figma.com/v1/files/AbC123xyz/nodes", {"ids": "1:1"}))

    def test_labels_lose_double_quotes_and_are_cut_to_60_characters(self):
        frame = {"id": "2:1", "name": 'Say "hi" ' + "y" * 80, "type": "RECTANGLE"}
        self.respond(FakeResponse(200, {"nodes": {"2:1": {"document": frame}}}))
        _, out, _ = self.call_main("AbC123xyz", "2:1")
        line = out.splitlines()[2]
        label = line.split('["', 1)[1].rsplit('"]', 1)[0]
        self.assertEqual(len(label), 60)
        self.assertTrue(label.startswith("Say 'hi' "))

    def test_node_missing_from_the_file_returns_1(self):
        self.respond(FakeResponse(200, {"nodes": {}}))
        code, out, err = self.call_main("AbC123xyz", "1:1")
        self.assertEqual(code, 1)
        self.assertIn("node 1:1 not found", err)
        self.assertEqual(out, "")

    # BUG: Figma answers {"nodes": {"<id>": null}} for an unknown id; .get(node_id, {}) returns None and .get("document") raises AttributeError
    @unittest.expectedFailure
    def test_node_reported_as_null_by_figma_returns_1(self):
        self.respond(FakeResponse(200, {"nodes": {"1:1": None}}))
        code, _, err = self.call_main("AbC123xyz", "1:1")
        self.assertEqual(code, 1)
        self.assertIn("node 1:1 not found", err)

    def test_wrong_number_of_arguments_returns_2(self):
        code, _, err = self.call_main("AbC123xyz")
        self.assertEqual(code, 2)
        self.assertIn("usage:", err)


if __name__ == "__main__":
    unittest.main()

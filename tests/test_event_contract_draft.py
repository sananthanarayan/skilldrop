import copy
import json
import os
import unittest

from tests.support import load, read, run, workdir, write

SKILL, SCRIPT = "event-contract-draft", "check_asyncapi.py"
m = load(SKILL, SCRIPT)

GOOD = {
    "asyncapi": "3.0.0",
    "info": {"title": "Order events", "version": "1.0.0"},
    "defaultContentType": "application/json",
    "channels": {
        "orders": {
            "address": "orders.v1",
            "description": "Facts about orders.",
            "x-partition-key": "orderId",
            "x-ordering": "Per orderId only; no global order across orders.",
            "x-delivery": "at-least-once; consumers deduplicate on eventId",
            "x-retention": "7 days",
            "x-replay": "From any offset inside retention",
            "x-dead-letter": "orders.dlq, watched by the orders team",
            "messages": {"OrderPlaced": {"$ref": "#/components/messages/OrderPlaced"}},
        }
    },
    "operations": {"publishOrderPlaced": {"action": "send", "channel": {"$ref": "#/channels/orders"}}},
    "components": {
        "messages": {"OrderPlaced": {"name": "OrderPlaced", "payload": {"$ref": "#/components/schemas/OrderPlaced"}}},
        "schemas": {"OrderPlaced": {
            "type": "object",
            "required": ["eventId", "eventType", "eventVersion", "occurredAt", "producer", "correlationId"],
            "properties": {
                "eventId": {"type": "string", "format": "uuid"},
                "eventType": {"type": "string", "const": "OrderPlaced"},
                "eventVersion": {"type": "integer"},
                "occurredAt": {"type": "string", "format": "date-time"},
                "producer": {"type": "string"},
                "correlationId": {"type": "string"},
                "causationId": {"type": "string"},
                "orderId": {"type": "string"},
            }}},
    },
}


def doc(**changes):
    d = copy.deepcopy(GOOD)
    d.update(changes)
    return d


def payload(d):
    return d["components"]["schemas"]["OrderPlaced"]


def channel(d):
    return d["channels"]["orders"]


def checked(d):
    rep, counts = m.check(d)
    return rep


def has(lines, *parts):
    return any(all(p in line for p in parts) for line in lines)


class TestCheckAsyncapi(unittest.TestCase):
    def test_a_complete_contract_has_no_failures_or_warnings(self):
        rep, counts = m.check(doc())
        self.assertEqual(rep.fails, [])
        self.assertEqual(rep.warns, [])
        self.assertEqual(counts, "1 channels, 1 messages, 1 operations")

    # structure

    def test_asyncapi_2_is_rejected(self):
        self.assertTrue(has(checked(doc(asyncapi="2.6.0")).fails, "asyncapi", "'2.6.0'", "AsyncAPI 3.x"))

    def test_missing_info_title_and_version_fail(self):
        fails = checked(doc(info={})).fails
        self.assertTrue(has(fails, "missing info.title"))
        self.assertTrue(has(fails, "missing info.version"))

    def test_unresolved_ref_fails_and_external_ref_warns(self):
        d = doc()
        channel(d)["messages"]["OrderPlaced"] = {"$ref": "#/components/messages/Nope"}
        payload(d)["properties"]["money"] = {"$ref": "https://example.test/money.json"}
        rep = checked(d)
        self.assertTrue(has(rep.fails, "#/components/messages/Nope does not resolve"))
        self.assertTrue(has(rep.warns, "external $ref https://example.test/money.json not checked"))

    def test_operation_needs_send_or_receive_and_a_channel_ref(self):
        d = doc(operations={"pub": {"action": "publish", "channel": "orders"}})
        fails = checked(d).fails
        self.assertTrue(has(fails, "operation pub", "'send' or 'receive'"))
        self.assertTrue(has(fails, "operation pub", "must be a $ref"))

    def test_no_operations_is_only_a_warning(self):
        rep = checked(doc(operations={}))
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "no operations"))

    # naming

    def name_fails(self, name):
        rep = m.Report()
        m.check_name(name, "message x", rep)
        return rep.fails

    def test_past_tense_names_pass(self):
        for name in ("OrderPlaced", "OrderPaid", "UserSignedUp", "order.shipped", "OrderPlacedV2", "PaymentCaptured.v3"):
            self.assertEqual(self.name_fails(name), [], name)

    def test_command_name_fails_as_a_command(self):
        self.assertTrue(has(self.name_fails("CreateShipment"), "reads as a command (Create ...)"))

    def test_generic_noun_name_fails(self):
        self.assertTrue(has(self.name_fails("OrderEvent"), "generic noun ('event')"))

    def test_present_tense_name_fails(self):
        self.assertTrue(has(self.name_fails("OrderPlace"), "is not past tense"))

    # envelope

    def test_missing_correlation_id_is_named_in_the_failure(self):
        d = doc()
        del payload(d)["properties"]["correlationId"]
        payload(d)["required"].remove("correlationId")
        self.assertTrue(has(checked(d).fails, "envelope fields missing", "correlation id (correlationId)"))

    def test_message_level_correlation_id_satisfies_the_envelope(self):
        d = doc()
        del payload(d)["properties"]["correlationId"]
        payload(d)["required"].remove("correlationId")
        d["components"]["messages"]["OrderPlaced"]["correlationId"] = {"location": "$message.header#/correlationId"}
        self.assertEqual(checked(d).fails, [])

    def test_envelope_field_that_is_not_required_fails(self):
        d = doc()
        payload(d)["required"].remove("eventId")
        self.assertTrue(has(checked(d).fails, "event id field payload.eventId is not in 'required'"))

    def test_occurred_at_needs_date_time_format(self):
        d = doc()
        payload(d)["properties"]["occurredAt"] = {"type": "string"}
        self.assertTrue(has(checked(d).fails, "payload.occurredAt needs format: date-time"))

    def test_envelope_can_live_in_headers_or_a_metadata_object_in_snake_case(self):
        d = doc()
        meta = {"type": "object", "required": ["event_id", "event_type", "event_version", "occurred_at", "producer"],
                "properties": {"event_id": {}, "event_type": {}, "event_version": {}, "producer": {},
                               "occurred_at": {"format": "date-time"}}}
        d["components"]["schemas"]["OrderPlaced"] = {"type": "object", "properties": {"metadata": meta, "orderId": {}}}
        d["components"]["messages"]["OrderPlaced"]["headers"] = {
            "type": "object", "required": ["correlation_id"],
            "properties": {"correlation_id": {}, "causation_id": {}}}
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertFalse(has(rep.warns, "causation"))

    def test_more_than_one_event_type_in_one_message_fails(self):
        d = doc()
        payload(d)["properties"]["eventType"] = {"type": "string", "enum": ["OrderPlaced", "OrderCancelled"]}
        self.assertTrue(has(checked(d).fails, "payload.eventType allows 2 event types"))

    def test_no_causation_id_is_a_warning_not_a_failure(self):
        d = doc()
        del payload(d)["properties"]["causationId"]
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "no causation id"))

    def test_message_without_payload_fails(self):
        d = doc()
        del d["components"]["messages"]["OrderPlaced"]["payload"]
        self.assertTrue(has(checked(d).fails, "message has no payload schema"))

    # privacy and openness

    def test_unmarked_personal_data_fails_and_marked_is_noted(self):
        d = doc()
        payload(d)["properties"]["customerEmail"] = {"type": "string"}
        payload(d)["properties"]["shippingAddress"] = {"type": "string", "x-pii": True}
        rep = checked(d)
        self.assertTrue(has(rep.fails, "payload.customerEmail", "no x-pii marker"))
        self.assertFalse(has(rep.fails, "shippingAddress"))
        self.assertTrue(has(rep.notes, "PII (marked)", "payload.shippingAddress"))

    def test_card_number_fails_even_when_marked(self):
        d = doc()
        payload(d)["properties"]["cardNumber"] = {"type": "string", "x-pii": True}
        self.assertTrue(has(checked(d).fails, "payload.cardNumber", "card data never goes on an event"))

    def test_fields_inside_a_marked_object_are_covered_by_its_marker(self):
        d = doc()
        payload(d)["properties"]["customer"] = {"type": "object", "x-pii": True,
                                                "properties": {"email": {}, "phone": {}}}
        self.assertEqual(checked(d).fails, [])

    def test_personal_data_inside_array_items_is_found(self):
        d = doc()
        payload(d)["properties"]["recipients"] = {"type": "array", "items": {"type": "object",
                                                                             "properties": {"email": {}}}}
        self.assertTrue(has(checked(d).fails, "payload.recipients[].email", "no x-pii marker"))

    def test_closed_schema_is_a_warning(self):
        d = doc()
        payload(d)["additionalProperties"] = False
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "payload", "additionalProperties: false"))

    # evolution

    def add_message(self, d, key, msg):
        d["components"]["messages"][key] = msg
        channel(d)["messages"][key] = {"$ref": "#/components/messages/" + key}

    def test_deprecated_message_needs_sunset_and_replacement(self):
        d = doc()
        d["components"]["messages"]["OrderPlaced"]["x-deprecated"] = True
        fails = checked(d).fails
        self.assertTrue(has(fails, "deprecated without x-sunset"))
        self.assertTrue(has(fails, "deprecated without x-replaced-by"))

    def test_deprecated_message_with_a_dated_sunset_and_real_replacement_passes(self):
        d = doc()
        self.add_message(d, "OrderPlacedV2", {"name": "OrderPlacedV2", "payload": {"$ref": "#/components/schemas/OrderPlaced"}})
        d["components"]["messages"]["OrderPlaced"].update(
            {"x-deprecated": True, "x-sunset": "2027-01-31", "x-replaced-by": {"$ref": "#/components/messages/OrderPlacedV2"}})
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertEqual(rep.warns, [])

    def test_sunset_that_is_not_a_date_warns_and_unknown_replacement_fails(self):
        d = doc()
        d["components"]["messages"]["OrderPlaced"].update(
            {"x-deprecated": True, "x-sunset": "next quarter", "x-replaced-by": "OrderPlacedV9"})
        rep = checked(d)
        self.assertTrue(has(rep.warns, "x-sunset is 'next quarter', not a date"))
        self.assertTrue(has(rep.fails, "x-replaced-by OrderPlacedV9 names no message"))

    def test_older_version_left_undeprecated_warns(self):
        d = doc()
        self.add_message(d, "OrderPlacedV2", {"name": "OrderPlacedV2", "payload": {"$ref": "#/components/schemas/OrderPlaced"}})
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "message OrderPlaced", "OrderPlaced and a newer version of OrderPlaced",
                            "not marked x-deprecated"))

    def test_deprecated_messages_own_faults_are_warnings(self):
        d = doc()
        self.add_message(d, "CreateOrder", {"name": "CreateOrder", "x-deprecated": True, "x-sunset": "2027-01-31",
                                            "x-replaced-by": "OrderPlaced",
                                            "payload": {"properties": {"email": {}}}})
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "WARN  (deprecated) message CreateOrder", "reads as a command"))
        self.assertTrue(has(rep.warns, "(deprecated)", "payload.email", "no x-pii marker"))

    # channels

    def test_each_missing_channel_promise_is_reported(self):
        d = doc()
        for key in ("x-partition-key", "x-ordering", "x-delivery", "x-retention", "x-replay", "x-dead-letter"):
            del channel(d)[key]
        rep = checked(d)
        for words in ("partition/ordering key", "says nothing about ordering", "no delivery semantics",
                      "no retention", "no dead-letter handling"):
            self.assertTrue(has(rep.fails, "channel orders", words), words)
        self.assertTrue(has(rep.warns, "channel orders", "no replay statement"))
        self.assertFalse(has(rep.fails, "replay"))

    def test_description_can_carry_every_channel_promise(self):
        d = doc()
        for key in ("x-partition-key", "x-ordering", "x-delivery", "x-retention", "x-replay", "x-dead-letter"):
            del channel(d)[key]
        channel(d)["description"] = ("Keyed by orderId, ordered per key. At-least-once. Retention 7 days. "
                                     "Consumers can replay from an offset. Failures go to a dead-letter topic.")
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertEqual(rep.warns, [])

    def test_kafka_message_key_binding_counts_as_the_partition_key(self):
        d = doc()
        del channel(d)["x-partition-key"]
        d["components"]["messages"]["OrderPlaced"]["bindings"] = {"kafka": {"key": {"type": "string"}}}
        self.assertFalse(has(checked(d).fails, "partition/ordering key"))

    def test_global_ordering_promise_fails(self):
        d = doc()
        channel(d)["x-ordering"] = "Events are globally ordered across all orders."
        self.assertTrue(has(checked(d).fails, "channel orders", "promises global/total ordering"))

    def test_exactly_once_claim_warns(self):
        d = doc()
        channel(d)["x-delivery"] = "exactly-once"
        rep = checked(d)
        self.assertEqual(rep.fails, [])
        self.assertTrue(has(rep.warns, "claims exactly-once"))

    def test_channel_with_no_messages_fails(self):
        d = doc()
        channel(d)["messages"] = {}
        self.assertTrue(has(checked(d).fails, "channel orders", "lists no messages"))

    # malformed documents

    # BUG: a structurally wrong document (channels is a list) crashes with AttributeError instead of a FAIL line
    @unittest.expectedFailure
    def test_channels_given_as_a_list_is_a_failure_not_a_crash(self):
        rep = checked(doc(channels=["orders"]))
        self.assertTrue(rep.fails)

    # BUG: info given as a string crashes with AttributeError ('str' has no .get) instead of a FAIL line
    @unittest.expectedFailure
    def test_info_given_as_a_string_is_a_failure_not_a_crash(self):
        rep = checked(doc(info="Order events 1.0"))
        self.assertTrue(has(rep.fails, "info"))


class TestCheckAsyncapiCli(unittest.TestCase):
    def test_clean_contract_exits_0_with_a_result_line(self):
        with workdir() as d:
            path = write(os.path.join(d, "asyncapi.json"), json.dumps(GOOD))
            code, out, _ = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 0)
        self.assertIn("1 channels, 1 messages, 1 operations", out)
        self.assertIn("Result: 0 failures, 0 warnings", out)

    def test_failures_exit_1_and_are_counted(self):
        bad = doc(asyncapi="2.6.0", info={"title": "Order events"})
        with workdir() as d:
            path = write(os.path.join(d, "asyncapi.json"), json.dumps(bad))
            code, out, _ = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 1)
        self.assertIn("FAIL  asyncapi:", out)
        self.assertIn("Result: 2 failures, 0 warnings", out)

    def test_warnings_alone_still_exit_0(self):
        with workdir() as d:
            path = write(os.path.join(d, "asyncapi.json"), json.dumps(doc(operations={})))
            code, out, _ = run(SKILL, SCRIPT, path)
        self.assertEqual(code, 0)
        self.assertIn("Result: 0 failures, 1 warnings", out)

    def test_reads_stdin_with_dash(self):
        code, out, _ = run(SKILL, SCRIPT, "-", stdin=json.dumps(GOOD))
        self.assertEqual(code, 0)
        self.assertIn("AsyncAPI check: -", out)

    def test_output_flag_writes_the_same_report(self):
        with workdir() as d:
            path = write(os.path.join(d, "asyncapi.json"), json.dumps(GOOD))
            report = os.path.join(d, "check-report.txt")
            code, out, _ = run(SKILL, SCRIPT, path, "-o", report)
            self.assertEqual(code, 0)
            self.assertEqual(read(report).splitlines(), out.splitlines())

    def test_unreadable_inputs_exit_2_with_a_message_and_no_traceback(self):
        cases = {
            "missing": (None, "cannot read"),
            "empty.json": ("  \n", "is empty"),
            "contract.yaml": ("asyncapi: 3.0.0\n", "is not JSON"),
            "broken.json": ('{"asyncapi": "3.0.0",\n  oops}', "not valid JSON"),
            "list.json": ("[1, 2]", "JSON object at the top level"),
        }
        with workdir() as d:
            for name, (text, expect) in cases.items():
                path = os.path.join(d, name)
                if text is not None:
                    write(path, text)
                code, out, err = run(SKILL, SCRIPT, path)
                self.assertEqual(code, 2, name)
                self.assertIn(expect, err, name)
                self.assertNotIn("Traceback", err, name)
                self.assertEqual(out, "", name)

    def test_invalid_json_message_gives_the_line(self):
        with workdir() as d:
            path = write(os.path.join(d, "broken.json"), '{"asyncapi": "3.0.0",\n  oops}')
            _, _, err = run(SKILL, SCRIPT, path)
        self.assertIn("line 2", err)


if __name__ == "__main__":
    unittest.main()

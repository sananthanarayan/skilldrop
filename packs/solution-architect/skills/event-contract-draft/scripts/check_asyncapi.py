#!/usr/bin/env python3
"""Check an AsyncAPI 3.0 event contract (JSON) for the rules a reviewer checks by eye.

Reads one AsyncAPI 3.0 document as JSON (AsyncAPI accepts JSON as-is; the
standard library has no YAML parser, so emit the contract as JSON) and reports:

  structure   asyncapi is 3.x, info.title / info.version present, channels present,
              every local $ref resolves, operations point at a channel
  naming      every message name is a fact in the past tense (OrderPlaced), not a
              command (CreateShipment) or a generic noun (OrderEvent)
  envelope    every message carries, in its headers or payload, required fields for
              event id, event type, event version, occurred-at (format date-time),
              producer and correlation id; causation id is a warning
  one type    an event-type field with more than one allowed value is a failure
  privacy     a field that looks like personal data must carry an x-pii marker;
              card numbers fail outright
  evolution   additionalProperties: false is a warning (consumers must be able to
              ignore unknown fields); a deprecated message needs x-replaced-by and
              an x-sunset date; an older version left undeprecated is a warning;
              a deprecated message's own naming/envelope/privacy faults are warnings,
              because it documents what is live today
  channels    every channel names its key (x-partition-key or a description), what
              ordering that key gives (x-ordering), delivery semantics (x-delivery),
              retention (x-retention) and dead-letter handling (x-dead-letter);
              replay (x-replay) is a warning; a global-ordering promise is a failure

Usage:
    python3 check_asyncapi.py asyncapi.json
    python3 check_asyncapi.py asyncapi.json -o check-report.txt
    cat asyncapi.json | python3 check_asyncapi.py -

Exit codes: 0 no failures (warnings allowed), 1 failures found, 2 unreadable input.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Envelope roles and the field names accepted for each (camelCase, snake_case, CloudEvents).
ENVELOPE = {
    "event id": ["eventId", "event_id", "id"],
    "event type": ["eventType", "event_type", "type"],
    "event version": ["eventVersion", "event_version", "schemaVersion", "schema_version",
                      "version", "dataschema"],
    "occurred-at": ["occurredAt", "occurred_at", "time"],
    "producer": ["producer", "source"],
    "correlation id": ["correlationId", "correlation_id"],
}
CAUSATION = ["causationId", "causation_id"]
ENVELOPE_CONTAINERS = {"metadata", "meta", "envelope", "header", "headers"}

COMMAND_VERBS = {
    "add", "approve", "calculate", "cancel", "change", "create", "delete", "do", "emit",
    "execute", "generate", "get", "handle", "make", "notify", "pay", "place", "process",
    "publish", "refund", "register", "reject", "remove", "request", "run", "send", "set",
    "ship", "start", "submit", "sync", "trigger", "update", "upsert",
}
GENERIC_SUFFIXES = {
    "event", "events", "message", "msg", "command", "cmd", "request", "notification",
    "data", "payload", "info", "update", "updates", "change", "changes",
}
IRREGULAR_PAST = {
    "begun", "bought", "broken", "built", "caught", "chosen", "cut", "done", "drawn",
    "found", "frozen", "given", "held", "hidden", "kept", "known", "laid", "left", "lost",
    "made", "met", "paid", "put", "quit", "read", "reset", "rewritten", "run", "seen",
    "sent", "set", "shown", "shut", "sold", "split", "spent", "stolen", "struck", "taken",
    "thrown", "told", "undone", "upheld", "withdrawn", "won", "written",
}
PARTICLES = {"up", "out", "in", "off", "over", "back", "down", "on", "away"}

PII_EXACT = {
    "email", "emailaddress", "phone", "phonenumber", "mobile", "mobilenumber", "firstname",
    "lastname", "surname", "givenname", "fullname", "customername", "recipientname",
    "address", "streetaddress", "deliveryaddress", "shippingaddress", "billingaddress",
    "homeaddress", "postcode", "zipcode", "postalcode", "dateofbirth", "dob", "birthdate",
    "ipaddress", "ip", "nationalid", "ssn", "nino", "passportnumber", "taxid", "iban",
    "accountnumber",
}
PII_SUFFIXES = ("email", "phone", "phonenumber", "address", "dateofbirth")
CARD_FIELDS = {"cardnumber", "pan", "primaryaccountnumber", "cvv", "cvc", "securitycode"}

VERSION_SUFFIX = re.compile(r"[._-]?v(\d+)$", re.IGNORECASE)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
KEY_TEXT = re.compile(r"\b(partition|ordering|message[- ]group|routing)[- ]key\b|\bkeyed (by|on)\b",
                      re.IGNORECASE)
ORDER_TEXT = re.compile(r"\border(ed|ing)\b", re.IGNORECASE)
GLOBAL_ORDER = re.compile(r"\b(global(ly)?|total(ly)?|strict(ly)?)\s+(order|ordered|ordering)\b",
                          re.IGNORECASE)
NEGATION = re.compile(r"\b(no|not|never|without|isn't|doesn't|cannot|can't)\b[^.;]{0,40}"
                      r"\b(global|total|strict)", re.IGNORECASE)
DELIVERY_TEXT = re.compile(r"\b(at[- ]least[- ]once|at[- ]most[- ]once|exactly[- ]once)\b",
                           re.IGNORECASE)
EXACTLY_ONCE = re.compile(r"\bexactly[- ]once\b", re.IGNORECASE)
RETENTION_TEXT = re.compile(r"\b(retention|retained|retain|kept for)\b", re.IGNORECASE)
REPLAY_TEXT = re.compile(r"\b(replay|re-?read|rewind|seek)\b", re.IGNORECASE)
DLQ_TEXT = re.compile(r"\b(dead[- ]letter|dlq|dlx)\b", re.IGNORECASE)


class Report:
    def __init__(self):
        self.fails = []
        self.warns = []
        self.notes = []

    def fail(self, where, msg):
        self.fails.append(f"FAIL  {where}: {msg}")

    def warn(self, where, msg):
        self.warns.append(f"WARN  {where}: {msg}")


def load(path):
    try:
        text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc.strerror}")
    stripped = text.lstrip()
    if not stripped:
        raise SystemExit(f"error: {path} is empty")
    if stripped[0] not in "{[":
        raise SystemExit(f"error: {path} is not JSON. This checker reads JSON only; emit the "
                         "AsyncAPI document as JSON (AsyncAPI accepts JSON as-is).")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {path} is not valid JSON: {exc.msg} at line {exc.lineno}, "
                         f"column {exc.colno}")
    if not isinstance(doc, dict):
        raise SystemExit(f"error: {path} must hold a JSON object at the top level")
    return doc


def pointer(doc, ref):
    """Resolve a local JSON pointer like #/components/messages/OrderPlaced; None if missing."""
    if ref == "#":
        return doc
    if not ref.startswith("#/"):
        return None
    node = doc
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return None
    return node


def deref(doc, node, depth=0):
    while isinstance(node, dict) and "$ref" in node and depth < 32:
        target = pointer(doc, node["$ref"]) if isinstance(node["$ref"], str) else None
        if target is None:
            return {}
        node, depth = target, depth + 1
    return node if isinstance(node, dict) else {}


def check_refs(doc, node, rep, path="#"):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            if not ref.startswith("#"):
                rep.warn(path, f"external $ref {ref} not checked; inline it or check it separately")
            elif pointer(doc, ref) is None:
                rep.fail(path, f"$ref {ref} does not resolve")
        for key, value in node.items():
            check_refs(doc, value, rep, f"{path}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            check_refs(doc, value, rep, f"{path}/{i}")


def flatten(doc, schema, depth=0):
    """Return (properties, required) for a schema, merging allOf members."""
    schema = deref(doc, schema)
    props = dict(schema.get("properties") or {})
    required = set(schema.get("required") or [])
    if depth < 8:
        for part in schema.get("allOf") or []:
            sub_props, sub_req = flatten(doc, part, depth + 1)
            for name, sub in sub_props.items():
                props.setdefault(name, sub)
            required |= sub_req
    return props, required


def words(name):
    base = VERSION_SUFFIX.sub("", name)
    base = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", base)
    return [w.lower() for w in re.split(r"[\s._\-:/]+", base) if w]


def check_name(name, where, rep):
    parts = words(name)
    if not parts:
        rep.fail(where, "message has no name")
        return
    last = parts[-1]
    if last in PARTICLES and len(parts) > 1:
        last = parts[-2]
    if last.endswith("ed") or last in IRREGULAR_PAST:
        return
    if parts[0] in COMMAND_VERBS and len(parts) > 1:
        rep.fail(where, f"'{name}' reads as a command ({parts[0].title()} ...); name the fact "
                        "that happened, in the past tense, in the producer's domain "
                        "(e.g. OrderPaid, not CreateShipment)")
    elif parts[-1] in GENERIC_SUFFIXES:
        rep.fail(where, f"'{name}' ends in a generic noun ('{parts[-1]}'); one event type per "
                        "message, named as a past-tense fact (OrderPlaced, not OrderEvent)")
    else:
        rep.fail(where, f"'{name}' is not past tense; name the fact that happened "
                        "(OrderPlaced, PaymentCaptured)")


def find_field(props, aliases):
    for alias in aliases:
        if alias in props:
            return alias
    return None


def envelope_sources(doc, message):
    """Yield (label, properties, required) for each schema an envelope field can live in."""
    sources = []
    for label in ("headers", "payload"):
        if label in message:
            props, req = flatten(doc, message[label])
            sources.append((label, props, req))
            for cname, csub in props.items():
                if cname.lower() in ENVELOPE_CONTAINERS:
                    cprops, creq = flatten(doc, csub)
                    sources.append((f"{label}.{cname}", cprops, creq))
    return sources


def check_envelope(doc, message, where, rep):
    sources = envelope_sources(doc, message)
    if not any(label == "payload" for label, _, _ in sources):
        rep.fail(where, "message has no payload schema")
    missing = []
    for role, aliases in ENVELOPE.items():
        hit = None
        for label, props, req in sources:
            field = find_field(props, aliases)
            if field:
                hit = (label, field, props[field], req)
                break
        if hit is None:
            if role == "correlation id" and "correlationId" in message:
                continue
            missing.append(f"{role} ({aliases[0]})")
            continue
        label, field, schema, req = hit
        if field not in req:
            rep.fail(where, f"{role} field {label}.{field} is not in 'required'")
        schema = deref(doc, schema)
        if role == "occurred-at" and schema.get("format") != "date-time":
            rep.fail(where, f"{label}.{field} needs format: date-time (UTC, RFC 3339)")
        if role == "event type":
            enum = schema.get("enum")
            if isinstance(enum, list) and len(enum) > 1:
                rep.fail(where, f"{label}.{field} allows {len(enum)} event types; one event "
                                "type per message schema")
    if missing:
        rep.fail(where, "envelope fields missing from headers and payload: " + ", ".join(missing))
    if not any(find_field(props, CAUSATION) for _, props, _ in sources):
        rep.warn(where, "no causation id (causationId); consumers cannot tell which event "
                        "caused this one")


def walk_props(doc, schema, path, depth=0):
    """Yield (path, name, schema) for every property, descending into objects and arrays."""
    if depth > 12:
        return
    schema = deref(doc, schema)
    props, _ = flatten(doc, schema)
    for name, sub in props.items():
        sub_r = deref(doc, sub)
        yield f"{path}.{name}", name, sub_r
        yield from walk_props(doc, sub_r, f"{path}.{name}", depth + 1)
    items = schema.get("items")
    if isinstance(items, dict):
        yield from walk_props(doc, items, f"{path}[]", depth + 1)
    for key in ("oneOf", "anyOf"):
        for i, part in enumerate(schema.get(key) or []):
            yield from walk_props(doc, part, f"{path}({key}{i})", depth + 1)


def check_privacy_and_openness(doc, message, where, rep):
    for label in ("headers", "payload"):
        if label not in message:
            continue
        root = deref(doc, message[label])
        if root.get("additionalProperties") is False:
            rep.warn(f"{where}.{label}", "additionalProperties: false; a validating consumer "
                     "then rejects every additive change. Leave the schema open")
        marked = []
        for path, name, sub in walk_props(doc, message[label], label):
            if any(path.startswith(m + ".") or path.startswith(m + "[") for m in marked):
                continue
            norm = re.sub(r"[^a-z0-9]", "", name.lower())
            if "x-pii" in sub and path not in marked:
                marked.append(path)
            if sub.get("additionalProperties") is False:
                rep.warn(f"{where}.{path}", "additionalProperties: false; leave it open so "
                         "new optional fields are not breaking")
            if norm in CARD_FIELDS:
                rep.fail(f"{where}.{path}", "card data never goes on an event; send a token "
                         "or a reference instead")
            elif norm in PII_EXACT or norm.endswith(PII_SUFFIXES):
                if "x-pii" in sub:
                    marked.append(path)
                    rep.notes.append(f"PII (marked): {where}.{path}")
                else:
                    rep.fail(f"{where}.{path}", "looks like personal data and has no x-pii "
                             "marker; drop it unless a named consumer needs it, and mark it "
                             "x-pii if it stays")


def channel_text(channel):
    parts = [str(channel.get("description") or ""), str(channel.get("summary") or "")]
    for key, value in channel.items():
        if key.startswith("x-"):
            parts.append(json.dumps(value) if not isinstance(value, str) else value)
    return " ".join(parts)


def has_kafka_key(doc, channel):
    for msg in (channel.get("messages") or {}).values():
        m = deref(doc, msg)
        if (m.get("bindings") or {}).get("kafka", {}).get("key"):
            return True
    return False


def check_channel(doc, name, channel, rep):
    where = f"channel {name}"
    text = channel_text(channel)
    desc = str(channel.get("description") or "")
    if not channel.get("messages"):
        rep.fail(where, "lists no messages")
    has_key = any(k in channel for k in ("x-partition-key", "x-ordering-key", "x-message-group-id")) \
        or has_kafka_key(doc, channel) or KEY_TEXT.search(desc)
    if not has_key:
        rep.fail(where, "names no partition/ordering key (x-partition-key or the description)")
    if "x-ordering" not in channel and not ORDER_TEXT.search(desc):
        rep.fail(where, "says nothing about ordering (x-ordering): what order the key gives "
                        "and what it does not")
    if GLOBAL_ORDER.search(text) and not NEGATION.search(text):
        rep.fail(where, "promises global/total ordering; brokers order per partition key only. "
                        "State per-key ordering and that there is no global order")
    if "x-delivery" not in channel and not DELIVERY_TEXT.search(desc):
        rep.fail(where, "no delivery semantics (x-delivery: at-least-once unless proven otherwise)")
    elif EXACTLY_ONCE.search(text) and not re.search(r"\bnot exactly[- ]once\b", text, re.I):
        rep.warn(where, "claims exactly-once; that holds inside the broker at best, so consumers "
                        "still deduplicate on the event id")
    if "x-retention" not in channel and not RETENTION_TEXT.search(desc):
        rep.fail(where, "no retention (x-retention): how long messages are kept")
    if "x-replay" not in channel and not REPLAY_TEXT.search(desc):
        rep.warn(where, "no replay statement (x-replay): can a consumer re-read, and from where")
    if "x-dead-letter" not in channel and not DLQ_TEXT.search(desc):
        rep.fail(where, "no dead-letter handling (x-dead-letter): what goes there and who watches it")


def collect_messages(doc):
    """Return list of (name, where, message) with each distinct message object once."""
    seen = {}
    out = []
    comps = (doc.get("components") or {}).get("messages") or {}
    for key, msg in comps.items():
        m = deref(doc, msg)
        if id(m) not in seen:
            seen[id(m)] = key
            out.append((m.get("name") or key, f"message {key}", m))
    for cname, channel in (doc.get("channels") or {}).items():
        ch = deref(doc, channel)
        for key, msg in (ch.get("messages") or {}).items():
            m = deref(doc, msg)
            if not m:
                continue  # an unresolved $ref, already reported
            if id(m) not in seen:
                seen[id(m)] = key
                out.append((m.get("name") or key, f"channel {cname} message {key}", m))
    return out


def check_versions(doc, messages, rep):
    names = {}
    for name, where, msg in messages:
        names[name] = msg
    by_base = {}
    for name, where, msg in messages:
        match = VERSION_SUFFIX.search(name)
        version = int(match.group(1)) if match else 1
        by_base.setdefault(VERSION_SUFFIX.sub("", name), []).append((version, name, where, msg))
    for base, versions in by_base.items():
        if len(versions) < 2:
            continue
        versions.sort()
        for version, name, where, msg in versions[:-1]:
            if not (msg.get("x-deprecated") or msg.get("deprecated")):
                rep.warn(where, f"{name} and a newer version of {base} both exist but {name} is "
                                "not marked x-deprecated with a sunset date")
    for name, where, msg in messages:
        if not (msg.get("x-deprecated") or msg.get("deprecated")):
            continue
        sunset = msg.get("x-sunset")
        if not sunset:
            rep.fail(where, "deprecated without x-sunset (the date the dual-publish window ends)")
        elif not ISO_DATE.match(str(sunset)):
            rep.warn(where, f"x-sunset is '{sunset}', not a date; agree the date and list it as "
                            "open until then")
        repl = msg.get("x-replaced-by")
        if not repl:
            rep.fail(where, "deprecated without x-replaced-by (the event consumers move to)")
        else:
            ref = repl.get("$ref") if isinstance(repl, dict) else repl
            if not (ref in names or (isinstance(ref, str) and pointer(doc, ref) is not None)):
                rep.fail(where, f"x-replaced-by {ref} names no message in this document")


def check(doc):
    rep = Report()
    version = str(doc.get("asyncapi") or "")
    if not version.startswith("3."):
        rep.fail("asyncapi", f"version is '{version or 'missing'}'; this checks AsyncAPI 3.x")
    info = doc.get("info") or {}
    for field in ("title", "version"):
        if not info.get(field):
            rep.fail("info", f"missing info.{field}")
    if not doc.get("defaultContentType"):
        rep.warn("document", "no defaultContentType (application/json, application/cloudevents+json, ...)")
    check_refs(doc, doc, rep)

    channels = doc.get("channels") or {}
    if not channels:
        rep.fail("channels", "no channels")
    for name, channel in channels.items():
        check_channel(doc, name, deref(doc, channel), rep)

    messages = collect_messages(doc)
    if not messages:
        rep.fail("messages", "no messages")
    for name, where, msg in messages:
        if msg.get("x-deprecated") or msg.get("deprecated"):
            # A deprecated message documents what is live today; its faults are why it is
            # being replaced, so they are reported as warnings, not failures.
            legacy = Report()
            check_name(name, where, legacy)
            check_envelope(doc, msg, where, legacy)
            check_privacy_and_openness(doc, msg, where, legacy)
            rep.warns += [line.replace("FAIL  ", "WARN  (deprecated) ", 1)
                          for line in legacy.fails] + legacy.warns
            rep.notes += legacy.notes
            continue
        check_name(name, where, rep)
        check_envelope(doc, msg, where, rep)
        check_privacy_and_openness(doc, msg, where, rep)
    check_versions(doc, messages, rep)

    operations = doc.get("operations") or {}
    if not operations:
        rep.warn("operations", "no operations; say who sends and who receives each channel")
    for name, op in operations.items():
        op = deref(doc, op)
        where = f"operation {name}"
        if op.get("action") not in ("send", "receive"):
            rep.fail(where, "action must be 'send' or 'receive'")
        ch = op.get("channel")
        if not (isinstance(ch, dict) and isinstance(ch.get("$ref"), str)):
            rep.fail(where, "channel must be a $ref to a channel")
    counts = f"{len(channels)} channels, {len(messages)} messages, {len(operations)} operations"
    return rep, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("path", help="AsyncAPI 3.0 document as JSON, or - for stdin")
    parser.add_argument("-o", "--output", help="write the report to this path as well as stdout")
    args = parser.parse_args(argv)
    try:
        doc = load(args.path)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    rep, counts = check(doc)
    lines = [f"AsyncAPI check: {args.path}", f"  {counts}"]
    lines += rep.fails + rep.warns + rep.notes
    lines.append(f"Result: {len(rep.fails)} failures, {len(rep.warns)} warnings")
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())

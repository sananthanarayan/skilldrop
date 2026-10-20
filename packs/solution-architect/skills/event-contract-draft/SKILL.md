---
name: event-contract-draft
description: Draft the contract for an event or message interface (Kafka topics, SNS/SQS, EventBridge, Pub/Sub, RabbitMQ, webhooks) as an AsyncAPI 3.0 document plus a short decisions page — past-tense event names, a required envelope with event id for deduplication, the partition key and the ordering it does and doesn't give, at-least-once delivery and how consumers stay idempotent, data minimisation with PII marked, additive-only versioning with dated deprecation, and retention, replay and dead-letter handling. Use when the user wants to define events, design a Kafka topic or message schema, write an AsyncAPI spec, agree what a producer publishes and what consumers must do, or version an event safely.
---

# event-contract-draft

Produces the contract for an asynchronous interface before producer and consumers build
against it: an AsyncAPI 3.0 document and a one-page decisions record. Request/response HTTP
APIs are `api-contract-draft`; a dataset's schema and quality SLAs for analytics readers are
`data-contract`; the system design that decides events are the right tool is `design-doc`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** When the request asks for something an event contract can't promise (global order, exactly-once, "change it in place", "include it just in case"), the first lines say no, why, and what the contract offers instead. Building the unsafe version quietly is the failure this skill exists to prevent.

1. **Size the reply to the ask.** A question about one rule ("is ordering guaranteed if we key
   by paymentId?") gets a direct answer in a few lines: yes or no, why, the fix. No AsyncAPI
   document. A request to define events gets the full contract (step 11).

2. **List the facts, the producer and the consumers.** For each consumer, write what it does
   with each event; that line decides payload size and justifies every field. Ask at most 2
   questions, spent on who consumes and what they do with it, and which broker. Missing broker
   → write broker-neutral with a Kafka binding, tagged `[assumption]`.

3. **Name events as facts, past tense, in the producer's domain.** One event type per message
   schema.
   - ✅ `OrderPaid` — ❌ `CreateShipment`. A command tells another team what to do and couples
     the producer to the warehouse's process; the warehouse decides to pick when it sees
     `OrderPaid`. If one named receiver must act, that is a command on the receiver's queue,
     outside this contract; say so.
   - ✅ `OrderPlaced`, `OrderCancelled` — ❌ `OrderEvent` with a `status` field. A generic
     event makes every consumer parse a union and breaks them all when a status is added.
   - ✅ `OrderDeliveryAddressChanged` — ❌ `OrderUpdated` when the business fact has a name.

4. **Decide notification or event-carried state per event, with the reason.** Notification =
   ids plus a link; consumers call back. Event-carried state = the fields named consumers act
   on, so they never call back. ✅ *"`OrderPaid` carries lines and address: fulfilment picks
   without calling the order API."* ❌ The whole order aggregate on every event "for
   flexibility". Table in [`reference.md`](reference.md).

5. **Put the envelope on every message, all required:** event id, event type, event version,
   occurred-at (UTC, RFC 3339, `format: date-time`), producer, correlation id; causation id
   too. Domain fields go under `data`, with a per-entity revision (`orderRevision`) that
   increases on each change. ❌ `"placedAt": "2026-10-19 14:03:11"` — no zone, not RFC 3339.
   Money is integer minor units plus currency: ❌ `"total": 42.50`.

6. **State delivery, ordering and duplicates per channel.**
   - **Delivery is at-least-once** unless the broker and the consumer prove otherwise.
     Consumers deduplicate on the event id or apply only a higher revision; name which, per
     consumer. ✅ *"Loyalty awards points keyed on (orderId, reason); a second OrderPaid is a
     no-op."* ❌ "Exactly-once delivery" in the description.
   - **Ordering exists only per partition key.** Name the key, what it orders, and what it
     doesn't. ✅ *"Keyed by orderId: one order's events arrive in order. No order across
     orders, no global order."* Events whose relative order matters (`OrderPaid`,
     `OrderCancelled`) share one channel and one key; on two topics they race.
   - **A global-order request is declined.** One partition means one consumer at a time, and
     retries and dead-letter redrives reorder it anyway. Offer what the reader needs:
     per-entity order plus `occurredAt` and the revision, sorted at read time.
   - **The producer publishes each entity's events in commit order** (an outbox written in
     the same transaction), or the per-key promise is false.
   - **Webhooks** have no ordering: receivers use the revision. Sign the raw body (HMAC) with
     a timestamp inside the signature so receivers reject replays; state the retry schedule,
     its cap, and where deliveries that keep failing go.

7. **Minimise the data.** Every field names the consumer that uses it; no consumer, no field.
   ❌ `customerEmail` "just in case": it sits in every consumer's log and replay for the whole
   retention window and cannot be recalled. Personal data a consumer does need stays and gets
   `x-pii` naming that consumer (✅ `deliveryAddress` for fulfilment). Card numbers never go on
   an event, marked or not; send a payment reference or the last four digits.

8. **Version additively; break only with a new version and a date.** Within a version only
   optional fields are added; consumers ignore unknown fields, so payload schemas stay open
   (no `additionalProperties: false`). A rename, type or unit change, removal, new required
   field or key change is breaking. ❌ Renaming `total` in place while a consumer reads it in
   production. ✅ Add `totalMinor` beside `total`, publish both, mark `total` deprecated with a
   sunset date; or publish `v2` on a new channel alongside `v1` for a dual-publish window. The
   sunset date comes from the input or is "to agree with <consumer>"; never invent one. New
   event types on a live topic whose consumers assume one type break those consumers: put
   them on a new channel or confirm the consumers skip unknown types.

9. **State retention, replay and dead-letter on every channel.** How long messages are kept
   (from the input or `[assumption]`), whether consumers can replay and from where, what goes
   to the DLQ after how many attempts, and who watches it. An unnamed DLQ owner goes under "To
   confirm", not a made-up team. Broker specifics in [`reference.md`](reference.md).

10. **Write the contract.** Start from
    [`templates/asyncapi-skeleton.json`](templates/asyncapi-skeleton.json); emit JSON (the
    check below reads JSON only). Channel facts go in `x-partition-key`, `x-ordering`,
    `x-delivery`, `x-retention`, `x-replay`, `x-dead-letter`; consumer duties in
    `info.description`. Then run the check and fix every FAIL:

    ```bash
    # Claude Code
    python3 "${CLAUDE_SKILL_DIR}/scripts/check_asyncapi.py" asyncapi.json
    # Other IDEs (from the skill folder)
    python3 scripts/check_asyncapi.py asyncapi.json
    ```

    It checks AsyncAPI 3.x structure, `$ref`s, past-tense names, the envelope in every message,
    one type per schema, unmarked personal data, closed schemas, deprecation dates, and each
    channel's key, ordering, delivery, retention, replay and DLQ notes. When it can't run, say
    the document is unchecked. Never claim a check that didn't run.

11. **Reply in this order:**
    1. **What the contract decides**, 3–6 lines, leading with every pushback from steps 3–9.
    2. **Decisions**: a table of decision, choice, why (shape in [`reference.md`](reference.md)).
    3. **What consumers must do**: numbered, at most 6: dedupe, ignore unknown fields, revision
       check, no cross-key order, DLQ duty, the migration they owe and by when.
    4. **The AsyncAPI document**, saved as `asyncapi.json` when files can be written, inline
       otherwise; then one line on the check result.
    5. **To confirm**: each open item with who can answer it.

**Non-interactive runs** (subagent, CI, headless): a missing broker, retention, consumer
detail or sunset date becomes a tagged `[assumption]` or a "To confirm" line, and the contract
ships. No producer or no event at all emits `BLOCKED: need the producing service and what
happens in it that others react to`.

## Useful references in this skill

- [`reference.md`](reference.md) — envelope fields and CloudEvents mapping, notification vs state, safe vs breaking changes, broker ordering/delivery/retention facts, consumer idempotency patterns, the `x-` extensions, decisions page shape
- [`templates/asyncapi-skeleton.json`](templates/asyncapi-skeleton.json) — valid AsyncAPI 3.0 starting point with envelope, two messages and every channel extension
- [`scripts/check_asyncapi.py`](scripts/check_asyncapi.py) — the structural and rule check (stdlib only; JSON input; exit 1 on failures)
- [`examples/order-service.md`](examples/order-service.md) — worked example: an order service brief with four traps, and the contract that answers it

## Quality bar

- **Every event name is a past-tense fact** in the producer's domain, one type per schema.
- **Every message has the full envelope, required**, with a stable event id for deduplication.
- **Every channel names its key, the order it gives and the order it doesn't.** No global order.
- **Each consumer's idempotency is stated**: dedupe on id, revision check, or a natural key.
- **Every field has a consumer**; personal data that stays is marked; nothing "just in case".
- **Breaking changes go through a new field or version** with a deprecation date that came from the input or is listed as open.
- **Retention, replay and dead-letter are stated per channel**, with the DLQ owner named or open.
- **The check result is reported only if it ran**, and the document has no FAIL.
- **Nothing invented**: no team names, dates, volumes or retention the input didn't give, except as `[assumption]`.

## When to use this skill

- ✅ Defining the events a service publishes, before consumers build against them
- ✅ Designing a Kafka topic, SNS/SQS, EventBridge, Pub/Sub or RabbitMQ message contract
- ✅ Changing a live event's schema without breaking its consumers
- ✅ A webhook contract partners will receive
- ✅ "Is ordering / exactly-once / dedup guaranteed if we do X?" about a message interface

## When NOT to use this skill

- ❌ A request/response HTTP API — `api-contract-draft`
- ❌ A table, dataset or analytics stream's schema, freshness and quality SLAs — `data-contract`
- ❌ Deciding whether the system should be event-driven at all, or its components — `design-doc`

## Anti-patterns to avoid

- ❌ **Commands dressed as events.** `CreateShipment` on a topic makes the order service own the warehouse's workflow.
- ❌ **Promising global order** or exactly-once because someone asked. Brokers give per-key order and at-least-once.
- ❌ **No event id**, so consumers dedupe on a hash of the payload and double-count the legitimate repeat.
- ❌ **Related events on separate topics** whose order then races: `OrderCancelled` overtakes `OrderPaid`.
- ❌ **The "just in case" field.** Personal data with no consumer, kept in every log for the retention window.
- ❌ **In-place breaking change** to a live event, "so there's one version to maintain". Fulfilment breaks at deploy.
- ❌ **`additionalProperties: false`** on payloads, which turns every additive change into a breaking one.
- ❌ **A DLQ nobody owns.** Messages land there and the business notices weeks later.

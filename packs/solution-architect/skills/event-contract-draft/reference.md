# event-contract-draft reference

House defaults for event contracts. Deviate when the input forces it and log the deviation in
the decisions page with its reason.

## Envelope

Every message carries these fields, all `required`, in the payload (structured mode, works on
every broker) or in broker headers (binary mode). Match the casing the producer already uses.

| Role | Default name | Type | CloudEvents 1.0 | Why it exists |
|---|---|---|---|---|
| Event id | `eventId` | string, `uuid` | `id` | Consumers deduplicate on it. Same value on every redelivery and replay; a new value per fact. |
| Event type | `eventType` | string, `const` per message | `type` | Routing and dispatch. One value per schema. |
| Event version | `eventVersion` | integer ≥ 1 | `dataschema` or a `type` suffix | Consumers pick the schema; breaking changes bump it. |
| Occurred at | `occurredAt` | string, `date-time`, UTC with `Z` | `time` | When the fact happened, not when it was published. |
| Producer | `producer` | string | `source` | The service that owns the fact. |
| Correlation id | `correlationId` | string | extension | Ties every event and request in one business flow together. |
| Causation id | `causationId` | string | extension | The `eventId` or request id that directly caused this event. Optional but expected. |

Domain fields sit under `data`. Each entity carries a **revision** (`orderRevision`: +1 on every
change to that entity) so a consumer can drop a stale or out-of-order event by comparing it with
the last revision it applied.

## Notification or event-carried state

| | Notification | Event-carried state |
|---|---|---|
| Carries | ids, the fact, a link or resource path | the fields the named consumers act on |
| Pick when | data is sensitive, changes fast, or consumers rarely need detail | consumers act without calling back, or the producer cannot take the call-back load |
| Cost | every consumer calls back; the call can see a newer state than the event | payload grows; every field is a field to version and to justify |

Event-carried state carries what named consumers need, not the whole aggregate.

## Safe and breaking changes

| Change | Within a version? |
|---|---|
| Add an optional field | ✅ safe — consumers ignore unknown fields |
| Add a new event type to a channel | ✅ safe if consumers skip types they don't handle (state it in the contract) |
| Add an enum value | ✅ only if the enum was declared open; ❌ otherwise |
| Rename a field | ❌ breaking — add the new field beside the old one, deprecate the old one |
| Change a field's type or unit (`42.50` → `4250`) | ❌ breaking — new field with a new name (`totalMinor`) |
| Change a field's meaning under the same name | ❌ breaking, and no validator catches it |
| Make an optional field required, or remove a field | ❌ breaking |
| Change the partition key | ❌ breaking — ordering guarantees change for every consumer |
| Change partition count (Kafka) | ❌ for ordering — keys remap to new partitions; plan a new topic or a drained cut-over |

Breaking-change routes, cheapest first:
1. **Additive shadow**: add the new field next to the old one, populate both, mark the old one
   `deprecated` with `x-sunset`, remove it in the next version.
2. **New version**: publish `vN+1` on a new channel (`orders.order-lifecycle.v2`) alongside `vN`
   for the dual-publish window, mark the `vN` messages `x-deprecated` with `x-sunset` and
   `x-replaced-by`. The window ends on a date the consumers agree to, not one the producer picks
   alone.

## Broker facts that change the contract

| Broker | Ordering | Delivery | Dedup help | Retention / replay | Dead letter |
|---|---|---|---|---|---|
| Kafka | per partition; key → partition by hash | at-least-once to consumers; idempotent producer and transactions stop producer duplicates inside Kafka only | none on the consumer side | `retention.ms` per topic (7 days unless set); consumers reset offsets to replay; compacted topics keep the latest per key | none built in; the consumer writes to a DLQ topic |
| SQS standard | best effort, none promised | at-least-once | none | 1 minute to 14 days (4 days default); no replay after delete | redrive policy, `maxReceiveCount` |
| SQS/SNS FIFO | per `MessageGroupId` | exactly-once processing within a 5-minute dedup interval | `MessageDeduplicationId` | as SQS | redrive policy |
| EventBridge | none | at-least-once; retries up to 24 hours by default | none | archive and replay must be switched on | per-target SQS DLQ |
| Google Pub/Sub | per ordering key, only when the subscription enables it | at-least-once; exactly-once delivery is an opt-in per subscription | `messageId` | seek to a time or snapshot inside the retention window | dead-letter topic, max delivery attempts |
| RabbitMQ | per queue, single consumer, until a redelivery | at-least-once with manual acks | none | gone once acked (streams excepted) | dead-letter exchange |
| Webhooks | none | at-least-once with retries | event id in the body | the producer's retry window and an event-list endpoint for catch-up | the producer's failed-delivery log |

Webhooks also need: an HMAC signature header over the raw body, a timestamp in the signed
content with a skew window to reject replays, the retry schedule with its cap, and "respond 2xx
fast, process asynchronously".

## Consumer idempotency patterns

- **Dedup table**: record `eventId` in the same transaction as the effect; skip if present. Keep
  ids at least as long as the retention window, or a replay re-applies everything.
- **Revision check**: upsert keyed on the entity id, applied only when `revision` is higher than
  the stored one. Handles duplicates and out-of-order arrival in one rule.
- **Natural key on the effect**: award points keyed on `(orderId, reason)`, so a second award
  for the same order is a no-op.
- **Side effects outside the database** (emails, partner calls): dedup record first, effect
  second, and accept that a crash between them means one retry of the effect.

## Extensions the checker reads

| Where | Key | Content |
|---|---|---|
| channel | `x-partition-key` | the field the broker keys on |
| channel | `x-ordering` | what order the key gives, and that there is no order across keys |
| channel | `x-delivery` | `at-least-once` plus where duplicates come from |
| channel | `x-retention` | how long messages are kept |
| channel | `x-replay` | whether and how a consumer re-reads |
| channel | `x-dead-letter` | what goes to the DLQ, after how many attempts, and who watches it |
| message | `x-event-style` | `notification` or `event-carried-state` |
| message | `x-deprecated`, `x-sunset`, `x-replaced-by` | deprecation state, end date, replacement message |
| property | `x-pii` | the consumer that needs this personal data |

## Decisions page

```markdown
## Decisions
| # | Decision | Choice | Why |
|---|---|---|---|
| 1 | Event names | OrderPlaced, OrderPaid, OrderCancelled | Facts in the order domain; the warehouse decides what to do with them |
| 2 | Channel and key | one channel per entity lifecycle, keyed by orderId | Events whose relative order matters share a key |
| … | | | |

## What consumers must do
1. Deduplicate on eventId …

## To confirm
- … (who can answer)
```

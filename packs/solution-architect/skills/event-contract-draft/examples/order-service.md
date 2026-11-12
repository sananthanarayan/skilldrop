# Worked example: order service events with four traps

## Input given to the skill

> We're moving fulfilment, loyalty and analytics off polling our order API and onto Kafka
> events. Our brief is in order-events-brief.md. Can you draft the event contract so the three
> teams can start building?

The brief (in [`../evals/files/1/order-events-brief.md`](../evals/files/1/order-events-brief.md))
asks for a `CreateShipment` event, an analytics feed "in one single global order", a
`customerEmail` on every event "just in case", and an in-place rename of `total` to an integer
`totalAmount` on the live `OrderPlaced`, which fulfilment consumes in production. Retention is
7 days; nobody owns failed messages yet.

## Output

**What the contract decides**

- `CreateShipment` becomes **`OrderPaid`**. The order service publishes the fact; the warehouse
  decides to pick when it sees it. A command on a shared topic would make the order service own
  the warehouse's workflow.
- **No single global order across all orders.** Kafka orders messages only within a partition;
  one partition for everything means one consumer at a time, and retries and dead-letter
  redrives reorder it anyway. Instead, every event for one order arrives in order (the topic is
  keyed by order id), and each event carries `occurredAt` and `orderRevision` so analytics can
  sort across orders when it reads.
- **`customerEmail` is dropped.** None of the three consumers uses it, and on Kafka it would
  sit in every consumer's copy for the whole retention window. The delivery address stays, on
  `OrderPaid` only, marked as personal data that fulfilment needs.
- **`total` is not changed in place.** Fulfilment reads `OrderPlaced` in production and would
  break on deploy. The new events go on a new topic, `orders.order-lifecycle.v1`: `OrderPlaced`
  version 2 (with `totalAmount` in pence), `OrderPaid` and `OrderCancelled`. The existing
  `orders` topic keeps publishing today's `OrderPlaced` unchanged until a date agreed with
  fulfilment.

**Decisions**

| # | Decision | Choice | Why |
|---|---|---|---|
| 1 | Event names | `OrderPlaced`, `OrderPaid`, `OrderCancelled` | Facts in the order domain; replaces `CreateShipment` |
| 2 | Topic and key | one topic, `orders.order-lifecycle.v1`, keyed by `orderId` | Paid and cancelled for one order must not race; one key means one partition, in order |
| 3 | Ordering | per order only; no order across orders, no global order | Kafka's guarantee is per partition |
| 4 | Producer publishing | each order's events published in commit order, from an outbox written in the same transaction | Without it the per-order promise in 2 is false |
| 5 | Payload style | `OrderPlaced` and `OrderPaid` carry the order; `OrderCancelled` carries ids and who cancelled | Fulfilment picks and loyalty awards from `OrderPaid` alone; cancelling needs only the id |
| 6 | Envelope | `eventId`, `eventType`, `eventVersion`, `occurredAt` (UTC, RFC 3339), `producer`, `correlationId`, `causationId` | Dedupe, routing, tracing; today's `placedAt` has no time zone |
| 7 | Money | `totalAmount` as integer pence plus `currency` | Today's `42.50` is a decimal float |
| 8 | Personal data | `customerEmail` dropped; `deliveryAddress` on `OrderPaid` only, marked | No consumer for the email; the address only once there is something to ship |
| 9 | The `total` change | `OrderPlaced` v2 on the new topic; v1 on `orders` unchanged until sunset | A rename plus a type change is breaking; both publish during the window |
| 10 | Delivery | at-least-once | Kafka redelivers on producer retries, rebalances and replays |
| 11 | Retention and replay | 7 days; consumer groups can reset offsets within it | Platform default from the brief |
| 12 | Dead letter | each consumer group parks a message after 5 failed attempts [assumption] on its own DLQ | Owner open; see below |

**What consumers must do**

1. Deduplicate on `eventId`. Fulfilment: a second `OrderPaid` for one order never starts a
   second pick. Loyalty: award points keyed on the order id, so a repeat is a no-op.
2. Apply an event only if its `orderRevision` is higher than the last one applied for that
   order; drop it otherwise.
3. Ignore fields and event types you don't recognise.
4. Never rely on order across orders. Analytics sorts by `occurredAt`, then `orderRevision`.
5. Park a message that fails 5 times on your DLQ, and watch it.
6. Fulfilment: move from `orders` to `orders.order-lifecycle.v1` before the agreed date.

**The AsyncAPI document** is saved as `asyncapi.json`
(here: [`order-service.asyncapi.json`](order-service.asyncapi.json)). It passes a structural
check: references resolve, every new message has the full envelope and a past-tense name, and
each topic states its key, ordering, delivery, retention, replay and dead-letter handling. The
only warnings are on the old `OrderPlaced` v1, documented as it runs today.

**To confirm**

- The date the old `OrderPlaced` stops on `orders`: order service team with fulfilment.
- Who watches each dead-letter queue: order service team with each consumer team.
- How the `orders` topic is keyed today: order service team.
- Whether analytics needs more than 7 days of history to replay; if so, longer retention or an
  archive: analytics with the platform team.
- Whether loyalty awards points on `OrderPaid` (assumed) or `OrderPlaced`: loyalty.
- Whether fulfilment reads `customerEmail` from today's event; if not, it can come off v1 now.

## Checker output on the example

```text
AsyncAPI check: examples/order-service.asyncapi.json
  2 channels, 4 messages, 2 operations
WARN  (deprecated) message OrderPlacedV1: envelope fields missing from headers and payload: event id (eventId), event type (eventType), event version (eventVersion), occurred-at (occurredAt), producer (producer), correlation id (correlationId)
WARN  message OrderPlacedV1: no causation id (causationId); consumers cannot tell which event caused this one
WARN  message OrderPlacedV1: x-sunset is 'to agree with fulfilment', not a date; agree the date and list it as open until then
PII (marked): message OrderPaid.payload.data.deliveryAddress
PII (marked): message OrderPlacedV1.payload.customerEmail
PII (marked): message OrderPlacedV1.payload.deliveryAddress
Result: 0 failures, 3 warnings
```

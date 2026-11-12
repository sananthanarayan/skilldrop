# Worked example: why do order events go through Kafka?

A made-up repository, in [`inputs/order-events/`](inputs/order-events/), with three ADRs:
- **ADR-0004** chose Kafka for order events in 2025.
- **ADR-0006** has receipts sent when the notifications service reads an OrderPlaced event, and
  cites ADR-0004.
- **ADR-0009** moved order events to SQS in 2026, and says it supersedes ADR-0004. Nobody updated
  ADR-0004's Status line, and ADR-0009 names a bridge folder that has since been deleted.

## The request

> I'm changing `services/orders/publisher.py`. Why do we publish order events to Kafka, and is
> that still the plan?

## Script runs

```bash
python3 scripts/context_graph.py --root examples/inputs/order-events --why services/orders/publisher.py
python3 scripts/context_graph.py --root examples/inputs/order-events
```

The `--why` output:

```text
# Decisions governing services/orders/publisher.py

- **ADR-0009 Order events on SQS** (accepted, current, 2026-02-10), via `services/orders/`: docs/adr/0009-sqs-for-order-events.md
- **ADR-0004 Kafka for order events** (marked accepted, but superseded by ADR-0009, 2025-03-02), via `services/orders/`: docs/adr/0004-kafka-for-order-events.md
```

The full check, which exits 1 because it found problems:

```text
## Problems (2)

- ADR-0004 is still marked Accepted, but ADR-0009 supersedes it: mark it 'Superseded by ADR-0009'
- ADR-0009 is accepted but points at code that is gone: services/kafka-bridge

## Warnings (1)

- ADR-0006 is current but cites ADR-0004, which ADR-0009 supersedes: check it still holds
```

## The reply

It isn't the plan any more. ADR-0009 (accepted 2026-02-10) moved order events from Kafka to SQS
queues, one per consumer, published from `services/orders/`. Its reasons: "only two consumers
ever replayed, and the Kafka cluster is the team's largest on-call load". It replaces ADR-0004,
which chose Kafka in 2025. ADR-0004's own Status line still says Accepted, so anyone reading it on
its own gets the wrong answer.

Before you change the publisher:

1. **ADR-0004 needs its status fixed.** Change `## Status` to `Superseded by ADR-0009`, linked
   to `0009-sqs-for-order-events.md`.
2. **ADR-0009 names `services/kafka-bridge/`, which no longer exists.** If billing has moved, add a
   line saying the bridge was removed. If it hasn't, find where the bridge went.
3. **ADR-0006 (receipts) still cites ADR-0004.** It has the notifications service read OrderPlaced
   events, which now come from an SQS queue. Check that the receipts consumer has its queue before
   you change what the publisher sends.

What the records don't say: when billing moved off Kafka, and whether replay for a new consumer
(now a backfill from the orders table, per ADR-0009) has been tested.

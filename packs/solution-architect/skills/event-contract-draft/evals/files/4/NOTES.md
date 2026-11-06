# shipments topic - working notes (tracking-core team)

Producer: tracking-core. Kafka topic `shipments`, 12 partitions, key = `carrierId`
(so each carrier's events stay together). Retention: cluster default, 7 days.

## Consumers

- **notify-svc** - texts/emails the recipient on status changes. Last month a consumer
  group rebalance made it re-read a batch and ~3,000 recipients got the
  "out for delivery" SMS twice. Also: sometimes "delivered" arrives before
  "out_for_delivery" for the same parcel and customers get confused.
- **analytics** - copies everything into the data lake, keeps it forever.
  They want to be able to replay events from last year after they fixed a bug
  in their pipeline.
- **billing** - charges the merchant per delivered parcel and remits `codAmount`.
  When it hits a message it can't parse, it crashes, restarts, reads the same
  message, crashes again. Happened twice in September.

## Plans

- Peak season: bump `shipments` from 12 to 48 partitions in November.
- Q1: rename `status` -> `state` and send `weight` in grams instead of kg.
  Plan is to just bump the version to v2 on the same topic and tell consumers.

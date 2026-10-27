# 3. Store vehicle telemetry in Cassandra

Date: 2021-06-02

## Status

Superseded by [8. Store vehicle telemetry in TimescaleDB](0008-store-vehicle-telemetry-in-timescaledb.md)

## Context

Each truck reports GPS position every 5 seconds. At 1,200 trucks this is
about 20 million rows a day, too much write volume for `haulmark_core`.

## Decision

Vehicle telemetry is written to a 3-node Cassandra cluster by
`services/telemetry/`, partitioned by vehicle and day.

## Consequences

High write throughput. Ad-hoc queries (e.g. "all trucks within 5 km of the
depot yesterday") are hard to express.

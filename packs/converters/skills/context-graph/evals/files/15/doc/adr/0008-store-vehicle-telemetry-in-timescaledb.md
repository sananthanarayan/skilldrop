# 8. Store vehicle telemetry in TimescaleDB

Date: 2023-04-11

## Status

Accepted

Supersedes [3. Store vehicle telemetry in Cassandra](0003-store-vehicle-telemetry-in-cassandra.md)

## Context

The Cassandra cluster from ADR 3 needs specialist operations knowledge
nobody on the team has, and geo queries over telemetry are now a product
requirement.

## Decision

Vehicle telemetry moves to TimescaleDB (a PostgreSQL extension) in a
separate database, `haulmark_telemetry`, written by `services/telemetry/`,
using a hypertable partitioned by time with PostGIS for geo queries.
Raw points are kept for 30 days and downsampled after that, as set out in
[10. Telemetry retention and downsampling](0010-telemetry-retention-and-downsampling.md).

## Consequences

One database technology to operate instead of two. Write throughput must be
watched as the fleet grows past 2,000 trucks.

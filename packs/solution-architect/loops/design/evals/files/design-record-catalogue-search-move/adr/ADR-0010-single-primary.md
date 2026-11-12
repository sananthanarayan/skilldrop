# ADR-0010: Single primary, no read replicas

## Status
Accepted

## Context
Read replicas would add replication lag to reason about in stock and checkout logic, and
our read load did not justify them.

## Decision
The catalogue database runs as a single primary with a standby for failover only. The
standby takes no traffic. All reads and writes, including checkout, go to the primary.

## Consequences and risks
No replication-lag bugs. Any new heavy read workload competes with checkout for the same
primary. Revisit if sustained primary CPU goes above 60%. Owner: platform team.

## Alternatives considered
Two read replicas for browse traffic; rejected as unnecessary at the time.

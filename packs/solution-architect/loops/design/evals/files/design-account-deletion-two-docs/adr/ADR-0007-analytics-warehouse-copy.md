# ADR-0007: Pseudonymised nightly copy to the analytics warehouse

Relates to: ADR-0002, ADR-0004
Status: Accepted

## Context
The data team needs run and challenge data for club-growth reporting without access to
production.

## Decision
A nightly job copies `runs`, `members` and challenge results to the analytics warehouse.
Names, emails and photos are dropped; `member_id` is replaced by `member_ref`, a keyed
hash of the member id. The data team owns the warehouse and its retention (currently
kept indefinitely). GPS traces are copied at full precision.

## Consequences
Reporting never touches production. Anyone holding the hash key can link a `member_ref`
back to a member, so warehouse rows remain personal data.

## Alternatives considered
Fully anonymised aggregates only; rejected because the data team needs per-member cohorts.

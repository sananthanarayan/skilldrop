---
id: ADR-0004
title: Store money as integer minor units
status: accepted
date: 2024-03-05
deciders: [m.okafor, j.lindqvist]
---

# Store money as integer minor units

## Context and Problem Statement

Floating point and arbitrary-precision decimals have both caused rounding bugs on previous
projects. How should monetary amounts be represented in the ledger?

## Considered Options

* `NUMERIC` columns with Python `Decimal`
* Integer minor units (cents, pence) with a separate ISO 4217 currency code

## Decision Outcome

Chosen option: "Integer minor units", because sums are exact and every currency we support
has a fixed minor-unit exponent.

Every amount column in `services/ledger/db/migrations/` is `BIGINT` named `*_minor`, paired
with a `currency CHAR(3)` column. `services/ledger/models/entry.py` exposes amounts as `int`.

### Consequences

* Good, because addition is exact and fast.
* Bad, because display code must apply the currency exponent.

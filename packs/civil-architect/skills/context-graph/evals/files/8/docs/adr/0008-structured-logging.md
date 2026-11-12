# ADR 0008: Structured JSON logging

* Status: Accepted
* Date: 2025-05-20

## Context

Log search across services is painful because each one logs free text differently.

## Decision

All ledger logging goes through `services/ledger/logging.py`, which emits one JSON object per
line with `ts`, `level`, `msg`, `trace_id` and `account_id` fields. The `trace_id` comes from
the tracing setup described in ADR-0011.

## Consequences

Plain `print` and ad-hoc `logging.basicConfig` calls are not allowed in service code.

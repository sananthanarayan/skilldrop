# ADR-0009: Store money as integer minor units

- Status: Accepted
- Date: 2024-06-03
- Deciders: Wen Haddad

## Context

Float rounding produced one-cent mismatches between invoice totals and line-item sums.

## Decision

Amounts are stored and computed as integers in the currency's minor unit (cents for USD/EUR).
Rounding rules for currencies with three minor digits follow ADR-0005.
Implemented in `src/ledgerline/money.py`.

## Consequences

All API payloads carry `amount_minor` plus `currency`.

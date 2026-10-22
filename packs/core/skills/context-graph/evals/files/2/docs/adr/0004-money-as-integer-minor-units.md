---
status: accepted
date: 2024-01-15
deciders: payments guild
---

# Money as integer minor units

## Context and Problem Statement

A float rounding error put a basket total out by 1p, and the refund did not match the charge.

## Decision Outcome

Chosen option: "integer minor units". Every amount in `libs/money/` is stored and computed as an
integer count of minor units (pence, cents). "No floats and no Decimal anywhere in money code:
one representation, exact by construction."

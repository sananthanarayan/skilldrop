---
status: accepted
date: 2025-02-27
deciders: marketplace team
---

# FX amounts with four decimal places

## Context and Problem Statement

Marketplace sellers are paid in their own currency. Converting a price in whole minor units and
then converting back loses sub-penny amounts, and seller statements drift.

## Decision Outcome

This builds on ADR-0004. Amounts in `libs/money/` are held as `Decimal` with four decimal places,
"so that a conversion and its reverse return the original amount", and are rounded to minor units
only when charged or paid out.

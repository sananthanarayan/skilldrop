# ADR 0004: Late-fee calculation rules

Status: Accepted
Date: 2014-03-11
Deciders: Billing operations, Finance

## Context

The 2011 tariff sets late fees as a percentage of the overdue balance. Regulator guidance
for priority (vulnerable) customers means priority customers must have a lower rate and a cap.

## Decision

- No fee within a 14-day grace period.
- Standard customers: 1.5% of balance. Priority customers: 1.0% of balance, capped at £25.00.
- Fees are rounded to the nearest penny, halves rounded up.
- A minimum fee of £5.00 applies whenever a fee is charged.
- Accounts more than 90 days overdue pay double (the second-stage arrears fee). The cap
  still applies to priority customers after doubling.
- Unknown tier codes are treated as standard.

## Consequences

The rules live in `legacy/feecalc.py`. Any change to them needs Finance approval
(currently: the Revenue Assurance Manager).

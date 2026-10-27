# PRD: Checkout without an account

**Status:** in review · **Owner:** Product, checkout · **Date:** 2026-09-15
**Binding constraint:** fixed deadline (Black Friday code freeze, 6 Nov) `[reported by head of e-commerce]`

## Problem

Shoppers who reach checkout without an account must create one before they can pay. In August,
38% of sessions that reached the sign-up step ended there `[data: funnel report, Aug 2026]`.

## Users

**Primary:** first-time shoppers arriving from paid social on mobile — job-to-be-done: buy the
item they clicked on in one sitting.
**Secondary (explicitly deprioritized):** returning shoppers who already have an account.

## Goals

| # | Goal | We'll know it worked when |
|---|---|---|
| G1 | More first-time shoppers complete checkout | Sign-up-step drop-off falls from 38% to under 20% within 4 weeks of launch |
| G2 | Guest orders can be supported like account orders | Support can find a guest order from the email address alone |

## Requirements

| ID | Requirement (testable, solution-free) | MoSCoW | Maps to goal |
|---|---|---|---|
| R1 | A shopper can pay without creating an account, giving only an email address and delivery details | M | G1 |
| R2 | A guest shopper receives an order confirmation email with a link to track the order | M | G1 |
| R3 | After paying, a guest shopper is offered an account, pre-filled from the order, which they can decline | S | G1 |
| R4 | Support staff can look up a guest order by email address in the admin tool | M | G2 |
| R5 | Guest orders are flagged in fraud screening with the same score shown for account orders | M | G2 |
| R6 | A guest shopper can return an item by entering their order number and email | S | G2 |
| R7 | Saved cards for guest shoppers | W | G1 |

**Won't have (this version):**
- Saved cards for guests (R7) — needs an account to attach the card to; revisit after launch.

## Non-goals (minimum 3 — the scope-creep firewall)

- **Social login** — a different fix for the same drop-off; measure guest checkout first.
- **Merging guest orders into an account created later** — useful, but not needed to hit G1.
- **Guest checkout in the mobile app** — the app already keeps shoppers signed in.

## Open questions

| Question | Owner | Needed by |
|---|---|---|
| Does the PSP need an account ID for 3-D Secure on guest payments? | Payments lead | 2026-09-25 |

## Assumptions log

- [assumption] Guest shoppers' emails are kept for 2 years, the same as account orders — challenge at privacy review.

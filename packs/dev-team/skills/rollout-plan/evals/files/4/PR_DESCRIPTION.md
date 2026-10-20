# PR #4182: Pay-in-4 at checkout (Lumen Pay integration)

Adds "Pay in 4 interest-free payments" as a payment option on web checkout, behind
flag `checkout.pay_in_4` (our in-house flag service, supports % of user_id and
allow-lists).

## What it does
- New payment tile on /checkout/payment when cart total is between $50 and $1,000.
- On submit we call Lumen Pay `POST /v2/agreements` which creates an installment
  agreement and runs a soft credit check. Lumen charges the first installment immediately.
- Order is written with `payment_method = 'installment'` (new enum value) and a
  `lumen_agreement_id`. Refunds for these orders go through Lumen's refund API, not Stripe.
- Lumen sends the customer its own welcome + schedule email on agreement creation.
- Order confirmation email template has a new installment-schedule block.

## Not in this PR
- iOS/Android apps (they hide the tile; app support lands in 6.14).
- Admin tool support for installment refunds is in #4190 (not merged yet; CS can
  refund via the Lumen dashboard in the meantime).

## Notes
- Lumen asked us to stay under 2,000 new agreements/day for the first 7 days while they
  scale their risk model for us.
- Migration 0412 adds the enum value; already applied to prod.

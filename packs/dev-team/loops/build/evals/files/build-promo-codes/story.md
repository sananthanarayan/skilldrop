# STORY-142: Percentage promo codes at checkout

**As a** shopper
**I want** to enter a promo code at checkout
**So that** I get the advertised percentage off my order

Epic: SPRING-PROMOS. Estimate: 3. Agreed at refinement on 29 Oct 2026 (Lena, Marco, Yusuf).

## Context

Marketing will hand engineering a list of codes for the spring campaign. For now the
codes are passed in to `cart_total` as a catalogue (a dict of code -> PromoCode); storing
them is a separate story (STORY-150). Existing callers of `cart_total` (the basket page
and the order-confirmation email) must keep working unchanged.

A `PromoCode` has: `code` (str), `percent_off` (Decimal, e.g. `Decimal("10")` for 10%),
`max_discount` (Decimal or None), `expires_on` (date or None, last valid day inclusive).

## Acceptance criteria

```gherkin
Scenario: AC1 percentage discount
  Given the catalogue has SAVE10 at 10% off with no cap and no expiry
  And the cart subtotal is 50.00
  When the shopper applies "SAVE10" with no tax
  Then the total is 45.00

Scenario: AC2 code matching is forgiving
  Given the catalogue has SAVE10
  When the shopper applies " save10 "
  Then SAVE10 is applied

Scenario: AC3 discount cap
  Given the catalogue has BIG20 at 20% off with a max discount of 50.00
  And the cart subtotal is 400.00
  When the shopper applies "BIG20" with no tax
  Then the total is 350.00

Scenario: AC4 expired code
  Given SPRING15 expires on 2026-03-31
  When the shopper applies "SPRING15" on 2026-04-01
  Then a PromoError is raised whose reason is "expired"
  And SPRING15 still applies on 2026-03-31

Scenario: AC5 unknown code
  When the shopper applies "NOPE"
  Then a PromoError is raised whose reason is "unknown"

Scenario: AC6 tax applies after the discount, rounding once
  Given the catalogue has SAVE10
  And the cart subtotal is 10.05
  When the shopper applies "SAVE10" with a tax rate of 0.2
  Then the total is 10.85
  # not 10.86: the discounted subtotal (9.045) is not rounded before tax
```

## Out of scope

- More than one code per order.
- Fixed-amount codes (e.g. 5.00 off).
- Storing codes, or usage limits per code (STORY-150).

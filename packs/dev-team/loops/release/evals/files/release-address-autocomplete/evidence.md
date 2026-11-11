# What we have

## Tests
- Unit and end-to-end checkout tests pass on main (run 2026-11-09).
- Load test on staging: address-lookup held p95 310 ms at 3x normal peak
  traffic. Normal peak is about 90 checkouts per minute.

## Monitoring
- Dashboard "Checkout funnel" shows checkout conversion rate and
  checkout error rate, by flag state.
- address-lookup has a latency dashboard. There is NO alert on its error
  rate or on the fallback rate yet.

## Baselines (last 4 weeks)
- Checkout conversion: 61.8%
- Checkout error rate: 0.3%

## People
- Release owner: Joaquin Thorne (checkout team lead) makes the go/no-go call.
- On-call: checkout team rota covers 08:00-20:00 weekdays only.

## Cost
- The outside address provider charges per lookup; the contract covers up to
  400,000 lookups a month.

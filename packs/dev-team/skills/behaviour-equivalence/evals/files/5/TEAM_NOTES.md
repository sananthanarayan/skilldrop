# orders-api: Express -> Fastify migration, parity notes

Replay setup: the 8 requests in `recordings/` were sent to the old Express service twice
(old_run1, old_run2) and once to the new Fastify service (new_run), against the same seeded
staging database (reset between runs).

Result after applying `normalisation.yaml`: 7 of 8 exchanges identical.

The one remaining diff is seq 4 (`GET /orders/ord_bad!!`, 400 vs 500). That's a garbage id
no real client sends, so we're treating it as noise.

Conclusion: **equivalent**. Proposing cutover Tuesday 27 Oct.

Context for reviewers:
- Consumers: the web checkout and the Android app. The Android app switches on `error.code`
  to choose which message to show the user.
- The web checkout reads `total` and passes it straight to the payment widget as a string.

-- Dana Okafor, platform-orders

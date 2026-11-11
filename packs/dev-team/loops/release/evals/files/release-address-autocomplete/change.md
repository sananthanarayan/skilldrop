# Merged: address autocomplete at checkout (PR #881, merged 2026-11-09)

Shoppers on the Pelham Home web shop now get address suggestions as they type
their postcode at checkout, instead of typing the full address.

- Behind the feature flag `checkout_address_autocomplete` (default off).
- Calls the internal `address-lookup` service, which calls an outside
  address provider. If the lookup fails or takes more than 800 ms, the form
  falls back to the old manual fields.
- No database schema changes. No change to how orders are stored.
- Web only; the mobile apps are unchanged.

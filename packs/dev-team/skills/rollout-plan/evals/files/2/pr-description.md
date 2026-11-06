# PR #874 — One-tap reorder

**Author:** Basketful app team · **Flag:** `one_tap_reorder` · **Ships in:** iOS/Android 5.8 and web

## What it does

Adds a "Reorder" button to past orders on the home screen. One tap rebuilds the basket from the
previous order, charges the saved card and places the order.

## How it works

- New endpoint `POST /v2/orders/reorder`. The web client and app 5.8+ call it when the flag is on.
- The flag is evaluated **in the client**. The app fetches flag config at launch and caches it
  for 24 hours. Web fetches it on page load.
- On success the order is sent to the fulfilling store partner (FreshPick) through the existing
  order webhook, and the user gets a push notification: "Your reorder is on its way".
- Reorders are tagged `source=one_tap` in the `orders` table (existing `source` column; new value).
  The order-history screen in app versions before 5.8 shows unknown `source` values as "Other".
- The basket rebuild substitutes out-of-stock items with the store's default substitute.

## Rollout

Product would like 1% on Monday, 100% by Thursday.

## Notes

- The home screen is also running the `home_carousel_v3` experiment (50% of users, until 2 Nov).
- Business accounts (office grocery orders) are on a contract with a 2-week notice for UI changes.

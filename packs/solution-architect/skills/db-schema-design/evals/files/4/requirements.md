# Greenlane Rewards rebuild — my notes (Tomasz, platform team)

Greenlane Markets: 220 stores, about 1.8M loyalty members.

## What we have today
- `members` table with a `points_balance` column. The tills update it directly.
- `points_txn` log table, bolted on in 2023. Nothing enforces that it agrees with the balance.
- `basket_value` is a FLOAT. Timestamps are whatever the till's clock said, no zone.

## What the new one has to do
1. Till scans a loyalty card -> look up the member by card number and show the balance. Needs to be fast (under 100 ms), it happens on every loyalty basket.
2. Till earns points on a basket, or redeems points against a basket.
3. App: member sees their points history, newest first, 20 rows at a time.
4. Points expire 24 months after they were earned. A nightly job expires them. Oldest points get spent first.
5. Customer services can make a manual adjustment. We need the reason and who did it.
6. Finance: month-end liability = unexpired points outstanding, split by the store where they were earned.
7. Marketing (Dalia) wants points by household.

## Numbers
- About 400k loyalty transactions a day, so roughly 50 million a year.
- 1 point per whole pound spent. A point is worth 0.5p when redeemed.

## Known problems
- Tills retry on timeout because store networks are flaky. We have definitely had the same receipt sent twice.
- Balances drift. Finance are not happy, see their email.

## Decided
- Postgres 16 (managed). Not changing.

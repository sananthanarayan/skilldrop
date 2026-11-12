# PR 41: Add loan renewals (LIB-212)

**Author:** Bram Oyelaran-Pike
**Branch:** `bram/lib-212-renewals` into `main`
**CI:** passing (see ci-run.txt)

Adds `Desk.renew()` so members can renew a loan from the self-service kiosk. The kiosk team are waiting on this to ship their renew button.

## Ticket LIB-212: acceptance criteria

1. A member can renew a loan at most twice.
2. Each renewal moves the due date 14 days on from the current due date, not from today.
3. A renewal is refused if another member has a hold on the item. The borrower's own hold does not count.
4. Only the member who has the item can renew it.

## Testing

Added `RenewTests` covering each criterion. All green locally and in CI.

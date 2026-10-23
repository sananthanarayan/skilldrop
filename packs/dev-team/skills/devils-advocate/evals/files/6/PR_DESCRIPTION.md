## Synchronous reward redemption (#412)

Members currently wait for the nightly batch to find out whether a redemption went through.
This moves redemption onto a synchronous endpoint so they get an answer straight away.

- `redeem()` backs `POST /members/{member_id}/redemptions`
- `list_redemptions()` backs the history screen, with a `sort` option
- The balance row is locked with `SELECT ... FOR UPDATE`, so a double tap on "Redeem" can't spend the same points twice
- A failed shipment returns 502 and asks the member to try again; this closes #398 and is covered by `test_fulfillment_failure_returns_502`
- Per-order cap of 10 so nobody can clear out a reward's stock in one request

### Test run

```
$ pytest tests/test_redeem.py -q
......                                                                   [100%]
6 passed in 0.41s
```

Ready for review. I'd like to get this into Thursday's release.

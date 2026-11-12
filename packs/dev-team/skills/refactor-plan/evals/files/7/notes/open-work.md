# web: open work (updated Mon 19 Oct 2026)

## Release
- **v4.8 ships Tue 3 Nov.** Code freeze Fri 30 Oct, 17:00. After freeze only
  release-blocker fixes go to main.

## Open PRs
- **#231 Gift cards at checkout** (dana) - adds gift card entry + balance
  deduction to `CheckoutPanel.tsx` (new state, changes the totals block and
  `submit()`). In v4.8 scope. Review this week, expected merge by Wed 28 Oct.
- **#236 Address autocomplete** (lee) - swaps the address inputs in
  `CheckoutPanel.tsx` for a lookup widget. NOT in v4.8; parked until after release.
- **#238 Bump vite 5.4 -> 5.5** (bot) - unrelated.

## Tickets
- **WEB-512** Checkout total in header cart sometimes 1p different from the
  checkout page. Reported twice by support. Unassigned.
- **WEB-530** Second payment provider (pay-by-bank) in Q1 2027. Needs the
  payment step to stop assuming card fields.

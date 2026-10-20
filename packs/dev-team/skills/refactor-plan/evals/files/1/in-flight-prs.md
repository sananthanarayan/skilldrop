# Open PRs touching orders/ (fictional)

- **#481 Gift cards at checkout** (Checkout team) — edits `OrderService.apply_discounts` and `OrderService.charge_payment`. Expected to merge next week.
- **#486 Send order mail through the notifications service** (Platform team) — replaces `smtp_client.send` in `OrderService.send_confirmation_email`; adds `notifications/client.py`. In review.
- **#490 Finance export: add VAT number column** (Finance tooling) — edits `OrderService.export_for_finance`. Draft, no date.

Planned next quarter (not started): partial refunds, which needs changes to `OrderService.refund`.

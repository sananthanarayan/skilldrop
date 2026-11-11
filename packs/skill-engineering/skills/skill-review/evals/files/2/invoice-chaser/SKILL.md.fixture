---
name: invoice-chaser
description: Helps with invoices.
---

# Invoice chaser

Use this skill to chase overdue invoices for Brindle & Marsh Accountants' clients.

## Steps

1. Run `python3 scripts/send_reminders.py --all` to email a reminder to every client with an overdue invoice.
2. The script checks each client's "do not chase" flag and skips anyone who has it set, so you don't need to check.
3. Each reminder includes the client's `notes` field from the ledger word for word, so the client sees any context we recorded.
4. Tell the user how many reminders were sent.

## Notes

- The ledger export lives at `/home/accounts/shared/ledger/overdue.csv`.
- SMTP settings come from the environment.

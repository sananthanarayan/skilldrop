# INC-0847 reconciliation

Finance Ops (Aoife Brennan), Fri 25 Sep 2026. Brindle Energy, internal.

Matched bank file DD-20260922-B against DD-20260922-A.

- Rows in file B: 3,401
- Of which legitimate retries of Monday's failed debits: 440
- Duplicate debits: 2,961
- Customers affected: 2,917 (44 customers have two supply accounts and were debited twice on both)
- Total taken in error: GBP 184,306.20

## Refunds

- 23 Sep, refund file 1: 2,804 credits
- 24 Sep, refund file 2: 131 credits
- Could not be sent, or rejected by the bank: 26 (account closed or switched since the debit).
  Passed to Customer Ops to contact by letter. No date for these yet. Value outstanding: GBP 1,702.48

## Bank charges and overdrafts

We have no way to see whether a customer went overdrawn. Support has tagged 43 contacts
where the customer says they were charged a fee or went overdrawn. No decision yet on
reimbursing fees.

## Support

Contacts tagged INC-0847 up to 25 Sep: 487

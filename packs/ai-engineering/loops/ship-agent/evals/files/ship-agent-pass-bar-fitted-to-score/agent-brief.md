# Ticket summary agent: brief

**Team:** Customer Support, Pebblestone Broadband (fictional)
**Launch owner:** Tomasz Brennan, Head of Support

## What it does

Customers raise tickets through the public web form at help.pebblestone.example. The text is free-form and anyone can submit it.

For each new ticket the agent:

1. Reads the ticket text.
2. Looks up the customer's account: name, address, broadband plan, open faults and the last four digits of the payment card.
3. Searches the knowledge base and picks up to three articles.
4. Writes an internal note on the ticket: a two-line summary and the suggested articles, top one first.

Only support staff see the note. The agent does not reply to customers and has no other way to send anything out.

## Tools

- Helpdesk: read ticket, write internal note
- Accounts: read customer account
- Knowledge base: search, read article

## What support leads have told us

Suggestions are only worth the screen space if the top article is the right one on at least 9 tickets in 10. Below that, staff learn to ignore the panel.

## Volume

About 9,000 tickets a month.

## Status

Prompt and tools are built. We ran evals last week (see `eval-run-1.md`). No threat model or spend plan written yet.

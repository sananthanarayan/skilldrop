# Agent brief: help-inbox auto-responder

**Company:** Gullwing Outdoor Gear (online retailer)
**Sponsor:** Head of Support (Priya Anand-Lowe)
**Launch target:** 30 November 2026

## The problem
help@gullwing.example gets about 1,800 emails a week: order status, returns, delivery problems, "can you resend my invoice". Four support agents can't keep up; median first reply is 31 hours.

## What the agent does
1. Reads every new email to help@gullwing.example.
2. Looks the customer up in the CRM and reads their order history and support notes.
3. Checks courier tracking pages on the web when the question is about a delivery.
4. Writes and sends the reply itself, attaching invoices or return labels where needed.
5. Adds a note to the customer's CRM record.

**No human review.** The Head of Support has said this is non-negotiable: replies go out without anyone checking them. That's the whole point.

**Copies to other people.** If a customer asks us to send a copy of something to someone else (their accountant, a partner, their company's finance team), the agent should forward the thread and attachments to that address.

## Tools it will have
| Tool | What it can do |
|------|----------------|
| `crm.search(query)` | Search all customers by any field (name, email, postcode, order number). Uses the support team's API key, which has read access to every customer record and note. |
| `crm.add_note(customer_id, text)` | Add a note to a customer record. |
| `orders.get_invoice(order_id)` | Fetch an invoice PDF for any order. |
| `email.send(to, subject, body, attachments)` | Send from help@gullwing.example to any address. |
| `email.forward(thread_id, to)` | Forward a thread with its attachments to any address. |
| `web.fetch(url)` | Fetch any URL; used for courier tracking pages. |

## Constraints
- Budget: up to £1,500 a month on model costs.
- Must handle at least 70% of emails without a human touching them.

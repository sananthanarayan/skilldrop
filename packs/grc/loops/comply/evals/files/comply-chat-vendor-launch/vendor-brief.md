# Vendor brief: Parlour Chat (live chat + chatbot for customer support)

Prepared by: Customer Operations, Brackenfield Outdoor Ltd
Date: 28 October 2026
Target go-live: 1 December 2026
Business owner (accountable for the risk): Mara Lindqvist-Obi, Head of Customer Operations
Security contact: Tom Ashdown, IT Security Lead
DPO: Hollis Granger (dpo@brackenfield.example)

## What we want to do

Replace the contact form on brackenfield.example with Parlour Chat, a hosted live-chat
and chatbot product from Parlour Software Inc. (parlour.example). Customers will chat with
the bot first; it hands over to one of our 40 support agents when it can't answer.

The bot will look up a customer's orders so it can answer "where is my order?" without an
agent. To do that, Parlour will call our order API (orders-api.brackenfield.example) with
the customer's email address and get back order number, items, delivery address and
delivery status.

## Data involved

- Customer name and email address (asked at chat start)
- Chat transcripts (free text; customers sometimes type phone numbers, addresses and,
  occasionally, card numbers despite the banner telling them not to)
- Order history returned by our order API: order number, items, delivery address, status
- Agent names and agent login details (our staff)
- Browser and device information and IP address (collected by the chat widget)

Roughly 18,000 chats a month based on current contact-form volume. Customers are UK and
EU consumers; no children's accounts (we don't sell to under-18s).

## Where the data goes

- Parlour hosts in AWS us-east-1 (United States). They offer an EU region but only on the
  Enterprise plan, which we are not buying.
- Parlour uses two subprocessors: a cloud host (AWS) and a language-model provider for the
  bot's answers (named in their subprocessor list as "LLM provider, US").
- Parlour's default transcript retention is 24 months. It can be set from 30 days to
  "forever" in the admin console.

## Contract and paperwork status

- Master services agreement: in legal review, not signed.
- Data processing agreement with EU Standard Contractual Clauses (module 2) and the UK
  addendum: Parlour's template received, not yet reviewed by our DPO.
- Parlour SOC 2 Type II report: received, covering 1 July 2024 to 30 June 2025.
- Transfer risk assessment for the US transfer: not started.

## Controls we plan to rely on

| # | Control | Status today | Who runs it |
|---|---------|--------------|-------------|
| C1 | Agent access to Parlour via our SSO (Okta) with MFA; no local Parlour passwords | Configured in Parlour test tenant; SSO screenshot from 21 Oct | IT Security |
| C2 | Quarterly access review of Parlour agent accounts | Not yet set up; we do quarterly reviews for Zendesk today (last one 30 Sep 2026, signed sheet on SharePoint) | Customer Ops team lead |
| C3 | Card-number redaction in transcripts (Parlour "PCI mask" feature) | Planned. Feature exists on Parlour's Business plan; we haven't enabled or tested it | Customer Ops |
| C4 | Transcript retention set to 90 days | Planned. Not yet configured | Customer Ops |
| C5 | Order API scoped token: read-only, orders endpoint only, rotated every 90 days | Token issued 22 Oct, scope confirmed in API gateway config (export attached to ticket SEC-2291) | Platform team |
| C6 | Vendor due diligence: SOC 2 report reviewed, security questionnaire completed | Questionnaire returned 15 Oct; SOC 2 report not yet reviewed by anyone | IT Security |
| C7 | Bot cannot see transcripts from other customers; each chat session isolated | Parlour says so in their questionnaire answer 4.7; we have not tested it | Parlour / IT Security |

## What we are worried about

1. A customer types a card number into chat and it sits in a US-hosted transcript for two
   years.
2. Someone gets the bot to read out another customer's order and delivery address by
   giving it that customer's email address.
3. The language-model provider uses our transcripts to train its models.
4. Ex-agents keep access after they leave.
5. Parlour has an outage on Black Friday weekend and customers can't reach us.

Mara needs to sign off the risk position before go-live. Please get us to that point.

# PRD-412 — Launch: scheduled exports for Team plan

**Type:** Launch  **Status:** In progress  **Reporter:** Hannah Ito (Product)  **Assignee:** Hannah Ito
**Labels:** team-plan, exports, launch-q4

## Description

Team plan customers can set up a recurring export (daily, weekly or monthly) of their project data as CSV, delivered by email link or to an SFTP server they own. Replaces the manual "Export all" button that customers currently run by hand.

Top customer asks (from the feedback board):
- "We export every Monday for our finance team. Please let us schedule it." — 41 upvotes
- "Need this to land on our SFTP so our BI tool can pick it up" — 17 upvotes
- "Weekly CSV by email would be enough for us" — 12 upvotes

What's in:
- Daily / weekly / monthly schedules, choose the time of day
- CSV format, same columns as today's manual export
- Delivery by emailed download link (link valid 7 days)
- Delivery to customer SFTP — see comments

Help-centre article: help.example.com/scheduled-exports (draft, not published)

## Comments

**Hannah Ito (Product)** — 20 Oct
Target launch Nov 12. Marketing will send the announcement email to Team plan admins on launch day.

**Oskar Brenner (Eng lead)** — 22 Oct
Nov 12 isn't realistic with SFTP in. Email delivery is done and in QA. SFTP destination still needs key management and the retry logic. If we cut SFTP from v1, earliest is Nov 26. With SFTP, I can't give a date yet.

**Hannah Ito (Product)** — 23 Oct
SFTP is the thing the bigger customers asked for, I don't want to launch without it. Let's discuss.

**Oskar Brenner (Eng lead)** — 23 Oct
Fine, but then the date moves. Need a decision from you.

**Hannah Ito (Product)** — 27 Oct
Pricing proposal: add-on at $15/month per workspace. Sent to finance.

**Gwen Adeyemi (Finance)** — 29 Oct
Not approved yet. We're also looking at including it in Team at no extra charge as a retention play. Will have an answer after the pricing committee on Nov 10.

**Hannah Ito (Product)** — 3 Nov
Marketing is asking for final copy for the announcement. Can someone draft it?

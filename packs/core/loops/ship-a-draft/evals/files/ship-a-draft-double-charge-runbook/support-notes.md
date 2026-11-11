# double charges - notes for the runbook (support team, Nov 2026)

from the call with Jonas + Priyanka, 6 Nov, plus bits pasted from slack

- happens when PayBrook times out and the customer hits pay again. we get 2 captures
- how to spot it: admin console https://admin.example.com/payments , search by order id. if there
  are two captures for the SAME amount within 10 minutes of each other it's a duplicate
- if the amounts differ it is NOT a duplicate - send it to the payments team queue, don't refund
- refund the LATER capture, not the first one. use the Refund button in the admin console, reason
  "duplicate"
- NEVER refund from the PayBrook dashboard directly - it breaks the ledger sync and finance has
  to fix it by hand (Jonas was very clear on this​)
- more than 5 duplicates in an hour = something's broken, page payments on-call in #payments-oncall
- what to tell the customer re timing:
  - Jonas: "3-5 working days"
  - Priyanka: "I think it's 5-10 since PayBrook changed something? not sure, will check"
  - (nobody checked yet)
- refunds over £500 need approval from someone - ask Fiona? or is it finance? TBD

pasted from the draft someone did last month in the AI tool, might be useful:

Sure! Here's a runbook draft for handling duplicate charges:​

1. Find the order in the admin​ console.
2. Check for two captures of the same amount.
3. Refund the later one with reason "duplicate".

Let me know if you'd like me to make any changes!

🤖 Generated with AssistBot

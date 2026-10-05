# INC-2291: summary

Opened 10 September 2026. Status at 30 September: open.

## What happened
On 9 September an engineer debugging failed refunds pasted about 600 lines of production logs into a personal account on a public chatbot.

## What was in the logs
- 2,300 customer email addresses
- The last four digits of card numbers
- No full card numbers, expiry dates or security codes

## Timeline
- 9 Sept: logs pasted.
- 10 Sept: the engineer reported it themselves to their team lead, who did not know where to send it. It reached Security that afternoon.
- 11 Sept: deletion request sent to the chatbot provider.
- 30 Sept: no confirmation of deletion received.

## Contributing factors
- The engineer had no CodePilot Enterprise seat and was on the waiting list.
- No written guidance on whether logs may be pasted into AI tools.
- No clear place to report it.

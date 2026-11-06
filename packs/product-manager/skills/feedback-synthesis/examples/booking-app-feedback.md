# Worked example — Corbel salon booking, September feedback

A fictional booking app for hair salons. Sixteen items from three sources; the owner of the
loudest ticket thread assumed the Instagram button was the priority because "everyone asks for
it". It shows a repeat filer, a request rewritten into a problem, a one-segment theme, and a
salon whose workaround hides it from the ticket count.

## Input

**The request:** *"Here's last month's feedback for Corbel: support tickets, CSAT comments and
three interview notes. What should we fix first? Product wants to build the Instagram booking
button next."*

**Support tickets** (salon ID, plan, country)

| ID | Salon | Plan | Country | Text |
|---|---|---|---|---|
| T-501 | S-12 | Team | UK | A client rescheduled through the text link and got put in a slot Marta already had. Two clients turned up at 10am. |
| T-502 | S-12 | Team | UK | Happened again today. Double booking from the reschedule link. |
| T-503 | S-12 | Team | UK | Third double booking this month. We had to give one client a free fringe trim to calm her down. |
| T-504 | S-31 | Team | UK | Reschedule link let a client into a slot that was already booked. |
| T-505 | S-07 | Solo | UK | Can you add a button on Instagram so people can book from there? |
| T-506 | S-44 | Solo | IE | The colours on the booking page don't match my brand. |
| T-507 | S-19 | Team | UK | How do I export my client list? |
| T-508 | S-52 | Solo | UK | Booking page font is hard to read on phones. |

**CSAT comments** (1–5)

| ID | Salon | Score | Comment |
|---|---|---|---|
| C-01 | S-31 | 2 | The double bookings are going to cost us clients. |
| C-02 | S-07 | 4 | Love the deposit feature, no-shows have nearly stopped. |
| C-03 | S-60 | 5 | Deposits changed my business. |
| C-04 | S-44 | 3 | Fine, but I'd like the booking page to look more like my salon. |
| C-05 | S-52 | 5 | Easy to use. |

**Interview notes** (quotation marks = the salon's words)

- **I-1, S-07, Solo, owner:** "Nearly all my new clients find me on Instagram, then I send them
  the link in a DM. Half of them never book."
- **I-2, S-12, Team, manager:** "I check the book every morning now because I don't trust the
  reschedule link."
- **I-3, S-73, Team, manager:** Gets many new clients from Instagram; has never tracked whether
  they book. "We turned the reschedule link off after a double booking in our first week."

## Coding sheet

[`inputs/booking-app-coded.csv`](inputs/booking-app-coded.csv): one row per item, salon ID as
`person_id`. T-503 is S1 because the salon gave away a service; I-2 is S2 (a daily manual check);
I-3's double booking is S3 because the salon has switched the link off. T-505 is coded to the
Instagram problem, not to a "button" theme. T-506 and T-508 are separate themes: brand colours
and legibility are different problems.

## Script output (abridged)

```
- Items: 16; distinct salons with an ID: 8
- Most items from one salon: S-12 4, S-07 3, S-31 2, S-44 2, S-52 2

| Theme                      | Salons | Mentions | Ranking severity | By severity | One segment only           |
|----------------------------|--------|----------|------------------|-------------|----------------------------|
| reschedule-double-book     | 3      | 7        | S1               | S1 2, S3 1  | plan=Team (4 of 8 overall) |
| instagram-new-clients      | 2      | 3        | S3               | S2 1, S3 1  | -                          |
| page-hard-to-read-on-phone | 1      | 1        | S3 (1 report)    | S3 1        | -                          |
| page-brand-mismatch        | 1      | 2        | S4 (1 report)    | S4 1        | -                          |
| +deposits                  | 2      | 2        | -                | -           | plan=Solo (4 of 8 overall) |

- WARNING: S-12 accounts for 56% of reschedule-double-book's mentions
## Items with no theme
T-507, C-05
```

## The reply

# What salons told us in September

**Fix the reschedule link before building the Instagram button.** The reschedule link is putting
clients into slots that are already taken: three salons, all on the Team plan, and one gave away
a service to calm a client down. The Instagram request comes from two salons, and the problem
behind it is new clients dropping off between a DM and a booking, which one owner puts at "half".
Counts below are salons, not messages.

## Themes, ranked

| # | Problem | Who | Severity | Sources |
|---|---|---|---|---|
| 1 | Rescheduling by text link books clients into slots that are already taken | 3 salons (7 messages, 4 from one salon); Team plan only | **Blocker:** two clients arrive for one slot; one salon gave a free service | tickets, CSAT, interviews |
| 2 | New clients found on Instagram are sent a link by DM and many never book | 2 salons (one Solo, one Team) | **Minor to major:** one owner says half never book; the other hasn't measured it | ticket, interviews |
| 3 | The booking page is hard to read on a phone | 1 salon | **Minor**, one report: confirm first | ticket |
| 4 | The booking page doesn't match the salon's branding | 1 salon (2 messages) | **Cosmetic**, one report | ticket, CSAT |

## Evidence

### 1. Rescheduling books clients into taken slots
- **Who:** S-12 (three tickets and an interview) and S-31 (a ticket and a CSAT score of 2), plus
  S-73, which switched the link off after one double booking. All three are Team salons; no
  Solo salon reported it.
- **In their words:** "Two clients turned up at 10am." (T-501); "We had to give one client a free
  fringe trim to calm her down." (T-503); "The double bookings are going to cost us clients."
  (C-01); "I don't trust the reschedule link." (I-2)
- **What would change this:** a Solo salon using the link without trouble would point at
  multi-staff calendars; no Solo salon in this set says whether it uses the link.

### 2. Instagram new clients drop off before booking
- **Who:** S-07 (Solo) and S-73 (Team).
- **In their words:** "Nearly all my new clients find me on Instagram, then I send them the link
  in a DM. Half of them never book." (I-1)
- **What they asked for:** "Can you add a button on Instagram so people can book from there?"
  (T-505)
- **What would change this:** S-73 has never tracked whether Instagram clients book, so the drop-off
  rests on one owner's estimate.

## What not to break
- **Deposits:** two salons, both Solo. "Love the deposit feature, no-shows have nearly stopped."
  (C-02); "Deposits changed my business." (C-03)

## Where the sources disagree
- S-07 rates the product 4 out of 5 in CSAT while losing "half" its Instagram leads in interview:
  the score doesn't reflect the problem it raised in conversation.

## What this can't tell us
- **Tickets** come from salons that hit a problem and wrote in. S-73 switched the reschedule link
  off and never filed a ticket, so salons with a workaround don't show up in the count.
- **CSAT** is five comments from salons that chose to leave one; no score here describes the
  customer base.
- **Interviews** are three conversations. Eight salons in total is enough to find problems, not
  to say how common they are.

## Questions for the next interviews
1. "Walk me through the last time a client rescheduled. What did you see in the book afterwards?"
   (theme 1; ask Solo salons too)
2. "Have you switched off any part of Corbel? What made you do it?" (finds hidden workarounds
   like S-73's)
3. "Which clients reschedule without a problem? What's different about those bookings?"
   (could disconfirm theme 1)
4. "Tell me about the last new client who found you on Instagram. What happened between the DM
   and the appointment?" (theme 2)

Next: turn theme 1 into a brief, with the Solo-salon question as an open risk.

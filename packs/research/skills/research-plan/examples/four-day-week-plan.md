# Worked example — "can you look into four-day weeks?"

## Input given to the skill

> Can you research four-day weeks for me? People keep bringing it up.

## The skill's one question

> Before I plan this: **what decision will the research inform, who makes it, and by when?**
> And what do you think the answer is right now?

## User's reply

> Our COO, Dana, has to decide by 1 November whether Acme's support team (14 people, B2B
> SaaS) goes to a four-day week from January. I think it'd be great for morale but I'm worried
> about response times. I've got about 20 hours over the next three weeks, and I can get
> ticket data from Zendesk.

---

## Output

# Research plan: four-day week for Acme support

_Prepared 2026-10-01 · Owner: the user · Due: 24 Oct 2026 (a week before the decision)_

## Decision

**Decision:** whether Acme's support team moves to a four-day week from January 2027.
**Decided by:** Dana (COO) · **By:** 1 Nov 2026
**Current belief:** good for morale, risky for response times. Overturned if comparable teams
kept response times within 10% and a rota is workable for 14 people.

## Question

For a 14-person B2B SaaS support team, does a four-day week keep first-response time within
10% of today and hold resolution volume, over six months, compared with the current five-day
week?

Out of scope: pay and contract changes (HR's question, after the decision), other teams,
and four-day weeks with longer days.

## Sub-questions

| # | Sub-question | Would change the decision if… | Method | Scope | Owner | Time |
|---|---|---|---|---|---|---|
| Q1 | What happened to response times and output in comparable pilots? | Response times rose more than 10% in most support-role pilots | Desk research | 15–25 sources screened, 5–10 kept | User | 8 h |
| Q2 | How does our ticket load spread across the week? | Friday and Monday together carry more than 45% of tickets, making a shared day off unworkable | Data pull | Zendesk, last 12 months, by weekday and hour | User + support ops | 3 h |
| Q3 | Can 14 people cover five days with staggered days off? | Fewer than 3 agents on any day at the current headcount | Rota model from Q2 data | One spreadsheet model | User | 3 h |
| Q4 | What does the team expect, and what worries them? | A majority of the team would prefer not to change | Short interviews | 5 agents and the team lead | User | 4 h |
| Q5 | Did any comparable team reverse its four-day week, and why? | Reversals cite customer coverage in support roles | Desk research (opposite-view search) | Included in Q1's budget | User | in Q1 |

## Sources (desk research)

**Source types, by weight:** pilot reports with before-and-after data; peer-reviewed studies;
surveys with stated sample and method; practitioner write-ups from support teams; news only
to find the underlying report.

**Include:** 2019 onwards; knowledge-work, support or customer-service roles; a measure of
output or response time before and after; UK, EU or North America.
**Exclude:** opinion pieces and vendor marketing (no data); manufacturing and shift work
(different coverage model); "four-day weeks" that keep 40 hours over four days (a different
intervention).

## Search strings

| For | String | Where | Filter |
|---|---|---|---|
| Q1 | `("four-day week" OR "4-day week" OR "reduced working week") AND (pilot OR trial) AND (productivity OR "response time" OR output)` | Google Scholar | 2019 onwards |
| Q1 | `("four-day week" OR "4-day week") AND ("customer support" OR "customer service" OR helpdesk)` | Google | past 5 years |
| Q5 | `("four-day week" OR "4-day week") AND (reversed OR abandoned OR "went back" OR ended)` | Google | past 5 years |

## Stopping rule

- **Enough when:** Q1 has at least three support-role sources with response-time or output
  data, and three more sources in a row add nothing new; Q2 to Q4 are answered.
- **Budget cap:** 20 hours or 24 Oct, whichever comes first. At the cap, deliver with the open
  sub-questions listed.

## Deliverable

A two-page synthesis for Dana by 24 Oct: cited findings for Q1 and Q5 (made with
`source-synthesis`), the Q2 weekday chart, the Q3 rota, the Q4 interview themes, and a
recommendation with the threshold each finding was judged against.

## Risks to the plan

| Risk | Fallback |
|---|---|
| Few published pilots cover support roles | Widen to all customer-facing roles and rate the evidence limited |
| Zendesk export lacks timestamps by hour | Use daily counts; the Q3 rota then works at day level |
| Interviewees tell the user what they think the user wants | Ask what would make it fail, and include the team lead's view separately |

## Assumptions to confirm

- [assumption] "Four-day week" means 32 hours at the same pay, not 40 hours over four days.
- [assumption] Current headcount stays at 14 through the pilot.

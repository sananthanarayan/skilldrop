# feedback-synthesis — reference

## Counting

- **The unit is a person or an account, stated once.** B2B with account IDs: accounts. B2C,
  or B2B with no account IDs: people. Say which in the headline or the theme table header.
- **Same ID, same person, across sources.** An interviewee identified as account A-1042 and the
  tickets from A-1042 are one account. Use the same `person_id` in every row.
- **No ID, own person.** A row with a blank `person_id` counts as its own person; the script
  labels these. When a theme is mostly anonymous rows, its count is a count of mentions and the
  reply says so.
- **Display names are weak IDs.** App-store reviewers with the same name and a consistent
  story (same device, same complaint, "updating my review") are treated as one; record it as
  an assumption. Two different stories under a common first name are two people.
- **Anonymous beside identified.** "3 accounts, plus one anonymous comment that may be one of
  them" — never 4.
- **A reporter speaking for others is one source, not many.** "Two of our clients in France
  couldn't pay" is one account reporting; the count of affected end users goes in the evidence
  as what the account said, not in the people count.
- **Repeat filing is evidence of cost, not of breadth.** Six tickets from one account say the
  problem is costing that account; they don't say six customers have it. Report the repeat
  filing as severity evidence ("raised six times in two months").

## Severity scale

Rate each item from what happened, not tone.

| Level | Rule | Edge cases |
|---|---|---|
| S1 — blocker | A core job can't be done, or money, data, security, privacy or compliance is at stake | A payment that fails and is later made another way is still S1: the job failed in the product. A message sent to the wrong recipient is S2 unless the person says it exposed sensitive data. |
| S2 — major | The job is done only through a costly recurring workaround, or the person says they will leave over it | "Thinking about moving to another tool" lifts an otherwise S3 item to S2. A one-off workaround that took an hour is S3. |
| S3 — minor | Slower, confusing or annoying; the workaround is quick | A how-to question is S3 when the person couldn't find something that exists; it is not a severity at all when they just asked. |
| S4 — cosmetic | Appearance, wording or preference with no stated cost | "Looks unprofessional" stays S4 unless the person says it cost them a client. |

A theme's severity is the worst level at least two people reached (that level or worse). A
theme raised by one person takes that person's level, labelled *one report — confirm before
acting*. Report the spread ("S1 for 3
accounts; S3 for 1") when it differs.

## Sampling bias by source

| Source | Who is in it | What it can't support |
|---|---|---|
| Support tickets | People who hit a problem and chose to write in; heavy users and the angriest over-represented | How common a problem is across all customers; what satisfied customers think |
| NPS / CSAT verbatims | Respondents who left a comment; strong opinions at both ends over-respond, and detractors write more | Satisfaction of the base; comparing themes by share of responses as if it were share of customers |
| App-store reviews | People moved to review, often right after a crash or a prompt; no IDs | Anything per user; retention; why non-reviewers stay |
| Interviews | Whoever agreed to talk, often recruited from engaged customers; small n | Frequency of anything; "4 of 5 interviewees" is a story count, not a rate |
| Sales-call notes | Prospects, filtered through a rep's summary; skews to those who asked for a demo and to what reps listen for | What existing customers need; prospect words, unless in quotation marks |
| Churn / exit surveys | Leavers who answered; the first reason ticked, often the easiest | Why people stay; reasons of segments that didn't churn in the period |
| Community / social posts | The vocal few; public posts perform | Anything per customer without IDs |

Always name, per source used, who is in it and one conclusion it can't support. Never turn a
self-selected count into a percentage of the user base. A share of the sample is allowed when
labelled as such: ✅ *"5 of the 10 exit-survey respondents"*.

## Rewriting a request into a problem

Ask of each request: *what was the person trying to do when they wanted this, and what does
not having it cost them?* Use only what they said.

| Request as given | Problem statement (when the item says why) | When the item doesn't say why |
|---|---|---|
| "Please add bulk edit for recurring invoices." + "had to open 58 recurring invoices one at a time" | Changing a rate means editing every recurring invoice by hand | — |
| "Add dark mode." | — | Request with no stated need; interview question: *"When do you use the app, and what's hard about it then?"* |
| "We need SSO with Entra." | Enterprise IT won't approve a rollout without central sign-in | — |
| "Make it work offline." + "half our jobs are in plant rooms" | Technicians lose access to job details where there's no signal | — |

The request stays in the evidence as a quote. Two different requests can sit under one problem,
and one request can point at two problems; code both.

## Codebook rules

- 4–12 problem themes plus the valued (`+`) themes. Fewer than 4 from 30+ items means themes are
  too broad; more than 12 means they are too narrow to act on.
- One sentence each: who, what happens, what it costs. Code is short kebab-case.
- An item can carry several codes. An item that fits no theme stays unthemed; don't stretch a
  theme to swallow it.
- How-to questions are coded only when several point at one gap ("can't find reports after the
  update"); otherwise they are unthemed and listed by count.
- Contradictions are their own finding, not a reason to drop a theme: code both sides.

## Interview questions

Tied to a theme, open, about past behaviour, not hypothetical, not leading:

- ✅ *"Tell me about the last time you changed your prices. What did you do in the product?"*
- ✅ Disconfirming: *"Which clients pay by card without trouble? What's different about them?"*
- ❌ *"Would you pay more for bulk edit?"* — hypothetical and leading
- ❌ *"Is dark mode important to you?"* — yes/no, and the answer is always yes

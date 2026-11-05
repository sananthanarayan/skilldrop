# Worked example: a "Slack approvals" brief whose data describes a different problem

Input → output oracle for `prd-draft`. Shows a solution-shaped brief rewritten as the problem
its own data describes, an unsupported goal replaced by one the data can measure, and a policy
constraint that the brief's "one click" pitch would have broken.

## Input

> Write the PRD for Slack approvals so eng can start next sprint. Sales says it's the #1 ask.
> Two pages max. Everything I have is below.
>
> **brief.md (Head of Sales):**
> Problem: we don't have a Slack integration and competitors do. Customers ask for it
> constantly. Solution: Slack approvals, so managers approve expenses with one click right in
> Slack. Seamless. Must use Slack Block Kit interactive messages. Goal: cut churn by 15%. Has
> to ship before the Ledgerline Summit on 2027-03-09.
>
> **crm-summary.md:**
> - Feature requests tagged "slack": 14 requests from 9 accounts in the last 12 months, out of
>   1,340 paying accounts.
> - Requests tagged "approval reminders" or "approve from phone": 31 requests from 22 accounts.
>
> **product-analytics.md:**
> - Median time an expense waits at the approver step: 4.6 days. Median time in all other
>   steps combined: 0.8 days.
> - Of reimbursements paid late (more than 10 days after submission, the SLA in our customer
>   contracts), 58% waited on an approver for more than 5 days.
> - Chat tool connected, by account: Slack 38%, Microsoft Teams 27%, none 35%.
> - Approvers who open the email notification approve a median of 1.1 days after it is sent.
>
> **policy.md (Finance and Security):**
> - Approving an expense over $2,500 requires the approver to be signed in with MFA.
> - Approvers cannot edit amounts. They can approve, reject with a reason, or return for changes.

## Output

```markdown
# PRD: Faster approver decisions on submitted expenses

**Status:** draft · **Owner:** Product Manager, Approvals · **Date:** 2026-11-05
**Binding constraint:** fixed deadline, ship before 2027-03-09 `[reported by Head of Sales]`

## Problem

Employees wait for reimbursement mainly because expenses sit with their approver. The median
wait at the approver step is 4.6 days, against 0.8 days for every other step combined
`[data: product analytics]`. Of the reimbursements that miss the 10-day contractual SLA, 58%
waited on an approver for more than 5 days `[data: product analytics]`. Approvers who open the
notification email act in a median of 1.1 days `[data: product analytics]`, which suggests the
delay is in noticing and getting to the request rather than in deciding `[assumption]`.
Customers ask about this in several forms: 31 requests from 22 accounts for reminders or
approving from a phone, and 14 requests from 9 accounts for Slack `[data: CRM]`.

## Users

**Primary:** a manager who approves their team's expenses, works mostly outside the expense
app, and gets to approvals in batches. Job-to-be-done: clear the pending requests without
setting time aside to log in.
**Secondary (explicitly deprioritized):** employees who submit expenses. They feel the delay
but cannot shorten it. Finance admins, who chase late approvals today, benefit indirectly.

## Goals

| # | Goal | We'll know it worked when |
|---|---|---|
| G1 | Approvers decide sooner | Median approver-step time drops from 4.6 to ≤ 2.0 days within 90 days of GA `[target: assumption]` |
| G2 | Fewer reimbursements miss the contractual SLA | The share of reimbursements paid after 10 days falls by a third within 90 days of GA `[baseline needed]` |

Full measurement design (instrumentation, guardrails, decision rule): hand to `success-metrics`.

## Requirements

| ID | Requirement (testable, solution-free) | MoSCoW | Maps to goal |
|---|---|---|---|
| R1 | An approver can approve, reject with a reason, or return for changes on an expense of $2,500 or less, from the notification itself, without signing in to the web app | M | G1 |
| R2 | For an expense over $2,500, the same notification takes the approver to a signed-in, MFA-verified screen to decide | M | G1 |
| R3 | The notification shows employee, amount, category, date and receipt thumbnail, enough to decide without opening the expense | M | G1 |
| R4 | An approver with any pending request older than 2 days gets one reminder per day, listing all of them | S | G1, G2 |
| R5 | The approver can act from at least one channel that reaches accounts with no chat tool connected | S | G2 |
| R6 | A decision made from a notification shows in the expense's audit history with time and channel | M | G1 |
| R7 | An approver can approve several pending requests in one action | C | G1 |

**Won't have (this version):**
- Editing amounts from a notification: policy forbids approvers editing amounts at all
- Decisions on expenses over $2,500 without MFA, however the notification is delivered

## Non-goals (minimum 3 — the scope-creep firewall)

- **Submitting expenses from chat:** the delay is at approval, not submission. Revisit if
  submission time becomes the bottleneck.
- **Every chat tool in v1:** Slack reaches 38% of accounts and Teams 27% `[data]`. Which
  channels ship first is a design decision, made against those numbers and the deadline.
- **Finance-admin bulk overrides:** a different user with a different authorization surface.
- **Churn reduction as a v1 target:** nothing in the inputs links approval time to churn. The
  brief's "−15% churn" is out until someone produces that link.

## Quality targets

A decision taken from a notification shows in the web app within 10 seconds `[assumption]`.
MFA rule as in policy. Full treatment → `nfr-spec`.

## Open questions

| Question | Owner | Needed by |
|---|---|---|
| Which channel(s) ship first given the 38% / 27% / 35% split and the 2027-03-09 date? | Eng lead + PM | 2026-11-19 |
| What is the current share of reimbursements paid after 10 days (G2 baseline)? | Data analyst | 2026-11-12 |
| Is there any evidence linking approval delay to churn? | Head of Sales | 2026-11-26 |
| Can a decision from a notification count as "signed in" for the audit trail Finance needs? | Security lead | 2026-11-19 |

## Assumptions log

- [assumption] The delay is in noticing requests, not deciding them. Challenge by checking time-to-open versus time-to-decide by 2026-11-19.
- [assumption] The G1 target of ≤ 2.0 days. Challenge in requirements review.

## Handoffs

- Stories & slicing → `user-story-splitter`
- Quality targets → `nfr-spec`
- Measurement → `success-metrics`
- Technical approach (including the Block Kit question in the brief) → `design-doc`
```

## Why this is the oracle

- **The problem statement passes the alternative-solution test.** The brief's problem, "we
  don't have a Slack integration", is the absence of a solution. The data describes approvers
  sitting on requests. Daily reminders, email actions, Teams, mobile push and Slack could each
  follow from the rewritten paragraph. That matters here because Slack alone reaches 38% of
  accounts.
- **Every claim is tagged to its source and every goal can be measured.** "Customers ask
  constantly" becomes 14 requests from 9 of 1,340 accounts, set beside the 31 requests from 22
  accounts for reminders. The −15% churn goal has no support in the inputs, so it moves to the
  non-goals with the reason, and G1 measures something the analytics already track.
- **Requirements are testable and free of implementation.** "Must use Block Kit" goes to
  design. "One click, seamless" becomes R1, which a tester can pass or fail. R2 carries the
  $2,500 MFA rule, which the brief's pitch would have broken.

A cheaper pass writes "Problem: competitors have Slack approvals and we don't", makes every
line in the brief a Must, keeps "cut churn 15%" as G1 and "use Block Kit" as R1, and specifies
one-click approval for every amount. That PRD ships a feature that 62% of accounts cannot
use, measures it against a number nothing supports, and fails a security review in sprint 4.

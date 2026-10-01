# Example: Northwind checkout, week ending 30 September

The user's message:

> Weekly status for the checkout team, 24–30 Sept, for Dana (head of e-commerce) and the
> payments steering group. Export attached: `northwind-week-40.csv`. Context the export doesn't
> have: SEC-88 is the security team's pen-test report, which the PCI questionnaire needs; they
> told us it lands 3 Oct. API-412 is the platform team's paginated order-history endpoint, no
> date yet. Black Friday code freeze is 6 Nov.

The export is [`northwind-week-40.csv`](northwind-week-40.csv): 15 Jira issues with `Resolved`,
`Due date` and `Inward issue link (Blocks)` columns. There's no sprint file, so the plan is
"items due in the period".

## Step 1: run the script

```bash
python3 scripts/status_counts.py examples/northwind-week-40.csv \
  --from 2026-09-24 --to 2026-09-30 -o status-numbers.md --json status-numbers.json
```

## Step 2: the script's output, unedited

```markdown
# Status numbers: 2026-09-24 to 2026-09-30

Source: northwind-week-40.csv · 15 items · plan: items due between 2026-09-24 and 2026-09-30
Columns used: key='Issue key', title='Summary', status='Status', owner='Assignee', priority='Priority', created='Created', updated='Updated', resolved='Resolved', due='Due date', blocker='Inward issue link (Blocks)', labels='Labels'

## Suggested RAG: Red

Rule: Red if plan completion < 60% or >= 2 planned items blocked; Amber if completion < 85%, any planned item blocked, or a High-or-above planned item slipped; otherwise Green.
- Red: plan completion 50% is below 60%
- Amber: 1 planned item is blocked
- Amber: 3 High-or-above planned item(s) slipped: CHK-102, CHK-107, CHK-119

| Measure | Count |
|---|---:|
| Shipped in period | 5 |
| In progress | 4 |
| Blocked | 2 |
| Planned to finish by 2026-09-30 | 8 |
| Planned and done | 4 (50%) |
| Slipped (planned, not done) | 4 |
| Shipped but not in plan | 1 |

## Shipped

| Key | Title | Owner | Done |
|---|---|---|---|
| CHK-103 | Apple Pay button missing on Safari 17 | Lena Fischer | 2026-09-29 |
| CHK-105 | Show delivery date estimate on the cart page | Lena Fischer | 2026-09-26 |
| CHK-113 | Add fraud score to order admin view | Tom Okafor | 2026-09-25 |
| CHK-121 | Discount line rounds to wrong penny on mixed-VAT carts | Marco Rossi | 2026-09-24 |
| CHK-122 | Rotate PSP API keys | Tom Okafor | 2026-09-28 |

## In progress

| Key | Title | Owner | Status |
|---|---|---|---|
| CHK-102 | Save card for future purchases | Tom Okafor | In Review |
| CHK-112 | One-click reorder from order history | Aisha Bello | In Progress |
| CHK-116 | Persist cart across devices for signed-in users | Lena Fischer | In Progress |
| CHK-125 | Load test checkout for Black Friday | Marco Rossi | In Progress |

## Blocked

| Key | Title | Owner | Blocker | Last update |
|---|---|---|---|---|
| CHK-107 | Update PCI self-assessment questionnaire | Aisha Bello | SEC-88 | 2026-09-30 |
| CHK-123 | Order history pagination | Marco Rossi | API-412 | 2026-09-22 |

## Slipped (planned, not done by 2026-09-30)

| Key | Title | Owner | Status | Priority | Due |
|---|---|---|---|---|---|
| CHK-102 | Save card for future purchases | Tom Okafor | In Review | High | 2026-09-30 |
| CHK-107 | Update PCI self-assessment questionnaire | Aisha Bello | Blocked | Highest | 2026-09-30 |
| CHK-116 | Persist cart across devices for signed-in users | Lena Fischer | In Progress | Medium | 2026-09-30 |
| CHK-119 | Accessibility fixes on the payment form | (none) | To Do | High | 2026-09-30 |

## Risk candidates

- CHK-107 (Update PCI self-assessment questionnaire): planned for this period and blocked
- CHK-119 (Accessibility fixes on the payment form): planned for this period with no owner
- CHK-114 (Klarna pay-later option): top priority (Highest) and not started

## Work in progress by owner (in progress + blocked)

| Owner | Items |
|---|---:|
| Aisha Bello | 2 |
| Marco Rossi | 2 |
| Lena Fischer | 1 |
| Tom Okafor | 1 |

```

## Step 3: the report

Every number is from the output above. The blocker descriptions and dates come from the
user's message, and are marked where the export didn't have them.

```markdown
# Checkout team status: 24–30 September 2026

**Status: Red.** Rule: plan completion below 60% is Red. We finished 4 of the 8 items due this
week (50%). One of the four that slipped is blocked; three are High or Highest priority.

## Shipped (5)

- CHK-113 Fraud score in the order admin view (Tom Okafor), 25 Sep
- CHK-105 Delivery date estimate on the cart page (Lena Fischer), 26 Sep
- CHK-122 Rotated PSP API keys (Tom Okafor), 28 Sep
- CHK-103 Apple Pay button fixed on Safari 17 (Lena Fischer), 29 Sep
- CHK-121 Discount rounding fix on mixed-VAT carts (Marco Rossi), 24 Sep. Unplanned: came in
  as a bug on 23 Sep.

## Slipped against plan (4 of 8 due)

| Item | Owner | Where it is | Priority |
|---|---|---|---|
| CHK-107 PCI self-assessment questionnaire | Aisha Bello | Blocked by SEC-88 | Highest |
| CHK-102 Save card for future purchases | Tom Okafor | In review | High |
| CHK-119 Accessibility fixes on the payment form | No owner | Not started | High |
| CHK-116 Persist cart across devices | Lena Fischer | In progress | Medium |

No new dates are given here: the export has none, and the owners haven't supplied them.

## Blocked (2)

| Item | Owner | Blocked by | Expected |
|---|---|---|---|
| CHK-107 PCI questionnaire | Aisha Bello | SEC-88, the security team's pen-test report | 3 Oct (security team, per user) |
| CHK-123 Order history pagination | Marco Rossi | API-412, the platform team's paginated endpoint; no update since 22 Sep | No date |

## In progress (4)

CHK-102 Save card (in review), CHK-112 One-click reorder, CHK-116 Persist cart, CHK-125
Black Friday load test (due 16 Oct).

## Risks

- **CHK-119 accessibility fixes have no owner and were due this week.** It's High priority
  and hasn't started.
- **CHK-114 Klarna is Highest priority and not started,** with no owner.
- **The Black Friday code freeze is 6 Nov** (per user). CHK-125's load test is due 16 Oct, which
  leaves three weeks to act on what it finds.

## Asks

1. **Security team:** confirm SEC-88 lands on 3 Oct, so CHK-107 can be finished.
2. **Platform team:** a date for API-412. CHK-123 has been waiting since 22 Sep.
3. **Dana:** name an owner for CHK-119 this week.
4. **Dana:** confirm CHK-114 Klarna is still Highest. Nobody is assigned to it.
```

What the report left out: a "% on track" or velocity figure (the export can't support one), a
reason for CHK-102 sitting in review (not in the data), and new dates for the slipped items
(none given).

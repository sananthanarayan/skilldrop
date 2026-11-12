# Example: triaging the Northwind checkout backlog

The user exported the Northwind checkout team's Jira backlog to CSV and asked: "Triage this
before Thursday's refinement. Who's missing, what's a duplicate, what should we pull next?"
The export is [`northwind-backlog.csv`](northwind-backlog.csv): 20 issues, Jira's default CSV
columns, dates in Jira's `02/Jun/26 9:14 AM` format.

## Step 1: run the script

```bash
python3 scripts/triage_backlog.py examples/northwind-backlog.csv --as-of 2026-10-01 \
  -o triage.md --changes changes.csv
```

## Step 2: the script's output, unedited

`triage.md`:

```markdown
# Backlog triage findings: northwind-backlog.csv

As of 2026-10-01 · 20 items in export · 18 open · 2 done or closed (skipped)
Thresholds: stale > 30 days · similarity >= 0.75 · oversized estimate > 8

Columns used: key='Issue key', title='Summary', description='Description', status='Status', owner='Assignee', priority='Priority', estimate='Custom field (Story Points)', created='Created', updated='Updated', labels='Labels'

| Check | Count |
|---|---:|
| Duplicate candidate pairs | 3 |
| No owner | 8 |
| No acceptance criteria | 11 |
| Stale (> 30 days) | 10 |
| Oversized | 3 |
| Priority conflicts | 11 |

## Duplicate candidates

| Pair | Score | Titles | Shared words |
|---|---:|---|---|
| CHK-116 / CHK-117 | 0.87 | Persist cart across devices for signed-in users / Persist the cart across devices for logged-in shoppers | across cart devices persist |
| CHK-103 / CHK-109 | 0.86 | Apple Pay button missing on Safari 17 / Apple Pay button not showing in Safari | apple button pay safari |
| CHK-101 / CHK-104 | 0.80 | Guest checkout without creating an account / Allow guest checkout without an account | account checkout guest without |

Title similarity only. Read both descriptions before merging.

## No owner

| Key | Title | Status | Priority | Last update |
|---|---|---|---|---|
| CHK-101 | Guest checkout without creating an account | To Do | Highest | 2026-06-10 |
| CHK-104 | Allow guest checkout without an account | Backlog | Medium | 2026-07-19 |
| CHK-109 | Apple Pay button not showing in Safari | Backlog | Medium | 2026-08-26 |
| CHK-111 | Split shipment tracking emails | Backlog | Medium | 2026-02-15 |
| CHK-114 | Klarna pay-later option | Backlog | Highest | 2026-08-22 |
| CHK-115 | Gift message at checkout | Backlog | Lowest | 2025-11-11 |
| CHK-117 | Persist the cart across devices for logged-in shoppers | Backlog | Low | 2026-06-18 |
| CHK-119 | Accessibility fixes on the payment form | To Do | High | 2026-09-21 |

## No acceptance criteria

| Key | Title | Status | Priority | Owner |
|---|---|---|---|---|
| CHK-101 | Guest checkout without creating an account | To Do | Highest | - |
| CHK-104 | Allow guest checkout without an account | Backlog | Medium | - |
| CHK-106 | Rebuild the payments service on the new platform | Backlog | High | Tom Okafor |
| CHK-109 | Apple Pay button not showing in Safari | Backlog | Medium | - |
| CHK-110 | Address autocomplete for UK postcodes | To Do | Low | Marco Rossi |
| CHK-111 | Split shipment tracking emails | Backlog | Medium | - |
| CHK-114 | Klarna pay-later option | Backlog | Highest | - |
| CHK-115 | Gift message at checkout | Backlog | Lowest | - |
| CHK-117 | Persist the cart across devices for logged-in shoppers | Backlog | Low | - |
| CHK-119 | Accessibility fixes on the payment form | To Do | High | - |
| CHK-120 | Checkout analytics dashboard | Backlog | Highest | Marco Rossi |

## Stale (no update in more than 30 days)

| Key | Title | Status | Priority | Days since update |
|---|---|---|---|---|
| CHK-115 | Gift message at checkout | Backlog | Lowest | 324 |
| CHK-111 | Split shipment tracking emails | Backlog | Medium | 228 |
| CHK-106 | Rebuild the payments service on the new platform | Backlog | High | 182 |
| CHK-110 | Address autocomplete for UK postcodes | To Do | Low | 154 |
| CHK-120 | Checkout analytics dashboard | Backlog | Highest | 142 |
| CHK-101 | Guest checkout without creating an account | To Do | Highest | 113 |
| CHK-117 | Persist the cart across devices for logged-in shoppers | Backlog | Low | 105 |
| CHK-104 | Allow guest checkout without an account | Backlog | Medium | 74 |
| CHK-114 | Klarna pay-later option | Backlog | Highest | 40 |
| CHK-109 | Apple Pay button not showing in Safari | Backlog | Medium | 36 |

## Oversized (split before scheduling)

| Key | Title | Status | Priority | Why |
|---|---|---|---|---|
| CHK-101 | Guest checkout without creating an account | To Do | Highest | estimate 13 > 8 |
| CHK-106 | Rebuild the payments service on the new platform | Backlog | High | estimate 21 > 8 |
| CHK-114 | Klarna pay-later option | Backlog | Highest | estimate 13 > 8 |

## Priority conflicts

- Priority inflation: 5 of 18 prioritised open items (28%) are at the top priority.
- CHK-101 (Guest checkout without creating an account): priority Highest but no owner
- CHK-101 (Guest checkout without creating an account): priority Highest but no update in 113 days
- CHK-106 (Rebuild the payments service on the new platform): priority High but no update in 182 days
- CHK-114 (Klarna pay-later option): priority Highest but no owner
- CHK-114 (Klarna pay-later option): priority Highest but no update in 40 days
- CHK-119 (Accessibility fixes on the payment form): priority High but no owner
- CHK-120 (Checkout analytics dashboard): priority Highest but no update in 142 days
- CHK-116 (Persist cart across devices for signed-in users): likely duplicate of CHK-117 but priority Medium vs Low
- CHK-103 (Apple Pay button missing on Safari 17): likely duplicate of CHK-109 but priority High vs Medium
- CHK-101 (Guest checkout without creating an account): likely duplicate of CHK-104 but priority Highest vs Medium

## Priority distribution (open items)

| Priority | Open items |
|---|---:|
| Highest | 5 |
| High | 5 |
| Medium | 5 |
| Low | 2 |
| Lowest | 1 |

```

`changes.csv` (first 6 of 35 rows):

```csv
key,action,field,proposed_value,reason
CHK-117,confirm-duplicate,status,Duplicate of CHK-116,title similarity 0.87 with CHK-116
CHK-109,confirm-duplicate,status,Duplicate of CHK-103,title similarity 0.86 with CHK-103
CHK-104,confirm-duplicate,status,Duplicate of CHK-101,title similarity 0.80 with CHK-101
CHK-101,assign-owner,assignee,,open item with no owner
CHK-104,assign-owner,assignee,,open item with no owner
CHK-109,assign-owner,assignee,,open item with no owner
```

## Step 3: the triage, after reading the descriptions

Every count below comes from the script output above. The duplicate verdicts, the priority
proposals and the ordering are judgment, and each one gives its reason.

```markdown
# Backlog triage: Northwind checkout, as of 2026-10-01

18 open items. 3 duplicate pairs, 8 with no owner, 11 with no acceptance criteria,
10 stale (over 30 days), 3 oversized. 5 of 18 open items (28%) are at Highest.

## Duplicates (confirmed by reading both descriptions)

| Keep | Close | Why they're the same | Why this one survives |
|---|---|---|---|
| CHK-116 | CHK-117 | Both ask for the cart to follow a signed-in shopper across devices | CHK-116 has an owner, acceptance criteria and an update 7 days ago; CHK-117 has none of these |
| CHK-103 | CHK-109 | Same symptom: the Apple Pay button doesn't show in Safari | CHK-103 names the version (Safari 17), the report count (14) and acceptance criteria. Copy CHK-109's customer note into CHK-103 as a comment |
| CHK-101 | CHK-104 | Both ask for guest checkout without an account | CHK-101 states the reason (the forced sign-up step is the biggest funnel drop-off). Carry CHK-104's reporter over as a watcher |

## Proposed ordering (open, not yet started)

| # | Key | Title | Why here | Ready to pull? |
|---|---|---|---|---|
| 1 | CHK-107 | Update PCI self-assessment questionnaire | Fixed external date: submit before 31 Oct. Owned, 2 points, definition of done present | Yes |
| 2 | CHK-103 | Apple Pay button missing on Safari 17 | 14 customer reports; blocks a payment method. Owned, 3 points | Yes |
| 3 | CHK-119 | Accessibility fixes on the payment form | Screen readers skip a payment field, so some shoppers can't pay | No: needs an owner and acceptance criteria |
| 4 | CHK-112 | One-click reorder from order history | High, owned, acceptance criteria, 5 points | Yes |
| 5 | CHK-101 | Guest checkout without creating an account | Highest value claim in the backlog, but 13 points, unowned, 113 days without an update | No: split first, then assign |
| 6 | CHK-105 | Show delivery date estimate on the cart page | Medium, owned, acceptance criteria, 3 points | Yes |
| 7 | CHK-116 | Persist cart across devices for signed-in users | Medium, owned, acceptance criteria, 5 points | Yes |

In progress and left where they are: CHK-102, CHK-113.

## Priority conflicts to resolve

- **Five items at Highest (28% of the backlog).** CHK-120 (analytics dashboard) has had no update
  in 142 days and has no acceptance criteria. Proposal: drop it to Medium unless someone owns a
  date for it.
- **CHK-114 Klarna is Highest but unowned, 13 points, no acceptance criteria.** The description
  says a partner deal is signed. Ask whether the deal carries a launch date; if it does, it
  moves above CHK-112 once split.
- **CHK-106 payments rebuild is High, 21 points, 182 days untouched.** Keep High only if the
  team can name the first slice; otherwise move it to Low and revisit at planning.

## Change list

| Key | Change | Reason |
|---|---|---|
| CHK-117 | Close as duplicate of CHK-116 | Same request, see above |
| CHK-109 | Close as duplicate of CHK-103; copy customer note | Same symptom |
| CHK-104 | Close as duplicate of CHK-101 | Same story |
| CHK-101, CHK-114, CHK-106 | Split with `user-story-splitter` | Estimates 13, 13, 21 (limit 8) |
| CHK-101, CHK-114, CHK-119, CHK-111 | Assign an owner | Open with no assignee |
| CHK-119, CHK-110, CHK-120 | Add acceptance criteria | None found |
| CHK-120 | Priority Highest → Medium (proposal) | Stale 142 days, no criteria |
| CHK-115 | Close: won't do | Lowest, no owner, 324 days without an update |
| CHK-111, CHK-110 | Ask the reporter to confirm or close | 228 and 154 days without an update |

## Questions before applying

1. Who owns CHK-101, CHK-114 and CHK-119?
2. Does the Klarna deal (CHK-114) have a launch date?
3. Is CHK-120 still Highest, and for whom?
```

What the triage did *not* do: it didn't change any priority on its own, and it didn't
invent an owner or a date. Each of those is a question in the last section.

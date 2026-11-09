# Worked example: heads of terms for a first office

## Input

> *"We've been offered heads of terms for our first office
> ([inputs/heads-of-terms.md](inputs/heads-of-terms.md)). The agent wants an answer this week.
> What are we committing to, and when could we get out?"*

The terms extracted are [`../templates/terms.json`](../templates/terms.json).

## What it computed

```text
# Lease: dates and money

Term: 2027-01-01 to 2031-12-31 (60 months).

## Deadlines

| Date | What | Detail |
|---|---|---|
| 2027-04-01 | rent starts | after 3 months rent-free |
| 2029-07-01 | tenant break notice | for the break on 2030-01-01; conditions: all rent paid; vacant possession |
| 2030-01-01 | rent review | cpi, upward only |
| 2031-06-30 | notice to leave at the end | for the end on 2031-12-31 |

## Committed cost

| Up to | Rent | Service charge | Total |
|---|---:|---:|---:|
| to the break on 2030-01-01 | £99,000 | £14,400 | £113,400 |
| to the end of the term (2031-12-31) | £179,990 | £24,000 | £203,990 |

## Rent by year

| Year | From | Yearly rent | Paid that year |
|---:|---|---:|---:|
| 1 | 2027-01-01 | £36,000 | £27,000 |
| 2 | 2028-01-01 | £36,000 | £36,000 |
| 3 | 2029-01-01 | £36,000 | £36,000 |
| 4 | 2030-01-01 | £40,495 | £40,495 |
| 5 | 2031-01-01 | £40,495 | £40,495 |

Deposit: £18,000.

WARN the break on 2030-01-01 is conditional (all rent paid; vacant possession): one unmet condition, such as a small unpaid sum, can make it fail
```

## Reply

**Signing commits Brightloop to £113,400 up to the break on 1 January 2030** (33 months' rent
after the rent-free, plus service charge), **and £203,990 if you stay to the end** on 31
December 2031. The break needs written notice by **1 July 2029**, and as drafted it fails if any
sum is unpaid or the unit isn't empty on the day, which would keep you in to 2031 for another
£90,590.

**Fixes before signing**
- 🟥 **Personal guarantee.** Ask for: *"No personal guarantee; the Tenant will provide a rent
  deposit of six months' rent instead."* The deposit is already there.
- 🟥 **Break conditions.** Ask for: *"The only condition of the break is that the Tenant has paid
  the principal rent due up to the break date."*
- 🟧 **Full repairing with no schedule of condition.** Ask for a photographic schedule of
  condition, attached to the lease, and repair limited to that condition.
- 🟧 **Service charge with no cap.** Ask for a cap at £4,800 rising with CPI, and no charges for
  improvements or replacing plant.
- 🟨 **No sharing.** Ask for the right to share with group companies without consent, and to
  sublet with consent not to be unreasonably withheld.

**Deadlines to diarise**
- 1 April 2027: rent starts.
- 1 July 2029: last day to serve the break notice.
- 1 January 2030: rent review, to £40,495 a year at the capped 4 % (CPI below the cap would mean less).
- 30 June 2031: notice to leave at the end.

**Worth a lawyer's hour:** the personal guarantee, if the landlord won't drop it.

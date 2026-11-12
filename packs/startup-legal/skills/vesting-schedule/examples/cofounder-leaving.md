# Worked example: a co-founder leaving 14 months in

## Input

> *"My co-founder Alex is leaving at the end of September. Alex has 3M shares, four-year vesting
> with a one-year cliff from 1 July 2025 when we started; the stock purchase agreement was
> signed on 15 September 2025. How much does Alex keep, and we're not sure Alex ever filed the
> 83(b) — does that matter?"*

## Input written (in a private temporary folder)

```json
{
  "company": "Brightloop Labs, Inc.",
  "jurisdiction": "US",
  "grants": [
    {"holder": "Alex (co-founder)", "type": "founder stock", "shares": 3000000, "grant_date": "2025-09-15", "vesting_start": "2025-07-01",
     "months": 48, "cliff_months": 12, "frequency": "monthly", "leave_date": "2026-09-30"}
  ]
}
```

## What it computed

```text
# Brightloop Labs, Inc.: vesting

| Holder | Type | Shares | Cliff | Fully vested | Vested on date | Unvested |
|---|---|---:|---|---|---:|---:|
| Alex (co-founder) | founder stock | 3,000,000 | 2026-07-01: 750,000 | 2029-07-01 | 875,000 (2026-09-30) | 2,125,000 |

## Alex (co-founder)
- 83(b) election: file by **2025-10-15**, 30 days from 2025-09-15.
- left 2026-09-30: 875,000 vested, 2,125,000 unvested shares the company can buy back

| Date | Vests | Total vested |
|---|---:|---:|
| 2026-07-01 | 750,000 | 750,000 |
| 2026-08-01 | 62,500 | 812,500 |
| 2027-07-01 | 62,500 | 1,500,000 |
| 2028-07-01 | 62,500 | 2,250,000 |
| 2029-07-01 | 62,500 | 3,000,000 |
| … 37 vesting dates in all (--full for every one) | | |
FAIL Alex (co-founder): the 83(b) deadline was 2025-10-15; it has passed unless it was filed
```

## Reply

**Alex keeps 875,000 of the 3,000,000 shares.** Vesting started on 1 July 2025, the cliff
vested 750,000 on 1 July 2026, and 62,500 more vested on 1 August and on 1 September. Leaving on
30 September, the other 2,125,000 are unvested, and under a standard founder stock agreement
the company can buy them back at the price Alex paid. Check the repurchase clause for how
long the company has to exercise that right (often 90 days) and diarise it.

**The 83(b) matters, and its deadline was 15 October 2025**, 30 days after the stock was bought
on 15 September. If it was filed, Alex was taxed on the shares' value at purchase, which for
founder stock is usually close to nothing. If it wasn't, each tranche that vested (the 750,000
in July, and 62,500 a month since) counts as income at its value on the day it vested. Ask
Alex for the IRS acknowledgement or the copy sent with the filing.

**Assumptions**
- `[assumption]` Monthly vesting after the cliff, on the 1st. If the agreement vests
  quarterly, Alex has 750,000: the next tranche would have been 1 October.

**Worth an hour with a tax adviser:** if Alex didn't file the 83(b), how the vested tranches
should be reported, before the next tax filing.

# Worked example: three SAFEs and a note into a Series A

## Input

> *"We're two founders with 4.5M shares each, 250k options granted and 750k left in the pool.
> We raised $500k on a post-money SAFE at an $8M cap, $125k from an accelerator (post-money,
> $6M cap, 20 % discount), $100k from an early angel on the old pre-money SAFE ($5M cap, 20 %
> discount), and a $50k friends-and-family note at 6 % from June 2025 ($5M cap, 20 %). The
> term sheet: $16M pre, $4M from the lead and $1M follow-on, 10 % option pool post-money,
> closing mid-December. What do we each end up with?"*

## Input written (in a private temporary folder)

```json
{
  "company": "Example Labs, Inc.",
  "currency": "USD",
  "holders": [
    {"name": "Founder A", "class": "common", "shares": 4500000},
    {"name": "Founder B", "class": "common", "shares": 4500000}
  ],
  "options": {"granted": 250000, "pool_unissued": 750000},
  "safes": [
    {"holder": "Angel syndicate", "amount": 500000, "type": "post", "cap": 8000000},
    {"holder": "Accelerator", "amount": 125000, "type": "post", "cap": 6000000, "discount": 0.2},
    {"holder": "Early angel", "amount": 100000, "type": "pre", "cap": 5000000, "discount": 0.2}
  ],
  "notes": [
    {"holder": "Friends and family note", "principal": 50000, "rate": 0.06, "issued": "2025-06-01", "cap": 5000000, "discount": 0.2}
  ],
  "round": {
    "pre_money": 16000000,
    "investors": [{"name": "Series A lead", "amount": 4000000}, {"name": "Series A follow-on", "amount": 1000000}],
    "pool_target": 0.10,
    "close": "2026-12-15"
  }
}
```

## Reply

**After the Series A you each own 28.3 %, down from 45 % today.** The new investors take
23.8 %, the SAFEs and note 8.0 % together, and the option pool 11.6 %.

| Holder | Class | Shares | % |
|---|---|---:|---:|
| Founder A | common | 4,500,000 | 28.30 |
| Founder B | common | 4,500,000 | 28.30 |
| Angel syndicate | preferred (safe) | 704,673 | 4.43 |
| Accelerator | preferred (safe) | 234,891 | 1.48 |
| Early angel | preferred (safe) | 216,801 | 1.36 |
| Friends and family note | preferred (note) | 118,415 | 0.74 |
| Series A lead | preferred (round) | 3,028,714 | 19.05 |
| Series A follow-on | preferred (round) | 757,178 | 4.76 |
| Options granted | options | 250,000 | 1.57 |
| Option pool, unissued | options | 1,590,074 | 10.00 |
| **Total** | | **15,900,746** | **100.00** |

**What each SAFE and note converted at.** All four convert at their caps; none of the
discounts gives a lower price at $1.3207 a share.

| SAFE or note | Invested (with interest) | Converts at | By | Shares |
|---|---:|---:|---|---:|
| Angel syndicate (post-money safe) | $500,000 | 0.7095 | cap | 704,673 |
| Accelerator (post-money safe) | $125,000 | 0.5322 | cap | 234,891 |
| Early angel (pre-money safe) | $100,000 | 0.4613 | cap | 216,801 |
| Friends and family note (pre-money note) | $54,619 | 0.4613 | cap | 118,415 |

**What the pool top-up costs you.** The term sheet's 10 % pool has to be topped up by 840,074
shares, and they come out of the pre-money. That makes the $16M headline worth $14.9M to the
existing holders: about $1.1M of the valuation goes to future hires before you've hired them.
If the lead agreed to top up the pool after the round instead, you'd each hold 28.8 %, half a
point more.

**Assumptions**
- `[assumption]` The pool is in the pre-money, the usual term. Moved after the round, you each hold 28.83 % instead of 28.30 %.
- `[assumption]` The note's interest runs to 15 December 2026: $54,619 converts, not $50,000.

**Before you sign:** have your lawyer confirm whether the term sheet's 10 % pool is pre- or
post-money, and that the early angel's SAFE really is the pre-money form; that is what
converts it at $0.46 rather than at its post-money equivalent.

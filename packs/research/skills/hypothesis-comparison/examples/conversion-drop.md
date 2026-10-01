# Worked example — why did Northwind's mobile checkout conversion drop?

## Input given to the skill

> Our checkout conversion dropped about 18% starting Tuesday 8 Sep and everyone has a theory.
> Engineering says it's seasonal, marketing thinks Contoso's 20%-off promo (launched 1 Sep) is
> pulling people away, and I suspect the checkout release we shipped Monday 7 Sep at 22:00.
> What we know:
> - last September we never saw a dip bigger than 3%
> - sessions and add-to-cart are flat week on week
> - it's only mobile Safari; desktop and Android look normal
> - the payment provider's dashboard shows settled orders down 17% for the same days
> - support tickets about "card declined" or "button not working" doubled since the 8th
> - the tag manager container was also republished on the 7th
> - our synthetic checkout test on iOS Safari has passed on every run since the release
>
> Which explanation actually fits?

---

## Output

# Competing hypotheses: Northwind mobile checkout conversion drop

_Prepared 2026-09-15 · Evidence as of 14 Sep · Method: analysis of competing hypotheses_

## Observation

Checkout conversion fell about 18% from Tue 8 Sep, on mobile Safari only.

## Assumptions to confirm first

- [assumption] "Conversion" means orders ÷ sessions in the web analytics tool, the same
  definition used last September.
- [assumption] The payment dashboard counts orders by settlement date, so its 17% fall covers
  the same days as the conversion drop.
- [assumption] The Safari-only split comes from the order records, not only from the analytics
  tag. If it comes from the tag, E4 says nothing about H4.

## Hypotheses

| Id | Hypothesis | Could be true alongside |
|---|---|---|
| H1 | The 7 Sep checkout release broke payment for some iOS Safari users | H3 |
| H2 | It's a normal seasonal dip | H3 |
| H3 | Contoso's promotion is taking buyers who would have checked out with us | H1, H2 |
| H4 | Nothing changed for customers; the 7 Sep tag manager change broke conversion tracking | none |

H4 is the measurement hypothesis. Nobody had raised it, but the tag manager change on the
same day makes it a real rival.

## Evidence and matrix

Rated row by row. Weights: E4 is 2 because a pattern this specific (one browser on one
platform) is hard to produce by chance; E6 is 0.5 because a promotion's existence says little
about who it affects.

| Id | Evidence | Weight | H1 | H2 | H3 | H4 | Diagnostic? |
|---|---|---|---|---|---|---|---|
| E1 | Fall starts Tue 8 Sep; release went out Mon 7 Sep 22:00 | 1 | C | N | N | C | no |
| E2 | Last September never dipped more than 3% | 1 | N | II | N | N | yes |
| E3 | Sessions and add-to-cart flat week on week | 1 | C | I | I | C | yes |
| E4 | Drop on mobile Safari only | 2 | C | I | I | N | yes |
| E5 | Payment provider: settled orders down 17% | 1 | C | C | C | II | yes |
| E6 | Contoso promo launched 1 Sep | 0.5 | N | N | C | N | no |
| E7 | "Card declined" / "button not working" tickets doubled | 1 | C | N | I | I | yes |
| E8 | Tag manager container republished 7 Sep | 1 | N | N | N | C | no |
| E9 | Synthetic iOS Safari checkout test passes every run | 1 | I | N | N | N | yes |

## Ranking

Script output (`python3 scripts/ach_matrix.py conversion-drop.csv`), ranking section:

```
| Rank | Hypothesis | Inconsistency score | I | II | C or CC |
|---|---|---|---|---|---|
| 1 | H1 checkout release | 1 | 1 | 0 | 5 |
| 2 | H4 tracking change | 3 | 1 | 1 | 3 |
| 3 | H3 competitor promo | 4 | 3 | 0 | 2 |
| 4 | H2 seasonal dip | 5 | 2 | 1 | 1 |

**Least contradicted:** H1 checkout release (score 1), 2 ahead of H4 tracking change.
```

## What the ranking rests on

- **Diagnostic evidence:** E4 (Safari only) and E3 (flat traffic) count against the seasonal
  and promotion hypotheses, because both would hit every device and cut sessions. E2 rules out
  "seasonal" almost alone. E5 (real orders down) is the one row against the tracking hypothesis.
- **Non-diagnostic, set aside:** E1, E6 and E8. The timing (E1) is the reason the release
  feels guilty, but it fits the tracking change just as well. The script flags all three:

  ```
  **Non-diagnostic:** E1, E6, E8. These count the same against every hypothesis, so they cannot help you choose. Keep them for completeness; don't cite them as support.
  ```

- **Linchpin:** E5. The script's sensitivity check:

  ```
  - **E5** (Payment-provider dashboard shows settled orders down 17% for the same days): without it, first place is H1 checkout release and H4 tracking change (tie)
  ```

  Everything that separates "customers are failing to pay" from "we stopped counting
  properly" rests on the payment dashboard. Confirm it matches the order database for
  7–14 Sep before acting on this ranking.

## Conclusion

**H1, the checkout release,** is the least contradicted explanation. Confidence:
**moderate**, because the lead over H4 rests on one row (E5) that hasn't been cross-checked,
and E9 counts against H1.

H2 and H3 can be dropped as main causes: each conflicts with the Safari-only pattern and the
flat traffic. H3 can still be acting in the background at a small scale.

What would rule out each survivor:

- **H1:** iOS Safari payment errors flat across the release, in the payment SDK logs.
- **H4:** the order database agreeing with the payment dashboard that real orders fell 17%.

E9 is worth a look on its own: the synthetic test may not cover the path real users take
(saved cards, Apple Pay), which would make it a weaker row than its weight of 1 suggests.

## Next observation

| Check | H1 predicts | H4 predicts | Who | How long |
|---|---|---|---|---|
| iOS Safari payment SDK errors, 6–10 Sep, by hour | A step up after 22:00 on 7 Sep | No change | Payments engineering | Under an hour |
| Order database count vs payment dashboard, 7–14 Sep | Both down about 17% | Database flat, which means the payment dashboard is wrong too | Data team | Half a day |

Run the first check today. If it shows the step, roll back or hotfix the release and watch
iOS Safari conversion for 48 hours.

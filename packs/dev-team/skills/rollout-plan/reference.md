# rollout-plan — reference

## How long a step must run

A step compares a flag-on cohort (treatment, share `e` of traffic, rate `p2` if the regression
is real) with a concurrent flag-off cohort (control, share `c`, baseline rate `p1`). With `T`
units per hour, after `t` hours the arms hold `n1 = T·e·t` and `n2 = T·c·t`. The two-proportion
z-test (normal approximation) is powered when

```
t = [ ( zα · √( p̄(1−p̄)(1/e + 1/c) ) + zβ · √( p2(1−p2)/e + p1(1−p1)/c ) ) / |p2 − p1| ]² / T
p̄ = (e·p2 + c·p1) / (e + c)
```

`zα` is 1.96 for a two-sided test at α = 0.05 (1.645 one-sided), `zβ` is 0.84 for power 0.8.
For two equal arms this reduces to the familiar units-per-arm figure
`n = (zα√(2p̄(1−p̄)) + zβ√(p1(1−p1) + p2(1−p2)))² / (p2 − p1)²`.

What the formula says in practice:

- **The small arm sets the clock.** At 1% exposure the control is enormous and adds almost no
  information; time is roughly `n_treatment / (T · e)`. Halving exposure doubles the time.
- **50/50 is the fastest comparison.** Past 50% the control becomes the small arm.
- **Small baselines are slow.** Catching +0.3 pp on a 0.5% error rate needs about 11,000 units
  per arm; catching +0.3 pp on a 30% rate needs about 367,000, because variance grows with `p(1−p)`.
  Relative regressions on rare events ("errors up 10%") need the most data of all.
- **Two-sided is the default** because a change can also look suspiciously good (a broken
  error counter reads as "fewer errors"). Use `--one-sided` only when the user accepts that.

## When the formula is the wrong tool

The formula assumes a step sees hundreds of events. When it sees a handful, change the rule,
not the step length:

- **Expected count first.** Exposure × volume per unit time. ✅ *"5 accounts × 2 statements a
  day = 10 statements a day"*. If the step expects fewer than one event, it is a smoke test and
  says so.
- **Zero-tolerance or count limits.** For correctness (a total, a price, a tax amount) one
  unexplained difference is the signal: hold or roll back on the first. For failure rates, compare
  counts with what the baseline predicts: at a 0.5% baseline, 400 runs predict 2 failures; 6 or
  more is a breach (Poisson, about 1-in-60 by chance).
- **Shadow beats exposure** when the old and new answers can be compared without sending anything:
  every real unit is evidence, nobody is exposed, and the gate is the diff report.
- **Cycles beat hours** when the volume is batched: one monthly run can carry more evidence than
  the rest of the month together. Count the runs left before the deadline before drawing the ladder.

## The randomisation unit

Count `--traffic` in the unit the flag assigns. When a user-level flag is judged on a
request-level metric, one user's requests are correlated, so the effective sample is smaller
than the request count; the script's figure is then a floor. Either count users and use a
per-user metric ("share of users who hit an error"), or say the time is a lower bound.

## Threshold patterns

| Metric | ✅ Testable | ❌ Untestable |
|---|---|---|
| Error rate | flag-on ≤ flag-off + 0.3 pp at 11,000 requests per arm | "no increase in errors" |
| Latency | p95 flag-on ≤ flag-off + 40 ms; p99 ≤ flag-off + 120 ms once 10,000+ requests per arm | "latency stays healthy" |
| Saturation | DB pool in use ≤ 80% at peak in the flag-on hosts | "watch the database" |
| Business | booking conversion flag-on ≥ flag-off − 1 pp | "no impact on revenue" |
| Abort | flag-on 5xx > 3× flag-off for 5 consecutive minutes | "if things go badly wrong" |

Abort triggers are wide and fast, sized to catch a disaster from small samples. Promotion
thresholds are tight and slow, read once at the planned sample. Mixing the two produces either
an abort that fires on noise or a promotion read on noise.

Tail percentiles need samples: an estimate of p99 rests on the 1% above it, so 10,000 requests
leave about 100 points in the tail; p95 at 2,000 leaves about 100 too. Below those counts, read
p95 or the median and say so.

## Cohort rules

- **Internal first** catches crashes and obvious breakage at no customer cost. It is not
  evidence about rates: staff behave differently and are few.
- **Nested hashing** (`hash(salt + unit_id) mod 1000 < k`, with `k` rising) keeps everyone
  from earlier steps exposed, so nobody flips back and forth.
- **Use a fresh salt per flag.** Reusing another flag's salt puts the same users in every 1%.
- **SLA and regulated customers** join at 50% or later unless they opted in; contractual notice
  periods can make even that a comms item.
- **Overlapping experiments** on the same surface confound both readings. Exclude, or make the
  allocations orthogonal and analyse by the other experiment's arm.

## What turning the flag off does not undo

| Category | Typical residue | Handling to plan |
|---|---|---|
| Data written in a new format | New-format JSON, enum values, encodings | Old code reads the new format before step 1, tested; or a cleanup job with an owner |
| Rows, events, jobs | Orders, records, queued jobs, analytics events | Jobs check the flag at run time, or are safe to run after flag-off |
| Messages | Emails, push, SMS, webhooks | No recall; a correction template ready; daily volume cap in early steps |
| Money and third parties | Charges, refunds, partner orders, per-call billing, filings | The reversal API or procedure, or written as permanent |
| Caches | Entries keyed the same as the old path | Versioned keys, or TTL stated as the rollback's tail |
| Shipped clients | Mobile and desktop builds with the path compiled in | A server-side switch; flag config TTL stated |
| Schema expansions | Columns, tables, indexes | Stay; contracted by the migration plan |
| Search indexes, ML features | Re-indexed documents, logged features used for training | Reindex job or a training-data exclusion window |

A **point of no return** exists when a step's residue changes what flag-off restores for
the people already exposed: data old code can't read, a partner contract triggered, a one-way
message campaign. Schedule it as late as the ladder allows and list what is verified just
before it.

# Worked example: delivery-estimate endpoint rewrite

## Input given to the skill

> We've rewritten `GET /v1/delivery-estimate` (Ruby → Kotlin). I replayed 8 requests against
> both and recorded the responses: `old_a.jsonl` and `old_b.jsonl` are two runs of the old
> service on the same requests, `new.jsonl` is the new one. Rule we care about: orders placed
> before 22:00 dispatch the same day, weekdays only. The diff is full of IDs and timestamps.
> Is it the same?

Each record is `{"case_id", "status", "body"}`; the body has `estimate_id`, `generated_at`,
`dispatch_date`, `delivery_date` and a `carriers` list. Requests (`placed_at` in UTC):

| Case | placed_at | Postcode |
|---|---|---|
| e01 | 2026-07-14 08:05 | SW1A 1AA |
| e02 | 2026-07-14 21:30 | SW1A 1AA |
| e03 | 2026-01-13 21:30 | SW1A 1AA |
| e04 | 2026-07-18 10:00 (Saturday) | EH1 1AA |
| e05 | 2026-07-14 09:00 | ZZ9 9ZZ (unknown) |
| e06 | 2026-01-13 22:15 | EH1 1AA |
| e07 | 2026-03-29 21:20 (Sunday, BST starts) | SW1A 1AA |
| e08 | 2026-07-15 21:59 | EH1 1AA |

## What the run looked like

Old against old, no rules: `estimate_id`, `generated_at` and the order of `carriers` differ in
all seven 200 responses; nothing else does. Those three fields get one rule each:

```json
{"rules": [
  {"path": "body.generated_at", "rule": "ignore", "reason": "wall-clock time of the call"},
  {"path": "body.estimate_id", "rule": "regex", "pattern": "^est_[0-9a-f]{10}$", "replace": "est_<id>", "reason": "random per call"},
  {"path": "body.carriers", "rule": "sort", "reason": "old service shuffles; the checkout page sorts carriers itself"}
]}
```

Old against old with the rules: `EQUIVALENT`, 8 of 8. Old against new with the same rules:

```
Verdict after rules: NOT EQUIVALENT

Cases: 8 old, 8 new, 8 compared: 6 matched, 2 mismatched, 0 accepted-only

Differences by field:
  path                                      diffs  cases  case ids
  body.dispatch_date                            2      2  e02, e08
  body.delivery_date                            2      2  e02, e08

First 4 of 4 differences:
  e02  body.dispatch_date  [changed]  old=2026-07-15  new=2026-07-14
  e02  body.delivery_date  [changed]  old=2026-07-16  new=2026-07-15
  e08  body.dispatch_date  [changed]  old=2026-07-16  new=2026-07-15
  e08  body.delivery_date  [changed]  old=2026-07-20  new=2026-07-17
```

## Reply

**NOT EQUIVALENT.** The new service applies the 22:00 cut-off in UTC; the old one applies it
in London time. In summer, orders placed between 21:00 and 22:00 UTC (22:00–23:00 in London)
now get same-day dispatch and a delivery date one to three days earlier than the old service
gave.

**Differences**
- 🟥 Defect: `dispatch_date` and `delivery_date`, e02 and e08. e02 (21:30 UTC, 22:30 BST): dispatch 15 Jul → 14 Jul. e08 (21:59 UTC, Wednesday): dispatch 16 Jul → 15 Jul, delivery Mon 20 Jul → Fri 17 Jul. Both are after 22:00 London time and before 22:00 UTC; e03, the same clock time in January, matches. Check where the new code converts `placed_at` before comparing with the cut-off.

**Noise, normalised:** `generated_at` (clock), `estimate_id` (random, format still checked) and
`carriers` order (shuffled by the old service, sorted by the page). All three varied between
the two old runs; nothing else did.

**Covered:** morning and late-evening weekday orders in winter and summer, a Saturday, an
unknown postcode (422, same body), a post-cut-off winter order. **Not covered:** the DST
change itself, because e07 falls on a Sunday and both versions roll it to Monday; the Friday
after-cut-off case; bank holidays, if the old service knows any.

**To confirm**
- Add a weekday order between 21:00 and 22:00 UTC on the Monday after each clock change, and a Friday 22:30 London order, then rerun.
- Fix the time-zone conversion and rerun all 8 before anyone treats the earlier dates as an improvement.

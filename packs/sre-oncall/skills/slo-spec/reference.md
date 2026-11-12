# slo-spec reference — SLIs, budgets, burn rates, dependencies, low traffic, policy

## SLI menu by journey type

| Journey type | SLI (good / valid) | Typical good threshold |
|---|---|---|
| Request/response (API, page) | Availability: non-5xx, non-timeout responses / valid requests | — |
| Request/response | Latency: requests answered under T / valid requests | T from what users tolerate (search ~1 s, API ~300 ms) |
| Asynchronous (queue, job) | End-to-end: items whose result is visible to the user within T of submission / valid submissions | T from the user's wait (order confirmed in 30 s) |
| Data pipeline | Freshness: reads served data newer than T / valid reads | T from how stale the user can bear |
| Data pipeline | Correctness: records passing a known-answer check / records checked | — |
| Batch | Completion: runs finished by deadline / scheduled runs | the deadline the consumer needs |
| Streaming / long session | Time-based: minutes with the stream healthy / minutes in use | — |

Use two SLIs for a journey at most (availability and latency is the usual pair). Latency is
always "share under a threshold", never an average or a bare percentile value.

## Defining "valid"

Write the exclusions explicitly. The usual list:

- **Exclude:** client errors the user caused (4xx validation, 401 bad credentials, 404 for
  genuinely missing items), business declines that are correct outcomes (a card the bank
  declines), health checks, synthetic and load-test traffic, requests from blocked bots.
- **Keep as valid (and bad):** 5xx, timeouts, 429s our own limits caused, a 200 carrying an
  error body, a 202 whose job never completes, a cancelled request the user gave up on after
  the threshold.
- **State the rule once** and apply it to both numerator and denominator. An SLI whose
  numerator and denominator come from different sources drifts.

## Measurement points and what each misses

| Point | Sees | Misses |
|---|---|---|
| Client / real-user beacon | What the user experienced, including network and rendering | Users who never load the beacon; noisy, needs sampling care |
| Synthetic probe | A fixed, known rate of events; works at zero traffic | Real users' paths and data |
| Load balancer / edge logs | Every request, total server-side time including queueing in front of the app | Client network, DNS, CDN failures before the LB |
| App server timer | Handler time | Time waiting in the accept queue, thread pool or message queue |
| Worker timer behind a queue | Processing time only | The queue wait — the part that grows under load |

On an async path, stamp the time the request reached the edge and measure to the moment the
result is visible to the user. Queue depth is a cause signal; it is not the SLI.

## Error-budget arithmetic

- Budget fraction `b = 1 − target` (99.9% → 0.001).
- Minutes of full outage per window = `b × window_days × 1440`. 99.9% / 30 d = 43.2 min;
  99.9% / 28 d = 40.32 min; 99.95% / 30 d = 21.6 min; 99.99% / 30 d = 4.32 min.
- Bad requests per window = `b × requests_per_day × window_days`.
- Minutes and requests agree only under even traffic. A peak hour at 3× average burns 3×
  faster in budget terms than the minutes suggest.

## Burn-rate alerts

Burn rate `B` = observed error rate / `b`. At 1× the budget lasts exactly the window.

- Error rate that trips an alert = `B × b`.
- Budget consumed when it fires = `B × long_window_hours / (window_days × 24)`.
- Time from a full budget to exhaustion = `window_days × 24 / B` hours.
- Expected bad events in a window at the threshold = `B × b × requests_per_hour × window_hours`.
  Under ~10, the window fires on a handful of failures.

Default set (Google SRE workbook, "Alerting on SLOs", for a 30-day window):

| Burn | Long | Short | Budget at fire | Exhausts in | Action |
|---|---|---|---|---|---|
| 14.4× | 1 h | 5 m | 2% | 50 h | page |
| 6× | 6 h | 30 m | 5% | 5 d | page |
| 1× | 3 d | 6 h | 10% | 30 d | ticket |

Fire only when both windows exceed the rate: the long one proves it's significant, the short
one proves it's still happening, so the alert resets within minutes of the fix. A burn rate
above `1 / b` can never fire (14.4× on a 95% target needs a 72% error rate; at 90%, 144%).

## Dependency ceilings

Hard dependencies called in series multiply: two at 99.9% and 99.95% give a ceiling of
`0.999 × 0.9995 = 99.85%`. A target above the ceiling needs one of:

- a second provider or replica in parallel (`1 − (1 − a)²` for two independent copies at `a`),
- a cache or stale-read fallback so the dependency's failure isn't the user's failure,
- an async path (accept now, retry later) where the journey tolerates delay.

Share of the budget a dependency spends at its own SLO = `(1 − ceiling) / b`. At 50% or
more, the service's own failures have half the room the number suggests.

## Low-traffic journeys

A ratio SLI needs volume. When the expected bad events per alert window are under ~10:

1. **Lengthen the SLO window** (90 days) so the budget holds more than a few events.
2. **Lengthen alert windows** and accept slower detection; say how much slower.
3. **Add a synthetic probe** at a fixed rate (one a minute = 1,440 events/day) and set the
   SLI on probes, or on probes plus real requests.
4. **Alert only when someone uses it:** ticket within working hours, page never, if the users
   are staff who will report a failure themselves.
5. **Group** several low-traffic endpoints with the same users into one SLI.

State which and why; don't silently reuse the high-traffic paging set.

## Error-budget policy skeleton

| Budget state | What changes | Who decides |
|---|---|---|
| < 50% spent | Normal releases | Team |
| ≥ 50% spent before half the window | Reliability work goes to the top of the next sprint; risky changes need review | Engineering lead |
| 100% spent | Freeze: only fixes, security patches and reliability changes ship until the budget is positive over the window | Engineering lead; product owner informed |
| Spent by one incident > 20% of budget | Postmortem with actions, tracked to done | Incident owner |
| Spent by a dependency | Escalate to the dependency's owner with the numbers; the freeze still covers risky changes; revisit the target or the redundancy | Engineering lead |

Plus: an **exception route** (who can approve shipping during a freeze, in writing, and how it
is recorded), **what's exempt** (security patches, legal deadlines), **agreed in advance** by
product and engineering with names or roles, and a **review date** for the targets themselves.

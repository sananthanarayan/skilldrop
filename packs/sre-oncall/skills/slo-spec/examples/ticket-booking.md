# Worked example — Larkspur Theatres booking API

## Input

> Set SLOs for our booking API. Customers browse showtimes (about 900,000 requests a day) and
> book seats (about 60,000 bookings a day). Booking calls our card processor, whose SLO is
> 99.95%; the API returns 200 only after the charge succeeds. Box-office staff use a back-office
> API, about 800 requests a day, 10:00–22:00. Last quarter from load balancer logs: browse
> 99.96%, booking 99.87%, back-office 99.4%. Our CTO wants "four nines everywhere". The team
> lead is Ines Calder; product owner is Raj Bhatt.

## Script runs

```bash
python3 scripts/slo_math.py --batch slos.json        # browse, booking (with --dep 99.95)
python3 scripts/slo_math.py --name "Box-office API (probe every minute)" \
    --target 99.5 --window 30 --rpd 1440 --alerts "6:6h:1h:ticket"
```

Output, abridged to the rows used below:

```
Browse showtimes (availability): 99.9% over 30 days
  = 43.2 minutes of full outage per window (43m 12s)
  = 27,000 bad requests per window at 900,000 requests/day
  14.4x  1h    5m     page      1.44%          2%              2d 2h       540        45
  6x     6h    30m    page      0.6%           5%              5d          1,350      112
  1x     3d    6h     ticket    0.1%           10%             30d         2,700      225

Book seats (end to end): 99.8% over 30 days
  = 86.4 minutes of full outage per window (1h 26m 24s)
  = 3,600 bad requests per window at 60,000 requests/day
  14.4x  1h    5m     page      2.88%          2%              2d 2h       72         6 *
  Hard dependencies in series: 99.95% -> ceiling 99.95%; at their SLOs they spend 25% of this budget
  - 14.4x 1h/5m: only 6 bad events in the 5m short window ... the short window will flap.

Box-office API (probe every minute): 99.5% over 30 days
  = 216 minutes of full outage per window (3h 36m)
  6x    6h    1h     ticket    3%             5%              5d          10.8       1.8 *
```

## Reply

**Four nines isn't reachable for booking: every booking needs the card processor, which only
promises 99.95%, so 99.99% would be spent five times over by the processor alone. I've set
booking at 99.8% (last quarter ran 99.87%), browse at 99.9%, and the back-office API at 99.5%
on a synthetic probe, because 800 requests a day is too few to page on.**

Assumptions: 30-day rolling window; traffic is the daily average you gave; the 1 s, 10 s and
2 s thresholds are mine `[assumption]`.

| Journey | SLI (good / valid) | Measured at | Target | Budget per 30 days |
|---|---|---|---|---|
| Browse showtimes | Good: non-5xx in < 1 s / Valid: all `GET /showtimes`, excluding health checks and bots | Load balancer | 99.9% | 43.2 min · 27,000 bad requests |
| Book seats | Good: 200 or a bank decline within 10 s / Valid: all `POST /bookings`, excluding 4xx validation errors | Load balancer | 99.8% | 86.4 min · 3,600 bad bookings |
| Back-office API | Good: probe gets a correct answer in < 2 s / Valid: one probe a minute | Probe | 99.5% | 216 min of failed probes |

At its own SLO the card processor spends 25% of booking's budget. Going above 99.95% would need
a second processor or an accept-now, charge-later path.

| Journey | Burn | Long / short | Trips at | Budget at fire | Exhausts in | Action |
|---|---|---|---|---|---|---|
| Browse | 14.4× | 1 h / 5 m | 1.44% errors | 2% | 2 d 2 h | page |
| Browse | 6× | 6 h / 30 m | 0.6% | 5% | 5 d | page |
| Browse | 1× | 3 d / 6 h | 0.1% | 10% | 30 d | ticket |
| Booking | 14.4× | 1 h / 15 m | 2.88% | 2% | 2 d 2 h | page |
| Booking | 6× | 6 h / 30 m | 1.2% | 5% | 5 d | page |
| Booking | 1× | 3 d / 6 h | 0.2% | 10% | 30 d | ticket |
| Back-office | 6× | 6 h / 1 h | 3% of probes | 5% | 5 d | ticket, 10:00–22:00 |

Booking's 5-minute short window would hold about 6 failed bookings at the threshold and
flap, so it is 15 minutes. The back-office probe still has fewer than 2 failures expected in an
hour, so it raises a ticket and never pages; staff will report an outage faster than a page.

**Error-budget policy** (owner: Ines Calder; to be agreed with Raj Bhatt before it applies)

| Budget state | What changes |
|---|---|
| 50% spent in the first 15 days | Reliability work tops the next sprint |
| 100% spent | Only fixes and security patches ship until the 30-day budget is positive |
| Card processor spent it | Raise it with the processor using the numbers; the freeze still covers risky changes |

Exception: the CTO approves a release during a freeze in writing, recorded on the release ticket.

To confirm: the three latency thresholds; whether bank declines reach the API as 200 or 402.

Next step: add the browse and booking alerts to the alerting system and set up the
back-office probe.

# catalogue-search — SLO status (Bramblecote Travel)

Service: `catalogue-search`, the holiday search behind the website and app.
Traffic: about 1,200,000 search requests a day.

People:
- Search team engineering lead: Marta Lindqvist
- Product manager, search: Owen Achterberg
- VP Engineering: Helen Varga
- Data Platform team lead (owns the shared Postgres cluster): Kofi Mensah

## Current SLO

- SLI: share of valid search requests answered with a non-5xx response in under 800 ms,
  measured at the load balancer. Valid excludes health checks and the partner scraper.
- Target: 99.5% over a rolling 28 days.

## The last two windows

| Window | Budget used | Biggest consumers |
|---|---|---|
| 4 Aug – 31 Aug | 140% | Shared Postgres cluster failover, 21 Aug: about 62% of the window's budget. Two search releases with a slow ranking query: about 55%. Remaining: scattered timeouts. |
| 1 Sep – 28 Sep | 115% | Search release 4.18 (index rebuild during peak): about 70%. Postgres replica lag, 12 Sep: about 30%. Remaining: scattered timeouts. |

Nothing changed after either window. Releases continued at 3–4 a week.

## The ask

Helen wants a written error-budget policy before Q4 planning, and has suggested raising the
target to 99.99% "so the team takes it seriously".

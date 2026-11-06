# Things that hurt (collected in retro, Sept)

- Order export builds the CSV with string concatenation (export/orders.py). Priya owns export.
- CI build takes 22 minutes on main (measured last week, `ci-timings.csv`). 14 engineers push to it. People batch PRs to avoid waiting.
- Export breaks when a customer name has a comma. Three incidents in Q3: INC-311, INC-318, INC-327. Each one was a manual re-export for finance.
- We should rewrite the frontend in TypeScript, it would be nicer.
- The `legacy_auth` module is still imported by the admin panel. It's scheduled for removal when admin moves to SSO in Q1.
- Feature flags are never cleaned up: 143 flags in `flags.yaml`, 61 of them at 100% for more than 6 months. New joiners ask which ones matter.
- Staging database is refreshed by hand by whoever remembers. Last refresh was 11 weeks ago; two bugs last month only reproduced in prod.

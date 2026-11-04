# Saved searches v2 — what we have for readiness

Collected by Elif Demir (tech lead), 4 Nov 2026. Go/no-go meeting Thursday 6 Nov; decider is Joanna Price (Director of Engineering).

## Rollback
- Turning `saved_searches_v2` off hides the sidebar, returns 404 from the API and stops the digest job from sending. Tested in staging on 31 Oct. Owner: Elif. Evidence: https://wiki.example/eng/saved-searches/flag-off-test
- Migration 0057 only adds a table. Nothing reads it with the flag off.

## Monitoring and alerts
- Dashboard: https://grafana.example/d/saved-searches (API latency, error rate, saves per hour).
- Alert: saved-searches API 5xx > 1% for 10 min pages the Search on-call. https://alerts.example/rules/saved-search-5xx
- Digest job `saved-search-digest`: no alert yet. If it fails, nobody would know until users say they didn't get the email. Elif: "on my list".

## Runbooks
- API: https://wiki.example/runbooks/saved-searches-api (owner: Rui).
- Digest job: none yet.

## Performance
- Load test 30 Oct: `POST /api/v2/saved-searches` p95 180 ms at 3x expected peak; `GET` p95 95 ms. https://wiki.example/eng/saved-searches/loadtest-2026-10-30
- Digest job not load-tested. In staging it took 4 min for 2,000 saved searches.

## Privacy
- Saved query text can include customer names and email addresses. Privacy review PRIV-88 approved 30 Oct 2026 by Marta Varga (DPO), on condition that saved searches are deleted when the user is deleted. Deletion hook merged in #815. https://wiki.example/privacy/PRIV-88

## Support and comms
- Support macro drafted and reviewed by Support lead (Owen Fitzgerald). https://wiki.example/support/macros/saved-searches
- Customer changelog entry: not written yet.

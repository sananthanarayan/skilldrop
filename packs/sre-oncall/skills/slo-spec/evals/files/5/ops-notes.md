# Tally — ops notes (Jonah)

Tally = internal expense approval app. Employees submit expenses, their approver approves, finance pays.

## Setup
- Django + gunicorn behind nginx, single VM `tally-vm-01`. Postgres runs on the same VM.
- I deploy by hand, ~2x/month. gunicorn restart takes ~30s; nginx returns 502 for anything that comes in meanwhile.
- IT auto-patches and reboots the VM every Sunday 02:00–02:20. PingDeck checks are paused during that window.

## Users / traffic
- ~300 employees submit, ~40 approvers, finance team of 6 (lead: Marisol Teague — month-end close is when she cares most).
- ~1,900 requests per working day on average, almost all 08:00–18:00 Mon–Fri, ~22 working days a month.
  Last 3 working days of the month are roughly 3x busier. Nights and weekends: under 20 requests total.
- Monthly requests (nginx access logs in Loki): Jul 40,300 · Aug 37,900 · Sep 42,600
- ~350 403s a month — people clicking approval links for reports they aren't the approver on.

## Errors (nginx 5xx, from Loki)
- Jul 61 · Aug 23 · Sep 140
- Sep 16: PeopleCore outage, ~2.5h. Every submit/approve failed with 500 because approver lookup failed.

## Monitoring
- Loki has nginx access logs (status, path, request_time) and Django app logs.
- PingDeck hits `GET /health` every minute. Reports 99.95% uptime over the last 90 days.
  `/health` just returns `{"ok": true}` from Django — doesn't touch Postgres or PeopleCore.
- Alerts: none right now apart from PingDeck emailing me.

## Dependencies
- Corp SSO (IT Identity team) — published SLO 99.9%. Needed to log in.
- PeopleCore HR API (vendor) — SLA 99.5% monthly. Approver lookup on every submit and every approval. No cache.
- Corporate SMTP relay — notification emails, async with retries; failures don't fail the request.

## People
- Me (Jonah Okafor) — only dev. Reachable business hours, no on-call rota.
- Dana Whitfield — my manager.

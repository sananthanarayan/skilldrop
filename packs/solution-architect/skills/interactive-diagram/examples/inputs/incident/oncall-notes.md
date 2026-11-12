# Incident 2026-10-03: card payments failing

Notes kept in the on-call channel, times in UTC.

09:12 deploy: payments v2.14 rolled out to all regions (release bot)
09:19 dashboard: card authorisation errors pass 5% and keep climbing
09:41 pager: "card-auth-error-rate" fires, 22 minutes after the climb began
09:44 Ana acknowledges the page and opens the incident
09:51 Ana: errors started with the 2.14 rollout, nothing else changed
09:58 rollback to v2.13 started
10:09 rollback finished in all regions
10:11 dashboard: card errors back under 0.5%
10:30 status page updated: resolved
6 Oct 14:00 postmortem held; action: alert on the error rate's rise, not a fixed 5% for 20 minutes

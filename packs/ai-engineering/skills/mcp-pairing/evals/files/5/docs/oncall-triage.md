# On-call triage loop (draft)

Trigger: a Sentry alert fires for `payments-api` or a Grafana alert pages the on-call.

1. **Gather** - pull the Sentry issue (stack trace, release, affected users count) and the
   Grafana dashboard panels for latency / error rate around the alert window.
2. **Correlate** - find the GitLab merge requests and deploys that landed in the 24h before
   the first event. Look at the diff of the suspect MR.
3. **Check data** - if the error looks data-related, run a couple of SELECTs against the
   `payments` Postgres database to see whether bad rows exist.
4. **Ticket** - open a Linear issue in the `PAY` team with the findings, priority Urgent, and
   assign it to the on-call.
5. **Postmortem draft** - write a first-draft postmortem in markdown from everything above,
   for the on-call to edit.

Constraints: Sentry is self-hosted at sentry.internal.example. Grafana is Grafana Cloud.
Payments DB has a primary and one read replica. We're PCI-scoped, so card data columns exist
in `payments.transactions` (pan_last4, card_token, billing_address).

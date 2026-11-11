# Brightwell booking platform today

- `booking-api`: a single service (Python) with a Postgres database
  (`appointments`, `patients`, `clinics` tables). Runs as 3 instances behind
  a load balancer.
- A nightly cron job on one instance sends email confirmations.
- No message queue is in use today. The platform team runs Postgres and Redis
  already and would rather not add another stateful system.
- Text messages are sent through "SMS Vendor A", which the clinic group has a
  contract with. Its API accepts one message per call, is rate limited to
  20 messages per second per account, and posts delivery reports and inbound
  replies to a webhook we host.
- Patient phone numbers are stored in `patients.phone`.

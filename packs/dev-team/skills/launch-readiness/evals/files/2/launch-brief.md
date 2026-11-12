# Launch brief: SMS "ready to collect" reminders

Owner: Digital Pharmacy product team, Brightwell Pharmacies
Status: PR #2207 merged to main on 13 Oct

## What it does
When a repeat prescription is ready, the patient gets an SMS telling them where and when to
collect it. Patients who have opted in to reminders only.

## Data change
Migration 0042 moves reminder opt-in from the `patients.reminder_opt_in` column to a new
`contact_preferences` table, then drops `patients.reminder_opt_in`.

## Rollout
Monday 08:00, all 140 stores at once: the `sms_reminders` flag is switched on globally.

## Rollback
Turn the `sms_reminders` flag off.

## Capacity
Load tested at 3x expected peak - see load-test-summary.txt.
Expected peak: 1,500 messages per minute on Monday morning (weekend backlog of prescriptions).

## Monitoring
SMS provider's delivery dashboard. Alerts: TBD.

## Comms
- Store staff briefing pack: drafted, sent to store managers 10 Oct.
- Patient FAQ page: drafted, not yet published.

## Privacy
Signed off - see privacy-signoff.txt. Message wording in sms-template.txt.

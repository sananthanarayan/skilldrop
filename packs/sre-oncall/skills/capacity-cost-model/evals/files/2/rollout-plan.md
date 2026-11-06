# Field operations: smart meter rollout plan (v3)

Prepared by the Field Operations lead.

## Install ramp

| Month | Meters installed (cumulative) |
|---|---|
| 3 | 15,000 |
| 6 | 40,000 |
| 9 | 65,000 |
| 12 | 85,000 |
| 18 | 105,000 |
| 24 | 120,000 |

## Meter behaviour (from the meter supplier's firmware spec)

- Meters take a reading every 15 minutes.
- Meters do not send each reading as it is taken. They upload a batch four times a day, at 00:00, 06:00, 12:00 and 18:00, carrying the last 6 hours of readings (24 readings per upload).
- Each meter picks a random start time within a 10-minute window after the scheduled time. There is no other spreading.
- The upload schedule is fixed in firmware for the whole 2027 contract term. The supplier will not change it before then.
- One upload is one message on the ingestion queue.

## Other environments

- A test rig of 500 meters on the bench at the depot, uploading on the same schedule.
- A staging copy of the full pipeline, which the platform team say they need for testing firmware updates.

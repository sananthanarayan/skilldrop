# Reminder push pipeline (notification-svc)

- Scheduler job runs every 15 min and plans each user's reminders for the next 24h.
- Planned sends are written to the `push_outbox` table with a send_at timestamp,
  then picked up by the sender workers (FCM for Android, APNs for iOS).
- The flag is checked by the scheduler at planning time, not by the sender.
- Smart reminders can schedule up to 3 nudges/day per habit (fixed-time mode: 1/day per habit).
- Deep link `larkspur://habit/{id}/checkin?src=smart` — handled by the app from 4.12.
  Older builds open the app home screen and ignore the `src` param.
- Notification category `SMART_NUDGE` (with "Snooze 1h" action) registered by the client from 4.12.

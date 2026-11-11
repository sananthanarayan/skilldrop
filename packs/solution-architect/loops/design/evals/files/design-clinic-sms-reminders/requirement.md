# Requirement: appointment reminders by text message

Ratified by the Brightwell Clinics product board on 2026-10-28.

Patients who book through the Brightwell booking app get a text message
reminder 24 hours before their appointment, and can reply STOP to opt out.

- Volume: about 18,000 appointments a day across 60 clinics; Monday morning
  is the peak, with about 4,000 reminders due in the 08:00-09:00 hour.
- A reminder must go out no later than 15 minutes after it falls due.
- A patient must never get two reminders for the same appointment.
- If an appointment is cancelled or moved, the old reminder must not be sent.
- STOP replies must take effect before the next reminder is sent to that number.
- The message may contain the clinic name and the time. It must not contain the
  reason for the visit or the clinician's name.

# REQ-031: Gates keep admitting fans when the venue internet drops

**Status:** Ratified by the Brindlemoor Live product council, 3 November 2026
**Owner:** Imogen Sallow-Reyes (Head of Venue Operations)

## Problem

At the Calderbrook Arena show on 17 October the venue's internet uplink dropped for 11 minutes during peak entry. Every handheld scanner stopped admitting, because each scan is a live call to the Admissions API. Queues backed up past the car park and we let roughly 2,000 people in unscanned.

## What must be true

1. **Entry continues through an uplink outage.** If the venue's internet uplink is down for up to 20 minutes, gates keep scanning and admitting at normal speed.
2. **One ticket, one entry.** A ticket must never let two people in, including through two different gates.
3. **Transfers keep working.** Fans can transfer a ticket to someone else up to the moment doors open. A transferred ticket gets a new QR code and the old QR code must stop working.
4. **Photo ID events.** For some events (about 1 in 10) gate staff check photo ID against the ticket holder's name before admitting.
5. **A scan feels instant.** Under 1 second from scan to green/red on the handheld.

## Scale

- Largest venue we sell for: 25,000 capacity, 40 entry gates, one handheld per gate.
- Doors open 90 minutes before the show. On past data, 70% of fans arrive in the last 30 minutes before the show.
- Tickets for a show: up to 25,000 QR codes, plus transfers (about 6% of tickets are transferred at least once).

## Out of scope

- Re-entry (we do not allow it).
- Box-office sales on the night.

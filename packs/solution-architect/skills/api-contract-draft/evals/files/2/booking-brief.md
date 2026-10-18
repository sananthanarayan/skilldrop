# Room bookings API — brief for the partner app team

Lanternfield Libraries runs 14 branches. Community groups book meeting rooms at the desk or by phone today. A partner team (Quillon Apps) is building a mobile app for groups and needs an API from us for bookings.

## What the app needs to do
- Show a group its bookings (upcoming and past).
- Make a booking for a room for a date and time range. Bookings are in 30-minute slots.
- Change the time of a booking.
- Cancel a booking. Please give them a DELETE that removes the booking and everything about it, so cancelled bookings don't clutter anything.
- Stop two groups getting the same room at the same time.

## Notes
- Rooms: the room catalogue (rooms, capacity, equipment, opening hours) already has an API owned by the Facilities team at /facilities/v2/rooms. Don't redesign it — just reference room IDs from it.
- Group accounts: groups sign in through our existing library account login (OAuth 2.0, already in place). Each group has a group_id.
- Volume, from the app team: "a group's list of bookings will only ever be a few items, so no paging needed."
- Last year: 38,400 bookings across all branches. The busiest group (Brenley Chess Club) made 412 bookings.
- The app is used on patchy mobile connections inside some branches; the app team says requests sometimes get re-sent when the connection drops.
- Deliverable: the OpenAPI file, saved as openapi.yaml, plus a short note of anything we need to decide.

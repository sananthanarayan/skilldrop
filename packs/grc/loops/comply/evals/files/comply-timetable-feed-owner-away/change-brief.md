# Change brief - move the open-data timetable feed to FeedHarbour (Tarnbrook Valley Buses)

**Go-live:** 20 November 2026
**Risk owner:** Tomasz Weller, Head of Digital (on leave until 24 November 2026)
**Project lead:** Annika Rowe

## What moves
Our public open-data feed - timetables, stop locations and fares - moves from our own server to
FeedHarbour (feedharbour.example), a hosted feed service. Journey-planner apps read the feed from
FeedHarbour from go-live.

No passenger or staff data goes to FeedHarbour. The feed is published under an open licence and
anyone can download it. We push to FeedHarbour with a single service account whose key is held in
our secrets vault.

FeedHarbour hosts in one region with no failover.

# Admissions: how it works today

Last updated: September 2026, by the platform team.

## Pieces

- **Ticketing service** (eu-west). Owns tickets, holders and transfers. Postgres, single primary (ADR-0003).
- **Admissions API** (eu-west). `POST /admit {qr}` looks the ticket up, checks it is valid and not already used, marks it used, and returns `{result, holder_name}`. Holder name is shown on the handheld for photo-ID events.
- **Handhelds.** Rugged Android handhelds with a built-in camera scanner, enrolled in our device management. They are wiped and re-enrolled between tours. Specs that matter: Android 14, Wi-Fi only (no SIM), 4 GB free storage, about 10 hours of battery.
- **Gate app.** A thin Android app: scan QR, call `/admit`, show green or red. No local storage today.

## QR codes

A QR code holds an opaque 16-byte random ticket token, base32-encoded. It carries no data of its own; it is only meaningful to the Admissions API. A transfer issues a new token and marks the old one void.

## Venue network

We rent venues. The venue provides Wi-Fi for our handhelds and an internet uplink. In the October incident the venue Wi-Fi stayed up and only the uplink failed; the venue's technical manager said that is the usual pattern, but we have seen whole-network failures at two smaller venues this year.

## Where things live

All services run in our cloud account in eu-west. Handhelds reach the Admissions API over the public internet with mutual TLS.

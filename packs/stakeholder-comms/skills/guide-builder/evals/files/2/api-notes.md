# partner API notes (Mirela — for whoever writes the real docs)

base url: https://api.tidewater-rentals.example/v2
auth: api key in a header, one key per partner. keys come from partner support (partners@tidewater-rentals.example)
all times are UTC, ISO 8601. money is integer cents, field names end in _cents.
rate limit: 120 req/min per key. over that -> 429 with a Retry-After header (seconds).

## GET /locations
list of rental locations. no params.
returns array of { id (string, "loc_..."), name (string), timezone (string, IANA name) }

## GET /slots
query params:
- location_id — required
- date — required, YYYY-MM-DD, in the location's local timezone
- item_type — optional, one of kayak | paddleboard | canoe. leave it off to get all three
returns array of { slot_id (string), starts_at, ends_at, item_type, available (int, how many are left) }
only the next 30 days are bookable. a date further out -> 422.

## POST /bookings
needs an Idempotency-Key header (any uuid). same key again within 24h returns the original booking, it does not make a second one.
body:
- slot_id — required
- quantity — required, 1 to 8
- customer — required object: name (required), email (required), phone (optional)
- partner_ref — optional, string, max 64 chars, the partner's own order id. we echo it back.
responses:
- 201 -> the booking object, see sample-booking.json. status starts as pending_payment.
- 409 slot_full -> not enough left in the slot. body { "error": "slot_full", "available": <int> }
- 422 validation_error -> body { "error": "validation_error", "fields": { "<field>": "<reason>" } }

## DELETE /bookings/{id}
cancels a booking. 204, no body.
free up to 48h before starts_at. after that -> 409, body { "error": "cancellation_window_closed" }

## webhook
we POST a booking.confirmed event to the partner's url once payment clears (usually seconds, can be a few minutes).
payload: { event, booking_id, partner_ref, occurred_at }
signed: HMAC-SHA256 of the raw request body, hex, in the X-Tidewater-Signature header. the secret is per partner.
retries: 5 attempts over about an hour, then we stop.

## changelog
- 2026-08-11 rate limit dropped to 60/min per key after the August incident. (haven't fixed the top of this doc yet)
- 2026-05-02 added partner_ref to POST /bookings and to the webhook payload

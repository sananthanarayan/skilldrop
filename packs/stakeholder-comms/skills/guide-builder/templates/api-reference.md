# {API / event stream name} — Developer reference

**Base URL:** `{https://api.example.com/v1}`
**Auth:** {e.g. "Bearer token in `Authorization` header; obtain via …"}
**Versioning:** {e.g. "URL-path `/v1`; breaking changes ship a new path. See Changelog."}
**Content type:** `application/json` unless stated.

## Conventions

These apply to every endpoint/event below — read once, don't repeat per item.

- **Errors** return this shape:
  ```json
  { "error": { "code": "string", "message": "human-readable", "details": {} } }
  ```
- **Pagination:** {e.g. "cursor-based: pass `?cursor=`; response includes `next_cursor` (null on last page)"}
- **Idempotency:** {e.g. "mutating calls accept an `Idempotency-Key` header; replays within 24h return the original result"}
- **Rate limits:** {e.g. "600 req/min/token; `429` with `Retry-After` when exceeded"}
- **Timestamps:** ISO 8601 UTC (`2026-05-26T14:30:00Z`).

---

## Endpoints

### `{METHOD} /{path}` — {one-line purpose}

{One sentence on when a consumer calls this.}

**Auth:** {required scope/role, or "none"}

**Path / query params**

| Param | In | Type | Required | Description |
|---|---|---|---|---|
| `{id}` | path | string | yes | {…} |
| `{limit}` | query | integer | no | {default, max} |

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `{field}` | string | yes | {…} |
| `{field}` | integer | no | {default} |

```json
{ "field": "value", "field2": 42 }
```

**Response `200`**

| Field | Type | Description |
|---|---|---|
| `{id}` | string | {…} |
| `{status}` | enum(`a`,`b`) | {…} |

```json
{ "id": "abc_123", "status": "a", "created_at": "2026-05-26T14:30:00Z" }
```

**Errors**

| Status | `error.code` | When |
|---|---|---|
| `400` | `invalid_request` | {…} |
| `404` | `not_found` | {…} |
| `409` | `conflict` | {…} |

```json
{ "error": { "code": "not_found", "message": "No resource with id abc_123" } }
```

---

## Events / messages

For each event a consumer subscribes to.

### `{event.name}` — {one-line: what happened}

- **Emitted when:** {the trigger}
- **Transport:** {e.g. "Kafka topic `orders.v1`" / "webhook POST to your callback URL" / "SNS topic ARN …"}
- **Delivery:** {e.g. "at-least-once; consumers MUST be idempotent on `event_id`"}
- **Ordering:** {e.g. "ordered per `partition_key = order_id`; no global order"}

**Payload**

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | string (uuid) | yes | dedup key |
| `occurred_at` | string (ISO 8601) | yes | when the fact happened (not when delivered) |
| `data.{field}` | string | yes | {…} |

```json
{
  "event_id": "evt_01HX...",
  "type": "{event.name}",
  "occurred_at": "2026-05-26T14:30:00Z",
  "data": { "order_id": "ord_123", "amount_cents": 4999 }
}
```

**Consumer notes:** {what a subscriber must handle — out-of-order arrival, schema evolution, poison messages}

---

## Error code catalog

| `error.code` | Meaning | Consumer action |
|---|---|---|
| `invalid_request` | malformed input | fix and retry; don't blind-retry |
| `rate_limited` | over quota | back off per `Retry-After` |
| `conflict` | idempotency or state clash | inspect existing resource |
| {…} | … | … |

## Changelog

| Version / date | Change | Breaking? |
|---|---|---|
| `v1` — {YYYY-MM-DD} | initial | — |
| {…} | … | yes/no |

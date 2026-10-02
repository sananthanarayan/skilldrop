# api-contract-draft reference — house conventions

These are defaults, not laws: deviate when the brief forces it, and log every deviation in the decisions table with its reason. An unlogged deviation is a bug in the contract.

## Naming & paths

- Resources are **plural nouns**: `/refunds`, `/payment-methods`. Kebab-case in paths, `snake_case` in JSON bodies.
- No verbs in paths. State changes are either a `PATCH` of a status field or a **sub-resource action collection** when the transition has its own data/lifecycle: ✅ `POST /orders/{id}/cancellations` — ❌ `POST /orders/{id}/cancel` (acceptable only when the action is truly fire-and-forget and modeling it as a resource adds nothing — log it).
- Nest **one level max** (`/customers/{id}/payment-methods`). Deeper relationships flatten to filters: ✅ `/invoices?customer_id=…` — ❌ `/customers/{id}/orders/{id}/invoices`.
- IDs are opaque strings with a type prefix in examples (`"ord_8f4k2m"`) — prefixed IDs make logs and support tickets self-describing.

## Errors — RFC 9457 `application/problem+json`

Every error response is a `Problem`:

```yaml
Problem:
  type: object
  required: [type, title, status, code]
  properties:
    type: { type: string, format: uri, description: "Stable URI identifying the error class" }
    title: { type: string, description: "Human summary, not for switching on" }
    status: { type: integer }
    code: { type: string, pattern: "^[a-z0-9_]+$", description: "Stable machine-readable code clients switch on" }
    detail: { type: string }
    errors: { type: array, description: "Field-level validation failures", items: { type: object, properties: { field: {type: string}, code: {type: string}, message: {type: string} } } }
```

- Enumerate **every 4xx the operation can produce**, each with its `code` values: `validation_failed`, `idempotency_key_reused`, `insufficient_funds`, …
- `5xx`: document `500` once globally with a generic Problem; never invent per-operation 500 variants.
- The `code` list is contract — adding one is additive; changing one is breaking.

## Pagination, filtering, sorting

- **Cursor pagination is the default**: request `?cursor=&limit=` (limit capped, cap stated), response `{ "data": [...], "next_cursor": "..." | null }`. Offset pagination only with a logged reason (e.g. "UI needs page numbers; dataset < 100k and stable").
- Every list endpoint paginates **from day one** — even "small" lists; retrofitting is a breaking change.
- Filters are query params named after the field (`?status=pending&created_after=…`). Sorting: `?sort=-created_at` (leading `-` = descending). Document which fields are filterable/sortable — "all of them" is never true.

## Idempotency & retries

- Every **unsafe POST** accepts `Idempotency-Key` (UUID, 24h retention stated). Same key + same body → replay the original response; same key + different body → `409` `idempotency_key_reused`.
- `PUT` and `DELETE` are idempotent by construction; `DELETE` of a missing resource is `404` first time, `404` every time (not `204` — log if you choose tombstone semantics instead).
- State the retry guidance in the operation description: which errors are retryable (`503`, `429` with `Retry-After`) and which never are (`4xx` except `429`).

## Versioning

- URL major version: `/v1/`. The policy sentence for `info.description`: *"Additive changes (new optional fields, new endpoints, new enum values where the field is documented as open) do not bump the version; removals, renames, type changes, and semantic changes do."*
- Mark enums **open or closed** explicitly (`x-extensible-enum` note or description) — clients must know whether to tolerate unknown values.
- Deprecation: `deprecated: true` + `Sunset` header mention + the replacement named in the description. No silent removals, ever.

## Field typing rules

| Concern | Rule |
|---|---|
| Money | Integer minor units + ISO-4217 `currency` field. Float money fails review. |
| Timestamps | `type: string, format: date-time`, UTC, ISO-8601. Field names end `_at`. |
| IDs | `type: string` opaque; never `integer` (leaks sequence, blocks resharding). |
| Enums | `enum: [...]` with every value, plus open/closed declared. |
| Free text | `maxLength` always — unbounded strings are a storage and abuse contract. |
| Booleans | Name as predicate: `is_default`, `has_failed`. Never tri-state a boolean — use an enum. |
| Optionality | `required` array on every object schema; absent ≠ null — pick one and state it. |
| Quantities | `minimum`/`maximum` on every numeric the business bounds. |

## Request/response shape separation

Per resource, three schemas minimum: `{Resource}` (response), `{Resource}CreateRequest`, `{Resource}UpdateRequest`. Server-set fields (`id`, `created_at`, `status` when machine-driven) appear **only** in the response schema. The update schema has no required fields (PATCH semantics) unless the business requires atomically-paired fields — log that decision.

## Event/webhook contracts (AsyncAPI-shaped)

- Channel names: `{domain}.{resource}.{event}` past-tense — `payments.refund.completed`.
- Payload: the same typing rigor; include `event_id` (UUID, for consumer dedupe), `occurred_at`, and a `schema_version`.
- Delivery semantics stated per channel: default **at-least-once** — consumers must dedupe on `event_id`; say so in the channel description.
- Webhooks out: HMAC signature header named, timestamp-skew window stated, retry schedule with backoff and a cap, and the consumer's expected 2xx contract ("respond 2xx within 10s; processing happens async on your side").

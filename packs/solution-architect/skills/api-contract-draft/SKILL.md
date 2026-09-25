---
name: api-contract-draft
description: Draft an OpenAPI 3.1 contract from a feature brief or story — resource-oriented paths, a full error catalog (RFC 9457), pagination/idempotency/versioning decided not deferred, examples on every operation, plus a decisions log so review argues choices instead of YAML. Use when the user wants to design an API, draft an OpenAPI/Swagger spec, define request/response shapes, or agree a contract between frontend/backend or two teams before code.
---

# api-contract-draft

Produces the contract *before* the code — a valid OpenAPI 3.1 document two teams can argue about and then build against in parallel. The YAML is half the artifact; the other half is the **decisions log**, because reviewers should debate "cursor vs offset pagination", not line 240. Designs new contracts; documenting an existing API is `guide-builder`'s job.

## How to respond

1. **Extract the resources from the brief.** Nouns the API owns, their relationships, and their lifecycle (who creates, what mutates, is delete real or soft). Ask at most 2 questions, and spend them on consumer shape ("who calls this — our SPA, partners, both?") and write semantics ("can a refund be requested twice?") — the two answers that change the contract most. Everything else: pick the convention from [`reference.md`](reference.md) and tag the choice `[assumption]` in the decisions log.

2. **Apply the house conventions** (full detail in [`reference.md`](reference.md)) — deviate only when the brief forces it, and log the deviation:
   - **Paths**: plural-noun resources, no verbs — ✅ `POST /refunds` ❌ `POST /createRefund`; nesting one level max, then flatten with filters
   - **Errors**: RFC 9457 `application/problem+json`, every 4xx the operation can return enumerated with a stable machine-readable `code`; no bare unexplained 500
   - **Pagination**: cursor-based by default (`cursor` + `limit`, response carries `next_cursor`); offset only with a logged reason
   - **Idempotency**: every unsafe POST takes `Idempotency-Key`; PUT/DELETE idempotent by construction
   - **Versioning**: URL major version (`/v1/`), additive changes don't bump, breaking changes do — the policy sentence goes in the spec's `description`
   - **Auth**: a `securityScheme` exists and every operation declares its requirement — including the explicitly-public ones

3. **Type every field like a reviewer will reject sloppiness.** Formats (`uuid`, `date-time`, `int64`), constraints (`maxLength`, `minimum`, `enum`, `pattern` for codes), required vs optional explicit on every schema, money as integer minor units (never float), timestamps UTC ISO-8601. A schema that's all bare `type: string` is a draft of a draft.

4. **Give every operation a realistic example** — request and the 2xx response, with values that look like production (`"cur_9f3k..."`, not `"string"`). Examples are where shape disagreements surface; they're the cheapest review tool in the document.

5. **Emit three sections in one message**:
   1. **Decisions log** — table of every contract decision (resource naming, pagination, error model, versioning, auth, the `[assumption]`s) with a one-line rationale each
   2. **The OpenAPI 3.1 YAML** — complete and valid: `info` (with the versioning policy), `servers`, `components.securitySchemes`, `components.schemas` (including the `Problem` schema), paths with examples
   3. **Open questions** — the unknowns that block freezing the contract, each with who can answer it
   Start from [`templates/openapi-skeleton.yaml`](templates/openapi-skeleton.yaml).

6. **For event/queue contracts** (the brief says "publish", "consume", "webhook out"): same discipline, AsyncAPI-shaped — channel name, payload schema with the same typing rigor, delivery semantics stated (at-least-once is the default; say it), and the consumer-retry/DLQ expectation in the channel description.

## Useful references in this skill

- [`reference.md`](reference.md) — the house conventions: naming, errors, pagination, idempotency, versioning, field-typing rules
- [`templates/openapi-skeleton.yaml`](templates/openapi-skeleton.yaml) — valid 3.1 starting point with `Problem` schema, security scheme, and one fully-worked resource

## Quality bar

- **The YAML validates.** OpenAPI 3.1, parseable, refs resolve. A contract that doesn't lint is a sketch.
- **Every operation enumerates its 4xx set** with stable `code` values a client can switch on. "400: Bad Request" alone is an unwritten error contract.
- **Every decision in the log has a rationale**, and every deviation from `reference.md` conventions is logged as a decision — silent deviation is how two services end up with three pagination styles.
- **Examples look like production data.** `"id": "string"` in an example means nobody pictured a real call.
- **No float money, no naked timestamps, no stringly-typed enums.** The three classic contract regrets, all preventable at draft time.
- **Unsafe operations state their idempotency story.** A reviewer can answer "what happens on retry?" for every POST.

## When to use this skill

- ✅ Designing a new API or new resource before implementation
- ✅ Frontend and backend (or two teams) need a contract to build against in parallel
- ✅ A story from `user-story-splitter` whose slice is "expose X over the API"
- ✅ Drafting the webhook/event contract a partner will consume

## When NOT to use this skill

- ❌ Documenting an API that already exists — that's `guide-builder` (reference archetype)
- ❌ Choosing REST vs GraphQL vs gRPC — that's `tech-comparison-matrix`; this skill starts after
- ❌ Reviewing a contract someone else drafted — `doc-critique` or `council-review`
- ❌ Generating server/client code from the spec — hand the frozen contract to the codegen tool

## Anti-patterns to avoid

- ❌ **RPC verbs in paths** (`/getUser`, `/doRefund`). The resource model is the contract's spine; verbs mean it was never designed.
- ❌ **The 200-with-error-body.** `200 {"success": false}` breaks every client's error handling; failures use failure status codes.
- ❌ **Deferring pagination "until we need it".** Retrofitting pagination onto a shipped list endpoint is a breaking change; decide it at draft.
- ❌ **One giant shared schema** reused for create-request, update-request, and response, with half the fields "ignored on input". Separate the shapes; optionality differs.
- ❌ **YAML without the decisions log.** Reviewers nitpick property names and never see that offset pagination or float money slipped through.
- ❌ **Contract churn after parallel build starts.** Once both sides build, every change is a versioned change — the open-questions section exists to drain *before* freezing, not after.

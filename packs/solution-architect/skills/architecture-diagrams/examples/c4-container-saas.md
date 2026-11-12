# Example: C4 container diagram for a SaaS app

**Prompt the user gave:** *"Give me a C4 container view of a B2B SaaS app — single tenant per database schema, with Stripe for billing."*

**Response:**

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

LAYOUT_WITH_LEGEND()

title Container diagram — Acme SaaS

Person(admin, "Tenant admin", "Configures workspace, invites users")
Person(user, "End user", "Day-to-day usage")

System_Boundary(saas, "Acme SaaS") {
    Container(web, "Web app", "Next.js", "Tenant-aware UI")
    Container(api, "API", "Node, Fastify", "REST/JSON, business logic")
    Container(worker, "Worker", "Python, Celery", "Async jobs, billing sync")
    ContainerDb(db, "Tenant DB", "Postgres", "One schema per tenant")
    ContainerDb(cache, "Cache", "Redis", "Session + rate-limit")
    ContainerQueue(queue, "Job queue", "SQS", "Async work")
}

System_Ext(stripe, "Stripe", "Subscriptions + invoicing")
System_Ext(idp, "Auth0", "OIDC identity provider")
System_Ext(post, "Postmark", "Transactional email")

Rel(admin, web, "Uses", "HTTPS")
Rel(user, web, "Uses", "HTTPS")
Rel(web, idp, "Auth (OIDC)", "HTTPS")
Rel(web, api, "Calls", "HTTPS / JSON")
Rel(api, db, "Reads/writes (per-tenant schema)", "SQL")
Rel(api, cache, "Reads/writes", "RESP")
Rel(api, queue, "Publishes", "HTTPS")
Rel(worker, queue, "Consumes", "HTTPS")
Rel(worker, db, "Reads/writes", "SQL")
Rel(worker, stripe, "Syncs subscriptions", "HTTPS")
Rel(worker, post, "Sends mail", "HTTPS")
Rel(stripe, api, "Webhooks (invoice.*)", "HTTPS")
@enduml
```

**Design notes:**

- **One schema per tenant** is shown via the relationship label on `api -> db` — keeps the diagram clean while making the isolation strategy reviewable.
- **Webhooks back from Stripe** (note arrow reversal) — a common trip-up; if it's missing, billing state drift is hard to debug.
- **Worker hits external services**, not the API — avoids the API being a chokepoint for outbound integrations and keeps retries close to the queue.
- For **context-level** (one box per system, no internals), drop everything inside `System_Boundary` and replace with one `System(saas, ...)`. For **component-level** (one container's internals), drill into `api` with `C4_Component.puml`.

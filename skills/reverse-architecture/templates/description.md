# Architecture Description

> Output shape: feeds directly into `/architecture-diagrams` if the user wants to switch notation.
> Source: reverse-engineered from `{repo / files}` on `{YYYY-MM-DD}`.

## What the system is
{One sentence.}

## Actors and external systems
- `{User type}` interacts via `{channel}` — e.g. browser, mobile app, partner API.
- `{External system}` — relationship: `{consumer / provider / both}`.

## Containers (the deployables)
For each, one line:

- **`{name}`** — `{language/runtime}` — purpose: `{one phrase}` — runs on: `{platform if known}`.

## Datastores and state
- **`{name}`** — `{engine}` — owned by: `{service name}` — purpose: `{e.g. "checkout transactional store"}`.

## Inbound surface
- Public ingress: `{HTTPS via {ALB | CloudFront | API Gateway | Ingress controller}}` — routes to: `{services}`.
- Authentication: `{mechanism, e.g. "Cognito JWT", "Auth0 OIDC", "internal session cookie"}`.

## Internal traffic
- `{service A} → {service B}` — `{protocol}` — purpose: `{what call is being made}`.
- `{service C} ⇢ {queue} ⇢ {worker}` — `{async, e.g. via Kafka topic "orders.created"}`.

## External dependencies (third-party SaaS)
- `{vendor}` — used for: `{purpose}` — called from: `{service}`.

## Deployment topology (if known)
- Cloud: `{AWS | Azure | GCP | on-prem | mixed}`.
- Regions: `{list}`.
- Compute: `{EKS cluster name / ECS service / Lambda functions / VMs}`.
- Network: `{VPC layout if discernible}`.

## Trust boundaries
- {Where does data cross a security/trust boundary — e.g. "client → API Gateway", "internal → vendor", "account A → account B"}.

## Known unknowns
- {Anything in the extraction's "What I couldn't see" — verbatim, so the next reader knows the diagram's limits.}

---

## Drawing hints for the diagram

- **Direction:** `LR` (request flow reads left-to-right) for container level, `TD` (deployment stack) for deployment level.
- **Group by:** {VPC | cluster | account | region — whichever boundary is most load-bearing in this system}.
- **Edge style:** solid for sync, dashed for async.
- **Label edges that cross a boundary** (trust, network, account) — that's where the value of the diagram concentrates.
- **Cap at ~15 nodes.** If this description has more, split — typically into `{Frontend stack}` and `{Backend stack}`, or by domain.

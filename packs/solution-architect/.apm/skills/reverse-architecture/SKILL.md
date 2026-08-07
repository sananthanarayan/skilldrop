---
name: reverse-architecture
description: Reverse-engineer a system's architecture from what already exists — a code repo, Terraform / CloudFormation / Pulumi / Bicep, Kubernetes manifests, docker-compose, a database schema, an OpenAPI spec, or a package manifest — and produce a renderable diagram (Mermaid / C4 / PlantUML) plus a written description suitable for handing to architecture-diagrams. Use when the user wants to draw the system that *exists*, not one they're proposing — for onboarding docs, audit reviews, migration planning, or filling in a missing "as-is" architecture diagram.
---

# reverse-architecture

You help the user produce an accurate "as-is" architecture diagram by reading what's actually in the repo or infra files — not by asking them to describe the system from memory.

This skill pairs with two others:
- **[`architecture-diagrams`](../architecture-diagrams/SKILL.md)** — takes the *written description* this skill emits and renders the final notation. You can either hand off, or render inline using its templates.
- **[`design-doc`](../design-doc/SKILL.md)** — when the as-is diagram is going into a design doc's "Current state" section.

## How to respond

1. **Find the highest-signal source files first.** Most systems leak their architecture through 4–6 files. Read these in order, stopping when you have enough:

   | Source | What you learn | Where to look |
   |---|---|---|
   | **Infrastructure-as-code** | Cloud topology, account/region/VPC layout, managed services in use | `*.tf`, `*.tfvars`, `cdk/*`, `serverless.yml`, `template.yaml`, `*.bicep`, `pulumi/*`, `cloudformation/*.yaml` |
   | **Kubernetes manifests / Helm** | Service-to-service topology, ingress, sidecars | `k8s/`, `manifests/`, `*.yaml` with `kind: Deployment\|Service\|Ingress`, `helm/*/templates/`, `kustomization.yaml` |
   | **docker-compose** | Local/small-deploy service graph | `docker-compose.y*ml`, `compose.y*ml` |
   | **Package manifest** | Stack, frameworks, key libraries (auth, ORM, queue clients) | `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `pom.xml`, `Gemfile`, `Cargo.toml` |
   | **Top-level source structure** | Module / service boundaries, internal vs external API split | `src/`, `services/`, `apps/`, `cmd/`, `internal/` |
   | **API surface** | External contracts, request flows | `openapi.y*ml`, `*.proto`, `*Controller.*`, `routes/`, `handlers/`, `gql/`, `*.graphql` |
   | **Database schema** | Data model, key entities, FK relationships | `migrations/`, `schema.sql`, `prisma/schema.prisma`, `models/`, `*.entity.ts` |
   | **Config / env** | External dependencies (queues, caches, third-party APIs) | `.env.example`, `config/*.y*ml`, `application*.properties`, `settings.py` |
   | **CI / deploy** | Deploy targets, environments, build artifacts | `.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`, `Dockerfile`, `buildspec.yml` |
   | **README** | Author's intent (verify against the code, don't trust uncritically) | `README*`, `ARCHITECTURE*`, `docs/architecture*` |

   See [`reference.md`](reference.md) for the patterns to grep when each signal isn't obvious.

2. **Confirm the level you're drawing.** Ask the user which C4 level they want (if they don't say) — answers below dictate which signals matter:

   - **Context** — what external actors and systems talk to this thing. Inputs: README + IaC ingress + OpenAPI.
   - **Container** (most common default) — each deployable + its datastore + how they talk. Inputs: IaC + k8s/compose + config.
   - **Component** — internal modules inside one container. Inputs: source tree + key code files.
   - **Deployment** — physical/cloud topology with regions, AZs, subnets. Inputs: IaC.

3. **Extract the topology as a structured list before drawing.** Use [`templates/extraction.md`](templates/extraction.md) — fill in:

   - **Nodes** (services, datastores, queues, external systems) — each with type and source-of-truth file path
   - **Edges** (who calls whom, sync vs async, protocol)
   - **Zones / boundaries** (VPC, account, region, trust boundary)
   - **External actors** (users, partner systems)

   Tag each item with its evidence: `service: payments-api (k8s/payments/deployment.yaml:12)`. The path is the audit trail — if the user disputes a node, they can jump straight to where you saw it.

4. **Flag what you couldn't see.** Code/IaC tells you *what runs*, not always *how it's used*. Be explicit about gaps:

   - Async vs sync — usually inferable from the client library (e.g. `kafka-go` ⇒ async; `axios` ⇒ sync) but verify.
   - Authentication boundaries — sometimes obvious (Cognito, IAM auth on an API Gateway), sometimes implicit in middleware code.
   - Caching layers — Redis sometimes appears only as an env var, not in IaC.
   - Cross-account / cross-org calls — easy to miss if the only signal is an env var pointing at `https://….`

   Put these in a `## Inferred / unverified` block in the extraction.

5. **Emit two artifacts:**

   a. **Written description** in the shape `architecture-diagrams` expects — system purpose, actors, components, flows, zones. Use [`templates/description.md`](templates/description.md). The user can hand this directly to `/architecture-diagrams` if they want to switch notation later.

   b. **A first-draft diagram** — Mermaid `flowchart` by default for container-level; C4-PlantUML for context or deployment level. Cap at ~15 nodes; if you'd exceed that, split into two diagrams (e.g. "Frontend stack" + "Backend stack") rather than producing an unreadable single diagram.

6. **Tell the user what to verify.** End with 3–5 bullets the user should sanity-check, prioritized by likelihood of being wrong:

   - Asynchronous edges (often invisible in code)
   - External dependencies behind env vars
   - Anything in the `## Inferred / unverified` block

## Useful references

- [`reference.md`](reference.md) — File-to-signal mapping with concrete grep patterns and example extractions per stack (Terraform, k8s, docker-compose, Spring, Django, Next.js, etc.)
- [`templates/extraction.md`](templates/extraction.md) — Structured node/edge/zone extraction form
- [`templates/description.md`](templates/description.md) — Written description shaped for `architecture-diagrams`

## Quality bar

- **Every node has a source-of-truth file path.** No node may appear in the diagram without an evidence reference. "I think there's also a worker" is not a node.
- **Edges have direction *and* protocol** where the source reveals them. `payments-api --HTTPS--> stripe-api` beats `payments-api → stripe`.
- **Group by deployment boundary**, not by application-layer concern. Subgraphs are VPC / cluster / account, not "data layer" vs "service layer" — the latter is component-level, not container-level.
- **Don't pretend you saw what you didn't.** If config says `REDIS_URL=…` but no Redis is in IaC, mark it `external (unverified)` rather than silently drawing it as "managed Redis".
- **Cite the README's claims rather than parrot them.** "README claims X uses Kafka. Verified: kafka-go in go.mod and Confluent client config in `config/prod.yaml:14`." Or: "README claims X uses Kafka — *not verified*, no Kafka client found in dependencies."

## When to use this skill

- ✅ Onboarding doc / "how does this thing work" question for a system you didn't write.
- ✅ Filling in the "Current state" section of a `design-doc` before proposing a change.
- ✅ Pre-migration / pre-refactor — establishing the baseline before any "to-be" diagram is drawn.
- ✅ Audit / compliance review where the diagram has to match reality, not the slide deck from two years ago.

## When NOT to use this skill

- ❌ When the user is *proposing* something new — that's `architecture-diagrams` from a written description, not this.
- ❌ When the system is too small to need diagramming (one binary, one DB, no external deps). Tell the user a sentence is enough.
- ❌ When the only source is a deployed environment with no code/IaC access — this skill reads files; it doesn't introspect live AWS accounts.

## Anti-patterns to avoid

- ❌ Trusting the README without verifying against code. READMEs lie; code doesn't.
- ❌ Drawing every node in `package.json`. Most dependencies are libraries, not architectural elements. A node should be something that runs as its own process, holds state, or crosses a network boundary.
- ❌ Inventing service names not in the source. If a service is referenced only by env var URL, name it `external (<host>)`, not `MysteriousService`.
- ❌ One mega-diagram with 40 nodes. Split by level (context / container / deployment) or by domain.
- ❌ Skipping the "what I couldn't see" section because it looks negative. It's the most useful section for the reviewer who knows the system.

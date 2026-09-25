# Architecture Extraction

> Reverse-engineered from: `{repo path or set of input files}`
> Level: `{context | container (default) | component | deployment}`
> Extracted: `{YYYY-MM-DD}`

## System purpose
{One sentence — what the system does. From README if available, verified against code.}

## External actors
- `{Actor name}` — {role, e.g. "end user", "partner system", "admin tool"} — _evidence: `{file path}`_

## Nodes

For each: name · type · stack/tech · evidence path.

| # | Name | Type | Stack | Evidence |
|---|---|---|---|---|
| 1 | `{name}` | service / job / queue / cache / db / external | {language/runtime} | `{path/to/file:line}` |
| 2 | | | | |

**Type vocabulary:**
- `service` — long-running process serving requests
- `job` — periodic / triggered batch
- `worker` — long-running consumer of a queue
- `queue` — Kafka topic, SQS queue, RabbitMQ exchange, etc.
- `db` — datastore (Postgres, Mongo, Dynamo, …)
- `cache` — Redis, Memcached, in-memory
- `object-store` — S3, GCS, blob storage
- `external` — third-party SaaS or system outside the codebase

## Edges

For each: source → target · protocol · sync/async · evidence.

| # | From | To | Protocol | Sync/Async | Evidence |
|---|---|---|---|---|---|
| 1 | `{node}` | `{node}` | HTTPS / gRPC / Kafka / SQS / SQL / Redis | sync / async | `{path}` |
| 2 | | | | | |

## Zones / boundaries
- **{Zone name}** ({type: VPC / account / region / cluster / trust boundary}) — contains: `{node, node, node}` — _evidence: `{path}`_

## Datastores (detail)
- `{db name}` — {engine + version} — owns: `{top 5 tables/entities}` — _evidence: `{schema file}`_

## Inferred / unverified
Things present in code/config but not fully confirmed. The diagram marks these with `?` or dashed edges.

- `{node or edge}` — _signal: `{what made you think it exists}`_ — _why unverified: `{what's missing}`_

## What I couldn't see
- {e.g. "No IaC in repo — deployment topology unknown"}
- {e.g. "No load-test artifacts — actual scale targets unknown"}
- {e.g. "Async paths suspected (kafka-go in go.mod) but no topic config found"}

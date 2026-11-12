# reverse-architecture — file-to-signal reference

A cheat sheet for what to read first when reverse-engineering an architecture. Use this when the obvious places (README, top-level dirs) aren't enough.

## Triage: 5-minute scan

Before reading anything deeply, run these in order:

```bash
# 1. The tree (depth 2 — surface-level structure)
find . -maxdepth 2 -type d -not -path '*/.*'

# 2. Look for the architecture-revealing files
ls README* ARCHITECTURE* docs/architecture* 2>/dev/null
find . -maxdepth 3 -name 'docker-compose*.y*ml' -o -name 'serverless.yml' -o -name 'template.yaml' -o -name 'Dockerfile' 2>/dev/null
find . -maxdepth 4 -name '*.tf' -o -name '*.bicep' -o -name 'kustomization.yaml' 2>/dev/null | head -20

# 3. The stack
ls package.json pyproject.toml requirements.txt go.mod pom.xml Gemfile Cargo.toml 2>/dev/null
```

What you find dictates the next step. If `docker-compose.yml` exists at the root, that's the highest-signal file. If you have Terraform, start there.

## Per-source patterns

### Terraform / OpenTofu

```bash
# What managed services are in use?
grep -rh '^resource "' --include='*.tf' | sort -u

# What's the data plane?
grep -rh 'aws_rds\|aws_dynamodb\|aws_elasticache\|aws_s3\|aws_sqs\|aws_sns\|aws_kinesis\|aws_msk' --include='*.tf'

# Ingress / public surface
grep -rh 'aws_lb\|aws_apigateway\|aws_cloudfront\|aws_route53_record' --include='*.tf'

# Networking
grep -rh 'aws_vpc\|aws_subnet\|aws_security_group\|aws_vpc_peering' --include='*.tf'
```

For Azure: `azurerm_*`. For GCP: `google_*`. For Pulumi/CDK: read the `*.ts` / `*.py` directly — the resource constructors are the architectural signal.

### Kubernetes / Helm

```bash
# All services and deployments at a glance
grep -rE '^kind:\s+(Deployment|StatefulSet|Service|Ingress|CronJob|Job)\b' --include='*.yaml' --include='*.yml' .

# Sidecars (auth, mesh, log shipping)
grep -rB2 '- name:' --include='*.yaml' | grep -E 'istio-proxy|linkerd-proxy|envoy|fluent-bit|vector|otel-collector'

# Ingresses ⇒ external surface
grep -rB1 'host:' --include='*.yaml' | grep -A1 'kind: Ingress\|kind: VirtualService'
```

In Helm charts, `values.yaml` often has more architecture signal than the templates — features get toggled on/off there.

### docker-compose

The service graph IS the file. Read top to bottom; pay attention to:

- `services:` — each is a node.
- `depends_on:` — directional edge (startup, not necessarily runtime).
- `networks:` — zones.
- `ports:` — `"x:y"` means external, no `ports:` means internal-only.
- `image:` — datastores (`postgres`, `redis`, `rabbitmq`) become cylinder nodes.

### Package manifests

These tell you the *stack*, not the topology. Use them to translate generic boxes into specific tech:

| Dep seen | What it means architecturally |
|---|---|
| `axios`, `node-fetch`, `requests`, `httpx`, `reqwest` | Sync HTTP calls to external services |
| `kafkajs`, `confluent-kafka`, `kafka-go`, `sarama` | Kafka producer/consumer — async edge |
| `bullmq`, `celery`, `sidekiq`, `rq`, `dramatiq` | Job queue — worker pattern |
| `redis`, `ioredis`, `redis-py` | Redis cache / pub-sub |
| `pg`, `psycopg`, `pgx`, `gorm`, `sqlalchemy`, `prisma`, `typeorm` | Postgres |
| `mongodb`, `mongoose`, `pymongo` | MongoDB |
| `@aws-sdk/*`, `boto3`, `aws-sdk-go` | Look for which clients are imported — that's the AWS surface |
| `passport`, `next-auth`, `auth0`, `clerk`, `oidc-client` | Auth provider |
| `@grpc/grpc-js`, `grpcio`, `connect-go` | gRPC edges |
| `socket.io`, `ws`, `websockets` | WebSocket edges — long-lived connection |
| `stripe`, `twilio`, `sendgrid`, `posthog` | External SaaS dependency |

### Source tree

Look at the depth-1 and depth-2 directories. Common patterns:

- `services/<name>/` or `apps/<name>/` — monorepo with multiple deployables; each `<name>` is a container.
- `cmd/<binary>/` (Go) — each subdir is a separate binary, each is a container.
- `src/`, `lib/`, `internal/` — single deployable; you're looking at component-level structure.
- `packages/` (npm/pnpm/yarn workspaces) — libraries shared between containers, not containers themselves. Don't draw them at container level.

### OpenAPI / proto / GraphQL

```bash
find . -name 'openapi.y*ml' -o -name '*.proto' -o -name '*.graphql' -o -name 'schema.graphql' | head
```

- OpenAPI `paths:` → public API surface — list 5–10 example operations to characterize the service in one line.
- `.proto` `service { rpc ... }` → gRPC service definition.
- GraphQL `type Query` / `type Mutation` → frontend → backend contract.

### Database schema

```bash
find . -name 'schema.prisma' -o -name 'schema.sql' -o -path '*/migrations/*.sql' -o -path '*/models/*' | head -20
```

For the diagram, the key signals are:

- Which entities exist (top 10–15 tables).
- Which FK relationships span what would otherwise be two separate services — that's a sign of *coupling* worth showing on the diagram.
- Whether there are obvious tenancy columns (`tenant_id`, `org_id`) — single-tenant vs multi-tenant matters at container level.

### Config / env

```bash
# External hostnames in env config
grep -rh 'https://\|http://' .env.example config/ application*.properties 2>/dev/null | grep -v localhost | sort -u
```

These are often the *only* signal that an external SaaS is in the loop.

### CI / deploy

```bash
# Where does this thing actually deploy to?
grep -rE 'aws-region|gcp-project|kubeconfig|cluster:|environment:' .github/workflows/ .gitlab-ci.yml 2>/dev/null
```

Useful for the deployment-level diagram (regions, environments).

## Common gotchas

- **Mono-repos vs. multi-repo:** if you see `services/*` directories each with their own `package.json`, treat each as a separate container. Don't merge them.
- **Backwards Helm templates:** Helm `_helpers.tpl` and `values.yaml` are where the real config lives; the `.yaml` templates are just substrate.
- **CDK / Pulumi:** the constructor calls (`new lambda.Function(…)`, `new aws.s3.Bucket(…)`) ARE the IaC. Read them like resource blocks.
- **Service mesh sidecars:** if every pod has an `istio-proxy` container, don't draw it on every node — call it out once in the description and assume it.
- **Library vs service:** something with no `Dockerfile`, no `main` entrypoint, and no `package.json` `bin` field is probably a library, not a container.

## When the code is missing signal

Sometimes you just don't have enough. Be explicit:

> "I can see the API services and the Postgres, but no IaC is in the repo and there's no docker-compose, so I can't tell where this runs (Kubernetes? ECS? bare VMs?) or what the ingress / load balancer is. The diagram below shows containers only; deployment topology is `unknown` pending IaC or a screenshot of the cloud console."

The diagram with explicit gaps is more useful than a diagram that pretends.

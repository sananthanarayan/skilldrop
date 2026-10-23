# Brief: Runbook

> Target downstream skill: `runbook-generator`

## Service
- **Name:** {service-name} [explicit|implied|inferred|missing]
- **One-line purpose:** {what it does} [explicit|implied|inferred|missing]
> "{verbatim snippet}"

## Owners
- **Team:** {team name — role-based, not individual} [explicit|implied|inferred|missing]
- **Primary on-call rotation:** {rotation name / PagerDuty schedule} [explicit|implied|inferred|missing]
- **Escalation chain:** {who's next if primary is unavailable} [explicit|implied|inferred|missing]

## Tech stack
- **Language / runtime:** {e.g. Go 1.22, Python 3.12} [explicit|implied|inferred|missing]
- **Storage:** {e.g. Postgres 15, Redis, S3} [explicit|implied|inferred|missing]
- **Message brokers / queues:** {e.g. Kafka, SQS — or `n/a`} [explicit|implied|inferred|missing]
- **External dependencies:** {APIs, vendor services} [explicit|implied|inferred|missing]

## Deployment surface
- **Platform:** {Kubernetes / ECS / Lambda / VMs} [explicit|implied|inferred|missing]
- **Namespace / cluster / region:** {coordinates} [explicit|implied|inferred|missing]
- **Deploy mechanism:** {GitHub Actions / ArgoCD / manual / …} [explicit|implied|inferred|missing]

## Known failure modes (the "common 5")
- {Failure 1 — symptom + suspected cause if known} [explicit|implied|inferred|missing]
- {Failure 2}
- {Failure 3}
- {Failure 4}
- {Failure 5}

## Existing dashboards / alerts referenced in source
- {Dashboard URL or name} [explicit|implied|inferred|missing]
- {Alert name → page severity}

## SLOs (if any)
- {Metric → target, e.g. "p99 latency < 200ms"} [explicit|implied|inferred|missing]

---

## 🚩 Missing for downstream
- {field: why it matters}
- {e.g. "No owner team — runbook-generator refuses to draft without current ownership"}

# AWS-flavoured Mermaid starter

Mermaid doesn't ship native AWS icons, but emojis + clear naming get you 80% of the visual clarity for free, and the diagram still renders anywhere Markdown does.

```mermaid
flowchart TB
    Internet([🌐 Internet])

    subgraph AWS["☁️ AWS — us-east-1"]
        subgraph VPC["🛡️ VPC 10.0.0.0/16"]
            subgraph Public["Public subnet"]
                ALB[🔀 ALB]
            end
            subgraph Private["Private subnet"]
                ECS1[📦 ECS web]
                ECS2[📦 ECS worker]
            end
            subgraph DataZone["Data"]
                RDS[(🐘 RDS Postgres)]
                Redis[(⚡ ElastiCache)]
            end
        end
        S3[(🪣 S3 assets)]
        SQS{{📨 SQS queue}}
    end

    Internet --> ALB --> ECS1
    ECS1 --> Redis
    ECS1 --> RDS
    ECS1 --> SQS --> ECS2
    ECS2 --> RDS
    ECS1 -.reads.-> S3
```

## Service → emoji cheat sheet

| Service | Emoji | Service | Emoji |
|---|---|---|---|
| EC2 / ECS / Fargate | 📦 | RDS / Aurora | 🐘 |
| Lambda | λ or ⚡ | DynamoDB | 🗄️ |
| S3 | 🪣 | ElastiCache | ⚡ |
| ALB / NLB / API GW | 🔀 | CloudFront | 🌍 |
| SQS / SNS | 📨 | EventBridge | 🚌 |
| Cognito / IAM | 🔐 | KMS | 🔑 |
| Route 53 | 🧭 | CloudWatch | 📊 |

## Tips

- Use `subgraph` to make VPC → subnet → service nesting visible — it's the single biggest readability win.
- Mark public vs private subnets explicitly.
- Dotted arrows (`-.label.->`) for async / read-only / observability paths so the primary request path stays prominent.
- For multi-region, draw one region in detail and a thin "replica" box for the others, with a labeled arrow between them.

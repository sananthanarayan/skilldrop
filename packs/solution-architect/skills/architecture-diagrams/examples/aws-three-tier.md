# Example: Three-tier web app on AWS

**Prompt the user gave:** *"Draw me a three-tier web app on AWS with an ALB, two ECS services (web + worker), and an RDS Postgres backend."*

**Response:**

```mermaid
flowchart TB
    Internet([🌐 Internet])

    subgraph AWS["☁️ AWS us-east-1"]
        subgraph VPC["🛡️ VPC 10.0.0.0/16"]
            subgraph PubSub["Public subnet"]
                ALB[🔀 Application Load Balancer]
            end
            subgraph PrivSub["Private subnet"]
                Web[📦 ECS web service]
                Worker[📦 ECS worker service]
            end
            subgraph DataSub["Data subnet"]
                RDS[(🐘 RDS Postgres Multi-AZ)]
            end
        end
        SQS{{📨 SQS jobs}}
        S3[(🪣 S3 user uploads)]
    end

    Internet -->|HTTPS 443| ALB
    ALB -->|HTTP 8080| Web
    Web -->|SQL| RDS
    Web -->|enqueue| SQS
    Worker -->|dequeue| SQS
    Worker -->|SQL| RDS
    Web -.signed URLs.-> S3
```

**Design notes:**

- **Why two ECS services and not one?** Long-running background work (image resize, email, exports) needs its own scaling profile and shouldn't share CPU with request-serving containers.
- **RDS Multi-AZ** for automatic failover — single-AZ is fine for dev/test but rarely acceptable in production for a three-tier app.
- **Uploads bypass the API** via S3 pre-signed URLs to avoid a 100 MB file streaming through ECS containers.
- **No NAT gateway shown** — add one (or VPC endpoints) if the private subnet containers need to reach S3/SQS over the AWS network without a public IP.

**Want to extend?** Common follow-ups: add CloudFront in front of ALB, add ElastiCache Redis for sessions, add WAF rules, split into multi-region active/passive.

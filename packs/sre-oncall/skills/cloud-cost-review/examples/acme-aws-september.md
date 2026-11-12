# Example: Acme, AWS, September vs August 2026

Acme's platform lead shared two months of a daily legacy CUR export and asked: "Where are we wasting money, and why did September go up?"

## Input

[`acme-cur-2026-08-09.csv`](acme-cur-2026-08-09.csv): 1,084 synthetic line items, 2026-08-01 to 2026-09-30, daily. Two accounts: 111111111111 (prod) and 222222222222 (staging). The ownership tag is `team`. It holds a subset of the real CUR columns: the ones the script maps, plus `resourceTags/user:team` and `resourceTags/user:env`. All amounts are made up for illustration and are not AWS list prices.

## Command

```bash
python3 scripts/cost_summary.py examples/acme-cur-2026-08-09.csv --tag team --top 8 --out out/summary.md
```

## Script output (real, unedited)

```markdown
# Cloud cost summary: 2026-09 vs 2026-08

Format: aws-cur. Days with data: 2026-09=30, 2026-08=31. Change basis: monthly totals. Amounts are usage line items at effective cost; tax, credits, refunds and commitment fees are listed separately.

| | 2026-09 | 2026-08 | Change |
|---|---:|---:|---:|
| Usage cost | $7,560.14 | $6,078.69 | $1,481.45 (+24.4%) |
| Commitment fees | $190.80 | $197.16 | |
| Tax | $455.12 | $412.37 | |
| Credits and discounts | -$250.00 | -$250.00 | |
| Excluded (savings plan negation) | -$276.48 | -$285.70 | |

## By service

| Service | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| Amazon Elastic Compute Cloud | $3,934.83 | $2,690.71 | $1,244.13 | +46.2% | 52.0% |
| Amazon Simple Storage Service | $1,149.63 | $977.50 | $172.13 | +17.6% | 15.2% |
| AmazonCloudWatch | $1,040.76 | $925.58 | $115.19 | +12.4% | 13.8% |
| AWS Data Transfer | $808.51 | $837.63 | -$29.12 | -3.5% | 10.7% |
| Amazon Relational Database Service | $619.20 | $639.84 | -$20.64 | -3.2% | 8.2% |
| Amazon Virtual Private Cloud | $7.20 | $7.44 | -$0.24 | -3.2% | 0.1% |

## By account / project / subscription

| Account | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 | $6,778.79 | $5,271.30 | $1,507.49 | +28.6% | 89.7% |
| 222222222222 | $781.35 | $807.39 | -$26.04 | -3.2% | 10.3% |

## By region

| Region | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| us-east-1 | $7,560.14 | $6,078.69 | $1,481.45 | +24.4% | 100.0% |

## Top movers (service / usage type)

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| Amazon Elastic Compute Cloud / USE1-NatGateway-Bytes | $1,657.73 | $559.05 | $1,098.68 | +196.5% | 21.9% |
| Amazon Simple Storage Service / TimedStorage-ByteHrs | $1,149.63 | $977.50 | $172.13 | +17.6% | 15.2% |
| Amazon Elastic Compute Cloud / USE1-DataTransfer-Regional-Bytes | $457.33 | $294.16 | $163.17 | +55.5% | 6.0% |
| AmazonCloudWatch / USE1-DataProcessing-Bytes | $1,040.76 | $925.58 | $115.19 | +12.4% | 13.8% |
| Amazon Elastic Compute Cloud / USE1-EBS:SnapshotUsage | $171.17 | $138.75 | $32.42 | +23.4% | 2.3% |
| AWS Data Transfer / USE1-DataTransfer-Out-Bytes | $808.51 | $837.63 | -$29.12 | -3.5% | 10.7% |
| Amazon Elastic Compute Cloud / USE1-BoxUsage:r6i.4xlarge | $725.76 | $749.95 | -$24.19 | -3.2% | 9.6% |
| Amazon Elastic Compute Cloud / USE1-BoxUsage:m6i.2xlarge | $842.06 | $865.32 | -$23.26 | -2.7% | 11.1% |

## Top resources by current cost

| Resource / service / usage type | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| nat-0c9prod / Amazon Elastic Compute Cloud / USE1-NatGateway-Bytes | $1,657.73 | $559.05 | $1,098.68 | +196.5% | 21.9% |
| acme-logs-archive / Amazon Simple Storage Service / TimedStorage-ByteHrs | $1,149.63 | $977.50 | $172.13 | +17.6% | 15.2% |
| i-0b7stgbatch / Amazon Elastic Compute Cloud / USE1-BoxUsage:r6i.4xlarge | $725.76 | $749.95 | -$24.19 | -3.2% | 9.6% |
| arn:aws:rds:us-east-1:111111111111:db:payments-primary / Amazon Relational Database Service / USE1-InstanceUsage:db.r6g.2xlarge | $619.20 | $639.84 | -$20.64 | -3.2% | 8.2% |
| i-0a1c3web02 / Amazon Elastic Compute Cloud / USE1-BoxUsage:m6i.2xlarge | $276.48 | $285.70 | -$9.22 | -3.2% | 3.7% |
| i-0a1c3web03 / Amazon Elastic Compute Cloud / USE1-BoxUsage:m6i.2xlarge | $276.48 | $285.70 | -$9.22 | -3.2% | 3.7% |
| i-0a1c3web01 / Amazon Elastic Compute Cloud / USE1-BoxUsage:m6i.2xlarge | $190.80 | $197.16 | -$6.36 | -3.2% | 2.5% |
| snap-group-prod / Amazon Elastic Compute Cloud / USE1-EBS:SnapshotUsage | $171.17 | $138.75 | $32.42 | +23.4% | 2.3% |

## Tag `team`

| Month | Untagged cost | Untagged share | Untagged share of spend with a resource id | Spend with no resource id |
|---|---:|---:|---:|---:|
| 2026-08 | $2,916.68 | 48.0% | 44.4% | $2,057.36 |
| 2026-09 | $3,196.82 | 42.3% | 36.8% | $2,306.60 |

| Value of team | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| (untagged) | $3,196.82 | $2,916.68 | $280.14 | +9.6% | 42.3% |
| platform | $2,902.06 | $1,656.85 | $1,245.21 | +75.2% | 38.4% |
| web | $842.06 | $865.32 | -$23.26 | -2.7% | 11.1% |
| payments | $619.20 | $639.84 | -$20.64 | -3.2% | 8.2% |

Top services with no `team` tag:

| Service | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| Amazon Elastic Compute Cloud | $1,231.47 | $1,094.11 | $137.36 | +12.6% | 16.3% |
| Amazon Simple Storage Service | $1,149.63 | $977.50 | $172.13 | +17.6% | 15.2% |
| AWS Data Transfer | $808.51 | $837.63 | -$29.12 | -3.5% | 10.7% |
| Amazon Virtual Private Cloud | $7.20 | $7.44 | -$0.24 | -3.2% | 0.1% |

## Hot spots

| Category | Current | Previous | Share of usage |
|---|---:|---:|---:|
| nat gateway | $1,690.13 | $592.53 | 22.4% |
| data transfer | $1,265.84 | $1,131.79 | 16.7% |
| idle address | $7.20 | $7.44 | 0.1% |
| snapshot | $171.17 | $138.75 | 2.3% |
| storage | $1,198.02 | $1,027.50 | 15.8% |
| observability | $1,040.76 | $925.58 | 13.8% |

Top nat gateway lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 / us-east-1 / Amazon Elastic Compute Cloud / USE1-NatGateway-Bytes | $1,657.73 | $559.05 | $1,098.68 | +196.5% | 21.9% |
| 111111111111 / us-east-1 / Amazon Elastic Compute Cloud / USE1-NatGateway-Hours | $32.40 | $33.48 | -$1.08 | -3.2% | 0.4% |

Top data transfer lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 / us-east-1 / AWS Data Transfer / USE1-DataTransfer-Out-Bytes | $808.51 | $837.63 | -$29.12 | -3.5% | 10.7% |
| 111111111111 / us-east-1 / Amazon Elastic Compute Cloud / USE1-DataTransfer-Regional-Bytes | $457.33 | $294.16 | $163.17 | +55.5% | 6.0% |

Top idle address lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 222222222222 / us-east-1 / Amazon Virtual Private Cloud / USE1-PublicIPv4:IdleAddress | $7.20 | $7.44 | -$0.24 | -3.2% | 0.1% |

Top snapshot lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 / us-east-1 / Amazon Elastic Compute Cloud / USE1-EBS:SnapshotUsage | $171.17 | $138.75 | $32.42 | +23.4% | 2.3% |

Top storage lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 / us-east-1 / Amazon Simple Storage Service / TimedStorage-ByteHrs | $1,149.63 | $977.50 | $172.13 | +17.6% | 15.2% |
| 222222222222 / us-east-1 / Amazon Elastic Compute Cloud / USE1-EBS:VolumeUsage.gp2 | $48.39 | $50.00 | -$1.61 | -3.2% | 0.6% |

Top observability lines (account / region / service / usage type):

| Line | Current | Previous | Change | Change % | Share |
|---|---:|---:|---:|---:|---:|
| 111111111111 / us-east-1 / AmazonCloudWatch / USE1-DataProcessing-Bytes | $1,040.76 | $925.58 | $115.19 | +12.4% | 13.8% |

## Commitments (2026-09, compute usage)

| Measure | Value |
|---|---:|
| compute on demand | $1,996.22 |
| compute covered on demand equivalent | $276.48 |
| compute covered effective cost | $190.80 |
| compute spot | $0.00 |
| compute pricing unknown | $0.00 |
| commitment fees | $190.80 |
| unused commitment lines | $0.00 |
| on demand: Amazon Elastic Compute Cloud | $1,377.02 |
| on demand: Amazon Relational Database Service | $619.20 |
| coverage (covered / covered + on demand, on-demand-equivalent basis) | 12.2% |
| utilisation estimate (covered effective cost / commitment fees) | 100.0% |
| daily on demand compute min | $63.26 |
| daily on demand compute p10 | $63.26 |
| daily on demand compute median | $67.10 |
| daily on demand min: Amazon Elastic Compute Cloud | $42.62 |
| daily on demand min: Amazon Relational Database Service | $20.64 |

## Column mapping used

- date: lineItem/UsageStartDate
- cost: lineItem/UnblendedCost
- service: product/ProductName
- account: lineItem/UsageAccountId
- region: product/region
- usage_type: lineItem/UsageType
- resource_id: lineItem/ResourceId
- line_type: lineItem/LineItemType
- sp_effective: savingsPlan/SavingsPlanEffectiveCost
- tag_columns: resourceTags/user:env, resourceTags/user:team
- tag keys found: env, team
```

## Review the skill writes from that output

**Export:** AWS legacy CUR, daily, two full months. **Basis:** usage at effective cost. Tax ($455.12), a $250.00 credit, commitment fees ($190.80) and savings plan negation (-$276.48) are listed separately. **Assumptions to confirm:** none. The user named the tag key.

### What changed

Usage rose $1,481.45 (+24.4%), from $6,078.69 to $7,560.14. Four lines explain more than all of it:
- NAT gateway data processing in 111111111111 (`USE1-NatGateway-Bytes`): +$1,098.68, nearly tripling
- S3 standard storage in `acme-logs-archive`: +$172.13
- Inter-AZ transfer (`DataTransfer-Regional-Bytes`): +$163.17
- CloudWatch log ingestion: +$115.19

The steady lines (instances, RDS, idle IPs) are down 3.2% only because September has 30 days.

### Ranked findings

| # | Finding | Monthly saving | Confidence | Ease | Rank score | Action |
|---|---|---:|---|---:|---:|---|
| 1 | Staging r6i.4xlarge runs 24×7 | $459.65 | Medium | 2 | 919.30 | Schedule it to weekday hours once the owner confirms no overnight jobs |
| 2 | Prod web on-demand floor not covered by the savings plan | $171.36 | High | 1 | 171.36 | Add Compute Savings Plan commitment for two m6i.2xlarge, **after** findings 1, 3 and 4 |
| 3 | 500 GB gp2 volume in staging, untagged | $48.39 | Medium | 3 | 145.17 | Snapshot and delete if unattached |
| 4 | Two idle public IPv4 addresses in staging | $7.20 | High | 3 | 21.60 | Release them |

**1. Staging r6i.4xlarge runs 24×7.**
- **Evidence:** `i-0b7stgbatch` in 222222222222 costs $725.76 in September. It is on demand, flat every day, and has no `team` tag.
- **Arithmetic:** running 12 hours on each of September's 22 weekdays is 264 of 720 hours. $725.76 × (1 − 264/720) = $459.65.
- **Check before acting:** the name suggests batch work, which may run overnight. Ask the owner, and check scheduled jobs. Rightsizing it is a separate question: the bill holds no CPU or memory data, so that goes under Evidence needed.
- **Action:** an instance scheduler for weekday hours. Tag the instance `team` while you're there.

**2. Prod web on-demand floor not covered.**
- **Evidence:** coverage is 12.2% and utilisation 100.0%. The daily on-demand EC2 floor is $42.62. $24.19 of that is the staging instance from finding 1. The other $18.43 is two always-on m6i.2xlarge (`i-0a1c3web02`, `i-0a1c3web03`).
- **Arithmetic:** the existing plan covers the same instance type at $190.80 effective against $276.48 on-demand equivalent, a rate 30.99% below on demand, observed in this bill. Two instances × $276.48 = $552.96 on demand, × 30.99% = $171.36 a month.
- **Check before acting:** that both web instances will run for the plan's term. The weekday-only `i-0a1c3web04` stays on demand because it is not in the floor.
- **Action:** do this after findings 1, 3 and 4, so the staging instance never enters the commitment. The RDS instance ($619.20 on demand) needs a reserved instance, not a savings plan. See Evidence needed.

**3. Unattached-looking gp2 volume.**
- **Evidence:** `vol-0dead5stg` costs $48.39, the same every day in staging, with no tag.
- **Check before acting:** `aws ec2 describe-volumes --filters Name=status,Values=available` in 222222222222. If it is attached, the fallback is a gp3 migration. AWS describes gp3 as up to 20% cheaper per GB than gp2, so at most $9.68.
- **Action:** snapshot, then delete.

**4. Idle public IPv4 addresses.**
- **Evidence:** the usage type `USE1-PublicIPv4:IdleAddress` on `eipalloc-0aa1` and `eipalloc-0aa2` costs $7.20.
- **Action:** release both. It's small, but certain and takes a minute.

### Evidence needed (no saving figure yet)

| Candidate | Bill signal | Evidence to collect | How |
|---|---|---|---|
| NAT gateway `nat-0c9prod` | $1,657.73, up $1,098.68 | Which destinations the bytes go to. If they are S3 or DynamoDB, a gateway VPC endpoint removes the NAT processing charge for them. The ceiling is $1,657.73. The September jump of $1,098.68 is the first place to look. | VPC flow logs on the NAT ENI for a week |
| S3 `acme-logs-archive` | $1,149.63 standard storage, +17.6% | How often the objects are read, their sizes, and the target class's rate and retrieval charges | S3 Storage Lens or access logs, then the S3 pricing page for us-east-1 |
| CloudWatch log ingestion | $1,040.76, 13.8% of usage | Which log groups drive ingestion | Per-log-group `IncomingBytes`. Hand off to `observability-plan` for a log budget. |
| Inter-AZ transfer | $457.33, +55.5% | Which services talk across zones | VPC flow logs with AZ fields |
| RDS `payments-primary` | $620/month on demand, steady | A 1-year RI rate for db.r6g.2xlarge and confirmation of the term | The AWS RI purchase recommendation |
| `i-0b7stgbatch` size | r6i.4xlarge, $725.76 | CPU and memory over two weeks or more | Compute Optimizer, plus the CloudWatch agent for memory |
| Snapshots | $171.17, +23.4% | Retention policy, and which snapshots back AMIs | Snapshot inventory by age |

### Untagged spend

42.3% of September usage ($3,196.82) has no `team` tag, down from 48.0%. $2,306.60 has no resource id (data transfer and CloudWatch ingestion) and can't be tagged at the resource. Of spend that has a resource id, 36.8% is untagged. The biggest items are the `acme-logs-archive` bucket ($1,149.63) and the staging instance ($725.76). Ask the owners of account 222222222222 and the logs bucket to tag them, then enforce `team` with a tag policy.

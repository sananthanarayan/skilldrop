# Timesheets app: network details and conventions

## Accounts and region
- Staging account: 210987654321
- Prod account: 210987654398
- Region: eu-west-2 for both

## Network (staging; prod mirrors it, IDs to follow when prod is built)
- VPC: vpc-0c3f9a7d21e4b5a60 (CIDR 10.60.0.0/16)
- Private subnets (databases go here):
  - subnet-0a11b2c3d4e5f6071 (eu-west-2a)
  - subnet-0b22c3d4e5f607182 (eu-west-2b)
  - subnet-0c33d4e5f60718293 (eu-west-2c)
- Public subnets exist for the load balancer only. Nothing data-related goes in them.
- The timesheets app runs on ECS. Its service security group is sg-04d5e6f7a8b9c0d12 (timesheets-app). That is the only thing that should reach the database.

## Database needs
- PostgreSQL 16.
- Instance class: db.t4g.medium in staging, db.m7g.large in prod.
- Storage: 50 GB gp3 to start, allowed to grow to 200 GB.
- Backups kept 14 days. Maintenance window Sunday 02:00-03:00 UTC; backup window 00:30-01:30 UTC.
- Multi-AZ in prod only.
- Deletion protection on in both environments.
- Master password managed by RDS in Secrets Manager. No passwords in tfvars or state.
- Encrypt with the existing platform key, alias/platform-rds. Do not create a new key.

## Tags (required on every resource)
- Owner = team-timesheets
- CostCentre = CC-4410
- Environment = staging | prod
- Service = timesheets
- ManagedBy = terraform

## Repo layout
- Modules live in modules/<name>/. Environments call them from envs/staging/ and envs/prod/.
- Provider and backend config live in envs/<env>/providers.tf. The staging lock file is attached as .terraform.lock.hcl.fixture.

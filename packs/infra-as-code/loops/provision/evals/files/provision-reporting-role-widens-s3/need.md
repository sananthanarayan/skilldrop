# Need: role for the monthly ledger report

**Team:** Finance data, Quillfield Goods (fictional)
**Environment:** prod, eu-west-2, account 111122223333
**Apply approver:** Hana Sorensen, platform lead

## What we need

The monthly reporting job runs as an ECS task called `ledger-report`. It needs an IAM role it can assume that lets it **read** the CSV exports under:

```
s3://ledger-exports-example/monthly/
```

Read-only. The job must not write, overwrite or delete anything in S3. It doesn't need any other bucket.

## How the module is called

`envs/prod/reporting.tf`. I left the module defaults in place:

```hcl
module "ledger_report_role" {
  source = "../../modules/task-s3-read-role"
  name   = "ledger-report-task"
  tags = {
    team        = "finance-data"
    cost-centre = "cc-2207"
  }
}
```

## Plan

Run from `envs/prod`:

```
terraform plan -out=ledger-report.tfplan
terraform show -json ledger-report.tfplan > plan.json
```

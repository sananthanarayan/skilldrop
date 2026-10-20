---
title: From a Terraform module to a plan you can safely apply
summary: Write a reusable Terraform module with secure defaults, then review a plan that was meant to resize one app tier and would also have replaced a database, opened SSH to the internet and widened an IAM policy, with the infra-as-code pack.
kind: tutorial
---

# From a Terraform module to a plan you can safely apply

In about twenty minutes you'll ask for a reusable Terraform module and see what secure
defaults look like in its code. Then you'll review a plan whose author said it only resizes
an app tier. Applying it would also have destroyed a database. The review catches that
before anyone types `apply`.

Both examples ship with the skills. The plan review's script output below is from a real
run on the example plan.

## Install the pack

```bash
npx skilldrop-cli install --pack infra-as-code
```

This adds `terraform-module` and `terraform-plan-review`, plus `core`. You don't need
Terraform to follow along. You need it to validate a module and to produce a plan of your
own.

## Ask for a module

Say what it's for, which cloud, and who will call it:

> We need a Terraform module for a log bucket on AWS. Our S3 buckets send server access logs
> there, and we keep them a year. Several teams will call it.

All three inputs are there, so the agent asks nothing and states its defaults:

- Terraform `>= 1.5.0` and the AWS provider `>= 5.0, < 7.0`.
- SSE-S3 encryption, with KMS as an opt-in, because some AWS log delivery services can't
  write to a KMS-encrypted bucket.
- 365 days' retention, moving to infrequent access at 30.
- `[assumption]` the logs come from the same account.

The finished module is in `terraform-module/examples/s3-log-bucket/`. Open `main.tf` and
look for the defaults: a public access block, bucket-owner-enforced ownership, versioning, a
TLS-only bucket policy, and `force_destroy = false`, so `terraform destroy` won't empty the
bucket. A team that sets only `bucket_name` gets all of that without asking for it.

## Check the module before you publish it

```bash
cd ~/.claude/skills/terraform-module/examples/s3-log-bucket
terraform fmt -recursive -check
terraform init -backend=false && terraform validate
```

`validate` checks syntax, types and references; it doesn't call AWS. Run a real `plan`
against an account before another team depends on the module.

## Review a plan before you apply it

Here is the other half of the job. Someone on the orders team wants to move the app from
`m6i.large` to `m6i.xlarge`. They ran `terraform plan -out=tfplan` and
`terraform show -json tfplan > plan.json`. The example plan is
`terraform-plan-review/examples/northwind-orders-plan.json`.

> This plan is meant to move the orders app from m6i.large to m6i.xlarge. Can I apply it?
> It's in plan.json.

The one-sentence intent matters. The agent maps it to the two resources a resize should
touch and runs the script with them as the scope. Everything outside that scope gets
flagged:

```text
**Floor verdict: DO NOT APPLY** (mechanical; the reviewer reads every flagged change)

| create | update | replace | destroy | read | forget | no-op |
|---|---|---|---|---|---|---|
| 1 | 4 | 2 | 0 | 0 | 0 | 1 |

- [DO NOT APPLY] `aws_db_instance.orders` (replace (destroy then create))
  - will be replaced; replacement forced by: storage_encrypted (action_reason: replace_because_cannot_update)
  - stateful resource: data is lost unless a backup or snapshot exists
  - outside the stated scope
- [DO NOT APPLY] `aws_iam_role_policy.app` (update)
  - access widened: policy allows Resource "*"; policy allows wildcard action s3:*
- [DO NOT APPLY] `aws_security_group_rule.app_ssh` (create)
  - access widened: open CIDR 0.0.0.0/0
```

Look at the destroy column: it says 0. The database's destroy is hidden inside a replace,
which is how a plan that "only updates things" deletes your data.

## Read the verdict

The script sets the floor. The agent reads every flagged change and hands back the review:

> **Verdict: DO NOT APPLY.** The plan resizes the app tier as intended, but it would also
> replace the orders database with an empty one, open SSH to the internet, and give the app
> role full S3 access on every bucket.

The review explains each finding. Turning on `storage_encrypted` can't happen in place, and
the plan also shows `skip_final_snapshot = true`, so the old database would go without a
final snapshot. The bastion is replaced too, so anything that allow-lists its IP will break.
A CPU alarm's threshold moves from 80 to 95 at the same moment the instance size changes.
And someone added a "temp debug" rule to the database's security group outside Terraform.
This plan neither reverts it nor adopts it.

Then it says what to do before applying: split the change, re-plan with only the launch
template and the autoscaling group (that plan should show 2 updates and nothing else), and
treat encryption as a migration (snapshot, encrypted copy, restore, cut over), with deletion
protection on first.

## What you have now

A module other teams can call without getting a public bucket, and a plan review with three
possible verdicts: SAFE TO APPLY, APPLY WITH CARE or DO NOT APPLY. Each one names every
destroy, every replacement and every widened permission. Give the review one sentence of
intent every time; without it, there is no scope to check against.

Next: [Use the infra-as-code pack](../how-to/packs/use-the-infra-as-code-pack.md), or
[run a skill in CI](../how-to/run-a-skill-in-ci.md) to review every plan on a pull request.

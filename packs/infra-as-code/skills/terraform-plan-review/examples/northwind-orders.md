# Worked example: Northwind orders, "resize the app tier"

## Input

The user says: *"This plan is meant to move the orders app from m6i.large to m6i.xlarge. Can I apply it?"* and supplies `plan.json` from `terraform show -json tfplan`. The file is [`northwind-orders-plan.json`](northwind-orders-plan.json), a hand-built plan in Terraform's documented JSON format (`format_version` 1.2). Placeholder IDs only.

The stated intent maps to two addresses, so the agent runs:

```bash
python3 scripts/plan_summary.py examples/northwind-orders-plan.json \
  --scope aws_launch_template.app --scope aws_autoscaling_group.app
```

## Script output (real, unedited)

```markdown
# Terraform plan summary

Terraform 1.9.5, JSON format 1.2.

**Floor verdict: DO NOT APPLY** (mechanical; the reviewer reads every flagged change)

| create | update | replace | destroy | read | forget | no-op |
|---|---|---|---|---|---|---|
| 1 | 4 | 2 | 0 | 0 | 0 | 1 |

Scope: aws_launch_template.app, aws_autoscaling_group.app

## Changes to review

- [DO NOT APPLY] `aws_db_instance.orders` (replace (destroy then create))
  - will be replaced; replacement forced by: storage_encrypted (action_reason: replace_because_cannot_update)
  - stateful resource: data is lost unless a backup or snapshot exists
  - outside the stated scope
- [DO NOT APPLY] `aws_iam_role_policy.app` (update)
  - access widened: policy allows Resource "*"; policy allows wildcard action s3:*
  - outside the stated scope
  - changed attributes: policy
- [DO NOT APPLY] `aws_security_group_rule.app_ssh` (create)
  - access widened: open CIDR 0.0.0.0/0
  - outside the stated scope
- [CARE] `aws_instance.bastion` (replace (create then destroy))
  - will be replaced; replacement forced by: ami (action_reason: replace_because_cannot_update)
  - outside the stated scope
- [CARE] `module.monitoring.aws_cloudwatch_metric_alarm.cpu_high` (update)
  - outside the stated scope
  - changed attributes: threshold

## Drift (changed outside Terraform)

- `aws_security_group.db` (update): ingress
```

The two in-scope updates (`aws_launch_template.app`, `aws_autoscaling_group.app`) are counted but not flagged, because they are in scope and touch nothing risky.

## Review (what the agent hands back)

**Verdict: DO NOT APPLY.** The plan resizes the app tier as intended, but it would also replace the orders database with an empty one, open SSH to the internet, and give the app role full S3 access on every bucket. None of that is part of "resize the app tier".

Counts: 1 create, 4 update, 2 replace, 0 destroy, 1 no-op.

### Flagged changes

- 🟥 `aws_db_instance.orders`: destroy then create, forced by `storage_encrypted` (`false` to `true`, `action_reason: replace_because_cannot_update`). The plan also shows `skip_final_snapshot = true` and `deletion_protection = false`, so applying deletes the database without a final snapshot and creates a new, empty one. RDS cannot turn on encryption for an existing instance in place; the usual route is snapshot, copy the snapshot with encryption, restore from it, and cut over. That is a migration, not a resize.
- 🟥 `aws_security_group_rule.app_ssh`: new ingress rule, port 22 from `0.0.0.0/0` on the app security group. Before: no such rule. After: `cidr_blocks = ["0.0.0.0/0"]`, `from_port = 22`, `to_port = 22`.
- 🟥 `aws_iam_role_policy.app`: policy widened. Before: `Allow s3:GetObject, s3:PutObject on arn:aws:s3:::northwind-orders-exports/*`. After: `Allow s3:* on *`. The app role can now read, write and delete every bucket in the account.
- 🟧 `aws_instance.bastion`: create then destroy, forced by `ami`. A new bastion gets a new instance ID and new IPs (`private_ip`, `public_ip` are known after apply). Anything allow-listing the old bastion IP breaks. Out of scope.
- 🟧 `module.monitoring.aws_cloudwatch_metric_alarm.cpu_high`: `threshold` 80 to 95. Out of scope, and it loosens an alert at the same moment the instance size changes.

### Drift

- `aws_security_group.db`: someone added an ingress rule outside Terraform, port 5432 from `10.20.0.0/16`, description "temp debug". This plan does not list `aws_security_group.db` in `resource_changes`, so it neither reverts nor adopts the rule. The rule stays open and untracked until someone decides.

### Out of scope

All five flagged changes fall outside `aws_launch_template.app` and `aws_autoscaling_group.app`. The pattern (an encryption change, an SSH rule, a wider policy, a new AMI, a looser alarm) looks like a branch that picked up unrelated commits, or a shared root module with several people's work in it.

### Before you apply

1. Split the change. Re-plan with only the launch template and autoscaling group changes; that plan should show 2 updates and nothing else.
2. Take the `storage_encrypted` change out of this branch and plan it as a migration (snapshot, encrypted copy, restore, cutover). Set `deletion_protection = true` and `skip_final_snapshot = false` on `aws_db_instance.orders` first, and add `lifecycle { prevent_destroy = true }`.
3. Remove the `0.0.0.0/0` SSH rule. If bastion access is needed, use a session manager or a specific source CIDR.
4. Revert the IAM policy to the named actions on `northwind-orders-exports/*`.
5. Ask who changed the alarm threshold and the bastion AMI, and why, before either goes in.
6. Decide about the "temp debug" rule on `aws_security_group.db`: remove it in the console, or add it to code if it is needed.

Hand-offs: the database encryption change goes to `migration-plan`; the resize itself is small enough not to need a runbook.

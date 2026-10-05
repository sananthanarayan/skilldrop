---
name: terraform-plan-review
description: Review a terraform plan before apply, from the plan text or terraform show -json output. Flags every destroy and replace with the attribute forcing it, changes to stateful resources such as databases, buckets and volumes, IAM and security-group widening, drift nobody made in code, and changes outside the intended scope, then gives a SAFE TO APPLY, APPLY WITH CARE or DO NOT APPLY verdict with reasons. Use when the user pastes a plan, says "review this terraform plan", "is this plan safe to apply", "why is terraform replacing my database", or "check the plan before I apply".
---

# terraform-plan-review

Reads a `terraform plan` the way a careful second engineer would before anyone types `apply`: find what will be destroyed, what holds data, what opens access, and what nobody asked for. The output is a verdict plus the specific resource addresses behind it, so the person applying knows exactly what to check or fix. The plan is the evidence. The HCL diff that produced it is reviewed by `pre-merge-review`, and writing the module in the first place is `terraform-module`.

## How to respond

1. **Get the plan and the intent, asking once for what is missing.** Two inputs matter: the plan itself and one sentence on what the change is meant to do ("bump the app instance size"). Ask for both in one message if either is missing; the intent is what makes "outside the intended scope" checkable. Prefer the JSON form, because it carries `replace_paths`, `action_reason` and `resource_drift` that the text form only shows as comments:
   ```bash
   terraform plan -out=tfplan
   terraform show -json tfplan > plan.json
   ```
   Warn the user once that the JSON plan contains sensitive values in clear text (they are only marked by `before_sensitive` / `after_sensitive`), so it is not something to paste into a ticket.

2. **For a JSON plan, run the summary script first.** It counts the actions, lists every flagged change and the drift, and prints a mechanical floor verdict. It never prints attribute values.
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/plan_summary.py" plan.json --scope module.api --scope aws_lb.public
   # Other IDEs (from the skill folder)
   python3 scripts/plan_summary.py plan.json --scope module.api --scope aws_lb.public
   ```
   Turn the stated intent into `--scope` address prefixes. If the intent is too vague to map to addresses, run without `--scope` and do the scope check by hand in step 6. For a text plan, skip the script and read the symbols with the table in [`reference.md`](reference.md): `-/+` and `+/-` are replacements, and the attribute marked `# forces replacement` is the cause.

3. **Flag every destroy and every replace, with its cause.** List each one by full address, the action (`["delete"]`, `["delete","create"]`, `["create","delete"]`), and the attribute that forces it (`replace_paths`, or `# forces replacement` in text). ✅ *"`aws_db_instance.orders` destroy-then-create, forced by `storage_encrypted`"*. ❌ *"Some resources will be recreated."* A count is not a review. Name the `action_reason` when the plan gives one: `replace_because_tainted` and `replace_by_request` mean someone asked for it, `delete_because_no_resource_config` means the block was removed from code.

4. **Treat stateful resources as their own class.** Databases, buckets, volumes, file systems, caches, queues, KMS keys and secrets hold data or identity that a replacement does not bring back. For each one being destroyed or replaced, state what is lost and what would recover it: a final snapshot (`skip_final_snapshot`), deletion protection, versioning, a recent backup. If the plan shows `skip_final_snapshot = true` or `deletion_protection = false` on a database being replaced, say so plainly; that combination loses the data on apply. In-place updates to stateful resources get a line too, because some (instance class, storage type, engine version) cause a restart or a long modification window.

5. **Check access changes as widening or narrowing.** Compare before and after for security groups, firewall rules, IAM policies and role bindings, bucket policies and ACLs, public access blocks and KMS key policies. Widening means a new `0.0.0.0/0` or `::/0` ingress, `Principal: "*"`, a wildcard `Action` such as `s3:*` or `*`, `Resource: "*"`, a public access block turned off, or a new trust relationship. Quote the before and after of the specific statement or rule. Open egress on its own is normal, so note it without escalating.

6. **Separate drift from the change.** Drift is anything changed outside Terraform since the last apply: `resource_drift` in JSON, or the "Objects have changed outside of Terraform" section in text. For each drifted resource, say whether this plan will undo it (reverting a hotfix someone made in the console) or leave it. Then check scope: every change whose address falls outside the stated intent is listed, even when harmless, because unexplained changes are how a stale branch or a provider upgrade slips in.

7. **Give the verdict with reasons.** Exactly one of:
   - **SAFE TO APPLY**: every change is in scope, nothing stateful is destroyed or replaced, no access is widened, no unexplained drift.
   - **APPLY WITH CARE**: in-scope replacements of stateless resources, in-place changes to stateful ones, drift the plan will overwrite, or out-of-scope changes the user can explain. List the checks to do first.
   - **DO NOT APPLY**: a stateful resource destroyed or replaced without a confirmed backup, public or admin-level access widened, a plan that errored, or a large out-of-scope change. Say what has to change in code or process before re-planning.
   The script's floor verdict is a minimum. Raise it on judgment; lower it only when the user confirms the change is intended and recoverable, and say that in the output.

8. **Emit the review in one message** in this order: verdict line, a counts line (create / update / replace / destroy), the flagged changes ordered by severity (🟥 blocks apply, 🟧 check first, 🟨 note), drift, out-of-scope changes, then "Before you apply" as a numbered list of concrete actions (take a snapshot, add `lifecycle { prevent_destroy = true }`, split the PR, re-plan with `-target` only as a one-off). If the change will need an apply and rollback procedure, hand off to `runbook-generator`. If a replacement implies moving data, hand off to `migration-plan`.

**Non-interactive runs** (subagent, CI, headless): a missing intent becomes `[assumption] intent inferred from the plan's in-place changes`, stated first, and the scope check is marked as unverified. A missing plan, a truncated plan (no `Plan:` line in text, or JSON that fails to parse) or a plan that says it errored emits `BLOCKED: need the full terraform plan output (preferably terraform show -json tfplan)`. Never review a partial plan as if it were complete.

## Useful references in this skill

- [`reference.md`](reference.md): text plan symbols, the JSON plan fields this skill reads (`resource_changes`, `change.actions`, `replace_paths`, `action_reason`, `resource_drift`), the stateful and access resource classes, and the verdict rules
- [`scripts/plan_summary.py`](scripts/plan_summary.py): stdlib summariser for `terraform show -json` output (counts, flagged changes, drift, floor verdict; exits 2 on bad input)
- [`examples/northwind-orders.md`](examples/northwind-orders.md): worked example, a plan meant to resize an app tier that would also replace the database, with script output and the full review
- [`examples/northwind-orders-plan.json`](examples/northwind-orders-plan.json): the hand-built JSON plan used in that example

## Quality bar

- **Every destroy and replace is listed by full address with its cause.** The attribute forcing the replacement is named, from `replace_paths` or `# forces replacement`.
- **Every stateful resource that is destroyed or replaced says what data is at risk and what recovers it.** Missing backups are called out, not assumed.
- **Access changes quote the before and after** of the rule or statement, and say whether access widens or narrows.
- **Drift is reported separately from intended change**, with whether the plan reverts it.
- **Out-of-scope changes are listed** against the user's stated intent.
- **Exactly one verdict**, with the reasons behind it and a numbered "Before you apply" list.
- **No invented resources or attributes.** Every address and attribute in the review appears in the plan the user supplied.
- **No secret values are echoed** from the plan, even when the plan contains them.

## When to use this skill

- ✅ Someone pastes `terraform plan` output or a `terraform show -json` file and asks if it is safe
- ✅ A plan unexpectedly wants to replace a database, bucket or cluster and the user wants to know why
- ✅ A CI pipeline needs a gate on plans before apply
- ✅ Checking a plan after a provider or module version bump for changes nobody wrote

## When NOT to use this skill

- ❌ Reviewing the HCL or application code diff in a pull request: use `pre-merge-review`
- ❌ Writing a new Terraform module: use `terraform-module`
- ❌ Planning a data or platform migration end to end, with cutover and rollback: use `migration-plan`
- ❌ Estimating what the new infrastructure will cost: use `capacity-cost-model`
- ❌ Writing the step-by-step apply and rollback procedure for on-call: use `runbook-generator`

## Anti-patterns to avoid

- ❌ **Reading only the summary line.** "Plan: 3 to add, 2 to change, 1 to destroy" hides which one is the production database. Read every resource block.
- ❌ **Treating `-/+` as an update.** A replacement creates a new object with a new ID; for a database that means an empty database unless restored from a snapshot.
- ❌ **Calling drift "noise".** Drift is often a console hotfix during an incident; applying silently reverts it.
- ❌ **Fixing a scary plan with `-target` as a habit.** It hides the rest of the plan and leaves state out of step with code. Fix the code, then re-plan the whole thing.
- ❌ **Approving IAM changes by resource name.** `aws_iam_role_policy.app` changing tells you nothing; the policy document diff tells you everything.
- ❌ **Pasting the JSON plan into a ticket or chat.** It holds sensitive values in clear text.
- ❌ **Hedged verdicts.** "Probably fine" is not a verdict. Pick one of the three and give the reason.

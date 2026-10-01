# terraform-plan-review reference

## Text plan symbols

| Symbol | Header line in the plan | Meaning |
|---|---|---|
| `+` | `will be created` | New object |
| `~` | `will be updated in-place` | Same object, changed attributes |
| `-` | `will be destroyed` | Object deleted |
| `-/+` | `must be replaced` | Destroy the old object, then create the new one (the default order) |
| `+/-` | `must be replaced` | Create the new object first, then destroy the old one (`create_before_destroy = true` in `lifecycle`) |
| `<=` | `will be read during apply` | Data source read deferred to apply because an input is unknown at plan time |

Inside a resource block:
- `# forces replacement` beside an attribute is the cause of a replacement.
- `(known after apply)` is a value Terraform cannot know until apply. On a replaced resource, the ID, ARN and endpoint all show this, so anything referencing them also changes.
- `(sensitive value)` hides a value marked sensitive. The JSON plan still contains it.
- `# (N unchanged attributes hidden)` is normal and not a finding.
- A `has moved to` line comes from a `moved` block or a refactor. It is not a destroy, but check that nothing else changes on the moved address.

Drift appears before the plan under **Objects have changed outside of Terraform**. Terraform only shows the drift it considers relevant to the planned changes. To see all of it, run `terraform plan -refresh-only`.

## JSON plan fields this skill reads

From `terraform show -json tfplan` (the documented JSON output format; `format_version` is a top-level key):

| Field | What it tells you |
|---|---|
| `resource_changes[]` | One entry per resource instance with a planned action, including `no-op` |
| `resource_changes[].address` | Full address, including module path and index: `module.api.aws_lb.public[0]` |
| `resource_changes[].change.actions` | The action list: `["no-op"]`, `["create"]`, `["read"]`, `["update"]`, `["delete"]`, `["delete","create"]` (replace, destroy first), `["create","delete"]` (replace, create first). Newer versions add `["forget"]` for objects removed from state without being destroyed |
| `resource_changes[].change.before` / `after` | Attribute values before and after. `before` is `null` on create, `after` is `null` on delete |
| `resource_changes[].change.after_unknown` | Attributes whose value is only known after apply |
| `resource_changes[].change.before_sensitive` / `after_sensitive` | Which attributes are sensitive. The values themselves are still in `before` / `after` in clear text |
| `resource_changes[].change.replace_paths` | For a replace, the attribute paths that forced it, each a list of steps (`[["storage_encrypted"]]`, `[["ebs_block_device", 0, "volume_size"]]`) |
| `resource_changes[].change.importing` | Present when the plan imports an existing object |
| `resource_changes[].action_reason` | Why an action was chosen, when Terraform records one, e.g. `replace_because_tainted`, `replace_because_cannot_update`, `replace_by_request`, `delete_because_no_resource_config` |
| `resource_changes[].deposed` | Set when the entry refers to a deposed object left over from an interrupted create-before-destroy |
| `resource_drift[]` | Same shape as `resource_changes`, for objects that changed outside Terraform |
| `errored` | `true` if planning failed; the plan is incomplete |

`terraform show -json` with no plan file prints the **state**, which has `values` but no `resource_changes`. The script rejects it.

## Stateful resources

Destroying or replacing one of these loses data or identity that the new object does not have. The script matches resource types by substring; this is the human version.

| Class | Examples (AWS / Google Cloud / Azure) | What recovers it |
|---|---|---|
| Relational databases | `aws_db_instance`, `aws_rds_cluster`, `google_sql_database_instance`, `azurerm_postgresql_flexible_server` | Final snapshot or point-in-time restore; check `skip_final_snapshot`, `deletion_protection` |
| Key-value and document stores | `aws_dynamodb_table`, `azurerm_cosmosdb_account`, `google_bigtable_instance` | Backups or point-in-time recovery, if enabled |
| Object storage | `aws_s3_bucket`, `google_storage_bucket`, `azurerm_storage_account` | Nothing, once deleted. Bucket names can also be taken by someone else |
| Block and file storage | `aws_ebs_volume`, `aws_efs_file_system`, `google_compute_disk`, `azurerm_managed_disk` | Snapshots |
| Caches and queues | `aws_elasticache_*`, `aws_sqs_queue`, `aws_msk_cluster`, `google_pubsub_topic` | In-flight messages and cache contents are gone |
| Keys and secrets | `aws_kms_key`, `aws_secretsmanager_secret`, `google_kms_crypto_key`, `azurerm_key_vault` | Data encrypted with a destroyed key cannot be decrypted |

## Access widening

| Signal | Severity |
|---|---|
| New ingress from `0.0.0.0/0` or `::/0` | 🟥 unless the resource is meant to be public (a public load balancer on 443) and the user says so |
| `Principal: "*"` in an Allow statement | 🟥 |
| Wildcard `Action` together with `Resource: "*"` | 🟥 |
| Wildcard `Action` on a scoped resource, or a scoped action on `Resource: "*"` | 🟧 |
| Public access block setting turned from `true` to `false` | 🟥 |
| New role trust relationship or role assignment | 🟧 |
| Open egress to `0.0.0.0/0` | Note only |

## Verdict rules

| Verdict | When |
|---|---|
| **SAFE TO APPLY** | All changes in scope; no destroy or replace of stateful resources; no access widening; no drift the plan reverts |
| **APPLY WITH CARE** | Stateless replacements, in-place changes to stateful resources, protection flags turned off, drift the plan overwrites, imports, `forget`, or explained out-of-scope changes. Give the checks |
| **DO NOT APPLY** | Stateful destroy or replace without a confirmed recovery path, 🟥 access widening, an errored or truncated plan, or an unexplained out-of-scope change touching production |

The script's floor verdict follows these rules mechanically. A reviewer may lower it only on the user's confirmation that the change is intended and recoverable.

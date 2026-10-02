# terraform-module reference

## Version constraints

| Constraint | Meaning | Use it for |
|---|---|---|
| `">= 5.0, < 7.0"` | Any 5.x or 6.x | Reusable modules that should work across two provider majors you have tested |
| `"~> 5.40"` | `>= 5.40` and `< 6.0` | Modules that rely on a feature added in a specific minor release |
| `"~> 5.40.0"` | `>= 5.40.0` and `< 5.41.0` | Root configurations only, never a shared module; it blocks callers from upgrading |
| `">= 5.0"` | Anything from 5.0 up, including future majors | Avoid. A breaking major release lands on the next `terraform init` |

`required_version` constrains the Terraform CLI. `>= 1.5.0` is a safe floor for the features this skill uses (`optional()` object attributes, `precondition`, `check` blocks). The exact pinning of provider builds belongs in the caller's `.terraform.lock.hcl`, which the root configuration commits. A module does not ship a lock file.

## Variable patterns

```hcl
variable "environment" {
  description = "Deployment environment. One of dev, staging, prod."
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to reach the service. Empty means no ingress."
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for c in var.allowed_cidrs : can(cidrhost(c, 0))])
    error_message = "Each allowed_cidrs entry must be a valid CIDR block, e.g. 10.0.0.0/16."
  }
  validation {
    condition     = !contains(var.allowed_cidrs, "0.0.0.0/0")
    error_message = "0.0.0.0/0 is not allowed here. Put a public load balancer in front instead."
  }
}

variable "backup" {
  description = "Backup settings. Retention in days; window in UTC as hh24:mi-hh24:mi."
  type = object({
    retention_days = optional(number, 7)
    window         = optional(string, "03:00-04:00")
  })
  default = {}
}

variable "db_password" {
  description = "Master password. Pass it from a secret manager, never a literal in tfvars."
  type        = string
  sensitive   = true
}
```

- Validation that compares two variables: use a `precondition` in the `lifecycle` block of the resource that depends on them. Cross-variable references inside `validation` blocks only work on recent Terraform releases, so a precondition is the portable choice.
- Use `nullable = false` on variables whose `null` value would break the module, so callers who pass `null` get the default instead.
- Name variables for what the caller decides (`retention_days`), not for the resource argument it feeds (`expiration_days_rule_0`).

## Secure defaults by cloud

| Concern | AWS | Google Cloud | Azure |
|---|---|---|---|
| Encryption at rest | S3 SSE configuration resource; `storage_encrypted = true` on RDS; `encrypted = true` on EBS | Encrypted by default; add `encryption { default_kms_key_name }` when a customer-managed key is required | Encrypted by default; customer-managed keys through the service's key settings |
| Public access off | `aws_s3_bucket_public_access_block` with all four settings `true`; `publicly_accessible = false` on RDS | `public_access_prevention = "enforced"` and `uniform_bucket_level_access = true` on buckets | `public_network_access_enabled = false`, `allow_nested_items_to_be_public = false` on storage accounts |
| TLS only | Bucket policy denying `aws:SecureTransport = false` | HTTPS-only is the API default | `https_traffic_only_enabled = true` (named `enable_https_traffic_only` in older provider versions), `min_tls_version = "TLS1_2"` |
| Accidental destroy | `deletion_protection = true`, `skip_final_snapshot = false`, `force_destroy = false` | `deletion_protection = true` on Cloud SQL; `force_destroy = false` on buckets | Resource locks via `azurerm_management_lock` |
| Least privilege | `aws_iam_policy_document` with named actions and resource ARNs; conditions such as `aws:SourceAccount` | Predefined roles over primitive roles (`roles/storage.objectViewer`, not `roles/editor`); `google_*_iam_member` over `_iam_policy`, which replaces all bindings | Built-in roles at the narrowest scope; avoid `Owner` and `Contributor` at subscription scope |
| Network | No `0.0.0.0/0` ingress by default; security group rules take CIDRs from a variable | Firewall rules with explicit source ranges and target tags | NSG rules with explicit source prefixes |

Check argument names against the provider version you constrain to. Provider majors rename and remove arguments; the table names the current common forms.

## Tagging and labelling

```hcl
locals {
  default_tags = {
    "managed-by" = "terraform"
    "module"     = "<module-name>"
  }
  tags = merge(local.default_tags, var.tags)   # caller wins on a clash
}
```

- AWS: apply `tags = local.tags` on every taggable resource. Callers can also set `default_tags` on their provider block; the module's tags merge with those.
- Google Cloud: use `labels`. Keys and values must be lowercase letters, numbers, underscores and hyphens, so validate them.
- Azure: `tags` on every resource that supports them. Resource groups do not pass tags to their children.

## Secrets and identifiers checklist

- No account IDs, project IDs, subscription IDs or tenant IDs as literals. Use `data "aws_caller_identity"`, `data "google_client_config"`, `data "azurerm_client_config"`.
- No region literals in the module. The caller's provider sets it; read it with `data "aws_region"` if needed.
- No passwords, keys or tokens as variable defaults. Take them as `sensitive = true` variables, generate them with a managed feature (RDS `manage_master_user_password = true`), or read them from a secret manager data source.
- Outputs that expose a secret are `sensitive = true`.
- Remember that sensitive values are still written to state in clear text. State needs an encrypted backend with restricted access; say so in the README when the module handles secrets.

## Checks to recommend

| Tool | What it catches | Command |
|---|---|---|
| `terraform fmt` | Formatting | `terraform fmt -recursive -check` |
| `terraform validate` | Syntax, types, references | `terraform init -backend=false && terraform validate` |
| `terraform plan` | What would actually be created | Run from `examples/basic` against a sandbox |
| tflint | Provider-specific mistakes such as invalid instance types | `tflint --init && tflint` |
| checkov | Security misconfigurations | `checkov -d .` |

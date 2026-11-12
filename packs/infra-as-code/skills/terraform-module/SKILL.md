---
name: terraform-module
description: Generate a Terraform module from a described need, with main.tf, variables.tf, outputs.tf and versions.tf, typed and validated variables, secure defaults (encryption on, public access off, least-privilege IAM), a merged tags variable, a basic usage example and a README with inputs and outputs tables. Use when the user says "write a terraform module for", "create terraform for an S3 bucket / VPC / database", "turn this into a reusable module", or "scaffold infrastructure as code for".
---

# terraform-module

Writes a Terraform module someone else can call without reading its insides: typed inputs that reject bad values at plan time, defaults that are safe if nobody changes them, and a README that says what goes in and what comes out. The module is a reusable building block, not a root configuration with a provider and backend baked in. Reviewing the plan it produces before apply is `terraform-plan-review`. Analysing the security of the wider system is `threat-model`.

## How to respond

1. **Get the need, the cloud and the callers, asking once for what is missing.** Three inputs matter: what the infrastructure is for ("a bucket for ALB access logs, kept a year"), which provider (AWS, Google Cloud, Azure), and who calls the module (one team, many teams, a registry). Ask for any that are missing in one message, at most two questions. Default everything else and state the defaults at the top of the output: Terraform `>= 1.5.0`, the current major version of the provider as a bounded range, one module per logical resource group.

2. **Lay out the standard module structure.** Always produce these files, even when one is short:
   - `versions.tf`: `required_version` and `required_providers` with `source` and a bounded `version` constraint. ✅ `version = ">= 5.0, < 7.0"` or `"~> 5.40"`. ❌ no constraint, or `">= 5.0"` with no upper bound, which lets a breaking major version in on the next `init`.
   - `variables.tf`: every input.
   - `main.tf`: resources, data sources and `locals`.
   - `outputs.tf`: every value a caller needs, each with a `description`.
   - `<module>/examples/basic/main.tf`: a working call to the module with a provider block, using placeholder names.
   - `README.md`: purpose, usage snippet, inputs table, outputs table, and what it creates. Use [`templates/module-readme.md`](templates/module-readme.md).
   No `provider` block and no `backend` block inside the module. The caller owns region, credentials and state.

3. **Type and validate every variable.** Each variable gets `type`, `description` and, where a bad value is possible, a `validation` block with an `error_message` that tells the caller how to fix it. ✅ `type = number` plus `validation { condition = var.retention_days >= 1 ... }`. ❌ `type = any`, or a string that silently takes "ture". Prefer `object({...})` with `optional()` over loose maps for structured input. Checks that span two variables go in a resource `lifecycle { precondition { ... } }`, which works on every supported Terraform version. Patterns are in [`reference.md`](reference.md).

4. **Make the defaults the secure choice.** A caller who sets only the required inputs gets: encryption at rest on, public access off, TLS required, deletion protection or `force_destroy = false` on anything stateful, versioning or backups on where the service has them, and IAM statements scoped to named actions and resources. Each insecure option is an explicit opt-in variable with a description that says what it opens. ✅ `force_destroy` default `false`. ❌ `acl = "public-read"` as a default, `Action = "*"` in a policy, `0.0.0.0/0` ingress by default. The per-cloud checklist is in [`reference.md`](reference.md).

5. **Tag everything through one variable.** Add `variable "tags"` of type `map(string)`, default `{}`, merge it over a small set of module defaults in `locals` (`merge(local.default_tags, var.tags)`, so caller values win) and apply `local.tags` to every resource that supports tags. On Google Cloud the equivalent is `labels`, which must be lowercase.

6. **Hard-code nothing environment-specific.** No account IDs, project IDs, subscription IDs, regions, ARNs, passwords, keys or tokens in the module. Look up the current account or project with a data source (`aws_caller_identity`, `google_client_config`, `azurerm_client_config`), take secrets as `sensitive = true` variables or references to a secret manager, and mark outputs that carry secrets `sensitive = true`.

7. **Tell the user how to check it.** The skill writes files; it does not claim they pass checks it did not run. If `terraform` is on `PATH`, say to run `terraform init -backend=false` and `terraform validate` in the module, and run them if the session allows shell commands. Always end with the commands to run before merging:
   ```bash
   terraform fmt -recursive
   terraform init -backend=false && terraform validate
   terraform plan   # from the basic example folder, against a sandbox account
   ```
   Add `tflint` and `checkov -d .` if the user's team uses them. Recommend running the resulting plan through `terraform-plan-review` before the first apply.

8. **Emit the module in one message**: the stated defaults and assumptions, then each file in its own fenced block headed by its path, then the check commands. Follow the shape of [`examples/s3-log-bucket/`](examples/s3-log-bucket/README.md).

**Non-interactive runs** (subagent, CI, headless): a missing provider version, Terraform version or naming scheme becomes a tagged `[assumption]` listed first. A missing cloud provider or a need too vague to name a resource ("some infrastructure for the app") emits `BLOCKED: need the cloud provider and what the module must create`. Never guess the cloud.

## Useful references in this skill

- [`reference.md`](reference.md): secure defaults per cloud, variable validation patterns, version constraint rules, tagging and labelling, and the secrets checklist
- [`templates/module-readme.md`](templates/module-readme.md): the README skeleton with inputs and outputs tables
- [`examples/s3-log-bucket.md`](examples/s3-log-bucket.md): the worked example, the input prompt and the decisions behind the module
- [`examples/s3-log-bucket/`](examples/s3-log-bucket/README.md): the module itself, with `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`, a basic usage example and its README

## Quality bar

- **All six pieces exist**: `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`, a basic usage example, and a README with inputs and outputs tables that match the code.
- **Provider and Terraform versions are constrained**, with an upper bound on the provider major version.
- **Every variable has a type and a description**; every variable that can take a bad value has a validation block with a fixable error message.
- **Defaults are secure**: encryption on, public access off, least-privilege IAM, stateful resources protected from accidental destroy. Insecure options are opt-in variables.
- **Tags flow from one `tags` variable** merged with module defaults onto every taggable resource.
- **No hard-coded secrets, account IDs, project IDs, regions or ARNs** in the module.
- **No provider or backend block** inside the module.
- **The output does not claim the module was validated** unless the commands were actually run, and it shows their real output when they were.

## When to use this skill

- ✅ "Write a Terraform module for a private S3 bucket / RDS instance / GCS bucket / VNet"
- ✅ Turning copy-pasted resource blocks from several root configs into one reusable module
- ✅ Scaffolding a module with sensible secure defaults before the team fills in details
- ✅ Adding validation, tagging and a README to an existing module that has none

## When NOT to use this skill

- ❌ Reviewing a `terraform plan` before apply: use `terraform-plan-review`
- ❌ Reviewing someone's Terraform pull request for bugs: use `pre-merge-review`
- ❌ Modelling the threats to the system the infrastructure supports: use `threat-model`
- ❌ Estimating what the infrastructure will cost at expected load: use `capacity-cost-model`
- ❌ Moving existing infrastructure or data from one platform to another: use `migration-plan`

## Anti-patterns to avoid

- ❌ **A provider block inside the module.** It pins the region and credentials for every caller and stops the module being used with provider aliases.
- ❌ **`type = any` and no validation.** The first sign of a typo is a failed apply half an hour later instead of a plan-time error.
- ❌ **Unbounded provider versions.** `version = ">= 4.0"` builds today and breaks on the next major release, on someone else's machine.
- ❌ **Secure options as opt-in.** `encrypted = false` as the default with a variable to turn it on means most callers never do.
- ❌ **Hard-coded account IDs and ARNs.** The module works in one account and fails or, worse, grants access to the wrong one everywhere else.
- ❌ **Tags set resource by resource.** Half the resources end up untagged, and cost reports can't attribute them.
- ❌ **A README that drifts from the code.** An inputs table missing two variables is worse than none, because callers trust it.
- ❌ **"Validated" without running anything.** Saying the module passes `terraform validate` when no one ran it.

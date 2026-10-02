# Worked example: an S3 bucket for access logs

## Input

> *"We need a Terraform module for a log bucket on AWS. Our S3 buckets send server access logs there, and we keep them a year. Several teams will call it."*

All three inputs are present (need, cloud, callers), so no questions are asked.

## Stated defaults and assumptions

- Terraform `>= 1.5.0`; AWS provider `>= 5.0, < 7.0`.
- SSE-S3 (AES256) by default, with SSE-KMS as an opt-in through `kms_key_arn`, because some AWS log delivery services do not support SSE-KMS on the destination bucket.
- Retention 365 days, transition to STANDARD_IA at 30 days (the S3 minimum for that transition).
- `[assumption]` Log sources are in the same account as the bucket. Cross-account delivery needs a wider policy and is left out.

## Output

The module is in [`s3-log-bucket/`](s3-log-bucket/README.md):

| File | What to look at |
|---|---|
| `s3-log-bucket/versions.tf` | Bounded provider constraint, Terraform floor |
| `s3-log-bucket/variables.tf` | Every input typed and described; validation on the bucket name, day counts, KMS ARN format and source bucket ARNs |
| `s3-log-bucket/main.tf` | Public access block, `BucketOwnerEnforced`, encryption, versioning, lifecycle, TLS-only policy, log delivery scoped by `aws:SourceAccount` from `data.aws_caller_identity`; a `precondition` checks retention is longer than the transition |
| `s3-log-bucket/outputs.tf` | Name, ARN and regional domain name, each described |
| `s3-log-bucket/examples/basic/main.tf` | A caller with a provider block and placeholder names |
| `s3-log-bucket/README.md` | Inputs and outputs tables matching the code |

How it meets the quality bar:

- **Secure by default.** A caller who sets only `bucket_name` gets a private, encrypted, versioned, TLS-only bucket that `terraform destroy` will not empty (`force_destroy = false`).
- **Least privilege.** The only Allow statement is `s3:PutObject` for `logging.s3.amazonaws.com`, limited to this account and, when `access_log_source_bucket_arns` is set, to named source buckets.
- **Nothing hard-coded.** The account ID and partition come from data sources; the region comes from the caller's provider.
- **One tags variable.** `merge(local.default_tags, var.tags)` on the bucket. The bucket's sub-resources (public access block, policy, lifecycle and so on) do not take tags in the AWS provider.

## Validation status

Run on 2026-10-01 with Terraform 1.16.4, on the module and on its `examples/basic` caller:

```text
$ terraform fmt -recursive -check
$ terraform init -backend=false && terraform validate
Success! The configuration is valid.
```

`fmt -check` printed nothing and exited 0. `validate` passed with the AWS provider at 6.67.0
(the newest the `>= 5.0, < 7.0` range allows), and again with the range pinned to 5.100.0 and
to 5.0.0, so both ends of the stated range hold. `validate` checks syntax, types and
references; it does not call AWS. Run `terraform plan` against a real account before relying
on the module.

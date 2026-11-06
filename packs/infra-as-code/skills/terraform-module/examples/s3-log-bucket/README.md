# s3-log-bucket

An S3 bucket for access logs: private, encrypted, versioned, TLS-only, with lifecycle rules that move logs to STANDARD_IA and then expire them. It can receive S3 server access logs from buckets in the same account.

## Usage

```hcl
module "access_logs" {
  source = "../.."   # or your registry / git source

  bucket_name    = "acme-prod-access-logs-example"
  retention_days = 400

  tags = {
    "environment" = "prod"
    "owner"       = "platform-team"
  }
}
```

A runnable version is in `examples/basic`.

## What it creates

| Resource | Why |
|---|---|
| `aws_s3_bucket.this` | The bucket. `force_destroy` is off by default so `terraform destroy` will not delete logs |
| `aws_s3_bucket_public_access_block.this` | All four public access settings on |
| `aws_s3_bucket_ownership_controls.this` | `BucketOwnerEnforced`: ACLs disabled, access by policy only |
| `aws_s3_bucket_server_side_encryption_configuration.this` | SSE-S3 (AES256) by default, SSE-KMS when `kms_key_arn` is set |
| `aws_s3_bucket_versioning.this` | Versioning on, so an overwrite or delete is recoverable for 30 days |
| `aws_s3_bucket_lifecycle_configuration.this` | Transition to STANDARD_IA, expire after `retention_days`, clean up noncurrent versions and incomplete uploads |
| `aws_s3_bucket_policy.this` | Deny any request not made over TLS; optionally allow S3 server access log delivery from this account |

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `bucket_name` | `string` | (required) | Globally unique bucket name, 3 to 63 lowercase characters |
| `retention_days` | `number` | `365` | Days before log objects expire. Must be greater than `transition_to_ia_days` |
| `transition_to_ia_days` | `number` | `30` | Days before objects move to STANDARD_IA. At least 30 |
| `kms_key_arn` | `string` | `null` | Customer-managed KMS key for SSE-KMS. Null means SSE-S3 |
| `allow_s3_server_access_logs` | `bool` | `true` | Allow the S3 logging service to write server access logs here |
| `access_log_source_bucket_arns` | `list(string)` | `[]` | Buckets allowed to deliver logs. Empty means any bucket in this account |
| `force_destroy` | `bool` | `false` | Let `terraform destroy` delete a non-empty bucket |
| `tags` | `map(string)` | `{}` | Extra tags, merged over the defaults `managed-by = terraform` and `module = s3-log-bucket` |

## Outputs

| Name | Description |
|---|---|
| `bucket_name` | Bucket name, to use as a logging target |
| `bucket_arn` | Bucket ARN, for IAM policies that read the logs |
| `bucket_regional_domain_name` | Regional domain name of the bucket |

## Notes

- Leave `kms_key_arn` null unless you know every log source supports SSE-KMS on the destination. Elastic Load Balancing access logs, for example, document SSE-S3 as the only supported option. Check the docs for each service that writes here.
- The account ID in the log delivery policy comes from `data.aws_caller_identity`, so nothing account-specific is hard-coded.
- This module does not configure a provider. The caller sets the region and credentials.

## Before you apply

```bash
terraform fmt -recursive
terraform init
terraform validate
terraform plan
```

Run `tflint` and `checkov -d .` too if your team uses them.

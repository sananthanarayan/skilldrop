variable "bucket_name" {
  description = "Globally unique name for the log bucket. Lowercase letters, numbers, dots and hyphens, 3 to 63 characters."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be 3-63 characters of lowercase letters, numbers, dots and hyphens, starting and ending with a letter or number."
  }
}

variable "retention_days" {
  description = "Days to keep log objects before they expire. Must be longer than transition_to_ia_days."
  type        = number
  default     = 365

  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 3650 && floor(var.retention_days) == var.retention_days
    error_message = "retention_days must be a whole number between 1 and 3650."
  }
}

variable "transition_to_ia_days" {
  description = "Days after which log objects move to STANDARD_IA. S3 requires at least 30."
  type        = number
  default     = 30

  validation {
    condition     = var.transition_to_ia_days >= 30 && floor(var.transition_to_ia_days) == var.transition_to_ia_days
    error_message = "transition_to_ia_days must be a whole number of at least 30."
  }
}

variable "kms_key_arn" {
  description = "ARN of a customer-managed KMS key for SSE-KMS. Leave null to use SSE-S3 (AES256), which is what most AWS log delivery services require."
  type        = string
  default     = null

  validation {
    condition     = var.kms_key_arn == null || can(regex("^arn:aws[a-z-]*:kms:", var.kms_key_arn))
    error_message = "kms_key_arn must be null or a KMS key ARN starting with arn:aws...:kms:."
  }
}

variable "allow_s3_server_access_logs" {
  description = "Add a bucket policy statement that lets the S3 logging service write server access logs into this bucket from buckets in the same account."
  type        = bool
  default     = true
}

variable "access_log_source_bucket_arns" {
  description = "ARNs of the buckets allowed to deliver server access logs here. Empty means any bucket in this account."
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for arn in var.access_log_source_bucket_arns : can(regex("^arn:aws[a-z-]*:s3:::", arn))])
    error_message = "Each entry in access_log_source_bucket_arns must be an S3 bucket ARN (arn:aws:s3:::name)."
  }
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete the bucket even when it still holds logs. Keep false outside throwaway environments."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to add to every resource. Merged over the module defaults; your values win on a key clash."
  type        = map(string)
  default     = {}
}

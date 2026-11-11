variable "name" {
  description = "Name of the IAM role."
  type        = string
}

variable "bucket_arns" {
  description = "Bucket ARNs the task may access."
  type        = list(string)
  default     = ["arn:aws:s3:::*"]
}

variable "actions" {
  description = "S3 actions granted on the buckets."
  type        = list(string)
  default     = ["s3:GetObject", "s3:ListBucket", "s3:PutObject", "s3:DeleteObject"]
}

variable "tags" {
  description = "Tags merged onto every resource."
  type        = map(string)
  default     = {}
}

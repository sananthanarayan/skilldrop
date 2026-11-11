variable "name" {
  description = "Name of the main queue. The DLQ is named <name>-dlq."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{1,76}$", var.name))
    error_message = "name must be 1-76 characters: letters, numbers, hyphens or underscores."
  }
}

variable "source_topic_arn" {
  description = "ARN of the SNS topic allowed to send to the queue."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:sns:[a-z0-9-]+:[0-9]{12}:[A-Za-z0-9_-]+$", var.source_topic_arn))
    error_message = "source_topic_arn must be an SNS topic ARN."
  }
}

variable "retention_seconds" {
  description = "How long the main queue keeps messages."
  type        = number
  default     = 345600

  validation {
    condition     = var.retention_seconds >= 60 && var.retention_seconds <= 1209600
    error_message = "retention_seconds must be between 60 and 1209600."
  }
}

variable "dlq_retention_seconds" {
  description = "How long the DLQ keeps messages."
  type        = number
  default     = 1209600

  validation {
    condition     = var.dlq_retention_seconds >= 60 && var.dlq_retention_seconds <= 1209600
    error_message = "dlq_retention_seconds must be between 60 and 1209600."
  }
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for the main queue."
  type        = number
  default     = 60

  validation {
    condition     = var.visibility_timeout_seconds >= 0 && var.visibility_timeout_seconds <= 43200
    error_message = "visibility_timeout_seconds must be between 0 and 43200."
  }
}

variable "max_receive_count" {
  description = "Failed receives before a message moves to the DLQ."
  type        = number
  default     = 5

  validation {
    condition     = var.max_receive_count >= 1 && var.max_receive_count <= 1000
    error_message = "max_receive_count must be between 1 and 1000."
  }
}

variable "tags" {
  description = "Tags merged onto every resource."
  type        = map(string)
  default     = {}
}

# modules/orders-db/variables.tf

variable "environment" {
  type        = string
  description = "Environment name, e.g. staging or prod."
  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be staging or prod."
  }
}

variable "vpc_id" {
  type        = string
  description = "VPC the database runs in."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR of the VPC; the only range allowed to reach Postgres."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for the DB subnet group."
}

variable "instance_class" {
  type        = string
  description = "Instance class for the primary."
}

variable "replica_instance_class" {
  type        = string
  description = "Instance class for the reporting read replica."
  default     = "db.r7g.large"
}

variable "kms_key_arn" {
  type        = string
  description = "KMS key used to encrypt storage."
}

variable "tags" {
  type        = map(string)
  description = "Tags merged onto every resource."
  default     = {}
}

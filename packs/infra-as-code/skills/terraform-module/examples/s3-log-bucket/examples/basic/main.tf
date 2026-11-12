terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 7.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

module "access_logs" {
  source = "../.."

  bucket_name    = "acme-prod-access-logs-example"
  retention_days = 400

  tags = {
    "environment" = "prod"
    "owner"       = "platform-team"
  }
}

output "log_bucket_name" {
  value = module.access_logs.bucket_name
}

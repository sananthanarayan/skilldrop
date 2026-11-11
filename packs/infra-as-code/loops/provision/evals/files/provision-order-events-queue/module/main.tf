data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  tags      = merge(var.tags, { module = "order-events-queue" })
  queue_arn = "arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.name}"
}

resource "aws_kms_key" "queue" {
  description             = "${var.name} queue encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.key.json
  tags                    = local.tags
}

data "aws_iam_policy_document" "key" {
  statement {
    sid = "AccountAdmin"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid = "AllowSourceTopic"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["kms:GenerateDataKey", "kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [var.source_topic_arn]
    }
  }
}

resource "aws_sqs_queue" "dlq" {
  name                              = "${var.name}-dlq"
  message_retention_seconds         = var.dlq_retention_seconds
  kms_master_key_id                 = aws_kms_key.queue.arn
  kms_data_key_reuse_period_seconds = 300
  tags                              = local.tags
}

resource "aws_sqs_queue" "main" {
  name                              = var.name
  message_retention_seconds         = var.retention_seconds
  visibility_timeout_seconds        = var.visibility_timeout_seconds
  kms_master_key_id                 = aws_kms_key.queue.arn
  kms_data_key_reuse_period_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = local.tags
}

data "aws_iam_policy_document" "queue" {
  statement {
    sid = "AllowSourceTopicSend"
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    actions   = ["sqs:SendMessage"]
    resources = [local.queue_arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [var.source_topic_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id
  policy    = data.aws_iam_policy_document.queue.json
}

resource "aws_sns_topic_subscription" "main" {
  topic_arn            = var.source_topic_arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.main.arn
  raw_message_delivery = true
}

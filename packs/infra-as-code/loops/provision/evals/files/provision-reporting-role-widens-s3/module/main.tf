locals {
  tags = merge(var.tags, { module = "task-s3-read-role" })
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  name               = var.name
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "s3" {
  statement {
    sid       = "S3Access"
    actions   = var.actions
    resources = concat(var.bucket_arns, [for arn in var.bucket_arns : "${arn}/*"])
  }
}

resource "aws_iam_policy" "this" {
  name   = "${var.name}-s3"
  policy = data.aws_iam_policy_document.s3.json
  tags   = local.tags
}

resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.this.arn
}

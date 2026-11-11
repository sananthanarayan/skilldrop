output "queue_arn" {
  description = "ARN of the main queue."
  value       = aws_sqs_queue.main.arn
}

output "queue_url" {
  description = "URL of the main queue."
  value       = aws_sqs_queue.main.id
}

output "dlq_arn" {
  description = "ARN of the dead-letter queue."
  value       = aws_sqs_queue.dlq.arn
}

output "kms_key_arn" {
  description = "ARN of the KMS key encrypting both queues."
  value       = aws_kms_key.queue.arn
}

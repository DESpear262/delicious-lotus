output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role (for application permissions)"
  value       = aws_iam_role.ecs_task.arn
}

output "s3_access_policy_arn" {
  description = "ARN of the S3 access policy"
  value       = aws_iam_policy.s3_access.arn
}

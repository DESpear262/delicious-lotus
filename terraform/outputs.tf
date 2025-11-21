# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = module.ecr.repository_name
}

# S3 Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.database_name
}

output "database_url" {
  description = "Full PostgreSQL connection string"
  value       = "postgresql://${var.db_username}:${var.db_password}@${module.rds.endpoint}/${var.db_name}"
  sensitive   = true
}

# ElastiCache Outputs
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.endpoint
}

output "redis_url" {
  description = "Full Redis connection string"
  value       = "redis://${module.elasticache.endpoint}:6379/0"
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "ecs_task_definition_arn" {
  description = "ECS task definition ARN"
  value       = module.ecs.task_definition_arn
}

# IAM Outputs
output "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = module.iam.ecs_task_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN (for application permissions)"
  value       = module.iam.ecs_task_role_arn
}

# CloudWatch Outputs
output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.cloudwatch.log_group_name
}

# Deployment Instructions
output "deployment_instructions" {
  description = "Next steps for deployment"
  sensitive   = true
  value       = <<-EOT

  ========================================
  AWS Resources Created Successfully!
  ========================================

  Region: us-east-2

  Next Steps:

  1. Push Docker image to ECR:
     aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin ${module.ecr.repository_url}
     docker tag backend-api:latest ${module.ecr.repository_url}:latest
     docker push ${module.ecr.repository_url}:latest

  2. Initialize the database schema:
     Run the init.sql script from docker/postgres/init.sql against:
     ${module.rds.endpoint}/${var.db_name}

  3. ECS Service will automatically start once image is pushed

  4. Monitor deployment:
     aws ecs describe-services --cluster ${module.ecs.cluster_name} --services ${module.ecs.service_name} --region us-east-2

  5. View logs:
     aws logs tail ${module.cloudwatch.log_group_name} --follow --region us-east-2

  Connection Strings (save these securely):
  - Database: postgresql://${var.db_username}:${var.db_password}@${module.rds.endpoint}/${var.db_name}
  - Redis: redis://${module.elasticache.endpoint}:6379/0
  - S3 Bucket: ${module.s3.bucket_name}

  Estimated Monthly Cost: ~$30-50 USD
  ========================================
  EOT
}

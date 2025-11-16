variable "log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
}

variable "retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 7 # 7 days for dev, increase for prod
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region for CloudWatch resources"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster for monitoring"
  type        = string
}

variable "ecs_service_name" {
  description = "Name of the ECS service for monitoring"
  type        = string
}

variable "rds_instance_id" {
  description = "RDS instance ID for monitoring"
  type        = string
}

variable "elasticache_cluster_id" {
  description = "ElastiCache cluster ID for monitoring"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for monitoring"
  type        = string
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
}

variable "monthly_cost_threshold" {
  description = "Monthly cost threshold in USD for cost alarms"
  type        = number
  default     = 60
}

variable "s3_storage_threshold_gb" {
  description = "S3 storage threshold in GB for storage alarms"
  type        = number
  default     = 50
}

# Region Configuration
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-2" # CRITICAL: User specified us-east-2, NOT us-east-1
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ECR Configuration
variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "ai-video-backend"
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "Name of the S3 bucket for video storage"
  type        = string
  # Must be globally unique - user should override this
}

# RDS Configuration
variable "db_identifier" {
  description = "RDS instance identifier"
  type        = string
  default     = "ai-video-db"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ai_video_pipeline"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "ai_video_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  # Must be provided via terraform.tfvars or environment variable
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro" # Cheapest option ~$12/month
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20 # Minimum for gp3
}

# ElastiCache Configuration
variable "redis_cluster_id" {
  description = "ElastiCache cluster identifier"
  type        = string
  default     = "ai-video-redis"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro" # Cheapest option ~$11/month
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1 # Single node for MVP
}

# ECS Configuration
variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "ai-video-cluster"
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
  default     = "ai-video-backend-service"
}

variable "ecs_task_family" {
  description = "ECS task definition family"
  type        = string
  default     = "ai-video-backend"
}

variable "container_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "task_cpu" {
  description = "Task CPU units (1024 = 1 vCPU)"
  type        = string
  default     = "1024" # 1 vCPU
}

variable "task_memory" {
  description = "Task memory in MB"
  type        = string
  default     = "2048" # 2 GB
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1 # Single instance for MVP
}

# Application Configuration
variable "cors_origins" {
  description = "Comma-separated list of CORS origins"
  type        = string
  default     = "http://localhost:3000,http://localhost:5173"
}

variable "replicate_api_token" {
  description = "Replicate API token for AI services"
  type        = string
  sensitive   = true
  default     = "" # Must be provided
}

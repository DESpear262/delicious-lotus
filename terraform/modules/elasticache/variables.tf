variable "cluster_id" {
  description = "ElastiCache cluster identifier"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for cache subnet group"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for ElastiCache"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "auth_token" {
  description = "AUTH token for Redis (required when transit_encryption_enabled = true). Min 16 chars, alphanumeric."
  type        = string
  default     = null
  sensitive   = true
}

variable "transit_encryption_enabled" {
  description = "Enable encryption in transit for Redis"
  type        = bool
  default     = false
}

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

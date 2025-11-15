variable "log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
}

variable "retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 7  # 7 days for dev, increase for prod
}

variable "environment" {
  description = "Environment name"
  type        = string
}

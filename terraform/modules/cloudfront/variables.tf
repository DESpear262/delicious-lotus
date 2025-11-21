variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (origin)"
  type        = string
}

variable "cloudfront_secret" {
  description = "Secret header value to verify requests come from CloudFront"
  type        = string
  default     = "random-secret-change-me"
}

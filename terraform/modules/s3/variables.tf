variable "bucket_name" {
  description = "Name of the S3 bucket (must be globally unique)"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cors_allowed_origins" {
  description = "List of allowed origins for CORS (use ['*'] for development, specific domains for production)"
  type        = list(string)
  default     = ["*"]
}

variable "enable_cors" {
  description = "Enable CORS configuration for S3 bucket (set to false if using same-origin deployment)"
  type        = bool
  default     = true
}

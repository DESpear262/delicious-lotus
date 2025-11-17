resource "aws_s3_bucket" "storage" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
  }
}

# Allow public read access for generated content
# Note: Public ACLs are still blocked, but bucket policies are allowed
resource "aws_s3_bucket_public_access_block" "storage" {
  bucket = aws_s3_bucket.storage.id

  block_public_acls       = true
  block_public_policy     = false  # Allow bucket policies for public read
  ignore_public_acls      = true
  restrict_public_buckets = false  # Allow public bucket policies
}

# Bucket policy for public read access
resource "aws_s3_bucket_policy" "storage_public_read" {
  bucket = aws_s3_bucket.storage.id

  # Ensure public access block is configured first
  depends_on = [aws_s3_bucket_public_access_block.storage]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.storage.arn}/*"
      }
    ]
  })
}

# Enable versioning for uploads folder only (important files)
resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CORS configuration for direct uploads (only if enabled)
resource "aws_s3_bucket_cors_configuration" "storage" {
  count  = var.enable_cors ? 1 : 0
  bucket = aws_s3_bucket.storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    # Security: Use specific domains in production (e.g., ["https://delicious-lotus.vercel.app"])
    # For same-origin deployment (Option B), disable CORS entirely by setting enable_cors = false
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Lifecycle policies per storage architecture documentation
resource "aws_s3_bucket_lifecycle_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id

  # Temp files - 7 day auto-delete
  rule {
    id     = "delete-temp-files"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 7
    }
  }

  # Generated clips - 30 day auto-delete
  rule {
    id     = "delete-generations"
    status = "Enabled"

    filter {
      prefix = "generations/"
    }

    expiration {
      days = 30
    }
  }

  # Final compositions - 90 day auto-delete
  rule {
    id     = "delete-compositions"
    status = "Enabled"

    filter {
      prefix = "compositions/"
    }

    expiration {
      days = 90
    }
  }

  # Intelligent tiering for cost optimization after 30 days
  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects
    }

    transition {
      days          = 30
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

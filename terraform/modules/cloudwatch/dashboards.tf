# Application Dashboard
resource "aws_cloudwatch_dashboard" "application" {
  dashboard_name = "${var.environment}-application-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # ECS CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average", label = "Service Average" }],
            ["...", { stat = "Maximum", label = "Service Maximum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS CPU Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # ECS Memory Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "MemoryUtilization", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name, { stat = "Average", label = "Service Average" }],
            ["...", { stat = "Maximum", label = "Service Maximum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Memory Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # ECS Task Count
      {
        type = "metric"
        properties = {
          metrics = [
            ["ECS/ContainerInsights", "RunningTaskCount", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name],
            [".", "PendingTaskCount", ".", ".", ".", "."],
            [".", "DesiredTaskCount", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Task Count"
        }
      },
      # Network I/O
      {
        type = "metric"
        properties = {
          metrics = [
            ["ECS/ContainerInsights", "NetworkRxBytes", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name],
            [".", "NetworkTxBytes", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Network I/O"
        }
      },
      # Log-based Metrics (API Request Rate)
      {
        type = "log"
        properties = {
          query   = <<-QUERY
            SOURCE '${aws_cloudwatch_log_group.ecs.name}'
            | fields @timestamp
            | filter @message like /GET|POST|PUT|DELETE|PATCH/
            | stats count() as request_count by bin(1m)
          QUERY
          region  = var.aws_region
          title   = "API Request Rate (requests/minute)"
          stacked = false
        }
      },
      # API Error Rate
      {
        type = "log"
        properties = {
          query   = <<-QUERY
            SOURCE '${aws_cloudwatch_log_group.ecs.name}'
            | fields @timestamp
            | filter @message like /ERROR/ or @message like /4[0-9]{2}/ or @message like /5[0-9]{2}/
            | stats count() as error_count by bin(5m)
          QUERY
          region  = var.aws_region
          title   = "API Error Rate (4xx, 5xx)"
          stacked = false
        }
      }
    ]
  })
}

# Infrastructure Dashboard
resource "aws_cloudwatch_dashboard" "infrastructure" {
  dashboard_name = "${var.environment}-infrastructure-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # RDS CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS CPU Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # RDS Database Connections
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Database Connections"
        }
      },
      # RDS Storage Space
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Free Storage Space"
        }
      },
      # RDS IOPS
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "ReadIOPS", "DBInstanceIdentifier", var.rds_instance_id],
            [".", "WriteIOPS", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Read/Write IOPS"
        }
      },
      # ElastiCache CPU Utilization
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Redis CPU Utilization"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # ElastiCache Memory Usage
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Redis Memory Usage"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      # ElastiCache Cache Hit Rate
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CacheHits", "CacheClusterId", var.elasticache_cluster_id],
            [".", "CacheMisses", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Redis Cache Hits/Misses"
        }
      },
      # ElastiCache Evictions
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "Evictions", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Redis Evictions"
        }
      },
      # ElastiCache Connection Count
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CurrConnections", "CacheClusterId", var.elasticache_cluster_id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Redis Connection Count"
        }
      },
      # S3 Bucket Size
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/S3", "BucketSizeBytes", "BucketName", var.s3_bucket_name, "StorageType", "StandardStorage"]
          ]
          period = 86400
          stat   = "Average"
          region = var.aws_region
          title  = "S3 Storage Used (Bytes)"
        }
      },
      # S3 Number of Objects
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/S3", "NumberOfObjects", "BucketName", var.s3_bucket_name, "StorageType", "AllStorageTypes"]
          ]
          period = 86400
          stat   = "Average"
          region = var.aws_region
          title  = "S3 Number of Objects"
        }
      }
    ]
  })
}

# Cost Dashboard
resource "aws_cloudwatch_dashboard" "cost" {
  dashboard_name = "${var.environment}-cost-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # Estimated Monthly Cost
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"]
          ]
          period = 86400
          stat   = "Maximum"
          region = "us-east-1" # Billing metrics are only in us-east-1
          title  = "Estimated Monthly Cost (USD)"
        }
      },
      # Cost by Service
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "ServiceName", "AmazonEC2", "Currency", "USD"],
            ["...", "AmazonRDS", ".", "."],
            ["...", "AmazonS3", ".", "."],
            ["...", "AmazonElastiCache", ".", "."],
            ["...", "AmazonECR", ".", "."]
          ]
          period = 86400
          stat   = "Maximum"
          region = "us-east-1"
          title  = "Cost by Service (USD)"
        }
      },
      # ECS Task Running Hours
      {
        type = "log"
        properties = {
          query   = <<-QUERY
            SOURCE '${aws_cloudwatch_log_group.ecs.name}'
            | fields @timestamp
            | stats count() / 12 as running_hours by bin(1h)
          QUERY
          region  = var.aws_region
          title   = "ECS Task Running Hours (approx)"
          stacked = false
        }
      }
    ]
  })
}

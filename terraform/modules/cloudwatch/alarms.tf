# CRITICAL ALARMS - Immediate Action Required

# ECS Service Unhealthy (0 running tasks)
resource "aws_cloudwatch_metric_alarm" "ecs_no_running_tasks" {
  alarm_name          = "${var.environment}-ecs-no-running-tasks"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "CRITICAL: ECS service has no running tasks"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = {
    Name        = "${var.environment}-ecs-no-running-tasks"
    Environment = var.environment
    Severity    = "critical"
  }
}

# RDS CPU > 90% for 5 minutes
resource "aws_cloudwatch_metric_alarm" "rds_cpu_critical" {
  alarm_name          = "${var.environment}-rds-cpu-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 90
  alarm_description   = "CRITICAL: RDS CPU usage above 90% for 5 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.environment}-rds-cpu-critical"
    Environment = var.environment
    Severity    = "critical"
  }
}

# RDS Storage < 10% free
resource "aws_cloudwatch_metric_alarm" "rds_storage_critical" {
  alarm_name          = "${var.environment}-rds-storage-critical"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648 # 2GB (10% of 20GB)
  alarm_description   = "CRITICAL: RDS storage less than 10% free"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.environment}-rds-storage-critical"
    Environment = var.environment
    Severity    = "critical"
  }
}

# API Error Rate > 10% for 5 minutes (log-based metric)
resource "aws_cloudwatch_log_metric_filter" "api_errors" {
  name           = "${var.environment}-api-errors"
  log_group_name = aws_cloudwatch_log_group.ecs.name
  pattern        = "[timestamp, request_id, level=ERROR*, ...]"

  metric_transformation {
    name      = "APIErrors"
    namespace = "CustomMetrics/${var.environment}"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "api_requests" {
  name           = "${var.environment}-api-requests"
  log_group_name = aws_cloudwatch_log_group.ecs.name
  pattern        = "[timestamp, request_id, level, method=GET* || method=POST* || method=PUT* || method=DELETE* || method=PATCH*, ...]"

  metric_transformation {
    name      = "APIRequests"
    namespace = "CustomMetrics/${var.environment}"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "api_error_rate_critical" {
  alarm_name          = "${var.environment}-api-error-rate-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 10
  alarm_description   = "CRITICAL: API error rate above 10% for 5 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "(m1 / m2) * 100"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      metric_name = "APIErrors"
      namespace   = "CustomMetrics/${var.environment}"
      period      = 300
      stat        = "Sum"
    }
  }

  metric_query {
    id = "m2"
    metric {
      metric_name = "APIRequests"
      namespace   = "CustomMetrics/${var.environment}"
      period      = 300
      stat        = "Sum"
    }
  }

  tags = {
    Name        = "${var.environment}-api-error-rate-critical"
    Environment = var.environment
    Severity    = "critical"
  }
}

# WARNING ALARMS - Investigate Soon

# ECS CPU > 70% for 10 minutes
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_warning" {
  alarm_name          = "${var.environment}-ecs-cpu-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "WARNING: ECS CPU usage above 70% for 10 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = {
    Name        = "${var.environment}-ecs-cpu-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# ECS Memory > 80% for 10 minutes
resource "aws_cloudwatch_metric_alarm" "ecs_memory_warning" {
  alarm_name          = "${var.environment}-ecs-memory-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "WARNING: ECS memory usage above 80% for 10 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = {
    Name        = "${var.environment}-ecs-memory-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# RDS Connections > 80% of max (assuming max_connections = 100 for db.t4g.micro)
resource "aws_cloudwatch_metric_alarm" "rds_connections_warning" {
  alarm_name          = "${var.environment}-rds-connections-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80 # 80% of ~100 max connections
  alarm_description   = "WARNING: RDS connections above 80% of maximum"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.environment}-rds-connections-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# Redis Memory > 80%
resource "aws_cloudwatch_metric_alarm" "redis_memory_warning" {
  alarm_name          = "${var.environment}-redis-memory-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "WARNING: Redis memory usage above 80%"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    CacheClusterId = var.elasticache_cluster_id
  }

  tags = {
    Name        = "${var.environment}-redis-memory-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# COST ALARMS

# Monthly Cost > $60 (20% over budget)
resource "aws_cloudwatch_metric_alarm" "monthly_cost_warning" {
  alarm_name          = "${var.environment}-monthly-cost-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 86400
  statistic           = "Maximum"
  threshold           = var.monthly_cost_threshold
  alarm_description   = "WARNING: Monthly AWS cost exceeds $${var.monthly_cost_threshold}"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    Currency = "USD"
  }

  tags = {
    Name        = "${var.environment}-monthly-cost-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# S3 Storage > 50GB (unexpected growth)
resource "aws_cloudwatch_metric_alarm" "s3_storage_warning" {
  alarm_name          = "${var.environment}-s3-storage-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = 86400
  statistic           = "Average"
  threshold           = 53687091200 # 50GB in bytes
  alarm_description   = "WARNING: S3 storage exceeds ${var.s3_storage_threshold_gb}GB"
  alarm_actions       = [aws_sns_topic.alarms.arn]

  dimensions = {
    BucketName  = var.s3_bucket_name
    StorageType = "StandardStorage"
  }

  tags = {
    Name        = "${var.environment}-s3-storage-warning"
    Environment = var.environment
    Severity    = "warning"
  }
}

# ECS Task Stopped Unexpectedly (using EventBridge to SNS)
resource "aws_cloudwatch_event_rule" "ecs_task_stopped" {
  name        = "${var.environment}-ecs-task-stopped"
  description = "Notify when ECS tasks stop unexpectedly"

  event_pattern = jsonencode({
    source      = ["aws.ecs"]
    detail-type = ["ECS Task State Change"]
    detail = {
      clusterArn   = ["arn:aws:ecs:${var.aws_region}:*:cluster/${var.ecs_cluster_name}"]
      lastStatus   = ["STOPPED"]
      desiredStatus = ["RUNNING"]
      stoppedReason = [{ "anything-but" = "Scaling activity initiated by deployment" }]
    }
  })

  tags = {
    Name        = "${var.environment}-ecs-task-stopped"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "ecs_task_stopped_sns" {
  rule      = aws_cloudwatch_event_rule.ecs_task_stopped.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.alarms.arn
}

resource "aws_sns_topic_policy" "alarms_event_policy" {
  arn = aws_sns_topic.alarms.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgePublish"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.alarms.arn
      }
    ]
  })
}

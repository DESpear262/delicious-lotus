# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs" {
  name              = var.log_group_name
  retention_in_days = var.retention_days

  tags = {
    Name        = var.log_group_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "migrations" {
  name              = "/ecs/migrations"
  retention_in_days = 30

  tags = {
    Name        = "/ecs/migrations"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/postgresql"
  retention_in_days = 7

  tags = {
    Name        = "/aws/rds/postgresql"
    Environment = var.environment
  }
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.environment}-cloudwatch-alarms"

  tags = {
    Name        = "${var.environment}-cloudwatch-alarms"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "alarm_email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# CloudWatch Log Insights Saved Queries
resource "aws_cloudwatch_query_definition" "error_rate_by_endpoint" {
  name = "${var.environment}/error-rate-by-endpoint"

  log_group_names = [
    aws_cloudwatch_log_group.ecs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /ERROR/
    | parse @message /(?<method>[A-Z]+)\s+(?<endpoint>\/[^\s]*)/
    | stats count() as error_count by endpoint
    | sort error_count desc
  QUERY
}

resource "aws_cloudwatch_query_definition" "slowest_endpoints" {
  name = "${var.environment}/slowest-api-endpoints"

  log_group_names = [
    aws_cloudwatch_log_group.ecs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | parse @message /duration=(?<duration>[0-9.]+)/
    | parse @message /(?<method>[A-Z]+)\s+(?<endpoint>\/[^\s]*)/
    | stats avg(duration) as avg_duration, max(duration) as max_duration, count() as request_count by endpoint
    | sort avg_duration desc
  QUERY
}

resource "aws_cloudwatch_query_definition" "failed_generation_jobs" {
  name = "${var.environment}/failed-generation-jobs"

  log_group_names = [
    aws_cloudwatch_log_group.ecs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /generation.*failed/ or @message like /error.*generation/
    | parse @message /job_id=(?<job_id>[a-zA-Z0-9-]+)/
    | stats count() as failure_count by job_id
    | sort @timestamp desc
  QUERY
}

resource "aws_cloudwatch_query_definition" "database_connection_errors" {
  name = "${var.environment}/database-connection-errors"

  log_group_names = [
    aws_cloudwatch_log_group.ecs.name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /database/ and (@message like /error/ or @message like /timeout/ or @message like /connection/)
    | stats count() as error_count by bin(5m)
    | sort @timestamp desc
  QUERY
}

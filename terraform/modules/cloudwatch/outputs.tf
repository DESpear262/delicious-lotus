# Log Groups
output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs.arn
}

output "migrations_log_group_name" {
  description = "Name of the migrations CloudWatch log group"
  value       = aws_cloudwatch_log_group.migrations.name
}

output "rds_log_group_name" {
  description = "Name of the RDS CloudWatch log group"
  value       = aws_cloudwatch_log_group.rds.name
}

# SNS Topic
output "sns_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms"
  value       = aws_sns_topic.alarms.arn
}

# Dashboard URLs
output "application_dashboard_url" {
  description = "URL to the Application Dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.application.dashboard_name}"
}

output "infrastructure_dashboard_url" {
  description = "URL to the Infrastructure Dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.infrastructure.dashboard_name}"
}

output "cost_dashboard_url" {
  description = "URL to the Cost Dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cost.dashboard_name}"
}

# Alarm Names (for reference)
output "critical_alarms" {
  description = "List of critical alarm names"
  value = [
    aws_cloudwatch_metric_alarm.ecs_no_running_tasks.alarm_name,
    aws_cloudwatch_metric_alarm.rds_cpu_critical.alarm_name,
    aws_cloudwatch_metric_alarm.rds_storage_critical.alarm_name,
    aws_cloudwatch_metric_alarm.api_error_rate_critical.alarm_name
  ]
}

output "warning_alarms" {
  description = "List of warning alarm names"
  value = [
    aws_cloudwatch_metric_alarm.ecs_cpu_warning.alarm_name,
    aws_cloudwatch_metric_alarm.ecs_memory_warning.alarm_name,
    aws_cloudwatch_metric_alarm.rds_connections_warning.alarm_name,
    aws_cloudwatch_metric_alarm.redis_memory_warning.alarm_name
  ]
}

output "cost_alarms" {
  description = "List of cost alarm names"
  value = [
    aws_cloudwatch_metric_alarm.monthly_cost_warning.alarm_name,
    aws_cloudwatch_metric_alarm.s3_storage_warning.alarm_name
  ]
}

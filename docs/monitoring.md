# Monitoring and Observability Guide

This document describes the monitoring, alerting, and logging infrastructure for the AI Video Generation Pipeline.

## Overview

The system uses AWS CloudWatch for comprehensive monitoring across:
- **Application Monitoring**: ECS tasks, API performance, and application metrics
- **Infrastructure Monitoring**: RDS, ElastiCache, S3, and network resources
- **Cost Monitoring**: Monthly AWS costs and storage usage
- **Alerting**: Email notifications via SNS for critical issues and warnings
- **Logging**: Centralized log aggregation with CloudWatch Logs

## CloudWatch Dashboards

### 1. Application Dashboard

**Access**: Run `terraform output application_dashboard_url` or navigate to:
```
AWS Console → CloudWatch → Dashboards → [environment]-application-dashboard
```

**Metrics Displayed**:

#### ECS Metrics
- **CPU Utilization**: Service average and maximum CPU usage
  - Normal: <50%
  - Warning: >70% (indicates need for scaling)
  - Critical: >90% (performance degradation)
- **Memory Utilization**: Service average and maximum memory usage
  - Normal: <60%
  - Warning: >80% (risk of OOM errors)
  - Critical: >90% (tasks may be killed)
- **Task Count**: Running, pending, and desired task counts
  - Should always have at least 1 running task
  - Pending tasks indicate scaling events
- **Network I/O**: Bytes received and transmitted
  - Useful for understanding traffic patterns

#### Application Metrics
- **API Request Rate**: Requests per minute
  - Derived from application logs
  - Helps identify traffic spikes
- **API Error Rate**: 4xx and 5xx errors over time
  - Should be <1% under normal conditions
  - Spike indicates application issues

### 2. Infrastructure Dashboard

**Access**: Run `terraform output infrastructure_dashboard_url` or navigate to:
```
AWS Console → CloudWatch → Dashboards → [environment]-infrastructure-dashboard
```

**Metrics Displayed**:

#### RDS PostgreSQL
- **CPU Utilization**: Database server CPU usage
  - Normal: <40%
  - Warning: >70% (slow queries or high load)
  - Critical: >90% (database bottleneck)
- **Database Connections**: Active database connections
  - Max connections for db.t4g.micro: ~100
  - Warning threshold: 80 connections
- **Free Storage Space**: Available disk space
  - Critical: <2GB (10% of 20GB allocation)
  - Action: Increase allocated storage
- **Read/Write IOPS**: Database I/O operations per second
  - Useful for identifying I/O bottlenecks

#### ElastiCache Redis
- **CPU Utilization**: Redis server CPU usage
  - Normal: <30%
  - Redis is single-threaded, high CPU indicates bottleneck
- **Memory Usage Percentage**: Redis memory consumption
  - Normal: <70%
  - Warning: >80%
  - Action: Increase node size or enable eviction policies
- **Cache Hit Rate**: Cache hits vs misses
  - Good: >80% hit rate
  - Low hit rate indicates ineffective caching
- **Evictions**: Number of keys evicted due to memory pressure
  - Should be 0 under normal conditions
- **Connection Count**: Active Redis connections
  - Useful for detecting connection leaks

#### S3 Bucket
- **Storage Used**: Total bucket size in bytes
  - Monitored for unexpected growth
  - Alert threshold: 50GB
- **Number of Objects**: Total object count
  - Helps track storage growth over time

### 3. Cost Dashboard

**Access**: Run `terraform output cost_dashboard_url` or navigate to:
```
AWS Console → CloudWatch → Dashboards → [environment]-cost-dashboard
```

**Metrics Displayed**:
- **Estimated Monthly Cost**: Total AWS bill projection (USD)
  - Budget: $50/month (MVP)
  - Warning threshold: $60/month (20% over budget)
- **Cost by Service**: Breakdown of costs by AWS service
  - EC2 (ECS tasks)
  - RDS
  - S3
  - ElastiCache
  - ECR
- **ECS Task Running Hours**: Approximate task uptime
  - Useful for cost optimization

## CloudWatch Alarms

All alarms send notifications to the SNS topic subscribed to your email address.

### Critical Alarms (Immediate Action Required)

#### ECS Service Unhealthy
- **Metric**: RunningTaskCount < 1
- **Duration**: 2 minutes
- **Impact**: Application is completely down
- **Actions**:
  1. Check ECS service events: `aws ecs describe-services --cluster [cluster] --services [service]`
  2. Review CloudWatch logs for task failures
  3. Check recent deployments or configuration changes
  4. Manually scale up if needed: `aws ecs update-service --desired-count 1`

#### RDS CPU Critical
- **Metric**: CPUUtilization > 90%
- **Duration**: 5 minutes
- **Impact**: Database queries are slow, API timeouts
- **Actions**:
  1. Check slow query logs in CloudWatch Logs
  2. Review active queries: `SELECT * FROM pg_stat_activity;`
  3. Kill long-running queries if needed
  4. Consider upgrading instance class if sustained

#### RDS Storage Critical
- **Metric**: FreeStorageSpace < 2GB (10% of 20GB)
- **Duration**: 5 minutes
- **Impact**: Database writes may fail, data loss risk
- **Actions**:
  1. Check storage usage: Query largest tables
  2. Clean up old data if possible
  3. Increase allocated storage via Terraform:
     ```hcl
     db_allocated_storage = 30  # Increase from 20
     ```
  4. Apply immediately via console if urgent

#### API Error Rate Critical
- **Metric**: (API Errors / API Requests) * 100 > 10%
- **Duration**: 5 minutes
- **Impact**: Application is returning errors to users
- **Actions**:
  1. Run saved query "Error Rate by Endpoint" in CloudWatch Insights
  2. Check application logs for error messages
  3. Verify dependencies (DB, Redis, S3, Replicate API)
  4. Check /health/detailed endpoint for dependency status

#### ECS Task Stopped Unexpectedly
- **Trigger**: EventBridge rule for task state changes
- **Impact**: Task crashed due to OOM, application error, or health check failure
- **Actions**:
  1. Check stopped task reason in ECS console
  2. Review CloudWatch logs from stopped task
  3. Check health check endpoint logs
  4. Increase memory allocation if OOM error

### Warning Alarms (Investigate Soon)

#### ECS CPU Warning
- **Metric**: CPUUtilization > 70%
- **Duration**: 10 minutes
- **Actions**:
  1. Monitor for sustained high CPU
  2. Review application performance metrics
  3. Consider horizontal scaling (increase desired count)
  4. Optimize application code if needed

#### ECS Memory Warning
- **Metric**: MemoryUtilization > 80%
- **Duration**: 10 minutes
- **Actions**:
  1. Monitor for memory leaks
  2. Review application memory usage patterns
  3. Consider vertical scaling (increase task memory)
  4. Check for memory-intensive operations

#### RDS Connections Warning
- **Metric**: DatabaseConnections > 80
- **Duration**: 10 minutes
- **Actions**:
  1. Check for connection leaks in application
  2. Review connection pool settings
  3. Consider implementing connection pooling (PgBouncer)
  4. Verify connections are being properly closed

#### Redis Memory Warning
- **Metric**: DatabaseMemoryUsagePercentage > 80%
- **Duration**: 10 minutes
- **Actions**:
  1. Review Redis memory usage: `redis-cli info memory`
  2. Check eviction policy and configure if needed
  3. Consider upgrading to larger node type
  4. Review cache key expiration settings

### Cost Alarms

#### Monthly Cost Warning
- **Metric**: EstimatedCharges > $60 USD
- **Duration**: 1 day
- **Actions**:
  1. Review Cost Explorer in AWS Console
  2. Identify unexpected cost increases
  3. Check for idle resources
  4. Review S3 storage and ECS task running hours

#### S3 Storage Warning
- **Metric**: BucketSizeBytes > 50GB
- **Duration**: 1 day
- **Actions**:
  1. Verify S3 lifecycle policies are working
  2. Check for orphaned temporary files
  3. Review retention periods
  4. Consider moving old data to Glacier

## CloudWatch Logs

### Log Groups

#### `/ecs/[environment]/ai-video-backend`
- **Purpose**: FastAPI application logs
- **Retention**: 7 days (dev), 30 days (prod)
- **Format**: JSON structured logs
- **Fields**:
  - `timestamp`: ISO 8601 timestamp
  - `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - `message`: Log message
  - `request_id`: Unique request identifier
  - `user_id`: Authenticated user (if applicable)
  - `endpoint`: API endpoint
  - `method`: HTTP method
  - `duration`: Request duration (ms)
  - `status_code`: HTTP response code

#### `/ecs/migrations`
- **Purpose**: Database migration logs
- **Retention**: 30 days
- **Use**: Debugging migration issues

#### `/aws/rds/postgresql`
- **Purpose**: PostgreSQL slow queries and errors
- **Retention**: 7 days
- **Use**: Database performance troubleshooting

### Log Insights Saved Queries

#### 1. Error Rate by Endpoint
```
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message /(?<method>[A-Z]+)\s+(?<endpoint>\/[^\s]*)/
| stats count() as error_count by endpoint
| sort error_count desc
```

**Use**: Identify which API endpoints are generating the most errors

#### 2. Slowest API Endpoints
```
fields @timestamp, @message
| parse @message /duration=(?<duration>[0-9.]+)/
| parse @message /(?<method>[A-Z]+)\s+(?<endpoint>\/[^\s]*)/
| stats avg(duration) as avg_duration, max(duration) as max_duration, count() as request_count by endpoint
| sort avg_duration desc
```

**Use**: Find performance bottlenecks in the API

#### 3. Failed Generation Jobs
```
fields @timestamp, @message
| filter @message like /generation.*failed/ or @message like /error.*generation/
| parse @message /job_id=(?<job_id>[a-zA-Z0-9-]+)/
| stats count() as failure_count by job_id
| sort @timestamp desc
```

**Use**: Track video generation failures

#### 4. Database Connection Errors
```
fields @timestamp, @message
| filter @message like /database/ and (@message like /error/ or @message like /timeout/ or @message like /connection/)
| stats count() as error_count by bin(5m)
| sort @timestamp desc
```

**Use**: Detect database connectivity issues

## Health Check Endpoints

The application provides two health check endpoints:

### `/health`
- **Type**: Basic liveness check
- **Response**: `200 OK` with `{"status": "healthy"}`
- **Use**: Kubernetes/ECS liveness probes
- **Fast**: <50ms response time

### `/health/detailed`
- **Type**: Detailed dependency checks
- **Checks**:
  - Database connectivity (PostgreSQL)
  - Redis connectivity (ElastiCache)
  - S3 access (bucket read/write test)
  - Replicate API reachability
- **Response**:
  - `200 OK`: All dependencies healthy
  - `503 Service Unavailable`: One or more dependencies down
- **Format**:
  ```json
  {
    "status": "healthy",
    "checks": {
      "database": "healthy",
      "redis": "healthy",
      "s3": "healthy",
      "replicate_api": "healthy"
    }
  }
  ```
- **Use**: Pre-deployment smoke tests, monitoring dashboards

## On-Call Runbook

### Responding to Alarms

1. **Check the alarm name and severity** in the email notification
2. **Assess impact**: Is the application down or degraded?
3. **Follow the specific playbook** for that alarm (see above)
4. **Document actions taken** for post-incident review
5. **Update stakeholders** if user-facing impact

### Common Troubleshooting Steps

#### Application is Down (No Running Tasks)
```bash
# Check service status
aws ecs describe-services --cluster ai-video-cluster --services ai-video-backend-service

# Check recent task failures
aws ecs list-tasks --cluster ai-video-cluster --desired-status STOPPED --max-results 10

# View task stop reason
aws ecs describe-tasks --cluster ai-video-cluster --tasks [task-id]

# Check CloudWatch logs
aws logs tail /ecs/dev/ai-video-backend --follow

# Force new deployment
aws ecs update-service --cluster ai-video-cluster --service ai-video-backend-service --force-new-deployment
```

#### High CPU or Memory
```bash
# Check current metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=ai-video-backend-service Name=ClusterName,Value=ai-video-cluster \
  --statistics Average --start-time 2024-01-01T00:00:00Z --end-time 2024-01-01T01:00:00Z --period 300

# Scale up tasks temporarily
aws ecs update-service --cluster ai-video-cluster --service ai-video-backend-service --desired-count 2

# Review logs for resource-intensive operations
aws logs tail /ecs/dev/ai-video-backend --filter-pattern "duration" --since 1h
```

#### Database Issues
```bash
# Connect to RDS instance
psql -h [rds-endpoint] -U ai_video_admin -d ai_video_pipeline

# Check active queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

# Check database size
SELECT pg_size_pretty(pg_database_size('ai_video_pipeline'));

# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

#### Redis Issues
```bash
# Connect to Redis
redis-cli -h [elasticache-endpoint]

# Check memory usage
INFO memory

# Check connected clients
CLIENT LIST

# Check slow log
SLOWLOG GET 10
```

### Escalation Path

1. **Check documentation** (this file) for standard procedures
2. **Review recent changes** in Git history and AWS Console
3. **Consult with team members** via Slack/chat
4. **Create incident ticket** if issue is prolonged
5. **Post-incident review** to prevent recurrence

## Testing Alarms

To verify alarms are working correctly:

### Test ECS CPU Alarm
```bash
# Start a CPU stress container
aws ecs run-task --cluster ai-video-cluster --task-definition stress-test --launch-type FARGATE
```

### Test RDS Alarms
```sql
-- Generate high CPU load
SELECT COUNT(*) FROM generate_series(1, 10000000);
```

### Test Cost Alarm
```bash
# Temporarily lower threshold via Terraform
monthly_cost_threshold = 1  # Will trigger immediately
terraform apply
```

## Best Practices

1. **Review dashboards daily** during initial deployment
2. **Set up email filters** to route alarms appropriately
3. **Document all alarm responses** for knowledge sharing
4. **Tune alarm thresholds** based on actual usage patterns
5. **Test alarm responses** quarterly with mock scenarios
6. **Keep runbooks updated** as infrastructure changes
7. **Use CloudWatch Insights** for deep troubleshooting
8. **Export and analyze logs** for long-term trends

## Additional Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [ECS CloudWatch Metrics](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cloudwatch-metrics.html)
- [RDS Enhanced Monitoring](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html)

## Getting Dashboard URLs

After applying Terraform, get direct links to dashboards:

```bash
terraform output application_dashboard_url
terraform output infrastructure_dashboard_url
terraform output cost_dashboard_url
```

## Viewing Alarms

List all active alarms:
```bash
aws cloudwatch describe-alarms --alarm-name-prefix dev- --query 'MetricAlarms[*].[AlarmName,StateValue]' --output table
```

Check alarm history:
```bash
aws cloudwatch describe-alarm-history --alarm-name dev-ecs-cpu-warning --max-records 10
```

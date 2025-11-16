# Troubleshooting Guide
## AI Video Generation Pipeline - Operational Playbook

This guide provides solutions to common issues you may encounter when operating the AI Video Generation Pipeline.

**Last Updated:** 2025-11-15
**Version:** 1.0.0 (MVP)
**Region:** us-east-2

---

## Table of Contents

1. [Container Startup Failures](#container-startup-failures)
2. [Database Connection Issues](#database-connection-issues)
3. [S3 Access Problems](#s3-access-problems)
4. [Frontend Not Loading](#frontend-not-loading)
5. [API Errors](#api-errors)
6. [Video Generation Failures](#video-generation-failures)
7. [Performance Issues](#performance-issues)
8. [Common Commands](#common-commands)

---

## Container Startup Failures

### ECS Task Won't Start

**Symptoms:**
- Task status stuck at `PENDING`
- Task immediately transitions to `STOPPED`
- No tasks running in ECS service

**Diagnostic Steps:**

```bash
# Check task status
CLUSTER_NAME=$(cd terraform && terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(cd terraform && terraform output -raw ecs_service_name)

aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].events[0:5]'

# Check stopped tasks
aws ecs list-tasks \
  --cluster $CLUSTER_NAME \
  --desired-status STOPPED \
  --region us-east-2

# Get task failure reason
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --desired-status STOPPED --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $TASK_ARN \
  --region us-east-2 \
  --query 'tasks[0].stoppedReason'
```

**Common Causes & Solutions:**

#### 1. Image Pull Failure
**Error:** `CannotPullContainerError: pull image manifest has been retried`

**Solution:**
```bash
# Verify ECR repository exists
ECR_URL=$(cd terraform && terraform output -raw ecr_repository_url)
aws ecr describe-repositories --region us-east-2 | grep ai-video-backend

# Verify image exists in ECR
aws ecr list-images \
  --repository-name ai-video-backend \
  --region us-east-2

# If no images, rebuild and push
docker build -t delicious-lotus-backend:latest -f backend/Dockerfile backend/
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $ECR_URL
docker tag delicious-lotus-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

#### 2. Insufficient Memory/CPU
**Error:** `OutOfMemoryError` or `ResourceInitializationError`

**Solution:**
```bash
# Increase task resources in terraform/variables.tf
vim terraform/terraform.tfvars

# Increase memory
# task_memory = "4096"  # 4 GB instead of 2 GB

terraform plan -out=tfplan
terraform apply tfplan
```

#### 3. Subnet Has No Internet Access
**Error:** `CannotPullContainerError: failed to pull image`

**Solution:**
```bash
# Check if subnet has route to Internet Gateway
SUBNET_ID=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets[0]' \
  --output text)

aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
  --region us-east-2 \
  --query 'RouteTables[0].Routes'

# Should see route: 0.0.0.0/0 → igw-xxxxx

# If missing, enable public IP assignment
# Update terraform/modules/ecs/main.tf
# assign_public_ip = true
```

#### 4. Invalid Environment Variables
**Error:** Task starts then immediately stops

**Solution:**
```bash
# Check CloudWatch logs for startup errors
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --since 5m

# Look for errors like:
# - "DATABASE_URL is required"
# - "Invalid REPLICATE_API_TOKEN"
# - "Cannot connect to database"

# Fix environment variables in terraform.tfvars
vim terraform/terraform.tfvars
# Update db_password, replicate_api_token, etc.

terraform apply -auto-approve
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2
```

### Health Check Failing

**Symptoms:**
- Task starts but fails health checks
- Task status: `UNHEALTHY`
- Task repeatedly restarts

**Diagnostic Steps:**

```bash
# Check health check configuration
aws ecs describe-task-definition \
  --task-definition ai-video-backend \
  --region us-east-2 \
  --query 'taskDefinition.containerDefinitions[0].healthCheck'

# Test health endpoint manually
TASK_IP=$(aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text | xargs aws ec2 describe-network-interfaces --network-interface-ids --region us-east-2 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

curl http://$TASK_IP:8000/health
```

**Solutions:**

#### 1. Application Not Ready
**Error:** Health endpoint returns 503 or connection refused

**Solution:**
```bash
# Increase health check grace period
# Edit terraform/modules/ecs/main.tf
# health_check_grace_period_seconds = 60  # Increase from default

# Or fix application startup
# Check CloudWatch logs for database connection delays
aws logs tail /ecs/dev/ai-video-backend --region us-east-2 --follow
```

#### 2. Wrong Health Check Path
**Error:** Health endpoint returns 404

**Solution:**
```bash
# Verify health endpoint exists in backend
# Check backend/app/main.py for:
# @app.get("/health")

# If missing, add health endpoint or update ECS health check path
```

### Out of Memory Errors

**Symptoms:**
- Task crashes during video processing
- CloudWatch logs show `MemoryError` or `Out of memory`

**Solution:**

```bash
# Monitor memory usage
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].containers[0].memory*'

# Increase task memory
vim terraform/terraform.tfvars
# task_memory = "4096"  # 4 GB instead of 2 GB

terraform apply -auto-approve

# Or optimize application memory usage
# - Reduce max_concurrent_jobs
# - Process videos in chunks
# - Clear intermediate files more frequently
```

---

## Database Connection Issues

### Connection Refused

**Symptoms:**
- Application logs: `could not connect to server: Connection refused`
- Health check fails on database dependency

**Diagnostic Steps:**

```bash
# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address,Endpoint.Port]'

# Should return: ["available", "ai-video-db.xxx.rds.amazonaws.com", 5432]
```

**Solutions:**

#### 1. RDS Not Running
**Error:** Instance status is not "available"

**Solution:**
```bash
# Check instance status
aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].DBInstanceStatus'

# Common statuses:
# - "creating" → Wait for creation to complete
# - "stopped" → Start the instance
# - "backing-up" → Wait for backup to complete

# Start stopped instance
aws rds start-db-instance \
  --db-instance-identifier ai-video-db \
  --region us-east-2
```

#### 2. Security Group Blocks Access
**Error:** Connection times out after 60 seconds

**Solution:**
```bash
# Get RDS security group
RDS_SG=$(aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)

# Check inbound rules
aws ec2 describe-security-groups \
  --group-ids $RDS_SG \
  --region us-east-2 \
  --query 'SecurityGroups[0].IpPermissions'

# Should allow port 5432 from ECS security group
# If missing, add rule via Terraform or AWS CLI

# Get ECS security group ID
ECS_SG=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0]' \
  --output text)

# Add rule to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG \
  --region us-east-2
```

#### 3. Wrong Database Credentials
**Error:** `password authentication failed for user "ai_video_admin"`

**Solution:**
```bash
# Verify DATABASE_URL in ECS task definition
aws ecs describe-task-definition \
  --task-definition ai-video-backend \
  --region us-east-2 \
  --query 'taskDefinition.containerDefinitions[0].environment[?name==`DATABASE_URL`]'

# Update password in terraform.tfvars and redeploy
vim terraform/terraform.tfvars
# db_password = "correct_password_here"

terraform apply -auto-approve
```

### Connection Timeout

**Symptoms:**
- Database queries hang for 60+ seconds
- Application becomes unresponsive

**Solution:**

```bash
# Check VPC/subnet configuration
aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].[DBSubnetGroup.VpcId,PubliclyAccessible]'

# Ensure:
# - RDS is in same VPC as ECS tasks
# - RDS is NOT publicly accessible (security)
# - ECS and RDS subnets can communicate

# Test connectivity from ECS task
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --container ai-video-backend \
  --command "nc -zv ai-video-db.xxx.rds.amazonaws.com 5432" \
  --interactive \
  --region us-east-2
```

### Too Many Connections

**Symptoms:**
- Error: `FATAL: too many connections for role "ai_video_admin"`
- Intermittent database errors under load

**Solution:**

```bash
# Check current connections
./scripts/migrate-db.sh status
# Then run in psql:
# SELECT count(*) FROM pg_stat_activity WHERE usename = 'ai_video_admin';

# Check RDS max_connections parameter
aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].DBParameterGroups'

# Typical max_connections for db.t4g.micro: ~80

# Solutions:
# 1. Reduce connection pool size in application
#    Update .env: DB_POOL_SIZE=5 (down from 10)

# 2. Upgrade RDS instance class for more connections
vim terraform/terraform.tfvars
# db_instance_class = "db.t4g.small"  # ~160 connections

# 3. Implement connection pooling with PgBouncer (future)
```

---

## S3 Access Problems

### Access Denied Errors

**Symptoms:**
- Error: `AccessDenied: Access Denied` when uploading/downloading
- Application can't read or write S3 objects

**Diagnostic Steps:**

```bash
# Check ECS task IAM role
TASK_ROLE_ARN=$(aws ecs describe-task-definition \
  --task-definition ai-video-backend \
  --region us-east-2 \
  --query 'taskDefinition.taskRoleArn' \
  --output text)

# List role policies
aws iam list-attached-role-policies \
  --role-name $(echo $TASK_ROLE_ARN | cut -d/ -f2)

# Get policy details
aws iam get-role-policy \
  --role-name $(echo $TASK_ROLE_ARN | cut -d/ -f2) \
  --policy-name ai-video-s3-access
```

**Solutions:**

#### 1. Missing IAM Permissions
**Error:** Task role doesn't have S3 access

**Solution:**
```bash
# Check terraform/modules/iam/main.tf
# Ensure task role has S3 permissions

# Policy should include:
# - s3:PutObject
# - s3:GetObject
# - s3:DeleteObject
# - s3:ListBucket

# Reapply Terraform
cd terraform
terraform apply -auto-approve
```

#### 2. Wrong Bucket Name
**Error:** `NoSuchBucket: The specified bucket does not exist`

**Solution:**
```bash
# Verify bucket exists
S3_BUCKET=$(cd terraform && terraform output -raw s3_bucket_name)
aws s3 ls s3://$S3_BUCKET --region us-east-2

# If bucket doesn't exist, check Terraform state
terraform state list | grep s3

# Recreate bucket if needed
terraform taint module.s3.aws_s3_bucket.main
terraform apply
```

#### 3. Bucket Policy Conflicts
**Error:** Access denied despite correct IAM role

**Solution:**
```bash
# Check bucket policy
aws s3api get-bucket-policy \
  --bucket $S3_BUCKET \
  --region us-east-2

# Remove restrictive bucket policy if present
aws s3api delete-bucket-policy \
  --bucket $S3_BUCKET \
  --region us-east-2

# Rely on IAM role permissions instead
```

### Slow Uploads/Downloads

**Symptoms:**
- S3 uploads take minutes for small files
- Timeouts during large video uploads

**Solution:**

```bash
# Check NAT gateway status (if using private subnets)
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" \
  --region us-east-2

# For Fargate in public subnet, ensure public IP assigned
# Check terraform/modules/ecs/main.tf:
# assign_public_ip = true

# Use multipart upload for large files (>100MB)
# Already implemented in backend/app/services/storage.py

# Monitor S3 CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BytesUploaded \
  --dimensions Name=BucketName,Value=$S3_BUCKET \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-2
```

### Lifecycle Policy Not Working

**Symptoms:**
- Temporary files not being deleted
- S3 costs increasing despite lifecycle policies

**Solution:**

```bash
# Verify lifecycle policy exists
aws s3api get-bucket-lifecycle-configuration \
  --bucket $S3_BUCKET \
  --region us-east-2

# Expected output: JSON with 7-day, 30-day, 90-day rules

# If missing, reapply via Terraform
cd terraform/modules/s3
terraform apply -auto-approve

# Manually check old files
aws s3 ls s3://$S3_BUCKET/temp/ --recursive --region us-east-2

# Note: Lifecycle policies run once daily at midnight UTC
# Files are deleted 24-48 hours after expiration date
```

---

## Frontend Not Loading

### Static Files 404 Errors

**Symptoms:**
- Browser shows blank page
- Console errors: `GET /assets/index.js 404 Not Found`
- FastAPI logs: `404 Not Found: /assets/index.js`

**Solutions:**

#### 1. Frontend Not Built
**Error:** `/app/frontend/dist` directory missing

**Solution:**
```bash
# Build frontend
cd frontend
npm install
npm run build

# Verify build output
ls -la dist/

# Rebuild Docker image
cd ..
docker build -t delicious-lotus-backend:latest -f backend/Dockerfile backend/

# Push to ECR and redeploy
./scripts/deploy.sh apply
```

#### 2. Wrong Static File Path
**Error:** FastAPI can't find `/app/frontend/dist`

**Solution:**
```bash
# Check Dockerfile COPY statement
# backend/Dockerfile should have:
# COPY --from=frontend-build /app/dist /app/frontend/dist

# Verify path in container
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --container ai-video-backend \
  --command "ls -la /app/frontend/dist" \
  --interactive \
  --region us-east-2
```

#### 3. Static Mount Configuration Wrong
**Error:** FastAPI not serving static files

**Solution:**
```python
# Check backend/app/main.py
# Should have:
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="/app/frontend/dist", html=True), name="frontend")

# Ensure this is AFTER API routes
# API routes must be registered first:
app.include_router(api_router, prefix="/api/v1")
app.mount("/", StaticFiles(...))  # Last
```

### CORS Errors

**Symptoms:**
- Browser console: `CORS policy: No 'Access-Control-Allow-Origin' header`
- API calls fail from frontend

**Note:** With Option B deployment (same origin), CORS should NOT occur.

**If it does occur:**

```bash
# This indicates frontend and backend on different domains
# Verify SERVE_FRONTEND=true in environment

# Check FastAPI CORS middleware
# backend/app/main.py should NOT need CORS middleware
# for same-origin requests

# If using ALB or separate domains, add CORS:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Blank Page / White Screen

**Symptoms:**
- Browser loads but shows blank page
- No JavaScript errors in console
- Network tab shows successful API calls

**Solutions:**

#### 1. Check Browser Console
```javascript
// Look for:
// - React errors
// - API endpoint mismatches
// - Missing environment variables
```

#### 2. Verify API Base URL
```bash
# Frontend should make requests to same origin
# Check frontend/.env or vite.config.ts

# For production:
# VITE_API_BASE_URL=/api/v1

# NOT: http://localhost:8000/api/v1
```

#### 3. Check React Router Configuration
```javascript
// frontend/src/main.tsx
// Ensure basename matches deployment path

import { BrowserRouter } from 'react-router-dom'

<BrowserRouter basename="/">
  <App />
</BrowserRouter>
```

---

## API Errors

### 500 Internal Server Error

**Symptoms:**
- API returns 500 status code
- Generic error message
- Application appears broken

**Diagnostic Steps:**

```bash
# Check CloudWatch logs for stack traces
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --follow \
  --filter-pattern "ERROR"

# Look for:
# - Python exceptions
# - Database errors
# - Replicate API failures
# - FFmpeg errors
```

**Solutions:**

#### 1. Database Connection Lost
**Error:** `OperationalError: (psycopg2.OperationalError) server closed the connection`

**Solution:**
```bash
# Restart ECS service
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2

# Check database pool settings
# Update .env: DB_POOL_SIZE=10, DB_MAX_OVERFLOW=20
```

#### 2. Replicate API Error
**Error:** `ReplicateError: Invalid API token` or rate limit

**Solution:**
```bash
# Verify Replicate API token
curl -H "Authorization: Token $REPLICATE_API_TOKEN" https://api.replicate.com/v1/predictions

# Check Replicate account status
# https://replicate.com/account

# Update token in Terraform
vim terraform/terraform.tfvars
# replicate_api_token = "r8_new_token_here"

terraform apply -auto-approve
```

### 503 Service Unavailable

**Symptoms:**
- API returns 503
- Service exists but not responding

**Solutions:**

```bash
# Check ECS service running count
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].[runningCount,desiredCount]'

# Should be [1, 1] or higher

# If runningCount = 0:
# - Check task failures (see "Container Startup Failures")
# - Check CloudWatch logs for errors

# Force new deployment
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2
```

### Timeout Errors

**Symptoms:**
- API calls timeout after 30-60 seconds
- Long-running video generation jobs fail

**Solution:**

```bash
# Increase Replicate timeout
# Update backend/.env:
# REPLICATE_TIMEOUT_SECONDS=600  # 10 minutes

# Use WebSocket for long operations instead of HTTP
# Client should connect to /ws/{job_id} for progress updates

# Check if timeout is from client-side
# Frontend axios timeout:
axios.defaults.timeout = 120000;  // 2 minutes
```

---

## Video Generation Failures

### Replicate API Errors

**Symptoms:**
- Generation jobs stuck in "generating" status
- Clips fail with API errors

**Solutions:**

```bash
# Check Replicate API status
curl https://status.replicate.com/

# Verify API token and account balance
curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/account

# Check rate limits
# Free tier: Limited requests per hour
# Paid tier: Higher limits

# Implement retry logic (already in backend)
# Check REPLICATE_MAX_RETRIES in .env
```

### FFmpeg Processing Errors

**Symptoms:**
- Video composition fails
- Error: `FFmpeg command failed with code 1`

**Solutions:**

```bash
# Check CloudWatch logs for FFmpeg command
aws logs tail /ecs/dev/ai-video-backend --region us-east-2 --follow | grep ffmpeg

# Common errors:
# - "No such file or directory" → Clip not downloaded from S3
# - "Invalid data found" → Corrupted video file
# - "Too many packets buffered" → Memory limit

# Verify FFmpeg installed in container
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --container ai-video-backend \
  --command "ffmpeg -version" \
  --interactive \
  --region us-east-2
```

### Clip Download Failures

**Symptoms:**
- Error: `Failed to download clip from Replicate`
- Generated clips not appearing in S3

**Solution:**

```bash
# Check network connectivity from ECS to Replicate
# Ensure security group allows outbound HTTPS

# Check S3 upload permissions
# Verify task role has s3:PutObject permission

# Increase download timeout
# backend/.env:
# REPLICATE_TIMEOUT_SECONDS=600
```

---

## Performance Issues

### High Latency

**Symptoms:**
- API responses slow (>2 seconds)
- Video generation takes much longer than expected

**Diagnostic Steps:**

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=$SERVICE_NAME Name=ClusterName,Value=$CLUSTER_NAME \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region us-east-2
```

**Solutions:**

#### 1. High CPU Usage
```bash
# Increase task CPU
vim terraform/terraform.tfvars
# task_cpu = "2048"  # 2 vCPU instead of 1

terraform apply -auto-approve
```

#### 2. Database Slow Queries
```bash
# Enable slow query logging
# Check pg_stat_statements

# Add indexes for common queries
# See backend/migrations/

# Consider read replica for heavy reads (post-MVP)
```

#### 3. Cache Not Working
```bash
# Check Redis connectivity
aws elasticache describe-cache-clusters \
  --cache-cluster-id ai-video-redis \
  --region us-east-2 \
  --query 'CacheClusters[0].CacheClusterStatus'

# Verify cache hit rate in application logs
aws logs tail /ecs/dev/ai-video-backend --region us-east-2 | grep "cache hit"

# Check Redis memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name BytesUsedForCache \
  --dimensions Name=CacheClusterId,Value=ai-video-redis \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --region us-east-2
```

### Memory Leaks

**Symptoms:**
- Task memory usage gradually increases
- Task crashes after running for hours

**Solution:**

```bash
# Monitor memory over time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=$SERVICE_NAME Name=ClusterName,Value=$CLUSTER_NAME \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum \
  --region us-east-2

# If steadily increasing:
# - Check for unclosed file handles
# - Ensure FFmpeg processes terminate
# - Clear temp files after each job
# - Implement periodic task restart (e.g., daily)
```

---

## Common Commands

### View ECS Task Logs

```bash
# Tail logs in real-time
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --follow

# Filter for errors only
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --follow \
  --filter-pattern "ERROR"

# View last 100 lines
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --since 10m
```

### Connect to RDS (via Migration Task)

```bash
# Initialize database
./scripts/migrate-db.sh init

# Check migration status
./scripts/migrate-db.sh status

# Apply migrations
./scripts/migrate-db.sh migrate

# Direct connection (if bastion host configured)
psql $(cd terraform && terraform output -raw database_url)
```

### Invalidate Caches

```bash
# Clear Redis cache
REDIS_ENDPOINT=$(cd terraform && terraform output -raw redis_endpoint)

# Using redis-cli (if installed)
redis-cli -h $REDIS_ENDPOINT FLUSHALL

# Via ECS task
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --container ai-video-backend \
  --command "python -c 'import redis; r=redis.from_url(\"redis://$REDIS_ENDPOINT:6379/0\"); r.flushall()'" \
  --interactive \
  --region us-east-2
```

### Restart Services

```bash
# Restart ECS service (rolling update)
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2

# Check deployment status
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].deployments'

# Stop specific task (ECS will start a new one)
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs stop-task \
  --cluster $CLUSTER_NAME \
  --task $TASK_ARN \
  --region us-east-2
```

### Check Resource Utilization

```bash
# CPU and Memory
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].containers[0].[cpu,memory]'

# Database connections
./scripts/migrate-db.sh status
# Then in psql: SELECT count(*) FROM pg_stat_activity;

# S3 storage usage
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name) \
  --recursive \
  --human-readable \
  --summarize \
  --region us-east-2
```

### Manual Cleanup

```bash
# Delete old generations from database
# (Before S3 lifecycle policy removes files)
./scripts/migrate-db.sh status
# Then in psql:
# DELETE FROM generation_jobs WHERE status='completed' AND completed_at < NOW() - INTERVAL '7 days';

# Force S3 lifecycle cleanup (for testing)
aws s3 rm s3://$(cd terraform && terraform output -raw s3_bucket_name)/temp/ \
  --recursive \
  --region us-east-2

# Clean up old ECS task definitions
aws ecs list-task-definitions \
  --family-prefix ai-video-backend \
  --status INACTIVE \
  --region us-east-2 | jq -r '.taskDefinitionArns[]' | \
  xargs -I {} aws ecs delete-task-definition --task-definition {} --region us-east-2
```

### Emergency Procedures

```bash
# Stop all processing (pause service)
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 0 \
  --region us-east-2

# Resume processing
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 1 \
  --region us-east-2

# Rollback to previous task definition
# See "Rollback Procedures" in deployment-guide.md

# Emergency: Delete everything
./scripts/deploy.sh destroy
# WARNING: This deletes ALL data!
```

---

## Support & Resources

### Documentation
- [Deployment Guide](./deployment-guide.md)
- [Architecture Guide](./architecture.md)
- [Cost Tracking Guide](./cost-tracking.md)
- [Scaling Guide](./scaling.md)

### AWS Documentation
- [ECS Troubleshooting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html)
- [RDS Troubleshooting](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html)
- [S3 Troubleshooting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshooting.html)

### External Resources
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---

**Troubleshooting Guide Version:** 1.0.0
**Last Updated:** 2025-11-15
**Maintained by:** DevOps Team

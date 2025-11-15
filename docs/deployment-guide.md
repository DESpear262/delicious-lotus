# Deployment Guide
## AI Video Generation Pipeline - Production Deployment

This guide provides step-by-step instructions for deploying and managing the AI Video Generation Pipeline on AWS.

**Last Updated:** 2025-11-15
**Version:** 1.0.0 (MVP)
**Infrastructure:** ECS Fargate, RDS PostgreSQL 17, ElastiCache Redis 7, S3
**Deployment Model:** Option B (FastAPI serves static frontend files in single container)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [First-Time Deployment](#first-time-deployment)
3. [Update & Redeployment Procedures](#update--redeployment-procedures)
4. [Rollback Procedures](#rollback-procedures)
5. [Health Checks & Validation](#health-checks--validation)
6. [Post-Deployment Checklist](#post-deployment-checklist)
7. [Troubleshooting Deployment Issues](#troubleshooting-deployment-issues)

---

## Prerequisites

### Required Software

Before deploying, ensure you have the following installed:

#### 1. AWS CLI (version 2.x)
```bash
# Check version
aws --version

# Install (macOS)
brew install awscli

# Install (Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Configure AWS credentials:**
```bash
aws configure
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-2
# Default output format: json
```

**Verify access:**
```bash
aws sts get-caller-identity
```

#### 2. Terraform (version 1.0+)
```bash
# Check version
terraform version

# Install (macOS)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Install (Linux)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

#### 3. Docker (version 20.10+)
```bash
# Check version
docker --version
docker-compose --version

# Install Docker Desktop
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Linux: https://docs.docker.com/engine/install/
```

**Verify Docker is running:**
```bash
docker ps
```

#### 4. Git
```bash
# Check version
git --version

# Install if needed
brew install git  # macOS
sudo apt install git  # Linux
```

### AWS Account Setup

#### 1. Create AWS Account
- Sign up at https://aws.amazon.com/
- Verify email address
- Add payment method
- Complete identity verification

#### 2. Create IAM User for Deployment
```bash
# Create IAM user with necessary permissions
aws iam create-user --user-name ai-video-deployer

# Attach required policies
aws iam attach-user-policy \
  --user-name ai-video-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access keys
aws iam create-access-key --user-name ai-video-deployer
```

**Note:** For production, use more restrictive IAM policies. AdministratorAccess is for initial setup only.

#### 3. Set Up AWS Budget Alerts (Recommended)
```bash
# Create budget to track costs (set to $60/month with alerts at 80%)
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget-config.json
```

**budget-config.json:**
```json
{
  "BudgetName": "AI-Video-Pipeline-Monthly",
  "BudgetLimit": {
    "Amount": "60",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

### Required Information

Before deployment, gather the following:

- [ ] AWS Account ID
- [ ] AWS Access Key ID and Secret Access Key
- [ ] Replicate API Token (from https://replicate.com/account/api-tokens)
- [ ] Desired S3 bucket name (must be globally unique)
- [ ] Strong database password (generate with: `openssl rand -base64 32`)
- [ ] Domain name (if using custom domain, otherwise ECS task public IP)

---

## First-Time Deployment

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd delicious-lotus
```

### Step 2: Configure Variables

#### Create terraform.tfvars

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

**Edit terraform.tfvars:**

```hcl
# Region (IMPORTANT: User specified us-east-2)
aws_region = "us-east-2"

# Environment
environment = "prod"  # or "dev" or "staging"

# S3 Bucket (must be globally unique)
s3_bucket_name = "ai-video-prod-bucket-YOUR-UNIQUE-ID"

# Database credentials (use strong passwords!)
db_password = "CHANGE-ME-generate-with-openssl-rand"

# Replicate API token
replicate_api_token = "r8_your_token_here"

# CORS origins (your production domain)
cors_origins = "https://your-production-domain.com"

# Optional: Override defaults if needed
# db_instance_class = "db.t4g.micro"  # ~$12/month
# redis_node_type = "cache.t4g.micro"  # ~$11/month
# task_cpu = "1024"  # 1 vCPU
# task_memory = "2048"  # 2 GB RAM
# desired_count = 1  # Number of ECS tasks
```

**Security Note:** Never commit `terraform.tfvars` to git. It's already in `.gitignore`.

### Step 3: Initialize Terraform

```bash
cd terraform

# Initialize Terraform (downloads providers)
terraform init

# Expected output:
# Terraform has been successfully initialized!
```

**Troubleshooting:**
- If you see provider errors, check your internet connection
- Ensure you're in the `terraform/` directory
- Try `rm -rf .terraform` and run `terraform init` again

### Step 4: Review Infrastructure Plan

```bash
# Generate execution plan
terraform plan -out=tfplan

# Review the output carefully
# You should see resources being created:
# - ECR repository
# - S3 bucket
# - RDS PostgreSQL instance
# - ElastiCache Redis cluster
# - ECS cluster, service, and task definition
# - IAM roles and policies
# - Security groups
# - CloudWatch log groups
```

**Expected resource count:** ~30-40 resources will be created.

### Step 5: Deploy Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# This will take 10-15 minutes (RDS and ElastiCache take the longest)
```

**What gets created:**
1. **ECR Repository** - Docker image storage
2. **S3 Bucket** - Video and asset storage with lifecycle policies
3. **RDS PostgreSQL 17** - db.t4g.micro instance (~$12/month)
4. **ElastiCache Redis 7** - cache.t4g.micro cluster (~$11/month)
5. **ECS Fargate Cluster** - Container orchestration
6. **ECS Service** - Runs 1 task (1 vCPU, 2GB RAM) (~$15/month)
7. **IAM Roles** - ECS task execution and task roles
8. **Security Groups** - Network firewall rules
9. **CloudWatch Log Group** - Application logging

**Monitor progress:**
```bash
# In another terminal, watch AWS resources being created
watch -n 5 'aws rds describe-db-instances --query "DBInstances[0].DBInstanceStatus"'
```

### Step 6: Build and Push Docker Image

After infrastructure is deployed, build and push the backend image:

```bash
# Return to project root
cd ..

# Build backend Docker image
docker build -t delicious-lotus-backend:latest -f backend/Dockerfile backend/

# Get ECR repository URL from Terraform
cd terraform
ECR_URL=$(terraform output -raw ecr_repository_url)
echo "ECR URL: $ECR_URL"

# Login to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin $ECR_URL

# Tag image for ECR
docker tag delicious-lotus-backend:latest $ECR_URL:latest

# Push to ECR (may take 5-10 minutes)
docker push $ECR_URL:latest
```

**Troubleshooting:**
- If ECR login fails, verify AWS credentials: `aws sts get-caller-identity`
- If push is slow, check your internet connection
- Ensure Docker daemon is running: `docker ps`

### Step 7: Deploy ECS Service

The ECS service is created by Terraform, but it needs the Docker image to start:

```bash
# Force new deployment with the pushed image
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2
```

**Monitor ECS task startup:**
```bash
# Watch task status
aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2

# Get task details
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text)

aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $TASK_ARN \
  --region us-east-2 \
  --query 'tasks[0].lastStatus'
```

**Expected task statuses:**
1. `PROVISIONING` - Fargate allocating resources
2. `PENDING` - Pulling Docker image from ECR
3. `RUNNING` - Task is healthy and running

This takes 2-5 minutes.

### Step 8: Initialize Database

```bash
# Return to project root
cd ..

# Initialize database with schema
./scripts/migrate-db.sh init
```

**What this does:**
- Connects to RDS PostgreSQL
- Creates all 9 tables (user_sessions, generation_jobs, clips, etc.)
- Creates indexes for performance
- Adds default configuration values
- Creates database functions and triggers

**Verify schema:**
```bash
./scripts/migrate-db.sh status

# Expected output shows:
# - schema_migrations table
# - version 1: Initial schema
# - All 9 tables listed
```

### Step 9: Verify Deployment

```bash
cd terraform

# Get all deployment outputs
terraform output

# Expected outputs:
# - ecr_repository_url
# - s3_bucket_name
# - database_endpoint
# - redis_endpoint
# - ecs_cluster_name
# - ecs_service_name
# - ecs_task_public_ip (if using public subnet)
```

**Test the API:**
```bash
# Get ECS task public IP
TASK_PUBLIC_IP=$(terraform output -raw ecs_task_public_ip 2>/dev/null || echo "")

# If no public IP, get ALB DNS (if configured)
# For Option B deployment without ALB, you may need to access via VPN or bastion

# Test health endpoint
curl http://$TASK_PUBLIC_IP:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-11-15T..."}
```

---

## Update & Redeployment Procedures

### Code Changes Deployment

When you update backend code or frontend:

```bash
# 1. Build new Docker image
docker build -t delicious-lotus-backend:latest -f backend/Dockerfile backend/

# 2. Push to ECR
cd terraform
ECR_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin $ECR_URL

docker tag delicious-lotus-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# 3. Update ECS service to use new image
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2

# 4. Monitor rollout
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].deployments'
```

**Automated deployment script:**
```bash
# Use the deploy.sh script
./scripts/deploy.sh apply
```

This script:
1. Checks prerequisites
2. Builds Docker image
3. Pushes to ECR
4. Updates ECS service
5. Shows deployment status

### Database Migrations

When you add new tables or modify schema:

```bash
# 1. Create migration file
cd backend/migrations
touch 002_add_new_feature.sql

# 2. Write SQL migration
# Example content:
# ALTER TABLE generation_jobs ADD COLUMN new_field VARCHAR(255);
# INSERT INTO schema_migrations (version, description)
# VALUES (2, 'Add new_field to generation_jobs');

# 3. Apply migration
cd ../..
./scripts/migrate-db.sh migrate

# 4. Verify migration
./scripts/migrate-db.sh status
```

**Migration best practices:**
- Always number migrations sequentially (002, 003, 004...)
- Test migrations on staging first
- Create rollback migrations for destructive changes
- Backup database before major migrations

### Configuration Updates (Environment Variables)

To update environment variables without changing code:

```bash
cd terraform

# 1. Update terraform.tfvars
vim terraform.tfvars
# Update cors_origins, replicate_api_token, etc.

# 2. Plan changes
terraform plan -out=tfplan

# 3. Apply changes
terraform apply tfplan

# 4. Force ECS service to pick up new environment
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region us-east-2
```

**Note:** ECS tasks must be restarted to pick up new environment variables.

### Infrastructure Changes

To modify infrastructure (e.g., increase RDS size):

```bash
cd terraform

# 1. Update variables.tf or terraform.tfvars
# Example: Change db_instance_class
vim terraform.tfvars
# db_instance_class = "db.t4g.small"  # Upgrade from micro to small

# 2. Plan changes
terraform plan -out=tfplan

# Review changes carefully! Check for resource replacements (destructive)

# 3. Apply changes
terraform apply tfplan

# Some changes (like RDS instance class) cause downtime
# Schedule during maintenance window
```

---

## Rollback Procedures

### ECS Task Rollback (Previous Task Definition)

If a new deployment fails:

```bash
# 1. List recent task definitions
TASK_FAMILY=$(terraform output -raw ecs_task_family 2>/dev/null || echo "ai-video-backend")

aws ecs list-task-definitions \
  --family-prefix $TASK_FAMILY \
  --region us-east-2 \
  --sort DESC \
  --max-items 5

# 2. Identify previous working version
# Example output:
# - ai-video-backend:5 (current, broken)
# - ai-video-backend:4 (previous, working) <-- rollback to this

# 3. Update service to use previous task definition
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --task-definition ai-video-backend:4 \
  --region us-east-2

# 4. Monitor rollback
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].deployments'
```

**Verify rollback:**
```bash
# Check task is running previous version
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].taskDefinitionArn'
```

### Database Rollback (Migration Down)

**WARNING:** Database rollbacks can be destructive. Always backup first.

```bash
# 1. Backup current database state
DB_URL=$(cd terraform && terraform output -raw database_url)
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

# Create backup via ECS task or direct psql connection
# See migrate-db.sh for ECS task approach

# 2. Create rollback migration
cd backend/migrations
touch 003_rollback_migration_002.sql

# Example rollback content:
# ALTER TABLE generation_jobs DROP COLUMN new_field;
# DELETE FROM schema_migrations WHERE version = 2;

# 3. Apply rollback manually
./scripts/migrate-db.sh migrate

# 4. Verify rollback
./scripts/migrate-db.sh status
```

**Better approach:** Write reversible migrations from the start:
- Store dropped data in archive tables
- Use feature flags to disable new features
- Test rollbacks in staging environment

### Terraform State Rollback

If Terraform state gets corrupted or you need to undo infrastructure changes:

```bash
cd terraform

# 1. List state file versions (if using remote backend)
aws s3 ls s3://your-terraform-state-bucket/ --recursive | grep terraform.tfstate

# 2. Restore previous state
aws s3 cp s3://your-terraform-state-bucket/terraform.tfstate.backup ./terraform.tfstate

# 3. Verify state
terraform show

# 4. Re-plan to see what would change
terraform plan

# 5. Apply if needed
terraform apply
```

**Prevention:**
- Enable state locking (use S3 + DynamoDB backend)
- Use Terraform workspaces for multiple environments
- Backup state files regularly
- Never manually edit state files

---

## Health Checks & Validation

### Application Health Endpoints

The backend exposes several health check endpoints:

```bash
# Basic health check
curl http://<ecs-task-ip>:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-15T10:30:00Z",
#   "version": "1.0.0"
# }

# Detailed health check (includes dependencies)
curl http://<ecs-task-ip>:8000/health/detailed

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": "connected",
#     "redis": "connected",
#     "s3": "accessible",
#     "replicate_api": "configured"
#   }
# }
```

### Database Health

```bash
# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier ai-video-db \
  --region us-east-2 \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]'

# Expected: ["available", "ai-video-db.xxx.us-east-2.rds.amazonaws.com"]

# Test database connectivity
./scripts/migrate-db.sh status
```

### Redis Health

```bash
# Check ElastiCache cluster status
aws elasticache describe-cache-clusters \
  --cache-cluster-id ai-video-redis \
  --region us-east-2 \
  --query 'CacheClusters[0].[CacheClusterStatus,CacheNodes[0].Endpoint.Address]'

# Expected: ["available", "ai-video-redis.xxx.cache.amazonaws.com"]
```

### S3 Bucket Health

```bash
# Verify bucket exists and is accessible
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name) --region us-east-2

# Check lifecycle policies are active
aws s3api get-bucket-lifecycle-configuration \
  --bucket $(cd terraform && terraform output -raw s3_bucket_name) \
  --region us-east-2

# Expected: JSON showing 7-day, 30-day, 90-day deletion rules
```

### ECS Service Health

```bash
CLUSTER_NAME=$(cd terraform && terraform output -raw ecs_cluster_name)
SERVICE_NAME=$(cd terraform && terraform output -raw ecs_service_name)

# Check service status
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region us-east-2 \
  --query 'services[0].[status,runningCount,desiredCount]'

# Expected: ["ACTIVE", 1, 1]

# Check task health
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2 --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].[lastStatus,healthStatus,containers[0].lastStatus]'

# Expected: ["RUNNING", "HEALTHY", "RUNNING"]
```

### CloudWatch Logs

```bash
# View recent logs
aws logs tail /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --follow \
  --since 10m

# Check for errors
aws logs filter-log-events \
  --log-group-name /ecs/dev/ai-video-backend \
  --region us-east-2 \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

---

## Post-Deployment Checklist

### Immediate Verification (0-15 minutes)

- [ ] Terraform apply completed successfully
- [ ] ECR repository created and Docker image pushed
- [ ] ECS task is running (status: RUNNING)
- [ ] Database initialized with all 9 tables
- [ ] S3 bucket created with lifecycle policies
- [ ] CloudWatch logs showing application startup
- [ ] Health endpoint returns 200 OK
- [ ] No errors in CloudWatch logs

### Functional Testing (15-30 minutes)

- [ ] Can create a new user session
- [ ] Can upload a brand asset (logo/image)
- [ ] Can submit a video generation request
- [ ] WebSocket connection established for real-time updates
- [ ] Generated video clips stored in S3
- [ ] Final composition downloadable via presigned URL
- [ ] Database records created correctly
- [ ] Redis caching working (check cache hits)

### Security Verification

- [ ] S3 bucket has "Block all public access" enabled
- [ ] RDS database not publicly accessible (no public IP)
- [ ] ElastiCache Redis in private subnet
- [ ] Security groups properly configured (minimal ports open)
- [ ] IAM roles follow least privilege principle
- [ ] SSL/TLS enabled for RDS connections
- [ ] Environment variables contain no hardcoded secrets
- [ ] CloudWatch logging enabled

### Cost Monitoring

- [ ] AWS Cost Explorer shows expected resource costs
- [ ] Budget alerts configured ($60/month threshold)
- [ ] Replicate API usage tracked
- [ ] S3 lifecycle policies active (7/30/90 day deletion)
- [ ] No unexpected resources running

### Documentation

- [ ] `terraform.tfvars` backed up securely (not in git)
- [ ] Database password stored in password manager
- [ ] AWS account ID and region documented
- [ ] Deployment date and version recorded
- [ ] Team notified of deployment

---

## Troubleshooting Deployment Issues

### Terraform Errors

**Error: "Error creating DB Instance: DBInstanceAlreadyExists"**
```bash
# Check if RDS instance exists
aws rds describe-db-instances --region us-east-2

# If it exists, either:
# 1. Import into Terraform state
terraform import module.rds.aws_db_instance.main ai-video-db

# 2. Or delete and recreate
aws rds delete-db-instance \
  --db-instance-identifier ai-video-db \
  --skip-final-snapshot \
  --region us-east-2
```

**Error: "Error creating S3 bucket: BucketAlreadyExists"**
```bash
# S3 bucket names are globally unique
# Change s3_bucket_name in terraform.tfvars to a unique value
# Example: ai-video-prod-bucket-12345-unique
```

**Error: "Error launching ECS task: No Container Instances"**
```bash
# For Fargate, ensure launch type is FARGATE, not EC2
# Check terraform/modules/ecs/main.tf:
# launch_type = "FARGATE"
```

### Docker Build/Push Errors

**Error: "denied: Your authorization token has expired"**
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin <ecr-url>
```

**Error: "Cannot connect to the Docker daemon"**
```bash
# Start Docker
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker
```

### Database Connection Errors

**Error: "Could not connect to server: Connection timed out"**
```bash
# RDS is in VPC, not publicly accessible
# Use migrate-db.sh which connects via ECS task in VPC
./scripts/migrate-db.sh init

# Or set up bastion host for direct access
```

### ECS Task Failures

**Task immediately stops after starting**
```bash
# Check CloudWatch logs for errors
aws logs tail /ecs/dev/ai-video-backend --region us-east-2 --follow

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Invalid Replicate API token
```

**Task stuck in PENDING state**
```bash
# Check task definition CPU/memory allocation
# Ensure subnet has NAT gateway or public IP for pulling images
# Verify ECR image exists and is accessible
```

### Access Denied Errors

**Error: "User is not authorized to perform: ecs:UpdateService"**
```bash
# Verify IAM user has necessary permissions
aws iam list-attached-user-policies --user-name ai-video-deployer

# Attach missing policies
aws iam attach-user-policy \
  --user-name ai-video-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess
```

---

## Support & Resources

### Documentation
- [Architecture Guide](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Cost Tracking Guide](./cost-tracking.md)
- [Scaling Guide](./scaling.md)
- [Local Setup Guide](./local-setup.md)
- [Environment Setup Guide](./environment-setup.md)

### AWS Documentation
- [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [ElastiCache Redis](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

### External Resources
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL 17 Documentation](https://www.postgresql.org/docs/17/)
- [Redis 7 Documentation](https://redis.io/docs/)

---

**Deployment Guide Version:** 1.0.0
**Last Updated:** 2025-11-15
**Maintained by:** DevOps Team

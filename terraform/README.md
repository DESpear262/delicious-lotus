# Terraform AWS Infrastructure

This Terraform configuration deploys the complete AWS infrastructure for the AI Video Generation Pipeline in **us-east-2** region.

## Architecture

The infrastructure includes:

- **ECR** - Docker container registry
- **S3** - Video storage with lifecycle policies (7/30/90 day auto-delete)
- **RDS PostgreSQL 16** - Database (db.t4g.micro)
- **ElastiCache Redis 7** - Caching and queuing (cache.t4g.micro)
- **ECS Fargate** - Container orchestration
- **IAM** - Roles and policies (least privilege)
- **Security Groups** - Network security
- **CloudWatch** - Logging

**Estimated Monthly Cost:** $30-50 USD

## Prerequisites

1. **AWS CLI configured** with credentials for us-east-2:
   ```bash
   aws configure
   # Use region: us-east-2
   ```

2. **Terraform installed** (>= 1.0):
   ```bash
   terraform --version
   ```

3. **Docker** installed and backend image built:
   ```bash
   docker images | grep delicious-lotus-backend
   ```

## Quick Start

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update:
- `s3_bucket_name` - **Must be globally unique!**
- `db_password` - Use a strong password
- `replicate_api_token` - Your Replicate API token

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

This will show you all resources that will be created. Review carefully!

### 4. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted. This will take **10-15 minutes** to create all resources.

### 5. Push Docker Image to ECR

After `terraform apply` completes, push your Docker image:

```bash
# Get ECR login
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url)

# Tag and push image
docker tag delicious-lotus-backend:latest $(terraform output -raw ecr_repository_url):latest
docker push $(terraform output -raw ecr_repository_url):latest
```

### 6. Initialize Database Schema

Connect to the RDS instance and run the init script:

```bash
# Get connection details
terraform output database_url

# Run init script (use psql or your preferred tool)
psql "$(terraform output -raw database_url)" -f ../docker/postgres/init.sql
```

### 7. Monitor Deployment

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services $(terraform output -raw ecs_service_name) \
  --region us-east-2

# View logs
aws logs tail $(terraform output -raw cloudwatch_log_group) --follow --region us-east-2
```

## Outputs

After applying, Terraform provides important outputs:

```bash
terraform output             # View all outputs
terraform output -raw ecr_repository_url    # Get ECR URL
terraform output -raw database_url          # Get database connection string
terraform output -raw redis_url             # Get Redis connection string
```

## Cost Optimization

Current configuration is optimized for MVP:
- **RDS:** db.t4g.micro (~$12/month)
- **ElastiCache:** cache.t4g.micro (~$11/month)
- **ECS Fargate:** 1 task, 1 vCPU, 2GB RAM (~$15/month)
- **S3:** Minimal with lifecycle policies (~$1-2/month)
- **Other:** ECR, CloudWatch logs (~$1-2/month)

**Total:** ~$30-50/month

## Scaling for Production

To scale for production, edit `terraform.tfvars`:

```hcl
environment = "prod"

# Upgrade database
db_instance_class = "db.t4g.small"  # or larger
db_allocated_storage = 100

# Upgrade Redis
redis_node_type = "cache.t4g.small"
redis_num_nodes = 2  # For HA

# Scale ECS
desired_count = 3  # Multiple tasks
task_cpu = "2048"  # 2 vCPU
task_memory = "4096"  # 4 GB
```

## Troubleshooting

### Image Pull Errors

If ECS can't pull the image:
```bash
# Verify image exists
aws ecr describe-images --repository-name ai-video-backend --region us-east-2

# Check IAM permissions
aws iam get-role --role-name dev-ecs-task-execution-role
```

### Database Connection Issues

```bash
# Verify RDS is running
aws rds describe-db-instances --db-instance-identifier ai-video-db --region us-east-2

# Check security group rules
terraform state show 'module.security.aws_security_group.rds'
```

### ECS Service Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster ai-video-cluster \
  --services ai-video-backend-service \
  --region us-east-2 \
  --query 'services[0].events[:5]'

# View task logs
aws logs tail /ecs/dev/ai-video-backend --follow --region us-east-2
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**WARNING:** This will delete everything including databases! Make backups first.

## Security Notes

1. **Never commit `terraform.tfvars`** - It contains secrets!
2. **RDS & Redis** are NOT publicly accessible (security groups enforce this)
3. **S3 bucket** has public access blocked
4. **IAM roles** use least privilege principle
5. **Change default passwords** before deploying to production!

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs
3. Check AWS Console for resource status
4. Review Terraform state: `terraform state list`

## Files

- `main.tf` - Main orchestration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `terraform.tfvars` - Your configuration (gitignored)
- `modules/` - Reusable modules for each service

## Region

**CRITICAL:** This configuration is specifically for **us-east-2** (Ohio).

Do NOT change to us-east-1 without reviewing all configurations!

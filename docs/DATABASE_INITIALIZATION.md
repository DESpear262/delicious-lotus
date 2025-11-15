# Database Initialization Guide

The RDS PostgreSQL database has been provisioned but needs schema initialization.

## Current Status

✅ **Infrastructure Deployed:**
- RDS PostgreSQL 17 instance running
- Database: `ai_video_pipeline`
- Endpoint: `ai-video-db.c1uuigcm4bd1.us-east-2.rds.amazonaws.com:5432`
- Security: VPC-only access (properly secured)

❌ **Schema Not Initialized:** Tables need to be created from `docker/postgres/init.sql`

---

## Why Can't We Initialize Remotely?

The database is correctly secured in private subnets within the VPC, which means:
- ✅ Good: Database is not exposed to the internet
- ❌ Challenge: Can't connect from your local machine directly
- ✅ Solution: Must initialize from within the VPC

---

## Option 1: Use Backend Container (Recommended)

The easiest method is to run the initialization script from within the running backend container:

### Steps:

1. **Copy the init script to the running container:**
   ```bash
   # Get the current task ID
   TASK_ARN=$(aws ecs list-tasks \
     --cluster ai-video-cluster \
     --service-name ai-video-backend-service \
     --region us-east-2 \
     --query 'taskArns[0]' \
     --output text)

   # Extract just the task ID
   TASK_ID=$(echo $TASK_ARN | awk -F/ '{print $NF}')

   # Copy init files (requires AWS CLI and Session Manager plugin)
   aws ecs execute-command \
     --cluster ai-video-cluster \
     --task $TASK_ID \
     --container backend \
     --interactive \
     --command "/bin/sh" \
     --region us-east-2
   ```

2. **Inside the container, run:**
   ```bash
   # Install psql if not available
   apk add --no-cache postgresql-client

   # Run the initialization script
   python /app/init_db.py
   ```

### Alternative: Manual SQL execution
```bash
# Inside the container
psql $DATABASE_URL < /path/to/init.sql
```

---

## Option 2: AWS Systems Manager Session Manager

If ECS Exec isn't working, use SSM Session Manager:

1. **Install Session Manager Plugin** (already done ✅)

2. **Start a session:**
   ```bash
   aws ecs execute-command \
     --cluster ai-video-cluster \
     --task $(aws ecs list-tasks --cluster ai-video-cluster --service-name ai-video-backend-service --region us-east-2 --query 'taskArns[0]' --output text | awk -F/ '{print $NF}') \
     --container backend \
     --interactive \
     --command "/bin/sh" \
     --region us-east-2
   ```

   Note: If you get "execute command was not enabled" error, the ECS service needs to be updated (already done, but tasks need restart).

---

## Option 3: One-Off ECS Task

Create a temporary task just for database initialization:

```bash
# Register the init task definition
aws ecs register-task-definition \
  --cli-input-json file://terraform/db-init-task.json \
  --region us-east-2

# Run the one-off task
aws ecs run-task \
  --cluster ai-video-cluster \
  --task-definition db-init-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-0afb3d69f93310ccd],assignPublicIp=ENABLED}" \
  --region us-east-2
```

---

## Option 4: Bastion Host (Most Complex)

If you frequently need database access:

1. Launch a small EC2 instance in the same VPC
2. Install PostgreSQL client
3. Connect via SSH and run init.sql
4. Terminate the instance when done

---

## Option 5: Temporary Public Access (Not Recommended)

**⚠️ Only use in emergencies and immediately revert!**

1. Make RDS temporarily public:
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier ai-video-db \
     --publicly-accessible \
     --apply-immediately \
     --region us-east-2
   ```

2. Add your IP to security group:
   ```bash
   MY_IP=$(curl -s https://api.ipify.org)
   aws ec2 authorize-security-group-ingress \
     --group-id sg-04287fe439227cb9e \
     --protocol tcp \
     --port 5432 \
     --cidr $MY_IP/32 \
     --region us-east-2
   ```

3. Wait 2-3 minutes for changes to apply

4. Run init script:
   ```bash
   docker run --rm -i postgres:16-alpine \
     psql "postgresql://ai_video_admin:PASSWORD@ai-video-db.c1uuigcm4bd1.us-east-2.rds.amazonaws.com:5432/ai_video_pipeline" \
     < docker/postgres/init.sql
   ```

5. **IMMEDIATELY** revert security:
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier ai-video-db \
     --no-publicly-accessible \
     --apply-immediately \
     --region us-east-2

   aws ec2 revoke-security-group-ingress \
     --group-id sg-04287fe439227cb9e \
     --protocol tcp \
     --port 5432 \
     --cidr $MY_IP/32 \
     --region us-east-2
   ```

---

## Verification

After initialization, verify tables were created:

```bash
# From within container or bastion
psql $DATABASE_URL -c "\dt public.*"
```

Expected tables:
- generation_jobs
- clips
- compositions
- brand_assets
- user_sessions
- (plus supporting views, functions, and triggers)

---

## Troubleshooting

### "Connection refused"
- Database is in private subnet (correct behavior)
- Must connect from within VPC (ECS task, EC2, or VPN)

### "Execute command not enabled"
- ECS service has been updated with execute command enabled
- New tasks will have it, old tasks need restart
- Force new deployment: `aws ecs update-service --cluster ai-video-cluster --service ai-video-backend-service --force-new-deployment --region us-east-2`

### "Session Manager plugin not found"
- Install from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
- Restart terminal after installation
- Verify: `session-manager-plugin --version`

---

## Files

- **Init Script:** `docker/postgres/init.sql`
- **Python Helper:** `backend/init_db.py`
- **Connection String:** Available in Terraform outputs (`terraform output database_url`)

---

## Next Steps

1. Choose an initialization method above
2. Run the init script
3. Verify tables were created
4. Backend application will be able to use the database

**Recommendation:** Use Option 1 (backend container) as it's the simplest and doesn't require additional infrastructure.

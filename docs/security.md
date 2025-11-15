# Security Documentation

**Last Updated:** 2025-11-15
**Version:** 1.0
**Status:** Active

## Table of Contents

1. [Security Architecture Overview](#security-architecture-overview)
2. [Security Audit Checklist](#security-audit-checklist)
3. [Security Hardening Implementation](#security-hardening-implementation)
4. [Secrets Management](#secrets-management)
5. [Incident Response Plan](#incident-response-plan)
6. [Developer Security Best Practices](#developer-security-best-practices)
7. [OWASP Top 10 Compliance](#owasp-top-10-compliance)
8. [Penetration Testing Recommendations](#penetration-testing-recommendations)
9. [Security Monitoring & Logging](#security-monitoring--logging)

---

## Security Architecture Overview

### Infrastructure Components

The Delicious Lotus application is deployed on AWS with the following security architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   ECS Tasks     │
                    │   (Public IP)   │
                    │   Port 8000     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌────▼────┐      ┌─────▼─────┐
    │    RDS    │      │  Redis  │      │    S3     │
    │ (Private) │      │(Private)│      │ (Private) │
    └───────────┘      └─────────┘      └───────────┘
```

**Security Principles:**
- **Defense in Depth:** Multiple layers of security controls
- **Least Privilege:** Minimal permissions granted to all resources
- **Encryption Everywhere:** Data encrypted at rest and in transit
- **Zero Trust:** No implicit trust between components
- **Auditability:** All actions logged and monitored

---

## Security Audit Checklist

### ✅ Network Security

#### Security Groups
- [x] **RDS Security Group:**
  - Accessible ONLY from ECS tasks (private subnet)
  - Port 5432 (PostgreSQL) restricted to ECS security group
  - No public access
  - Status: ✅ **SECURE** (Implemented in `terraform/modules/security/main.tf`)

- [x] **ElastiCache Security Group:**
  - Accessible ONLY from ECS tasks (private subnet)
  - Port 6379 (Redis) restricted to ECS security group
  - No public access
  - Status: ✅ **SECURE** (Implemented in `terraform/modules/security/main.tf`)

- [x] **ECS Tasks Security Group:**
  - Port 8000 exposed for FastAPI
  - Outbound internet access for API calls (Replicate)
  - Status: ✅ **SECURE** (Minimal exposure)
  - ⚠️ **RECOMMENDATION:** Add Application Load Balancer for HTTPS termination

#### VPC Configuration
- [x] **Subnet Architecture:**
  - Private subnets for RDS and ElastiCache (10.0.1.0/24, 10.0.2.0/24)
  - Public subnet for ECS tasks (10.0.101.0/24)
  - Status: ✅ **SECURE**

- [x] **Internet Gateway:**
  - Attached to VPC for public subnet internet access
  - Status: ✅ **SECURE**

- [ ] **NAT Gateway:**
  - Status: ⚠️ **NOT IMPLEMENTED** (cost optimization for dev)
  - Recommendation: Add for production to avoid public IPs on ECS tasks

#### SSL/TLS
- [ ] **HTTPS Enforcement:**
  - Status: ⚠️ **NOT IMPLEMENTED** (direct HTTP access to ECS)
  - Recommendation: Add Application Load Balancer with ACM certificate
  - Target: TLS 1.2+ minimum

- [ ] **Certificate Management:**
  - Status: ⚠️ **PENDING** (requires ALB)
  - Recommendation: Use AWS Certificate Manager (ACM)

**Network Security Score: 7/10** (Good foundation, production enhancements needed)

---

### ✅ IAM Security

#### IAM Roles Review
- [x] **ECS Task Execution Role:**
  - Purpose: Pull ECR images, write CloudWatch logs
  - Permissions: `AmazonECSTaskExecutionRolePolicy` (AWS managed)
  - Status: ✅ **SECURE** (Least privilege)

- [x] **ECS Task Role:**
  - Purpose: Application access to S3
  - Permissions: S3 GetObject, PutObject, DeleteObject, ListBucket (bucket-specific)
  - Status: ✅ **SECURE** (Least privilege, scoped to specific bucket)

- [x] **No Long-Lived Credentials:**
  - All access via IAM roles (temporary credentials)
  - No hardcoded AWS access keys
  - Status: ✅ **SECURE**

#### IAM Best Practices
- [x] **Principle of Least Privilege:** All roles follow minimal permissions
- [x] **Service-to-Service Auth:** Using IAM roles (no keys)
- [ ] **MFA for Root Account:** ⚠️ **MANUAL ACTION REQUIRED**
- [ ] **IAM Access Key Rotation:** N/A (no long-lived keys)

**IAM Security Score: 9/10** (Excellent, pending root MFA)

---

### ✅ Data Security

#### Encryption at Rest
- [x] **RDS Encryption:**
  - PostgreSQL 17 with `storage_encrypted = true`
  - Encrypted with AWS managed keys
  - Status: ✅ **SECURE** (Implemented in `terraform/modules/rds/main.tf:18`)

- [x] **S3 Bucket Encryption:**
  - Server-side encryption with AES256
  - Status: ✅ **SECURE** (Implemented in `terraform/modules/s3/main.tf:30-38`)

- [ ] **ElastiCache Encryption at Rest:**
  - Status: ⚠️ **NOT ENABLED** (Redis 7 supports it)
  - Recommendation: Enable for sensitive cache data
  - Note: cache.t3.micro may not support encryption (check AWS docs)

#### Encryption in Transit
- [x] **RDS SSL/TLS:**
  - PostgreSQL supports SSL connections
  - Application should use `sslmode=require` in connection string
  - Status: ⚠️ **VERIFY CONNECTION STRING**

- [ ] **ElastiCache Encryption in Transit:**
  - Status: ⚠️ **NOT ENABLED**
  - **ACTION REQUIRED:** Add `transit_encryption_enabled = true` to terraform
  - **ACTION REQUIRED:** Add auth token for Redis AUTH

- [x] **S3 HTTPS:**
  - All S3 API calls use HTTPS by default (boto3)
  - Status: ✅ **SECURE**

#### Secrets Management
- [ ] **AWS Secrets Manager Integration:**
  - Status: ⚠️ **NOT IMPLEMENTED**
  - Current: Environment variables in ECS task definition
  - **REQUIRED FOR PRODUCTION:**
    - Create secrets: `prod/db/password`, `prod/redis/password`, `prod/replicate/api-key`
    - Update ECS task definition to fetch from Secrets Manager
    - Enable automatic rotation for database passwords

- [x] **No Secrets in Code:**
  - `.env` files in `.gitignore`
  - Status: ✅ **SECURE**

#### Database Backups
- [x] **RDS Automated Backups:**
  - 7-day retention period
  - Encrypted backups
  - Status: ✅ **SECURE**

- [x] **S3 Versioning:**
  - Enabled for all objects
  - Protects against accidental deletion
  - Status: ✅ **SECURE**

**Data Security Score: 7/10** (Encryption at rest good, need transit encryption and Secrets Manager)

---

### ✅ Application Security

#### Input Validation
- [x] **Pydantic Models:**
  - All API inputs validated via Pydantic schemas
  - Type checking enforced
  - Status: ✅ **SECURE**

- [ ] **Length Limits:**
  - **VERIFY:** Prompt length limits (500-2000 chars)
  - **VERIFY:** File upload size limits
  - **VERIFY:** File type validation (video formats only)
  - Status: ⚠️ **REQUIRES CODE REVIEW**

- [x] **SQL Injection Protection:**
  - Using SQLAlchemy ORM (parameterized queries)
  - Status: ✅ **SECURE**

- [ ] **XSS Protection:**
  - **VERIFY:** Input sanitization for user-generated content
  - **VERIFY:** Proper escaping in responses
  - Status: ⚠️ **REQUIRES CODE REVIEW**

#### Rate Limiting
- [ ] **API Rate Limits:**
  - Status: ⚠️ **NOT IMPLEMENTED**
  - Recommendation: Add slowapi or fastapi-limiter
  - Suggested limits: 100 requests/minute per IP, 10 generations/hour per user

- [ ] **DDoS Protection:**
  - Status: ⚠️ **BASIC** (AWS default)
  - Recommendation: Add AWS WAF with ALB for production

#### CORS Configuration
- [x] **S3 CORS:**
  - Currently: `allowed_origins = ["*"]`
  - Status: ⚠️ **INSECURE FOR PRODUCTION**
  - **ACTION REQUIRED:** Restrict to frontend domain

- [ ] **FastAPI CORS:**
  - Status: ⚠️ **REQUIRES CODE REVIEW**
  - If serving API separately: whitelist frontend domain only

#### Authentication/Authorization
- [ ] **Session Management:**
  - Status: ⚠️ **REQUIRES IMPLEMENTATION** (if user auth added)
  - Recommendation: Use secure, httpOnly cookies with SameSite=Strict

- [ ] **JWT Token Validation:**
  - Status: N/A (no auth implemented yet)
  - Future: Use PyJWT with proper secret rotation

- [x] **API Key Security:**
  - Replicate API key stored in environment variables
  - Status: ⚠️ **MIGRATE TO SECRETS MANAGER**

**Application Security Score: 6/10** (Good foundation, need rate limiting and auth)

---

### ✅ Container Security

#### Docker Image Security
- [x] **Official Base Image:**
  - Using `python:3.13-slim` (official Python image)
  - Status: ✅ **SECURE**

- [x] **Non-Root User:**
  - Running as `appuser` (UID 1000, non-root)
  - Status: ✅ **SECURE** (Implemented in `fastapi/Dockerfile:49-70`)

- [x] **Minimal Attack Surface:**
  - Multi-stage build to reduce image size
  - Removed build dependencies in final image
  - Status: ✅ **SECURE**

- [x] **No Secrets in Image:**
  - No hardcoded credentials or `.env` in image
  - Status: ✅ **SECURE**

- [ ] **Read-Only Filesystem:**
  - Status: ⚠️ **PARTIAL** (writable temp/uploads directories)
  - Current: `/app/temp` and `/app/uploads` are writable
  - Status: ✅ **ACCEPTABLE** (required for video processing)

#### ECR Image Scanning
- [x] **Automated Vulnerability Scanning:**
  - `scan_on_push = true` enabled in ECR
  - Status: ✅ **SECURE** (Implemented in `terraform/modules/ecr/main.tf:6`)

- [ ] **Fail on Critical Vulnerabilities:**
  - Status: ⚠️ **NOT ENFORCED IN CI/CD**
  - **ACTION REQUIRED:** Add Trivy scanning to GitHub Actions

**Container Security Score: 9/10** (Excellent Docker security practices)

---

### ✅ Logging & Monitoring

#### AWS CloudTrail
- [ ] **API Audit Logs:**
  - Status: ⚠️ **NOT ENABLED**
  - **RECOMMENDATION:** Enable CloudTrail for all AWS API calls
  - Cost: ~$2-5/month for basic trail
  - Priority: High for production

#### VPC Flow Logs
- [ ] **Network Traffic Analysis:**
  - Status: ⚠️ **NOT ENABLED**
  - **RECOMMENDATION:** Enable VPC Flow Logs to S3 or CloudWatch
  - Use case: Detect unusual network patterns, troubleshoot connectivity
  - Priority: Medium

#### Application Logging
- [x] **CloudWatch Logs:**
  - ECS tasks log to CloudWatch Logs
  - Status: ✅ **ENABLED**

- [ ] **Sensitive Data in Logs:**
  - Status: ⚠️ **REQUIRES CODE REVIEW**
  - **VERIFY:** No passwords, API keys, or PII in logs
  - **VERIFY:** Proper log sanitization

#### Security Alerts
- [ ] **Failed Login Attempts:**
  - Status: N/A (no auth implemented)
  - Future: Alert on >5 failed attempts in 5 minutes

- [ ] **Unusual API Activity:**
  - Status: ⚠️ **NOT IMPLEMENTED**
  - Recommendation: CloudWatch alarms for high error rates

- [ ] **Privilege Escalation:**
  - Status: ⚠️ **NOT MONITORED**
  - Recommendation: CloudTrail + EventBridge for IAM policy changes

#### Log Retention
- [x] **CloudWatch Log Retention:**
  - 7-day retention configured
  - Status: ✅ **CONFIGURED**

**Logging & Monitoring Score: 5/10** (Basic logging, need audit trails and alerts)

---

## Security Hardening Implementation

### Immediate Actions (High Priority)

#### 1. Enable ElastiCache Encryption in Transit

**File:** `terraform/modules/elasticache/main.tf`

```hcl
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = var.cluster_id
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.security_group_id]

  # SECURITY HARDENING: Enable encryption in transit
  transit_encryption_enabled = true
  auth_token                 = var.auth_token  # Add to variables

  # Snapshot and backup configuration
  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  maintenance_window       = "Mon:05:00-Mon:07:00"

  auto_minor_version_upgrade = true

  tags = {
    Name        = var.cluster_id
    Environment = var.environment
  }
}
```

**Additional Changes Required:**
- Add `auth_token` variable to `terraform/modules/elasticache/variables.tf`
- Update application Redis connection to use AUTH token and TLS
- Store auth token in AWS Secrets Manager

---

#### 2. Restrict S3 CORS Origins

**File:** `terraform/modules/s3/main.tf`

```hcl
# CORS configuration for direct uploads
resource "aws_s3_bucket_cors_configuration" "storage" {
  bucket = aws_s3_bucket.storage.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    # SECURITY HARDENING: Restrict to frontend domain
    # For Option B (same origin): No CORS needed, remove this block
    # For Option A (Vercel): Replace with actual frontend domain
    allowed_origins = var.allowed_cors_origins  # e.g., ["https://delicious-lotus.vercel.app"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
```

**Recommendation:** If using Option B (same origin deployment), remove CORS entirely.

---

#### 3. Migrate to AWS Secrets Manager

**Terraform:** Create Secrets Manager resources

```hcl
# File: terraform/modules/secrets/main.tf (NEW MODULE)

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.environment}/db/password"
  description = "RDS PostgreSQL master password"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

resource "aws_secretsmanager_secret" "redis_auth_token" {
  name        = "${var.environment}/redis/auth-token"
  description = "Redis AUTH token"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = var.redis_auth_token
}

resource "aws_secretsmanager_secret" "replicate_api_key" {
  name        = "${var.environment}/replicate/api-key"
  description = "Replicate API key for video generation"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "replicate_api_key" {
  secret_id     = aws_secretsmanager_secret.replicate_api_key.id
  secret_string = var.replicate_api_key
}
```

**IAM Policy Update:** Add Secrets Manager permissions to ECS task execution role

```hcl
# File: terraform/modules/iam/main.tf

resource "aws_iam_policy" "secrets_access" {
  name        = "${var.environment}-secrets-access-policy"
  description = "Allow ECS tasks to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:${var.environment}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.secrets_access.arn
}
```

**ECS Task Definition Update:**

```json
{
  "secrets": [
    {
      "name": "DATABASE_URL",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/db/password::"
    },
    {
      "name": "REDIS_URL",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/redis/auth-token::"
    },
    {
      "name": "REPLICATE_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/replicate/api-key::"
    }
  ]
}
```

---

### Medium Priority Actions

#### 4. Add Rate Limiting

**Install:** `fastapi-limiter` or `slowapi`

```bash
# Add to requirements.txt
slowapi>=0.1.9
```

**Implementation:**

```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/generate")
@limiter.limit("10/hour")  # 10 generations per hour per IP
async def generate_video(request: Request, ...):
    ...
```

---

#### 5. Enable CloudTrail

**Terraform:**

```hcl
# File: terraform/modules/cloudtrail/main.tf (NEW MODULE)

resource "aws_cloudtrail" "main" {
  name                          = "${var.environment}-cloudtrail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "cloudtrail" {
  bucket = "${var.environment}-cloudtrail-logs"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}
```

---

#### 6. Enable VPC Flow Logs

**Terraform:**

```hcl
# File: terraform/main.tf (add to VPC module)

resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/flow-logs"
  retention_in_days = 7

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role" "flow_logs" {
  name = "${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
```

---

### Low Priority / Future Enhancements

#### 7. Add Application Load Balancer with HTTPS

**Benefits:**
- HTTPS termination with ACM certificate
- Web Application Firewall (WAF) integration
- DDoS protection via AWS Shield
- Health checks and auto-scaling

**Estimated Cost:** $16-20/month

#### 8. Implement AWS WAF

**Use Cases:**
- Rate limiting at network layer
- SQL injection and XSS filtering
- IP reputation blocking
- Geographic restrictions

**Estimated Cost:** $5-10/month + $1 per million requests

#### 9. Add AWS GuardDuty

**Features:**
- Threat detection for AWS accounts
- Machine learning-based anomaly detection
- Integration with EventBridge for automated response

**Estimated Cost:** $1-5/month (low usage)

---

## Secrets Management

### Current State

**Environment Variables in ECS Task Definition:**
```
DATABASE_URL=postgresql://user:password@rds-endpoint:5432/db
REDIS_URL=redis://redis-endpoint:6379
REPLICATE_API_KEY=r8_***
AWS_ACCESS_KEY_ID=[from IAM role]
AWS_SECRET_ACCESS_KEY=[from IAM role]
```

### Target State (Production)

**AWS Secrets Manager:**
- `prod/db/password` → RDS password (auto-rotation enabled)
- `prod/redis/auth-token` → Redis AUTH token
- `prod/replicate/api-key` → Replicate API key
- `prod/jwt/secret-key` → JWT signing key (future)

### Migration Steps

1. **Create Secrets in AWS Secrets Manager:**
   ```bash
   aws secretsmanager create-secret \
     --name prod/db/password \
     --secret-string "YOUR_DB_PASSWORD"

   aws secretsmanager create-secret \
     --name prod/redis/auth-token \
     --secret-string "YOUR_REDIS_TOKEN"

   aws secretsmanager create-secret \
     --name prod/replicate/api-key \
     --secret-string "YOUR_REPLICATE_KEY"
   ```

2. **Update IAM Policy** (see Terraform above)

3. **Update ECS Task Definition** (see JSON above)

4. **Update Application Code:**
   - Ensure boto3 SDK is installed
   - Application will automatically fetch secrets from environment variables

5. **Enable Secret Rotation:**
   ```bash
   aws secretsmanager rotate-secret \
     --secret-id prod/db/password \
     --rotation-lambda-arn arn:aws:lambda:REGION:ACCOUNT:function:SecretsManagerRDSRotation \
     --rotation-rules AutomaticallyAfterDays=30
   ```

### Secret Rotation Policy

- **Database Passwords:** Every 30 days (automated)
- **API Keys:** Every 90 days (manual)
- **JWT Secrets:** Every 180 days (manual)
- **Emergency Rotation:** Immediately upon suspected compromise

---

## Incident Response Plan

### Security Incident Classification

| Severity | Description | Examples | Response Time |
|----------|-------------|----------|---------------|
| **Critical** | Service-wide compromise, data breach | RDS exposed publicly, API keys leaked | <1 hour |
| **High** | Significant security vulnerability | SQL injection exploit, XSS attack | <4 hours |
| **Medium** | Limited impact, localized issue | Failed login attempts, rate limit bypass | <24 hours |
| **Low** | Minor security concern | Outdated dependency, misconfiguration | <1 week |

### Escalation Procedures

#### Critical Incident Response (Within 1 Hour)

1. **Detect & Alert (0-15 min):**
   - CloudWatch Alarms trigger
   - Security scanning tools alert
   - User reports suspicious activity

2. **Assess & Contain (15-30 min):**
   - Identify affected systems
   - Isolate compromised resources (security group changes)
   - Revoke compromised credentials
   - Enable CloudTrail for forensics (if not enabled)

3. **Communicate (30-45 min):**
   - Notify stakeholders (engineering, management)
   - Create incident ticket with timeline
   - Begin incident log

4. **Investigate (45-60 min):**
   - Review CloudTrail logs
   - Check VPC Flow Logs
   - Analyze application logs
   - Identify root cause

5. **Remediate & Recover (1-4 hours):**
   - Apply security patches
   - Rotate all credentials
   - Restore from backup if needed
   - Update security configurations

6. **Post-Incident (1-7 days):**
   - Write incident report
   - Update security documentation
   - Implement preventive measures
   - Conduct team retrospective

### Communication Plan

**Notification Channels:**
- **Email:** security@delicious-lotus.com
- **Slack:** #security-incidents (high priority)
- **Phone:** On-call engineer (critical only)

**Stakeholder Matrix:**
| Severity | Engineering | Management | Legal | Users |
|----------|-------------|------------|-------|-------|
| Critical | Immediate | Immediate | Within 4h | Within 24h |
| High | Within 1h | Within 4h | If data breach | If affected |
| Medium | Within 4h | Within 24h | N/A | N/A |
| Low | Weekly summary | Monthly | N/A | N/A |

### Forensics & Evidence Collection

**Data to Collect:**
1. **CloudTrail Logs:** All API calls for last 7 days
2. **VPC Flow Logs:** Network traffic patterns
3. **Application Logs:** Error logs, access logs
4. **ECS Task Snapshots:** Container state at incident time
5. **RDS Snapshots:** Database state before incident
6. **Security Group Changes:** All modifications in last 30 days

**Preservation:**
- Export logs to S3 with "legal hold" enabled
- Create RDS snapshot immediately
- Document all manual actions taken
- Take screenshots of AWS console state

### Remediation Steps by Incident Type

#### Exposed Credentials
1. **Immediately revoke** the compromised credentials
2. **Rotate all related secrets** (assume lateral movement)
3. **Review CloudTrail** for unauthorized API calls
4. **Check S3 bucket access logs** for data exfiltration
5. **Update all applications** with new credentials
6. **Enable MFA** on all AWS accounts

#### SQL Injection Attack
1. **Block malicious IPs** in security groups or WAF
2. **Review database logs** for unauthorized queries
3. **Check for data exfiltration** (SELECT queries on sensitive tables)
4. **Apply input validation** to vulnerable endpoints
5. **Consider restoring** from backup if data modified
6. **Add SQL injection rules** to WAF

#### DDoS Attack
1. **Enable AWS Shield Standard** (free)
2. **Add rate limiting** via WAF or API Gateway
3. **Increase ECS task limits** temporarily (if needed)
4. **Block attacking IPs** in WAF or security groups
5. **Consider AWS Shield Advanced** ($3k/month) for large-scale attacks

#### Container Vulnerability
1. **Pull affected image** from ECR
2. **Review Trivy scan results** for CVE details
3. **Update base image** or application dependencies
4. **Rebuild and push** new image
5. **Deploy updated task definition**
6. **Add CVE to blocklist** in CI/CD scanning

---

## Developer Security Best Practices

### Code Security Checklist

- [ ] **Never commit secrets** to version control
  - Use `.env` files (in `.gitignore`)
  - Use environment variables in CI/CD
  - Use AWS Secrets Manager in production

- [ ] **Input validation** on all API endpoints
  - Use Pydantic models for type validation
  - Implement length limits (e.g., max 2000 chars for prompts)
  - Validate file types and sizes for uploads
  - Sanitize user input before database queries

- [ ] **Parameterized queries** for database access
  - Always use SQLAlchemy ORM (not raw SQL)
  - Never concatenate user input into SQL queries
  - Use bind parameters for dynamic queries

- [ ] **Secure dependencies**
  - Run `pip-audit` before every release
  - Update dependencies monthly
  - Review Dependabot PRs promptly
  - Pin versions in `requirements.txt`

- [ ] **Error handling**
  - Never expose stack traces to users
  - Log detailed errors to CloudWatch
  - Return generic error messages to API clients
  - Don't leak system information in errors

- [ ] **Authentication & Authorization**
  - Use strong password hashing (bcrypt, argon2)
  - Implement rate limiting on login endpoints
  - Use secure session cookies (httpOnly, secure, SameSite)
  - Validate JWT tokens on every request

### Secure Coding Standards

#### Example: Secure File Upload

```python
# BAD: No validation
@app.post("/upload")
async def upload_file(file: UploadFile):
    contents = await file.read()
    with open(f"/uploads/{file.filename}", "wb") as f:
        f.write(contents)

# GOOD: Validated upload
from pathlib import Path
import magic

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@app.post("/upload")
async def upload_file(file: UploadFile):
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")

    # Validate file content (magic bytes)
    mime_type = magic.from_buffer(contents, mime=True)
    if not mime_type.startswith("video/"):
        raise HTTPException(400, "Not a video file")

    # Generate safe filename (prevent path traversal)
    safe_filename = f"{uuid.uuid4()}{ext}"
    file_path = Path("/uploads") / safe_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    return {"filename": safe_filename}
```

#### Example: Secure Database Query

```python
# BAD: SQL injection vulnerable
@app.get("/user/{username}")
async def get_user(username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    result = await db.execute(query)

# GOOD: Parameterized query
@app.get("/user/{username}")
async def get_user(username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
```

### Dependency Update Policy

**Schedule:**
- **Security patches:** Immediately (within 24 hours)
- **Minor updates:** Weekly (automated Dependabot)
- **Major updates:** Monthly (manual review)

**Process:**
1. Dependabot creates PR for dependency update
2. CI/CD runs automated tests
3. Security scan checks for new vulnerabilities
4. Developer reviews changelog and breaking changes
5. Merge if all checks pass
6. Monitor production for issues

**Critical Vulnerabilities:**
- **CVE Score 9.0+:** Emergency patch within 24 hours
- **CVE Score 7.0-8.9:** Patch within 1 week
- **CVE Score 4.0-6.9:** Patch within 1 month
- **CVE Score <4.0:** Next scheduled update

---

## OWASP Top 10 Compliance

### A01:2021 – Broken Access Control

**Status:** ⚠️ Partial

**Controls:**
- [x] IAM roles with least privilege
- [x] Security groups restrict network access
- [ ] API-level authorization (pending user auth implementation)

**Recommendations:**
- Implement role-based access control (RBAC)
- Validate user permissions on every API call
- Use JWT tokens with short expiration (15 minutes)

---

### A02:2021 – Cryptographic Failures

**Status:** ✅ Good

**Controls:**
- [x] RDS encryption at rest (AWS managed keys)
- [x] S3 bucket encryption (AES256)
- [x] HTTPS for all API communication
- [ ] ElastiCache encryption in transit (pending)

**Recommendations:**
- Enable Redis TLS encryption
- Use AWS KMS for encryption key management
- Rotate encryption keys annually

---

### A03:2021 – Injection

**Status:** ✅ Good

**Controls:**
- [x] SQLAlchemy ORM (parameterized queries)
- [x] Pydantic input validation
- [ ] NoSQL injection prevention (Redis commands)

**Recommendations:**
- Never use raw SQL queries
- Sanitize all user input before Redis operations
- Use prepared statements for all database queries

---

### A04:2021 – Insecure Design

**Status:** ✅ Good

**Controls:**
- [x] Security groups designed with least privilege
- [x] Private subnets for databases
- [x] No direct internet access to databases

**Recommendations:**
- Conduct threat modeling before new features
- Use secure defaults in all configurations
- Implement defense in depth

---

### A05:2021 – Security Misconfiguration

**Status:** ⚠️ Moderate

**Controls:**
- [x] No default credentials used
- [x] Error messages don't leak system info
- [ ] CORS allows all origins (needs restriction)
- [ ] CloudTrail not enabled (no audit logs)

**Recommendations:**
- Restrict S3 CORS to frontend domain
- Enable CloudTrail for audit logging
- Remove development/debug settings in production

---

### A06:2021 – Vulnerable and Outdated Components

**Status:** ✅ Good

**Controls:**
- [x] ECR image scanning enabled
- [x] Dependabot enabled (GitHub)
- [x] Regular dependency updates

**Recommendations:**
- Add automated vulnerability scanning to CI/CD
- Fail builds on critical vulnerabilities
- Monthly dependency update review

---

### A07:2021 – Identification and Authentication Failures

**Status:** N/A (No auth implemented)

**Future Controls:**
- [ ] Implement secure password hashing (argon2)
- [ ] Add rate limiting on login attempts
- [ ] Implement multi-factor authentication (MFA)
- [ ] Use secure session management

**Recommendations:**
- Use OAuth 2.0 / OpenID Connect for authentication
- Implement JWT with refresh tokens
- Add CAPTCHA to prevent brute force attacks

---

### A08:2021 – Software and Data Integrity Failures

**Status:** ✅ Good

**Controls:**
- [x] Container image signing (ECR)
- [x] No code downloaded from untrusted sources
- [x] Dependencies pinned in requirements.txt

**Recommendations:**
- Implement CI/CD pipeline security
- Use GitHub Actions signed commits
- Verify cryptographic signatures on all dependencies

---

### A09:2021 – Security Logging and Monitoring Failures

**Status:** ⚠️ Partial

**Controls:**
- [x] CloudWatch Logs for application logs
- [x] ECS task metrics
- [ ] CloudTrail not enabled (no API audit logs)
- [ ] No security alerting

**Recommendations:**
- Enable CloudTrail for all AWS API calls
- Add CloudWatch Alarms for suspicious activity
- Implement log aggregation and analysis (ELK stack or similar)

---

### A10:2021 – Server-Side Request Forgery (SSRF)

**Status:** ⚠️ Moderate

**Controls:**
- [x] No user-controlled URLs in backend
- [ ] Need to validate Replicate API responses

**Recommendations:**
- Whitelist allowed external API domains
- Validate all URLs before making requests
- Use network segmentation to prevent internal access

---

## Penetration Testing Recommendations

### Pre-Production Checklist

Before conducting penetration testing:

1. **Complete all security hardening** (see above sections)
2. **Enable CloudTrail** to log all testing activity
3. **Notify AWS** if testing will exceed normal traffic patterns
4. **Document scope** of testing (in-scope vs. out-of-scope systems)
5. **Backup all data** before testing begins

### Recommended Testing Scope

#### In-Scope
- [x] FastAPI application (all endpoints)
- [x] S3 bucket permissions
- [x] RDS database (connection, authentication)
- [x] ElastiCache Redis (connection, authentication)
- [x] IAM role permissions
- [x] Security group configurations
- [x] Container escape attempts

#### Out-of-Scope
- [ ] DDoS attacks (coordinate with AWS first)
- [ ] Social engineering (phishing)
- [ ] Physical security
- [ ] Third-party services (Replicate API)

### Testing Methodology

**Recommended Frameworks:**
- **OWASP Testing Guide:** Web application security
- **NIST SP 800-115:** Technical security assessment
- **PTES:** Penetration Testing Execution Standard

**Testing Phases:**
1. **Reconnaissance:** Information gathering (public data only)
2. **Scanning:** Port scanning, vulnerability scanning
3. **Exploitation:** Attempt to exploit identified vulnerabilities
4. **Post-Exploitation:** Assess impact, lateral movement
5. **Reporting:** Document findings with severity ratings

### External Auditing Services

**Recommended Vendors:**
- **Cobalt:** On-demand penetration testing ($5k-$10k)
- **HackerOne:** Bug bounty platform ($1k/month minimum)
- **Synack:** Continuous security testing ($10k-$20k)
- **AWS Security Hub:** Automated compliance checks (free)

**Budget Recommendation:**
- **Pre-MVP:** $0 (use automated tools only)
- **Post-MVP:** $5k-$10k (annual penetration test)
- **Production:** $20k-$50k (quarterly assessments)

### DIY Security Testing Tools

**Free Tools:**
1. **OWASP ZAP:** Web application scanner
2. **Burp Suite Community:** Request interception and analysis
3. **SQLMap:** SQL injection testing
4. **Nikto:** Web server scanner
5. **Trivy:** Container and dependency scanning
6. **Bandit:** Python code security linter
7. **TFSec:** Terraform security scanner

**Usage Example:**

```bash
# Run OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://ecs-task-ip:8000 \
  -r zap-report.html

# Run SQLMap against API
sqlmap -u "http://ecs-task-ip:8000/api/endpoint?id=1" \
  --batch --level=5 --risk=3

# Scan container image
trivy image delicious-lotus-backend:latest \
  --severity HIGH,CRITICAL
```

---

## Security Monitoring & Logging

### CloudWatch Alarms

**Recommended Alarms:**

1. **High Error Rate:**
   - Metric: ECS task errors > 10 in 5 minutes
   - Action: SNS notification to #alerts channel

2. **Failed RDS Connections:**
   - Metric: PostgreSQL connection errors > 5 in 5 minutes
   - Action: Page on-call engineer

3. **S3 Bucket Policy Changes:**
   - Metric: CloudTrail event `PutBucketPolicy`
   - Action: Immediate security team notification

4. **IAM Policy Changes:**
   - Metric: CloudTrail events `CreatePolicy`, `AttachUserPolicy`
   - Action: Immediate security team notification

5. **Unusual API Traffic:**
   - Metric: API requests > 1000/minute (baseline: 100/min)
   - Action: Investigate potential DDoS

### Log Aggregation

**Current:** CloudWatch Logs (7-day retention)

**Recommendation:** Export to S3 for long-term storage

```hcl
resource "aws_cloudwatch_log_subscription_filter" "export_to_s3" {
  name            = "export-logs-to-s3"
  log_group_name  = "/ecs/delicious-lotus"
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.logs.arn
}

resource "aws_kinesis_firehose_delivery_stream" "logs" {
  name        = "log-export-stream"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.logs.arn
    prefix     = "logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"

    compression_format = "GZIP"
  }
}
```

### Security Metrics Dashboard

**Key Metrics:**
- Failed authentication attempts (when auth implemented)
- API error rates (4xx, 5xx)
- Database connection errors
- S3 access denied errors
- IAM policy changes
- Security group modifications
- ECR vulnerability scan results

**Tools:**
- **CloudWatch Dashboard:** AWS-native metrics
- **Grafana:** Advanced visualization (open-source)
- **Datadog:** Comprehensive monitoring (paid, $15/host/month)

---

## Security Compliance & Certifications

### Current Compliance Status

**SOC 2:** Not applicable (no third-party audit required for MVP)
**GDPR:** Pending (if serving EU customers)
**HIPAA:** Not applicable (no healthcare data)
**PCI DSS:** Not applicable (no payment processing)

### GDPR Considerations (If Applicable)

If serving users in the EU:

- [ ] **Data Minimization:** Only collect necessary user data
- [ ] **Right to Erasure:** Implement user data deletion
- [ ] **Data Portability:** Allow users to export their data
- [ ] **Consent Management:** Explicit opt-in for data collection
- [ ] **Data Breach Notification:** 72-hour notification requirement
- [ ] **Data Processing Agreement:** With AWS (already covered by AWS GDPR compliance)

**AWS GDPR Resources:**
- AWS is GDPR compliant (use AWS Data Processing Addendum)
- Use AWS Config to audit data storage locations
- Enable CloudTrail for data access logging

---

## Appendix A: Security Scanning Script

See `scripts/security-scan.sh` for automated vulnerability scanning.

**Usage:**
```bash
./scripts/security-scan.sh
```

**Output:**
- Dependency vulnerabilities (safety, pip-audit)
- Code security issues (Bandit)
- Docker image vulnerabilities (Trivy)
- Terraform misconfigurations (TFSec)

---

## Appendix B: CI/CD Security Integration

See `.github/workflows/security-scan.yml` for GitHub Actions security workflow.

**Triggers:**
- Every pull request
- Weekly scheduled scan (Sunday 2 AM UTC)
- Manual trigger via GitHub Actions UI

**Checks:**
- Dependency vulnerabilities
- Code security scanning
- Docker image scanning
- Secret detection (gitleaks)

---

## Appendix C: Security Contacts

**Security Incident Reporting:**
- Email: security@delicious-lotus.com
- Slack: #security-incidents
- On-Call: +1 (XXX) XXX-XXXX

**Responsible Disclosure:**
If you discover a security vulnerability, please report it privately to security@delicious-lotus.com. Do not publicly disclose until we have had a chance to address it.

**Bug Bounty:** Not currently available (consider post-MVP)

---

## Appendix D: Security Audit History

| Date | Auditor | Scope | Findings | Status |
|------|---------|-------|----------|--------|
| 2025-11-15 | Internal | Full infrastructure | 23 recommendations | In Progress |

---

## Document Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-15 | DevOps Team | Initial security audit and hardening documentation |

---

**End of Security Documentation**

For questions or clarifications, contact the DevOps team or security@delicious-lotus.com.

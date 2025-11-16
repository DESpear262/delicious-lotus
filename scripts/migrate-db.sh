#!/bin/bash
#
# Database Migration Script
# Applies schema changes to the PostgreSQL database
#
# Usage:
#   ./scripts/migrate-db.sh [init|migrate|rollback|status]
#
# Commands:
#   init      - Initialize database with base schema (fresh install)
#   migrate   - Apply pending migrations
#   rollback  - Rollback last migration
#   status    - Show current schema version and pending migrations
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIGRATIONS_DIR="$PROJECT_ROOT/backend/migrations"
INIT_SQL="$PROJECT_ROOT/docker/postgres/init.sql"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

get_database_url() {
    # Try to get from terraform output
    if [ -f "$PROJECT_ROOT/terraform/terraform.tfstate" ]; then
        cd "$PROJECT_ROOT/terraform"
        DB_URL=$(terraform output -raw database_url 2>/dev/null || echo "")
        if [ -n "$DB_URL" ]; then
            echo "$DB_URL"
            return
        fi
    fi

    # Fall back to environment variable
    if [ -n "$DATABASE_URL" ]; then
        echo "$DATABASE_URL"
        return
    fi

    log_error "Could not determine database URL."
    log_error "Please set DATABASE_URL environment variable or deploy infrastructure first."
    exit 1
}

run_via_ecs_task() {
    log_info "Running migration via ECS task in VPC..."

    cd "$PROJECT_ROOT/terraform"

    CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "ai-video-cluster")
    AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-2")

    # Get subnet and security group
    SUBNET_ID=$(aws ec2 describe-subnets \
        --filters "Name=default-for-az,Values=true" \
        --region "$AWS_REGION" \
        --query 'Subnets[0].SubnetId' \
        --output text)

    SG_ID=$(terraform state show 'module.security.aws_security_group.ecs' 2>/dev/null | grep 'id ' | head -1 | awk '{print $3}' | tr -d '"')

    # Encode SQL script
    SQL_B64=$(base64 -w 0 "$1")

    # Create temporary task definition
    TASK_DEF=$(cat <<EOF
{
  "family": "db-migrate-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/dev-ecs-task-execution-role",
  "containerDefinitions": [{
    "name": "postgres-client",
    "image": "postgres:16-alpine",
    "essential": true,
    "command": ["sh", "-c", "echo \"\$SQL_SCRIPT\" | base64 -d | psql \"\$DATABASE_URL\""],
    "environment": [
      {"name": "DATABASE_URL", "value": "$(get_database_url)"},
      {"name": "SQL_SCRIPT", "value": "$SQL_B64"}
    ]
  }]
}
EOF
)

    # Register task definition
    TASK_ARN=$(echo "$TASK_DEF" | aws ecs register-task-definition \
        --cli-input-json file:///dev/stdin \
        --region "$AWS_REGION" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

    # Run task
    RUN_TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER_NAME" \
        --task-definition "$TASK_ARN" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region "$AWS_REGION" \
        --query 'tasks[0].taskArn' \
        --output text)

    TASK_ID=$(echo "$RUN_TASK_ARN" | awk -F/ '{print $NF}')

    # Wait for task to complete
    log_info "Waiting for migration task to complete..."
    sleep 15

    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster "$CLUSTER_NAME" \
        --tasks "$TASK_ID" \
        --region "$AWS_REGION" \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)

    if [ "$EXIT_CODE" == "0" ]; then
        log_info "Migration completed successfully ✓"
    else
        log_error "Migration failed with exit code $EXIT_CODE"
        exit 1
    fi
}

init_database() {
    log_info "Initializing database with base schema..."

    if [ ! -f "$INIT_SQL" ]; then
        log_error "Init SQL file not found: $INIT_SQL"
        exit 1
    fi

    # Check if we can connect directly
    DB_URL=$(get_database_url)

    if command -v psql &> /dev/null; then
        log_info "Attempting direct connection..."
        if psql "$DB_URL" -c "SELECT 1" &> /dev/null; then
            log_info "Direct connection successful"
            psql "$DB_URL" < "$INIT_SQL"
            log_info "Database initialized ✓"
            return
        fi
    fi

    # Fall back to ECS task
    log_warn "Direct connection failed. Using ECS task (requires deployed infrastructure)..."
    run_via_ecs_task "$INIT_SQL"
}

migrate_database() {
    log_info "Applying database migrations..."

    if [ ! -d "$MIGRATIONS_DIR" ]; then
        log_warn "Migrations directory not found. Creating it..."
        mkdir -p "$MIGRATIONS_DIR"
        log_info "Add migration SQL files to: $MIGRATIONS_DIR"
        log_info "Name them: 001_description.sql, 002_description.sql, etc."
        return
    fi

    # Find all migration files
    MIGRATIONS=$(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

    if [ -z "$MIGRATIONS" ]; then
        log_info "No migrations found. Database is up to date."
        return
    fi

    DB_URL=$(get_database_url)

    for migration in $MIGRATIONS; do
        FILENAME=$(basename "$migration")
        VERSION=$(echo "$FILENAME" | cut -d_ -f1)

        log_info "Checking migration $FILENAME..."

        # Check if already applied
        APPLIED=$(psql "$DB_URL" -tAc "SELECT COUNT(*) FROM schema_migrations WHERE version = $VERSION" 2>/dev/null || echo "0")

        if [ "$APPLIED" == "0" ]; then
            log_info "Applying migration $FILENAME..."

            if command -v psql &> /dev/null && psql "$DB_URL" -c "SELECT 1" &> /dev/null; then
                # Direct connection
                psql "$DB_URL" < "$migration"
                psql "$DB_URL" -c "INSERT INTO schema_migrations (version, description) VALUES ($VERSION, '$(basename "$migration" .sql)')"
            else
                # Via ECS task
                run_via_ecs_task "$migration"
            fi

            log_info "Migration $FILENAME applied ✓"
        else
            log_info "Migration $FILENAME already applied, skipping."
        fi
    done

    log_info "All migrations applied ✓"
}

show_status() {
    log_info "Database migration status:"

    DB_URL=$(get_database_url)

    if command -v psql &> /dev/null && psql "$DB_URL" -c "SELECT 1" &> /dev/null 2>&1; then
        echo ""
        echo "Current schema version:"
        psql "$DB_URL" -c "SELECT version, description, applied_at FROM schema_migrations ORDER BY version DESC LIMIT 5"

        echo ""
        echo "Database tables:"
        psql "$DB_URL" -c "\dt public.*"
    else
        log_warn "Cannot connect directly to database. Database is in VPC (secure)."
        log_info "To check status, use AWS Console or deploy a bastion host."
    fi
}

# Main script
COMMAND=${1:-status}

case "$COMMAND" in
    init)
        init_database
        ;;
    migrate)
        migrate_database
        ;;
    status)
        show_status
        ;;
    rollback)
        log_error "Rollback not implemented yet. Please create a new migration to undo changes."
        exit 1
        ;;
    *)
        echo "Usage: $0 [init|migrate|rollback|status]"
        echo ""
        echo "Commands:"
        echo "  init      - Initialize database with base schema"
        echo "  migrate   - Apply pending migrations"
        echo "  rollback  - Rollback last migration (TODO)"
        echo "  status    - Show current schema version"
        exit 1
        ;;
esac

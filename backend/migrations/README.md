# Database Migrations

This directory contains SQL migration scripts for evolving the database schema over time.

## Migration Files

Migrations are numbered sequentially and should follow this naming convention:

```
001_description_of_change.sql
002_another_change.sql
003_add_new_table.sql
```

## Initial Schema

The initial schema (version 1) is in `docker/postgres/init.sql` and includes:
- All core tables (user_sessions, generation_jobs, clips, compositions, brand_assets, etc.)
- Indexes, views, functions, and triggers
- Default configuration data

## Creating a New Migration

1. Create a new SQL file with the next sequential number
2. Write your SQL changes (ALTER TABLE, CREATE INDEX, etc.)
3. Test locally first: `psql $DATABASE_URL < backend/migrations/00X_your_change.sql`
4. Run migration script: `./scripts/migrate-db.sh migrate`

## Example Migration

**File:** `002_add_user_email.sql`

```sql
-- Add email column to user_sessions table
ALTER TABLE user_sessions
ADD COLUMN email VARCHAR(255);

CREATE INDEX idx_user_sessions_email ON user_sessions(email);

-- Update schema_migrations is handled automatically by migrate-db.sh
```

## Running Migrations

### Local Development
```bash
# Check migration status
./scripts/migrate-db.sh status

# Apply all pending migrations
./scripts/migrate-db.sh migrate
```

### Production
Migrations are automatically run through ECS tasks in the VPC:
```bash
# Same commands work - script detects environment
./scripts/migrate-db.sh migrate
```

## Migration Tracking

Migrations are tracked in the `schema_migrations` table:
- `version`: Sequential number matching the migration file
- `description`: Description from the filename
- `applied_at`: Timestamp when migration was applied

## Best Practices

1. **Never modify existing migrations** - Create new ones instead
2. **Test in development first** - Always test before production
3. **Make migrations reversible** - Include rollback instructions in comments
4. **Keep migrations small** - One logical change per migration
5. **Document breaking changes** - Add comments for API/code changes needed

## Rollback Strategy

If a migration fails or needs to be reversed:

1. Create a new migration that undoes the changes
2. Don't delete or modify the failed migration
3. Document the rollback in the new migration file

Example:
```sql
-- Rollback for migration 005_add_analytics_table.sql
DROP TABLE IF EXISTS analytics CASCADE;
```

## Schema Version

Current schema version: **1** (Initial MVP schema)

Check current version:
```bash
./scripts/migrate-db.sh status
```

#!/bin/bash
# ===================================
# FFmpeg Backend Database Initialization
# ===================================
#
# This script creates the ffmpeg_backend database for the FFmpeg Backend service.
# It connects to the postgres database to create the new database.
#
# During initialization, this script runs as the postgres superuser.
# ===================================

set -e

# Get database user from environment or use default
POSTGRES_USER="${POSTGRES_USER:-ai_video_user}"

# Check if database exists and create if it doesn't
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ffmpeg_backend') THEN
            CREATE DATABASE ffmpeg_backend;
        END IF;
    END
    \$\$;

    -- Grant privileges to the application user
    GRANT ALL PRIVILEGES ON DATABASE ffmpeg_backend TO "$POSTGRES_USER";
EOSQL

# Add comment to the database (need to connect to it)
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "ffmpeg_backend" <<-EOSQL
    COMMENT ON DATABASE ffmpeg_backend IS 'Database for FFmpeg Backend service - handles video composition processing';
EOSQL

echo "FFmpeg Backend database 'ffmpeg_backend' created successfully (if it didn't exist)."


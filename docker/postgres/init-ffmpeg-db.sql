-- ===================================
-- FFmpeg Backend Database Initialization
-- ===================================
--
-- This script creates the ffmpeg_backend database for the FFmpeg Backend service.
-- Note: This runs in the context of the ai_video_pipeline database, so we need
-- to connect to postgres database to create a new database.
--
-- However, since SQL files in /docker-entrypoint-initdb.d/ run against the
-- database specified by POSTGRES_DB, we'll use a shell script approach instead.
-- This file is kept for reference but the actual creation is done via init-ffmpeg-db.sh
--
-- ===================================

-- This SQL file cannot directly create another database from within a database context.
-- The actual database creation is handled by init-ffmpeg-db.sh shell script.


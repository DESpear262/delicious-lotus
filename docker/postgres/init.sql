-- ===================================
-- AI Video Generation Pipeline
-- Initial Database Schema
-- ===================================
--
-- This script initializes the PostgreSQL database with tables
-- for tracking video generation jobs, clips, compositions, and assets.
--
-- Based on PRD Data Models:
-- - Generation Job: Tracks overall video generation request
-- - Clip: Individual generated video/image segment
-- - Composition: Final assembled video
-- - Brand Asset: Uploaded logos/images
-- - User Session: Tracks user interactions
--
-- ===================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================================
-- Core Tables
-- ===================================

-- User Sessions (simplified for MVP - full auth in Phase 2)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_identifier VARCHAR(255),  -- IP address or anonymous ID for MVP
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- Generation Jobs (tracks overall video generation request)
CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,

    -- Job type and status
    job_type VARCHAR(50) NOT NULL,  -- 'ad_creative' or 'music_video'
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, planning, generating, composing, completed, failed

    -- Input parameters
    prompt TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,  -- 15-60 for ads, 60-180 for music
    aspect_ratio VARCHAR(10) NOT NULL,  -- '16:9', '9:16', '1:1'

    -- Ad-specific parameters
    brand_colors JSONB,  -- Array of hex colors
    cta_text VARCHAR(255),  -- Call-to-action text

    -- Music video specific parameters
    audio_file_url TEXT,  -- S3 URL or local path to audio file
    music_genre VARCHAR(100),  -- Genre for visual theme selection
    beat_data JSONB,  -- Beat detection results (tempo, beats array)

    -- Processing metadata
    clip_count INTEGER,  -- Number of clips to generate
    planned_scenes JSONB,  -- Array of scene descriptions
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Cost tracking
    estimated_cost_usd DECIMAL(10, 4),
    actual_cost_usd DECIMAL(10, 4),

    -- Output
    composition_id UUID,  -- FK to compositions table (set when complete)

    CONSTRAINT valid_job_type CHECK (job_type IN ('ad_creative', 'music_video')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'planning', 'generating', 'composing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_aspect_ratio CHECK (aspect_ratio IN ('16:9', '9:16', '1:1')),
    CONSTRAINT valid_duration CHECK (
        (job_type = 'ad_creative' AND duration_seconds BETWEEN 15 AND 60) OR
        (job_type = 'music_video' AND duration_seconds BETWEEN 60 AND 180)
    )
);

CREATE INDEX idx_jobs_session ON generation_jobs(session_id);
CREATE INDEX idx_jobs_status ON generation_jobs(status);
CREATE INDEX idx_jobs_type ON generation_jobs(job_type);
CREATE INDEX idx_jobs_created ON generation_jobs(created_at DESC);

-- Clips (individual generated video/image segments)
CREATE TABLE clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,

    -- Clip metadata
    sequence_number INTEGER NOT NULL,  -- Order in the final video (1-indexed)
    clip_type VARCHAR(50) NOT NULL,  -- 'image', 'video', 'text_overlay'

    -- Generation details
    prompt TEXT NOT NULL,  -- Scene-specific prompt used to generate this clip
    model_name VARCHAR(255),  -- Replicate model used
    model_version VARCHAR(255),  -- Model version/hash

    -- Asset references
    source_url TEXT,  -- URL to generated asset (S3 or Replicate)
    local_path TEXT,  -- Local file path (if downloaded)
    thumbnail_url TEXT,  -- Preview thumbnail

    -- Clip properties
    duration_seconds DECIMAL(5, 2),  -- Duration for video clips
    width INTEGER,
    height INTEGER,
    file_size_bytes BIGINT,
    format VARCHAR(10),  -- 'mp4', 'png', 'jpg'

    -- Processing status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, generating, completed, failed
    generation_time_seconds DECIMAL(8, 2),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_at TIMESTAMP WITH TIME ZONE,

    -- Cost tracking
    generation_cost_usd DECIMAL(10, 4),

    -- Metadata for editor
    editor_metadata JSONB DEFAULT '{}'::jsonb,  -- Trim points, effects, etc.

    CONSTRAINT valid_clip_status CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    CONSTRAINT valid_clip_type CHECK (clip_type IN ('image', 'video', 'text_overlay'))
);

CREATE INDEX idx_clips_job ON clips(job_id);
CREATE INDEX idx_clips_sequence ON clips(job_id, sequence_number);
CREATE INDEX idx_clips_status ON clips(status);

-- Compositions (final assembled videos)
CREATE TABLE compositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,

    -- Composition metadata
    title VARCHAR(255),
    description TEXT,

    -- Timeline data
    timeline_data JSONB NOT NULL,  -- Full timeline with clips, transitions, overlays

    -- Output details
    output_url TEXT,  -- S3 URL to final video
    local_path TEXT,  -- Local file path
    thumbnail_url TEXT,  -- Video thumbnail

    -- Video properties
    duration_seconds DECIMAL(8, 2) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    file_size_bytes BIGINT,
    format VARCHAR(10) DEFAULT 'mp4',
    codec VARCHAR(50) DEFAULT 'h264',

    -- Audio properties
    audio_codec VARCHAR(50) DEFAULT 'aac',
    audio_bitrate_kbps INTEGER DEFAULT 128,

    -- Processing details
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, rendering, completed, failed
    render_time_seconds DECIMAL(8, 2),
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rendered_at TIMESTAMP WITH TIME ZONE,

    -- Versioning (for edits/re-renders)
    version INTEGER DEFAULT 1,
    parent_composition_id UUID REFERENCES compositions(id),  -- For tracking edits

    CONSTRAINT valid_composition_status CHECK (status IN ('pending', 'rendering', 'completed', 'failed')),
    CONSTRAINT valid_format CHECK (format IN ('mp4', 'mov', 'webm'))
);

CREATE INDEX idx_compositions_job ON compositions(job_id);
CREATE INDEX idx_compositions_status ON compositions(status);
CREATE INDEX idx_compositions_parent ON compositions(parent_composition_id);

-- Update generation_jobs FK to compositions
ALTER TABLE generation_jobs
ADD CONSTRAINT fk_jobs_composition
FOREIGN KEY (composition_id) REFERENCES compositions(id) ON DELETE SET NULL;

-- Brand Assets (uploaded logos/images for ads)
CREATE TABLE brand_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,

    -- Asset details
    asset_type VARCHAR(50) NOT NULL,  -- 'logo', 'product_image', 'background'
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),

    -- Storage
    storage_url TEXT NOT NULL,  -- S3 URL or local path
    thumbnail_url TEXT,

    -- File properties
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,

    -- Metadata
    description TEXT,
    tags JSONB DEFAULT '[]'::jsonb,

    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),

    CONSTRAINT valid_asset_type CHECK (asset_type IN ('logo', 'product_image', 'background', 'audio', 'other'))
);

CREATE INDEX idx_assets_session ON brand_assets(session_id);
CREATE INDEX idx_assets_type ON brand_assets(asset_type);
CREATE INDEX idx_assets_expires ON brand_assets(expires_at);

-- ===================================
-- Job Processing Queue (for Celery tracking)
-- ===================================

CREATE TABLE task_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,  -- Celery task ID
    job_id UUID REFERENCES generation_jobs(id) ON DELETE CASCADE,

    task_name VARCHAR(255) NOT NULL,  -- e.g., 'generate_clip', 'compose_video'
    task_args JSONB,
    task_kwargs JSONB,

    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, started, retry, success, failure
    priority INTEGER DEFAULT 5,  -- 1-10, higher = more important

    result JSONB,
    error_message TEXT,
    traceback TEXT,

    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_task_status CHECK (status IN ('pending', 'started', 'retry', 'success', 'failure', 'cancelled'))
);

CREATE INDEX idx_tasks_task_id ON task_queue(task_id);
CREATE INDEX idx_tasks_job ON task_queue(job_id);
CREATE INDEX idx_tasks_status ON task_queue(status);
CREATE INDEX idx_tasks_priority ON task_queue(priority DESC, created_at ASC);

-- ===================================
-- Analytics & Metrics (for monitoring)
-- ===================================

CREATE TABLE job_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,

    -- Performance metrics
    total_duration_seconds DECIMAL(10, 2),
    planning_time_seconds DECIMAL(8, 2),
    generation_time_seconds DECIMAL(8, 2),
    composition_time_seconds DECIMAL(8, 2),

    -- Resource usage
    clip_count INTEGER,
    total_api_calls INTEGER,
    cache_hits INTEGER,
    cache_misses INTEGER,

    -- Cost metrics
    total_cost_usd DECIMAL(10, 4),
    cost_per_second_usd DECIMAL(10, 6),

    -- Quality metrics
    final_file_size_mb DECIMAL(10, 2),
    compression_ratio DECIMAL(6, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_job ON job_metrics(job_id);
CREATE INDEX idx_metrics_created ON job_metrics(created_at DESC);

-- ===================================
-- System Configuration
-- ===================================

CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    value_type VARCHAR(50) NOT NULL,  -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255) DEFAULT 'system'
);

-- Insert default configuration
INSERT INTO system_config (key, value, value_type, description) VALUES
    ('max_concurrent_jobs', '5', 'integer', 'Maximum number of concurrent video generation jobs'),
    ('default_clip_count_ads', '5', 'integer', 'Default number of clips for ad videos'),
    ('default_clip_count_music', '15', 'integer', 'Default number of clips for music videos'),
    ('cleanup_jobs_after_days', '7', 'integer', 'Delete completed jobs after this many days'),
    ('enable_ad_pipeline', 'true', 'boolean', 'Enable ad creative pipeline'),
    ('enable_music_pipeline', 'false', 'boolean', 'Enable music video pipeline (post-MVP)'),
    ('cost_alert_threshold_usd', '10.00', 'string', 'Alert when single job exceeds this cost'),
    ('storage_quota_gb', '100', 'integer', 'Maximum storage quota in GB');

-- ===================================
-- Cleanup Functions
-- ===================================

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old jobs
CREATE OR REPLACE FUNCTION cleanup_old_jobs(days_old INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM generation_jobs
    WHERE status IN ('completed', 'failed', 'cancelled')
    AND completed_at < (CURRENT_TIMESTAMP - (days_old || ' days')::INTERVAL);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update job status
CREATE OR REPLACE FUNCTION update_job_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'started' AND OLD.status = 'pending' THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('completed', 'failed', 'cancelled') AND NEW.completed_at IS NULL THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update timestamps
CREATE TRIGGER trigger_update_job_timestamps
    BEFORE UPDATE ON generation_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_job_status();

-- ===================================
-- Views for Convenience
-- ===================================

-- Active jobs view
CREATE VIEW active_jobs AS
SELECT
    j.id,
    j.job_type,
    j.status,
    j.duration_seconds,
    j.aspect_ratio,
    j.created_at,
    j.started_at,
    COUNT(c.id) AS clips_generated,
    j.clip_count AS clips_total,
    COALESCE(m.total_cost_usd, 0) AS cost_usd
FROM generation_jobs j
LEFT JOIN clips c ON c.job_id = j.id AND c.status = 'completed'
LEFT JOIN job_metrics m ON m.job_id = j.id
WHERE j.status NOT IN ('completed', 'failed', 'cancelled')
GROUP BY j.id, m.total_cost_usd;

-- Job summary view
CREATE VIEW job_summary AS
SELECT
    j.id,
    j.job_type,
    j.status,
    j.created_at,
    j.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(j.completed_at, CURRENT_TIMESTAMP) - j.created_at)) AS duration_seconds,
    COUNT(c.id) AS total_clips,
    COALESCE(m.total_cost_usd, 0) AS total_cost_usd,
    comp.output_url,
    comp.file_size_bytes
FROM generation_jobs j
LEFT JOIN clips c ON c.job_id = j.id
LEFT JOIN job_metrics m ON m.job_id = j.id
LEFT JOIN compositions comp ON comp.id = j.composition_id
GROUP BY j.id, m.total_cost_usd, comp.output_url, comp.file_size_bytes;

-- ===================================
-- Initial Data
-- ===================================

-- Create a default session for testing
INSERT INTO user_sessions (session_token, user_identifier)
VALUES ('dev_session_token', 'localhost_developer');

-- ===================================
-- Permissions (for application user)
-- ===================================

-- Grant permissions to the application user
-- Note: In production, create a separate app_user with limited permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO CURRENT_USER;

-- ===================================
-- Schema Version Tracking
-- ===================================

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) VALUES
    (1, 'Initial schema - MVP database structure for AI Video Generation Pipeline');

-- ===================================
-- Helpful Comments
-- ===================================

COMMENT ON TABLE generation_jobs IS 'Tracks overall video generation requests from users';
COMMENT ON TABLE clips IS 'Individual generated video/image segments that compose the final video';
COMMENT ON TABLE compositions IS 'Final assembled videos with timeline data';
COMMENT ON TABLE brand_assets IS 'User-uploaded logos, images, and audio files for video generation';
COMMENT ON TABLE user_sessions IS 'User sessions for MVP (anonymous/IP-based, OAuth in Phase 2)';
COMMENT ON TABLE task_queue IS 'Celery task tracking for async job processing';
COMMENT ON TABLE job_metrics IS 'Performance and cost metrics for completed jobs';
COMMENT ON TABLE system_config IS 'System-wide configuration key-value store';

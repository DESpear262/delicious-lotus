-- Database schema for AI Video Generation Pipeline
-- PR 303: Clip Assembly & DB/Redis Integration

-- Generations table (base table for video generation jobs)
CREATE TABLE IF NOT EXISTS generations (
    id VARCHAR(255) PRIMARY KEY,
    status VARCHAR(50) DEFAULT 'queued',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Clips table (stores individual video clips)
CREATE TABLE IF NOT EXISTS clips (
    clip_id VARCHAR(255) PRIMARY KEY,
    generation_id VARCHAR(255) NOT NULL,
    scene_id VARCHAR(255) NOT NULL,
    sequence_order INTEGER NOT NULL,
    start_time_seconds REAL NOT NULL,
    end_time_seconds REAL NOT NULL,
    storage_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    storage_path TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Video details
    video_url TEXT,
    duration_seconds REAL NOT NULL,
    resolution VARCHAR(10) DEFAULT '720p',
    format VARCHAR(10) DEFAULT 'mp4',

    -- Generation metadata
    model_used VARCHAR(255) DEFAULT 'google/veo-3.1-fast',
    prompt_used TEXT NOT NULL,
    negative_prompt_used TEXT,

    -- Quality metrics
    generation_time_seconds REAL,
    model_version VARCHAR(255),
    quality_score REAL CHECK (quality_score >= 0.0 AND quality_score <= 1.0),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_started_at TIMESTAMP WITH TIME ZONE,
    generation_completed_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message TEXT,
    error_code VARCHAR(255),
    retry_count INTEGER DEFAULT 0,

    -- Additional metadata
    file_size_bytes BIGINT,
    thumbnail_url TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Foreign key constraint
    FOREIGN KEY (generation_id) REFERENCES generations(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_clips_generation_id ON clips(generation_id);
CREATE INDEX IF NOT EXISTS idx_clips_sequence_order ON clips(generation_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(storage_status);
CREATE INDEX IF NOT EXISTS idx_clips_created_at ON clips(created_at);

-- Generations table indexes
CREATE INDEX IF NOT EXISTS idx_generations_status ON generations(status);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations(created_at);

-- Comments for documentation
COMMENT ON TABLE generations IS 'Base table for video generation jobs';
COMMENT ON TABLE clips IS 'Individual video clips generated for each scene';
COMMENT ON COLUMN clips.sequence_order IS 'Order of clip in final video assembly (0-based)';
COMMENT ON COLUMN clips.start_time_seconds IS 'Start time in final video timeline';
COMMENT ON COLUMN clips.end_time_seconds IS 'End time in final video timeline';
COMMENT ON COLUMN clips.storage_status IS 'Current status: pending, generating, completed, failed, retrying';

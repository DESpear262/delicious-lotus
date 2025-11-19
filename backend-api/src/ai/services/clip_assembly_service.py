"""
Clip Assembly Service - PR 303: Clip Assembly & DB/Redis Integration
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

from ..models.clip_assembly import (
    DatabaseClipMetadata,
    GenerationProgress,
    ClipAssemblyRequest,
    ClipAssemblyResponse,
    ClipRetrievalRequest,
    ClipRetrievalResponse,
    ClipStorageStatus
)

logger = logging.getLogger(__name__)


class ClipAssemblyService:
    """
    Service for assembling and managing video clips

    Handles database storage of clip metadata and Redis-based progress tracking.
    Maintains clip ordering and provides retrieval operations.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", db_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the clip assembly service

        Args:
            redis_url: Redis connection URL
            db_config: Database configuration dictionary
        """
        self.redis_url = redis_url
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'video_generation',
            'user': 'postgres',
            'password': 'password'
        }

        # Initialize connections (lazy loading)
        self._redis_client = None
        self._db_connection = None

        logger.info("ClipAssemblyService initialized")

    @property
    def redis_client(self) -> redis.Redis:
        """Lazy-loaded Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis_client

    @property
    def db_connection(self):
        """Lazy-loaded database connection"""
        if self._db_connection is None:
            self._db_connection = psycopg2.connect(**self.db_config)
            self._ensure_tables_exist()
        return self._db_connection

    def _ensure_tables_exist(self):
        """Create database tables if they don't exist"""
        with self.db_connection.cursor() as cursor:
            # Create clips table
            cursor.execute("""
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

                    -- Indexes for performance
                    FOREIGN KEY (generation_id) REFERENCES generations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_clips_generation_id ON clips(generation_id);
                CREATE INDEX IF NOT EXISTS idx_clips_sequence_order ON clips(generation_id, sequence_order);
                CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(storage_status);
            """)

            # Create generations table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    id VARCHAR(255) PRIMARY KEY,
                    status VARCHAR(50) DEFAULT 'queued',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    metadata JSONB
                );
            """)

            self.db_connection.commit()

    async def assemble_clips(self, request: ClipAssemblyRequest) -> ClipAssemblyResponse:
        """
        Store clips and update progress for a generation job

        Args:
            request: Clip assembly request with clips and progress

        Returns:
            Response indicating success and details
        """
        try:
            logger.info(f"Assembling {len(request.clips)} clips for generation {request.generation_id}")

            # Store clips in database
            stored_clips = []
            errors = []

            for clip in request.clips:
                try:
                    self._store_clip(clip)
                    stored_clips.append(clip.clip_id)
                except Exception as e:
                    error_msg = f"Failed to store clip {clip.clip_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Update progress in Redis
            try:
                self._update_progress(request.progress)
            except Exception as e:
                error_msg = f"Failed to update progress: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                progress_updated = False
            else:
                progress_updated = True

            # Update clip ordering in Redis
            try:
                self._update_clip_ordering(request.generation_id, request.clips)
            except Exception as e:
                error_msg = f"Failed to update clip ordering: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

            success = len(errors) == 0

            return ClipAssemblyResponse(
                generation_id=request.generation_id,
                clips_stored=len(stored_clips),
                progress_updated=progress_updated,
                success=success,
                stored_clip_ids=stored_clips,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Clip assembly failed for generation {request.generation_id}: {str(e)}")
            return ClipAssemblyResponse(
                generation_id=request.generation_id,
                clips_stored=0,
                progress_updated=False,
                success=False,
                errors=[str(e)]
            )

    def retrieve_clips(self, request: ClipRetrievalRequest) -> ClipRetrievalResponse:
        """
        Retrieve clips for a generation job

        Args:
            request: Clip retrieval request

        Returns:
            Response with retrieved clips
        """
        try:
            # Get clips from database
            clips = self._retrieve_clips_from_db(request)

            # Get progress from Redis
            progress = self._get_progress(request.generation_id)

            # Filter by status if requested
            if not request.include_failed:
                clips = [c for c in clips if c.storage_status != ClipStorageStatus.FAILED]

            # Sort by sequence order if requested
            if request.order_by_sequence:
                clips.sort(key=lambda c: c.sequence_order)

            successful_clips = sum(1 for c in clips if c.is_successful())

            return ClipRetrievalResponse(
                generation_id=request.generation_id,
                clips=clips,
                progress=progress,
                total_clips=len(clips),
                successful_clips=successful_clips,
                failed_clips=len(clips) - successful_clips
            )

        except Exception as e:
            logger.error(f"Clip retrieval failed for generation {request.generation_id}: {str(e)}")
            return ClipRetrievalResponse(
                generation_id=request.generation_id,
                clips=[],
                total_clips=0,
                successful_clips=0,
                failed_clips=0
            )

    def _store_clip(self, clip: DatabaseClipMetadata):
        """Store a single clip in the database"""
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO clips (
                    clip_id, generation_id, scene_id, sequence_order,
                    start_time_seconds, end_time_seconds, storage_status, storage_path,
                    video_url, duration_seconds, resolution, format,
                    model_used, prompt_used, negative_prompt_used,
                    generation_time_seconds, model_version, quality_score,
                    generation_started_at, generation_completed_at,
                    error_message, error_code, retry_count,
                    file_size_bytes, thumbnail_url, tags,
                    last_updated
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (clip_id) DO UPDATE SET
                    storage_status = EXCLUDED.storage_status,
                    video_url = EXCLUDED.video_url,
                    generation_time_seconds = EXCLUDED.generation_time_seconds,
                    generation_completed_at = EXCLUDED.generation_completed_at,
                    error_message = EXCLUDED.error_message,
                    error_code = EXCLUDED.error_code,
                    retry_count = EXCLUDED.retry_count,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    thumbnail_url = EXCLUDED.thumbnail_url,
                    last_updated = NOW()
            """, (
                clip.clip_id, clip.generation_id, clip.scene_id, clip.sequence_order,
                clip.start_time_seconds, clip.end_time_seconds, clip.storage_status.value, clip.storage_path,
                clip.video_url, clip.duration_seconds, clip.resolution.value, clip.format.value,
                clip.model_used, clip.prompt_used, clip.negative_prompt_used,
                clip.generation_time_seconds, clip.model_version, clip.quality_score,
                clip.generation_started_at, clip.generation_completed_at,
                clip.error_message, clip.error_code, clip.retry_count,
                clip.file_size_bytes, clip.thumbnail_url, clip.tags,
                clip.last_updated
            ))

        self.db_connection.commit()

    def _update_progress(self, progress: GenerationProgress):
        """Update generation progress in Redis"""
        key = f"generation:{progress.generation_id}:progress"

        progress_data = {
            'generation_id': progress.generation_id,
            'status': progress.status.value,
            'progress_percentage': progress.progress_percentage,
            'current_step': progress.current_step,
            'total_clips': progress.total_clips,
            'completed_clips': progress.completed_clips,
            'failed_clips': progress.failed_clips,
            'current_clip_index': progress.current_clip_index,
            'started_at': progress.started_at.isoformat() if progress.started_at else None,
            'estimated_completion_at': progress.estimated_completion_at.isoformat() if progress.estimated_completion_at else None,
            'last_updated': progress.last_updated.isoformat(),
            'total_generation_time_seconds': progress.total_generation_time_seconds,
            'average_clip_time_seconds': progress.average_clip_time_seconds
        }

        # Store as JSON in Redis
        self.redis_client.set(key, json.dumps(progress_data))

        # Set expiration (24 hours)
        self.redis_client.expire(key, 86400)

    def _get_progress(self, generation_id: str) -> Optional[GenerationProgress]:
        """Get generation progress from Redis"""
        key = f"generation:{generation_id}:progress"
        progress_data = self.redis_client.get(key)

        if not progress_data:
            return None

        try:
            data = json.loads(progress_data)
            return GenerationProgress(**data)
        except Exception as e:
            logger.error(f"Failed to parse progress data for {generation_id}: {str(e)}")
            return None

    def _update_clip_ordering(self, generation_id: str, clips: List[DatabaseClipMetadata]):
        """Update clip ordering in Redis using sorted set"""
        key = f"generation:{generation_id}:clips"

        # Clear existing ordering
        self.redis_client.delete(key)

        # Add clips with sequence order as score
        for clip in clips:
            clip_data = {
                'clip_id': clip.clip_id,
                'scene_id': clip.scene_id,
                'status': clip.storage_status.value,
                'sequence_order': clip.sequence_order
            }
            self.redis_client.zadd(key, {clip.clip_id: clip.sequence_order})

            # Store clip details in a separate hash
            clip_detail_key = f"clip:{clip.clip_id}"
            self.redis_client.hset(clip_detail_key, mapping={
                'generation_id': generation_id,
                'scene_id': clip.scene_id,
                'sequence_order': clip.sequence_order,
                'status': clip.storage_status.value,
                'video_url': clip.video_url or '',
                'duration': clip.duration_seconds,
                'last_updated': clip.last_updated.isoformat()
            })

        # Set expiration
        self.redis_client.expire(key, 86400)

    def _retrieve_clips_from_db(self, request: ClipRetrievalRequest) -> List[DatabaseClipMetadata]:
        """Retrieve clips from database"""
        with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM clips
                WHERE generation_id = %s
                ORDER BY sequence_order
            """, (request.generation_id,))

            rows = cursor.fetchall()

        clips = []
        for row in rows:
            # Convert row to DatabaseClipMetadata
            # Handle enum conversions
            row_dict = dict(row)
            row_dict['resolution'] = row_dict['resolution'] or '720p'
            row_dict['format'] = row_dict['format'] or 'mp4'
            row_dict['storage_status'] = row_dict['storage_status'] or 'pending'

            clips.append(DatabaseClipMetadata(**row_dict))

        return clips

    def get_clip_ordering(self, generation_id: str) -> List[str]:
        """Get ordered list of clip IDs for a generation"""
        key = f"generation:{generation_id}:clips"
        return self.redis_client.zrange(key, 0, -1)

    def update_clip_status(self, clip_id: str, status: ClipStorageStatus, error_message: Optional[str] = None):
        """Update the status of a specific clip"""
        # Update in database
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                UPDATE clips
                SET storage_status = %s, error_message = %s, last_updated = NOW()
                WHERE clip_id = %s
            """, (status.value, error_message, clip_id))

        self.db_connection.commit()

        # Update in Redis
        clip_detail_key = f"clip:{clip_id}"
        self.redis_client.hset(clip_detail_key, mapping={
            'status': status.value,
            'last_updated': datetime.utcnow().isoformat()
        })

    def cleanup_generation(self, generation_id: str):
        """Clean up all data for a generation (for testing/completion)"""
        # Remove Redis keys
        progress_key = f"generation:{generation_id}:progress"
        clips_key = f"generation:{generation_id}:clips"

        self.redis_client.delete(progress_key, clips_key)

        # Get all clip IDs for this generation
        with self.db_connection.cursor() as cursor:
            cursor.execute("SELECT clip_id FROM clips WHERE generation_id = %s", (generation_id,))
            clip_ids = [row[0] for row in cursor.fetchall()]

        # Remove individual clip details
        for clip_id in clip_ids:
            self.redis_client.delete(f"clip:{clip_id}")

        # Note: Database records are kept for historical purposes

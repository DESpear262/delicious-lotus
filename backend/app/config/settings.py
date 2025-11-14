"""
AI Video Generation Pipeline - Configuration Management

This module provides centralized configuration management for the application,
loading settings from environment variables with validation and type conversion.

Usage:
    from app.config.settings import settings

    database_url = settings.DATABASE_URL
    debug_mode = settings.DEBUG
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, AnyHttpUrl


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic for validation and type conversion.
    See .env.example or deploy/env.*.template for all available variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ===================================
    # Environment Identification
    # ===================================
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="info", description="Logging level")
    LOG_FORMAT: str = Field(default="text", description="Log format: json or text")

    # ===================================
    # Database Configuration
    # ===================================
    POSTGRES_DB: str = Field(default="ai_video_pipeline", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="ai_video_user", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="dev_password_change_me", description="PostgreSQL password")
    POSTGRES_HOST: str = Field(default="postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")

    DATABASE_URL: str = Field(
        default="postgresql://ai_video_user:dev_password_change_me@postgres:5432/ai_video_pipeline",
        description="Full database connection string"
    )

    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Connection pool timeout (seconds)")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time (seconds)")
    DB_SSL_MODE: str = Field(default="disable", description="SSL mode for database")

    # ===================================
    # Redis Configuration
    # ===================================
    REDIS_HOST: str = Field(default="redis", description="Redis hostname")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_URL: str = Field(default="redis://redis:6379/0", description="Full Redis URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis max connections")

    # ===================================
    # Backend API Configuration
    # ===================================
    BACKEND_PORT: int = Field(default=8000, description="Backend API port")
    API_BASE_URL: str = Field(default="http://localhost:8000", description="API base URL")

    SECRET_KEY: str = Field(
        default="dev_secret_key_change_me_in_production",
        description="Application secret key"
    )
    JWT_SECRET_KEY: str = Field(
        default="dev_jwt_secret_key_change_me",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="JWT access token expiry")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="JWT refresh token expiry")

    # ===================================
    # CORS Configuration
    # ===================================
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://localhost:8000",
        description="Comma-separated CORS allowed origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS allow credentials")
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,DELETE,PATCH,OPTIONS",
        description="CORS allowed methods"
    )
    CORS_ALLOW_HEADERS: str = Field(default="*", description="CORS allowed headers")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def cors_methods_list(self) -> List[str]:
        """Parse CORS_ALLOW_METHODS into a list."""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    # ===================================
    # AI Services (Replicate)
    # ===================================
    REPLICATE_API_TOKEN: str = Field(
        default="your_replicate_token_here",
        description="Replicate API token"
    )
    REPLICATE_USE_CHEAP_MODELS: bool = Field(default=True, description="Use cheaper models")
    REPLICATE_MODEL_QUALITY_TIER: str = Field(default="standard", description="Model quality tier")
    REPLICATE_IMAGE_MODEL: str = Field(
        default="stability-ai/sdxl:latest",
        description="Image generation model"
    )
    REPLICATE_VIDEO_MODEL: str = Field(
        default="deforum/deforum_stable_diffusion:latest",
        description="Video generation model"
    )
    REPLICATE_TIMEOUT_SECONDS: int = Field(default=300, description="Replicate API timeout")
    REPLICATE_MAX_RETRIES: int = Field(default=3, description="Max retry attempts")
    REPLICATE_RETRY_DELAY_SECONDS: int = Field(default=5, description="Retry delay")

    # ===================================
    # AWS Configuration
    # ===================================
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret key")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_DEFAULT_REGION: str = Field(default="us-east-1", description="AWS default region")

    S3_BUCKET: str = Field(default="ai-video-dev-bucket", description="S3 bucket name")
    S3_UPLOADS_PREFIX: str = Field(default="uploads/", description="S3 uploads prefix")
    S3_GENERATIONS_PREFIX: str = Field(default="generations/", description="S3 generations prefix")
    S3_COMPOSITIONS_PREFIX: str = Field(default="compositions/", description="S3 compositions prefix")
    S3_TEMP_PREFIX: str = Field(default="temp/", description="S3 temp prefix")
    S3_PRESIGNED_URL_EXPIRY: int = Field(default=3600, description="Presigned URL expiry (seconds)")

    ECR_REPOSITORY: Optional[str] = Field(default=None, description="ECR repository URL")
    ECS_CLUSTER: Optional[str] = Field(default=None, description="ECS cluster name")
    ECS_SERVICE: Optional[str] = Field(default=None, description="ECS service name")
    ECS_TASK_DEFINITION: Optional[str] = Field(default=None, description="ECS task definition")

    # ===================================
    # Storage Configuration
    # ===================================
    USE_LOCAL_STORAGE: bool = Field(default=True, description="Use local storage instead of S3")
    LOCAL_STORAGE_PATH: str = Field(default="/app/storage", description="Local storage path")
    STORAGE_CLEANUP_ENABLED: bool = Field(default=True, description="Enable storage cleanup")
    STORAGE_CLEANUP_TEMP_FILES_DAYS: int = Field(default=1, description="Temp file cleanup days")
    STORAGE_CLEANUP_GENERATIONS_DAYS: int = Field(default=7, description="Generations cleanup days")

    # ===================================
    # Video Processing (FFmpeg)
    # ===================================
    FFMPEG_PATH: str = Field(default="/usr/bin/ffmpeg", description="FFmpeg binary path")
    FFPROBE_PATH: str = Field(default="/usr/bin/ffprobe", description="FFprobe binary path")
    FFMPEG_THREADS: int = Field(default=4, description="FFmpeg processing threads")
    FFMPEG_PRESET: str = Field(default="medium", description="FFmpeg encoding preset")
    FFMPEG_LOG_LEVEL: str = Field(default="info", description="FFmpeg log level")

    OUTPUT_VIDEO_QUALITY: str = Field(default="720p", description="Output video quality")
    OUTPUT_VIDEO_WIDTH: int = Field(default=1280, description="Output video width")
    OUTPUT_VIDEO_HEIGHT: int = Field(default=720, description="Output video height")
    OUTPUT_VIDEO_CODEC: str = Field(default="libx264", description="Output video codec")
    OUTPUT_VIDEO_BITRATE: str = Field(default="2M", description="Output video bitrate")
    OUTPUT_AUDIO_CODEC: str = Field(default="aac", description="Output audio codec")
    OUTPUT_AUDIO_BITRATE: str = Field(default="128k", description="Output audio bitrate")
    OUTPUT_AUDIO_SAMPLE_RATE: int = Field(default=48000, description="Audio sample rate")

    MIN_VIDEO_DURATION: int = Field(default=15, description="Minimum video duration (seconds)")
    MAX_VIDEO_DURATION: int = Field(default=180, description="Maximum video duration (seconds)")
    MAX_AD_DURATION: int = Field(default=60, description="Maximum ad duration (seconds)")
    MAX_MUSIC_VIDEO_DURATION: int = Field(default=180, description="Max music video duration")

    SUPPORTED_ASPECT_RATIOS: str = Field(default="16:9,9:16,1:1", description="Supported aspect ratios")

    @property
    def aspect_ratios_list(self) -> List[str]:
        """Parse SUPPORTED_ASPECT_RATIOS into a list."""
        return [ratio.strip() for ratio in self.SUPPORTED_ASPECT_RATIOS.split(",")]

    # ===================================
    # Job Processing (Celery)
    # ===================================
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/0", description="Celery result backend")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False, description="Run tasks synchronously")
    CELERY_TASK_TRACK_STARTED: bool = Field(default=True, description="Track task start time")
    CELERY_TASK_TIME_LIMIT: int = Field(default=1800, description="Task hard time limit (seconds)")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=1500, description="Task soft time limit")

    CELERY_WORKER_CONCURRENCY: int = Field(default=4, description="Celery worker concurrency")
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(default=1, description="Prefetch multiplier")
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=100, description="Max tasks per child")

    MAX_CONCURRENT_JOBS: int = Field(default=5, description="Max concurrent video jobs")
    JOB_TIMEOUT_SECONDS: int = Field(default=1200, description="Job timeout (seconds)")
    JOB_RETRY_MAX_ATTEMPTS: int = Field(default=3, description="Max job retry attempts")
    JOB_RETRY_DELAY_SECONDS: int = Field(default=10, description="Job retry delay")

    CLEANUP_COMPLETED_JOBS_AFTER_DAYS: int = Field(default=7, description="Cleanup completed jobs")
    CLEANUP_FAILED_JOBS_AFTER_DAYS: int = Field(default=3, description="Cleanup failed jobs")

    # ===================================
    # Performance & Caching
    # ===================================
    ENABLE_CACHING: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL (seconds)")
    CACHE_AI_RESPONSES: bool = Field(default=True, description="Cache AI responses")
    CACHE_ASSET_METADATA: bool = Field(default=True, description="Cache asset metadata")

    REUSE_SIMILAR_PROMPTS: bool = Field(default=True, description="Reuse similar prompts")
    PROMPT_SIMILARITY_THRESHOLD: float = Field(default=0.85, description="Prompt similarity threshold")

    # ===================================
    # Rate Limiting
    # ===================================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Requests per minute")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Requests per hour")
    RATE_LIMIT_PER_DAY: int = Field(default=10000, description="Requests per day")
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst allowance")

    # ===================================
    # Security Settings
    # ===================================
    MAX_UPLOAD_SIZE_MB: int = Field(default=100, description="Max upload size (MB)")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=104857600, description="Max upload size (bytes)")

    ALLOWED_IMAGE_EXTENSIONS: str = Field(
        default=".jpg,.jpeg,.png,.gif,.webp",
        description="Allowed image extensions"
    )
    ALLOWED_AUDIO_EXTENSIONS: str = Field(
        default=".mp3,.wav,.m4a,.aac",
        description="Allowed audio extensions"
    )
    ALLOWED_VIDEO_EXTENSIONS: str = Field(
        default=".mp4,.mov,.avi,.webm",
        description="Allowed video extensions"
    )
    ALLOWED_UPLOAD_EXTENSIONS: str = Field(
        default=".mp3,.wav,.m4a,.jpg,.jpeg,.png,.gif,.webp",
        description="All allowed upload extensions"
    )

    MAX_PROMPT_LENGTH: int = Field(default=2000, description="Max prompt length")
    MIN_PROMPT_LENGTH: int = Field(default=10, description="Min prompt length")
    SANITIZE_USER_INPUT: bool = Field(default=True, description="Sanitize user input")

    SESSION_TIMEOUT_MINUTES: int = Field(default=60, description="Session timeout")
    SESSION_COOKIE_SECURE: bool = Field(default=False, description="Secure session cookies")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, description="HTTPOnly cookies")
    SESSION_COOKIE_SAMESITE: str = Field(default="lax", description="SameSite cookie policy")

    FORCE_HTTPS: bool = Field(default=False, description="Force HTTPS redirects")

    @property
    def allowed_image_extensions_list(self) -> List[str]:
        """Parse ALLOWED_IMAGE_EXTENSIONS into a list."""
        return [ext.strip() for ext in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def allowed_audio_extensions_list(self) -> List[str]:
        """Parse ALLOWED_AUDIO_EXTENSIONS into a list."""
        return [ext.strip() for ext in self.ALLOWED_AUDIO_EXTENSIONS.split(",")]

    @property
    def allowed_upload_extensions_list(self) -> List[str]:
        """Parse ALLOWED_UPLOAD_EXTENSIONS into a list."""
        return [ext.strip() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]

    # ===================================
    # Monitoring & Logging
    # ===================================
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN")
    SENTRY_ENVIRONMENT: str = Field(default="development", description="Sentry environment")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, description="Sentry trace sample rate")
    SENTRY_ENABLED: bool = Field(default=False, description="Enable Sentry")

    CLOUDWATCH_LOG_GROUP: str = Field(
        default="/aws/ecs/ai-video-dev",
        description="CloudWatch log group"
    )
    CLOUDWATCH_LOG_STREAM_PREFIX: str = Field(default="backend", description="Log stream prefix")
    CLOUDWATCH_ENABLED: bool = Field(default=False, description="Enable CloudWatch")

    HEALTH_CHECK_PATH: str = Field(default="/health", description="Health check endpoint")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, description="Health check timeout")

    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Metrics port")

    # ===================================
    # Feature Flags
    # ===================================
    ENABLE_AD_PIPELINE: bool = Field(default=True, description="Enable Ad Creative Pipeline")
    ENABLE_MUSIC_VIDEO_PIPELINE: bool = Field(default=False, description="Enable Music Video Pipeline")
    ENABLE_TIMELINE_EDITOR: bool = Field(default=False, description="Enable timeline editor")
    ENABLE_ADVANCED_TRANSITIONS: bool = Field(default=False, description="Enable advanced transitions")
    ENABLE_CUSTOM_FONTS: bool = Field(default=False, description="Enable custom fonts")
    ENABLE_BATCH_PROCESSING: bool = Field(default=False, description="Enable batch processing")
    ENABLE_TEMPLATE_MARKETPLACE: bool = Field(default=False, description="Enable template marketplace")

    ENABLE_EXPERIMENTAL_MODELS: bool = Field(default=True, description="Enable experimental models")
    ENABLE_BETA_FEATURES: bool = Field(default=True, description="Enable beta features")

    # ===================================
    # Frontend Configuration
    # ===================================
    FRONTEND_BUILD_PATH: str = Field(default="/app/frontend/dist", description="Frontend build path")
    SERVE_FRONTEND: bool = Field(default=True, description="Serve frontend from backend")
    FRONTEND_CDN_URL: Optional[str] = Field(default=None, description="Frontend CDN URL")
    STATIC_FILE_CACHE_MAX_AGE: int = Field(default=3600, description="Static file cache max age")

    # ===================================
    # Cost Optimization
    # ===================================
    USE_CHEAP_MODELS: bool = Field(default=True, description="Use cheap models")
    MODEL_QUALITY_TIER: str = Field(default="standard", description="Model quality tier")

    MAX_CLIPS_PER_AD: int = Field(default=5, description="Max clips per ad")
    MAX_CLIPS_PER_MUSIC_VIDEO: int = Field(default=20, description="Max clips per music video")
    DEFAULT_CLIPS_PER_AD: int = Field(default=3, description="Default clips per ad")
    DEFAULT_CLIPS_PER_MUSIC_VIDEO: int = Field(default=10, description="Default clips per music video")

    BATCH_API_CALLS: bool = Field(default=True, description="Batch API calls")
    MAX_BATCH_SIZE: int = Field(default=5, description="Max batch size")

    ENABLE_ASSET_REUSE: bool = Field(default=True, description="Enable asset reuse")
    ASSET_REUSE_SIMILARITY_THRESHOLD: float = Field(default=0.9, description="Asset reuse threshold")

    # ===================================
    # Development Tools
    # ===================================
    HOT_RELOAD: bool = Field(default=True, description="Enable hot reload")
    AUTO_RELOAD: bool = Field(default=True, description="Enable auto reload")

    ENABLE_DOCS: bool = Field(default=True, description="Enable API docs")
    DOCS_URL: str = Field(default="/docs", description="API docs URL")
    REDOC_URL: str = Field(default="/redoc", description="ReDoc URL")
    OPENAPI_URL: str = Field(default="/openapi.json", description="OpenAPI JSON URL")

    ENABLE_DEBUG_ENDPOINTS: bool = Field(default=True, description="Enable debug endpoints")
    ENABLE_TEST_ENDPOINTS: bool = Field(default=True, description="Enable test endpoints")

    AUTO_MIGRATE: bool = Field(default=True, description="Auto-run migrations")
    AUTO_CREATE_TABLES: bool = Field(default=True, description="Auto-create tables")

    # ===================================
    # Validators
    # ===================================

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.lower()

    @validator("LOG_FORMAT")
    def validate_log_format(cls, v):
        """Validate log format."""
        allowed = ["json", "text"]
        if v.lower() not in allowed:
            raise ValueError(f"LOG_FORMAT must be one of {allowed}")
        return v.lower()

    @validator("DEBUG")
    def validate_production_debug(cls, v, values):
        """Ensure DEBUG is false in production."""
        if values.get("ENVIRONMENT") == "production" and v is True:
            raise ValueError("DEBUG must be False in production environment")
        return v

    @validator("SESSION_COOKIE_SECURE")
    def validate_production_secure_cookies(cls, v, values):
        """Ensure secure cookies in production."""
        if values.get("ENVIRONMENT") == "production" and v is False:
            raise ValueError("SESSION_COOKIE_SECURE must be True in production")
        return v

    # ===================================
    # Helper Properties
    # ===================================

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.ENVIRONMENT == "staging"


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the application settings.

    This function can be used as a dependency in FastAPI:

    @app.get("/info")
    async def info(settings: Settings = Depends(get_settings)):
        return {"environment": settings.ENVIRONMENT}
    """
    return settings


# Environment-specific configuration helpers

def get_database_config() -> dict:
    """Get database configuration dictionary."""
    return {
        "url": settings.DATABASE_URL,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    }


def get_redis_config() -> dict:
    """Get Redis configuration dictionary."""
    return {
        "url": settings.REDIS_URL,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
    }


def get_cors_config() -> dict:
    """Get CORS configuration dictionary."""
    return {
        "allow_origins": settings.cors_origins_list,
        "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
        "allow_methods": settings.cors_methods_list,
        "allow_headers": settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS != "*" else ["*"],
    }


def get_celery_config() -> dict:
    """Get Celery configuration dictionary."""
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_always_eager": settings.CELERY_TASK_ALWAYS_EAGER,
        "task_track_started": settings.CELERY_TASK_TRACK_STARTED,
        "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
        "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT,
        "worker_concurrency": settings.CELERY_WORKER_CONCURRENCY,
        "worker_prefetch_multiplier": settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
        "worker_max_tasks_per_child": settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    }

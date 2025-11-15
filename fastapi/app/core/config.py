"""
Configuration settings for the AI Video Generation Pipeline
Block 0: API Skeleton & Core Infrastructure
"""

import os
from typing import Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        # Don't try to parse env vars as JSON
        env_parse_none_str=None,
    )

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    internal_v1_prefix: str = "/internal/v1"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Application Metadata
    title: str = "AI Video Generation Pipeline"
    description: str = "Backend API for AI-powered video generation and editing"
    version: str = "0.1.0"

    # CORS Configuration - accepts comma-separated string or list
    cors_origins: Union[str, list[str]] = "http://localhost:3000,http://localhost:5173"

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # Database Configuration (placeholders for future use)
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # External Service URLs (placeholders)
    replicate_api_token: Optional[str] = None
    openai_api_key: Optional[str] = None


# Global settings instance
settings = Settings()

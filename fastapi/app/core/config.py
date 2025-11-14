"""
Configuration settings for the AI Video Generation Pipeline
Block 0: API Skeleton & Core Infrastructure
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

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

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database Configuration (placeholders for future use)
    database_url: Optional[str] = None
    redis_url: Optional[str] = None

    # External Service URLs (placeholders)
    replicate_api_token: Optional[str] = None
    openai_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

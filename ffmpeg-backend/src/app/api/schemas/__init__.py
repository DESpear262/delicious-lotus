"""API schemas package."""

from .composition import (
    AudioConfig,
    ClipConfig,
    CompositionCreateRequest,
    CompositionMetadataResponse,
    CompositionResponse,
    CompositionStatusResponse,
    DownloadResponse,
    OutputSettings,
    OverlayConfig,
    ProcessingStageInfo,
    ResourceMetrics,
)
from .errors import ErrorDetail, ErrorResponse

__all__ = [
    # Composition schemas
    "ClipConfig",
    "AudioConfig",
    "OverlayConfig",
    "OutputSettings",
    "CompositionCreateRequest",
    "CompositionResponse",
    "CompositionStatusResponse",
    "CompositionMetadataResponse",
    "DownloadResponse",
    "ProcessingStageInfo",
    "ResourceMetrics",
    # Error schemas
    "ErrorResponse",
    "ErrorDetail",
]

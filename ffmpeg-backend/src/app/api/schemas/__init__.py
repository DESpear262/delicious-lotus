"""API schemas package."""

from .composition import (
    AudioConfig,
    ClipConfig,
    CompositionCreateRequest,
    CompositionMetadataResponse,
    CompositionResponse,
    CompositionStatusResponse,
    DownloadResponse,
    InputFileInfo,
    OutputFileInfo,
    OutputSettings,
    OverlayConfig,
    ProcessingStage,
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
    "ProcessingStage",
    "ProcessingStageInfo",
    "ResourceMetrics",
    "InputFileInfo",
    "OutputFileInfo",
    # Error schemas
    "ErrorResponse",
    "ErrorDetail",
]

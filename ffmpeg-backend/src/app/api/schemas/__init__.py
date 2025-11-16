"""API schemas package."""

from .composition import (
    AudioConfig,
    BulkCancelResponse,
    ClipConfig,
    CompositionCancelResponse,
    CompositionCreateRequest,
    CompositionListResponse,
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
from .job import JobCancelResponse, JobListResponse, JobResponse, JobStatus
from .replicate import (
    NanoBananaErrorResponse,
    NanoBananaRequest,
    NanoBananaResponse,
)
from .websocket import (
    ConnectionState,
    WSBaseMessage,
    WSClientMessage,
    WSConnectedMessage,
    WSErrorMessage,
    WSHeartbeatMessage,
    WSMessageType,
    WSPongMessage,
    WSProgressMessage,
    WSStatusMessage,
)

__all__ = [
    # Composition schemas
    "ClipConfig",
    "AudioConfig",
    "OverlayConfig",
    "OutputSettings",
    "CompositionCreateRequest",
    "CompositionResponse",
    "CompositionListResponse",
    "CompositionStatusResponse",
    "CompositionMetadataResponse",
    "CompositionCancelResponse",
    "BulkCancelResponse",
    "DownloadResponse",
    "ProcessingStage",
    "ProcessingStageInfo",
    "ResourceMetrics",
    "InputFileInfo",
    "OutputFileInfo",
    # Error schemas
    "ErrorResponse",
    "ErrorDetail",
    # Job schemas
    "JobStatus",
    "JobResponse",
    "JobListResponse",
    "JobCancelResponse",
    # Replicate schemas
    "NanoBananaRequest",
    "NanoBananaResponse",
    "NanoBananaErrorResponse",
    # WebSocket schemas
    "WSMessageType",
    "WSBaseMessage",
    "WSProgressMessage",
    "WSStatusMessage",
    "WSErrorMessage",
    "WSHeartbeatMessage",
    "WSPongMessage",
    "WSConnectedMessage",
    "ConnectionState",
    "WSClientMessage",
]

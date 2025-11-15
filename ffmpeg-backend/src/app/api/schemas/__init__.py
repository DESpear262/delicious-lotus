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

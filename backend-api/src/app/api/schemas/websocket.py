"""Pydantic schemas for WebSocket message protocol."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .composition import ProcessingStage


class WSMessageType(str, Enum):
    """WebSocket message types."""

    PROGRESS = "progress"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    PONG = "pong"
    CONNECTED = "connected"


class WSBaseMessage(BaseModel):
    """Base WebSocket message structure."""

    type: WSMessageType = Field(..., description="Message type identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the message was created"
    )
    composition_id: UUID = Field(..., description="Composition identifier this message relates to")


class WSProgressMessage(WSBaseMessage):
    """Progress update message for composition processing."""

    type: WSMessageType = Field(default=WSMessageType.PROGRESS, description="Message type")
    stage: ProcessingStage = Field(..., description="Current processing stage")
    percentage: float = Field(
        ..., ge=0, le=100, description="Progress percentage for current stage"
    )
    message: str | None = Field(None, description="Human-readable progress message")
    overall_progress: float | None = Field(
        None, ge=0, le=100, description="Overall composition progress percentage"
    )
    estimated_time_remaining: int | None = Field(
        None, ge=0, description="Estimated seconds remaining until completion"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "progress",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "stage": "encoding",
                "percentage": 65.5,
                "message": "Encoding video with H.264 codec",
                "overall_progress": 85.0,
                "estimated_time_remaining": 45,
            }
        }


class WSStatusMessage(WSBaseMessage):
    """Status update message for composition state changes."""

    type: WSMessageType = Field(default=WSMessageType.STATUS, description="Message type")
    status: str = Field(..., description="Current composition status")
    stage: ProcessingStage = Field(..., description="Current processing stage")
    message: str | None = Field(None, description="Status message details")
    metadata: dict[str, Any] | None = Field(None, description="Additional status metadata")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "status",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "stage": "downloading",
                "message": "Started downloading video clips",
                "metadata": {"clips_count": 5, "total_size_mb": 250},
            }
        }


class WSErrorMessage(WSBaseMessage):
    """Error message for composition processing failures."""

    type: WSMessageType = Field(default=WSMessageType.ERROR, description="Message type")
    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error message")
    stage: ProcessingStage | None = Field(None, description="Stage where error occurred")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    is_recoverable: bool = Field(default=False, description="Whether error is recoverable")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "error",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "error_code": "DOWNLOAD_FAILED",
                "error_message": "Failed to download video from URL",
                "stage": "downloading",
                "details": {"url": "https://example.com/video.mp4", "status_code": 404},
                "is_recoverable": True,
            }
        }


class WSHeartbeatMessage(WSBaseMessage):
    """Heartbeat/ping message to detect stale connections."""

    type: WSMessageType = Field(default=WSMessageType.HEARTBEAT, description="Message type")
    sequence: int = Field(..., ge=0, description="Heartbeat sequence number")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "heartbeat",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "sequence": 42,
            }
        }


class WSPongMessage(WSBaseMessage):
    """Pong response message to heartbeat."""

    type: WSMessageType = Field(default=WSMessageType.PONG, description="Message type")
    sequence: int = Field(..., ge=0, description="Heartbeat sequence number being acknowledged")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "pong",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "sequence": 42,
            }
        }


class WSConnectedMessage(WSBaseMessage):
    """Connection established message sent when client connects."""

    type: WSMessageType = Field(default=WSMessageType.CONNECTED, description="Message type")
    status: str = Field(..., description="Current composition status")
    stage: ProcessingStage = Field(..., description="Current processing stage")
    overall_progress: float = Field(..., ge=0, le=100, description="Current overall progress")
    message: str = Field(..., description="Welcome message")
    reconnection_token: str | None = Field(None, description="Token for reconnection recovery")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "connected",
                "timestamp": "2024-01-15T10:30:45.123Z",
                "composition_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "stage": "encoding",
                "overall_progress": 75.5,
                "message": "Connected to composition updates",
                "reconnection_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class ConnectionState(str, Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    SUBSCRIBED = "subscribed"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WSClientMessage(BaseModel):
    """Messages that can be sent from client to server."""

    type: str = Field(..., description="Message type from client")
    data: dict[str, Any] | None = Field(None, description="Message payload")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "type": "pong",
                "data": {"sequence": 42},
            }
        }

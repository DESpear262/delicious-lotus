"""WebSocket endpoints for real-time composition updates."""

import logging
from typing import Annotated
from uuid import UUID

from db.models import Composition
from db.session import get_db
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from services.websocket import (
    ConnectionInfo,
    ConnectionManager,
    HeartbeatManager,
    ReconnectionManager,
    RedisSubscriber,
)
from sqlalchemy.orm import Session
from workers.redis_pool import get_redis_connection

from app.api.schemas.websocket import (
    ConnectionState,
    ProcessingStage,
    WSConnectedMessage,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Global instances (initialized on startup)
connection_manager = ConnectionManager()
redis_subscriber: RedisSubscriber | None = None
heartbeat_manager: HeartbeatManager | None = None
reconnection_manager: ReconnectionManager | None = None


async def get_redis_subscriber() -> RedisSubscriber:
    """Get or create Redis subscriber instance."""
    global redis_subscriber
    if redis_subscriber is None:
        reconnect_mgr = get_reconnection_manager()
        redis_subscriber = RedisSubscriber(connection_manager, reconnect_mgr)
        await redis_subscriber.connect()
        await redis_subscriber.start_listening()
    return redis_subscriber


async def get_heartbeat_manager() -> HeartbeatManager:
    """Get or create heartbeat manager instance."""
    global heartbeat_manager
    if heartbeat_manager is None:
        heartbeat_manager = HeartbeatManager(
            connection_manager, ping_interval=30, max_missed_heartbeats=3
        )
        await heartbeat_manager.start()
    return heartbeat_manager


def get_reconnection_manager() -> ReconnectionManager:
    """Get or create reconnection manager instance."""
    global reconnection_manager
    if reconnection_manager is None:
        redis_client = get_redis_connection()
        reconnection_manager = ReconnectionManager(
            redis_client, message_ttl=300, max_stored_messages=100
        )
    return reconnection_manager


async def verify_composition_access(
    composition_id: UUID, user_id: str | None, db: Session
) -> Composition:
    """
    Verify that a composition exists and user has access to it.

    Args:
        composition_id: Composition UUID
        user_id: User identifier (from token)
        db: Database session

    Returns:
        Composition object if access is granted

    Raises:
        WebSocketException: If composition not found or access denied
    """
    composition = db.query(Composition).filter(Composition.id == composition_id).first()

    if not composition:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Composition {composition_id} not found",
        )

    # TODO: Add user ownership/access check when authentication is implemented
    # For now, allow all access
    # if composition.user_id != user_id:
    #     raise WebSocketException(
    #         code=status.WS_1008_POLICY_VIOLATION,
    #         reason="Access denied to this composition",
    #     )

    return composition


async def authenticate_websocket(token: str | None) -> str | None:
    """
    Authenticate WebSocket connection using JWT token.

    Args:
        token: JWT token from query params or headers

    Returns:
        User ID if authentication successful, None otherwise

    Raises:
        WebSocketException: If authentication fails
    """
    # TODO: Implement JWT validation when authentication is added
    # For now, allow connections without authentication
    # This is a placeholder that should be replaced with actual JWT validation

    if not token:
        logger.warning("WebSocket connection attempted without token")
        # For development, allow connections without token
        return None

    # Placeholder for JWT validation
    # try:
    #     payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    #     user_id = payload.get("sub")
    #     if not user_id:
    #         raise WebSocketException(
    #             code=status.WS_1008_POLICY_VIOLATION,
    #             reason="Invalid token: missing user ID",
    #         )
    #     return user_id
    # except jwt.ExpiredSignatureError:
    #     raise WebSocketException(
    #         code=status.WS_1008_POLICY_VIOLATION,
    #         reason="Token expired",
    #     )
    # except jwt.InvalidTokenError:
    #     raise WebSocketException(
    #         code=status.WS_1008_POLICY_VIOLATION,
    #         reason="Invalid token",
    #     )

    return token  # Return token as user_id placeholder


@router.websocket("/ws/compositions/{composition_id}")
async def websocket_composition_updates(
    websocket: WebSocket,
    composition_id: UUID,
    token: Annotated[str | None, Query()] = None,
    reconnection_token: Annotated[str | None, Query()] = None,
    last_sequence: Annotated[int, Query()] = 0,
) -> None:
    """
    WebSocket endpoint for real-time composition progress updates.

    Clients connect to this endpoint to receive real-time updates about
    composition processing progress, status changes, and errors.

    Args:
        websocket: WebSocket connection
        composition_id: UUID of the composition to monitor
        token: Optional JWT authentication token
        reconnection_token: Optional reconnection token for message recovery
        last_sequence: Last message sequence number received (for reconnection)

    Example:
        ws://localhost:8000/api/v1/ws/compositions/{composition_id}?token={jwt_token}
        ws://localhost:8000/api/v1/ws/compositions/{composition_id}?reconnection_token={token}&last_sequence=42
    """
    conn_info: ConnectionInfo | None = None
    subscriber: RedisSubscriber | None = None
    reconnect_mgr = get_reconnection_manager()
    is_reconnection = False

    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for composition {composition_id}")

        # Get database session
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Handle reconnection token validation
            if reconnection_token:
                validated_comp_id, validated_user_id = reconnect_mgr.validate_reconnection_token(
                    reconnection_token
                )
                if validated_comp_id == composition_id:
                    user_id = validated_user_id
                    is_reconnection = True
                    logger.info(
                        f"Validated reconnection token for composition {composition_id}, "
                        f"user {user_id}"
                    )
                else:
                    logger.warning(f"Invalid reconnection token for composition {composition_id}")
                    user_id = await authenticate_websocket(token)
            else:
                # Authenticate user normally
                user_id = await authenticate_websocket(token)

            # Update connection state to authenticating
            conn_info = await connection_manager.add_connection(
                websocket=websocket,
                composition_id=composition_id,
                user_id=user_id,
                state=ConnectionState.AUTHENTICATING,
            )

            # Verify composition exists and user has access
            composition = await verify_composition_access(composition_id, user_id, db)

            # Update connection state to authenticated
            await connection_manager.update_connection_state(
                websocket, composition_id, ConnectionState.AUTHENTICATED
            )

            logger.info(f"WebSocket authenticated for composition {composition_id}, user {user_id}")

            # Subscribe to Redis channel for this composition
            subscriber = await get_redis_subscriber()
            await subscriber.subscribe_to_composition(composition_id)

            # Update connection state to subscribed
            await connection_manager.update_connection_state(
                websocket, composition_id, ConnectionState.SUBSCRIBED
            )

            # Generate new reconnection token for this connection
            new_reconnection_token = reconnect_mgr.generate_reconnection_token(
                composition_id, user_id
            )

            # Send initial connected message with current status
            current_stage = ProcessingStage(composition.status)
            connected_msg = WSConnectedMessage(
                composition_id=composition_id,
                status=composition.status,
                stage=current_stage,
                overall_progress=0.0,  # TODO: Calculate from composition metadata
                message=f"Connected to updates for composition {composition_id}",
                reconnection_token=new_reconnection_token,
            )

            await websocket.send_json(connected_msg.model_dump(mode="json"))

            logger.info(f"Sent connected message for composition {composition_id}")

            # If reconnecting, send missed messages
            if is_reconnection and last_sequence > 0:
                missed_messages = reconnect_mgr.get_missed_messages(composition_id, last_sequence)

                if missed_messages:
                    logger.info(
                        f"Sending {len(missed_messages)} missed messages to "
                        f"composition {composition_id} (after sequence {last_sequence})"
                    )

                    for msg_entry in missed_messages:
                        try:
                            await websocket.send_json(msg_entry["message"])
                        except Exception as e:
                            logger.error(f"Failed to send missed message: {e}")
                            break
                else:
                    logger.info(
                        f"No missed messages for composition {composition_id} "
                        f"(last_sequence: {last_sequence})"
                    )

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Receive messages from client (e.g., pong responses)
                    data = await websocket.receive_json()

                    # Handle client messages
                    if data.get("type") == "pong":
                        # Update heartbeat
                        sequence = data.get("data", {}).get("sequence", 0)
                        await connection_manager.update_heartbeat(
                            websocket, composition_id, sequence
                        )
                        logger.debug(f"Received pong {sequence} from composition {composition_id}")

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for composition {composition_id}")
                    break
                except Exception as e:
                    logger.error(
                        f"Error receiving WebSocket message for composition {composition_id}: {e}"
                    )
                    break

        finally:
            # Clean up database session
            try:
                db.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")

    except WebSocketException as e:
        logger.warning(
            f"WebSocket authentication failed for composition {composition_id}: {e.reason}"
        )
        try:
            await websocket.close(code=e.code, reason=e.reason)
        except Exception:
            pass

    except HTTPException as e:
        logger.warning(
            f"HTTP exception during WebSocket setup for composition {composition_id}: {e.detail}"
        )
        try:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e.detail))
        except Exception:
            pass

    except Exception as e:
        logger.exception(
            f"Unexpected error in WebSocket connection for composition {composition_id}: {e}"
        )
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Internal server error",
            )
        except Exception:
            pass

    finally:
        # Clean up connection
        if conn_info:
            try:
                # Unsubscribe from Redis if no more connections for this composition
                connection_count = await connection_manager.get_connection_count(composition_id)
                if connection_count <= 1 and subscriber:  # This is the last connection
                    await subscriber.unsubscribe_from_composition(composition_id)
                    logger.info(f"Unsubscribed from Redis channel for composition {composition_id}")

                # Remove connection from manager
                await connection_manager.remove_connection(websocket, composition_id)
                logger.info(
                    f"Removed WebSocket connection for composition {composition_id}, "
                    f"user {conn_info.user_id}"
                )

            except Exception as e:
                logger.error(f"Error during WebSocket cleanup: {e}")


@router.get("/ws/stats")
async def get_websocket_stats() -> dict:
    """
    Get statistics about active WebSocket connections.

    Returns:
        Dictionary with connection statistics
    """
    stats = await connection_manager.get_stats()
    subscriber = await get_redis_subscriber()
    heartbeat = await get_heartbeat_manager()

    return {
        **stats,
        "redis_subscriptions": await subscriber.get_subscription_count(),
        "redis_connected": subscriber.is_connected,
        "redis_listening": subscriber.is_running,
        "heartbeat": await heartbeat.get_stats(),
    }

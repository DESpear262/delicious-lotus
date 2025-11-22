"""Redis pub/sub subscriber for real-time composition updates."""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

import redis.asyncio as aioredis
from app.api.schemas.websocket import (
    ProcessingStage,
    WSErrorMessage,
    WSProgressMessage,
    WSStatusMessage,
)
from app.config import settings
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from .connection_manager import ConnectionManager

if TYPE_CHECKING:
    from .reconnection_manager import ReconnectionManager

logger = logging.getLogger(__name__)


class RedisSubscriber:
    """
    Async Redis pub/sub subscriber for composition progress updates.

    Subscribes to composition-specific channels and routes messages to WebSocket connections.
    Handles automatic reconnection and subscription management.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        reconnection_manager: "ReconnectionManager | None" = None,
    ) -> None:
        """
        Initialize Redis subscriber.

        Args:
            connection_manager: WebSocket connection manager instance
            reconnection_manager: Optional reconnection manager for message storage
        """
        self.connection_manager = connection_manager
        self.reconnection_manager = reconnection_manager
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._subscribed_channels: set[str] = set()
        self._running = False
        self._listener_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._max_reconnect_delay = 60  # Maximum delay between reconnection attempts
        self._message_sequence: dict[UUID, int] = {}  # Track message sequences per composition
        logger.info("RedisSubscriber initialized")

    async def connect(self) -> None:
        """
        Connect to Redis and create pub/sub instance.

        Raises:
            RedisConnectionError: If unable to connect to Redis
        """
        try:
            # Create async Redis connection
            self._redis = await aioredis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
            )

            # Test connection
            await self._redis.ping()

            # Create pub/sub instance
            self._pubsub = self._redis.pubsub()

            logger.info("Connected to Redis for pub/sub")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RedisConnectionError(f"Failed to connect to Redis: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Redis and cleanup resources."""
        logger.info("Disconnecting from Redis pub/sub")

        # Stop listener task
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        # Stop reconnect task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # Unsubscribe from all channels
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing pub/sub: {e}")

        # Close Redis connection
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

        self._subscribed_channels.clear()
        logger.info("Disconnected from Redis pub/sub")

    async def subscribe_to_composition(self, composition_id: UUID) -> bool:
        """
        Subscribe to a composition's progress channel.

        Args:
            composition_id: Composition UUID

        Returns:
            True if subscription successful, False otherwise
        """
        channel = f"composition:{composition_id}:progress"

        if channel in self._subscribed_channels:
            logger.debug(f"Already subscribed to {channel}")
            return True

        try:
            if not self._pubsub:
                await self.connect()

            await self._pubsub.subscribe(channel)  # type: ignore
            self._subscribed_channels.add(channel)
            logger.info(f"Subscribed to Redis channel: {channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to {channel}: {e}")
            return False

    async def unsubscribe_from_composition(self, composition_id: UUID) -> bool:
        """
        Unsubscribe from a composition's progress channel.

        Args:
            composition_id: Composition UUID

        Returns:
            True if unsubscription successful, False otherwise
        """
        channel = f"composition:{composition_id}:progress"

        if channel not in self._subscribed_channels:
            logger.debug(f"Not subscribed to {channel}")
            return True

        try:
            if self._pubsub:
                await self._pubsub.unsubscribe(channel)
                self._subscribed_channels.discard(channel)
                logger.info(f"Unsubscribed from Redis channel: {channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {channel}: {e}")
            return False

    async def start_listening(self) -> None:
        """
        Start listening for Redis pub/sub messages.

        Creates a background task to continuously listen for messages.
        """
        if self._running:
            logger.warning("Listener already running")
            return

        if not self._pubsub:
            await self.connect()

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Started Redis pub/sub listener")

    async def stop_listening(self) -> None:
        """Stop listening for Redis pub/sub messages."""
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                logger.info("Listener task cancelled")

    async def _listen_loop(self) -> None:
        """
        Main loop for listening to Redis pub/sub messages.

        Continuously processes messages and routes them to WebSocket connections.
        """
        logger.info("Starting pub/sub listen loop")

        while self._running:
            try:
                if not self._pubsub:
                    logger.warning("Pub/sub not initialized, reconnecting...")
                    await self._reconnect()
                    continue

                # Listen for messages
                async for message in self._pubsub.listen():  # type: ignore
                    if not self._running:
                        break

                    if message["type"] == "message":
                        await self._handle_message(message)

            except asyncio.CancelledError:
                logger.info("Listen loop cancelled")
                break

            except (RedisConnectionError, RedisError) as e:
                logger.error(f"Redis error in listen loop: {e}")
                if self._running:
                    await self._reconnect()

            except Exception as e:
                logger.exception(f"Unexpected error in listen loop: {e}")
                if self._running:
                    await asyncio.sleep(5)  # Brief pause before continuing

        logger.info("Pub/sub listen loop stopped")

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """
        Handle a Redis pub/sub message and route to WebSocket connections.

        Args:
            message: Redis message dictionary
        """
        try:
            channel = message.get("channel", "")
            data = message.get("data", "")

            # Parse channel to extract composition_id
            # Channel format: "composition:{uuid}:progress"
            if not channel.startswith("composition:") or not channel.endswith(":progress"):
                logger.warning(f"Unexpected channel format: {channel}")
                return

            composition_id_str = channel.split(":")[1]
            composition_id = UUID(composition_id_str)

            # Parse message data
            message_data = json.loads(data) if isinstance(data, str) else data

            # Create appropriate WebSocket message based on message type
            ws_message = self._create_ws_message(composition_id, message_data)

            if ws_message:
                # Get next sequence number for this composition
                if composition_id not in self._message_sequence:
                    self._message_sequence[composition_id] = 0
                self._message_sequence[composition_id] += 1
                sequence = self._message_sequence[composition_id]

                # Store message for reconnection if manager available
                if self.reconnection_manager:
                    self.reconnection_manager.store_message(composition_id, ws_message, sequence)

                # Broadcast to all WebSocket connections for this composition
                sent_count = await self.connection_manager.broadcast_to_composition(
                    composition_id, ws_message
                )
                logger.debug(
                    f"Routed message {sequence} to {sent_count} WebSocket connections "
                    f"for composition {composition_id}"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message data as JSON: {e}")
        except ValueError as e:
            logger.error(f"Invalid composition UUID in channel: {e}")
        except Exception as e:
            logger.exception(f"Error handling message: {e}")

    def _create_ws_message(
        self, composition_id: UUID, message_data: dict[str, Any]
    ) -> WSProgressMessage | WSStatusMessage | WSErrorMessage | None:
        """
        Create appropriate WebSocket message from Redis message data.

        Args:
            composition_id: Composition UUID
            message_data: Message payload from Redis

        Returns:
            WebSocket message object or None if unable to create
        """
        try:
            msg_type = message_data.get("type", "")

            if msg_type == "progress":
                return WSProgressMessage(
                    composition_id=composition_id,
                    stage=ProcessingStage(message_data.get("stage", "pending")),
                    percentage=float(message_data.get("percentage", 0)),
                    message=message_data.get("message"),
                    overall_progress=message_data.get("overall_progress"),
                    estimated_time_remaining=message_data.get("estimated_time_remaining"),
                )

            elif msg_type == "status":
                return WSStatusMessage(
                    composition_id=composition_id,
                    status=message_data.get("status", "unknown"),
                    stage=ProcessingStage(message_data.get("stage", "pending")),
                    message=message_data.get("message"),
                    metadata=message_data.get("metadata"),
                )

            elif msg_type == "error":
                return WSErrorMessage(
                    composition_id=composition_id,
                    error_code=message_data.get("error_code", "UNKNOWN_ERROR"),
                    error_message=message_data.get("error_message", "An error occurred"),
                    stage=(
                        ProcessingStage(message_data.get("stage"))
                        if message_data.get("stage")
                        else None
                    ),
                    details=message_data.get("details"),
                    is_recoverable=message_data.get("is_recoverable", False),
                )

            else:
                logger.warning(f"Unknown message type: {msg_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating WebSocket message: {e}")
            return None

    async def _reconnect(self) -> None:
        """
        Reconnect to Redis with exponential backoff.

        Attempts to reconnect and re-subscribe to all channels.
        """
        delay = 1
        max_delay = self._max_reconnect_delay

        while self._running:
            try:
                logger.info(f"Attempting Redis reconnection (delay: {delay}s)")

                # Close existing connections
                if self._pubsub:
                    try:
                        await self._pubsub.close()
                    except Exception:
                        pass

                if self._redis:
                    try:
                        await self._redis.close()
                    except Exception:
                        pass

                # Reconnect
                await self.connect()

                # Re-subscribe to all channels
                if self._subscribed_channels:
                    channels_to_resubscribe = self._subscribed_channels.copy()
                    self._subscribed_channels.clear()

                    for channel in channels_to_resubscribe:
                        # Extract composition_id from channel
                        composition_id_str = channel.split(":")[1]
                        composition_id = UUID(composition_id_str)
                        await self.subscribe_to_composition(composition_id)

                logger.info("Redis reconnection successful")
                return

            except Exception as e:
                logger.error(f"Reconnection attempt failed: {e}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, max_delay)  # Exponential backoff

        logger.warning("Reconnection loop stopped")

    async def get_subscription_count(self) -> int:
        """
        Get the number of subscribed channels.

        Returns:
            Number of active channel subscriptions
        """
        return len(self._subscribed_channels)

    async def get_subscribed_compositions(self) -> set[UUID]:
        """
        Get all composition IDs currently subscribed to.

        Returns:
            Set of composition UUIDs
        """
        compositions = set()
        for channel in self._subscribed_channels:
            try:
                composition_id_str = channel.split(":")[1]
                compositions.add(UUID(composition_id_str))
            except (IndexError, ValueError) as e:
                logger.warning(f"Invalid channel format: {channel}, error: {e}")

        return compositions

    @property
    def is_running(self) -> bool:
        """Check if listener is currently running."""
        return self._running

    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._redis is not None and self._pubsub is not None

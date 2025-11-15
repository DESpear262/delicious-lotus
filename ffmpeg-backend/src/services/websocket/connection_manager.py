"""WebSocket connection manager for handling multiple concurrent connections."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.websocket import ConnectionState, WSBaseMessage
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    websocket: WebSocket
    composition_id: UUID
    user_id: str | None
    state: ConnectionState
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    heartbeat_sequence: int = 0
    missed_heartbeats: int = 0
    reconnection_token: str | None = None

    def __hash__(self) -> int:
        """Make ConnectionInfo hashable by using websocket id."""
        return id(self.websocket)

    def __eq__(self, other: object) -> bool:
        """Compare ConnectionInfo by websocket instance."""
        if not isinstance(other, ConnectionInfo):
            return NotImplemented
        return self.websocket is other.websocket


class ConnectionManager:
    """
    Manages WebSocket connections for composition updates.

    Supports multiple concurrent connections per composition with thread-safe operations.
    Tracks connection state and handles lifecycle management.
    """

    _instance: "ConnectionManager | None" = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls) -> "ConnectionManager":
        """Implement singleton pattern for connection manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # Only initialize once
        if not hasattr(self, "_initialized"):
            # Dict mapping composition_id -> set of ConnectionInfo
            self._connections: dict[UUID, set[ConnectionInfo]] = defaultdict(set)
            # Lock for thread-safe operations
            self._operation_lock = asyncio.Lock()
            self._initialized = True
            logger.info("ConnectionManager initialized")

    async def add_connection(
        self,
        websocket: WebSocket,
        composition_id: UUID,
        user_id: str | None = None,
        state: ConnectionState = ConnectionState.CONNECTING,
    ) -> ConnectionInfo:
        """
        Add a new WebSocket connection for a composition.

        Args:
            websocket: FastAPI WebSocket instance
            composition_id: UUID of the composition
            user_id: Optional user identifier
            state: Initial connection state

        Returns:
            ConnectionInfo object for the new connection
        """
        async with self._operation_lock:
            conn_info = ConnectionInfo(
                websocket=websocket,
                composition_id=composition_id,
                user_id=user_id,
                state=state,
            )
            self._connections[composition_id].add(conn_info)
            logger.info(
                f"Added WebSocket connection for composition {composition_id}, "
                f"user {user_id}, total connections: {len(self._connections[composition_id])}"
            )
            return conn_info

    async def remove_connection(
        self, websocket: WebSocket, composition_id: UUID
    ) -> ConnectionInfo | None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket instance to remove
            composition_id: Composition ID the connection belongs to

        Returns:
            Removed ConnectionInfo if found, None otherwise
        """
        async with self._operation_lock:
            if composition_id not in self._connections:
                logger.warning(f"No connections found for composition {composition_id}")
                return None

            # Find the connection info by websocket instance
            conn_info = None
            for conn in self._connections[composition_id]:
                if conn.websocket is websocket:
                    conn_info = conn
                    break

            if conn_info:
                self._connections[composition_id].discard(conn_info)
                # Clean up empty composition entries
                if not self._connections[composition_id]:
                    del self._connections[composition_id]

                logger.info(
                    f"Removed WebSocket connection for composition {composition_id}, "
                    f"user {conn_info.user_id}"
                )
                return conn_info
            else:
                logger.warning(f"WebSocket connection not found for composition {composition_id}")
                return None

    async def get_connections(self, composition_id: UUID) -> set[ConnectionInfo]:
        """
        Get all active connections for a composition.

        Args:
            composition_id: Composition UUID

        Returns:
            Set of ConnectionInfo objects
        """
        async with self._operation_lock:
            return self._connections.get(composition_id, set()).copy()

    async def get_connection_count(self, composition_id: UUID) -> int:
        """
        Get the number of active connections for a composition.

        Args:
            composition_id: Composition UUID

        Returns:
            Number of active connections
        """
        async with self._operation_lock:
            return len(self._connections.get(composition_id, set()))

    async def update_connection_state(
        self, websocket: WebSocket, composition_id: UUID, state: ConnectionState
    ) -> bool:
        """
        Update the state of a connection.

        Args:
            websocket: WebSocket instance
            composition_id: Composition UUID
            state: New connection state

        Returns:
            True if connection was found and updated, False otherwise
        """
        async with self._operation_lock:
            if composition_id not in self._connections:
                return False

            for conn in self._connections[composition_id]:
                if conn.websocket is websocket:
                    old_state = conn.state
                    conn.state = state
                    logger.info(
                        f"Updated connection state for composition {composition_id}, "
                        f"user {conn.user_id}: {old_state.value} -> {state.value}"
                    )
                    return True

            return False

    async def update_heartbeat(
        self, websocket: WebSocket, composition_id: UUID, sequence: int
    ) -> bool:
        """
        Update heartbeat information for a connection.

        Args:
            websocket: WebSocket instance
            composition_id: Composition UUID
            sequence: Heartbeat sequence number

        Returns:
            True if connection was found and updated, False otherwise
        """
        async with self._operation_lock:
            if composition_id not in self._connections:
                return False

            for conn in self._connections[composition_id]:
                if conn.websocket is websocket:
                    conn.last_heartbeat = datetime.utcnow()
                    conn.heartbeat_sequence = sequence
                    conn.missed_heartbeats = 0
                    return True

            return False

    async def increment_missed_heartbeat(
        self, websocket: WebSocket, composition_id: UUID
    ) -> int | None:
        """
        Increment missed heartbeat count for a connection.

        Args:
            websocket: WebSocket instance
            composition_id: Composition UUID

        Returns:
            New missed heartbeat count, or None if connection not found
        """
        async with self._operation_lock:
            if composition_id not in self._connections:
                return None

            for conn in self._connections[composition_id]:
                if conn.websocket is websocket:
                    conn.missed_heartbeats += 1
                    return conn.missed_heartbeats

            return None

    async def broadcast_to_composition(self, composition_id: UUID, message: WSBaseMessage) -> int:
        """
        Broadcast a message to all connections for a composition.

        Args:
            composition_id: Composition UUID
            message: Message to broadcast

        Returns:
            Number of connections the message was sent to
        """
        connections = await self.get_connections(composition_id)
        if not connections:
            logger.debug(f"No connections to broadcast to for composition {composition_id}")
            return 0

        message_dict = message.model_dump(mode="json")
        sent_count = 0
        failed_connections = []

        for conn in connections:
            try:
                await conn.websocket.send_json(message_dict)
                sent_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to send message to connection for composition {composition_id}, "
                    f"user {conn.user_id}: {e}"
                )
                failed_connections.append(conn)

        # Remove failed connections
        if failed_connections:
            async with self._operation_lock:
                for conn in failed_connections:
                    self._connections[composition_id].discard(conn)
                    logger.info(
                        f"Removed failed connection for composition {composition_id}, "
                        f"user {conn.user_id}"
                    )

                # Clean up empty composition entries
                if not self._connections[composition_id]:
                    del self._connections[composition_id]

        logger.debug(
            f"Broadcast message to {sent_count} connections for composition {composition_id}"
        )
        return sent_count

    async def send_to_connection(
        self, websocket: WebSocket, composition_id: UUID, message: WSBaseMessage
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            websocket: WebSocket instance
            composition_id: Composition UUID
            message: Message to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        connections = await self.get_connections(composition_id)

        for conn in connections:
            if conn.websocket is websocket:
                try:
                    message_dict = message.model_dump(mode="json")
                    await conn.websocket.send_json(message_dict)
                    return True
                except Exception as e:
                    logger.error(
                        f"Failed to send message to connection for composition {composition_id}, "
                        f"user {conn.user_id}: {e}"
                    )
                    # Remove failed connection
                    await self.remove_connection(websocket, composition_id)
                    return False

        logger.warning(
            f"Connection not found for composition {composition_id} when sending message"
        )
        return False

    async def get_all_composition_ids(self) -> set[UUID]:
        """
        Get all composition IDs that have active connections.

        Returns:
            Set of composition UUIDs
        """
        async with self._operation_lock:
            return set(self._connections.keys())

    async def get_total_connection_count(self) -> int:
        """
        Get total number of active connections across all compositions.

        Returns:
            Total connection count
        """
        async with self._operation_lock:
            return sum(len(conns) for conns in self._connections.values())

    async def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about active connections.

        Returns:
            Dictionary with connection statistics
        """
        async with self._operation_lock:
            total_connections = sum(len(conns) for conns in self._connections.values())
            compositions_with_connections = len(self._connections)

            connections_per_composition = {
                str(comp_id): len(conns) for comp_id, conns in self._connections.items()
            }

            return {
                "total_connections": total_connections,
                "compositions_with_connections": compositions_with_connections,
                "connections_per_composition": connections_per_composition,
            }


# Singleton instance
connection_manager = ConnectionManager()

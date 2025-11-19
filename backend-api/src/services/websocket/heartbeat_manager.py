"""Heartbeat manager for WebSocket connection health monitoring."""

import asyncio
import logging
from datetime import datetime, timedelta

from app.api.schemas.websocket import WSHeartbeatMessage

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """
    Manages heartbeat/ping-pong mechanism for WebSocket connections.

    Sends periodic ping messages to all connections and monitors responses
    to detect and clean up stale connections.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        ping_interval: int = 30,
        max_missed_heartbeats: int = 3,
    ) -> None:
        """
        Initialize heartbeat manager.

        Args:
            connection_manager: WebSocket connection manager instance
            ping_interval: Seconds between ping messages (default: 30)
            max_missed_heartbeats: Maximum consecutive missed heartbeats before cleanup (default: 3)
        """
        self.connection_manager = connection_manager
        self.ping_interval = ping_interval
        self.max_missed_heartbeats = max_missed_heartbeats
        self._running = False
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._sequence_counter = 0
        logger.info(
            f"HeartbeatManager initialized with {ping_interval}s interval, "
            f"max {max_missed_heartbeats} missed heartbeats"
        )

    async def start(self) -> None:
        """Start the heartbeat monitoring loop."""
        if self._running:
            logger.warning("Heartbeat manager already running")
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Heartbeat manager started")

    async def stop(self) -> None:
        """Stop the heartbeat monitoring loop."""
        self._running = False
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                logger.info("Heartbeat task cancelled")
        logger.info("Heartbeat manager stopped")

    async def _heartbeat_loop(self) -> None:
        """
        Main loop for sending heartbeat pings and monitoring responses.

        Continuously sends ping messages at regular intervals and checks
        for stale connections.
        """
        logger.info("Starting heartbeat loop")

        while self._running:
            try:
                # Send heartbeat pings to all connections
                await self._send_heartbeat_pings()

                # Check for stale connections and clean them up
                await self._cleanup_stale_connections()

                # Wait for next heartbeat interval
                await asyncio.sleep(self.ping_interval)

            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break

            except Exception as e:
                logger.exception(f"Error in heartbeat loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(5)

        logger.info("Heartbeat loop stopped")

    async def _send_heartbeat_pings(self) -> None:
        """Send heartbeat ping messages to all active connections."""
        self._sequence_counter += 1
        composition_ids = await self.connection_manager.get_all_composition_ids()

        if not composition_ids:
            logger.debug("No active connections to send heartbeat pings")
            return

        total_sent = 0
        total_failed = 0

        for composition_id in composition_ids:
            connections = await self.connection_manager.get_connections(composition_id)

            for conn in connections:
                try:
                    # Create heartbeat message
                    heartbeat_msg = WSHeartbeatMessage(
                        composition_id=composition_id,
                        sequence=self._sequence_counter,
                    )

                    # Send to connection
                    success = await self.connection_manager.send_to_connection(
                        conn.websocket, composition_id, heartbeat_msg
                    )

                    if success:
                        total_sent += 1
                    else:
                        total_failed += 1
                        # Increment missed heartbeat counter
                        await self.connection_manager.increment_missed_heartbeat(
                            conn.websocket, composition_id
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to send heartbeat to connection for composition {composition_id}: {e}"
                    )
                    total_failed += 1
                    # Increment missed heartbeat counter
                    try:
                        await self.connection_manager.increment_missed_heartbeat(
                            conn.websocket, composition_id
                        )
                    except Exception:
                        pass

        if total_sent > 0 or total_failed > 0:
            logger.debug(
                f"Sent heartbeat pings: {total_sent} successful, {total_failed} failed "
                f"(sequence: {self._sequence_counter})"
            )

    async def _cleanup_stale_connections(self) -> None:
        """
        Identify and clean up stale connections that haven't responded to heartbeats.

        Closes connections that have missed more than max_missed_heartbeats consecutive pings.
        """
        composition_ids = await self.connection_manager.get_all_composition_ids()
        stale_count = 0

        for composition_id in composition_ids:
            connections = await self.connection_manager.get_connections(composition_id)

            for conn in connections.copy():  # Copy to avoid modification during iteration
                try:
                    # Check if connection has missed too many heartbeats
                    if conn.missed_heartbeats >= self.max_missed_heartbeats:
                        logger.warning(
                            f"Connection stale for composition {composition_id}, "
                            f"user {conn.user_id}: {conn.missed_heartbeats} missed heartbeats"
                        )

                        # Close the WebSocket connection
                        try:
                            await conn.websocket.close(
                                code=1000,
                                reason=f"Connection timeout: missed {conn.missed_heartbeats} heartbeats",
                            )
                        except Exception as e:
                            logger.debug(f"Error closing stale connection: {e}")

                        # Remove from connection manager
                        await self.connection_manager.remove_connection(
                            conn.websocket, composition_id
                        )

                        stale_count += 1
                        logger.info(
                            f"Cleaned up stale connection for composition {composition_id}, "
                            f"user {conn.user_id}"
                        )

                    # Also check if connection hasn't sent heartbeat in a long time
                    # (fallback in case missed_heartbeats counter isn't working)
                    elif conn.last_heartbeat:
                        time_since_heartbeat = datetime.utcnow() - conn.last_heartbeat
                        max_silence_duration = timedelta(
                            seconds=self.ping_interval * (self.max_missed_heartbeats + 1)
                        )

                        if time_since_heartbeat > max_silence_duration:
                            logger.warning(
                                f"Connection silent for {time_since_heartbeat.total_seconds()}s "
                                f"for composition {composition_id}, user {conn.user_id}"
                            )

                            try:
                                await conn.websocket.close(
                                    code=1000,
                                    reason=f"Connection timeout: no activity for {int(time_since_heartbeat.total_seconds())}s",
                                )
                            except Exception as e:
                                logger.debug(f"Error closing silent connection: {e}")

                            await self.connection_manager.remove_connection(
                                conn.websocket, composition_id
                            )

                            stale_count += 1
                            logger.info(
                                f"Cleaned up silent connection for composition {composition_id}, "
                                f"user {conn.user_id}"
                            )

                except Exception as e:
                    logger.error(
                        f"Error checking stale connection for composition {composition_id}: {e}"
                    )

        if stale_count > 0:
            logger.info(f"Cleaned up {stale_count} stale connections")

    async def get_stats(self) -> dict:
        """
        Get heartbeat manager statistics.

        Returns:
            Dictionary with heartbeat statistics
        """
        return {
            "running": self._running,
            "ping_interval": self.ping_interval,
            "max_missed_heartbeats": self.max_missed_heartbeats,
            "current_sequence": self._sequence_counter,
        }

    @property
    def is_running(self) -> bool:
        """Check if heartbeat manager is currently running."""
        return self._running

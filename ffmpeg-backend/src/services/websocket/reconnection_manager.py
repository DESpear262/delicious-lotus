"""Reconnection manager for WebSocket message recovery and state synchronization."""

import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.websocket import WSBaseMessage
from redis import Redis

logger = logging.getLogger(__name__)


class ReconnectionManager:
    """
    Manages WebSocket reconnection tokens and message recovery.

    Stores recent messages in Redis for recovery during reconnection
    and generates reconnection tokens for state continuity.
    """

    def __init__(
        self,
        redis_client: Redis,
        message_ttl: int = 300,  # 5 minutes
        max_stored_messages: int = 100,
    ) -> None:
        """
        Initialize reconnection manager.

        Args:
            redis_client: Redis client instance
            message_ttl: TTL for stored messages in seconds (default: 300 = 5 minutes)
            max_stored_messages: Maximum messages to store per composition (default: 100)
        """
        self.redis_client = redis_client
        self.message_ttl = message_ttl
        self.max_stored_messages = max_stored_messages
        logger.info(
            f"ReconnectionManager initialized with {message_ttl}s TTL, "
            f"max {max_stored_messages} messages per composition"
        )

    def generate_reconnection_token(self, composition_id: UUID, user_id: str | None = None) -> str:
        """
        Generate a reconnection token for a composition and user.

        Args:
            composition_id: Composition UUID
            user_id: Optional user identifier

        Returns:
            Reconnection token string
        """
        # Generate a secure random token component
        random_part = secrets.token_urlsafe(16)

        # Create a deterministic part from composition and user
        deterministic_data = f"{composition_id}:{user_id or 'anonymous'}"
        deterministic_hash = hashlib.sha256(deterministic_data.encode()).hexdigest()[:16]

        # Combine both parts
        token = f"{deterministic_hash}_{random_part}"

        # Store token metadata in Redis with TTL
        token_key = f"reconnection_token:{token}"
        token_data = {
            "composition_id": str(composition_id),
            "user_id": user_id or "",
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            self.redis_client.setex(token_key, self.message_ttl, json.dumps(token_data))
            logger.debug(f"Generated reconnection token for composition {composition_id}")
        except Exception as e:
            logger.error(f"Failed to store reconnection token: {e}")

        return token

    def validate_reconnection_token(self, token: str) -> tuple[UUID | None, str | None]:
        """
        Validate a reconnection token and retrieve associated data.

        Args:
            token: Reconnection token to validate

        Returns:
            Tuple of (composition_id, user_id) if valid, (None, None) otherwise
        """
        token_key = f"reconnection_token:{token}"

        try:
            token_data_str = self.redis_client.get(token_key)
            if not token_data_str:
                logger.debug("Reconnection token not found or expired")
                return None, None

            token_data = json.loads(token_data_str)
            composition_id = UUID(token_data["composition_id"])
            user_id = token_data.get("user_id") or None

            logger.debug(f"Validated reconnection token for composition {composition_id}")
            return composition_id, user_id

        except Exception as e:
            logger.error(f"Error validating reconnection token: {e}")
            return None, None

    def store_message(self, composition_id: UUID, message: WSBaseMessage, sequence: int) -> bool:
        """
        Store a message in Redis for potential recovery during reconnection.

        Args:
            composition_id: Composition UUID
            message: WebSocket message to store
            sequence: Message sequence number

        Returns:
            True if stored successfully, False otherwise
        """
        messages_key = f"composition:{composition_id}:messages"

        try:
            # Create message entry with sequence number
            message_entry = {
                "sequence": sequence,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message.model_dump(mode="json"),
            }

            # Add to sorted set (sorted by sequence number)
            self.redis_client.zadd(messages_key, {json.dumps(message_entry): sequence})

            # Set TTL on the key
            self.redis_client.expire(messages_key, self.message_ttl)

            # Trim to max stored messages (keep most recent)
            message_count = self.redis_client.zcard(messages_key)
            if message_count > self.max_stored_messages:
                # Remove oldest messages
                remove_count = message_count - self.max_stored_messages
                self.redis_client.zremrangebyrank(messages_key, 0, remove_count - 1)

            logger.debug(f"Stored message {sequence} for composition {composition_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store message for composition {composition_id}: {e}")
            return False

    def get_missed_messages(self, composition_id: UUID, last_sequence: int) -> list[dict[str, Any]]:
        """
        Retrieve messages that were sent after a given sequence number.

        Args:
            composition_id: Composition UUID
            last_sequence: Last sequence number the client received

        Returns:
            List of messages with sequence numbers greater than last_sequence
        """
        messages_key = f"composition:{composition_id}:messages"

        try:
            # Get all messages with sequence > last_sequence
            message_entries = self.redis_client.zrangebyscore(
                messages_key, last_sequence + 1, "+inf"
            )

            missed_messages = []
            for entry_str in message_entries:
                try:
                    entry = json.loads(entry_str)
                    missed_messages.append(entry)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse stored message: {e}")
                    continue

            logger.info(
                f"Retrieved {len(missed_messages)} missed messages for "
                f"composition {composition_id} (after sequence {last_sequence})"
            )
            return missed_messages

        except Exception as e:
            logger.error(
                f"Failed to retrieve missed messages for composition {composition_id}: {e}"
            )
            return []

    def get_latest_sequence(self, composition_id: UUID) -> int:
        """
        Get the latest sequence number for a composition.

        Args:
            composition_id: Composition UUID

        Returns:
            Latest sequence number, or 0 if none found
        """
        messages_key = f"composition:{composition_id}:messages"

        try:
            # Get the highest score (sequence number) in the sorted set
            latest = self.redis_client.zrange(messages_key, -1, -1, withscores=True)

            if latest:
                return int(latest[0][1])  # Return the score (sequence number)

            return 0

        except Exception as e:
            logger.error(f"Failed to get latest sequence for composition {composition_id}: {e}")
            return 0

    def clear_messages(self, composition_id: UUID) -> bool:
        """
        Clear all stored messages for a composition.

        Args:
            composition_id: Composition UUID

        Returns:
            True if cleared successfully, False otherwise
        """
        messages_key = f"composition:{composition_id}:messages"

        try:
            self.redis_client.delete(messages_key)
            logger.debug(f"Cleared stored messages for composition {composition_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear messages for composition {composition_id}: {e}")
            return False

    def extend_token_ttl(self, token: str) -> bool:
        """
        Extend the TTL of a reconnection token.

        Args:
            token: Reconnection token

        Returns:
            True if TTL extended successfully, False otherwise
        """
        token_key = f"reconnection_token:{token}"

        try:
            self.redis_client.expire(token_key, self.message_ttl)
            logger.debug("Extended reconnection token TTL")
            return True

        except Exception as e:
            logger.error(f"Failed to extend token TTL: {e}")
            return False

    def get_stats(self, composition_id: UUID) -> dict[str, Any]:
        """
        Get statistics about stored messages for a composition.

        Args:
            composition_id: Composition UUID

        Returns:
            Dictionary with message storage statistics
        """
        messages_key = f"composition:{composition_id}:messages"

        try:
            message_count = self.redis_client.zcard(messages_key)
            latest_sequence = self.get_latest_sequence(composition_id)
            ttl = self.redis_client.ttl(messages_key)

            return {
                "stored_message_count": message_count,
                "latest_sequence": latest_sequence,
                "ttl_seconds": ttl if ttl > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get stats for composition {composition_id}: {e}")
            return {
                "stored_message_count": 0,
                "latest_sequence": 0,
                "ttl_seconds": 0,
                "error": str(e),
            }

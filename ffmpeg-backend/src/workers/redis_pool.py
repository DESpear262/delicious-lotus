"""Redis connection pool management with error handling and health checks."""

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from app.config import settings
from redis import ConnectionPool, Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import (
    BusyLoadingError,
    ConnectionError,
    RedisError,
    TimeoutError,
)
from redis.retry import Retry

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """Manages Redis connection pool with health checks and reconnection logic."""

    def __init__(
        self,
        url: str | None = None,
        max_connections: int | None = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ) -> None:
        """Initialize Redis connection manager.

        Args:
            url: Redis connection URL (defaults to settings.redis_url)
            max_connections: Maximum number of connections in pool (defaults to settings.redis_max_connections)
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Interval between health checks in seconds
        """
        self.url = url or str(settings.redis_url)
        self.max_connections = max_connections or settings.redis_max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval

        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
        self._last_health_check: float = 0.0
        self._is_healthy: bool = False

        logger.info(
            "Initialized RedisConnectionManager",
            extra={
                "max_connections": self.max_connections,
                "socket_timeout": self.socket_timeout,
                "health_check_interval": self.health_check_interval,
            },
        )

    def _create_pool(self) -> ConnectionPool:
        """Create a new Redis connection pool with retry logic.

        Returns:
            ConnectionPool: Configured connection pool

        Raises:
            ConnectionError: If unable to create connection pool
        """
        try:
            # Configure retry logic with exponential backoff
            retry = Retry(ExponentialBackoff(), retries=3)

            pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                retry=retry,
                health_check_interval=self.health_check_interval,
                decode_responses=True,  # Automatically decode responses to strings
            )

            logger.info("Created Redis connection pool successfully")
            return pool

        except Exception as e:
            logger.exception(
                "Failed to create Redis connection pool",
                extra={"error": str(e)},
            )
            raise ConnectionError(f"Failed to create Redis connection pool: {e}") from e

    def _create_client(self) -> Redis:
        """Create a new Redis client using the connection pool.

        Returns:
            Redis: Redis client instance

        Raises:
            ConnectionError: If unable to create Redis client
        """
        if self._pool is None:
            self._pool = self._create_pool()

        try:
            client = Redis(connection_pool=self._pool)
            logger.debug("Created Redis client successfully")
            return client

        except Exception as e:
            logger.exception(
                "Failed to create Redis client",
                extra={"error": str(e)},
            )
            raise ConnectionError(f"Failed to create Redis client: {e}") from e

    def get_connection(self) -> Redis:
        """Get a Redis connection from the pool.

        Returns:
            Redis: Redis client instance

        Raises:
            ConnectionError: If unable to get connection
        """
        if self._client is None:
            self._client = self._create_client()

        # Perform periodic health checks
        current_time = time.time()
        if current_time - self._last_health_check > self.health_check_interval:
            self.health_check()

        return self._client

    def health_check(self, raise_on_failure: bool = False) -> bool:
        """Perform health check on Redis connection.

        Args:
            raise_on_failure: Whether to raise exception on health check failure

        Returns:
            bool: True if healthy, False otherwise

        Raises:
            ConnectionError: If raise_on_failure=True and health check fails
        """
        try:
            if self._client is None:
                self._client = self._create_client()

            # Try to ping Redis
            self._client.ping()

            # Check connection pool stats
            if self._pool:
                pool_info = {
                    "max_connections": self._pool.max_connections,
                    "pid": self._pool.pid,
                }
                logger.debug("Redis health check passed", extra=pool_info)

            self._is_healthy = True
            self._last_health_check = time.time()
            return True

        except (ConnectionError, TimeoutError, BusyLoadingError) as e:
            logger.warning(
                "Redis health check failed - attempting reconnection",
                extra={"error": str(e), "error_type": type(e).__name__},
            )

            # Attempt reconnection
            try:
                self._reconnect()
                self._is_healthy = True
                return True
            except Exception as reconnect_error:
                logger.error(
                    "Redis reconnection failed",
                    extra={"error": str(reconnect_error)},
                )
                self._is_healthy = False

                if raise_on_failure:
                    raise ConnectionError(
                        f"Redis health check failed: {reconnect_error}"
                    ) from reconnect_error

                return False

        except Exception as e:
            logger.exception(
                "Unexpected error during Redis health check",
                extra={"error": str(e)},
            )
            self._is_healthy = False

            if raise_on_failure:
                raise ConnectionError(f"Redis health check failed: {e}") from e

            return False

    def _reconnect(self) -> None:
        """Reconnect to Redis by recreating pool and client.

        Raises:
            ConnectionError: If reconnection fails
        """
        logger.info("Attempting Redis reconnection")

        try:
            # Close existing connections
            if self._client:
                try:
                    self._client.close()
                except Exception as e:
                    logger.warning(f"Error closing existing client: {e}")

            if self._pool:
                try:
                    self._pool.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting pool: {e}")

            # Recreate pool and client
            self._pool = None
            self._client = None
            self._pool = self._create_pool()
            self._client = self._create_client()

            # Verify connection works
            self._client.ping()

            logger.info("Redis reconnection successful")

        except Exception as e:
            logger.exception(
                "Redis reconnection failed",
                extra={"error": str(e)},
            )
            raise ConnectionError(f"Failed to reconnect to Redis: {e}") from e

    @contextmanager
    def pipeline(self, transaction: bool = True) -> Generator[Any, None, None]:
        """Get a Redis pipeline context manager.

        Args:
            transaction: Whether to use transaction mode (MULTI/EXEC)

        Yields:
            Pipeline: Redis pipeline instance

        Example:
            with redis_manager.pipeline() as pipe:
                pipe.set('key1', 'value1')
                pipe.set('key2', 'value2')
                pipe.execute()
        """
        client = self.get_connection()
        pipe = client.pipeline(transaction=transaction)

        try:
            yield pipe
        except RedisError as e:
            logger.error(f"Pipeline error: {e}")
            raise
        finally:
            try:
                pipe.reset()
            except Exception as e:
                logger.warning(f"Error resetting pipeline: {e}")

    def close(self) -> None:
        """Close Redis connections and cleanup resources."""
        logger.info("Closing Redis connection manager")

        if self._client:
            try:
                self._client.close()
                logger.debug("Closed Redis client")
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")
            finally:
                self._client = None

        if self._pool:
            try:
                self._pool.disconnect()
                logger.debug("Disconnected connection pool")
            except Exception as e:
                logger.warning(f"Error disconnecting pool: {e}")
            finally:
                self._pool = None

        self._is_healthy = False

    def get_pool_stats(self) -> dict[str, Any]:
        """Get connection pool statistics.

        Returns:
            dict: Pool statistics including connection counts
        """
        if not self._pool:
            return {"status": "not_initialized"}

        try:
            return {
                "status": "healthy" if self._is_healthy else "unhealthy",
                "max_connections": self._pool.max_connections,
                "pid": self._pool.pid,
                "last_health_check": self._last_health_check,
                "time_since_check": time.time() - self._last_health_check,
            }
        except Exception as e:
            logger.exception("Error getting pool stats", extra={"error": str(e)})
            return {"status": "error", "error": str(e)}

    @property
    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        return self._is_healthy


# Global Redis connection manager instance
redis_connection_manager = RedisConnectionManager()


def get_redis_connection() -> Redis:
    """Get a Redis connection from the global connection manager.

    Returns:
        Redis: Redis client instance

    Example:
        redis_conn = get_redis_connection()
        redis_conn.set('key', 'value')
    """
    return redis_connection_manager.get_connection()

"""Redis connection and caching utilities."""

from typing import Any

import structlog
from redis.asyncio import Redis, from_url

from vallorys.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Global Redis client
redis_client: Redis | None = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client
    logger.info("Initializing Redis connection")
    redis_client = from_url(
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
    )
    # Test connection
    await redis_client.ping()
    logger.info("Redis connected")


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        logger.info("Closing Redis connection")
        await redis_client.close()
        redis_client = None


def get_redis() -> Redis:
    """Get Redis client dependency."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client


class CacheService:
    """Caching service with automatic serialization."""

    def __init__(self, prefix: str = "vallorys"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        """Get cached value."""
        import json

        client = get_redis()
        value = await client.get(self._key(key))
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set cached value with optional TTL."""
        import json

        client = get_redis()
        ttl = ttl or settings.redis_cache_ttl
        await client.setex(
            self._key(key),
            ttl,
            json.dumps(value),
        )

    async def delete(self, key: str) -> None:
        """Delete cached value."""
        client = get_redis()
        await client.delete(self._key(key))

    async def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: int | None = None,
    ) -> Any:
        """Get cached value or compute and cache it."""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory()
        await self.set(key, value, ttl)
        return value


# Singleton cache service
cache = CacheService()

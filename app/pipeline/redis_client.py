"""Redis client helper for async publishing and subscribing."""
import redis.asyncio as redis


async def initialize_redis_client(host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None) -> redis.Redis:
    """Create a Redis client configured for async usage."""
    try:
        return await redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
    except Exception as exc:  # pragma: no cover - network path
        raise ConnectionError(f"Failed to connect to Redis: {exc}") from exc

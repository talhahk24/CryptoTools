import redis.asyncio as redis

async def initialize_redis_client(host='localhost', port=6379, db=0, password=None):
    try:
        await redis.Redis(host=host, port=port, db=db, password=password)
        return
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        raise

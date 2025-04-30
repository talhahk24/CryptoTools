import redis.asyncio as redis
import asyncio

async def publish_to_redis(data_queue:asyncio.Queue, redis_client:redis.Redis, stream_key:str, shutdown_event:asyncio.Event):
    while not shutdown_event.is_set():
        data = await data_queue.get()
        await redis_client.xadd(stream_key, data, nomkstream=True)
        print(f"Published to {stream_key}: {data}")




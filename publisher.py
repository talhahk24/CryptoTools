import redis.asyncio as redis
import asyncio
import options
import pydantic_models

async def publish_to_redis(data_queue:asyncio.Queue, redis_client:redis.Redis, exchange:options.ExchangeOptions, shutdown_event:asyncio.Event):
    while not shutdown_event.is_set():
        response = await data_queue.get()
        if "result" in response and "id" in response:
            continue
        if "code" in response and "msg" in response:
            continue
        if "data" not in response:
            continue

        stream_symbol = response.get("stream")
        stream_key=f"{exchange}:{stream_symbol}"
        data=validate_and_map(response["data"])
        await redis_client.xadd(stream_key, data, nomkstream=False)
        print(f"Published to {stream_key}: {data}")


def validate_and_map(raw_data:dict):
    try:
        event_type = raw_data.get("e")
        if event_type == "kline":
            mapped = {
                "event_type": event_type,
                "symbol": raw_data["s"],
                "timestamp": raw_data["E"],
                "kline_open": float(raw_data["k"]["o"] or 0.0),
                "kline_close": float(raw_data["k"]["c"] or 0.0),
                "kline_high": float(raw_data["k"]["h"] or 0.0),
                "kline_low": float(raw_data["k"]["l"] or 0.0),
                "kline_volume": float(raw_data["k"]["v"] or 0.0),
                "kline_trades": raw_data["k"]["n"],
                "kline_closed": str(raw_data["k"]["x"])
            }
            return pydantic_models.KlineEvent(**mapped).model_dump()
        else:
            return {}
    except Exception as e:
        print(f"Data validation/mapping error: {e}")
        return {}


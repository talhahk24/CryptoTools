import redis.asyncio as redis
import asyncio
import logging
import typing
import json

import options
import pydantic_models


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def parse_json(data):
    try:
        parsed = json.loads(data)
        return parsed
    except json.JSONDecodeError:
        return None

async def publish_to_redis(data_queue:asyncio.Queue, redis_client:redis.Redis,
                           exchange:options.ExchangeOptions, shutdown_event:asyncio.Event):
    logging.info(f"Starting Publisher for {exchange}")
    while not shutdown_event.is_set():
        response = await data_queue.get()

        parsed_data: dict[str, typing.Any] = parse_json(response)

        if not parsed_data:
            logger.warning(f"Could not parse response to JSON: {response} from {exchange}")
        if "result" in parsed_data and "id" in parsed_data:
            logger.info(f"Ignored subscription confirmation: {parsed_data}")
            continue
        if "code" in parsed_data and "msg" in parsed_data:
            logger.warning(f"Received error message from exchange {exchange}: {parsed_data}")
            continue
        if "data" not in parsed_data:
            logger.warning(f"Received unexpected message format from exchange {exchange}: {parsed_data}")
            continue

        stream_symbol = parsed_data.get("stream")
        stream_key=f"{exchange}:{stream_symbol}"
        val_data=validate_and_map(parsed_data)

        if not val_data:
            continue

        try:
            await redis_client.xadd(stream_key, val_data, nomkstream=False)
            logging.debug(f"Published to Redis stream {stream_key}: {val_data}")
        except Exception as e:
            logger.error(f"Error publishing to Redis stream {stream_key}: {e}", exc_info=True)
            continue

    logging.info(f"Closing Publisher for {exchange}")
    return


def validate_and_map(parsed_data:dict):
    try:
        event_type = parsed_data["data"]["e"]
        if event_type == "kline":
            binance_message = pydantic_models.BinanceWebSocketMessage(**parsed_data)

            mapped = {
                "kline_open": binance_message.data.kline.open_price,
                "kline_close": binance_message.data.kline.close_price,
                "kline_high": binance_message.data.kline.close_price,
                "kline_low": binance_message.data.kline.low_price,
                "kline_volume": binance_message.data.kline.base_volume,
                "kline_start_time": binance_message.data.kline.start_time,
                "kline_close_time": binance_message.data.kline.close_time,
                "kline_is_closed": 1 if binance_message.data.kline.is_closed else 0
            }

            return mapped
        elif event_type == "trade":
            binance_message = pydantic_models.BinanceWebSocketMessage(**parsed_data)

            mapped = {
                "event_time": binance_message.data.event_time,
                "trade_id": binance_message.data.trade_id,
                "price": binance_message.data.price,
                "quantity": binance_message.data.quantity,
                "trade_time": binance_message.data.trade_time,
                "is_buyer_maker": 1 if binance_message.data.is_buyer_maker else 0
            }

            return mapped
        else:
            logger.warning(f"Unsupported event type: {event_type}")
            return None

    except ValueError:
        logger.error("Validation error", exc_info=True)
        return  None
    except Exception as e:
        logger.error(f"Error validating/mapping data: {e}", exc_info=True)
        return None


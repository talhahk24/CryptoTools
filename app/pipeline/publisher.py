"""Normalize websocket responses and publish to Redis Streams."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import options
from app.models.binance import BinanceWebSocketMessage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def parse_json(data: str) -> dict | None:
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        logger.warning("Received non-JSON payload: %s", data)
        return None


async def publish_to_redis(
    data_queue: asyncio.Queue,
    redis_client: redis.Redis,
    exchange: options.ExchangeOptions,
    shutdown_event: asyncio.Event,
) -> None:
    logger.info("Starting publisher for %s", exchange)
    while not shutdown_event.is_set():
        response = await data_queue.get()
        parsed_data = parse_json(response)

        if not parsed_data:
            continue
        if parsed_data.get("result") is not None and "id" in parsed_data:
            logger.debug("Ignored subscription confirmation: %s", parsed_data)
            continue
        if "code" in parsed_data and "msg" in parsed_data:
            logger.warning("Received error message from %s: %s", exchange, parsed_data)
            continue
        if "data" not in parsed_data:
            logger.warning("Unexpected message format from %s: %s", exchange, parsed_data)
            continue

        stream_symbol = parsed_data.get("stream")
        stream_key = f"{exchange}:{stream_symbol}"
        validated = validate_and_map(parsed_data)

        if not validated:
            continue

        try:
            await redis_client.xadd(stream_key, validated, nomkstream=False)
            logger.debug("Published to Redis stream %s: %s", stream_key, validated)
        except Exception as exc:  # pragma: no cover - network path
            logger.error("Error publishing to Redis stream %s: %s", stream_key, exc, exc_info=True)
            continue

    logger.info("Closing publisher for %s", exchange)


def validate_and_map(parsed_data: dict[str, Any]) -> dict[str, Any] | None:
    try:
        event_type = parsed_data["data"]["e"]
        message = BinanceWebSocketMessage(**parsed_data)

        if event_type == "kline":
            kline = message.data.kline
            return {
                "kline_open": kline.open_price,
                "kline_close": kline.close_price,
                "kline_high": kline.high_price,
                "kline_low": kline.low_price,
                "kline_volume": kline.base_volume,
                "kline_start_time": kline.start_time,
                "kline_close_time": kline.close_time,
                "kline_is_closed": 1 if kline.is_closed else 0,
            }
        if event_type == "trade":
            trade = message.data
            return {
                "event_time": trade.event_time,
                "trade_id": trade.trade_id,
                "price": trade.price,
                "quantity": trade.quantity,
                "trade_time": trade.trade_time,
                "is_buyer_maker": 1 if trade.is_buyer_maker else 0,
            }

        logger.warning("Unsupported event type: %s", event_type)
        return None
    except ValueError:
        logger.error("Validation error", exc_info=True)
        return None
    except Exception as exc:  # pragma: no cover - network path
        logger.error("Error validating/mapping data: %s", exc, exc_info=True)
        return None

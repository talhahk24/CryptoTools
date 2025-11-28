"""Example strategy subscriber consuming Redis Streams messages."""
from __future__ import annotations

import asyncio
import logging
from typing import Generator

import redis.asyncio as redis

from app.config import options
from app.strategies import STRATEGY_HANDLERS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_stream_key(exchange: str, symbol: str, interval: str | None, data_type: str) -> str | None:
    symbol = symbol.lower().replace("/", "")
    if data_type == "kline":
        return f"{exchange}:{symbol}@kline_{interval}"
    if data_type == "trade":
        return f"{exchange}:{symbol}@trade"
    return None


def get_consumer_name(
    consumer_type: options.ConsumerOptions, stream_key: str, id_generator: Generator[int, None, None]
) -> str:
    gen_id = next(id_generator)
    return f"{gen_id}-{consumer_type}:{stream_key}_consumer"


async def strategy_subscriber(
    redis_client: redis.Redis,
    symbol: options.SymbolOptions,
    exchange: options.ExchangeOptions,
    interval: options.TimeFramesOptions | None,
    data_type: options.DataTypesOptions,
    strategy: options.StrategyOptions,
    shutdown_event: asyncio.Event,
    id_generator: Generator[int, None, None],
) -> None:
    stream_key = get_stream_key(exchange, symbol, interval, data_type)
    consumer_name = get_consumer_name(options.ConsumerOptions.STRATEGY, stream_key, id_generator)

    if not stream_key:
        logger.error("Unsupported data type: %s called by consumer: %s", data_type, consumer_name)
        return

    strategy_fn = STRATEGY_HANDLERS.get(strategy)
    if not strategy_fn:
        logger.error("No strategy handler registered for %s", strategy)
        return

    while not shutdown_event.is_set():
        logger.debug("%s listening to %s", consumer_name, stream_key)
        read = await redis_client.xread(streams={stream_key: "$"}, count=1, block=10000)
        if not read:
            logger.debug("%s got nothing for 10s on %s", consumer_name, stream_key)
            continue
        signal = strategy_fn(read)
        logger.info("%s generated signal: %s", consumer_name, signal)


async def dashboard_subscriber(
    redis_client: redis.Redis,
    symbol: options.SymbolOptions,
    exchange: options.ExchangeOptions,
    interval: options.TimeFramesOptions,
    data_type: options.DataTypesOptions,
    consumer_name: str,
    strategy: str,
    shutdown_event: asyncio.Event,
) -> None:
    stream_key = get_stream_key(exchange, symbol, interval, data_type)
    while not shutdown_event.is_set():
        logger.debug("Dashboard listening to %s", stream_key)
        read = await redis_client.xread(streams={stream_key: ">"}, count=1)
        logger.debug("Dashboard received data: %s", read)

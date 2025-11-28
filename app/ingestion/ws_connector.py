"""Async websocket ingestion for exchange market data."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import ssl
from typing import Set

import certifi
import websockets

from app.config import options

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EXCHANGE_WEBSOCKET_URIS = {
    options.ExchangeOptions.BINANCE: "wss://stream.binance.com:9443/stream",
}


async def resubscribe_all(
    websocket: websockets.WebSocketClientProtocol, resub_set: Set[tuple], exchange: options.ExchangeOptions
) -> None:
    """Resubscribe to all streams after reconnecting."""
    logger.debug("Resubscribing to %s", exchange)
    stream_list = [stream_name for _, stream_name in resub_set]
    subscribe_message = {"method": "SUBSCRIBE", "params": stream_list, "id": len(stream_list) + 1}
    await websocket.send(json.dumps(subscribe_message))
    logger.debug("Sent resubscribe request for %s to %s", stream_list, exchange)


async def retry_connection(
    uri: str,
    ssl_context: ssl.SSLContext,
    exchange: options.ExchangeOptions,
    live_exchange_ws: Set[options.ExchangeOptions],
) -> websockets.WebSocketClientProtocol:
    """Attempt reconnection with exponential backoff and jitter."""
    attempt = 0
    max_delay = 67
    while exchange not in live_exchange_ws:
        try:
            websocket = await websockets.connect(uri, ssl=ssl_context)
            live_exchange_ws.add(exchange)
            return websocket
        except Exception as exc:  # pragma: no cover - network path
            attempt += 1
            delay = min(5 * 2 ** (attempt - 1), max_delay)
            jitter_delay = delay + random.uniform(0, delay / 10)
            logger.error(
                "%s WebSocket reconnection attempt %s failed: %s. Retrying in %.2f seconds...",
                exchange,
                attempt,
                exc,
                jitter_delay,
            )
            await asyncio.sleep(jitter_delay)
    raise RuntimeError(f"Failed to reconnect to {exchange}")


async def start_websocket_connection(
    exchange: options.ExchangeOptions,
    live_exchange_ws: Set[options.ExchangeOptions],
    subscriptions: Set[tuple],
    ssl_context: ssl.SSLContext,
    response_queue: asyncio.Queue,
    shutdown_event: asyncio.Event,
) -> tuple[websockets.WebSocketClientProtocol, Set[options.ExchangeOptions]]:
    uri = EXCHANGE_WEBSOCKET_URIS[exchange]
    live_exchange_ws.add(exchange)
    websocket = await websockets.connect(uri, ssl=ssl_context)

    async def listener() -> None:
        nonlocal websocket
        while not shutdown_event.is_set():
            try:
                response = await websocket.recv()
                await response_queue.put(response)
            except websockets.ConnectionClosed:  # pragma: no cover - network path
                while not shutdown_event.is_set():
                    live_exchange_ws.discard(exchange)
                    logger.warning("%s WebSocket closed. Attempting to reconnect...", exchange)
                    websocket = await retry_connection(uri, ssl_context, exchange, live_exchange_ws)
                    logger.info("Reconnected to %s WebSocket", exchange)

                    resub_set = {sub for sub in subscriptions if sub[0] == exchange}
                    if resub_set:
                        asyncio.create_task(resubscribe_all(websocket, resub_set, exchange))
                    break
            except Exception as exc:  # pragma: no cover - network path
                logger.error("Error in listener for %s: %s", exchange, exc, exc_info=True)

    asyncio.create_task(listener())
    return websocket, live_exchange_ws


async def add_subscription(
    websocket: websockets.WebSocketClientProtocol,
    subscriptions: Set[tuple],
    exchange: options.ExchangeOptions,
    symbol: options.SymbolOptions,
    timeframe: options.TimeFramesOptions | None = None,
) -> None:
    stream_name = f"{symbol.value.lower().replace('/', '')}"
    if timeframe:
        stream_name += f"@kline_{timeframe.value}"
    else:
        stream_name += "@trade"

    if (exchange, stream_name) in subscriptions:
        return

    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": [stream_name],
        "id": len(subscriptions) + 1,
    }
    await websocket.send(json.dumps(subscribe_message))
    subscriptions.add((exchange, stream_name))


def build_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.load_verify_locations(certifi.where())
    return context

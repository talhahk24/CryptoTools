"""Demo runner wiring ingestion -> validation -> Redis Streams -> strategy consumer."""
from __future__ import annotations

import asyncio
import itertools

from app.config import options
from app.ingestion import ws_connector
from app.pipeline import publisher, redis_client
from app.subscribers import strategy_consumer


async def start_system() -> None:
    def start_strategy_id_generator():
        counter = itertools.count(1)
        while True:
            yield next(counter)

    strategy_id_generator = start_strategy_id_generator()

    redis_conn = await redis_client.initialize_redis_client()
    response_queue = asyncio.Queue()
    live_exchange_websockets = set()
    active_subscriptions = set()
    ssl_context = ws_connector.build_ssl_context()
    end_main = asyncio.Event()

    websocket, live_exchange_websockets = await ws_connector.start_websocket_connection(
        options.ExchangeOptions.BINANCE,
        live_exchange_websockets,
        active_subscriptions,
        ssl_context,
        response_queue,
        end_main,
    )

    await ws_connector.add_subscription(
        websocket,
        active_subscriptions,
        options.ExchangeOptions.BINANCE,
        options.SymbolOptions.BTC_USDT,
        options.TimeFramesOptions.ONE_SECOND,
    )

    await ws_connector.add_subscription(
        websocket,
        active_subscriptions,
        options.ExchangeOptions.BINANCE,
        options.SymbolOptions.ETH_USDT,
    )

    asyncio.create_task(
        publisher.publish_to_redis(response_queue, redis_conn, options.ExchangeOptions.BINANCE, end_main),
        name="publisher_task_binance",
    )

    symbol = options.SymbolOptions.BTC_USDT
    exchange = options.ExchangeOptions.BINANCE
    interval = options.TimeFramesOptions.ONE_SECOND
    data_type_kline = options.DataTypesOptions.KLINE
    data_type_trade = options.DataTypesOptions.TRADE
    strategy = options.StrategyOptions.RSI

    asyncio.create_task(
        strategy_consumer.strategy_subscriber(
            redis_conn,
            symbol,
            exchange,
            interval,
            data_type_kline,
            strategy,
            end_main,
            strategy_id_generator,
        ),
        name="strategy_subscriber_task",
    )
    asyncio.create_task(
        strategy_consumer.strategy_subscriber(
            redis_conn,
            options.SymbolOptions.ETH_USDT,
            exchange,
            interval,
            data_type_trade,
            strategy,
            end_main,
            strategy_id_generator,
        ),
        name="strategy_subscriber_task_eth",
    )

    await end_main.wait()


if __name__ == "__main__":
    asyncio.run(start_system())

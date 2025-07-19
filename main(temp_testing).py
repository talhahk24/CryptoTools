import redis_client
import ws_connector
import publisher
import subscribers
import options
import asyncio
import ssl
import certifi
import itertools

async def start_system():

    def start_strategy_id_generator():
        counter = itertools.count(1)
        while True:
            yield next(counter)

    strategy_id_generator = start_strategy_id_generator()

    r = await redis_client.initialize_redis_client()

    response_queue = asyncio.Queue()
    live_exchange_websockets = set()
    active_subscriptions = set()
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(certifi.where())
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

    asyncio.create_task(publisher.publish_to_redis(response_queue, r, options.ExchangeOptions.BINANCE, end_main), name="publisher_task_binance")

    symbol = options.SymbolOptions.BTC_USDT
    exchange = options.ExchangeOptions.BINANCE
    interval = options.TimeFramesOptions.ONE_SECOND
    data_type_kline = options.DataTypesOptions.KLINE
    data_type_trade = options.DataTypesOptions.TRADE
    strategy = options.StrategyOptions.RSI

    asyncio.create_task(subscribers.strategy_subscriber(r,symbol,exchange,interval,
                                                        data_type_kline, strategy,
                                                        end_main, strategy_id_generator), name="strategy_subscriber_task")
    asyncio.create_task(subscribers.strategy_subscriber(r,
                                                        options.SymbolOptions.ETH_USDT,
                                                        exchange,
                                                        interval,
                                                        data_type_trade,
                                                        strategy,
                                                        end_main, strategy_id_generator), name="strategy_subscriber_task_eth")

    #await subscribers.dashboard_subscriber(r, stream_key, consumer_name, end_main)

    await end_main.wait()


if __name__ == "__main__":
    asyncio.run(start_system())
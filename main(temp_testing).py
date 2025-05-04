import redis_client
import ws_connector
import publisher
import subscribers
import options
import asyncio
import ssl
import certifi

async def start_system():
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
        options.TimeFramesOptions.ONE_SECOND,
    )

    asyncio.create_task(publisher.publish_to_redis(response_queue, r, options.ExchangeOptions.BINANCE, end_main), name="publisher_task")

    symbol = options.SymbolOptions.BTC_USDT
    exchange = options.ExchangeOptions.BINANCE
    interval = options.TimeFramesOptions.ONE_SECOND
    data_type = options.DataTypesOptions.KLINE
    consumer_name = "strategy_consumer_1"
    strategy = options.StrategyOptions.RSI

    asyncio.create_task(subscribers.strategy_subscriber(r,symbol,exchange,interval,
                                                        data_type, consumer_name, strategy,
                                                        end_main), name="strategy_subscriber_task")
    #await subscribers.dashboard_subscriber(r, stream_key, consumer_name, end_main)

    await end_main.wait()


if __name__ == "__main__":
    asyncio.run(start_system())
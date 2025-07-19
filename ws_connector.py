import asyncio
import websockets
import ssl
import certifi
import json
import logging
import random


import options

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


EXCHANGE_WEBSOCKET_URIS = {
    options.ExchangeOptions.BINANCE: "wss://stream.binance.com:9443/stream"
}

async def resubscribe_all(websocket, resub_set:set, exchange:options.ExchangeOptions):
    logger.debug(f"Resubscribing to {exchange}")
    stream_list = []
    for exchange, stream_name in resub_set:
        stream_list.append(stream_name)
    subscribe_message = {"method": "SUBSCRIBE", "params": stream_list, "id": len(stream_list)+1}
    await websocket.send(json.dumps(subscribe_message))
    logger.debug(f"Resub request send for {stream_list} to {exchange}")

async def retry_connection(uri, ssl_contxt, exchange:options.ExchangeOptions ,
                           live_exchange_ws:set[options.ExchangeOptions]):
    attempt = 0
    max_delay = 67 #six-seven!!!
    while exchange not in live_exchange_ws:
        try:
            websocket = await websockets.connect(uri, ssl=ssl_contxt)
            live_exchange_ws.add(exchange)
            return websocket
        except Exception as e:
            attempt += 1
            delay = min(5 * 2 ** (attempt - 1), max_delay)

            jitter_delay = delay + random.uniform(0, delay/10)
            logger.error(f"{exchange} WebSocket reconnection attempt {attempt} failed: {e}. Retrying in {jitter_delay:.2f} seconds...")

            await asyncio.sleep(jitter_delay)

async def start_websocket_connection(exchange:options.ExchangeOptions,
                                     live_exchange_ws:set[options.ExchangeOptions], subscriptions:set,
                                     ssl_contxt:ssl.SSLContext, response_queue:asyncio.Queue,
                                     shutdown_event:asyncio.Event):
    uri = EXCHANGE_WEBSOCKET_URIS[exchange]
    live_exchange_ws.add(exchange)
    websocket = await websockets.connect(uri, ssl=ssl_contxt)

    async def listener():
        while not shutdown_event.is_set():
            nonlocal websocket
            try:
                response = await websocket.recv()
                print(response)
                await response_queue.put(response)


            except websockets.ConnectionClosed:
                while not shutdown_event.is_set():
                    live_exchange_ws.remove(exchange)
                    logger.warning(f"{exchange} WebSocket connection closed. Attempting to reconnect...")
                    websocket = await retry_connection(uri, ssl_contxt, exchange, live_exchange_ws)
                    logger.info(f"Reconnected to {exchange} WebSocket")

                    resub_set = {
                        sub for sub in subscriptions
                        if sub[0] == exchange
                    }
                    if resub_set:
                        asyncio.create_task(resubscribe_all(websocket, resub_set, exchange))
                    break

            except Exception as e:
                logging.error(f"Error in listener for {exchange}: {e}", exc_info=True)

    asyncio.create_task(listener())
    return websocket, live_exchange_ws

async def add_subscription(websocket, subscriptions:set, exchange:options.ExchangeOptions,
                           symbol:options.SymbolOptions, timeframe:options.TimeFramesOptions=None):
    stream_name = f"{symbol.value.lower().replace('/', '')}"
    if timeframe:
        stream_name += f"@kline_{timeframe.value}"
    else:
        stream_name += "@trade"
    if (exchange,stream_name) in subscriptions:
        return
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": [stream_name],
        "id": len(subscriptions) + 1
    }
    await websocket.send(json.dumps(subscribe_message))
    subscriptions.add((exchange,stream_name))

async def close(end_event:asyncio.Event):
    end_event.set()

async def main():
    response_queue = asyncio.Queue()
    live_exchange_websockets = set()
    active_subscriptions = set()
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(certifi.where())
    end_main = asyncio.Event()

    websocket,live_exchange_websockets = await start_websocket_connection(options.ExchangeOptions.BINANCE, live_exchange_websockets,
                                                                          active_subscriptions, ssl_context, response_queue,
                                                                          end_main)
    await add_subscription(websocket, active_subscriptions, options.ExchangeOptions.BINANCE,
                           options.SymbolOptions.BTC_USDT)

    # await add_subscription(
    #     websocket, active_subscriptions,options.ExchangeOptions.BINANCE,
    #     options.SymbolOptions.ETH_USDT, options.TimeFramesOptions.ONE_SECOND)


    await end_main.wait()
    await websocket.close()

if __name__ == "__main__":
    asyncio.run(main())



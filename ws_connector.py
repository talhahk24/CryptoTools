import asyncio
import websockets
import ssl
import certifi
import json
from typing import Any

import options


EXCHANGE_WEBSOCKET_URIS = {
    options.ExchangeOptions.BINANCE: "wss://stream.binance.com:9443/stream"
}

def parse_json(data):
    try:
        parsed = json.loads(data)
        return parsed
    except json.JSONDecodeError:
        return None

async def retry_connection(uri, ssl_contxt):
    while True:
        try:
            websocket = await websockets.connect(uri, ssl=ssl_contxt)
            return websocket
        except Exception as e:
            #--------log
            await asyncio.sleep(5)

async def start_websocket_connection(exchange:options.ExchangeOptions, live_exchange_ws:set[options.ExchangeOptions],
                                     ssl_contxt:ssl.SSLContext, response_queue:asyncio.Queue,
                                     shutdown_event:asyncio.Event):
    uri = EXCHANGE_WEBSOCKET_URIS[exchange]
    websocket = await websockets.connect(uri, ssl=ssl_contxt)

    async def listener():
        while not shutdown_event.is_set():
            nonlocal websocket
            try:
                response = await websocket.recv()
                parsed_data:dict[str,Any] = parse_json(response)
                # --------data validation
                if parsed_data:
                    await response_queue.put(parsed_data)

            except websockets.ConnectionClosed:
                while not shutdown_event.is_set():
                    websocket = await retry_connection(uri, ssl_contxt)
            except Exception as e:
                #--------log
                await asyncio.sleep(1)

    live_exchange_ws.add(exchange)
    asyncio.create_task(listener())
    return websocket, live_exchange_ws

async def add_subscription(websocket, subscriptions, exchange:options.ExchangeOptions,
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

async def close(name:asyncio.Event):
    name.set()

async def main():
    response_queue = asyncio.Queue()
    live_exchange_websockets = set()
    active_subscriptions = set()
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(certifi.where())
    end_main = asyncio.Event()

    websocket,live_exchange_websockets = await start_websocket_connection(options.ExchangeOptions.BINANCE, live_exchange_websockets,
                                                                          ssl_context, response_queue, end_main)
    await add_subscription(websocket, active_subscriptions, options.ExchangeOptions.BINANCE,
                           options.SymbolOptions.BTC_USDT, options.TimeFramesOptions.ONE_SECOND)

    await add_subscription(
        websocket, active_subscriptions,options.ExchangeOptions.BINANCE,
        options.SymbolOptions.ETH_USDT, options.TimeFramesOptions.ONE_SECOND)


    await end_main.wait()
    await websocket.close()

if __name__ == "__main__":
    asyncio.run(main())



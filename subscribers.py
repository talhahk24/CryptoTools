import redis.asyncio as redis
import asyncio
import strategies
import options

async def strategy_subscriber(r:redis.Redis, symbol:options.SymbolOptions, exchange:options.ExchangeOptions, interval:options.TimeFramesOptions, data_type:options.DataTypesOptions,
                              consumer_name:str, strategy:str, shutdown_event:asyncio.Event):
    symbol = symbol.value.lower().replace("/", "")
    if data_type.value == "kline":
        stream_key = f"{exchange}:{symbol}@kline_{interval}"
    elif data_type.value == "trade":
        stream_key = f"{exchange}:{symbol}@trade"
    else:
        raise ValueError("Unsupported market data type called by strat subscriber")

    while not shutdown_event.is_set():
        print("reading from stream key:", stream_key)
        read = await r.xread(streams={stream_key:"$"}, count=1, block=0)
        #signal = getattr(strategies.Strategies(), strategy)(read)
        if read:
            signal = "HOLD"
            print("Subsriber worker read:", read)
        else:
            signal = "NO_DATA"
        print(signal)

async def dashboard_subscriber(r:redis.Redis, stream_key:str, consumer_name:str, shutdown_event:asyncio.Event):
    while not shutdown_event.is_set():
        read = await r.xread(streams={stream_key:">"}, count=1)
        print(f"Dashboard received: {read}")

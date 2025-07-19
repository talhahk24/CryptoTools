import redis.asyncio as redis
import asyncio
import logging
import typing

import strategies
import options

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_stream_key(exchange:str, symbol:str, interval:str|None, data_type:str) -> str|None:
    symbol = symbol.lower().replace("/", "")
    if data_type == "kline":
        return f"{exchange}:{symbol}@kline_{interval}"
    elif data_type == "trade":
        return f"{exchange}:{symbol}@trade"
    else:
        return None

def get_consumer_name (consumer_type:options.ConsumerOptions, stream_key:str, id_generator:typing.Generator[int, None, None]) -> str:
    gen_id = next(id_generator)
    return f"{gen_id}-{consumer_type}:{stream_key}_consumer"

async def strategy_subscriber(r:redis.Redis, symbol:options.SymbolOptions, exchange:options.ExchangeOptions,
                              interval:options.TimeFramesOptions|None, data_type:options.DataTypesOptions,
                              strategy:str, shutdown_event:asyncio.Event, id_generator:typing.Generator[int, None, None]):

    stream_key = get_stream_key(exchange, symbol, interval, data_type)
    consumer_name = get_consumer_name(options.ConsumerOptions.STRATEGY, stream_key, id_generator)

    if not stream_key:
        logger.error(f"Unsupported data type: {data_type} called by consumer:{consumer_name}")

    while not shutdown_event.is_set():
        logger.debug(f"{consumer_name} listening to {stream_key}")
        read = await r.xread(streams={stream_key:"$"}, count=1, block=10000)
        if not read:
            logging.debug(f"{consumer_name} got nothing for 10s on {stream_key}")
            continue
        signal = getattr(strategies.Strategies(), strategy)(read)
        logger.info(f"{consumer_name} generated signal: {signal}")

async def dashboard_subscriber(r:redis.Redis, symbol:options.SymbolOptions, exchange:options.ExchangeOptions,
                              interval:options.TimeFramesOptions, data_type:options.DataTypesOptions,
                              consumer_name:str, strategy:str, shutdown_event:asyncio.Event):
    stream_key = get_stream_key(exchange,symbol, interval, data_type)
    while not shutdown_event.is_set():
        logger.debug(f"Dashboard listening to {stream_key}")
        read = await r.xread(streams={stream_key:">"}, count=1)
        ### Call dashboard function here
        logger.debug(f"Dashboard received data: {read}")

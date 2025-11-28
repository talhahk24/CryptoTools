# Async Event-Driven Redis Streams Pipeline

An async Python pipeline that ingests live crypto market data, normalizes it with Pydantic models, and publishes it to Redis Streams for downstream consumers.

## Highlights
- **Async ingestion** from Binance websockets with reconnection and resubscription.
- **Schema validation** via Pydantic models to normalize trade and kline payloads.
- **Redis Streams fan-out** using a lightweight publisher and sample strategy subscriber.
- **Typed configuration** with enums for exchanges, symbols, timeframes, and data types.
- **Demo script** that wires ingestion → validation → Redis publish → consumer logging.

## Architecture
```
Exchange WS (Binance)
    ↓
app/ingestion/ws_connector.py (async listener + subscriptions)
    ↓
asyncio.Queue
    ↓
app/pipeline/publisher.py (validate + normalize)
    ↓
Redis Streams
    ↓
app/subscribers/strategy_consumer.py (example strategy consumer)
```

## Repository Layout
- `app/config/options.py` – enums for exchanges, symbols, timeframes, data types, strategies.
- `app/ingestion/ws_connector.py` – websocket connector with reconnect + resubscribe logic.
- `app/models/binance.py` – Pydantic models for trade/kline payloads.
- `app/pipeline/publisher.py` – validation/normalization and Redis Streams publishing.
- `app/pipeline/redis_client.py` – async Redis client helper.
- `app/subscribers/strategy_consumer.py` – sample consumer that reads from Redis Streams.
- `app/strategies/` – placeholder strategy registry + RSI stub.
- `scripts/demo_pipeline.py` – runnable demo wiring ingestion → publish → consumer.

## Quickstart
1. **Install dependencies** (Python 3.11+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Redis** (local or Docker):
   ```bash
   redis-server
   # or
   docker run -p 6379:6379 redis:alpine
   ```
3. **Start the demo pipeline**:
   ```bash
   python scripts/demo_pipeline.py
   ```
   The script subscribes to BTC/USDT klines (1s) and ETH/USDT trades on Binance, normalizes the payloads, publishes them to Redis Streams, and logs placeholder RSI strategy signals from the consumer.

## Future Extensions
- Add additional exchange connectors and payload mappers.
- Expand strategy implementations and dashboards built on Redis Streams.
- Provide offline replay fixtures for running the pipeline without live market connectivity.

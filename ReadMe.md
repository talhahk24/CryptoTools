# CryptoTools Real-Time Trading System

## Current State
```
WebSocket (Binance) ✅
    ↓
ws_connector.py (with reconnection) ✅
    ↓
Queue ✅
    ↓
publisher.py (validate & normalize) ✅
    ↓
Redis Streams ✅
    ↓
subscribers.py (strategy/dashboard/db workers)
    ↓
[strategies, dashboards, storage[flatfile-->db?]]
```

### Publishing Pipeline (Core - Mostly Complete ✓)
- **ws_connector.py**
  - websocket connection to exchanges
  - robust reconnection logic with exponential backoff + jitter
  - automatic resubscription on connection drops
  - only binance supported currently (other exchanges can be added post-MVP)
  - comprehensive logging throughout
  
- **publisher.py**
  - consumes from websocket queue and publishes to redis streams
  - validates and maps exchange data to normalized format
  - handles kline and trade data
  - error handling and logging
  - data validation using pydantic models

- **redis_client.py**
  - redis client wrapper for initialization
  - simple and clean

### Data Models & Configuration
- **pydantic_models.py**
  - structured models for Binance websocket messages
  - separate models for trade and kline events
  - validation ready (some validators commented out for flexibility)
  
- **options.py**
  - enum classes for all system options
  - exchanges, symbols, timeframes, data types, strategies, consumers
  - easy to extend

### Consumption Pipeline (Work in Progress)
- **subscribers.py**
  - strategy workers implemented (basic structure)
  - dashboard workers scaffolded
    - **needs implementation**
  - database/flatfile workers
    - **not started yet**
  - stream key generation logic complete
  - consumer naming with ID generation
  - logging in place

- **strategies.py**
  - basic strategy framework
  - RSI placeholder (returns signals but no actual logic yet)
    - **needs actual implementation**
  - MACD, BollingerBands mentioned but not coded
    - **needs work**
  - ML strategies architecture needs consideration
    - **need to think how transformation stage can support them naturally**
  - users can add their own strategies here

### API & Orchestration
- **api.py**
  - fastapi app initialized
  - basic health check endpoint
  - strategy execution endpoints scaffolded
    - **(~1% complete, needs major work)**

- **main(temp_testing).py**
  - temporary orchestrator for testing data flow
  - starts websocket connections, publishers, and subscribers
  - demonstrates full pipeline
  - will be replaced/integrated with fastapi app in future

### Logging
- comprehensive logging added throughout:
  - ws_connector: connection events, reconnections, subscriptions
  - publisher: data validation, redis operations, errors
  - subscribers: consumption events, strategy signals
  - all set to DEBUG level for development

## What Works Now
- ✓ Connect to Binance websocket
- ✓ Subscribe to kline/trade streams
- ✓ Handle connection drops and reconnect automatically
- ✓ Validate and normalize data
- ✓ Publish to Redis streams
- ✓ Consume from Redis streams
- ✓ Basic strategy worker framework

## What Needs Work
- Strategy implementations (actual trading logic)
- Dashboard workers (visualization/monitoring)
- Database persistence
- API endpoints (control and monitoring)
- Support for additional exchanges (post-MVP)
- ML strategy architecture decisions

## Architecture
```
WebSocket (Binance) 
    ↓
ws_connector.py (with reconnection)
    ↓
Queue
    ↓
publisher.py (validate & normalize)
    ↓
Redis Streams
    ↓
subscribers.py (strategy/dashboard/db workers)
    ↓
[strategies, dashboards, storage]
```

## Running
```bash
# Start Redis first
redis-server

# Run the test orchestrator
python main(temp_testing).py
```

## Next Steps
1. Implement actual strategy logic
   - RSI calculation and signal generation
   - MACD implementation
   - Bollinger Bands implementation
   - Figure out ML strategy architecture (data transformation pipeline)
2. Build out API endpoints
   - Start/stop strategy workers
   - Subscribe/unsubscribe to symbols
   - Get active strategies status
   - System health/monitoring endpoints
3. Add flatfile persistence workers
   - Save streams to parquet files (for MVP)
   - Implement rotation/archival logic
   - (Later) Add database support post-MVP
4. Dashboard workers for real-time monitoring
   - Stream data to frontend/dashboard
   - Aggregate metrics
5. (Post-MVP) Support additional exchanges
   - Add exchange-specific data mapping
   - Update publisher validation logic

import json
import pandas as pd
import datetime
import config
import strategies
from binance.client import Client, BinanceAPIException
from binance.enums import *
import requests
import keys
import websocket
import ssl 
import config
import psutil
import ta
from mcp.server.fastmcp import FastMCP
import threading
import uuid
import threading


data_lock = threading.Lock()

mcp = FastMCP("trading_agent")

# Global dictionaries to manage multiple strategies
active_strategies = {}  # Keeps track of all running strategies
websocket_connections = {}  # Manages websocket connections (pair+interval -> connection)
data_frames = {}  # Stores dataframes for each pair+interval combination
positions = {}  # Tracks positions for each trading pair

MAX_CANDLES = 100  # Maximum candles to store

client = Client(keys.API_KEY, keys.API_SECRET, tld="com")

@mcp.tool()
def get_external_ip():
    try:
        response = requests.get("https://api.ipify.org")
        return {"External IP": response.text}
    except Exception as e:
        return {"Failed to get IP": str(e)}

@mcp.tool()
def test_binance_connectivity():
    try:
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        if response.status_code == 200:
            return {"Ping successful": True}
        else:
            return {"Ping failed with status": response.status_code}
    except Exception as e:
        return {"Ping failed": str(e)}

@mcp.tool()
def read_binance_account():
    try:
        response = client.get_account()
        return {"Connection successful": response}
    except BinanceAPIException as e:
        return {"Connection failed": f"Binance API error: {str(e)}"}
    except Exception as e:
        return {"Connection failed": str(e)}

@mcp.tool()
def list_active_strategies():
    """Returns a list of all currently active trading strategies"""
    strategies_info = []
    
    for strategy_id, strategy in active_strategies.items():
        strategies_info.append({
            "id": strategy_id,
            "type": strategy["type"],
            "symbol": strategy["symbol"],
            "interval": strategy["interval"],
            "parameters": strategy["parameters"],
            "start_time": strategy["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        })
    
    if not strategies_info:
        return {"status": "info", "message": "No active strategies"}
    
    return {"status": "success", "active_strategies": strategies_info}

def generate_strategy_id():
    """Generates a unique ID for a strategy"""
    return str(uuid.uuid4())[:8]

@mcp.tool()
def start_RSI_strategy(symbol="ETHUSDT", interval="1m", RSI_period=14, RSI_overbought=60, RSI_oversold=40):
    strategy_type = "RSI"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "RSI_period": RSI_period,
            "RSI_overbought": RSI_overbought,
            "RSI_oversold": RSI_oversold
        }
    )

@mcp.tool()
def start_MACD_strategy(symbol="ETHUSDT", interval="1m", MACD_fast_period=12, MACD_slow_period=26, MACD_signal_period=9):
    strategy_type = "MACD"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "MACD_fast_period": MACD_fast_period,
            "MACD_slow_period": MACD_slow_period,
            "MACD_signal_period": MACD_signal_period
        }
    )

@mcp.tool()
def start_Bollinger_Bands_strategy(symbol="ETHUSDT", interval="1m", BB_period=20, BB_std_dev=2):
    strategy_type = "Bollinger Bands"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "BB_period": BB_period,
            "BB_std_dev": BB_std_dev
        }
    )

@mcp.tool()
def start_EMA_Cross_strategy(symbol="ETHUSDT", interval="1m", EMA_fast_period=9, EMA_slow_period=21):
    strategy_type = "EMA Cross"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "EMA_fast_period": EMA_fast_period,
            "EMA_slow_period": EMA_slow_period
        }
    )

@mcp.tool()
def start_Ichimoku_Cloud_strategy(symbol="ETHUSDT", interval="1m", Ichimoku_conversion_period=9, Ichimoku_base_period=26, 
                               Ichimoku_span_b_period=52, Ichimoku_displacement=26):
    strategy_type = "Ichimoku Cloud"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "Ichimoku_conversion_period": Ichimoku_conversion_period,
            "Ichimoku_base_period": Ichimoku_base_period,
            "Ichimoku_span_b_period": Ichimoku_span_b_period,
            "Ichimoku_displacement": Ichimoku_displacement
        }
    )

@mcp.tool()
def start_VWAP_strategy(symbol="ETHUSDT", interval="1m", VWAP_period=14):
    strategy_type = "VWAP"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "VWAP_period": VWAP_period
        }
    )

@mcp.tool()
def start_Support_Resistance_strategy(symbol="ETHUSDT", interval="1m", SR_period=14, SR_threshold=0.05):
    strategy_type = "Support Resistance"
    return start_strategy(
        strategy_type=strategy_type,
        symbol=symbol,
        interval=interval,
        parameters={
            "SR_period": SR_period,
            "SR_threshold": SR_threshold
        }
    )

def start_strategy(strategy_type, symbol, interval, parameters):
    """
    Generic function to start any strategy
    
    Parameters:
    strategy_type (str): Type of strategy (RSI, MACD, etc.)
    symbol (str): Trading pair symbol
    interval (str): Candle interval
    parameters (dict): Strategy-specific parameters
    
    Returns:
    dict: Status of the operation
    """
    global active_strategies, websocket_connections
    
    # Standardize inputs
    symbol = symbol.upper()
    interval = str(interval).lower()
    
    # Generate a unique ID for this strategy instance
    strategy_id = generate_strategy_id()
    
    # Create connection key (used to determine if we need a new WebSocket)
    conn_key = f"{symbol.lower()}_{interval}"
    
    # Initialize positions tracking if needed
    if symbol not in positions:
        positions[symbol] = {
            "in_buy_position": False,
            "in_sell_position": False,
            "position_size": 0
        }
    
    # Create strategy record
    active_strategies[strategy_id] = {
        "id": strategy_id,
        "type": strategy_type,
        "symbol": symbol,
        "interval": interval,
        "parameters": parameters,
        "start_time": datetime.datetime.now(),
        "conn_key": conn_key
    }
    
    # Check if we need to create a new WebSocket or reuse existing
    if conn_key not in websocket_connections:
        # Initialize price data for this connection
        data_frames[conn_key] = {
            "opens": [],
            "highs": [],
            "lows": [],
            "closes": [],
            "volumes": [],
            "times": [],
            "df": pd.DataFrame()
        }
        
        # Fetch historical data
        fetch_historical_candles(symbol, interval, conn_key)
        
        # Start WebSocket connection
        establish_websocket_connection(symbol, interval, conn_key)
    
    return {
        "status": "success", 
        "message": f"Started {strategy_type} strategy on {symbol} with {interval} interval",
        "strategy_id": strategy_id
    }

def establish_websocket_connection(symbol, interval, conn_key):
    """
    Establish a WebSocket connection for a specific symbol and interval
    
    Parameters:
    symbol (str): Trading pair symbol
    interval (str): Candle interval
    conn_key (str): Unique key for this connection
    """
    strmSym = symbol.lower()
    strmInt = interval.lower()
    
    SOCKET = f"wss://stream.binance.com:9443/ws/{strmSym}@kline_{strmInt}"
    
    # Create WebSocket app with connection-specific callbacks
    def on_message_wrapper(ws, message):
        on_message(ws, message, conn_key)
    
    def on_open_wrapper(ws):
        on_open(ws, conn_key)
    
    def on_error_wrapper(ws, error):
        on_error(ws, error, conn_key)
    
    def on_close_wrapper(ws, close_status_code, close_msg):
        on_close(ws, close_status_code, close_msg, conn_key)
    
    ws = websocket.WebSocketApp(
        SOCKET,
        on_open=on_open_wrapper,
        on_message=on_message_wrapper,
        on_error=on_error_wrapper,
        on_close=on_close_wrapper
    )
    
    # Store the connection
    websocket_connections[conn_key] = {
        "ws": ws,
        "symbol": symbol,
        "interval": interval
    }
    
    # Start WebSocket in background thread
    def run_websocket():
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    thread = threading.Thread(target=run_websocket)
    thread.daemon = True
    thread.start()
    
    print(f"Started WebSocket connection for {symbol} {interval}")
    
    return ws

def on_open(ws, conn_key):
    print(f"WebSocket opened for {conn_key}")

# def on_close(ws, close_status_code, close_msg, conn_key):
#     print(f"WebSocket closed for {conn_key}: {close_status_code} - {close_msg}")
    
#     # Clean up resources
#     if conn_key in websocket_connections:
#         del websocket_connections[conn_key]
    
#     # Remove strategies using this connection
#     strategies_to_remove = []
#     for strategy_id, strategy in active_strategies.items():
#         if strategy["conn_key"] == conn_key:
#             strategies_to_remove.append(strategy_id)
    
#     for strategy_id in strategies_to_remove:
#         del active_strategies[strategy_id]

def on_close(ws, close_status_code, close_msg, conn_key):
    with data_lock:
        # Only cleanup if not already handled by stop_strategy
        if conn_key in websocket_connections:
            del websocket_connections[conn_key]
            
        # Remove orphaned strategies (if any)
        strategies_to_remove = [
            s_id for s_id, s in active_strategies.items() 
            if s["conn_key"] == conn_key
        ]
        for s_id in strategies_to_remove:
            del active_strategies[s_id]

def on_error(ws, error, conn_key):
    print(f"WebSocket error for {conn_key}: {error}")

def on_message(ws, message, conn_key):
    """Process incoming WebSocket message"""
    if conn_key not in data_frames:
        print(f"Error: No data frame for {conn_key}")
        return
    
    data = data_frames[conn_key]
    
    json_message = json.loads(message)
    if 'k' in json_message:
        candle = json_message['k']
        
        # Extract candle data
        is_candle_closed = candle['x']
        close = float(candle['c'])
        high = float(candle['h'])
        low = float(candle['l'])
        open_price = float(candle['o'])
        volume = float(candle['v'])
        candle_time = candle['t']
        
        # Only process closed candles
        if is_candle_closed:
            print(f"New candle closed at {close} for {conn_key}")
            data["closes"].append(close)
            data["highs"].append(high)
            data["lows"].append(low)
            data["opens"].append(open_price)
            data["volumes"].append(volume)
            data["times"].append(candle_time)
            
            # Limit data size
            if len(data["closes"]) > MAX_CANDLES:
                data["closes"] = data["closes"][-MAX_CANDLES:]
                data["highs"] = data["highs"][-MAX_CANDLES:]
                data["lows"] = data["lows"][-MAX_CANDLES:]
                data["opens"] = data["opens"][-MAX_CANDLES:]
                data["volumes"] = data["volumes"][-MAX_CANDLES:]
                data["times"] = data["times"][-MAX_CANDLES:]
            
            # Update dataframe
            data["df"] = create_dataframe(data)
            
            # Process all strategies using this connection
            for strategy_id, strategy in active_strategies.items():
                if strategy["conn_key"] == conn_key:
                    process_strategy(strategy_id, data["df"])

def create_dataframe(data):
    """Create a DataFrame from OHLCV data"""
    df = pd.DataFrame({
        'open': data["opens"],
        'high': data["highs"],
        'low': data["lows"],
        'close': data["closes"],
        'volume': data["volumes"],
        'time': data["times"]
    })
    
    # Convert timestamp to datetime
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    
    return df

def fetch_historical_candles(symbol, interval, conn_key, limit=MAX_CANDLES):
    """Fetch historical candles from Binance API"""
    if conn_key not in data_frames:
        data_frames[conn_key] = {
            "opens": [],
            "highs": [],
            "lows": [],
            "closes": [],
            "volumes": [],
            "times": [],
            "df": pd.DataFrame()
        }
    
    data = data_frames[conn_key]
    
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        klines = response.json()
        
        # Clear existing data and add new data
        data["opens"].clear()
        data["highs"].clear()
        data["lows"].clear()
        data["closes"].clear()
        data["volumes"].clear()
        data["times"].clear()
        
        for kline in klines:
            data["opens"].append(float(kline[1]))
            data["highs"].append(float(kline[2]))
            data["lows"].append(float(kline[3]))
            data["closes"].append(float(kline[4]))
            data["volumes"].append(float(kline[5]))
            data["times"].append(kline[0])
        
        print(f"Fetched {len(klines)} historical candles for {symbol} {interval}")
        
        # Create DataFrame
        data["df"] = create_dataframe(data)
    except Exception as e:
        print(f"Error fetching historical data: {e}")

def process_strategy(strategy_id, df):
    """Process a specific strategy with the latest data"""
    if strategy_id not in active_strategies:
        print(f"Strategy {strategy_id} not found")
        return
    
    strategy = active_strategies[strategy_id]
    signal = run_strategy(strategy["type"], df, strategy["symbol"], strategy["parameters"])
    
    # Log signal
    log_signal(signal, strategy_id)
    
    # Execute trade if appropriate
    if signal["action"] in ["BUY", "SELL"]:
        execute_trade(signal, strategy["symbol"])
    
    return signal

def run_strategy(strategy_type, df, symbol, parameters):
    """Run a specific trading strategy with parameters"""
    if strategy_type == 'RSI':
        return strategies.rsi_strategy(
            df, symbol,
            period=parameters.get("RSI_period", 14),
            overbought=parameters.get("RSI_overbought", 70),
            oversold=parameters.get("RSI_oversold", 30)
        )
    
    elif strategy_type == 'MACD':
        return strategies.macd_strategy(
            df, symbol,
            fast_period=parameters.get("MACD_fast_period", 12),
            slow_period=parameters.get("MACD_slow_period", 26),
            signal_period=parameters.get("MACD_signal_period", 9)
        )
    
    elif strategy_type == 'Bollinger Bands':
        return strategies.bollinger_bands_strategy(
            df, symbol,
            period=parameters.get("BB_period", 20),
            std_dev=parameters.get("BB_std_dev", 2)
        )
    
    elif strategy_type == 'EMA Cross':
        return strategies.ema_cross_strategy(
            df, symbol,
            fast_period=parameters.get("EMA_fast_period", 9),
            slow_period=parameters.get("EMA_slow_period", 21)
        )
    
    elif strategy_type == 'Ichimoku Cloud':
        return strategies.ichimoku_cloud_strategy(
            df, symbol,
            conversion_period=parameters.get("Ichimoku_conversion_period", 9),
            base_period=parameters.get("Ichimoku_base_period", 26),
            span_b_period=parameters.get("Ichimoku_span_b_period", 52),
            displacement=parameters.get("Ichimoku_displacement", 26)
        )
    
    elif strategy_type == 'VWAP':
        return strategies.vwap_strategy(
            df, symbol,
            period=parameters.get("VWAP_period", 14)
        )
    
    elif strategy_type == 'Support Resistance':
        return strategies.support_resistance_strategy(
            df, symbol,
            period=parameters.get("SR_period", 14),
            threshold=parameters.get("SR_threshold", 0.05)
        )
    
    else:
        return {
            "action": "ERROR",
            "symbol": symbol,
            "strategy": strategy_type,
            "message": f"Strategy '{strategy_type}' not found"
        }

def execute_trade(signal, symbol):
    """Execute a trade based on the signal"""
    if not hasattr(config, 'ENABLE_TRADING') or not config.ENABLE_TRADING:
        print(f"Trading disabled. Signal would not execute: {signal['action']} {signal['symbol']}")
        return
    
    # Get trading parameters
    action = signal['action']
    quantity = config.TRADE_QUANTITY
    
    # Get position information
    pos = positions.get(symbol, {
        "in_buy_position": False,
        "in_sell_position": False,
        "position_size": 0
    })
    
    account_data = get_account_status(symbol)
    
    try:
        if action == "BUY":
            if not pos["in_buy_position"]:
                if account_data['quote_balance'] > config.TRADE_QUANTITY:
                    order = client.create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    print(f"BUY ORDER EXECUTED: {order}")
                    pos["in_buy_position"] = True
                    pos["in_sell_position"] = False
                    pos["position_size"] += quantity
                    
                    # Update positions dictionary
                    positions[symbol] = pos
                else:
                    print(f"Insufficient balance to execute buy order. Available: {account_data['quote_balance']}, Required: {config.TRADE_QUANTITY}")
            else:
                print("Signal to BUY, but already in BUY Position")
        
        elif action == "SELL":
            if not pos["in_sell_position"]:
                if account_data['base_balance'] > config.TRADE_QUANTITY:
                    order = client.create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    print(f"SELL ORDER EXECUTED: {order}")
                    pos["in_sell_position"] = True
                    pos["in_buy_position"] = False
                    pos["position_size"] -= quantity
                    
                    # Update positions dictionary
                    positions[symbol] = pos
                else:
                    print(f"Insufficient balance to execute sell order. Available: {account_data['base_balance']}, Required: {config.TRADE_QUANTITY}")
            else:
                print("Signal to SELL, but already in SELL Position")
    except Exception as e:
        print(f"Error executing trade: {e}")


@mcp.tool()
def stop_strategy(strategy_id: str, liquidate: bool = False):
    global active_strategies, websocket_connections, positions
    with data_lock:
        if strategy_id not in active_strategies:
            return {"status": "error", "message": f"Strategy {strategy_id} not found"}
        
        strategy = active_strategies.pop(strategy_id)  # Atomic removal
        conn_key = strategy["conn_key"]
        symbol = strategy["symbol"]

        # Check if other strategies use this conn_key
        other_strategies = [s for s in active_strategies.values() if s["conn_key"] == conn_key]
        if not other_strategies:
            # Close WebSocket if it exists
            if conn_key in websocket_connections:
                ws = websocket_connections[conn_key]["ws"]
                ws.close()  # This will trigger on_close
                del websocket_connections[conn_key]
    
    # Liquidate positions if requested
    if liquidate and symbol in positions and positions[symbol]["position_size"] > 0:
        try:
            quantity = positions[symbol]["position_size"]
            order = client.create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            print(f"LIQUIDATION SELL ORDER EXECUTED: {order}")
            positions[symbol]["position_size"] = 0
            positions[symbol]["in_buy_position"] = False
            positions[symbol]["in_sell_position"] = False
            
            return {"status": "success", "message": f"Strategy {strategy_id} stopped and positions liquidated"}
        except Exception as e:
            return {"status": "error", "message": f"Strategy stopped but failed to liquidate: {str(e)}"}
    
    return {"status": "success", "message": f"Strategy {strategy_id} stopped"}

@mcp.tool()
def stop_all_strategies(liquidate=False):
    """Stop all active strategies atomically"""
    global active_strategies, websocket_connections, positions
    
    with data_lock:  # Acquire lock for atomic operations
        if not active_strategies:
            return {"status": "info", "message": "No active strategies to stop"}
        
        # Group strategies by conn_key to manage WebSockets efficiently
        strategies_by_conn = {}
        for strategy_id, strategy in list(active_strategies.items()):
            conn_key = strategy["conn_key"]
            if conn_key not in strategies_by_conn:
                strategies_by_conn[conn_key] = []
            strategies_by_conn[conn_key].append(strategy_id)
        
        # Remove all strategies first
        stopped_strategies = list(active_strategies.values())
        active_strategies.clear()  # Remove all strategies at once
        
        # Close WebSockets that are no longer needed
        for conn_key in strategies_by_conn:
            if conn_key in websocket_connections:
                ws = websocket_connections[conn_key]["ws"]
                ws.close()  # Trigger WebSocket closure
                del websocket_connections[conn_key]  # Remove from tracking
        
        # Liquidate positions if requested
        liquidation_results = []
        if liquidate:
            for strategy in stopped_strategies:
                symbol = strategy["symbol"]
                if symbol in positions and positions[symbol]["position_size"] > 0:
                    try:
                        quantity = positions[symbol]["position_size"]
                        order = client.create_order(
                            symbol=symbol,
                            side=SIDE_SELL,
                            type=ORDER_TYPE_MARKET,
                            quantity=quantity
                        )
                        positions[symbol]["position_size"] = 0
                        liquidation_results.append({
                            "symbol": symbol,
                            "status": "liquidated",
                            "order": order
                        })
                    except Exception as e:
                        liquidation_results.append({
                            "symbol": symbol,
                            "status": "error",
                            "message": str(e)
                        })
        
        return {
            "status": "success",
            "stopped_strategies": len(stopped_strategies),
            "liquidated_positions": liquidation_results
        }

def get_account_status(symbol):
    """Get account status including balances and PnL"""
    try:
        # Split symbol to get base and quote assets
        quote_asset = 'USDT'  # Default
        base_asset = symbol.replace(quote_asset, '')
        
        # Get current price
        conn_key = f"{symbol.lower()}_{active_strategies[list(active_strategies.keys())[0]]['interval']}"
        if conn_key in data_frames and not data_frames[conn_key]["df"].empty:
            current_price = data_frames[conn_key]["df"]['close'].iloc[-1]
        else:
            ticker = client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
        
        # Get account info
        account_info = client.get_account()
        
        # Find balances
        quote_balance = next((float(asset['free']) + float(asset['locked']) 
                           for asset in account_info['balances'] if asset['asset'] == quote_asset), 0.0)
        base_balance = next((float(asset['free']) + float(asset['locked']) 
                          for asset in account_info['balances'] if asset['asset'] == base_asset), 0.0)
        
        total_value = quote_balance + (base_balance * current_price)
        
        # Get trades
        trades = client.get_my_trades(symbol=symbol)
        buy_trades = [t for t in trades if t['isBuyer']]
        sell_trades = [t for t in trades if not t['isBuyer']]
        
        # Calculate PnL
        total_buy_qty = sum(float(t['qty']) for t in buy_trades)
        total_buy_cost = sum(float(t['quoteQty']) for t in buy_trades)
        avg_buy_price = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0
        
        unrealized_pnl = (current_price - avg_buy_price) * base_balance if avg_buy_price > 0 else 0
        unrealized_pnl_pct = (unrealized_pnl / (avg_buy_price * base_balance)) * 100 if avg_buy_price > 0 and base_balance > 0 else 0
        
        realized_pnl = sum((float(t['price']) - avg_buy_price) * float(t['qty']) for t in sell_trades) if avg_buy_price > 0 else 0
        total_pnl = unrealized_pnl + realized_pnl
        
        # Recent transactions
        transactions = []
        for trade in reversed(trades[-5:]):
            transactions.append({
                'time': datetime.datetime.fromtimestamp(trade['time']/1000).strftime("%Y-%m-%d %H:%M"),
                'side': 'BUY' if trade['isBuyer'] else 'SELL',
                'qty': float(trade['qty']),
                'price': float(trade['price']),
                'value': float(trade['quoteQty'])
            })
        
        return {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'current_price': current_price,
            'quote_asset': quote_asset,
            'base_asset': base_asset,
            'quote_balance': quote_balance,
            'base_balance': base_balance,
            'total_value': total_value,
            'avg_buy_price': avg_buy_price,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct,
            'realized_pnl': realized_pnl,
            'total_pnl': total_pnl,
            'transactions': transactions
        }
    except Exception as e:
        print(f"Error getting account status: {e}")
        return {
            'quote_balance': 0,
            'base_balance': 0
        }

def log_signal(signal, strategy_id):
    """Log trading signal with strategy ID"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    strategy_type = active_strategies[strategy_id]["type"] if strategy_id in active_strategies else "Unknown"
    signal_message = f"[{timestamp}] [Strategy {strategy_id} - {strategy_type}] {signal['action']}: {signal['message']}"
    
    print(signal_message)
    
    # Log to file
    if hasattr(config, 'LOG_FILE') and config.LOG_FILE:
        try:
            with open(config.LOG_FILE, 'a') as f:
                f.write(signal_message + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")


@mcp.tool()                                      
def get_strategy_performance(strategy_id=None):
    """Get performance metrics for strategies"""
    if strategy_id and strategy_id not in active_strategies:
        return {"status": "error", "message": f"Strategy {strategy_id} not found"}
    
    performance = []
    
    # If strategy_id is provided, only get that one
    strategy_ids = [strategy_id] if strategy_id else active_strategies.keys()
    
    for s_id in strategy_ids:
        if s_id not in active_strategies:
            continue
            
        strategy = active_strategies[s_id]
        symbol = strategy["symbol"]
        strategy_type = strategy["type"]
        
        # Get account data for this symbol
        account_data = get_account_status(symbol)
        
        # Calculate runtime
        runtime = datetime.datetime.now() - strategy["start_time"]
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        
        # Get current position
        pos = positions.get(symbol, {
            "in_buy_position": False,
            "in_sell_position": False,
            "position_size": 0
        })
        
        performance.append({
            "strategy_id": s_id,
            "type": strategy_type,
            "symbol": symbol,
            "runtime": runtime_str,
            "current_price": account_data["current_price"],
            "position": "BUY" if pos["in_buy_position"] else "SELL" if pos["in_sell_position"] else "NONE",
            "position_size": pos["position_size"],
            "unrealized_pnl": account_data["unrealized_pnl"],
            "unrealized_pnl_pct": account_data["unrealized_pnl_pct"],
            "realized_pnl": account_data["realized_pnl"],
            "total_pnl": account_data["total_pnl"],
            "parameters": strategy["parameters"]
        })
    
    return {"status": "success", "performance": performance}

@mcp.tool()
def get_system_status():
    """Get system status information"""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get active connections
        active_connections = len(websocket_connections)
        
        # Get number of active strategies
        num_strategies = len(active_strategies)
        
        # Get dataframe sizes
        df_sizes = {conn_key: len(data["df"]) for conn_key, data in data_frames.items()}
        
        # Get Binance API status
        binance_status = test_binance_connectivity()
        
        # Get account balances
        account_balances = {}
        try:
            account_info = client.get_account()
            for asset in account_info['balances']:
                if float(asset['free']) > 0 or float(asset['locked']) > 0:
                    account_balances[asset['asset']] = {
                        'free': float(asset['free']),
                        'locked': float(asset['locked']),
                        'total': float(asset['free']) + float(asset['locked'])
                    }
        except Exception as e:
            account_balances = {"error": str(e)}
        
        return {
            "status": "success",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "process_uptime": str(datetime.datetime.now() - process_start_time).split('.')[0]
            },
            "trading_bot": {
                "active_connections": active_connections,
                "active_strategies": num_strategies,
                "dataframe_sizes": df_sizes
            },
            "binance": binance_status,
            "account_balances": account_balances
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_market_overview():
    """Get market overview for major cryptocurrencies"""
    try:
        # Define major cryptocurrencies to check
        major_cryptos = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "SOLUSDT"]
        
        # Get tickers for all symbols
        all_tickers = client.get_ticker()
        
        # Filter for major cryptos and get 24h stats
        crypto_stats = []
        for ticker in all_tickers:
            if ticker['symbol'] in major_cryptos:
                price_change_percent = float(ticker['priceChangePercent'])
                crypto_stats.append({
                    "symbol": ticker['symbol'],
                    "price": float(ticker['lastPrice']),
                    "price_change_24h": float(ticker['priceChange']),
                    "price_change_percent_24h": price_change_percent,
                    "volume_24h": float(ticker['volume']),
                    "high_24h": float(ticker['highPrice']),
                    "low_24h": float(ticker['lowPrice']),
                    "trend": "UP" if price_change_percent > 0 else "DOWN"
                })
        
        # Sort by market cap (approximated by price * volume)
        crypto_stats.sort(key=lambda x: x['price'] * x['volume_24h'], reverse=True)
        
        return {
            "status": "success",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_data": crypto_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_detailed_strategy_data(strategy_id):
    """Get detailed data for a specific strategy including charts data"""
    if strategy_id not in active_strategies:
        return {"status": "error", "message": f"Strategy {strategy_id} not found"}
    
    strategy = active_strategies[strategy_id]
    conn_key = strategy["conn_key"]
    
    if conn_key not in data_frames or data_frames[conn_key]["df"].empty:
        return {"status": "error", "message": "No data available for this strategy"}
    
    df = data_frames[conn_key]["df"].copy()
    
    # Get technical indicators based on strategy type
    indicators = {}
    
    if strategy["type"] == "RSI":
        period = strategy["parameters"]["RSI_period"]
        df[f'RSI_{period}'] = ta.momentum.RSIIndicator(df['close'], window=period).rsi()
        indicators["RSI"] = df[f'RSI_{period}'].dropna().tolist()[-20:]  # Last 20 values
    
    elif strategy["type"] == "MACD":
        fast = strategy["parameters"]["MACD_fast_period"]
        slow = strategy["parameters"]["MACD_slow_period"]
        signal = strategy["parameters"]["MACD_signal_period"]
        
        macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        indicators["MACD"] = df['MACD'].dropna().tolist()[-20:]
        indicators["MACD_signal"] = df['MACD_signal'].dropna().tolist()[-20:]
        indicators["MACD_diff"] = df['MACD_diff'].dropna().tolist()[-20:]
    
    elif strategy["type"] == "Bollinger Bands":
        period = strategy["parameters"]["BB_period"]
        std_dev = strategy["parameters"]["BB_std_dev"]
        
        bollinger = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std_dev)
        df['BB_upper'] = bollinger.bollinger_hband()
        df['BB_middle'] = bollinger.bollinger_mavg()
        df['BB_lower'] = bollinger.bollinger_lband()
        
        indicators["BB_upper"] = df['BB_upper'].dropna().tolist()[-20:]
        indicators["BB_middle"] = df['BB_middle'].dropna().tolist()[-20:]
        indicators["BB_lower"] = df['BB_lower'].dropna().tolist()[-20:]
    
    elif strategy["type"] == "EMA Cross":
        fast = strategy["parameters"]["EMA_fast_period"]
        slow = strategy["parameters"]["EMA_slow_period"]
        
        df[f'EMA_{fast}'] = ta.trend.EMAIndicator(df['close'], window=fast).ema_indicator()
        df[f'EMA_{slow}'] = ta.trend.EMAIndicator(df['close'], window=slow).ema_indicator()
        
        indicators[f"EMA_{fast}"] = df[f'EMA_{fast}'].dropna().tolist()[-20:]
        indicators[f"EMA_{slow}"] = df[f'EMA_{slow}'].dropna().tolist()[-20:]
    
    # Prepare OHLCV data for charting
    candles = []
    times = df['time'].astype(str).tolist()[-50:]  # Last 50 candles
    
    for i in range(-50, 0):
        if i + len(df) >= 0:  # Ensure we don't go out of bounds
            idx = i + len(df)
            candles.append({
                'time': times[i],
                'open': df['open'].iloc[idx],
                'high': df['high'].iloc[idx],
                'low': df['low'].iloc[idx],
                'close': df['close'].iloc[idx],
                'volume': df['volume'].iloc[idx]
            })
    
    # Get performance data for this strategy
    performance = get_strategy_performance(strategy_id)
    
    return {
        "status": "success",
        "strategy_info": {
            "id": strategy_id,
            "type": strategy["type"],
            "symbol": strategy["symbol"],
            "interval": strategy["interval"],
            "parameters": strategy["parameters"],
            "start_time": strategy["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        },
        "performance": performance,
        "chart_data": {
            "candles": candles,
            "indicators": indicators
        }
    }

@mcp.tool()
def get_available_symbols():
    """Get available trading symbols from Binance"""
    try:
        exchange_info = client.get_exchange_info()
        symbols = []
        
        # Filter for USDT pairs that are currently trading
        for symbol_info in exchange_info['symbols']:
            if symbol_info['quoteAsset'] == 'USDT' and symbol_info['status'] == 'TRADING':
                symbols.append({
                    'symbol': symbol_info['symbol'],
                    'baseAsset': symbol_info['baseAsset'],
                    'quoteAsset': symbol_info['quoteAsset']
                })
        
        # Sort by symbol name
        symbols.sort(key=lambda x: x['symbol'])
        
        return {
            "status": "success",
            "symbols": symbols
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def update_strategy_parameters(strategy_id, parameters=None):
    """Update parameters for an existing strategy"""
    if strategy_id not in active_strategies:
        return {"status": "error", "message": f"Strategy {strategy_id} not found"}
    
    if not parameters:
        return {"status": "error", "message": "No parameters provided"}
    
    strategy = active_strategies[strategy_id]
    strategy_type = strategy["type"]
    
    # Validate parameters based on strategy type
    if strategy_type == "RSI":
        valid_params = ["RSI_period", "RSI_overbought", "RSI_oversold"]
    elif strategy_type == "MACD":
        valid_params = ["MACD_fast_period", "MACD_slow_period", "MACD_signal_period"]
    elif strategy_type == "Bollinger Bands":
        valid_params = ["BB_period", "BB_std_dev"]
    elif strategy_type == "EMA Cross":
        valid_params = ["EMA_fast_period", "EMA_slow_period"]
    elif strategy_type == "Ichimoku Cloud":
        valid_params = ["Ichimoku_conversion_period", "Ichimoku_base_period", 
                      "Ichimoku_span_b_period", "Ichimoku_displacement"]
    elif strategy_type == "VWAP":
        valid_params = ["VWAP_period"]
    elif strategy_type == "Support Resistance":
        valid_params = ["SR_period", "SR_threshold"]
    else:
        return {"status": "error", "message": f"Unknown strategy type: {strategy_type}"}
    
    # Update valid parameters
    updated_params = {}
    for param, value in parameters.items():
        if param in valid_params:
            active_strategies[strategy_id]["parameters"][param] = value
            updated_params[param] = value
    
    if not updated_params:
        return {"status": "error", "message": "No valid parameters to update"}
    
    return {
        "status": "success", 
        "message": f"Updated parameters for strategy {strategy_id}",
        "updated_parameters": updated_params
    }

@mcp.tool()
def get_signal_history(strategy_id=None, limit=20):
    """Get trading signal history for strategies"""
    if strategy_id and strategy_id not in active_strategies:
        return {"status": "error", "message": f"Strategy {strategy_id} not found"}
    
    # This would be implemented with a proper signal history storage system
    # For now, we'll return a placeholder message
    
    return {
        "status": "info",
        "message": "Signal history functionality requires implementing a database or log parser. Please check the logs for signal history."
    }

@mcp.tool()
def backtest_strategy(strategy_type, symbol, interval, parameters, days=30):
    """Backtest a strategy with historical data"""
    try:
        # Fetch historical data
        end_time = int(datetime.datetime.now().timestamp() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)  # days back in milliseconds
        
        url = "https://api.binance.com/api/v3/klines"
        klines = []
        
        # We may need to fetch in batches due to API limits
        current_start = start_time
        while current_start < end_time:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'startTime': current_start,
                'endTime': end_time,
                'limit': 1000  # Max limit per request
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            batch = response.json()
            
            if not batch:
                break
                
            klines.extend(batch)
            
            # Update start time for next batch
            current_start = batch[-1][0] + 1
        
        # Create DataFrame
        df = pd.DataFrame(klines, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert types
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Apply strategy
        signals = []
        in_buy_position = False
        in_sell_position = False
        
        # Run strategy on each candle
        for i in range(max(100, len(df) // 10), len(df)):  # Skip the first few candles for indicator warmup
            temp_df = df.iloc[:i+1].copy()  # Include all data up to this point
            
            signal = run_strategy(strategy_type, temp_df, symbol, parameters)
            
            # Track positions and simulated trades
            if signal["action"] == "BUY" and not in_buy_position:
                in_buy_position = True
                in_sell_position = False
                signals.append({
                    "time": temp_df['time'].iloc[-1].strftime("%Y-%m-%d %H:%M:%S"),
                    "price": temp_df['close'].iloc[-1],
                    "action": "BUY",
                    "message": signal["message"]
                })
            elif signal["action"] == "SELL" and not in_sell_position:
                in_sell_position = True
                in_buy_position = False
                signals.append({
                    "time": temp_df['time'].iloc[-1].strftime("%Y-%m-%d %H:%M:%S"),
                    "price": temp_df['close'].iloc[-1],
                    "action": "SELL",
                    "message": signal["message"]
                })
        
        # Calculate basic backtest metrics
        if signals:
            buy_signals = [s for s in signals if s["action"] == "BUY"]
            sell_signals = [s for s in signals if s["action"] == "SELL"]
            
            # Calculate returns (simplified)
            trades = []
            buy_price = None
            
            for signal in signals:
                if signal["action"] == "BUY":
                    buy_price = signal["price"]
                elif signal["action"] == "SELL" and buy_price is not None:
                    sell_price = signal["price"]
                    profit_pct = ((sell_price - buy_price) / buy_price) * 100
                    trades.append({
                        "buy_time": next(s["time"] for s in signals if s["action"] == "BUY" and s["price"] == buy_price),
                        "buy_price": buy_price,
                        "sell_time": signal["time"],
                        "sell_price": sell_price,
                        "profit_pct": profit_pct
                    })
                    buy_price = None
            
            # If we have an open position at the end
            if buy_price is not None:
                last_price = df['close'].iloc[-1]
                profit_pct = ((last_price - buy_price) / buy_price) * 100
                trades.append({
                    "buy_time": next(s["time"] for s in signals if s["action"] == "BUY" and s["price"] == buy_price),
                    "buy_price": buy_price,
                    "sell_time": "OPEN",
                    "sell_price": last_price,
                    "profit_pct": profit_pct
                })
            
            # Calculate performance metrics
            total_trades = len(trades)
            profitable_trades = len([t for t in trades if t["profit_pct"] > 0])
            total_profit_pct = sum(t["profit_pct"] for t in trades)
            avg_profit_pct = total_profit_pct / total_trades if total_trades > 0 else 0
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            
            return {
                "status": "success",
                "backtest_results": {
                    "symbol": symbol,
                    "strategy": strategy_type,
                    "interval": interval,
                    "parameters": parameters,
                    "period": f"{days} days",
                    "start_date": df['time'].iloc[0].strftime("%Y-%m-%d"),
                    "end_date": df['time'].iloc[-1].strftime("%Y-%m-%d"),
                    "metrics": {
                        "total_trades": total_trades,
                        "profitable_trades": profitable_trades,
                        "win_rate": win_rate,
                        "total_profit_pct": total_profit_pct,
                        "avg_profit_pct": avg_profit_pct
                    },
                    "trades": trades[:20],  # Return only the first 20 trades
                    "signals": signals[:20]  # Return only the first 20 signals
                }
            }
        else:
            return {
                "status": "info",
                "message": f"No trading signals generated during backtest period for {strategy_type} on {symbol} {interval}"
            }
    except Exception as e:
        return {"status": "error", "message": f"Backtest failed: {str(e)}"}

# Process startup time
process_start_time = datetime.datetime.now()

# Main entry point
if __name__ == "__main__":
    print(f"Trading bot started at {process_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Use MCP tools to interact with the bot")
    mcp.run(transport="stdio")
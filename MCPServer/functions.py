import json
import pandas as pd
import datetime
import config
import strategies
# from binance.client import Client, BinanceAPIException
# from binance.enums import *
import requests
import keys
import websocket
import ssl 
import config
# import psutil
# import ta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("trading_agent")



# Data Variables
start_time = datetime.datetime.now()
opens = []
highs = []
lows = []
closes = []
volumes = []
times = []
strats = []
sym = None
cdlTme = None
cdlInt = None
in_buy_position = False
in_sell_position = False
liquidate_on_exit = False
position_size = 0


MAX_CANDLES = 100 # This needs to be dynamic based on max candles required

# client = Client(keys.API_KEY, keys.API_SECRET, tld = "com")

# def start_strategy(strategy, symbol, interval, candletime):
#     global strats, sym, cdlTme, cdlInt

#     # Store strategy in global variable
#     strats = strategy
#     sym = symbol.upper()
#     cdlTme = candletime
#     cdlInt = interval
    
#     # Make sure strategy is a list
#     if isinstance(strategy, str):
#         strategy = [strategy]
        
#     # Fetch historical data if needed
#     fetch_historical_candles(symbol, interval)
    
#     # Establish WebSocket connection
#     establish_wesocket_connection(symbol, interval, candletime)

# # def start_weighted_strategy(strategies, symbol, interval, candletime, **kwargs):
# #     global strats, sym, cdlTme, cdlInt
    
# #     # Fetch historical data if needed
# #     fetch_historical_candles(symbol, interval)
# #     establish_wesocket_connection(symbol, interval, candletime)
# #     strats = strategies
# #     sym = symbol.upper()
# #     cdlTme = candletime
# #     cdlInt = interval


# def establish_wesocket_connection(symbol, interval, candletime):
#     # Function to establish WebSocket connection
#         # Print start message
#         print("Starting Real-Time Crypto Trading Bot...")
#         print(f"Trading pair: {symbol}")
#         print(f"Ticker timezone: {candletime}")
#         print(f"Interval: {interval}")

#         websocket.enableTrace(False)

#         # Format WebSocket URL
#         strmSym = symbol.lower()
#         strmInt = interval
#         cdlTme = candletime

#         SOCKET = f"wss://stream.binance.com:9443/ws/{strmSym}@kline_{strmInt}"
#         print(f"Connecting to WebSocket: {SOCKET}")

#         # Create WebSocket app
#         ws = websocket.WebSocketApp(SOCKET, 
#                                 on_open=on_open, 
#                                 on_message=on_message, 
#                                 on_error=on_error, 
#                                 on_close=on_close)

#         # Start WebSocket connection
#         print("Starting WebSocket connection...")
#         ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


# def on_open(ws):
#     global df
#     df = create_dataframe()
#     print("Opened connection")

# def on_close(ws, close_status_code, close_msg):
#     global liquidate_on_exit
#     print(f"Connection closed: liquidating positions?")
#     # Liquidate positions
#     l_inp = input("Y/N: Liquidate positions? (Y/N): ")
#     if l_inp.lower() == "y" or l_inp.lower() == "Y":
#         liquidate_on_exit = True
#         print("Liquidating positions...")
#         liquidate_all_positions()
#     else:
#         print("Not liquidating positions.")
        

# def on_error(ws, error): 
#     print(f"Error: {error}")

# def on_message(ws, message):
#     global closes, highs, lows, opens, volumes, times, df, strats, sym, cdlTme, cdlInt, MAX_CANDLES
    
#     json_message = json.loads(message)
#     if len(df)<MAX_CANDLES or df.empty: 
#             fetch_historical_candles(sym, cdlInt, limit=MAX_CANDLES)

#     if 'k' in json_message:
#         candle = json_message['k']
        
#         # Extract candle data
#         is_candle_closed = candle['x']
#         close = float(candle['c'])
#         high = float(candle['h'])
#         low = float(candle['l'])
#         open_price = float(candle['o'])
#         volume = float(candle['v'])
#         candle_time = candle['t']
        
#         # Only process closed candles
#         if is_candle_closed:
#             print(f"New candle closed at {close}")
#             closes.append(close)
#             highs.append(high)
#             lows.append(low)
#             opens.append(open_price)
#             volumes.append(volume)
#             times.append(candle_time)
#             if len(closes) > MAX_CANDLES:
#                 closes = closes[-MAX_CANDLES:]
#                 highs = highs[-MAX_CANDLES:]
#                 lows = lows[-MAX_CANDLES:]
#                 opens = opens[-MAX_CANDLES:]
#                 volumes = volumes[-MAX_CANDLES:]
#                 times = times[-MAX_CANDLES:]
#             df = create_dataframe()
            

#             process_strategies(df)


# def process_strategies(dataframe):
#     """
#     Process all strategies with the current dataframe
#     Parameters:
#     dataframe (pandas.DataFrame): DataFrame with OHLCV data
#     """
#     global strats, sym
    
#     # Get configurations
#     symbol = sym.upper()
#     strategy_config = config.STRATEGY_CONFIG if hasattr(config, 'STRATEGY_CONFIG') else {}
#     enabled_strategies = strats
    
#     # Run all enabled strategies
#     results = []
#     # buy_weight = 0
#     # sell_weight = 0

#     for strategy_name in enabled_strategies:
#         if strategy_name in strategies.Strategy_List:
#             # Get strategy-specific config
#             strategy_params = strategy_config.get(strategy_name, {})
            
#             # Run the strategy
#             signal = run_strategy(strategy_name, dataframe, symbol, **strategy_params)
#             results.append(signal)
            
#             # Execute niggaaa
#             if signal["action"] in ["BUY", "SELL"]:
#                 if signal["action"] == "BUY":
#                     # buy_weight += config.STRATEGY_CONFIG.get(strategy_name, {}).get("weight")
#                      execute_trade(signal)
#                 elif signal["action"] == "SELL":
#                     # sell_weight += config.STRATEGY_CONFIG.get(strategy_name, {}).get("weight")
#                      execute_trade(signal)
    
#     # Log signals and account status
#     log_all(signal)


#     # if buy_weight >= config.DECISION_THRESHOLD:
#     #     execute_trade(signal)
#     # if sell_weight >= config.DECISION_THRESHOLD:
#     #     execute_trade(signal)
    
#     return results


# def create_dataframe():
#     df = pd.DataFrame({
#         'open': opens,
#         'high': highs,
#         'low': lows,
#         'close': closes,
#         'volume': volumes,
#         'time': times
#     })
#     # timestamp to datetime
#     df['time'] = pd.to_datetime(df['time'], unit='ms')

#     return df

# def fetch_historical_candles(symbol, interval, limit=MAX_CANDLES):
#     """
#     Fetch historical candles from Binance public API to initialize our data
    
#     Parameters:
#     symbol (str): Trading pair symbol (e.g., 'ETHUSDT')
#     interval (str): Candle interval (e.g., '1m', '1h')
#     limit (int): Number of candles to fetch
#     """
#     global closes, highs, lows, opens, volumes, times, df
    
#     try:
#         # Binance public API endpoint for klines (candlestick data)
#         url = f"https://api.binance.com/api/v3/klines"
        
#         # Params for the API request
#         params = {
#             'symbol': symbol.upper(),
#             'interval': interval,
#             'limit': limit
#         }
        
#         # Make the GET request
#         response = requests.get(url, params=params)
#         response.raise_for_status()
        
#         # Parse the JSON response
#         klines = response.json()
        
#         # Clear existing data and add new data
#         opens.clear()
#         highs.clear()
#         lows.clear()
#         closes.clear()
#         volumes.clear()
#         times.clear()
#         for kline in klines:
#             opens.append(float(kline[1]))
#             highs.append(float(kline[2]))
#             lows.append(float(kline[3]))
#             closes.append(float(kline[4]))
#             volumes.append(float(kline[5]))
#             times.append(kline[0])
        
#         print(f"Fetched {len(klines)} historical candles")
#         # Create DataFrame
#         df = create_dataframe()
#     except Exception as e:
#         print(f"Error fetching historical data: {e}")

@mcp.tool()
def run_strategy(strategy_name, df, symbol, **kwargs):
    """
    Run a specific trading strategy
    
    Parameters:
    strategy_name (str): Name of the strategy to run
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    **kwargs: Additional parameters
    
    Returns:
    dict: Trading signal with action and params
    """

    strategy_config = config.STRATEGY_CONFIG.get(strategy_name, {})
    if strategy_name == 'RSI':
        return strategies.rsi_strategy(
            df, symbol,
            period=kwargs.get('period', strategy_config.get('rsi_period')),
            overbought=kwargs.get('overbought', strategy_config.get('rsi_overbought')),
            oversold=kwargs.get('oversold', strategy_config.get('rsi_oversold'))
        )
    
    elif strategy_name == 'MACD':
        return strategies.macd_strategy(
            df, symbol,
            fast_period=kwargs.get('fast_period', strategy_config.get('macd_fast_period')),
            slow_period=kwargs.get('slow_period', strategy_config.get('macd_slow_period')),
            signal_period=kwargs.get('signal_period', strategy_config.get('macd_signal_period'))
        )
    
    elif strategy_name == 'Bollinger Bands':
        return strategies.bollinger_bands_strategy(
            df, symbol,
            period=kwargs.get('period', strategy_config.get('bb_period')),
            std_dev=kwargs.get('std_dev', strategy_config.get('bb_std_dev'))
        )
    
    elif strategy_name == 'EMA Cross':
        return strategies.ema_cross_strategy(
            df, symbol,
            fast_period=kwargs.get('fast_period', strategy_config.get('ema_fast_period')),
            slow_period=kwargs.get('slow_period', strategy_config.get('ema_slow_period'))
        )
    
    elif strategy_name == 'Ichimoku Cloud':
        return strategies.ichimoku_cloud_strategy(
            df, symbol,
            conversion_period=kwargs.get('conversion_period', strategy_config.get('ich_conversion_period')),
            base_period=kwargs.get('base_period', strategy_config.get('ich_base_period')),
            span_b_period=kwargs.get('span_b_period', strategy_config.get('ich_span_b_period')),
            displacement=kwargs.get('displacement', strategy_config.get('ich_displacement'))
        )
    
    elif strategy_name == 'VWAP':
        return strategies.vwap_strategy(
            df, symbol,
            period=kwargs.get('period', strategy_config.get('vwap_period'))
        )
    
    elif strategy_name == 'Support Resistance':
        return strategies.support_resistance_strategy(
            df, symbol,
            period=kwargs.get('period', strategy_config.get('sr_period')),
            threshold=kwargs.get('threshold', strategy_config.get('sr_threshold'))
        )
      
    else:
        return {
            "action": "ERROR",
            "symbol": symbol,
            "strategy": strategy_name,
            "message": f"Strategy '{strategy_name}' not found"
        }

# def execute_trade(signal):
#     """
#     Execute a trade based on the signal
#     Parameters:
#     signal (dict): Trading signal with action and params
#     """
#     global position_size, in_buy_position, in_sell_position, client
#     # Check if trading is enabled in config
#     if not hasattr(config, 'ENABLE_TRADING') or not config.ENABLE_TRADING:
#         print(f"Trading disabled. Signal would not execute: {signal['action']} {signal['symbol']}")
#         return
    
#     account_data = get_account_status()

#     # Get trading parameters
#     action = signal['action']
#     quantity = config.TRADE_QUANTITY

#     try:
#         if action == "BUY":
#             if not in_buy_position:
#                 if account_data['quote_balance'] > config.TRADE_QUANTITY:
                    
#                     order = client.create_order(symbol=sym.upper(), side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity)
#                     print(f"BUY ORDER EXECUTED: {order}")
#                     in_buy_position = True
#                     in_sell_position = False
#                     position_size += quantity 

#                 else:
#                     print(f"Insufficient balance to execute buy order. Available: {account_data['quote_balance']}, Required: {config.TRADE_QUANTITY}")
#             else:
#                 print("Signal to BUY, but already in BUY Position")
        
#         elif action == "SELL": 
#             if not in_sell_position: 
#                 if account_data['base_balance'] > config.TRADE_QUANTITY:

#                     order = client.create_order(symbol=sym.upper(), side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity)
#                     in_sell_position = True
#                     in_buy_position = False
#                     position_size -= quantity
#                     print(f"SELL ORDER EXECUTED: {order}")

#                 else:
#                     print(f"Insufficient balance to execute sell order. Available: {account_data['base_balance']}, Required: {config.TRADE_QUANTITY}")
#             else:
#                 print("Signal to SELL, but already in SELL Position") 
#         else:
#             print(f"Unknown action: {action}. No trade executed.")
#     except Exception as e:
#         print(f"Error executing trade: {e}")



# def get_minimum_notional_value():
#     global sym, client

#     exchange_info = client.get_exchange_info()
#     symbol_info = None
#     for s in exchange_info['symbols']:
#         if s['symbol'] == sym.upper():
#             symbol_info = s
#             break

#     if symbol_info is None:
#         print(f"Symbol {sym.upper()} not found")
#     else:
#         # Find the MIN_NOTIONAL filter
#         min_notional = None
#         for f in symbol_info['filters']:
#             if f['filterType'] in ['NOTIONAL', 'MIN_NOTIONAL']:
#                 min_notional = f.get('minNotional')
#                 break

#         if min_notional:
#             return min_notional
#         else:
#             print(f"MIN_NOTIONAL filter not found for {sym.upper()}")
#             return



# def log_all(signal):
#     """Logs all relevant information including signal and account status"""
#     log_signal(signal)
#     account_data = get_account_status()
#     if account_data:
#         log_account_status(account_data)

# def get_account_status():
#     """Collects account status data and returns it as a dictionary"""
#     global df, sym, client
    
#     try:
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         # Get current price from dataframe
#         current_price = df['close'].iloc[-1] if not df.empty else 0.0

#         # Get account balances
#         account_info = client.get_account()
#         quote_asset = 'USDT'
#         base_asset = sym.replace(quote_asset, '')
        
#         quote_balance = next((float(asset['free']) + float(asset['locked']) 
#                            for asset in account_info['balances'] if asset['asset'] == quote_asset), 0.0)
#         base_balance = next((float(asset['free']) + float(asset['locked']) 
#                           for asset in account_info['balances'] if asset['asset'] == base_asset), 0.0)
#         total_value = quote_balance + (base_balance * current_price)

#         # Fetch trade history
#         trades = client.get_my_trades(symbol=sym)
#         buy_trades = [t for t in trades if t['isBuyer']]
#         sell_trades = [t for t in trades if not t['isBuyer']]

#         # Calculate PnL metrics
#         total_buy_qty = sum(float(t['qty']) for t in buy_trades)
#         total_buy_cost = sum(float(t['quoteQty']) for t in buy_trades)
#         avg_buy_price = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0
#         unrealized_pnl = (current_price - avg_buy_price) * base_balance if avg_buy_price > 0 else 0
#         unrealized_pnl_pct = (unrealized_pnl / (avg_buy_price * base_balance)) * 100 if avg_buy_price > 0 and base_balance > 0 else 0
#         realized_pnl = sum((float(t['price']) - avg_buy_price) * float(t['qty']) for t in sell_trades) if avg_buy_price > 0 else 0
#         total_pnl = unrealized_pnl + realized_pnl

#         # Prepare transaction history
#         transactions = []
#         for trade in reversed(trades[-5:]):
#             transactions.append({
#                 'time': datetime.datetime.fromtimestamp(trade['time']/1000).strftime("%Y-%m-%d %H:%M"),
#                 'side': 'BUY' if trade['isBuyer'] else 'SELL',
#                 'qty': float(trade['qty']),
#                 'price': float(trade['price']),
#                 'value': float(trade['quoteQty'])
#             })

#         return {
#             'timestamp': timestamp,
#             'current_price': current_price,
#             'quote_asset': quote_asset,
#             'base_asset': base_asset,
#             'quote_balance': quote_balance,
#             'base_balance': base_balance,
#             'total_value': total_value,
#             'avg_buy_price': avg_buy_price,
#             'unrealized_pnl': unrealized_pnl,
#             'unrealized_pnl_pct': unrealized_pnl_pct,
#             'realized_pnl': realized_pnl,
#             'total_pnl': total_pnl,
#             'transactions': transactions
#         }
        
#     except Exception as e:
#         print(f"Error collecting account data: {e}")
#         return None

# def log_account_status(data):
#     """Logs account status data in a formatted way"""
#     if not data:
#         return

#     log_separator = "=" * 80
#     transaction_lines = [f"{t['time']} {t['side']} {t['qty']:.4f} {data['base_asset']} @ {t['price']:.6f} {data['quote_asset']}" 
#                        for t in data['transactions']]
    
#     log_lines = [
#         log_separator,
#         f"💼 ACCOUNT STATUS - {data['timestamp']} 💼",
#         log_separator,
#         f"💰 BALANCES:",
#         f"   {data['quote_asset']}: {data['quote_balance']:.2f}",
#         f"   {data['base_asset']}: {data['base_balance']:.6f}",
#         f"   Total Value: {data['total_value']:.2f} {data['quote_asset']}",
#         "",
#         f"📈 CURRENT PRICE: {data['current_price']:.6f} {data['quote_asset']}",
#         "",
#         f"📊 PROFIT & LOSS:",
#         f"   Avg Buy Price: {data['avg_buy_price']:.6f}" if data['avg_buy_price'] > 0 else "   No buy trades yet",
#         f"   Unrealized PnL: {data['unrealized_pnl']:.2f} ({data['unrealized_pnl_pct']:.2f}%)" if data['avg_buy_price'] > 0 else "",
#         f"   Realized PnL: {data['realized_pnl']:.2f}",
#         f"   Total PnL: {data['total_pnl']:.2f}",
#         "",
#         f"📝 RECENT TRANSACTIONS:"
#     ]
    
#     log_lines.extend(transaction_lines if transaction_lines else ["   No transactions"])
#     log_lines.extend([
#         "",
#         f"📉 RISK METRICS:",
#         "   Sharpe Ratio: N/A (Feature not implemented)",
#         "   VaR (95%): N/A (Feature not implemented)",
#         log_separator
#     ])
    
#     log_message = "\n".join([line for line in log_lines if line])
    
#     # Print and log with reverse chronological order
#     print(f"[{data['timestamp']}] - Tracker Log Updated")
#     if hasattr(config, 'LOG_FILE') and config.LOG_FILE:
#         try:
#             with open(config.LOG_FILE, 'r+') as f:
#                 content = f.read()
#                 f.seek(0, 0)
#                 f.write(log_message + "\n\n" + content)
#         except FileNotFoundError:
#             with open(config.LOG_FILE, 'w') as f:
#                 f.write(log_message + "\n")

# def log_signal(signal):
#     """Logs trading signals with integrated account status"""
#     # Log the signal
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     signal_message = f"[{timestamp}] [{signal['strategy']}] {signal['action']}: {signal['message']}"
#     print(signal_message)
    
#     # Log to file
#     if hasattr(config, 'LOG_FILE') and config.LOG_FILE:
#         try:
#             with open(config.LOG_FILE, 'r+') as f:
#                 content = f.read()
#                 f.seek(0, 0)
#                 f.write(signal_message + "\n" + content)
#         except FileNotFoundError:
#             with open(config.LOG_FILE, 'w') as f:
#                 f.write(signal_message + "\n")


# def liquidate_all_positions():
#     if position_size > 0 and liquidate_on_exit == True:
#         try:
#             order = client.create_order(symbol=sym, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=position_size)
#             print(f"SELL ORDER EXECUTED: {order}")
#         except BinanceAPIException as e:
#             print(f"Error executing sell order: {e}, please try liquidate manually")
#     else:
#         print("No positions to liquidate.")



# def calculate_position_size(symbol, risk_percent=config.RISK_PERCENT, stop_loss_percent=config.STOP_LOSS_PERCENT):
#     """
#     Calculate position size based on account balance and risk parameters
#     Parameters:
#     symbol (str): Trading pair symbol
#     risk_percent (float): Percentage of balance to risk per trade
#     stop_loss_percent (float): Stop loss percentage from entry
#     Returns:
#     float: Position size in base currency
#     """
#     try:
#         # Get account balance
#         account = client.get_account()
#         balance = float([asset for asset in account['balances'] if asset['asset'] == 'USDT'][0]['free'])
#         print(f"Account balance: {balance} USDT")
        
#         # Calculate risk amount
#         risk_amount = balance * (risk_percent / 100)
        
#         # Get current price
#         ticker = client.get_symbol_ticker(symbol=symbol)
#         price = float(ticker['price'])
        
#         # Calculate stop loss price
#         stop_loss_price = price * (1 - stop_loss_percent / 100)
        
#         # Calculate position size
#         position_size = risk_amount / (price - stop_loss_price)
        
#         return position_size
    
#     except Exception as e:
#         print(f"Error calculating position size: {e}")

if __name__ == "__main__":
    mcp.run(transport="stdio")
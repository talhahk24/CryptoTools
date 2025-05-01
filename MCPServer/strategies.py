import numpy as np
# import pandas as pd
import talib as ta
# from binance.enums import *


# List of available strategies
Strategies_impl = ['RSI', 'MACD', 'Bollinger Bands', 'EMA Cross', 'Ichimoku Cloud', 'VWAP', 'Support Resistance']
Strategy_List = ['RSI', 'MACD', 'Bollinger Bands', 'EMA Cross', 'Ichimoku Cloud', 'VWAP', 'Support Resistance']
        

def rsi_strategy(df, symbol, period, overbought, oversold):
    """
    RSI Strategy: Buy when RSI is below oversold level and sell when RSI is above overbought level
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    period (int): RSI period
    overbought (int): RSI overbought threshold
    oversold (int): RSI oversold threshold
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < period:
        return {"action": "WAIT", "symbol": symbol, "strategy": "RSI", "message": "Not enough data"}
    
    # Calculate RSI
    rsi = ta.RSI(df['close'].astype(float).values, timeperiod=period)
    current_rsi = rsi[-1]
    
    # Generate signals
    if current_rsi < oversold:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "RSI",
            "message": f"RSI below oversold level ({current_rsi:.2f} < {oversold})",
            "indicators": {"rsi": current_rsi}
        }

    elif current_rsi > overbought:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "RSI",
            "message": f"RSI above overbought level ({current_rsi:.2f} > {overbought})",
            "indicators": {"rsi": current_rsi}
        }
    else:
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "RSI",
            "message": f"RSI in neutral zone ({current_rsi:.2f})",
            "indicators": {"rsi": current_rsi}
        }

def macd_strategy(df, symbol, fast_period, slow_period, signal_period):
    """
    MACD Strategy: Buy when MACD crosses above signal line and sell when MACD crosses below signal line
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    fast_period (int): MACD fast EMA period
    slow_period (int): MACD slow EMA period
    signal_period (int): MACD signal line period
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < slow_period + signal_period:
        return {"action": "WAIT", "symbol": symbol, "strategy": "MACD", "message": "Not enough data"}
    
    # Calculate MACD
    macd, signal, hist = ta.MACD(
        df['close'].astype(float).values,
        fastperiod=fast_period,
        slowperiod=slow_period,
        signalperiod=signal_period
    )
    
    current_macd = macd[-1]
    current_signal = signal[-1]
    current_hist = hist[-1]
    prev_hist = hist[-2]
    
    # Generate signals
    if current_hist > 0 and prev_hist < 0:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "MACD",
            "message": f"MACD crossed above signal line (MACD: {current_macd:.6f}, Signal: {current_signal:.6f})",
            "indicators": {"macd": current_macd, "signal": current_signal, "histogram": current_hist}
        }
    elif current_hist < 0 and prev_hist > 0:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "MACD",
            "message": f"MACD crossed below signal line (MACD: {current_macd:.6f}, Signal: {current_signal:.6f})",
            "indicators": {"macd": current_macd, "signal": current_signal, "histogram": current_hist}
        }
    else:
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "MACD",
            "message": f"No MACD crossover (MACD: {current_macd:.6f}, Signal: {current_signal:.6f})",
            "indicators": {"macd": current_macd, "signal": current_signal, "histogram": current_hist}
        }

def bollinger_bands_strategy(df, symbol, period, std_dev):
    """
    Bollinger Bands Strategy: Buy when price touches lower band and sell when price touches upper band
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    period (int): Bollinger Bands period
    std_dev (int): Standard deviation multiplier
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < period:
        return {"action": "WAIT", "symbol": symbol, "strategy": "Bollinger Bands", "message": "Not enough data"}
    
    # Calculate Bollinger Bands
    upper, middle, lower = ta.BBANDS(
        df['close'].astype(float).values,
        timeperiod=period,
        nbdevup=std_dev,
        nbdevdn=std_dev,
        matype=0
    )
    
    current_close = df['close'].iloc[-1]
    current_upper = upper[-1]
    current_middle = middle[-1]
    current_lower = lower[-1]
    
    # Generate signals
    if current_close <= current_lower:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "Bollinger Bands",
            "message": f"Price at/below lower band (Price: {current_close:.6f}, Lower: {current_lower:.6f})",
            "indicators": {"price": current_close, "upper": current_upper, "middle": current_middle, "lower": current_lower}
        }
    elif current_close >= current_upper:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "Bollinger Bands",
            "message": f"Price at/above upper band (Price: {current_close:.6f}, Upper: {current_upper:.6f})",
            "indicators": {"price": current_close, "upper": current_upper, "middle": current_middle, "lower": current_lower}
        }
    else:
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "Bollinger Bands",
            "message": f"Price within bands (Price: {current_close:.6f}, Upper: {current_upper:.6f}, Lower: {current_lower:.6f})",
            "indicators": {"price": current_close, "upper": current_upper, "middle": current_middle, "lower": current_lower}
        }

def ema_cross_strategy(df, symbol, fast_period, slow_period):
    """
    EMA Cross Strategy: Buy when fast EMA crosses above slow EMA and sell when fast EMA crosses below slow EMA
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    fast_period (int): Fast EMA period
    slow_period (int): Slow EMA period
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < slow_period:
        return {"action": "WAIT", "symbol": symbol, "strategy": "EMA Cross", "message": "Not enough data"}
    
    # Calculate EMAs
    fast_ema = ta.EMA(df['close'].astype(float).values, timeperiod=fast_period)
    slow_ema = ta.EMA(df['close'].astype(float).values, timeperiod=slow_period)
    
    current_fast = fast_ema[-1]
    current_slow = slow_ema[-1]
    prev_fast = fast_ema[-2]
    prev_slow = slow_ema[-2]
    
    # Generate signals
    if current_fast > current_slow and prev_fast <= prev_slow:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "EMA Cross",
            "message": f"Fast EMA crossed above slow EMA (Fast: {current_fast:.6f}, Slow: {current_slow:.6f})",
            "indicators": {"fast_ema": current_fast, "slow_ema": current_slow}
        }
    elif current_fast < current_slow and prev_fast >= prev_slow:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "EMA Cross",
            "message": f"Fast EMA crossed below slow EMA (Fast: {current_fast:.6f}, Slow: {current_slow:.6f})",
            "indicators": {"fast_ema": current_fast, "slow_ema": current_slow}
        }
    else:
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "EMA Cross",
            "message": f"No EMA crossover (Fast: {current_fast:.6f}, Slow: {current_slow:.6f})",
            "indicators": {"fast_ema": current_fast, "slow_ema": current_slow}
        }

def ichimoku_cloud_strategy(df, symbol, conversion_period, 
                           base_period, span_b_period, 
                           displacement):
    """
    Ichimoku Cloud Strategy: 
    Buy when price crosses above the cloud and Tenkan-sen crosses above Kijun-sen
    Sell when price crosses below the cloud and Tenkan-sen crosses below Kijun-sen
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    conversion_period (int): Tenkan-sen (Conversion Line) period
    base_period (int): Kijun-sen (Base Line) period
    span_b_period (int): Senkou Span B period
    displacement (int): Displacement period
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < max(conversion_period, base_period, span_b_period) + displacement:
        return {"action": "WAIT", "symbol": symbol, "strategy": "Ichimoku Cloud", "message": "Not enough data"}
    
    # Extract high and low values
    high = df['high'].astype(float).values
    low = df['low'].astype(float).values
    close = df['close'].astype(float).values
    
    # Calculate Ichimoku components
    tenkan_sen = (ta.MAX(high, timeperiod=conversion_period) + ta.MIN(low, timeperiod=conversion_period)) / 2
    kijun_sen = (ta.MAX(high, timeperiod=base_period) + ta.MIN(low, timeperiod=base_period)) / 2
    
    # Calculate Senkou Span A (Leading Span A)
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    
    # Calculate Senkou Span B (Leading Span B)
    senkou_span_b = (ta.MAX(high, timeperiod=span_b_period) + ta.MIN(low, timeperiod=span_b_period)) / 2
    
    # Get current values
    current_close = close[-1]
    current_tenkan = tenkan_sen[-1]
    current_kijun = kijun_sen[-1]
    current_span_a = senkou_span_a[-displacement] if len(senkou_span_a) > displacement else None
    current_span_b = senkou_span_b[-displacement] if len(senkou_span_b) > displacement else None
    
    # Previous values for crossover detection
    prev_tenkan = tenkan_sen[-2]
    prev_kijun = kijun_sen[-2]
    
    # Generate signals
    if current_span_a is None or current_span_b is None:
        return {"action": "WAIT", "symbol": symbol, "strategy": "Ichimoku Cloud", "message": "Waiting for cloud formation"}
    
    # Calculate cloud boundaries
    cloud_top = max(current_span_a, current_span_b)
    cloud_bottom = min(current_span_a, current_span_b)
    
    # Buy signals: Price above cloud + Tenkan crosses above Kijun
    if current_close > cloud_top and current_tenkan > current_kijun and prev_tenkan <= prev_kijun:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "Ichimoku Cloud",
            "message": f"Price above cloud with bullish TK cross (Price: {current_close:.6f}, Cloud: {cloud_top:.6f})",
            "indicators": {
                "tenkan": current_tenkan,
                "kijun": current_kijun,
                "span_a": current_span_a,
                "span_b": current_span_b
            }
        }
    # Sell signals: Price below cloud + Tenkan crosses below Kijun
    elif current_close < cloud_bottom and current_tenkan < current_kijun and prev_tenkan >= prev_kijun:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "Ichimoku Cloud",
            "message": f"Price below cloud with bearish TK cross (Price: {current_close:.6f}, Cloud: {cloud_bottom:.6f})",
            "indicators": {
                "tenkan": current_tenkan,
                "kijun": current_kijun,
                "span_a": current_span_a,
                "span_b": current_span_b
            }
        }
    else:
        position = "above cloud" if current_close > cloud_top else "below cloud" if current_close < cloud_bottom else "in cloud"
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "Ichimoku Cloud",
            "message": f"No signal, price {position} (Price: {current_close:.6f})",
            "indicators": {
                "tenkan": current_tenkan,
                "kijun": current_kijun,
                "span_a": current_span_a,
                "span_b": current_span_b
            }
        }

def vwap_strategy(df, symbol, period):
    """
    VWAP Strategy: Buy when price crosses above VWAP and sell when price crosses below VWAP
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    period (int): VWAP calculation period
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < period:
        return {"action": "WAIT", "symbol": symbol, "strategy": "VWAP", "message": "Not enough data"}
    
    # Calculate VWAP
    df = df.copy()
    df['hlc3'] = (df['high'].astype(float) + df['low'].astype(float) + df['close'].astype(float)) / 3
    df['hlc3_volume'] = df['hlc3'] * df['volume'].astype(float)
    
    df['cum_volume'] = df['volume'].astype(float).rolling(window=period).sum()
    df['cum_hlc3_volume'] = df['hlc3_volume'].rolling(window=period).sum()
    df['vwap'] = df['cum_hlc3_volume'] / df['cum_volume']
    
    current_close = df['close'].iloc[-1]
    current_vwap = df['vwap'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    prev_vwap = df['vwap'].iloc[-2]
    
    # Generate signals
    if current_close > current_vwap and prev_close <= prev_vwap:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "VWAP",
            "message": f"Price crossed above VWAP (Price: {current_close:.6f}, VWAP: {current_vwap:.6f})",
            "indicators": {"price": current_close, "vwap": current_vwap}
        }
    elif current_close < current_vwap and prev_close >= prev_vwap:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "VWAP",
            "message": f"Price crossed below VWAP (Price: {current_close:.6f}, VWAP: {current_vwap:.6f})",
            "indicators": {"price": current_close, "vwap": current_vwap}
        }
    else:
        position = "above VWAP" if current_close > current_vwap else "below VWAP"
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "VWAP",
            "message": f"No signal, price {position} (Price: {current_close:.6f}, VWAP: {current_vwap:.6f})",
            "indicators": {"price": current_close, "vwap": current_vwap}
        }

def support_resistance_strategy(df, symbol, period, threshold):
    """
    Support and Resistance Strategy:
    Buy when price bounces off support level and sell when price rejects from resistance level
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing OHLCV data
    symbol (str): Trading pair symbol
    period (int): Period to look for pivots
    threshold (float): Percentage threshold to consider as a level breach
    
    Returns:
    dict: Trading signal with action and params
    """
    if len(df) < period * 2:
        return {"action": "WAIT", "symbol": symbol, "strategy": "Support Resistance", "message": "Not enough data"}
    
    # Find pivot highs and lows
    close_series = df['close'].astype(float)
    high_series = df['high'].astype(float)
    low_series = df['low'].astype(float)
    
    # Get recent pivots (simplified method)
    pivot_highs = []
    pivot_lows = []
    
    for i in range(period, len(df) - period):
        # Check if this point is a pivot high
        if all(high_series[i] > high_series[i-j] for j in range(1, period+1)) and \
           all(high_series[i] > high_series[i+j] for j in range(1, period+1)):
            pivot_highs.append((i, high_series[i]))
        
        # Check if this point is a pivot low
        if all(low_series[i] < low_series[i-j] for j in range(1, period+1)) and \
           all(low_series[i] < low_series[i+j] for j in range(1, period+1)):
            pivot_lows.append((i, low_series[i]))
    
    # Get recent levels (last 3 pivots)
    recent_highs = sorted([price for _, price in pivot_highs[-3:]]) if pivot_highs else []
    recent_lows = sorted([price for _, price in pivot_lows[-3:]]) if pivot_lows else []
    
    current_close = close_series.iloc[-1]
    current_high = high_series.iloc[-1]
    current_low = low_series.iloc[-1]
    
    # Check if price is near any support or resistance
    buy_signal = False
    sell_signal = False
    nearest_support = None
    nearest_resistance = None
    
    # Find nearest support
    if recent_lows:
        supports_below = [level for level in recent_lows if level < current_close]
        if supports_below:
            nearest_support = max(supports_below)
            # Check if bounced off support
            if abs(current_low - nearest_support) / nearest_support < threshold and current_close > current_low:
                buy_signal = True
    
    # Find nearest resistance
    if recent_highs:
        resistances_above = [level for level in recent_highs if level > current_close]
        if resistances_above:
            nearest_resistance = min(resistances_above)
            # Check if rejected from resistance
            if abs(current_high - nearest_resistance) / nearest_resistance < threshold and current_close < current_high:
                sell_signal = True
    
    # Generate signals
    if buy_signal and nearest_support is not None:
        return {
            "action": "BUY",
            "symbol": symbol,
            "strategy": "Support Resistance",
            "message": f"Price bounced off support (Price: {current_close:.6f}, Support: {nearest_support:.6f})",
            "indicators": {"price": current_close, "support": nearest_support, "resistance": nearest_resistance}
        }
    elif sell_signal and nearest_resistance is not None:
        return {
            "action": "SELL",
            "symbol": symbol,
            "strategy": "Support Resistance",
            "message": f"Price rejected from resistance (Price: {current_close:.6f}, Resistance: {nearest_resistance:.6f})",
            "indicators": {"price": current_close, "support": nearest_support, "resistance": nearest_resistance}
        }
    else:
        return {
            "action": "WAIT",
            "symbol": symbol,
            "strategy": "Support Resistance",
            "message": f"No clear support/resistance signal (Price: {current_close:.6f})",
            "indicators": {"price": current_close, "support": nearest_support, "resistance": nearest_resistance}
        }

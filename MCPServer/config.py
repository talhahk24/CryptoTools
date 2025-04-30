# Trading parameters
TRADE_QUANTITY = 0.04 
ENABLE_TRADING = True
TIMEZONE = "UTC+8"  # Hong Kong timezone

# DECISION_THRESHOLD = 0.6

# Strategy-specific params
STRATEGY_CONFIG = {
    "RSI": {
        "rsi_period": 14,
        "rsi_overbought": 60,
        "rsi_oversold": 40,
        "weight": 0.3,
        "rsi_timeframe": "1m"
    },
    "MACD": {
        "macd_fast_period": 12,
        "macd_slow_period": 26,
        "macd_signal_period": 9,
        "weight": 0.1,
        "macd_timeframe": "15m"
    },
    "Bollinger Bands": {
        "bb_period": 20,
        "bb_std_dev": 2,
        "weight": 0.1,
        "bb_timeframe": "1h"
    },
    "EMA Cross": {
        "ema_fast_period": 9,
        "ema_slow_period": 21,
        "weight": 0.1,
        "ema_timeframe": "15m"
    },
    "Ichimoku Cloud": {
        "ich_conversion_period": 9,
        "ich_base_period": 26,
        "ich_span_b_period": 52,
        "ich_displacement": 26,
        "weight": 0.1,
        "ich_timeframe": "4h"
    },
    "VWAP": {
        "vwap_period": 14,
        "weight": 0.1,
        "vwap_timeframe": "1h"
    },
    "Support Resistance": {
        "sr_period": 14,
        "sr_threshold": 0.05,
        "weight": 0.1,
        "sr_timeframe": "4h"
    }
}

# Logging settings
LOG_FILE = "trading_log.txt"

# Risk management settings
# RISK_PERCENT = 3.0  # 3% of account balance per trade
# STOP_LOSS_PERCENT = 8.0  # 8% stop loss from entry price
# TAKE_PROFIT_PERCENT = 8.0  # 8% take profit from entry price